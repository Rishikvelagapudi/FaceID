import math
from pathlib import Path
from typing import Dict, Any, Optional, Union
from PIL import Image
import imagehash
import numpy as np

from app.image.downloader import download_image
from app.face.encoder import cosine_similarity

def _histogram_cosine(a, b):
    dot = sum(x*y for x, y in zip(a, b))
    na = math.sqrt(sum(x*x for x in a))
    nb = math.sqrt(sum(y*y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

_cosine = _histogram_cosine

def _histogram_embedding(image: Image.Image):
    img = image.resize((128, 128)).convert("RGB")
    hist = []
    for channel in range(3):
        values = list(img.getchannel(channel).histogram())
        total = sum(values) or 1
        hist.extend(v / total for v in values)
    return hist

def compute_source_descriptors(original_input: Union[Path, str, Image.Image]):
    """Precompute source pHash and color histogram once for the query image."""
    if isinstance(original_input, (Path, str)):
        original = Image.open(original_input).convert("RGB")
    else:
        original = original_input.convert("RGB")
    
    src_phash = imagehash.phash(original)
    src_hist = _histogram_embedding(original)
    return src_phash, src_hist

def verify_candidate(
    original_path: Path,
    item: dict,
    source_embedding: Optional[np.ndarray] = None,
    face_encoder = None,
    similarity_threshold: float = 0.40,
    phash_max_distance: int = 12,
    candidate_image: Optional[Image.Image] = None,
    source_phash = None,
    source_hist = None,
) -> Dict[str, Any]:
    """
    Independently re-verifies a candidate image by downloading it, extracting
    ArcFace 512-D biometric face embeddings across all detected faces, and computing
    exact cosine similarity alongside perceptual hashing.
    """
    candidate_url = item.get("image_url")
    fallback_url = item.get("fallback_url")
    if not candidate_url and candidate_image is None:
        raise ValueError("No candidate image URL available.")

    # 1. Download or use pre-fetched candidate image
    candidate = candidate_image if candidate_image is not None else download_image(candidate_url, fallback_url=fallback_url)

    # 2. Perceptual hashing (pHash) with precomputed source hash
    if source_phash is None:
        original = Image.open(original_path).convert("RGB")
        source_phash = imagehash.phash(original)
        source_hist = _histogram_embedding(original)

    candidate_phash = imagehash.phash(candidate)
    distance = int(source_phash - candidate_phash)
    phash_similarity = max(0.0, 1.0 - (distance / 64.0))

    # 3. Histogram visual descriptor
    h2 = _histogram_embedding(candidate)
    hist_cosine = _histogram_cosine(source_hist, h2)

    # 4. Multi-Face Biometric ArcFace 512-D Cosine Similarity
    biometric_similarity = 0.0
    candidate_face_detected = False
    candidate_norm = 0.0
    faces_checked = 0

    if face_encoder is not None:
        try:
            # Check ALL faces in candidate image (group shots, crowds, team photos)
            all_cand_faces = face_encoder.get_all_embeddings(candidate)
            faces_checked = len(all_cand_faces)
            if all_cand_faces:
                candidate_face_detected = True
                candidate_norm = float(np.linalg.norm(all_cand_faces[0][0]))
                if source_embedding is not None:
                    # Compare source embedding against every face detected in candidate
                    sims = [cosine_similarity(source_embedding, emb) for emb, score, bbox in all_cand_faces]
                    biometric_similarity = max(0.0, max(sims)) if sims else 0.0
        except Exception:
            candidate_face_detected = False

    # 5. Strict Forensic Verification Rules (Eliminate False Positives)
    if source_embedding is not None:
        # Query image is a human face. A candidate MUST have a detected face to be verified!
        if candidate_face_detected:
            overall_similarity = round(float(biometric_similarity), 4)
            verified = bool(overall_similarity >= similarity_threshold)
        else:
            # Candidate has no detectable face (e.g. background landscape, car, text, logo)
            overall_similarity = round(float((0.50 * phash_similarity) + (0.50 * max(0.0, hist_cosine))), 4)
            verified = False  # NEVER verify non-face candidate when query has a face!
    else:
        # Fallback when query image itself has no face (e.g. logo, document, graphic)
        overall_similarity = round(float((0.65 * phash_similarity) + (0.35 * max(0.0, hist_cosine))), 4)
        verified = bool(distance <= phash_max_distance and overall_similarity >= similarity_threshold)

    # Assign forensic confidence classification
    if candidate_face_detected and source_embedding is not None:
        if biometric_similarity >= 0.65:
            confidence_tier = "HIGH_CONFIDENCE_MATCH"
        elif biometric_similarity >= similarity_threshold:
            confidence_tier = "CONFIRMED_MATCH"
        elif biometric_similarity >= 0.35:
            confidence_tier = "POTENTIAL_MATCH"
        else:
            confidence_tier = "NO_CONFIRMED_MATCH"
    else:
        confidence_tier = "NON_BIOMETRIC_SIMILARITY" if verified else "NO_MATCH"

    return {
        "candidate_image_url": candidate_url,
        "phash_distance": distance,
        "phash_similarity": round(phash_similarity, 4),
        "histogram_cosine": round(hist_cosine, 4),
        "cosine_similarity": round(float(biometric_similarity), 4) if candidate_face_detected else None,
        "visual_similarity": overall_similarity,
        "candidate_face_detected": candidate_face_detected,
        "candidate_faces_found": faces_checked,
        "candidate_norm": round(candidate_norm, 2),
        "confidence_tier": confidence_tier,
        "verified": verified,
    }
