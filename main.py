import argparse
import json
import sys
from pathlib import Path

from app.pipeline import FaceIDPipeline

def main():
    parser = argparse.ArgumentParser(
        description="FaceID - image provenance and biometric verification pipeline"
    )
    parser.add_argument("--image", required=True, help="Path to input image")
    parser.add_argument("--no-blockchain", action="store_true",
                        help="Run verification without submitting a blockchain transaction")
    parser.add_argument("--max-results", type=int, default=None)
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"ERROR: Image not found: {image_path}")
        sys.exit(1)

    pipeline = FaceIDPipeline()
    try:
        result = pipeline.run(
            image_path,
            write_blockchain=not args.no_blockchain,
            max_results=args.max_results,
        )
    except Exception as exc:
        print(f"\nERROR: {exc}")
        sys.exit(1)

    print("\n" + "=" * 64)
    print("FACEID VERIFICATION COMPLETE")
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
        print(f"Explorer            : {blockchain['explorer_url']}")
    else:
        print("Blockchain         : NOT SUBMITTED")

    print("=" * 64)

if __name__ == "__main__":
    main()
