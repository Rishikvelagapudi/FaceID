import math
from pathlib import Path
from typing import Dict, Any, Optional
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

def verify_candidate(
    original_path: Path,
    item: dict,
    source_embedding: Optional[np.ndarray] = None,
    face_encoder = None,
    similarity_threshold: float = 0.40,
    phash_max_distance: int = 12,
) -> Dict[str, Any]:
    """
    Independently re-verifies a candidate image by downloading it, extracting
    ArcFace 512-D biometric face embeddings (if a face is detected), and computing
    exact cosine similarity alongside perceptual hashing.
    """
    candidate_url = item.get("image_url")
    if not candidate_url:
        raise ValueError("No candidate image URL available.")

    original = Image.open(original_path).convert("RGB")
    candidate = download_image(candidate_url)

    # 1. Perceptual hashing (pHash)
    original_phash = imagehash.phash(original)
    candidate_phash = imagehash.phash(candidate)
    distance = int(original_phash - candidate_phash)
    phash_similarity = max(0.0, 1.0 - (distance / 64.0))

    # 2. Histogram visual descriptor
    h1 = _histogram_embedding(original)
    h2 = _histogram_embedding(candidate)
    hist_cosine = _histogram_cosine(h1, h2)

    # 3. Biometric ArcFace 512-D Cosine Similarity
    biometric_similarity = 0.0
    candidate_face_detected = False
    candidate_norm = 0.0

    if face_encoder is not None:
        try:
            cand_emb, telemetry = face_encoder.get_embedding(candidate)
            if cand_emb is not None and telemetry.get("detected"):
                candidate_face_detected = True
                candidate_norm = telemetry.get("norm", 0.0)
                if source_embedding is not None:
                    biometric_similarity = max(0.0, cosine_similarity(source_embedding, cand_emb))
        except Exception:
            candidate_face_detected = False

    # 4. Composite ranking score
    if candidate_face_detected and source_embedding is not None:
        # If faces detected on both, biometric similarity dominates
        overall_similarity = round(float(biometric_similarity), 4)
        verified = bool(overall_similarity >= similarity_threshold)
    else:
        # Fallback to visual and pHash similarity when candidate has non-frontal or undetectable face
        overall_similarity = round(float((0.65 * phash_similarity) + (0.35 * max(0.0, hist_cosine))), 4)
        verified = bool(distance <= phash_max_distance and overall_similarity >= similarity_threshold)

    return {
        "candidate_image_url": candidate_url,
        "phash_distance": distance,
        "phash_similarity": round(phash_similarity, 4),
        "histogram_cosine": round(hist_cosine, 4),
        "cosine_similarity": round(float(biometric_similarity), 4) if candidate_face_detected else None,
        "visual_similarity": overall_similarity,
        "candidate_face_detected": candidate_face_detected,
        "candidate_norm": round(candidate_norm, 2),
        "verified": verified,
    }
