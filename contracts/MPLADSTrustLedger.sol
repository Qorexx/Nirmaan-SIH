// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title MPLADSTrustLedger
 * @dev Immutable audit trail for MPLADS project milestones and funding
 */
contract MPLADSTrustLedger {
    
    address public admin;

    struct ProjectRecord {
        bytes32 dataHash;
        uint256 sanctionedAmount;
        uint256 createdAt;
        bool isActive;
    }

    struct ProgressUpdate {
        uint8 progressPercentage;
        bytes32 evidenceHash; // IPFS or local hash of physical evidence
        uint256 timestamp;
    }

    // Mappings
    mapping(bytes32 => ProjectRecord) public projects;
    mapping(bytes32 => ProgressUpdate[]) public projectProgress;
    mapping(bytes32 => bytes32[]) public transactionHashes; // Maps projectId to funding TX hashes

    // Events for indexing
    event ProjectSanctioned(bytes32 indexed projectId, bytes32 dataHash, uint256 amount);
    event ProgressRecorded(bytes32 indexed projectId, uint8 percentage, bytes32 evidenceHash);
    event FundsReleased(bytes32 indexed projectId, bytes32 txHash, uint256 amount);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Not authorized");
        _;
    }

    constructor() {
        admin = msg.sender;
    }

    /**
     * @dev Records initial project sanction data
     */
    function sanctionProject(bytes32 _projectId, bytes32 _dataHash, uint256 _amount) external onlyAdmin {
        require(!projects[_projectId].isActive, "Project already exists");
        
        projects[_projectId] = ProjectRecord({
            dataHash: _dataHash,
            sanctionedAmount: _amount,
            createdAt: block.timestamp,
            isActive: true
        });

        emit ProjectSanctioned(_projectId, _dataHash, _amount);
    }

    /**
     * @dev Records physical progress verified by ML Vision Oracle
     */
    function updateProgress(bytes32 _projectId, uint8 _percentage, bytes32 _evidenceHash) external onlyAdmin {
        require(projects[_projectId].isActive, "Project does not exist");
        require(_percentage <= 100, "Invalid percentage");

        projectProgress[_projectId].push(ProgressUpdate({
            progressPercentage: _percentage,
            evidenceHash: _evidenceHash,
            timestamp: block.timestamp
        }));

        emit ProgressRecorded(_projectId, _percentage, _evidenceHash);
    }

    /**
     * @dev Audits/Retrieves the latest progress hash for verification
     */
    function getLatestProgressHash(bytes32 _projectId) external view returns (bytes32) {
        uint256 len = projectProgress[_projectId].length;
        require(len > 0, "No progress recorded");
        return projectProgress[_projectId][len - 1].evidenceHash;
    }
}
