import base64
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.pipeline import FaceProofPipeline
from blockchain.blockchain import LocalBlockchain

app = FastAPI(
    title="face-chain API",
    description="Biometric Provenance, OSINT Social Attribution & Dual-Layer Blockchain Forensic API",
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

pipeline = FaceProofPipeline()
local_chain = LocalBlockchain()

UPLOAD_DIR = Path("data/input")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

class Base64ImageRequest(BaseModel):
    image_base64: str
    write_blockchain: Optional[bool] = False
    threshold: Optional[float] = None
    top_k: Optional[int] = None

@app.get("/health")
@app.get("/api/health")
def health_check():
    valid, err = local_chain.is_valid_chain()
    return {
        "status": "online",
        "service": "face-chain Forensic API",
        "version": "2.0.0",
        "blockchain_layer1": {
            "valid": valid,
            "chain_length": len(local_chain),
        },
    }

@app.post("/analyse")
@app.post("/api/verify")
async def analyse_image(
    file: UploadFile = File(...),
    write_blockchain: bool = False,
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
        file_ext = Path(file.filename).suffix or ".jpg"
        temp_filename = f"upload_{uuid.uuid4().hex[:8]}{file_ext}"
        temp_path = UPLOAD_DIR / temp_filename

        contents = await file.read()
        temp_path.write_bytes(contents)

        if threshold is not None:
            pipeline.similarity_threshold = float(threshold)

        result = pipeline.run(
            image_path=temp_path,
            write_blockchain=write_blockchain,
            max_results=top_k,
            verbose=False,
        )

        return JSONResponse(content=result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

@app.post("/api/verify-base64")
async def verify_image_base64(req: Base64ImageRequest):
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
            write_blockchain=req.write_blockchain,
            max_results=req.top_k,
            verbose=False,
        )

        return JSONResponse(content=result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))

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
    return {"message": "face-chain Forensic API is running. Web UI not found."}
