from pathlib import Path
from blockchain.blockchain import LocalBlockchain

def test_local_blockchain_lifecycle(tmp_path: Path):
    chain_file = tmp_path / "test_chain.json"
    chain = LocalBlockchain(chain_path=chain_file)

    assert len(chain) == 1
    assert chain.get_chain()[0]["index"] == 0

    # Add forensic block
    evidence = {
        "evidence_hash": "a" * 64,
        "source_image": "test.jpg",
        "match": True
    }
    block1 = chain.add_block(evidence)
    assert block1["index"] == 1
    assert len(chain) == 2
    assert block1["previous_hash"] == chain.get_chain()[0]["hash"]

    # Verify validity
    valid, err = chain.is_valid_chain()
    assert valid is True
    assert err is None

    # Search for evidence hash
    found = chain.verify_evidence_hash("a" * 64)
    assert found is not None
    assert found["index"] == 1

def test_local_blockchain_tamper_detection(tmp_path: Path):
    chain_file = tmp_path / "tamper_chain.json"
    chain = LocalBlockchain(chain_path=chain_file)
    chain.add_block({"evidence_hash": "1" * 64})

    # Tamper with block data
    chain.chain[1]["evidence_record"]["evidence_hash"] = "2" * 64
    valid, err = chain.is_valid_chain()
    assert valid is False
    assert "mismatch" in err.lower()
