// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract ProvenanceRegistry {
    struct Record {
        bytes32 imageHash;
        bytes32 metadataHash;
        uint256 timestamp;
        address submitter;
    }

    mapping(bytes32 => Record) public records;

    event RecordRegistered(
        bytes32 indexed imageHash,
        bytes32 metadataHash,
        uint256 timestamp,
        address indexed submitter
    );

    function registerRecord(
        bytes32 imageHash,
        bytes32 metadataHash
    ) external {
        records[imageHash] = Record(
            imageHash,
            metadataHash,
            block.timestamp,
            msg.sender
        );

        emit RecordRegistered(
            imageHash,
            metadataHash,
            block.timestamp,
            msg.sender
        );
    }

    function getRecord(bytes32 imageHash)
        external
        view
        returns (Record memory)
    {
        return records[imageHash];
    }
}
