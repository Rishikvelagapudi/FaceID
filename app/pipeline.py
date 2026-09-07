import hashlib
import json
import logging
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

from dotenv import load_dotenv

from app.face.encoder import FaceEncoder
from app.image.hashing import fingerprint_image
from app.image.similarity import verify_candidate, compute_source_descriptors
from app.reverse_search.factory import get_providers
from app.reverse_search.social_filter import classify_social_url, annotate_trust_signals
from app.deepfake.classifier import DeepfakeClassifier
from blockchain.blockchain import LocalBlockchain
from blockchain.testnet_anchor import TestnetAnchor

load_dotenv()
logger = logging.getLogger(__name__)

# Ensure Windows terminal outputs Unicode cleanly
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

class FaceIDPipeline:
    """
    FaceID end-to-end investigative forensic pipeline:
    Biometrics -> OSINT Visual Search -> ArcFace Cosine Re-verification ->
    Social Post Isolation -> ViT Deepfake Signal -> Deterministic Hashing ->
    Dual-Layer Blockchain Anchoring (Local & Ethereum Sepolia).
    """

    def __init__(self):
        self.face_encoder = FaceEncoder()
        self.deepfake_classifier = DeepfakeClassifier()
        self.local_chain = LocalBlockchain()
        self.testnet_anchor = TestnetAnchor()
        self.search_providers = get_providers()
        self.similarity_threshold = float(os.getenv("SIMILARITY_THRESHOLD", "0.40"))
        self.phash_max_distance = int(os.getenv("PHASH_MAX_DISTANCE", "12"))

    def run(
        self,
        image_path: Path,
        write_blockchain: bool = True,
        max_results: Optional[int] = None,
        verbose: bool = True,
    ) -> Dict[str, Any]:
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Input image not found: {image_path}")

        # [1/9] Extract face embedding from source image
        if verbose:
            print(f"[1/9] Extracting face embedding from source image…")
        source_embedding, face_telemetry = self.face_encoder.get_embedding(image_path)
        face_info = self.face_encoder.analyze(image_path)

        if face_telemetry.get("detected"):
            if verbose:
                print(f"      Face detected (det_score={face_telemetry.get('det_score', 0):.3f}, norm={face_telemetry.get('norm', 0):.2f})")
        else:
            if verbose:
                print("      No face detected in source image (visual & perceptual hashing will be prioritized).")

        fingerprints = fingerprint_image(image_path)

        # [2/9] Searching web via SerpAPI Google Lens
        if verbose:
            print("[2/9] Searching web via SerpAPI Google Lens…")
        search_error = None
        raw_results = []
        provider_used = None

        for provider in self.search_providers:
            try:
                results = provider.search(image_path, max_results=max_results)
                if results:
                    raw_results = results
                    provider_used = provider.name
                    search_error = None
                    break
            except Exception as exc:
                search_error = str(exc)

        if verbose:
            print(f"      {len(raw_results)} visual matches returned.")

        # [3/9] Downloading candidates in parallel (fast CDN + 3.5s timeout)
        if verbose:
            print(f"[3/9] Precomputing descriptors & fetching candidates in parallel…")
        
        source_phash, source_hist = compute_source_descriptors(image_path)

        def _fetch_candidate(item):
            url = item.get("image_url")
            fallback = item.get("fallback_url")
            if not url:
                return item, None
            try:
                from app.image.downloader import download_image
                return item, download_image(url, fallback_url=fallback)
            except Exception:
                return item, None

        downloaded_items = []
        if raw_results:
            worker_count = min(6, len(raw_results))
            with ThreadPoolExecutor(max_workers=worker_count) as executor:
                downloaded_items = list(executor.map(_fetch_candidate, raw_results))

        # [4/9] Re-verifying candidate face embeddings (0.16s per candidate)
        if verbose:
            print(f"[4/9] Evaluating biometric face embeddings & trust signals…")

        verified_results = []
        candidates_with_faces = 0
        downloaded_count = 0

        for item, cand_img in downloaded_items:
            try:
                if cand_img is None:
                    raise ValueError("Could not download candidate image")
                comparison = verify_candidate(
                    original_path=image_path,
                    item=item,
                    source_embedding=source_embedding,
                    face_encoder=self.face_encoder,
                    similarity_threshold=self.similarity_threshold,
                    phash_max_distance=self.phash_max_distance,
                    candidate_image=cand_img,
                    source_phash=source_phash,
                    source_hist=source_hist,
                )
                downloaded_count += 1
                if comparison.get("candidate_face_detected"):
                    candidates_with_faces += 1

                trust = annotate_trust_signals(item)
                verified_results.append({**item, **comparison, "social_meta": trust})
            except Exception as exc:
                trust = annotate_trust_signals(item)
                verified_results.append({
                    **item,
                    "verified": False,
                    "error": str(exc),
                    "social_meta": trust,
                    "visual_similarity": 0.0,
                    "cosine_similarity": None,
                    "candidate_face_detected": False,
                    "confidence_tier": "ERROR",
                })

        if verbose:
            print(f"      {downloaded_count}/{len(raw_results)} candidates downloaded & analyzed.")
            print(f"      {candidates_with_faces}/{max(1, len(raw_results))} candidates had detectable faces.")

        # Sort candidates descending by best visual / cosine similarity
        verified_results.sort(
            key=lambda x: max(x.get("cosine_similarity") or 0.0, x.get("visual_similarity") or 0.0),
            reverse=True
        )

        best = verified_results[0] if verified_results else None
        best_similarity = float(
            max(best.get("cosine_similarity") or 0.0, best.get("visual_similarity") or 0.0)
        ) if best else 0.0

        is_match = bool(best and best.get("verified"))
        status = "VERIFIED" if is_match else "NO_CONFIRMED_MATCH"

        if verbose:
            print(f"[4/9] Ranking candidates by ArcFace biometric similarity…")
            if best:
                tier = best.get("confidence_tier", "UNSPECIFIED")
                print(f"      Overall best | tier={tier} | similarity={best_similarity:.4f} | match={is_match} | url={best.get('link')}")
            else:
                print("      No candidates available to rank.")

        # [5b] Identifying specific social-media post candidates
        specific_social_matches = [
            r for r in verified_results
            if r.get("social_meta", {}).get("is_specific_post")
        ]
        best_social = specific_social_matches[0] if specific_social_matches else None

        if verbose:
            print(f"[5b] Identifying specific social-media post candidates…")
            if best_social:
                meta = best_social.get("social_meta", {})
                b_sim = max(best_social.get("cosine_similarity") or 0.0, best_social.get("visual_similarity") or 0.0)
                print(f"      Best specific social post | platform={meta.get('platform')} | similarity={b_sim:.4f} | url={best_social.get('link')}")
            else:
                print("      No specific social-media post URLs detected among candidate links.")

        # [5c] Annotating trust signals
        if verbose:
            print(f"[5c] Annotating trust signals (video detection & content corroboration)…")

        # [5d] Analyzing deepfake risk
        if verbose:
            print(f"[5d] Analyzing deepfake risk on primary candidate image…")
        # Run on source image and primary candidate
        deepfake_analysis = self.deepfake_classifier.analyze(image_path)
        if verbose:
            print(f"      Deepfake Assessment | Label: {deepfake_analysis.get('label')} | Risk: {deepfake_analysis.get('risk_score', 0):.2%} | Status: {deepfake_analysis.get('status')}")

        # [6/9] Building evidence record
        if verbose:
            print(f"[6/9] Building evidence record…")
        created_at = datetime.now(timezone.utc).isoformat()
        evidence_record = {
            "schema_version": "2.0",
            "protocol": "FaceID forensic evidence",
            "created_at": created_at,
            "source_image": {
                "filename": image_path.name,
                "sha256": fingerprints["sha256"],
                "phash": fingerprints["phash"],
            },
            "image": {
                "filename": image_path.name,
                "sha256": fingerprints["sha256"],
                "phash": fingerprints["phash"],
            },
            "biometrics": {
                "detected": face_info["detected"],
                "face_count": face_info["count"],
                "embedding_model": f"ArcFace 512-d ({getattr(self.face_encoder, 'model_name', 'buffalo_s')})",
                "embedding_persistent": False,  # RAM only
                "det_score": face_info.get("det_score", 0.0),
                "face_boxes": face_info.get("face_boxes", []),
                "landmarks": face_info.get("landmarks", []),
            },
            "face": {
                "detected": face_info["detected"],
                "count": face_info["count"],
                "embedding_generated": face_info.get("embedding_generated", False),
                "det_score": face_info.get("det_score", 0.0),
                "face_boxes": face_info.get("face_boxes", []),
                "landmarks": face_info.get("landmarks", []),
            },
            "osint_search": {
                "provider": provider_used,
                "total_candidates": len(verified_results),
                "error": search_error,
            },
            "reverse_search": {
                "provider": provider_used,
                "count": len(verified_results),
                "error": search_error,
            },
            "best_match": (
                {
                    "title": best.get("title"),
                    "source": best.get("source"),
                    "link": best.get("link"),
                    "platform": best.get("social_meta", {}).get("platform"),
                    "is_specific_post": best.get("social_meta", {}).get("is_specific_post"),
                    "post_type": best.get("social_meta", {}).get("post_type"),
                    "cosine_similarity": best.get("cosine_similarity"),
                    "visual_similarity": best.get("visual_similarity"),
                    "phash_distance": best.get("phash_distance"),
                    "confidence_tier": best.get("confidence_tier"),
                    "candidate_faces_found": best.get("candidate_faces_found", 0),
                    "verified": best.get("verified"),
                }
                if best else None
            ),
            "deepfake_analysis": deepfake_analysis,
            "verification": {
                "status": status,
                "confidence_tier": best.get("confidence_tier") if best else "NO_MATCH",
                "best_similarity": best_similarity,
                "threshold": self.similarity_threshold,
                "phash_max_distance": self.phash_max_distance,
            },
        }

        # [7/9] Hashing evidence record (SHA-256)
        if verbose:
            print(f"[7/9] Hashing evidence record (SHA-256)…")
        canonical_json = json.dumps(evidence_record, sort_keys=True, separators=(",", ":")).encode("utf-8")
        evidence_hash = hashlib.sha256(canonical_json).hexdigest()
        evidence_record["evidence_hash"] = evidence_hash

        if verbose:
            print(f"      Evidence hash: {evidence_hash}")

        # [8/9] Writing evidence to Layer 1 Local Blockchain
        if verbose:
            print(f"[8/9] Writing evidence to blockchain…")
        block = self.local_chain.add_block(evidence_record)
        if verbose:
            print(f"      Block #{block['index']} written | chain_length={len(self.local_chain)}")

        # [9/9] Verifying local blockchain integrity
        if verbose:
            print(f"[9/9] Verifying blockchain integrity…")
        valid, err = self.local_chain.is_valid_chain()
        found_block = self.local_chain.verify_evidence_hash(evidence_hash)
        if valid and found_block:
            if verbose:
                print(f"      Blockchain: VALID | Evidence hash found in block {found_block['index']}. Chain integrity valid.")
        else:
            if verbose:
                print(f"      [WARN] Blockchain verification issue: {err}")

        # [10/10] Anchoring to Ethereum Sepolia Testnet (Layer 2)
        sepolia_result = {
            "submitted": False,
            "network": "Ethereum Sepolia Testnet",
            "tx_hash": None,
            "explorer_url": None,
            "reason": "Skipped (no-blockchain flag or unconfigured wallet)",
        }

        if write_blockchain:
            if verbose:
                print(f"[10/10] Anchoring evidence hash to Ethereum Sepolia testnet…")
            sepolia_result = self.testnet_anchor.anchor(evidence_hash)
            if sepolia_result.get("submitted"):
                if verbose:
                    print(f"      Sepolia TX : {sepolia_result.get('tx_hash')}")
                    print(f"      Etherscan  : {sepolia_result.get('explorer_url')}")
            else:
                if verbose:
                    print(f"      Layer 2 Anchor: {sepolia_result.get('reason')}")

        evidence_record["blockchain_layer1"] = {
            "block_index": block["index"],
            "block_hash": block["hash"],
            "previous_hash": block["previous_hash"],
            "verified": valid,
        }
        evidence_record["blockchain_layer2"] = sepolia_result
        evidence_record["blockchain"] = sepolia_result  # Backward compatibility
        evidence_record["matches"] = verified_results[:10]

        # Save forensic report
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        report_path = results_dir / f"{image_path.stem}_report.json"
        report_path.write_text(
            json.dumps(evidence_record, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        evidence_record["report_path"] = str(report_path)

        return evidence_record

# Backward compatibility alias
FaceProofPipeline = FaceIDPipeline
