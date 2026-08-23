# Methodology Progress Report — Financial Anomaly Detection Engine

**Project:** SIH 2026 — Problem Statement SIH26102  
**Organization:** Ministry of Statistics and Programme Implementation (MoSPI)  
**Lead:** Person 1 (Financial AI / Anomaly Detection Engine)  

---

## Checkpoint 1 — Project Initialization

### What I did
- Initialized the repository directory structure for the Financial Anomaly Detection Engine microservice.
- Set up isolated directory layers (`src/`, `data/raw/`, `data/processed/`, `models/`, `docs/`, `tests/`).
- Created a Python virtual environment (`.venv`) for project isolation.
- Defined explicit dependency requirements in `requirements.txt`.
- Configured `.gitignore` to prevent committing binary artifacts, virtual environments, cache files, and datasets.
- Authored initial project documentation in `README.md` and basic runtime settings in `src/config.py`.

### How I did it
- Configured modular layout:
  - `src/` to hold core Python modules (`config.py`, feature engineering, Isolation Forest model, rule engine, FastAPI app).
  - `data/raw/` and `data/processed/` for mock/production dataset management.
  - `models/` for serializing trained `scikit-learn` Isolation Forest models.
  - `tests/` for `pytest` unit/integration test suites.
- Created `.venv` using `virtualenv` and installed initial dependencies (`pandas`, `numpy`, `scikit-learn`, `fastapi`, `uvicorn`, `pydantic`, `pytest`, `python-dotenv`).
- Set environment defaults in `src/config.py` (Port 8001, risk threshold boundaries, contamination factor).

### Why I did it
- **Modular Isolation:** Person 1's module must run independently as a FastAPI microservice (`http://localhost:8001`) that Person 6 can easily integrate.
- **Reproducibility:** Enforcing virtual environment separation and explicit `requirements.txt` ensures seamless execution across team members' local machines.
- **Data & Model Hygiene:** Keeping dataset placeholders and serialized models out of Git prevents repository bloat while preserving reproducible directory structures (`.gitkeep`).

### Verification
- Verified directory tree creation using file system checks.
- Verified Python environment version (`Python 3.12.3`).
- Verified dependencies installation within `.venv`.
- Verified importability of `src.config`.

### Files Created
- `README.md` — Project documentation and setup guide.
- `.gitignore` — Ignore rules for Python, virtual environments, models, and data.
- `requirements.txt` — Project dependencies specification.
- `src/__init__.py` — Package initializer.
- `src/config.py` — Configuration constants & threshold settings.
- `tests/__init__.py` — Test package initializer.
- `data/raw/.gitkeep` — Directory placeholder.
- `data/processed/.gitkeep` — Directory placeholder.
- `models/.gitkeep` — Directory placeholder.
- `docs/.gitkeep` — Directory placeholder.
- `Project_Progress_1.md` — Chronological development progress log.
