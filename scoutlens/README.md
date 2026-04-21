# ScoutLens

**Role-aware player similarity search engine for football scouting and recruitment.**

ScoutLens answers the question every recruitment department faces: *"If we lose Player X, who can genuinely fulfil the same tactical function in our system?"*

Unlike generic stat-matching tools, ScoutLens infers each player's functional role from event data (e.g. Ball-Playing CB, Pressing Forward, Inside Forward), then conditions the similarity search on that role. Results are presented with explainable feature breakdowns, interactive radar charts, and scouting-language summaries.

## Key Features

- **Role-aware similarity search** across 1,533 outfield players from Europe's Big Five leagues (2015/16)
- **14 functional role archetypes** derived from hierarchical clustering on 42 per-90 statistical features
- **Adjustable dimension weights** — scouts can prioritise Attacking, Creativity, Passing, Carrying, Defending, or Physicality
- **Cosine decomposition** explaining *why* two players are similar, broken down by dimension
- **Role-adaptive radar charts** — each role shows the most relevant features, not a fixed generic set
- **Scouting-language summaries** for every role archetype
- **Shortlist management** with personal notes (JWT-authenticated)

## Data Source

[StatsBomb Open Data](https://github.com/statsbomb/open-data) — 2015/16 season covering:
- Premier League (380 matches)
- La Liga (380 matches)
- Bundesliga (306 matches)
- Serie A (380 matches)
- Ligue 1 (377 matches)

Total: ~6.4 million events processed into 42 per-90 features per player.

## Architecture

```
Frontend (React/TypeScript)
    │
    │  HTTP / JSON
    ▼
Backend API (FastAPI)
    │
    ├── FAISS Vector Index ──── Cosine similarity search
    ├── Metadata Cache ──────── Player profiles, features, roles
    └── PostgreSQL ──────────── User accounts, shortlists
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, Recharts, TanStack Query |
| Backend | Python 3.11, FastAPI, Pydantic, SQLAlchemy 2.0 |
| ML / Search | FAISS (IndexFlatIP), scikit-learn, Ward's hierarchical clustering |
| Data | pandas, StatsBomb Open Data, parquet storage |
| Auth | JWT (python-jose), bcrypt |
| Database | PostgreSQL 15 |
| Infrastructure | Docker, Docker Compose |

## Repository Structure

```
scoutlens/
├── backend/
│   ├── app/                  # FastAPI application
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── routers/          # API endpoint handlers
│   │   ├── services/         # Business logic (similarity, auth, etc.)
│   │   ├── ml/               # FAISS wrapper, UMAP projector
│   │   └── utils/            # Constants (42 features, 14 roles), percentiles
│   ├── pipeline/             # Data processing pipeline (Steps 1-8)
│   └── tests/                # Unit and integration tests
├── frontend/
│   └── src/
│       ├── pages/            # Search, Profile, Similarity, Shortlist, Auth
│       ├── components/       # Radar charts, player cards, filter panels
│       ├── hooks/            # React Query hooks for API calls
│       └── context/          # JWT authentication context
├── evaluation/               # Dissertation evaluation scripts
└── data/                     # Pipeline outputs (git-ignored)
```

## The 42-Feature Statistical Model

Features are grouped into 6 dimensions, all per-90 normalised:

| Dimension | Features | Examples |
|-----------|----------|---------|
| Attacking (7) | xG, shots, goals, npxG, touches in box | Goal-scoring output |
| Chance Creation (7) | xA, key passes, assists, through balls | Creative contribution |
| Passing (7) | Pass volume, completion %, progressive distance | Distribution quality |
| Carrying (7) | Progressive carries, dribbles, carry distance | Ball progression |
| Defending (8) | Pressures, tackles, interceptions, recoveries | Defensive work |
| Aerial/Physical (6) | Aerial duels, ground duels, fouls won | Physical profile |

## The 14 Role Archetypes

Assigned via Ward's hierarchical clustering, constrained by position group:

| Position Group | Roles |
|---------------|-------|
| Centre-Back | Ball-Playing CB, Aerial/Stopper CB |
| Full-Back | Attacking Full-Back, Inverted Full-Back |
| Defensive Midfield | Deep-Lying Playmaker, Ball-Winning Midfielder |
| Central Midfield | Box-to-Box Midfielder, Advanced Playmaker |
| Attacking Midfield | Advanced Playmaker |
| Wide Forward | Inside Forward, Touchline Winger |
| Centre-Forward | Complete Forward, Poacher, Target Forward, Pressing Forward |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/v1/search?q=Messi` | Search players by name |
| `GET` | `/api/v1/player/{id}` | Full profile with per-90 stats and radar axes |
| `POST` | `/api/v1/similar/{id}` | Find similar players via FAISS |
| `GET` | `/api/v1/explain/{id}?target_id={id}` | Per-feature similarity decomposition |
| `GET` | `/api/v1/health` | System health check |
| `POST` | `/api/v1/auth/register` | Create account |
| `POST` | `/api/v1/auth/login` | Authenticate and receive JWT |
| `GET` | `/api/v1/shortlist` | View shortlist (authenticated) |
| `POST` | `/api/v1/shortlist` | Add player to shortlist (authenticated) |

Interactive API documentation available at `http://localhost:8000/docs` when the server is running.

## Testing

```bash
cd backend
.venv\Scripts\activate
pytest tests/ -v
```

45 tests covering:
- Data pipeline integrity (ingestion, normalisation, minutes, filtering)
- Feature engineering (42 features, no NaN/Inf, value bounds)
- Role classification (labels assigned, confidence scores, cluster sizes)
- FAISS index (self-query verification, vector count)
- API endpoints (health, search, auth, schema validation)

## Evaluation Metrics

| Metric | Method | Target |
|--------|--------|--------|
| RC@k | Role Consistency at k (% of top-k sharing query's role) | RC@10 >= 0.75 |
| Latency | FAISS query p95 over 500 queries | p95 < 100ms |
| Temporal Stability | Pearson r between perturbed and full-data rankings | r > 0.6 |
| Ablation | RC@10 drop when each dimension is removed | Identify critical dims |
| SUS | System Usability Scale from user study | >= 70 |

Run evaluation scripts:
```bash
python evaluation/latency_benchmark.py
python evaluation/role_consistency.py
python evaluation/ablation_study.py
```

## Licence

StatsBomb Open Data is used under their [open data licence](https://github.com/statsbomb/open-data). This project is submitted as a BSc Computer Science dissertation at the University of Greenwich.
