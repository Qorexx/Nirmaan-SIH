# NIRMAN — MPLADS Monitoring Platform
## Person 3: Duplicate & Similarity Detection AI
### Project Methodology & Progress Checkpoints Report (`Project_Progress_3.md`)

---

## Executive Overview

This document presents the methodology report for **Person 3 — Duplicate & Similarity Detection AI**, implemented for Smart India Hackathon (SIH 2024) Problem Statement **PS-26102** (Ministry of Statistics and Programme Implementation - MoSPI / DIID).

Person 3's sole responsibility is to build the backend ML microservice that detects duplicate, overlapping, or suspiciously similar MPLADS developmental projects across India by combining **Semantic NLP Vector Similarity**, **Geographic Proximity (Haversine)**, **Project Category Taxonomy**, and **Execution Period Overlap**.

---

## Progress Checkpoints & Methodology Report

### Checkpoint 1: Repository Audit, API Contracts & Scope Isolation

#### 1. What Was Done
- Conducted an initial audit of project requirements and defined rigid API boundaries for Person 3's backend ML module.
- Defined input schemas (`ProjectRecord`) and output schemas (`Potential Duplicate Score (0–100)`, risk level, breakdown, reasons).
- Isolated Person 3's responsibilities cleanly.

#### 2. How It Was Done
- Established clean REST contracts (`/health`, `/compare-pair`, `/find-duplicates`, `/check-new-project`).
- Isolated Person 3's backend responsibilities:
  - **Included**: Semantic NLP vector matching, Haversine spatial proximity, category taxonomy mapper, real date-interval overlap ratio, score fusion, weight renormalisation, structured evidence output.
  - **Excluded**: Frontend UI/dashboard (teammate's role), financial anomaly detection (Person 1), cost/delay overrun prediction (Person 2), PostgreSQL/PostGIS (Person 4), Blockchain (Person 5), overall composite risk aggregation (Person 6).

#### 3. Why It Was Done
- To ensure clean modular role separation, prevent merge conflicts, and maintain strict API contracts for teammate frontend and Person 6 integrations.

---

### Checkpoint 2: Python FastAPI ML Microservice Architecture (`duplicate-ml/`)

#### 1. What Was Done
- Designed and built a standalone Python 3.14 FastAPI ML microservice (`duplicate-ml/`).
- Implemented standard REST endpoints with lifespan model loading and built-in CORS support.

#### 2. How It Was Done
- Created a modular Python package structure:
  - `app.py`: FastAPI server with ASGI `uvicorn` runner and CORS middleware (`allow_origins=["*"]`).
  - `schemas/project.py`: Pydantic input models supporting both flat `latitude`/`longitude` and nested `coordinates.lat`/`lng`.
  - `start.ps1`: PowerShell launcher script for automated server startup.

#### 3. Why It Was Done
- A dedicated Python FastAPI microservice provides high-performance asynchronous request handling, automatic OpenAPI/Swagger documentation (`/docs`), and native integration with PyTorch and HuggingFace ML libraries.

---

### Checkpoint 3: Multilingual Sentence Transformers & FAISS Vector Search

#### 1. What Was Done
- Integrated `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` for dense text embeddings.
- Integrated **FAISS** (`faiss-cpu`) for fast vector candidate retrieval.

#### 2. How It Was Done
- `services/embeddings.py`: Generates 384-dimensional dense vector embeddings for project titles and descriptions. Computes true L2-normalised dot-product Cosine Similarity.
- `services/faiss_index.py`: `FAISSProjectIndex` wraps `faiss.IndexFlatIP` (Inner Product on unit vectors = Cosine Search) to index project embeddings in memory and retrieve top-K candidates in $O(K \log N)$ time.
- `services/duplicate_detector.py`: Orchestrates FAISS candidate search, pre-filtering (embedding similarity $\ge 0.20$), and full multi-factor scoring.

#### 3. Why It Was Done
- Simple string matching fails when different wording is used (e.g. *"Construction of community hall"* vs *"Development of public community centre"*). Sentence Transformers understand semantic meaning across English and regional languages.
- FAISS eliminates slow $O(N^2)$ brute-force pair comparisons across large national project databases.

---

### Checkpoint 4: Haversine Distance & Real Date-Overlap Arithmetic (Zero Hardcoding)

#### 1. What Was Done
- Completely purged all hardcoded rules (`return 0.91;`, `timeScore = 0.85;`, `duplicateProbability = 0.93;`).
- Implemented a continuous, physically-motivated **Haversine Geographic Distance** decay curve.
- Implemented a **Multi-Sector Category Taxonomy** mapper.
- Implemented a real **Execution-Period Overlap Ratio** based on calendar date arithmetic.

#### 2. How It Was Done
- **Spatial Proximity (`services/location_similarity.py`)**:
  - Computes Haversine great-circle distance $d$ in meters.
  - Applies a smooth exponential/linear decay curve ($d \le 10\text{m} \rightarrow 1.0$, $48.8\text{m} \rightarrow 0.8979$).
- **Category Similarity (`services/category_similarity.py`)**:
  - Maps 8 macro-sectors (`1.0` exact match, `0.7` same group, `0.4` sector match, `0.0` distinct).
- **Temporal Overlap (`services/temporal_similarity.py`)**:
  - Calculates real Jaccard interval overlap ratio: $\frac{\text{overlapping\_days}}{\text{union\_days}}$. Missing dates return `None` (never fake default values).

#### 3. Why It Was Done
- Hardcoded scores destroy AI credibility. All scores must be mathematically derived from actual input data and trained ML embeddings.

---

### Checkpoint 5: Score Fusion, Weight Renormalisation & Person 6 Risk Contract

#### 1. What Was Done
- Implemented a composite score fusion engine with dynamic weight renormalisation for missing data.
- Enforced spec-mandated risk tiers (0–100).
- Generated structured evidence output (`reasons` array) for Person 6.

#### 2. How It Was Done
- **Score Fusion (`services/scoring.py`)**:
  - Base weights: Text 50%, Location 25%, Category 15%, Temporal 10%.
  - When signals are missing (`None`), available weights are scaled proportionally so effective weights sum to 1.0.
- **Spec Risk Tiers**:
  - 90–100: **CRITICAL REVIEW** (🔴 Critical Duplicate Risk)
  - 75–89: **VERY HIGH** (🟠 Very High Overlap Risk)
  - 60–74: **HIGH** (🟠 High Risk Overlap)
  - 40–59: **MODERATE** (🟡 Moderate Similarity)
  - 0–39: **LOW** (🟢 Low Similarity)
- **Evidence Generation (`services/explanation.py`)**:
  - Builds structured finding strings for Person 6's Unified Risk Engine.

#### 3. Why It Was Done
- Real-world government datasets often have missing fields. Dynamic weight renormalisation prevents unsubmitted fields from unfairly skewing duplicate scores.

---

### Checkpoint 6: Verification, Unit Testing & Git Persistence

#### 1. What Was Done
- Developed a comprehensive 22-test automated unit test suite (`duplicate-ml/tests/test_services.py`).
- Verified live API endpoints (`http://localhost:8000`).
- Configured `.gitignore` and committed Person 3's ML backend files to Git.

#### 2. How It Was Done
- Executed `pytest tests/ -v` testing Haversine math, decay monotonicity, category taxonomy, date overlap ratio, risk tiers, and weight renormalisation (**22 / 22 PASSED**).
- Verified live FastAPI health check (`GET /health` $\rightarrow$ `{"model_loaded": true}`).
- Pushed clean branch `DC--508` to GitHub containing strictly Person 3 ML files.

#### 3. Why It Was Done
- Automated unit tests guarantee mathematical correctness and long-term backend stability.

---

## Summary Matrix: Checkpoint Breakdown

| Checkpoint | What Was Done | How It Was Done | Why It Was Done |
|------------|---------------|-----------------|-----------------|
| **1. API & Scope** | API contract definition & scope isolation | REST endpoint contracts & Pydantic models | Ensure modular role separation with zero scope creep |
| **2. Architecture** | Python FastAPI ML service (`duplicate-ml/`) | `app.py`, ASGI `uvicorn`, CORS middleware | High performance, auto Swagger docs & easy integration |
| **3. Vector Search** | Sentence Transformers & FAISS indexing | `paraphrase-multilingual-MiniLM-L12-v2` & `IndexFlatIP` | Capture semantic text meaning & enable $O(K \log N)$ retrieval |
| **4. Real Math** | Purged hardcoding; implemented Haversine & date math | Exponential spatial decay & Jaccard date overlap | Ensure 100% AI credibility based on real data |
| **5. Score Fusion** | Weight renormaliser & Person 6 evidence contract | `scoring.py` renormaliser & `explanation.py` | Safe missing-data handling & Person 6 export |
| **6. Verification** | 22 unit tests & Git persistence | `pytest` suite & Git branch `DC--508` push | Mathematical correctness & codebase reliability |

---

## How to Run & Verify

```powershell
# 1. Start Python FastAPI ML Service (Port 8000)
cd c:\Users\Admin\OneDrive\Desktop\SIH\duplicate-ml
uvicorn app:app --reload --port 8000

# 2. Run Unit Tests
cd c:\Users\Admin\OneDrive\Desktop\SIH\duplicate-ml
pytest tests/ -v
```

- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
