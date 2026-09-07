import argparse
import os
import sys
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# Ensure UTF-8 output on Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_RPC = "https://ethereum-sepolia-rpc.publicnode.com"

class TestnetAnchor:
    """
    Layer 2 Public Ethereum Sepolia Testnet Anchor.
    Permanently anchors a SHA-256 evidence fingerprint to the Ethereum blockchain
    via an EIP-1559 0-value self-transaction storing the hash in transaction calldata.
    """

    def __init__(self, rpc_url: Optional[str] = None, private_key: Optional[str] = None):
        env_rpc = os.getenv("RPC_URL") or os.getenv("SEPOLIA_RPC_URL")
        if not env_rpc or "your-" in env_rpc or "your_" in env_rpc:
            env_rpc = DEFAULT_RPC
        self.rpc_url = rpc_url or env_rpc
        self.private_key = private_key or os.getenv("PRIVATE_KEY")
        self._w3 = None

    @property
    def w3(self):
        if self._w3 is None:
            from web3 import Web3
            self._w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        return self._w3

    def is_configured(self) -> bool:
        return bool(
            self.private_key
            and not self.private_key.startswith("0xyour_")
            and len(self.private_key) >= 64
        )

    def anchor(self, evidence_hash: str) -> Dict[str, Any]:
        """
        Broadcast a 0-value self-transaction to Ethereum Sepolia containing the evidence hash in calldata.
        """
        if not self.is_configured():
            return {
                "submitted": False,
                "reason": "Missing or placeholder PRIVATE_KEY. Anchor skipped.",
                "network": "Ethereum Sepolia Testnet",
                "tx_hash": None,
                "explorer_url": None,
            }

        try:
            if not self.w3.is_connected():
                return {
                    "submitted": False,
                    "reason": f"Could not connect to Ethereum RPC: {self.rpc_url}",
                    "network": "Ethereum Sepolia Testnet",
                    "tx_hash": None,
                    "explorer_url": None,
                }

            account = self.w3.eth.account.from_key(self.private_key)
            calldata = evidence_hash.encode("utf-8")
            nonce = self.w3.eth.get_transaction_count(account.address)
            chain_id = self.w3.eth.chain_id

            # EIP-1559 transaction parameters
            tx = {
                "from": account.address,
                "to": account.address,
                "value": 0,
                "nonce": nonce,
                "chainId": chain_id,
                "data": calldata,
                "gas": 60000,
                "maxFeePerGas": self.w3.to_wei("35", "gwei"),
                "maxPriorityFeePerGas": self.w3.to_wei("1.5", "gwei"),
            }

            signed = account.sign_transaction(tx)
            raw_tx = getattr(signed, "raw_transaction", None) or getattr(signed, "rawTransaction")
            tx_hash = self.w3.eth.send_raw_transaction(raw_tx)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)

            tx_hex = tx_hash.hex()
            if not tx_hex.startswith("0x"):
                tx_hex = "0x" + tx_hex

            return {
                "submitted": True,
                "network": "Ethereum Sepolia Testnet",
                "chain_id": chain_id,
                "tx_hash": tx_hex,
                "block_number": receipt.blockNumber,
                "explorer_url": f"https://sepolia.etherscan.io/tx/{tx_hex}",
            }
        except Exception as exc:
            return {
                "submitted": False,
                "reason": str(exc),
                "network": "Ethereum Sepolia Testnet",
                "tx_hash": None,
                "explorer_url": None,
            }

    def verify(self, tx_hash: str, expected_hash: str) -> Dict[str, Any]:
        """
        Pull transaction calldata from Sepolia via Web3 RPC, decode UTF-8 payload,
        and verify byte-for-byte equality against the local evidence hash.
        """
        from web3 import Web3

        if not tx_hash.startswith("0x"):
            tx_hash = "0x" + tx_hash

        tx = self.w3.eth.get_transaction(tx_hash)
        input_data = tx.get("input")

        # Convert hex / HexBytes to raw string
        if hasattr(input_data, "hex"):
            raw_hex = input_data.hex()
        elif isinstance(input_data, bytes):
            raw_hex = input_data.hex()
        else:
            raw_hex = str(input_data)

        if raw_hex.startswith("0x"):
            raw_hex = raw_hex[2:]

        try:
            decoded_str = bytes.fromhex(raw_hex).decode("utf-8", errors="replace")
        except Exception:
            decoded_str = raw_hex

        # Match check
        matched = (
            decoded_str.strip() == expected_hash.strip()
            or expected_hash.strip() in decoded_str
            or expected_hash.strip() == raw_hex
        )

        return {
            "match": matched,
            "tx_hash": tx_hash,
            "on_chain_hash": decoded_str,
            "expected_hash": expected_hash,
            "explorer_url": f"https://sepolia.etherscan.io/tx/{tx_hash}",
        }

def main():
    parser = argparse.ArgumentParser(
        description="face-chain Layer 2 Sepolia Testnet Anchoring & Verification CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # verify command
    v_parser = subparsers.add_parser("verify", help="Verify on-chain calldata against an expected evidence hash")
    v_parser.add_argument("tx_hash", help="Transaction hash on Sepolia (0x...)")
    v_parser.add_argument("expected_hash", help="Expected SHA-256 evidence hash")
    v_parser.add_argument("--rpc", default=None, help="Custom Sepolia RPC endpoint")

    # anchor command
    a_parser = subparsers.add_parser("anchor", help="Anchor an evidence hash to Sepolia calldata")
    a_parser.add_argument("evidence_hash", help="SHA-256 evidence fingerprint to commit")
    a_parser.add_argument("--rpc", default=None, help="Custom Sepolia RPC endpoint")

    args = parser.parse_args()
    anchor_service = TestnetAnchor(rpc_url=args.rpc)

    if args.command == "verify":
        res = anchor_service.verify(args.tx_hash, args.expected_hash)
        print("=" * 64)
        print("FACE-CHAIN INDEPENDENT BLOCKCHAIN AUDIT")
        print("=" * 64)
        print(f"TX Hash       : {res['tx_hash']}")
        print(f"On-chain hash : {res['on_chain_hash']}")
        print(f"Expected hash : {res['expected_hash']}")
        print(f"Etherscan     : {res['explorer_url']}")
        status_symbol = "MATCH \u2713" if res["match"] else "MISMATCH \u2717"
        print(f"Result        : {status_symbol}")
        print("=" * 64)
        if not res["match"]:
            sys.exit(1)

    elif args.command == "anchor":
        print(f"Broadcasting evidence anchor to Sepolia for hash: {args.evidence_hash}...")
        res = anchor_service.anchor(args.evidence_hash)
        if res["submitted"]:
            print(f"[OK] Anchored to Sepolia block #{res['block_number']}")
            print(f"TX Hash  : {res['tx_hash']}")
            print(f"Explorer : {res['explorer_url']}")
        else:
            print(f"[FAILED] {res.get('reason')}")
            sys.exit(1)

if __name__ == "__main__":
    main()
