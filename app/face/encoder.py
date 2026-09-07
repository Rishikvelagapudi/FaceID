import os
import logging
from pathlib import Path
from typing import Union, Optional, Tuple, List
import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

def cosine_similarity(vec1: Union[np.ndarray, List[float]], vec2: Union[np.ndarray, List[float]]) -> float:
    """Compute cosine similarity between two feature vectors."""
    a = np.asarray(vec1, dtype=np.float32).flatten()
    b = np.asarray(vec2, dtype=np.float32).flatten()
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))

class FaceEncoder:
    """
    Local face detection + 512-dimensional ArcFace embedding generation using InsightFace.
    Biometric vectors are retained strictly in volatile RAM for similarity ranking
    and are never committed to public logs, reports, or the blockchain.
    """

    def __init__(self):
        self._app = None
        self.model_name = os.getenv("FACE_MODEL", "buffalo_s")

    def _load(self):
        if self._app is not None:
            return
        try:
            from insightface.app import FaceAnalysis
        except ImportError as exc:
            raise RuntimeError(
                "InsightFace is not installed. Run: pip install -r requirements.txt"
            ) from exc

        try:
            self._app = FaceAnalysis(
                name=self.model_name,
                providers=["CPUExecutionProvider"]
            )
            self._app.prepare(ctx_id=0)
        except Exception as exc:
            if self.model_name != "buffalo_s":
                logger.warning("Could not load %s, falling back to buffalo_s: %s", self.model_name, exc)
                self.model_name = "buffalo_s"
                self._app = FaceAnalysis(
                    name="buffalo_s",
                    providers=["CPUExecutionProvider"]
                )
                self._app.prepare(ctx_id=0)
            else:
                raise

    def _to_cv2(self, image_input: Union[Path, str, Image.Image, np.ndarray]) -> np.ndarray:
        if isinstance(image_input, (str, Path)):
            img_path = Path(image_input)
            try:
                pil_img = Image.open(img_path).convert("RGB")
                return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            except Exception:
                img = cv2.imread(str(img_path))
                if img is None:
                    raise ValueError(f"Unable to read image from path: {image_input}")
                return img
        elif isinstance(image_input, Image.Image):
            rgb = image_input.convert("RGB")
            return cv2.cvtColor(np.array(rgb), cv2.COLOR_RGB2BGR)
        elif isinstance(image_input, np.ndarray):
            return image_input
        else:
            raise TypeError(f"Unsupported image input type: {type(image_input)}")

    def get_embedding(
        self, image_input: Union[Path, str, Image.Image, np.ndarray]
    ) -> Tuple[Optional[np.ndarray], dict]:
        """
        Extract the primary 512-D ArcFace facial embedding and detection telemetry.
        """
        self._load()
        img = self._to_cv2(image_input)
        faces = self._app.get(img)
        if not faces:
            return None, {"detected": False, "count": 0, "det_score": 0.0, "norm": 0.0}

        # Sort faces by detection score descending
        faces = sorted(faces, key=lambda f: getattr(f, "det_score", 0.0), reverse=True)
        primary = faces[0]
        raw_emb = getattr(primary, "embedding", None)
        det_score = float(getattr(primary, "det_score", 0.0))

        if raw_emb is not None:
            embedding = np.asarray(raw_emb, dtype=np.float32).flatten()
            norm = float(np.linalg.norm(embedding))
            return embedding, {
                "detected": True,
                "count": len(faces),
                "det_score": det_score,
                "norm": norm,
            }

        return None, {"detected": True, "count": len(faces), "det_score": det_score, "norm": 0.0}

    def analyze(self, image_path: Path):
        """
        Full facial topology analysis for forensic reporting.
        """
        self._load()
        img = self._to_cv2(image_path)
        faces = self._app.get(img)

        embedding_generated = False
        det_score = 0.0
        norm = 0.0
        face_boxes = []
        landmarks = []

        if faces:
            faces = sorted(faces, key=lambda f: getattr(f, "det_score", 0.0), reverse=True)
            primary = faces[0]
            if getattr(primary, "embedding", None) is not None:
                embedding_generated = True
                emb = np.asarray(primary.embedding, dtype=np.float32).flatten()
                norm = float(np.linalg.norm(emb))
                det_score = float(getattr(primary, "det_score", 0.0))

            for face in faces:
                if hasattr(face, "bbox") and face.bbox is not None:
                    face_boxes.append([float(x) for x in face.bbox])
                if hasattr(face, "kps") and face.kps is not None:
                    landmarks.append([[float(x), float(y)] for x, y in face.kps])

        return {
            "detected": len(faces) > 0,
            "count": len(faces),
            "embedding_generated": embedding_generated,
            "det_score": det_score,
            "norm": norm,
            "face_boxes": face_boxes,
            "landmarks": landmarks,
        }
