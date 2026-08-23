# NIRMAN — MPLADS AI Monitoring Platform
### SIH 2024 | Problem Statement 26102 | MoSPI, DIID

---

## Person 3 Module: Duplicate & Similarity Detection AI

This repository contains **Person 3's** implementation — the Duplicate & Similarity Detection module for the NIRMAN MPLADS monitoring platform.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Browser → Next.js Frontend (port 3000)                      │
│    ↓ fetch('/api/find-duplicates')                           │
│    ↓ fetch('/api/compare-pair')                              │
│    ↓ fetch('/api/check-new-project')                         │
│  Next.js API Routes (app/api/)                               │
│    ↓ HTTP POST to DUPLICATE_AI_URL                           │
│  Python FastAPI ML Service (port 8000)  ← duplicate-ml/     │
│    ├── Sentence Transformers (paraphrase-multilingual-MiniLM-L12-v2)
│    ├── FAISS (IndexFlatIP — cosine similarity search)        │
│    ├── Haversine distance (real GPS math, no hardcoding)     │
│    ├── Category taxonomy (configurable groups)               │
│    └── Temporal overlap (real date Jaccard ratio)            │
└─────────────────────────────────────────────────────────────┘
```

**Fallback**: If the Python service is offline, all API routes fall back to the JS heuristic engine automatically. A `_warning` field in the response signals this.

---

## Scoring System

| Potential Duplicate Score | Risk Tier | Badge |
|---------------------------|-----------|-------|
| 90 – 100 | CRITICAL REVIEW | 🔴 Critical Duplicate Risk |
| 75 – 89  | VERY HIGH       | 🟠 Very High Overlap Risk |
| 60 – 74  | HIGH            | 🟠 High Risk Overlap |
| 40 – 59  | MODERATE        | 🟡 Moderate Similarity |
| 0 – 39   | LOW             | 🟢 Low Similarity |

**Score formula** (renormalised for missing signals):
```
Score = text_sim×0.50 + location_sim×0.25 + category_sim×0.15 + temporal_sim×0.10
```

---

## Quick Start

### 1. Start Python ML Service (required for real AI scores)

```powershell
cd c:\...\SIH\duplicate-ml
pip install -r requirements.txt
uvicorn app:app --reload --port 8000
```

**First run**: Downloads the Sentence Transformer model (~480MB) to HuggingFace cache.

Check service health: http://localhost:8000/health  
Swagger API docs: http://localhost:8000/docs

### 2. Start Next.js Frontend

```powershell
cd c:\...\SIH
npm install
npm run dev
```

Dashboard: http://localhost:3000

---

## API Endpoints

### Python FastAPI (port 8000)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health + model status |
| POST | `/compare-pair` | Compare 2 projects directly |
| POST | `/find-duplicates` | Scan full corpus for duplicates |
| POST | `/check-new-project` | Gate a new project submission |

### Next.js API Routes (port 3000) — proxies to Python

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/find-duplicates` | Dashboard data |
| POST | `/api/compare-pair` | Sandbox tester |
| POST | `/api/check-new-project` | New project check |

---

## Person 6 Risk Engine Integration

The `/find-duplicates` endpoint returns structured findings for Person 6:

```json
{
  "pair_id": "DUP-MPLAD-2024-1042-MPLAD-2025-0319",
  "potential_duplicate_score": 87,
  "risk_level": "VERY HIGH",
  "risk_badge": "🟠 Very High Overlap Risk",
  "explanation": "...",
  "reasons": ["STRONG TEXT MATCH: ...", "VERY CLOSE PROXIMITY: ..."],
  "score_breakdown": {
    "text_similarity_percentage": 91,
    "location_proximity_percentage": 98,
    "distance_meters": 48.3,
    "category_match": 1.0,
    "time_overlap": 0.51,
    "effective_weights": {"text": 0.5, "location": 0.25, "category": 0.15, "temporal": 0.1}
  },
  "metadata": {
    "model": "paraphrase-multilingual-MiniLM-L12-v2",
    "embedding_cosine_similarity": 0.9122
  }
}
```

---

## File Structure

```
SIH/
├── app/                         # Next.js App Router
│   ├── api/
│   │   ├── find-duplicates/route.js   # Proxies to Python
│   │   ├── compare-pair/route.js      # Proxies to Python + adapter
│   │   └── check-new-project/route.js # Proxies to Python
│   ├── layout.jsx
│   └── page.jsx                 # Main dashboard
├── components/
│   ├── Navbar.jsx
│   ├── DuplicateCard.jsx
│   ├── ComparisonModal.jsx
│   ├── SandboxTester.jsx        # Live AI sandbox
│   ├── ApiJsonViewer.jsx
│   └── GeoDistanceMap.jsx
├── lib/
│   ├── duplicateEngine.js       # JS heuristic (fallback only)
│   └── sampleProjects.js        # 8 MPLADS sample projects
├── duplicate-ml/                # Python FastAPI ML Service
│   ├── app.py                   # FastAPI endpoints
│   ├── requirements.txt
│   ├── start.ps1
│   ├── schemas/
│   │   └── project.py           # Pydantic input models
│   ├── services/
│   │   ├── embeddings.py        # Sentence Transformers
│   │   ├── faiss_index.py       # FAISS IndexFlatIP
│   │   ├── location_similarity.py  # Haversine + scoring curve
│   │   ├── category_similarity.py  # Taxonomy mapping
│   │   ├── temporal_similarity.py  # Date overlap (Jaccard)
│   │   ├── scoring.py           # Weighted composite scoring
│   │   ├── explanation.py       # Evidence text generation
│   │   └── duplicate_detector.py   # Orchestrator
│   └── tests/
│       └── test_services.py     # Unit tests (pytest)
├── .env.local                   # DUPLICATE_AI_URL=http://localhost:8000
├── next.config.mjs
├── tailwind.config.js
└── package.json
```

---

## Running Unit Tests

```powershell
cd c:\...\SIH\duplicate-ml
pytest tests/ -v
```

Note: Tests for embeddings require the model to be downloaded. Non-ML tests (location, category, temporal, scoring) run without internet access.

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Next.js 14 (App Router), Tailwind CSS, Lucide React |
| API Layer | Next.js API Routes (proxy with fallback) |
| ML Service | Python 3.14, FastAPI, Uvicorn |
| Text AI | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` |
| Vector Search | FAISS `IndexFlatIP` (cosine similarity) |
| Geo Distance | Haversine formula (real GPS math) |
| Date Math | `python-dateutil` (Jaccard interval overlap) |
| Schemas | Pydantic v2 |
