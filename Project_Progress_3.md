# NIRMAN — MPLADS Monitoring Platform
## Person 3: Duplicate & Similarity Detection AI
### Project Methodology & Remarkable Progress Checkpoints Report (`Project_Progress_3.md`)

---

## Executive Overview

This document presents the complete methodology report for **Person 3 — Duplicate & Similarity Detection AI**, implemented for Smart India Hackathon (SIH 2024) Problem Statement **PS-26102** (Ministry of Statistics and Programme Implementation - MoSPI / DIID).

The sole mandate of Person 3 is to detect duplicate, overlapping, or suspiciously similar MPLADS developmental projects across India by combining **Semantic NLP Vector Similarity**, **Geographic Proximity (Haversine)**, **Project Category Taxonomy**, and **Execution Period Overlap**.

---

## Progress Checkpoints & Methodology Report

### Checkpoint 1: Repository Audit & Scope Boundary Definition

#### 1. What Was Done
- Conducted a full audit of the NIRMAN project workspace (`c:\Users\Admin\OneDrive\Desktop\SIH`).
- Analyzed existing frontend UI components, Express backend endpoints, sample project datasets (`sampleProjects.json`), and legacy similarity logic (`lib/duplicateEngine.js`).
- Defined rigid scope boundaries for Person 3.

#### 2. How It Was Done
- Inspected file dependencies and API routes across `app/`, `components/`, `lib/`, and `server/`.
- Isolated Person 3's responsibilities:
  - **Included**: Detecting text, spatial, category, and temporal project duplicates; producing Potential Duplicate Scores (0–100); generating evidence explanations; outputting structured JSON for Person 6's Unified Risk Engine.
  - **Excluded**: Financial anomaly detection (Person 1), cost/delay overrun prediction (Person 2), PostgreSQL/PostGIS data engineering (Person 4), Blockchain integration (Person 5), Unified Risk aggregation (Person 6).

#### 3. Why It Was Done
- To ensure modular software architecture, prevent scope creep, avoid duplicate effort across hackathon team roles, and maintain clean API contracts between Person 3 and Person 6.

---

### Checkpoint 2: Next.js Frontend Modernization & Interactive AI Sandbox

#### 1. What Was Done
- Migrated the application frontend from Vite/React to Next.js 14 (App Router) with Tailwind CSS.
- Built an **Interactive AI Sandbox Tester** allowing live side-by-side comparison of custom project titles, descriptions, and GPS coordinates.
- Created a **GeoDistance Map Component**, **Side-by-Side Comparison Modal**, **Flagged Duplicate Cards**, and an **API JSON Inspector**.
- Removed obsolete role tags (e.g. `"Person 3 — Next.js AI Module"`) from UI headers to present a clean "MoSPI MPLADS Platform" interface.

#### 2. How It Was Done
- Created `app/page.jsx`, `app/layout.jsx`, and `app/globals.css`.
- Developed UI components in `components/`: `SandboxTester.jsx`, `DuplicateCard.jsx`, `ComparisonModal.jsx`, `GeoDistanceMap.jsx`, `ApiJsonViewer.jsx`, and `Navbar.jsx`.
- Utilized relative module imports to resolve Next.js 14 App Router bundler pathing cleanly.

#### 3. Why It Was Done
- Hackathon evaluators and district sanctioning officers require an intuitive, interactive visual interface to inspect duplicate evidence, visualize GPS coordinates on maps, and simulate custom project pairs live without touching code.

---

### Checkpoint 3: Python FastAPI ML Microservice Architecture (`duplicate-ml/`)

#### 1. What Was Done
- Designed and built a standalone Python 3.14 FastAPI ML microservice (`duplicate-ml/`) to handle high-dimensional vector NLP embeddings and scalable vector search.
- Integrated `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` for semantic embeddings.
- Integrated **FAISS** (`faiss-cpu`) for fast vector indexing and candidate retrieval.

#### 2. How It Was Done
- Architected a modular Python package structure:
  - `app.py`: FastAPI endpoints with lifespan model loading.
  - `schemas/project.py`: Pydantic input models supporting both flat `latitude`/`longitude` and nested `coordinates.lat`/`lng`.
  - `services/embeddings.py`: Singleton model manager loading `paraphrase-multilingual-MiniLM-L12-v2` once at startup; generates L2-normalised float32 embeddings and dot-product cosine similarity.
  - `services/faiss_index.py`: `FAISSProjectIndex` wrapping `faiss.IndexFlatIP` (Inner Product on unit vectors = Cosine Search) for $O(K \log N)$ candidate pre-filtering.
  - `services/duplicate_detector.py`: Orchestrator driving candidate search, multi-factor scoring, and evidence generation.

#### 3. Why It Was Done
- JavaScript string matching algorithms (like Jaccard token overlap) cannot recognize semantic equivalence when different phrasing is used (e.g., *"Construction of community hall in Village X"* vs. *"Development of public community centre in Village X"*).
- Pre-trained Multilingual Sentence Transformers map text to a 384-dimensional dense vector space where semantic distance corresponds to true conceptual similarity.
- FAISS avoids brute-force $O(N^2)$ pair comparison across thousands of national MPLADS projects.

---

### Checkpoint 4: Purging Hardcoded Logic & Implementing Pure Math Scoring

#### 1. What Was Done
- Completely purged all legacy hardcoded values (`return 0.91;`, `timeScore = 0.85;`, `duplicateProbability = 0.93;`) from both Python ML logic and JS fallback engines.
- Implemented a continuous, physically-motivated **Haversine Geographic Distance** scoring curve.
- Implemented a **Multi-Sector Category Taxonomy** mapper.
- Implemented a real **Execution-Period Overlap Ratio** based on calendar date arithmetic.
- Created a **Dynamic Weight Renormalisation Engine** to safely process incomplete project data without inflating or deflating scores.

#### 2. How It Was Done
- **Spatial Distance (`location_similarity.py`)**:
  - Computed Haversine great-circle distance $d$ in meters.
  - Applied piecewise exponential/linear decay:
    $$S_{\text{loc}}(d) = \begin{cases} 
    1.0 & d \le 10\text{ m} \\
    0.98 \cdot e^{-0.002(d-10)} & 10 < d \le 100\text{ m} \\
    0.80 \cdot e^{-0.0017(d-100)} & 100 < d \le 500\text{ m} \\
    0.40 \cdot \left(1 - \frac{d-500}{1500}\right) & 500 < d \le 2000\text{ m} \\
    0.0 & d > 2000\text{ m}
    \end{cases}$$
- **Temporal Overlap (`temporal_similarity.py`)**:
  - Calculated Jaccard interval overlap: $\frac{\text{overlap\_days}}{\text{union\_days}}$.
  - Missing dates return `None` (not fake 0.85).
- **Weight Renormalisation (`scoring.py`)**:
  - Base weights: Text 50%, Location 25%, Category 15%, Temporal 10%.
  - When signals are missing (`None`), available weights are scaled proportionally so effective weights sum to 1.0.
- **Spec Risk Tiers**:
  - 90–100: **CRITICAL REVIEW** (🔴 Critical Duplicate Risk)
  - 75–89: **VERY HIGH** (🟠 Very High Overlap Risk)
  - 60–74: **HIGH** (🟠 High Risk Overlap)
  - 40–59: **MODERATE** (🟡 Moderate Similarity)
  - 0–39: **LOW** (🟢 Low Similarity)

#### 3. Why It Was Done
- Hardcoded scores destroy AI credibility during hackathon evaluation.
- Real-world government datasets often omit start/end dates or exact GPS coordinates. Returning `None` and renormalising weights prevents unsubmitted fields from unfairly skewing risk calculations.

---

### Checkpoint 5: API Proxy Layer & Person 6 Risk Engine Output Contract

#### 1. What Was Done
- Connected Next.js API routes (`/api/find-duplicates`, `/api/compare-pair`, `/api/check-new-project`) to proxy requests to `http://localhost:8000` with 30-second timeout handling and automatic fallback.
- Implemented an Output Adapter in `app/api/compare-pair/route.js` ensuring backward compatibility with all frontend expectations.
- Standardized structured JSON output for Person 6 Unified Risk Engine.

#### 2. How It Was Done
- Next.js API routes use Node `fetch()` to forward JSON payloads to Python FastAPI (`DUPLICATE_AI_URL=http://localhost:8000`).
- Responses include a `reasons` evidence array (e.g. `"STRONG TEXT MATCH: Semantic similarity is 81% — descriptions are nearly identical in meaning."`) and a `metadata` payload detailing embedding parameters.
- If the Python ML service is offline, API routes automatically fall back to the JS math engine (`lib/duplicateEngine.js`) and attach `_engine: "js-heuristic-fallback"`.

#### 3. Why It Was Done
- Guarantees 100% uptime for the Next.js presentation frontend even if the Python ML service is restarting or downloading model weights.
- Provides Person 6's Unified Risk Engine with explicit finding strings for overall composite risk scoring.

---

### Checkpoint 6: Verification, Unit Testing & Git Version Control

#### 1. What Was Done
- Developed a comprehensive 22-test unit test suite (`duplicate-ml/tests/test_services.py`).
- Performed live end-to-end integration tests on running servers (`http://localhost:8000` and `http://localhost:3000`).
- Configured `.gitignore` and committed all project files to Git version control.

#### 2. How It Was Done
- Ran `pytest tests/ -v` testing Haversine math, decay monotonicity, category taxonomy, date interval overlap, risk tier boundaries, and weight renormalisation (**22 / 22 PASSED**).
- Verified live FastAPI health check (`GET /health` $\rightarrow$ `{"model_loaded": true}`) and vector search (`POST /compare-pair` $\rightarrow$ `80% Potential Duplicate Score`).
- Created `.gitignore` excluding `node_modules`, `.next`, `__pycache__`, and `.pytest_cache`.
- Executed `git init`, `git add .`, and `git commit` (`bf5c8bd` & `8acf329`).

#### 3. Why It Was Done
- Rigorous automated unit testing ensures mathematical correctness, prevents regression bugs, and guarantees production stability.

---

## Summary Matrix: Checkpoint Breakdown

| Checkpoint | What Was Done | How It Was Done | Why It Was Done |
|------------|---------------|-----------------|-----------------|
| **1. Scope & Audit** | Workspace audit & boundary definition | File dependency inspection & scope isolation | Prevent scope creep; maintain modular role separation |
| **2. UI & Frontend** | Next.js 14 App Router migration & Live Sandbox | `page.jsx`, `SandboxTester.jsx`, `GeoDistanceMap.jsx` | Provide evaluators interactive proof & live simulation |
| **3. Python ML Service** | Standalone FastAPI microservice (`duplicate-ml/`) | `SentenceTransformers` + `FAISS` + `Pydantic` schemas | Capture deep semantic text similarity & enable $O(K \log N)$ search |
| **4. Purge Hardcoding** | Removed `0.91`, `0.85`, `0.93`; built pure math scoring | Haversine decay formula, date Jaccard ratio, weight renormaliser | Ensure 100% AI credibility based purely on empirical input data |
| **5. Integration Layer** | Next.js HTTP proxies & Person 6 JSON contract | `app/api/*/route.js` proxies with JS math fallback | High availability & structured risk evidence export |
| **6. Verification & Git** | 22 unit tests, live API testing, Git version control | `pytest`, live HTTP assertions, `.gitignore`, Git commits | Guarantee mathematical correctness & complete code persistence |

---

## How to Run & Verify

```powershell
# 1. Start Python FastAPI ML Service (Port 8000)
cd c:\Users\Admin\OneDrive\Desktop\SIH\duplicate-ml
uvicorn app:app --reload --port 8000

# 2. Start Next.js Frontend Dashboard (Port 3000)
cd c:\Users\Admin\OneDrive\Desktop\SIH
npm run dev

# 3. Run Unit Tests
cd c:\Users\Admin\OneDrive\Desktop\SIH\duplicate-ml
pytest tests/ -v
```

- **Frontend Dashboard & Sandbox**: [http://localhost:3000](http://localhost:3000)
- **FastAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)
