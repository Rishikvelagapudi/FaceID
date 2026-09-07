import json
import os
from pathlib import Path

from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

ABI_PATH = Path(__file__).resolve().parent / "abi.json"

class BlockchainRegistry:
    def __init__(self):
        self.rpc = os.getenv("RPC_URL") or os.getenv("SEPOLIA_RPC_URL")
        self.private_key = os.getenv("PRIVATE_KEY")
        self.contract_address = os.getenv("CONTRACT_ADDRESS")

        if not self.rpc or not self.private_key or "your_" in self.private_key:
            raise RuntimeError(
                "Valid RPC_URL (or SEPOLIA_RPC_URL) and PRIVATE_KEY are required for blockchain anchoring."
            )

        self.w3 = Web3(Web3.HTTPProvider(self.rpc))
        if not self.w3.is_connected():
            raise RuntimeError(f"Unable to connect to the configured Ethereum RPC: {self.rpc}")

        self.account = self.w3.eth.account.from_key(self.private_key)

        # Optional smart contract mode
        self.contract = None
        if self.contract_address and not self.contract_address.startswith("0xyour_"):
            try:
                checksummed = Web3.to_checksum_address(self.contract_address)
                abi = json.loads(ABI_PATH.read_text(encoding="utf-8"))
                self.contract = self.w3.eth.contract(address=checksummed, abi=abi)
            except Exception:
                self.contract = None

    def register(self, image_sha256: str, metadata_sha256: str):
        nonce = self.w3.eth.get_transaction_count(self.account.address)
        chain_id = self.w3.eth.chain_id

        # Mode A: Smart Contract Registry
        if self.contract:
            image_hash = bytes.fromhex(image_sha256)
            metadata_hash = bytes.fromhex(metadata_sha256)
            tx = self.contract.functions.registerRecord(
                image_hash,
                metadata_hash
            ).build_transaction({
                "from": self.account.address,
                "nonce": nonce,
                "chainId": chain_id,
                "gas": 250000,
                "maxFeePerGas": self.w3.to_wei("30", "gwei"),
                "maxPriorityFeePerGas": self.w3.to_wei("1", "gwei"),
            })
        else:
            # Mode B: EVM Calldata Proof of Existence (PoE) self-transaction
            calldata = metadata_sha256.encode("utf-8")
            tx = {
                "from": self.account.address,
                "to": self.account.address,
                "value": 0,
                "nonce": nonce,
                "chainId": chain_id,
                "data": calldata,
                "gas": 60000,
                "maxFeePerGas": self.w3.to_wei("30", "gwei"),
                "maxPriorityFeePerGas": self.w3.to_wei("1", "gwei"),
            }

        signed = self.account.sign_transaction(tx)
        tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)

        tx_hex = tx_hash.hex()
        return {
            "submitted": True,
            "network": "Ethereum Sepolia",
            "tx_hash": tx_hex,
            "block_number": receipt.blockNumber,
            "explorer_url": f"https://sepolia.etherscan.io/tx/{tx_hex}",
        }
