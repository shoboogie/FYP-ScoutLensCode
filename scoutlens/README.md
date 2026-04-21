# ScoutLens

Role-aware player similarity search engine for football scouting and recruitment.

Built as a BSc Computer Science dissertation project at the University of Greenwich. ScoutLens finds the most statistically and tactically similar players across Europe's Top 5 Leagues using StatsBomb Open Data (2015/16 season), FAISS vector search, and hierarchical role clustering.

## Architecture

```
React/TypeScript ──→ FastAPI ──→ FAISS + PostgreSQL
   (Vite)            (Pydantic)   (1,533 players × 42 features)
```

- **Data pipeline:** StatsBomb → normalise → per-90 features → Ward's clustering → FAISS index
- **Backend:** FastAPI with async SQLAlchemy, JWT auth, cosine decomposition explainer
- **Frontend:** React 18, TanStack Query, Recharts radar charts, Tailwind CSS
- **ML engine:** 42 per-90 features across 6 dimensions, 14 functional role archetypes

## Quick Start

```bash
# 1. Start PostgreSQL
docker compose up -d db

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3. Run the data pipeline (downloads ~800MB from StatsBomb, takes ~35 min first run)
python -m pipeline.run_pipeline

# 4. Seed the database
python -m pipeline.seed_db

# 5. Start the API server
uvicorn app.main:app --reload --port 8000

# 6. Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 for the UI, http://localhost:8000/docs for API documentation.

## Data Pipeline

| Step | Module | Output |
|------|--------|--------|
| 1. Ingest | `pipeline/ingest.py` | Raw parquets from StatsBomb |
| 2. Normalise | `pipeline/normalise_schema.py` | Split locations, rename columns |
| 3. Minutes | `pipeline/compute_minutes.py` | Per-player per-match minutes |
| 4. Filter | `pipeline/quality_filter.py` | 1,533 qualified outfield players |
| 5. Features | `pipeline/engineer_features.py` | 42 per-90 features |
| 6. Roles | `pipeline/classify_roles.py` | 14 role labels via Ward's clustering |
| 7. Index | `pipeline/build_index.py` | FAISS IndexFlatIP for cosine search |
| 8. Seed | `pipeline/seed_db.py` | Populate PostgreSQL |

Use `--skip-ingest` to skip downloading if raw data is cached:
```bash
python -m pipeline.run_pipeline --skip-ingest
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/search?q=` | Search players by name |
| GET | `/api/v1/player/{id}` | Full player profile with stats |
| POST | `/api/v1/similar/{id}` | Find similar players (FAISS) |
| GET | `/api/v1/explain/{id}?target_id=` | Cosine decomposition |
| POST | `/api/v1/auth/register` | Create account |
| POST | `/api/v1/auth/login` | Get JWT token |
| GET | `/api/v1/shortlist` | View saved players (authed) |
| POST | `/api/v1/shortlist` | Add to shortlist (authed) |

## Testing

```bash
cd backend
pytest tests/ -v
```

## Tech Stack

Python 3.11 · FastAPI · PostgreSQL 15 · SQLAlchemy 2.0 · FAISS · scikit-learn · pandas · React 18 · TypeScript · Vite · Tailwind CSS · Recharts · TanStack Query · Docker

## Licence

StatsBomb Open Data is used under their [open data licence](https://github.com/statsbomb/open-data).
