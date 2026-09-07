import argparse
import os
import sys
from pathlib import Path

def run_server(port: int = 8000, host: str = "127.0.0.1"):
    import uvicorn
    uvicorn.run("app.server:app", host=host, port=port, reload=False)

def run_pipeline(image_path: Path, write_blockchain: bool = True, max_results: int = None, threshold: float = None):
    from app.pipeline import FaceIDPipeline

    pipeline = FaceIDPipeline()
    if threshold is not None:
        pipeline.similarity_threshold = threshold

    result = pipeline.run(
        image_path,
        write_blockchain=write_blockchain,
        max_results=max_results,
    )

    print("\n" + "=" * 64)
    print("FACEID FORENSIC VERIFICATION COMPLETE")
    print("=" * 64)
    print(f"Status             : {result['verification']['status']}")
    print(f"Face detected      : {result['face']['detected']}")
    print(f"Face count         : {result['face']['count']}")
    print(f"SHA-256            : {result['image']['sha256']}")
    print(f"pHash              : {result['image']['phash']}")
    print(f"Search results     : {result['reverse_search']['count']}")
    print(f"Best similarity    : {result['verification']['best_similarity']:.4f}")
    print(f"Report             : {result['report_path']}")

    blockchain = result.get("blockchain")
    if blockchain and blockchain.get("submitted"):
        print(f"Network            : {blockchain['network']}")
        print(f"Transaction        : {blockchain['tx_hash']}")
        print(f"Explorer           : {blockchain['explorer_url']}")
    else:
        print("Blockchain         : NOT SUBMITTED")

    print("=" * 64)
    return result

def main():
    default_port = int(os.getenv("PORT", "8000"))
    default_host = os.getenv("HOST", "0.0.0.0" if os.getenv("PORT") else "127.0.0.1")

    parser = argparse.ArgumentParser(
        description="FaceID — Biometric Provenance & OSINT Forensic Pipeline"
    )
    parser.add_argument("--image", type=str, default=None, help="Path to input face image")
    parser.add_argument("--serve", action="store_true", help="Launch interactive Web UI & REST API")
    parser.add_argument("--port", type=int, default=default_port, help=f"Port to bind server (default: {default_port})")
    parser.add_argument("--host", type=str, default=default_host, help=f"Host address (default: {default_host})")
    parser.add_argument("--no-blockchain", action="store_true", help="Skip blockchain registration")
    parser.add_argument("--top-k", "--max-results", type=int, default=None, dest="top_k", help="Max search candidates to inspect")
    parser.add_argument("--threshold", type=float, default=None, help="Minimum cosine similarity threshold")
    parser.add_argument("--log-level", type=str, default="INFO", help="Logging level")
    args = parser.parse_args()

    if args.serve:
        print(f"Starting FaceID on http://{args.host}:{args.port}...")
        run_server(port=args.port, host=args.host)
        return

    if args.image:
        img_path = Path(args.image)
        if not img_path.exists():
            print(f"ERROR: Target image not found: {img_path}")
            sys.exit(1)

        run_pipeline(
            image_path=img_path,
            write_blockchain=not args.no_blockchain,
            max_results=args.top_k,
            threshold=args.threshold,
        )
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
