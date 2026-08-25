# NIRMAAN — MPLADS AI Monitoring & Compliance Platform

> **NIRMAAN** — An AI-driven monitoring platform for detecting statistical irregularities, duplicate works, project delays, cost escalation, and compliance risks in MPLADS implementation.

[![SIH 2026](https://img.shields.io/badge/SIH-2026-blue)](https://www.sih.gov.in/)
[![Problem Statement](https://img.shields.io/badge/PS-SIH26102-orange)](https://sih.gov.in/sih2026PS)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)](https://fastapi.tiangolo.com/)
[![AI/ML](https://img.shields.io/badge/AI%2FML-XGBoost%20%7C%20Isolation%20Forest%20%7C%20Sentence--Transformers-purple)](https://huggingface.co/sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)
[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL-336791)](https://www.postgresql.org/)
[![Solidity](https://img.shields.io/badge/Blockchain-Solidity-363636)](https://soliditylang.org/)

---

## 1. SIH Problem Statement

### SIH26102 — Development of an AI-powered system to detect anomalies, fraud, and inefficiencies in MPLAD Scheme implementation

**Organization:** Ministry of Statistics and Programme Implementation (MoSPI)  
**Category:** Software  
**Theme:** Miscellaneous

The Members of Parliament Local Area Development Scheme (MPLADS) involves large-scale recommendation, sanction, funding, and execution of developmental works through multiple administrative and implementing agencies.

The SIH problem requires an AI-powered monitoring and analytics platform capable of analyzing project and financial information to identify:

- Trends and anomalies in fund utilization
- Unusual expenditure patterns
- Cost overruns
- Duplicate or overlapping works
- Delayed or stalled projects
- Deviations between physical progress and financial activity
- Irregularities requiring administrative attention
- Risk-based alerts and predictive insights
- Decision-support dashboards for MPs, State Nodal Authorities, District Authorities, and the Ministry

The official problem statement specifically calls for AI/ML and advanced analytics to improve transparency, accountability, monitoring efficiency, and early identification of potential irregularities.

---

# 2. Our Solution

NIRMAAN approaches MPLADS monitoring as a **multi-signal risk and compliance problem** rather than relying on a single rule or model.

The repository contains several independently developed components that can be integrated into a unified monitoring platform:

1. **MPLADS data ingestion**
   - Extracts project records from the public MPLADS dashboard API.
   - Cleans monetary and date fields.
   - Removes duplicate work records.

2. **Financial anomaly detection**
   - Uses an Isolation Forest model on approved project-level features.
   - Produces statistical anomaly signals and explainable domain-rule findings.
   - Explicitly distinguishes statistical anomalies from confirmed fraud.

3. **Predictive early warning**
   - Uses XGBoost models to predict project delay and final project cost.
   - Uses SHAP to identify important contributing factors.
   - Converts predictions into actionable warning triggers.

4. **Duplicate and similarity detection**
   - Uses multilingual Sentence Transformers to create semantic project embeddings.
   - Uses FAISS for candidate retrieval.
   - Combines text similarity with geographical proximity, project category, and execution-period overlap.

5. **Rules and compliance engine**
   - Converts ML outputs into human-readable compliance alerts.
   - Classifies projects into states such as `CRITICAL_ALERT`, `HIGH_RISK`, `NEEDS_ATTENTION`, and `ON_TRACK`.

6. **Database layer**
   - Provides PostgreSQL/SQLAlchemy models for projects, agencies, transactions, compliance alerts, and blockchain ledger records.

7. **Blockchain trust layer**
   - Provides a Solidity `MPLADSTrustLedger` contract for recording project hashes, sanctioned amounts, progress evidence hashes, and funding events.
   - Provides a Python Web3 bridge for integrity verification.

8. **Government-facing dashboard**
   - Provides a static HTML/CSS/JavaScript prototype with stakeholder-specific views for Ministry, State, District, and MP users.
   - Includes bilingual English/Hindi interface logic.

The current repository is therefore best understood as a **multi-module SIH prototype**, where some modules are implemented end-to-end while others are integration-ready or represented through UI/prototype components.

---

# 3. Key Features

## Core Features

- MPLADS project data extraction from the public dashboard API
- Data cleaning and duplicate-record validation
- Project-level statistical anomaly detection
- Predictive delay forecasting
- Predictive cost-overrun estimation
- Semantic duplicate-project detection
- Geospatial similarity scoring
- Category similarity scoring
- Temporal overlap analysis
- Rule-based compliance alerts
- PostgreSQL data model
- Blockchain-backed project integrity architecture
- Government-oriented monitoring dashboard
- Stakeholder persona switching
- English/Hindi dashboard terminology
- REST APIs for ML modules
- Swagger/OpenAPI documentation through FastAPI

## AI/ML Features

### Financial Anomaly Detection

- Isolation Forest
- Three engineered model features
- Model anomaly score
- Domain-rule explanations
- Configurable anomaly thresholds

### Predictive Early Warning

- XGBoost delay model
- XGBoost cost model
- SHAP-based explanations
- Delay and cost-overrun trigger generation

### Duplicate Detection

- `paraphrase-multilingual-MiniLM-L12-v2`
- Dense text embeddings
- FAISS vector retrieval
- Haversine geographical similarity
- Category taxonomy
- Temporal Jaccard overlap
- Weighted composite duplicate score

## Dashboard Features

- Project search
- High-risk project view
- Compliance alert feed
- Stakeholder persona views
- Project metadata
- Physical-vs-financial progress presentation
- Blockchain verification indicators
- Satellite/drone verification UI placeholders
- Contractor relationship-analysis UI placeholder

The repository's current static dashboard explicitly labels several advanced visualization areas as placeholders, so those components are not presented here as completed production functionality.

---

# 4. Innovation & USP

## 4.1 Multi-signal rather than single-rule detection

NIRMAAN does not treat a single unusual field as sufficient evidence of an irregular project.

The duplicate detector combines:

```text
Semantic Similarity
        +
Geographical Proximity
        +
Category Similarity
        +
Execution Period Overlap
        ↓
Potential Duplicate Score
```

The score is generated using configurable weights and automatically redistributes weights when an input signal is unavailable.

## 4.2 Explainable AI

The system is designed to return not only predictions but also reasons for those predictions.

Examples include:

- Top SHAP factors for delay
- Top SHAP factors for cost prediction
- Statistical anomaly rules
- Text similarity
- Geographic distance
- Category match
- Temporal overlap

This makes the system more suitable for administrative decision support than a black-box risk score.

## 4.3 Early warning instead of post-facto analysis

The predictive module generates concrete outputs such as:

- Predicted delay in days
- Predicted cost overrun in ₹
- Predicted final cost
- Actionable warning triggers

The implementation also generates warnings for stalled projects, excessive timeline deviation, and significant predicted cost escalation.

## 4.4 Immutable audit architecture

The blockchain component provides a mechanism for recording project data hashes and milestone evidence hashes independently of the mutable application database.

The Solidity contract supports project sanction records, progress updates, evidence hashes, and funding-event structures.

## 4.5 Government-oriented interface

The prototype is designed around the actual stakeholder hierarchy described by the SIH problem:

- Ministry / Central Executive
- State Nodal Authority
- District Authority
- Member of Parliament

The dashboard also includes bilingual English/Hindi terminology and accessibility-oriented UI controls.

---

# 5. System Architecture

The repository currently contains several independently runnable services rather than one completely consolidated production deployment.

```mermaid
flowchart TB

    A[MPLADS Public Dashboard API]
    B[MPLADS Data Pipeline]
    C[Cleaned Project Dataset]

    D[Financial Anomaly Engine]
    E[Predictive Early Warning Engine]
    F[Duplicate & Similarity AI]

    G[FastAPI Rules & Alert Backend]
    H[(PostgreSQL)]
    I[Blockchain Trust Ledger]

    J[Static Government Dashboard]
    K[Risk & Compliance Alerts]

    A --> B
    B --> C

    C --> D
    C --> E
    C --> F

    D --> G
    E --> G
    F --> G

    G --> H
    G --> I
    G --> K

    H --> J
    K --> J
    I --> J
```

### Implemented architecture

- `mplads_pipeline.py` provides the MPLADS ingestion pipeline.
- `ml_modules/financial/` contains the financial anomaly pipeline.
- `Nirmaan_Predictive_ai/` contains the predictive AI service.
- `duplicate-ml/` contains the duplicate-detection FastAPI service.
- Root `main.py` provides the central rules/alert backend.
- PostgreSQL is represented through SQLAlchemy models and Docker Compose.
- `contracts/MPLADSTrustLedger.sol` provides the Solidity trust ledger.
- Static HTML dashboards provide the current user-facing prototype.

---

# 6. End-to-End Workflow

```mermaid
flowchart LR

    A[Public MPLADS Data] --> B[Data Collection]
    B --> C[Cleaning & Validation]

    C --> D1[Financial Features]
    C --> D2[Predictive Features]
    C --> D3[Project Text + Location + Dates]

    D1 --> E1[Isolation Forest + Rules]
    D2 --> E2[XGBoost Delay/Cost Models]
    D3 --> E3[Sentence Transformer + FAISS]

    E1 --> F[Rules & Alert Engine]
    E2 --> F
    E3 --> F

    F --> G[(PostgreSQL)]
    F --> H[Blockchain Integrity Layer]
    F --> I[Government Dashboard]

    E2 --> J[SHAP Explanations]
    E3 --> K[Duplicate Evidence]
    E1 --> L[Anomaly Reasons]

    J --> I
    K --> I
    L --> I
```

### Step 1 — Data Collection

The repository contains a pipeline targeting the MPLADS public dashboard API:

```text
https://mplads.mospi.gov.in/rest/PreLoginDashboardData/getTilesReportData
```

The pipeline queries three work categories:

- Works Sanctioned
- Works Recommended
- Works Completed

across state IDs 1–36 for the Lok Sabha house configuration.

### Step 2 — Cleaning

The pipeline:

- Normalizes column names
- Converts sanction amounts to numeric values
- Parses date columns
- Removes duplicate records based on `work_recommendation_dtl_id` and query category

The cleaned data is written to `mplads_projects.csv`.

### Step 3 — Financial Analysis

Financial records are filtered and transformed into approved anomaly-detection features.

### Step 4 — Predictive Analysis

The predictive module processes project, cost, timeline, contractor-history, environmental, and progress-related features.

### Step 5 — Duplicate Analysis

Project titles and descriptions are converted into multilingual embeddings. Candidate projects are retrieved using FAISS and then evaluated using four similarity signals.

### Step 6 — Compliance Logic

The root FastAPI backend converts incoming ML findings into structured compliance alerts.

### Step 7 — Storage

PostgreSQL models store projects, agencies, transactions, alerts, and blockchain ledger references.

### Step 8 — Trust Verification

The Web3 bridge can compare locally generated project hashes with records associated with the Solidity trust ledger.

### Step 9 — Dashboard

The static dashboard presents project risk, alerts, stakeholder views, and verification indicators.

---

# 7. Technology Stack

| Layer | Technologies |
|---|---|
| Frontend / Prototype UI | HTML5, CSS3, JavaScript |
| Backend | Python, FastAPI, Uvicorn |
| Database | PostgreSQL, SQLAlchemy, psycopg2 |
| Financial AI | scikit-learn Isolation Forest, NumPy, pandas |
| Predictive AI | XGBoost, scikit-learn |
| Explainability | SHAP |
| NLP | Sentence Transformers |
| Vector Search | FAISS |
| Geospatial Analysis | Haversine distance |
| Temporal Analysis | `python-dateutil`, Jaccard overlap |
| Validation | Pydantic |
| Blockchain | Solidity, Web3.py |
| Data Collection | Requests, pandas |
| Containerization | Docker, Docker Compose |
| Testing | pytest |
| Environment Management | python-dotenv |

The root dependency file contains FastAPI, Uvicorn, Pydantic, SQLAlchemy, PostgreSQL support, Web3, HTTPX, NumPy, pandas, scikit-learn, Requests, pytest, and python-dotenv.

The predictive module separately specifies XGBoost, SHAP, scikit-learn, pandas, NumPy, joblib, FastAPI, Uvicorn, and Pydantic.

---

# 8. AI / ML Implementation

## 8.1 Financial Anomaly Detection

### Model

**Isolation Forest**

The implementation uses:

```text
IsolationForest(
    contamination="auto",
    n_estimators=200,
    random_state=42
)
```

### Features

The current model contract uses exactly three features:

| Feature | Description |
|---|---|
| `log1p_sanction_amount` | Log-transformed sanction amount |
| `rec_to_sanc_days` | Days between recommendation and sanction |
| `days_since_tenure_start` | Days from MP tenure start to recommendation |

The implementation deliberately does not use `StandardScaler` because the model is tree-based.

### Inference

The inference pipeline:

1. Validates the project record.
2. Extracts the project identifier.
3. Derives model features.
4. Loads the trained Isolation Forest.
5. Calculates the model anomaly score.
6. Obtains the raw Isolation Forest prediction.
7. Applies domain-specific anomaly rules.
8. Produces an explainable structured result.

The implementation explicitly treats an anomaly as a **statistical/project irregularity**, not proof of fraud or corruption.

### Current anomaly rule examples

The rule engine includes configurable thresholds for:

- Unusually long recommendation-to-sanction delay
- Unusually high sanction amount
- Early-tenure recommendation
- Multi-signal statistical anomaly
- Model-detected statistical anomaly

The current approved model-score cutoff is `-0.093716`.

---

## 8.2 Predictive Early Warning

The predictive module contains:

- XGBoost cost model
- XGBoost delay model
- Shared preprocessing pipeline
- Serialized model artifacts
- SHAP explanation utility
- FastAPI inference API

The repository documentation describes a synthetic MPLADS dataset containing 5,000 records for the predictive pipeline.

### Input features

The API validates fields including:

- State
- Constituency type
- Project category
- Estimated cost
- Sanctioned amount
- Expected duration
- Elapsed duration
- Physical progress
- Contractor historical delays
- Monsoon overlap
- Material inflation
- Labour shortage
- Terrain difficulty
- Sanction year



### Output

The API returns:

```json
{
  "project_id": "...",
  "forecasts": {
    "predicted_delay_days": 0,
    "predicted_cost_overrun_amount": 0,
    "predicted_final_cost": 0
  },
  "explanations": {
    "top_delay_factors": [],
    "top_cost_factors": []
  },
  "actionable_triggers": []
}
```

The service generates explicit triggers rather than relying exclusively on an abstract risk score.

---

## 8.3 Duplicate & Similarity Detection

The duplicate module is one of the most complete AI components in the repository.

### Model

```text
sentence-transformers/
└── paraphrase-multilingual-MiniLM-L12-v2
```

The model produces normalized dense embeddings and computes cosine similarity between project text representations.

### Pipeline

```text
Project Title + Description
          ↓
Sentence Transformer
          ↓
Normalized Embedding
          ↓
FAISS Candidate Retrieval
          ↓
┌─────────────────────────────┐
│ Text Similarity             │
│ Location Similarity         │
│ Category Similarity         │
│ Temporal Similarity         │
└─────────────────────────────┘
          ↓
Weighted Composite Score
          ↓
Risk Tier + Explanation
```

### Score

The default weights are:

| Signal | Weight |
|---|---:|
| Text similarity | 50% |
| Location proximity | 25% |
| Category match | 15% |
| Temporal overlap | 10% |

Missing signals are automatically excluded and their weights are redistributed proportionally.

### Risk tiers

| Score | Classification |
|---:|---|
| 90–100 | Critical Review |
| 75–89 | Very High |
| 60–74 | High |
| 40–59 | Moderate |
| 0–39 | Low |



### FAISS candidate retrieval

The duplicate detector:

1. Embeds the project corpus.
2. Builds a FAISS `IndexFlatIP`.
3. Retrieves the top 15 candidates per project.
4. Applies an embedding pre-filter of `0.20`.
5. Calculates the complete four-signal score.
6. Removes duplicate pairs.
7. Sorts results by potential duplicate score.



---

# 9. Data Pipeline

```text
MPLADS Public Dashboard API
            ↓
       HTTP Collection
            ↓
       JSON Extraction
            ↓
       pandas DataFrame
            ↓
 Column Normalization
            ↓
 Monetary / Date Parsing
            ↓
 Duplicate Removal
            ↓
       Clean Dataset
       ┌────┼────┐
       ↓    ↓    ↓
 Financial Predictive Duplicate
   AI       AI       AI
       └────┼────┘
            ↓
    Rules / Alert Layer
            ↓
       PostgreSQL
            ↓
   Dashboard / Decision Support
```

## Data source

The repository contains an extraction script targeting the MPLADS public dashboard endpoint:

`getTilesReportData`

The pipeline adds a `QUERY_CATEGORY` field so that records can be distinguished by whether they came from Works Sanctioned, Works Recommended, or Works Completed queries.

## Data validation

The financial module contains dedicated validation logic for:

- Required identifiers
- Monetary values
- Date parsing
- Positive sanction amounts
- Timeline consistency
- Missing values
- Domain-specific warning conditions

The progress report documents a synthetic 500-row financial dataset used during model validation, including injected anomaly categories and integrity checks.

---

# 10. Repository Structure

The repository is a multi-module prototype rather than a single monolithic application.

```text
Nirmaan-SIH/
│
├── API responses/
├── Nirmaan-SIH/
├── Nirmaan_Predictive_ai/
│   ├── data/
│   ├── models/
│   ├── src/
│   │   ├── api.py
│   │   ├── data_generator.py
│   │   ├── shap_explainer.py
│   │   └── train_models.py
│   ├── Project_Progress_2.md
│   ├── README.md
│   ├── requirements.txt
│   └── run_pipeline.py
│
├── assets/
│
├── blockchain/
│
├── contracts/
│   └── MPLADSTrustLedger.sol
│
├── data/
│
├── docs/
│
├── duplicate-ml/
│   ├── schemas/
│   │   └── project.py
│   ├── services/
│   │   ├── category_similarity.py
│   │   ├── duplicate_detector.py
│   │   ├── embeddings.py
│   │   ├── explanation.py
│   │   ├── faiss_index.py
│   │   ├── location_similarity.py
│   │   ├── scoring.py
│   │   └── temporal_similarity.py
│   ├── tests/
│   │   └── test_services.py
│   ├── app.py
│   ├── requirements.txt
│   └── start.ps1
│
├── ml_modules/
│   └── financial/
│       ├── anomaly_model.py
│       ├── anomaly_rules.py
│       ├── data_loader.py
│       ├── data_validation.py
│       ├── inference.py
│       └── send_alert.py
│
├── scripts/
├── tests/
│
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── blockchain.py
├── contract_data.json
├── crud.py
├── dashboard.html
├── database.py
├── feature_engineering.py
├── gov_dashboard.html
├── gov_index.html
├── gov_script.js
├── gov_style.css
├── index.html
├── main.py
├── migrate_db.py
├── ml_integrator.py
├── models.py
├── mplads_api_test.py
├── mplads_pipeline.py
├── populate_db.py
├── requirements.txt
├── rules_engine.py
├── schemas.py
├── script.js
├── sih_context_full.md
├── style.css
└── validate_data.py
```

The top-level repository listing confirms the presence of the major data, AI, blockchain, contract, dashboard, testing, and deployment components.

---

# 11. Installation & Setup

Because the repository contains multiple services, each major component has its own startup path.

## Prerequisites

Recommended:

- Python 3.11+
- pip
- PostgreSQL 15+ or Docker
- Git
- Optional local Ethereum-compatible node for blockchain experiments

The root Dockerfile uses Python 3.11, while the repository's duplicate-detection documentation specifies Python 3.14 for that isolated service.

---

## Clone Repository

```bash
git clone https://github.com/Qorexx/Nirmaan-SIH.git
cd Nirmaan-SIH
```

---

## Root Backend

Create and activate a virtual environment:

### Windows

```powershell
python -m venv .venv
.venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The root backend uses FastAPI/Uvicorn, SQLAlchemy, PostgreSQL support, Web3.py, HTTPX, pandas, NumPy, scikit-learn, Requests, pytest, and python-dotenv.

Run:

```bash
uvicorn main:app --reload --port 8000
```

---

# 12. PostgreSQL Setup

The repository includes Docker Compose configuration for PostgreSQL 15.

```bash
docker compose up -d db
```

The configured database service uses:

```text
Database: mplads_db
Port:     5432
User:     postgres
```

The Docker Compose configuration also provides a persistent `postgres_data` volume.

The root backend defaults to:

```text
postgresql://postgres:postgres@localhost:5432/mplads_db
```

and can be overridden with `DATABASE_URL`.

---

# 13. Docker Setup

The repository contains:

- `Dockerfile`
- `docker-compose.yml`

The backend container exposes port `8000`, while PostgreSQL exposes `5432`.

Run:

```bash
docker compose up --build
```

> **Important:** the Docker Compose configuration currently provisions the root FastAPI backend and PostgreSQL. It does not automatically orchestrate the separate predictive-AI and duplicate-AI services.

---

# 14. Predictive AI Service

Navigate to:

```bash
cd Nirmaan_Predictive_ai
```

Install dependencies:

```bash
pip install -r requirements.txt
```

The repository provides a pipeline orchestrator:

```bash
python run_pipeline.py
```

The documented pipeline performs:

```text
Generate Data
      ↓
Train Models
      ↓
Save Model Artifacts
      ↓
Start FastAPI Service
```

The service exposes:

```text
http://localhost:8000
```

and Swagger documentation at:

```text
http://localhost:8000/docs
```



Alternative commands documented by the module:

```bash
python run_pipeline.py --no-serve
python run_pipeline.py --serve-only
python run_pipeline.py --records 10000 --port 8080
```



---

# 15. Duplicate Detection AI Service

Navigate to:

```bash
cd duplicate-ml
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the service:

```bash
uvicorn app:app --reload --port 8000
```

The first startup downloads the Sentence Transformer model into the Hugging Face cache.

Health check:

```text
http://localhost:8000/health
```

Swagger:

```text
http://localhost:8000/docs
```

Run tests:

```bash
pytest tests/ -v
```



---

# 16. Static Dashboard

The repository also contains a static HTML prototype.

Open:

```text
index.html
```

or serve the repository directory using a simple local HTTP server:

```bash
python -m http.server 8080
```

Then visit:

```text
http://localhost:8080/
```

The static dashboard currently operates using JavaScript mock project data rather than being a fully connected production frontend. The sample project data includes `PROJ-999` and `PROJ-101`.

---

# 17. Environment Variables

The repository contains `.env.example` and uses environment variables for database and blockchain configuration.

| Variable | Purpose | Required |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | For database-backed execution |
| `SUPABASE_URL` | Example PostgreSQL/Supabase connection string | Optional |
| `WEB3_PROVIDER_URL` | Ethereum-compatible RPC provider | For blockchain integration |
| `CONTRACT_ADDRESS` | Deployed trust-ledger contract address | For blockchain integration |

The `.env.example` currently provides a PostgreSQL/Supabase connection-string template.

The blockchain bridge reads `WEB3_PROVIDER_URL` and `CONTRACT_ADDRESS`, with local-development defaults.

**Never commit real credentials, database passwords, private keys, or API secrets.**

---

# 18. API Documentation

## 18.1 Root FastAPI Backend

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/projects/{project_id}/financial-anomaly` | Receive financial anomaly findings |
| POST | `/api/v1/projects/{project_id}/predictive-delay` | Receive predictive delay/cost findings |
| POST | `/api/v1/projects/{project_id}/duplicate-detection` | Receive duplicate detection findings |
| POST | `/api/v1/projects/{project_id}/trigger-ml` | Trigger external predictive/duplicate services |
| GET | `/api/v1/projects/{project_id}/dashboard` | Return project dashboard data |



### Financial anomaly payload

```json
{
  "project_id": "MPLADS-1234",
  "is_anomalous": true,
  "anomaly_features": [
    "model_detected_statistical_anomaly"
  ],
  "variance_amount_inr": null
}
```

### Predictive payload

```json
{
  "project_id": "MPLADS-1234",
  "predicted_delay_days": 45,
  "predicted_cost_overrun_inr": 500000,
  "shap_key_drivers": [
    "contractor_historical_delay"
  ]
}
```

### Duplicate payload

```json
{
  "project_id": "MPLADS-1234",
  "is_duplicate_flagged": true,
  "similarity_percentage": 92.5,
  "matched_historical_project_id": "PROJ-2022-001",
  "shared_keywords": [
    "water_treatment"
  ]
}
```

The schemas are defined in `schemas.py`.

---

# 19. Predictive AI API

### `POST /api/v1/predict-early-warning`

Accepts validated project features and returns:

- Predicted delay
- Predicted cost overrun
- Predicted final cost
- SHAP-derived top delay factors
- SHAP-derived top cost factors
- Actionable triggers



### `GET /health`

Returns model-loading status for the predictive service.

---

# 20. Duplicate Detection API

The standalone duplicate service exposes:

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Service health and model status |
| POST | `/compare-pair` | Compare two projects |
| POST | `/find-duplicates` | Scan a project corpus |
| POST | `/check-new-project` | Compare a new project against existing projects |



### Example response structure

```json
{
  "status": "success",
  "analysis": {
    "pair_id": "DUP-PROJ-A-PROJ-B",
    "potential_duplicate_score": 87,
    "risk_level": "VERY HIGH",
    "risk_badge": "🟠 Very High Overlap Risk",
    "explanation": "...",
    "reasons": [],
    "score_breakdown": {
      "text_similarity_percentage": 91,
      "location_proximity_percentage": 98,
      "distance_meters": 48.3,
      "category_match": 1.0,
      "time_overlap": 0.51
    }
  }
}
```

The exact response fields are generated by `duplicate_detector.py` and exposed by `app.py`.

---

# 21. User Interface / Demo

The repository contains two main UI concepts.

## Standard Project Dashboard

Files:

```text
index.html
dashboard.html
script.js
style.css
```

The dashboard provides:

- Project search
- Project status
- Compliance alerts
- Blockchain verification badge
- Geospatial verification container
- Financial analytics container
- NLP similarity container

Several advanced visualization sections are explicitly placeholders in the current implementation.

## Government Audit Command Center

Files:

```text
gov_index.html
gov_dashboard.html
gov_script.js
gov_style.css
```

The government dashboard provides:

- Ministry view
- State view
- District view
- MP view
- English/Hindi interface
- Audit command-center layout
- Compliance feed
- Project audit information
- Blockchain verification indicators
- Satellite/drone verification placeholders
- Contractor relationship-analysis placeholder



### Screenshot placeholders

If screenshots are added later, place them under:

```text
docs/screenshots/
```

and reference them as:

```md
![NIRMAAN Government Dashboard](docs/screenshots/government-dashboard.png)
```

No screenshot is claimed here because the repository does not currently provide a dedicated screenshot documentation set.

---

# 22. Security & Reliability

## Implemented

### Input validation

FastAPI/Pydantic schemas validate project input ranges such as:

- Positive project costs
- Positive sanctioned amount
- Non-negative elapsed days
- Progress between 0 and 100
- Valid categorical fields



### Database abstraction

SQLAlchemy provides the database model and session layer.

### Blockchain hashing

The Python blockchain bridge creates deterministic SHA-256 hashes from sorted project-data JSON before attempting blockchain verification.

### Smart-contract authorization

The Solidity trust ledger restricts state-changing functions using an `onlyAdmin` modifier.

### Error handling

FastAPI services return HTTP errors for inference failures and model-loading problems.

### Graceful database behavior

The root backend catches PostgreSQL `OperationalError` in several paths so the prototype can continue in mock/hackathon mode when the database is unavailable.

---

## Important Security Limitations

The current repository is an SIH prototype and is **not production-hardened**.

For example:

- CORS is currently configured with `allow_origins=["*"]`.
- Blockchain verification contains bypass behavior when the contract or Web3 provider is unavailable.
- Docker Compose contains development database credentials.
- No production authentication/authorization system is implemented.
- No rate limiting is implemented.
- No centralized secrets-management system is implemented.

These should be addressed before government production deployment.

---

# 23. Scalability & Deployment

## Currently Implemented

- Modular FastAPI services
- Independent ML microservice structure
- PostgreSQL persistence layer
- Dockerfile for root backend
- Docker Compose PostgreSQL + backend
- FAISS candidate retrieval for duplicate detection
- Serialized predictive model artifacts
- REST API boundaries between modules



## Proposed Production Scaling

For national-scale MPLADS deployment, the architecture can evolve toward:

```text
Government Data Sources
        ↓
API / Batch Ingestion Layer
        ↓
Message Queue
        ↓
Data Validation & Feature Pipeline
        ↓
┌───────────────┬────────────────┬─────────────────┐
│ Financial AI  │ Predictive AI  │ Duplicate AI    │
└───────────────┴────────────────┴─────────────────┘
        ↓
Unified Risk / Compliance Engine
        ↓
PostgreSQL + PostGIS
        ↓
Audit Ledger / Blockchain
        ↓
Government Dashboards
```

Potential production improvements:

- Containerized deployment of every ML service
- Kubernetes or equivalent orchestration
- Managed PostgreSQL
- PostGIS for spatial queries
- Redis caching
- Background task queues
- Centralized logging
- API gateway
- Authentication and RBAC
- Secrets manager
- Model monitoring
- Data-drift monitoring
- Model versioning
- Automated CI/CD
- Audit-grade observability

These are **proposed production enhancements**, not claims about the current deployment.

---

# 24. SIH Problem-Solution Alignment

| SIH Requirement / Challenge | NIRMAAN Implementation |
|---|---|
| Detect anomalies in MPLADS data | Isolation Forest + explainable financial rules |
| Detect unusual project patterns | Multi-signal anomaly and compliance analysis |
| Detect duplicate works | Sentence Transformer + FAISS similarity engine |
| Detect delayed projects | XGBoost delay prediction |
| Detect cost escalation | XGBoost final-cost prediction and overrun calculation |
| Explain AI findings | SHAP + deterministic rule explanations + similarity breakdown |
| Analyze project data | MPLADS API extraction and pandas-based processing |
| Generate risk-based alerts | Root FastAPI rules engine and severity classification |
| Provide predictive insights | Early-warning prediction service |
| Support decision making | Government-oriented dashboard and actionable triggers |
| Improve auditability | Blockchain trust-ledger architecture |
| Support multiple stakeholders | Ministry, State, District, and MP dashboard personas |
| Support compliance monitoring | Structured compliance-alert model |
| Improve monitoring efficiency | Automated data processing and AI-assisted prioritization |

The implementation therefore directly addresses the major analytical requirements of SIH26102, while some proposed capabilities such as satellite verification, GNN-based collusion detection, and a fully unified production dashboard remain future/integration scope rather than completed functionality.

---

# 25. Impact & Use Cases

## Ministry / Central Authorities

NIRMAAN can prioritize projects requiring attention based on:

- Statistical irregularities
- Predicted delays
- Predicted cost escalation
- Duplicate-work signals
- Compliance alerts

## State Nodal Authorities

Potential uses include:

- Monitoring state-level project execution
- Identifying delayed works
- Reviewing cost escalation warnings
- Prioritizing administrative intervention

## District Authorities

The platform can support:

- Project-level audit queues
- Contractor/project monitoring
- Compliance alert review
- Investigation prioritization

## MPs

The proposed stakeholder view can provide visibility into:

- Recommended works
- Project progress
- Project status
- Compliance signals

## Audit & Investigation Teams

The duplicate detector and financial anomaly engine can provide evidence-oriented signals such as:

- Similar project descriptions
- Distance between projects
- Category overlap
- Timeline overlap
- Statistical anomaly reasons

The system is intended as a **decision-support and early-warning platform**, not an autonomous authority for declaring fraud.

---

# 26. Current Implementation vs Future Scope

| Implemented in MVP / Repository | Future Scope |
|---|---|
| MPLADS public API extraction script | Scheduled production ingestion |
| Data cleaning and duplicate-record removal | Streaming/event-driven ingestion |
| Financial Isolation Forest pipeline | Expanded financial feature set using richer expenditure/payment data |
| Financial anomaly rule engine | Continuous model retraining and monitoring |
| XGBoost delay prediction | Production-scale historical training data |
| XGBoost cost prediction | More granular cost forecasting |
| SHAP explanations | Advanced model monitoring |
| Sentence Transformer duplicate detection | Larger distributed vector index |
| FAISS candidate retrieval | Persistent/vector-database deployment |
| Haversine similarity | PostGIS-based national geospatial analytics |
| Category similarity | Learned category representations |
| Temporal overlap | Advanced project lifecycle modeling |
| Root FastAPI alert engine | Fully unified orchestration service |
| PostgreSQL models | PostgreSQL + PostGIS production schema |
| Solidity trust ledger | Production blockchain deployment and governance |
| Web3 integrity bridge | Complete transaction/event verification |
| Static dashboard | Production Next.js/React dashboard |
| Government persona UI | Authenticated role-based government portals |
| English/Hindi UI | Full localization |
| Mock dashboard data | Live API-backed dashboard |
| Satellite/drone UI placeholders | Actual imagery and EXIF verification |
| Contractor graph UI placeholder | Implemented graph analytics / GNN pipeline |
| Docker backend deployment | Full multi-service container orchestration |

---

# 27. Testing & Validation

## Financial Module

The repository contains validation and testing infrastructure around:

- Input structure
- Monetary values
- Date consistency
- Progress constraints
- Model feature preparation
- Anomaly rules
- Inference behavior

The project progress report documents a 500-record synthetic validation dataset and multiple validation checks.

## Duplicate AI

Run:

```bash
cd duplicate-ml
pytest tests/ -v
```

The duplicate module includes tests for its service-layer components.

## Predictive AI

The predictive module includes a repeatable data-generation and model-training pipeline:

```bash
python run_pipeline.py
```

and supports:

```bash
python run_pipeline.py --no-serve
python run_pipeline.py --serve-only
```



## Current validation status

The repository contains module-level validation and testing, but there is no single end-to-end test suite that validates the complete flow:

```text
MPLADS API
→ Data Pipeline
→ All ML Services
→ Unified Backend
→ PostgreSQL
→ Blockchain
→ Dashboard
```

That should be added before production deployment.

---

# 28. Limitations

The current implementation has several important limitations that should be understood by evaluators.

### 1. Multi-service integration is incomplete

The repository contains separate financial, predictive, duplicate, backend, and blockchain components, but they are not yet completely orchestrated into one production deployment.

### 2. Root ML integration contracts differ from standalone services

The root `ml_integrator.py` expects the predictive service and duplicate service at fixed local URLs and sends simplified project-ID payloads. The standalone duplicate service currently expects full project records for its `/check-new-project` endpoint.

This means the integration bridge requires further contract alignment before the complete ML pipeline can operate seamlessly.

### 3. Dashboard is partly mock-driven

The static dashboard uses hard-coded sample projects and alerts. It should therefore be treated as a UI prototype/demo rather than a live government monitoring portal.

### 4. Some advanced modules are placeholders

Satellite imagery, drone EXIF verification, GNN contractor analysis, and several visualization components are represented in the UI/context but are not implemented as complete production services in the current repository.

### 5. Financial feature availability is limited

The financial inference pipeline explicitly notes that expenditure data is unavailable in the official snapshot used by that module, so its current model focuses on available sanction/timeline features rather than a complete expenditure-analysis model.

### 6. Blockchain verification is prototype-level

The Web3 bridge currently contains bypass behavior when the blockchain provider or contract is unavailable. It should not be interpreted as production-grade tamper protection until deployment and transaction verification are fully configured.

### 7. Security hardening is pending

Authentication, authorization, rate limiting, production CORS configuration, secure secret storage, and comprehensive audit logging require further implementation.

---

# 29. Future Scope

## AI & Analytics

- Expand financial anomaly detection to expenditure, payment, release, and utilization data.
- Add richer project lifecycle features.
- Introduce calibrated risk probabilities where appropriate.
- Add model-drift monitoring.
- Retrain models using validated real-world historical data.
- Add graph-based contractor/collusion analysis.
- Integrate advanced geospatial analytics.

## Computer Vision & Geospatial Intelligence

The project context proposes future integration of:

- Satellite imagery
- Geo-tagged photographs
- EXIF validation
- Land-cover/change detection
- Geofencing
- PostGIS spatial analytics

These capabilities are currently architectural/planned rather than fully implemented in the repository.

## Government Integration

Potential production integrations include:

- Official MPLADS APIs
- PFMS
- Government identity/RBAC systems
- State and district administrative systems
- Digital audit workflows
- Automated compliance notices

## Platform

- Production React/Next.js application
- Role-based access control
- Mobile-responsive government interface
- Real-time notifications
- Scheduled audits
- PDF audit reports
- Case-management workflows
- Investigator feedback loops
- Model feedback and retraining

## Trust Layer

- Production smart-contract deployment
- Formal contract audit
- On-chain event indexing
- Hash verification workflows
- Permissioned blockchain deployment where appropriate

---

# 30. Team

```text
Team Name: NIRMAAN
Smart India Hackathon 2026
Problem Statement: SIH26102
Organization: Ministry of Statistics and Programme Implementation (MoSPI)
```

The repository does not provide a definitive SIH team-member roster, so individual names are intentionally not fabricated.

---

# 31. License

The Solidity trust-ledger contract declares the **MIT License** through its SPDX identifier.

The repository does not appear to contain a separate repository-wide `LICENSE` file. Therefore, the MIT declaration should be interpreted specifically for the Solidity contract unless a repository-wide license is added.

---

# 32. Implementation Status Summary

| Component | Status |
|---|---|
| MPLADS API extraction | **Implemented** |
| Data cleaning | **Implemented** |
| Financial anomaly model | **Implemented** |
| Financial rule engine | **Implemented** |
| Predictive delay model | **Implemented** |
| Predictive cost model | **Implemented** |
| SHAP explanations | **Implemented** |
| NLP duplicate detection | **Implemented** |
| FAISS retrieval | **Implemented** |
| Geographical similarity | **Implemented** |
| Temporal similarity | **Implemented** |
| Category similarity | **Implemented** |
| Root FastAPI rules backend | **Implemented** |
| PostgreSQL schema/models | **Implemented** |
| Docker backend configuration | **Implemented** |
| Solidity trust ledger | **Implemented as contract source** |
| Web3 verification bridge | **Implemented, prototype-level** |
| Static dashboard | **Implemented as prototype** |
| Government dashboard | **Implemented as prototype** |
| Live dashboard-to-all-ML integration | **Partial** |
| Satellite imagery processing | **Planned / Placeholder** |
| Drone EXIF verification | **Planned / Placeholder** |
| GNN contractor analysis | **Planned / Placeholder** |
| Production authentication | **Planned** |
| Full production deployment | **Planned** |

---

# 33. Why NIRMAAN Fits SIH26102

NIRMAAN is designed around the core requirement of SIH26102: **move MPLADS monitoring from manual, fragmented inspection toward automated, explainable, data-driven early warning.**

Its current implementation demonstrates three complementary AI perspectives:

```text
                 MPLADS PROJECT
                       │
          ┌────────────┼────────────┐
          ↓            ↓            ↓
     FINANCIAL      PREDICTIVE    DUPLICATE
      ANOMALY        WARNING      DETECTION
          │            │            │
          └────────────┼────────────┘
                       ↓
              COMPLIANCE ENGINE
                       ↓
             PRIORITIZED ALERTS
                       ↓
             GOVERNMENT ACTION
```

The key design principle is that **AI identifies signals, rules contextualize them, and human authorities make the final administrative decision**.

This distinction is especially important for public-sector deployment: an anomaly should trigger investigation and evidence gathering rather than automatically being treated as confirmed fraud.

---

# 34. Repository Reference

**Source Repository:**  
Qorexx / Nirmaan-SIH

The repository contains the implementation, module-specific documentation, AI services, data pipelines, database layer, blockchain contract, and dashboard prototypes described above.

---

## NIRMAAN

**AI-assisted monitoring. Explainable alerts. Predictive governance. Immutable auditability.**

> **From monitoring projects to prioritizing action.**