# COMPREHENSIVE PROJECT CONTEXT: SIH 2026 - MPLADS FRAUD DETECTION PLATFORM

## 1. PROJECT ORIGINS (NIRMAAN X402)
The project originally began as "Nirmaan x402," a decentralized, AI-driven Escrow Protocol built to eliminate corruption in public infrastructure projects. 
Governments spend billions on infrastructure, but funds are lost to corruption due to human verification bottlenecks (bribery, forged documents). 
Nirmaan solved this by locking project funds in an immutable smart contract vault. Money was only released when a Multi-Oracle Consensus independently verified physical milestone completion.

### The Original 5-Step Flow
1. The Smart Vault: Government deposits funds into a blockchain smart contract.
2. Data Capture: Contractor completes a milestone and uploads cryptographic, geo-tagged proof via a portal.
3. The x402 Gateway: System intercepts requests using HTTP 402, paying micro-fees for AI access.
4. Multi-Oracle Consensus: Gemini analyzes images for structural defects; IoT telemetry checks heavy machinery engine hours.
5. Autonomous Payout: Smart contract executes payout upon consensus, logs to Supabase, generates PDF audit.

### The "Twin-Ledger" Approach
To satisfy government regulatory compliance, the blockchain does not hold real fiat. It acts as an "Immutable Logic Engine" holding cryptographic proof. 
Upon AI approval, the state changes to `APPROVED`, firing a secure webhook to the government's Public Financial Management System (PFMS) for actual INR payout via DBT/NEFT.

---

## 2. TARGET PROBLEM STATEMENT (SIH26102)
Organization: Ministry of Statistics and Programme Implementation (MoSPI)
Category: Software | Theme: Miscellaneous

The Members of Parliament Local Area Development Scheme (MPLADS) allows MPs to recommend developmental works. The Scheme involves massive fund utilization across multiple agencies. 
There is a critical need for an AI-powered solution to leverage machine learning and advanced analytics to detect trends, anomalies in expenditure, fund utilization, cost estimates, and work execution.

Expected Solution:
- Identify trends, anomalies, irregularities, and potential fraud in fund utilization.
- Analyze data relating to sanctions, expenditures, cost estimates, work progress, payments, and asset creation.
- Detect unusual patterns, cost overruns, duplicate works, delayed projects, and deviations.
- Generate risk-based alerts, predictive insights, and decision-support dashboards.
- Facilitate automated compliance monitoring and early warning mechanisms.

---

## 3. ADVANCED TECHNICAL ARCHITECTURE (MODULES 1-4)

### Module 1: Multimodal Data Processing
Receipt & Invoice Audit: Utilizes LayoutLMv3 or Donut for OCR-free document understanding to parse Vendor Name, GSTIN, Line Items, Unit Prices, and Date.
NLP Duplicate Cross-Checking: Project descriptions are converted into semantic vector embeddings using Sentence-BERT. A FAISS vector database compares incoming proposals against historical databases.

### Module 2: Computer Vision & Geospatial Validation
Satellite & Geo-tagged Photo Verification: EXIF metadata is validated against geofences. Sentinel-2 and PlanetScope fetch temporal imagery.
CNN Land Cover Change Detection: Siamesed Convolutional Neural Networks (Siamese CNNs) process "Before" and "After" satellite images to highlight pixel-level structural changes to catch "Ghost Projects."

### Module 3: Machine Learning Anomaly Detection
Fraud & Risk Scoring Engine: XGBoost & Isolation Forests analyze structured attributes (completion timelines, cost variations, contractor history).
Graph Neural Network (GNN): Relational data in Neo4j (Nodes: Contractors, MPs, Districts; Edges: Payments, Bids) processed by Graph Convolutional Networks (GCNs) to detect Circular Collusion and Shared Attributes.

### Module 4: Interactive Governance Dashboard
- Geospatial Heatmaps: Mapbox GL / PostGIS spatial queries.
- Automated Alerts: Webhooks + Celery background tasks.
- Audit Log Trail: Immutable PostgreSQL / Hash chain logs.

---

## 4. TEAM DIVISION OF LABOR

### Person 1 — Financial AI / Anomaly Detection
- Clean and analyze financial/project data.
- Compare estimated cost, sanctioned amount, funds released, expenditure, payments, and work progress.
- Detect unusual spending patterns and payment behavior.
- Build an Anomaly Detection ML model (Isolation Forest).
- Generate an anomaly/risk score + reason for each suspicious project.

### Person 2 — Predictive AI / Early Warning
- Analyze project progress, duration, expenditure, payments, location, project type.
- Build a Cost Overrun Prediction model.
- Build a Project Delay Prediction model.
- Generate risk scores and reasons for predictions using XGBoost/Random Forest and SHAP.

### Person 3 — Duplicate & Similarity Detection AI
- Analyze project names and descriptions using NLP/embeddings.
- Compare project locations using latitude/longitude.
- Find projects with high textual similarity using Sentence Transformers + FAISS.
- Generate a duplicate probability/score and explain the overlap.

### Person 4 — Data Engineering & Database
- Collect/prepare MPLADS project and financial datasets.
- Design the PostgreSQL + PostGIS database for spatial querying.
- Feature Engineering: Fund utilization %, Cost overrun %, Progress vs expenditure, Days elapsed.
- Build the pipeline: Raw Data -> Cleaning -> Feature Eng -> PostgreSQL.

### Person 5 — Blockchain & Trust Layer (Partially User)
- Adapt existing Nirmaan blockchain architecture for MPLADS Trust Ledger.
- Record project approval, sanction, fund release, payment, progress update, completion.
- Store hashes, timestamps, project IDs on-chain.
- Build a tamper-detection mechanism comparing DB records with blockchain hashes.
- Develop smart contracts for project milestones.

### Person 6 — Backend, Risk Engine & Integration Lead (User)
- Build the FastAPI backend and core routing architecture.
- Connect PostgreSQL database with ML APIs and Blockchain.
- Build the Unified Risk Engine: Combine outputs from Persons 1–3 into one overall risk score.
- Generate explainable alerts and recommended actions.
- Integrate the blockchain verification system.
- Provide unified REST APIs for the Frontend developer.

### Frontend Developer (Role 7)
- Consume REST APIs provided by Person 6.
- Build interactive UI using Next.js/React.
- Render Mapbox GL geospatial heatmaps.
- Display detailed project pages with Risk Scores and Blockchain verification badges.

---

## 5. DATABASE ARCHITECTURE (POSTGRESQL / POSTGIS DDL)
The following defines the raw relational structure required for the integration layer.

```sql
-- Enable PostGIS for geospatial queries
CREATE EXTENSION IF NOT EXISTS postgis;

-- 1. Agencies / Contractors
CREATE TABLE agencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gstin VARCHAR(15) UNIQUE NOT NULL,
    agency_name VARCHAR(255) NOT NULL,
    bank_account_hash VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(20),
    risk_rating DECIMAL(5,2) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Projects (MPLADS Core Data)
CREATE TABLE projects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    mp_id VARCHAR(50) NOT NULL,
    project_title TEXT NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    estimated_cost DECIMAL(15,2) NOT NULL,
    sanctioned_amount DECIMAL(15,2) NOT NULL,
    state_nodal_agency VARCHAR(255) NOT NULL,
    district_authority VARCHAR(255) NOT NULL,
    agency_id UUID REFERENCES agencies(id),
    location GEOMETRY(Point, 4326),
    start_date DATE NOT NULL,
    expected_end_date DATE NOT NULL,
    current_progress_pct INTEGER DEFAULT 0 CHECK (current_progress_pct >= 0 AND current_progress_pct <= 100),
    status VARCHAR(50) DEFAULT 'SANCTIONED',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Transactions / Fund Utilization
CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    transaction_type VARCHAR(50) NOT NULL, -- e.g., 'DISBURSEMENT', 'EXPENDITURE'
    amount DECIMAL(15,2) NOT NULL,
    transaction_date TIMESTAMP WITH TIME ZONE NOT NULL,
    reference_id VARCHAR(255) UNIQUE NOT NULL,
    pfms_status VARCHAR(50) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. ML Alerts & Risk Cache
CREATE TABLE ml_risk_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    financial_risk_score INTEGER NOT NULL,
    delay_risk_score INTEGER NOT NULL,
    cost_overrun_risk_score INTEGER NOT NULL,
    duplicate_risk_score INTEGER NOT NULL,
    overall_risk_score INTEGER NOT NULL,
    overall_risk_level VARCHAR(20) NOT NULL,
    ai_recommendation TEXT NOT NULL,
    flagged_anomalies JSONB,
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Blockchain Audit Ledger
CREATE TABLE blockchain_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id UUID REFERENCES projects(id) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    local_data_hash VARCHAR(256) NOT NULL,
    onchain_tx_hash VARCHAR(256) NOT NULL,
    block_number BIGINT NOT NULL,
    verified boolean DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

---

## 6. BLOCKCHAIN TRUST LAYER (SOLIDITY SMART CONTRACT)
The following details the on-chain registry used to verify database integrity.

```solidity
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
```

---

## 7. INTERNAL API CONTRACTS (FASTAPI & ML INTEGRATION)
These JSON schemas dictate exactly how Persons 1, 2, and 3 must return their ML inferences to Person 6's Risk Engine.

### 7.1 Financial Anomaly Payload (Person 1)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Financial Anomaly Report",
  "type": "object",
  "properties": {
    "project_id": { "type": "string" },
    "anomaly_score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "risk_classification": { "type": "string", "enum": ["LOW", "MEDIUM", "HIGH"] },
    "detected_patterns": {
      "type": "array",
      "items": { "type": "string" }
    },
    "expenditure_variance": { "type": "number" }
  },
  "required": ["project_id", "anomaly_score", "risk_classification"]
}
```

### 7.2 Predictive Delay/Cost Payload (Person 2)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Predictive Risk Report",
  "type": "object",
  "properties": {
    "project_id": { "type": "string" },
    "delay_risk_score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "predicted_delay_days": { "type": "integer" },
    "cost_overrun_risk_score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "predicted_final_cost": { "type": "number" },
    "shap_explanations": {
      "type": "object",
      "additionalProperties": { "type": "number" }
    }
  },
  "required": ["project_id", "delay_risk_score", "cost_overrun_risk_score"]
}
```

### 7.3 Duplicate NLP Payload (Person 3)
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Duplicate Detection Report",
  "type": "object",
  "properties": {
    "project_id": { "type": "string" },
    "is_flagged": { "type": "boolean" },
    "max_similarity_score": { "type": "integer", "minimum": 0, "maximum": 100 },
    "similar_projects": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "related_id": { "type": "string" },
          "faiss_distance": { "type": "number" },
          "shared_keywords": { "type": "array", "items": { "type": "string" } }
        }
      }
    }
  }
}
```

---

## 8. UNIFIED RISK ENGINE ALGORITHM (PERSON 6)
The backend integration calculates the final programmatic risk using a weighted heuristic function.

```python
# Pseudo-code for FastAPI Integration Core
def calculate_unified_risk(fin_payload, pred_payload, dup_payload, blockchain_status):
    # Weights defined by MoSPI risk appetite guidelines
    WEIGHT_FINANCIAL = 0.35
    WEIGHT_DELAY = 0.20
    WEIGHT_COST = 0.20
    WEIGHT_DUPLICATE = 0.25

    # Extract base scores
    s_fin = fin_payload.get('anomaly_score', 0)
    s_del = pred_payload.get('delay_risk_score', 0)
    s_cost = pred_payload.get('cost_overrun_risk_score', 0)
    s_dup = dup_payload.get('max_similarity_score', 0)

    # Base Weighted Score
    base_score = (s_fin * WEIGHT_FINANCIAL) + \
                 (s_del * WEIGHT_DELAY) + \
                 (s_cost * WEIGHT_COST) + \
                 (s_dup * WEIGHT_DUPLICATE)

    # Critical Multipliers
    if dup_payload.get('is_flagged') == True:
        base_score = min(100, base_score * 1.5) # Duplicate works highly penalize the project
        
    if blockchain_status == False:
        base_score = 100 # Immediate highest risk if data integrity is compromised
        
    # Classification Boundary
    if base_score >= 75:
        level = "HIGH"
    elif base_score >= 40:
        level = "MEDIUM"
    else:
        level = "LOW"
        
    return {
        "overall_score": int(base_score),
        "risk_level": level,
        "is_blockchain_verified": blockchain_status
    }
```

---

## 9. FASTAPI BACKEND BOILERPLATE (PERSON 6)
To accelerate the hackathon, the following is the exact FastAPI architecture expected for the integration layer.

### `main.py`
```python
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas, crud, risk_engine
from .database import engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MPLADS Risk Engine Analytics",
    description="Backend integration layer for ML modules and Blockchain verification.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/v1/projects/{project_id}/analyze", response_model=schemas.RiskAnalysisResponse)
async def analyze_project(project_id: str, db: Session = Depends(get_db)):
    # 1. Fetch project data from PostgreSQL
    project = crud.get_project(db, project_id=project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # 2. Asynchronously call ML APIs (Persons 1, 2, 3)
    # In a real environment, this would use httpx for async requests
    fin_risk = await risk_engine.call_financial_ml(project_id)
    pred_risk = await risk_engine.call_predictive_ml(project_id)
    dup_risk = await risk_engine.call_duplicate_ml(project_id)

    # 3. Verify Blockchain Integrity
    is_verified = await risk_engine.verify_blockchain_hash(project_id)

    # 4. Compute Unified Risk
    final_risk = risk_engine.calculate_unified_risk(
        fin_risk, pred_risk, dup_risk, is_verified
    )

    # 5. Log the alert in DB
    crud.create_ml_alert(db, project_id, final_risk)

    return final_risk
```

### `schemas.py`
```python
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class MLScoreBase(BaseModel):
    score: int = Field(..., ge=0, le=100)
    risk_level: str
    reason: str

class FinancialMLScore(MLScoreBase):
    expenditure_variance: float

class PredictiveMLScore(MLScoreBase):
    predicted_delay_days: int
    predicted_final_cost: float

class DuplicateProjectInfo(BaseModel):
    related_id: str
    faiss_distance: float
    shared_keywords: List[str]

class DuplicateMLScore(BaseModel):
    is_flagged: bool
    max_similarity_score: int
    similar_projects: List[DuplicateProjectInfo]

class RiskAnalysisResponse(BaseModel):
    project_id: str
    financial_risk: FinancialMLScore
    predictive_risk: PredictiveMLScore
    duplicate_risk: DuplicateMLScore
    blockchain_integrity: bool
    overall_risk_score: int = Field(..., ge=0, le=100)
    overall_risk_level: str
    recommended_action: str
    calculated_at: datetime
```

## 10. GRAPH DATABASE SPECIFICATION (NEO4J CYPHER)
For advanced collusion detection (Person 1 / Person 4), the following Cypher queries form the basis of the Graph Convolutional Network (GCN) feature extraction.

### Node and Edge Definitions
- `(:Contractor {gstin, name, risk_score})`
- `(:MP {mp_id, name, constituency})`
- `(:Project {project_id, category, status})`
- `(:BankAccount {account_hash})`

**Relationships:**
- `(Contractor)-[:BID_ON]->(Project)`
- `(Contractor)-[:AWARDED]->(Project)`
- `(MP)-[:RECOMMENDED]->(Project)`
- `(Contractor)-[:USES_ACCOUNT]->(BankAccount)`

### Query 1: Finding Shared Bank Accounts (Shell Companies)
```cypher
MATCH (c1:Contractor)-[:USES_ACCOUNT]->(b:BankAccount)<-[:USES_ACCOUNT]-(c2:Contractor)
WHERE id(c1) < id(c2)
RETURN c1.name, c2.name, b.account_hash
```

### Query 2: Finding Circular Bidding Rings
```cypher
MATCH path = (c1:Contractor)-[:BID_ON]->(p:Project)<-[:AWARDED]-(c2:Contractor)
WHERE c1.gstin <> c2.gstin
WITH c1, c2, count(p) as co_bids
WHERE co_bids > 3
RETURN c1.name, c2.name, co_bids
ORDER BY co_bids DESC
```

These queries generate the adjacency matrices required by the GCN to flag systemic, multi-project collusion which cannot be caught by single-project linear ML models.
