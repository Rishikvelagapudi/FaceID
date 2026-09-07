import hashlib
import json
import os
import time
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional, Union

DEFAULT_CHAIN_FILE = Path("chain/blockchain.json")

def compute_block_hash(index: int, timestamp: float, previous_hash: str, evidence_record: Dict[str, Any]) -> str:
    """
    Deterministically hash block contents using SHA-256.
    """
    canonical_record = json.dumps(evidence_record, sort_keys=True, separators=(",", ":"))
    payload = f"{index}|{timestamp:.6f}|{previous_hash}|{canonical_record}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()

class LocalBlockchain:
    """
    Layer 1 Local Cryptographically Linked Hash Ledger.
    Provides zero-cost, high-throughput, offline-capable forensic proof of existence.
    """

    def __init__(self, chain_path: Union[Path, str] = DEFAULT_CHAIN_FILE):
        self.chain_path = Path(chain_path)
        self.chain: List[Dict[str, Any]] = []
        self._load_or_init()

    def _load_or_init(self):
        self.chain_path.parent.mkdir(parents=True, exist_ok=True)
        if self.chain_path.exists():
            try:
                data = json.loads(self.chain_path.read_text(encoding="utf-8"))
                if isinstance(data, list) and len(data) > 0:
                    self.chain = data
                    valid, err = self.is_valid_chain()
                    if not valid:
                        print(f"[WARN] Local blockchain integrity warning: {err}")
                    return
            except Exception as exc:
                print(f"[WARN] Failed to load local chain from {self.chain_path}: {exc}. Reinitializing.")

        # Create Genesis Block
        genesis = self._create_genesis_block()
        self.chain = [genesis]
        self._save()

    def _create_genesis_block(self) -> Dict[str, Any]:
        timestamp = 1726000000.0
        prev_hash = "0" * 64
        record = {
            "title": "FaceID Genesis Block",
            "protocol": "FaceID Biometric Provenance Ledger v2.0",
            "status": "INITIALIZED",
        }
        b_hash = compute_block_hash(0, timestamp, prev_hash, record)
        return {
            "index": 0,
            "timestamp": timestamp,
            "evidence_record": record,
            "previous_hash": prev_hash,
            "hash": b_hash,
        }

    def _save(self):
        self.chain_path.parent.mkdir(parents=True, exist_ok=True)
        self.chain_path.write_text(
            json.dumps(self.chain, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def add_block(self, evidence_record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Append a new verified forensic record to the local blockchain ledger.
        """
        import copy
        latest = self.chain[-1]
        index = latest["index"] + 1
        timestamp = time.time()
        prev_hash = latest["hash"]
        sealed_record = copy.deepcopy(evidence_record)
        b_hash = compute_block_hash(index, timestamp, prev_hash, sealed_record)

        block = {
            "index": index,
            "timestamp": timestamp,
            "evidence_record": sealed_record,
            "previous_hash": prev_hash,
            "hash": b_hash,
        }

        self.chain.append(block)
        self._save()
        return block

    def is_valid_chain(self) -> Tuple[bool, Optional[str]]:
        """
        Verify the mathematical integrity and continuous link hashes of the entire chain.
        """
        if not self.chain:
            return False, "Chain is empty"

        for i in range(len(self.chain)):
            block = self.chain[i]
            expected_hash = compute_block_hash(
                block["index"],
                block["timestamp"],
                block["previous_hash"],
                block["evidence_record"]
            )
            if block["hash"] != expected_hash:
                return False, f"Hash mismatch at block index {i}: expected {expected_hash}, got {block['hash']}"

            if i > 0:
                prev_block = self.chain[i - 1]
                if block["previous_hash"] != prev_block["hash"]:
                    return False, f"Broken link at block index {i}: previous_hash does not match prior block hash"

        return True, None

    def verify_evidence_hash(self, evidence_hash: str) -> Optional[Dict[str, Any]]:
        """
        Search for an evidence SHA-256 fingerprint within the verified chain.
        """
        for block in self.chain:
            record = block.get("evidence_record", {})
            # Look for matching hash in various evidence attributes
            if (
                record.get("evidence_hash") == evidence_hash
                or record.get("metadata_sha256") == evidence_hash
                or record.get("image_sha256") == evidence_hash
                or block["hash"] == evidence_hash
            ):
                return block
        return None

    def get_chain(self) -> List[Dict[str, Any]]:
        return self.chain

    def __len__(self) -> int:
        return len(self.chain)
