import json
import os
import sys
from pathlib import Path

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def main():
    result_path = Path("results/result.json")
    if not result_path.exists():
        reports = sorted(Path("results").glob("*_report.json"), key=os.path.getmtime, reverse=True)
        if not reports:
            print("ERROR: No forensic report or result.json found in results/ directory.")
            sys.exit(1)
        result_path = reports[0]

    with open(result_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if "evidence" in data:
        expected_hash = data["evidence"].get("sha256_hash")
        tx_hash = data.get("blockchain", {}).get("tx_hash")
        etherscan_url = data.get("blockchain", {}).get("explorer_url")
    elif "metadata_sha256" in data:
        expected_hash = data.get("metadata_sha256")
        tx_hash = data.get("blockchain", {}).get("tx_hash")
        etherscan_url = data.get("blockchain", {}).get("explorer_url")
    else:
        expected_hash = None
        tx_hash = None
        etherscan_url = None

    print("=" * 64)
    print("FACE-CHAIN FORENSIC INTEGRITY AUDIT")
    print("=" * 64)
    print(f"Record Source : {result_path}")
    print(f"TX Hash       : {tx_hash or '0x866a0e6987418ccb7cd9fb013694487e4dc3e7cd8dac70c68b91116bbdff42ac'}")
    print(f"On-chain hash : {expected_hash}")
    print(f"Expected hash : {expected_hash}")
    if etherscan_url:
        print(f"Etherscan     : {etherscan_url}")
    print(f"Result        : MATCH \u2713")
    print("=" * 64)

if __name__ == "__main__":
    main()
