# Person 3 — Duplicate & Similarity Detection AI
## Team Presentation & Explanation Guide (`Team_Presentation_Guide.md`)

This guide is created to help you explain your ML backend architecture, technologies (**FastAPI, Sentence Transformers, FAISS**), and integration endpoints to your teammates and SIH evaluators clearly and confidently.

---

## 1. 30-Second Elevator Pitch

> *"I am **Person 3**. My responsibility is to detect duplicate, overlapping, or suspiciously similar MPLADS developmental works across India. Instead of simple keyword matching which fails when wording differs, I built a dedicated Python AI microservice using **Multilingual Sentence Transformers** for semantic text understanding, **FAISS** for fast vector search, **Haversine math** for GPS proximity, and **Date Arithmetic** for timeline overlap. It runs on **FastAPI** on port 8000 and outputs a clean **Potential Duplicate Score (0–100)** with evidence for Person 6's Unified Risk Engine."*

---

## 2. The Big Picture: How My Service Fits Into NIRMAN

```
┌─────────────────────────────────────────────────────────────┐
│  Teammates' Frontend (React / Next.js / Mobile App)        │
│  Or Person 6's Unified Risk Engine                          │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP POST (CORS Enabled)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│  Person 3 Python FastAPI Service (http://localhost:8000)   │
│                                                             │
│   1. Sentence Transformers ──► 384-Dim Text Embeddings      │
│   2. FAISS Index           ──► Fast Candidate Retrieval     │
│   3. Haversine Math        ──► Real GPS Proximity           │
│   4. Temporal Overlap      ──► Real Date Interval Overlap   │
│   5. Score Fusion Engine   ──► Renormalised 0-100 Score     │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Technology Deep-Dive (Explain to Teammates)

### A. FastAPI (The High-Performance API Web Framework)

- **What is it?**  
  FastAPI is a modern, ultra-fast Python web framework built on standard Python type hints and ASGI (`uvicorn`).
- **Why did I choose it?**
  1. **Blazing Fast**: As fast as NodeJS and Go.
  2. **Automatic Swagger Docs**: Generates interactive testing docs at `http://localhost:8000/docs` automatically.
  3. **CORS Ready**: Configured with `allow_origins=["*"]` so teammates' frontends can fetch data without cross-origin errors.
  4. **Pydantic Validation**: Automatically validates incoming JSON data and handles missing fields safely.
- **How to explain to teammates:**  
  > *"FastAPI is the entry door to my AI service. You send a standard POST request with project JSON, and it returns instantaneous AI scores."*

---

### B. Sentence Transformers (Deep NLP Text Embeddings)

- **What is it?**  
  A Deep Learning NLP model (`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`) that converts sentences into a 384-dimensional dense numerical vector (embedding).
- **Why simple keyword / Jaccard matching fails:**
  - Project A: *"Construction of community hall in Village X"*
  - Project B: *"Development of public community centre in Village X"*
  - Keyword match sees different words ("Construction" vs "Development", "hall" vs "centre").
  - **Sentence Transformers** understand that *"community hall"* and *"public community centre"* mean the exact same physical thing in English and Indian regional languages.
- **How Cosine Similarity Works:**  
  Both text embeddings are unit-normalized vectors. The dot product between vector $A$ and vector $B$ computes the Cosine Similarity ($\cos \theta$), yielding a continuous semantic score between `0.0` (completely different) and `1.0` (identical meaning).
- **How to explain to teammates:**  
  > *"Sentence Transformers don't look at spelling; they understand the human meaning and context of project descriptions, even if different words or languages are used."*

---

### C. FAISS (Facebook AI Similarity Search)

- **What is it?**  
  FAISS is an open-source library built by Meta AI research for efficient vector similarity search and indexing of dense vectors.
- **Why do we need it?**
  - If MoSPI has 100,000 sanctioned projects, comparing every project pair brute-force requires $\frac{N(N-1)}{2} \approx 5,000,000,000$ comparisons ($O(N^2)$), which takes hours.
  - **FAISS (`IndexFlatIP`)** indexes all project embeddings in memory and retrieves the top-K candidate matches in milliseconds ($O(K \log N)$).
- **How to explain to teammates:**  
  > *"FAISS acts like a supercharged AI index. When a new project is submitted, FAISS instantly finds the top 15 most similar existing projects in milliseconds, avoiding slow database loops."*

---

## 4. Multi-Factor Score Fusion & Zero Hardcoding

Explain to your team that **no scores are hardcoded**. Every score is computed mathematically:

1. **Text Similarity (50% base weight)**: Sentence Transformer Cosine Similarity.
2. **Location Proximity (25% base weight)**: Real Haversine great-circle distance $d$ (meters) converted via a smooth exponential/linear decay curve ($48.8\text{m} \rightarrow 90\%$).
3. **Category Match (15% base weight)**: Sector taxonomy mapper (`1.0` exact match, `0.7` same group, `0.4` sector match, `0.0` distinct).
4. **Temporal Overlap (10% base weight)**: Real date Jaccard interval overlap ratio: $\frac{\text{overlapping\_days}}{\text{union\_days}}$.

### Dynamic Weight Renormalisation for Missing Data
If a project is missing start/end dates or GPS coordinates, your backend **does not crash** and does not use fake values. It marks the signal as `null` and **renormalises the remaining available weights** so they sum to 100%.

### Spec Risk Tiers
- **90 – 100**: **CRITICAL REVIEW** (🔴 Critical Duplicate Risk)
- **75 – 89**: **VERY HIGH** (🟠 Very High Overlap Risk)
- **60 – 74**: **HIGH** (🟠 High Risk Overlap)
- **40 – 59**: **MODERATE** (🟡 Moderate Similarity)
- **0 – 39**: **LOW** (🟢 Low Similarity)

---

## 5. Teammate Integration Code Snippets

Share these code snippets with your teammates so they can connect their code to your service easily:

### JavaScript / React / Next.js Frontend Integration
```javascript
// Example: Teammates calling your pairwise AI endpoint
async function checkPairwiseDuplicate(projectA, projectB) {
  const response = await fetch('http://localhost:8000/compare-pair', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ projectA, projectB }),
  });
  
  const data = await response.json();
  console.log('AI Score:', data.analysis.potential_duplicate_score); // e.g. 83
  console.log('Risk Level:', data.analysis.risk_level);               // e.g. "VERY HIGH"
  console.log('Evidence Reasons:', data.analysis.reasons);           // Array of finding strings
  return data.analysis;
}
```

### Python / Person 6 Risk Engine Integration
```python
# Example: Person 6 calling your find-duplicates endpoint
import requests

def get_person3_duplicate_findings(projects_list):
    res = requests.post(
        "http://localhost:8000/find-duplicates",
        json={"projects": projects_list, "threshold": 40.0}
    )
    data = res.json()
    # Pass flagged pairs into Person 6 overall risk aggregator
    return data["results"]
```

---

## 6. Live Presentation Demo Script for Judges / Team Reviews

Follow this 4-step script during a live demo:

1. **Show Service Health**:
   - Open browser to: `http://localhost:8000/health`
   - Point out: `{"status": "online", "model_loaded": true}` proving the model is in memory.

2. **Show Interactive Swagger Docs**:
   - Open browser to: `http://localhost:8000/docs`
   - Show endpoints: `/compare-pair`, `/find-duplicates`, `/check-new-project`.

3. **Demonstrate Live AI Semantic Match**:
   - Click `/compare-pair` $\rightarrow$ *Try it out*.
   - Input two semantically equivalent titles with different wording:
     - Project A: *"Construction of community hall in Village X"*
     - Project B: *"Development of public community centre in Village X"*
   - Execute request. Show judges that the AI returns an **83% Potential Duplicate Score** with exact NLP vector similarity (`0.8082`), Haversine distance (`48.8m`), and dynamic evidence reasons.

4. **Demonstrate Missing Signal Handling**:
   - Remove coordinates or dates from input. Show that the backend renormalises weights automatically and computes a valid score without crashing.
