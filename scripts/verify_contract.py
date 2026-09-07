import os
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ETHERSCAN_API_KEY = os.getenv("ETHERSCAN_API_KEY")
CONTRACT_ADDRESS = os.getenv("CONTRACT_ADDRESS")

def verify_contract():
    if not ETHERSCAN_API_KEY or ETHERSCAN_API_KEY.startswith("your_"):
        print("ERROR: ETHERSCAN_API_KEY is not configured in .env")
        return

    if not CONTRACT_ADDRESS or CONTRACT_ADDRESS.startswith("0xyour_"):
        print("ERROR: CONTRACT_ADDRESS is not set in .env")
        return

    contract_path = Path("contracts/ProvenanceRegistry.sol")
    if not contract_path.exists():
        print("ERROR: ProvenanceRegistry.sol not found")
        return

    source = contract_path.read_text(encoding="utf-8")

    url = "https://api-sepolia.etherscan.io/api"
    payload = {
        "apikey": ETHERSCAN_API_KEY,
        "module": "contract",
        "action": "verifysourcecode",
        "contractaddress": CONTRACT_ADDRESS,
        "sourceCode": source,
        "codeformat": "solidity-single-file",
        "contractname": "ProvenanceRegistry",
        "compilerversion": "v0.8.20+commit.a1b79de6",
        "optimizationUsed": "0",
    }

    print(f"Submitting contract verification for {CONTRACT_ADDRESS} on Etherscan Sepolia...")
    try:
        response = requests.post(url, data=payload, timeout=20)
        res = response.json()
        print(f"Etherscan Status: {res.get('status')}")
        print(f"Etherscan Result: {res.get('result')}")
    except Exception as exc:
        print(f"Verification request failed: {exc}")

if __name__ == "__main__":
    verify_contract()
