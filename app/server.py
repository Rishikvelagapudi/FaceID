import base64
import os
import uuid
from pathlib import Path
from typing import Optional, Union, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.pipeline import FaceIDPipeline
from blockchain.blockchain import LocalBlockchain

app = FastAPI(
    title="FaceID API",
    description="FaceID: Biometric Provenance, OSINT Social Attribution & Dual-Layer Blockchain Forensic API",
    version="2.0.0",
)

# Enable CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

pipeline = FaceIDPipeline()
local_chain = LocalBlockchain()

UPLOAD_DIR = Path("data/input")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Base64ImageRequest(BaseModel):
    image_base64: str
    write_blockchain: Optional[bool] = False
    threshold: Optional[float] = None
    top_k: Optional[int] = None

class UrlImageRequest(BaseModel):
    url: str

@app.get("/health")
@app.get("/api/health")
def health_check():
    valid, err = local_chain.is_valid_chain()
    return {
        "status": "online",
        "service": "FaceID Forensic API",
        "version": "2.0.0",
        "blockchain_layer1": {
            "valid": valid,
            "chain_length": len(local_chain),
        },
    }

@app.get("/api/diagnose")
def diagnose_system():
    diag = {}
    try:
        import psutil
        mem = psutil.virtual_memory()
        diag["memory_total_mb"] = round(mem.total / 1024 / 1024, 1)
        diag["memory_available_mb"] = round(mem.available / 1024 / 1024, 1)
    except Exception as e:
        diag["memory_error"] = str(e)

    diag["serpapi_configured"] = bool(os.getenv("SERPAPI_API_KEY") or os.getenv("SERPAPI_KEY"))
    diag["sepolia_rpc_configured"] = bool(os.getenv("RPC_URL"))
    diag["wallet_configured"] = bool(os.getenv("WALLET_ADDRESS"))
    diag["private_key_configured"] = bool(os.getenv("PRIVATE_KEY"))

    try:
        import cv2
        import numpy as np
        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        diag["opencv_numpy"] = "OK"
    except Exception as e:
        diag["opencv_numpy"] = str(e)

    try:
        valid, err = local_chain.is_valid_chain()
        diag["blockchain"] = {"valid": valid, "length": len(local_chain), "err": err}
    except Exception as e:
        diag["blockchain_error"] = str(e)

    try:
        enc = pipeline.face_encoder
        enc._load()
        emb, info = enc.get_embedding(dummy)
        diag["face_encoder"] = {"status": "OK", "model": enc.model_name, "info": info}
    except Exception as e:
        diag["face_encoder_error"] = str(e)

    try:
        df = pipeline.deepfake_classifier
        from PIL import Image
        pil_dummy = Image.fromarray(dummy)
        res = df.analyze(pil_dummy)
        diag["deepfake_classifier"] = {"status": "OK", "model": res.get("model")}
    except Exception as e:
        diag["deepfake_classifier_error"] = str(e)

    return diag

@app.post("/analyse")
@app.post("/api/verify")
def analyse_image(
    file: UploadFile = File(...),
    write_blockchain: Optional[Union[bool, str]] = Form(None),
    write_blockchain_query: Optional[Union[bool, str]] = Query(None, alias="write_blockchain"),
    threshold: Optional[float] = Query(None, description="Cosine similarity threshold"),
    top_k: Optional[int] = Query(None, description="Max candidate results to inspect"),
):
    """
    Primary investigative endpoint:
    Uploads an image, extracts 512-D ArcFace embedding, runs live Google Lens visual search,
    re-verifies candidate faces with cosine similarity, isolates social post URLs,
    runs ViT deepfake risk evaluation, deterministically hashes evidence,
    and logs to Layer 1 local blockchain (+ optional Layer 2 Sepolia).
    """
    try:
        raw_wb = write_blockchain if write_blockchain is not None else write_blockchain_query
        wb = False
        if isinstance(raw_wb, bool):
            wb = raw_wb
        elif isinstance(raw_wb, str):
            wb = raw_wb.strip().lower() in ("true", "1", "yes")

        file_ext = Path(file.filename).suffix or ".jpg"
        temp_filename = f"upload_{uuid.uuid4().hex[:8]}{file_ext}"
        temp_path = UPLOAD_DIR / temp_filename

        contents = file.file.read()
        temp_path.write_bytes(contents)

        if threshold is not None:
            pipeline.similarity_threshold = float(threshold)

        result = pipeline.run(
            image_path=temp_path,
            write_blockchain=wb,
            max_results=top_k,
            verbose=False,
        )

        return JSONResponse(content=result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/verify-base64")
def verify_image_base64(req: Base64ImageRequest):
    """
    Webcam live capture endpoint.
    """
    try:
        b64_data = req.image_base64
        if "," in b64_data:
            b64_data = b64_data.split(",", 1)[1]

        image_bytes = base64.b64decode(b64_data)
        temp_filename = f"webcam_{uuid.uuid4().hex[:8]}.jpg"
        temp_path = UPLOAD_DIR / temp_filename
        temp_path.write_bytes(image_bytes)

        if req.threshold is not None:
            pipeline.similarity_threshold = float(req.threshold)

        result = pipeline.run(
            image_path=temp_path,
            write_blockchain=bool(req.write_blockchain),
            max_results=req.top_k,
            verbose=False,
        )

        return JSONResponse(content=result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/load-url")
def load_image_url(req: UrlImageRequest):
    """
    Fetch an image from an external URL server-side (bypassing browser CORS)
    and return as base64 data URI for frontend canvas display.
    """
    url = (req.url or "").strip()
    if not url:
        raise HTTPException(status_code=400, detail="Empty image URL provided.")
    if not (url.startswith("http://") or url.startswith("https://")):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http:// or https://")
    
    try:
        import requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        res = requests.get(url, headers=headers, timeout=12)
        if res.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to fetch image from URL: HTTP {res.status_code}")
        
        content_type = res.headers.get("content-type", "").lower()
        if "image" not in content_type:
            if not (res.content[:4] in (b'\xff\xd8\xff\xe0', b'\xff\xd8\xff\xe1') or res.content[:8] == b'\x89PNG\r\n\x1a\n' or res.content[:4] == b'RIFF'):
                raise HTTPException(status_code=400, detail=f"URL did not return a valid image format.")
            content_type = "image/jpeg"
        
        clean_mime = content_type.split(';')[0].strip() or "image/jpeg"
        b64 = base64.b64encode(res.content).decode("utf-8")
        data_uri = f"data:{clean_mime};base64,{b64}"
        return {"status": "ok", "data_uri": data_uri, "size_bytes": len(res.content)}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Error loading image URL: {str(exc)}")

@app.get("/chain")
def get_blockchain_ledger():
    """
    Fetch the entire local cryptographically linked hash ledger and validation status.
    """
    valid, err = local_chain.is_valid_chain()
    return {
        "status": "VALID" if valid else "INVALID",
        "error": err,
        "chain_length": len(local_chain),
        "blocks": local_chain.get_chain(),
    }

@app.get("/verify/{evidence_hash}")
def verify_hash_in_chain(evidence_hash: str):
    """
    Verify if a specific SHA-256 evidence hash exists within a mathematically valid local block.
    """
    valid, err = local_chain.is_valid_chain()
    block = local_chain.verify_evidence_hash(evidence_hash)
    if not block:
        raise HTTPException(status_code=404, detail=f"Evidence hash {evidence_hash} not found in blockchain ledger.")

    return {
        "verified": valid,
        "match": True,
        "evidence_hash": evidence_hash,
        "block": block,
    }

# Mount static directory for forensic terminal web interface
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/")
def serve_index():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "FaceID Forensic API is running. Web UI not found."}

@app.get("/team")
def serve_team():
    team_file = static_dir / "team.html"
    if team_file.exists():
        return FileResponse(str(team_file))
    return {"message": "Team page not found."}
