import json
import os
from pathlib import Path

from dotenv import load_dotenv
from solcx import compile_standard, install_solc
from web3 import Web3

load_dotenv()

RPC = os.getenv("SEPOLIA_RPC_URL")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

if not RPC or not PRIVATE_KEY:
    raise RuntimeError("Set SEPOLIA_RPC_URL and PRIVATE_KEY in .env")

contract_path = Path("contracts/ProvenanceRegistry.sol")
source = contract_path.read_text(encoding="utf-8")

install_solc("0.8.20")

compiled = compile_standard(
    {
        "language": "Solidity",
        "sources": {
            "ProvenanceRegistry.sol": {"content": source}
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "evm.bytecode"]
                }
            }
        },
    },
    solc_version="0.8.20",
)

artifact = compiled["contracts"]["ProvenanceRegistry.sol"]["ProvenanceRegistry"]
abi = artifact["abi"]
bytecode = artifact["evm"]["bytecode"]["object"]

w3 = Web3(Web3.HTTPProvider(RPC))
if not w3.is_connected():
    raise RuntimeError("RPC connection failed.")

account = w3.eth.account.from_key(PRIVATE_KEY)
contract = w3.eth.contract(abi=abi, bytecode=bytecode)

nonce = w3.eth.get_transaction_count(account.address)
tx = contract.constructor().build_transaction({
    "from": account.address,
    "nonce": nonce,
    "chainId": w3.eth.chain_id,
    "gas": 1000000,
    "maxFeePerGas": w3.to_wei("30", "gwei"),
    "maxPriorityFeePerGas": w3.to_wei("1", "gwei"),
})

signed = account.sign_transaction(tx)
tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

address = receipt.contractAddress
print("Contract deployed:", address)
print("Transaction:", tx_hash.hex())

abi_path = Path("app/blockchain/abi.json")
abi_path.parent.mkdir(parents=True, exist_ok=True)
abi_path.write_text(json.dumps(abi, indent=2), encoding="utf-8")

print("\nAdd this to .env:")
print(f"CONTRACT_ADDRESS={address}")
