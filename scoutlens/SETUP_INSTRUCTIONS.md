# ScoutLens — Setup and Running Instructions

These instructions will get ScoutLens running on a fresh machine using VS Code.

---

## Prerequisites

Install the following before starting:

1. **Python 3.11+** — https://python.org/downloads
   - **Windows:** During installation, tick "Add Python to PATH"
   - **Mac:** `brew install python@3.11` (or download from python.org)

2. **Node.js (LTS)** — https://nodejs.org
   - **Windows:** Download the LTS installer
   - **Mac:** `brew install node` or download from nodejs.org

3. **Git** — https://git-scm.com/downloads
   - **Mac:** Comes pre-installed, or run `xcode-select --install`

4. **VS Code** — https://code.visualstudio.com

---

## Step 1: Clone the Repository

Open VS Code, then open the terminal.
- **Windows:** `Ctrl + backtick`
- **Mac:** `Cmd + backtick`

**Windows:**
```powershell
cd C:\Users\YourUsername
git clone https://github.com/shoboogie/FYP-ScoutLensCode.git
cd FYP-ScoutLensCode
```

**Mac:**
```bash
cd ~/Desktop
git clone https://github.com/shoboogie/FYP-ScoutLensCode.git
cd FYP-ScoutLensCode
```

Then open the project folder: **File > Open Folder > FYP-ScoutLensCode**

---

## Step 2: Set Up the Backend

Open a terminal in VS Code and run:

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you see a "running scripts is disabled" error on Windows, run this first:
```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

**Mac (Terminal):**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

You should see `(.venv)` at the start of your terminal line on both platforms.

---

## Step 3: Run the Data Pipeline

**First time (downloads data from StatsBomb — takes approximately 35 minutes):**

**Windows:**
```powershell
python -m pipeline.run_pipeline
```

**Mac:**
```bash
python3 -m pipeline.run_pipeline
```

**If data is already downloaded (takes seconds):**

**Windows:**
```powershell
python -m pipeline.run_pipeline --skip-ingest
```

**Mac:**
```bash
python3 -m pipeline.run_pipeline --skip-ingest
```

This processes 6.4 million football events into:
- 42 per-90 statistical features for each player
- 14 functional role classifications
- A FAISS similarity search index

---

## Step 4: Start the Backend Server

**Windows:**
```powershell
uvicorn app.main:app --reload --port 8000
```

**Mac:**
```bash
python3 -m uvicorn app.main:app --reload --port 8000
```

Leave this terminal running. You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Verify by opening http://localhost:8000/docs in your browser — you should see the interactive API documentation.

---

## Step 5: Start the Frontend

Open a **second terminal** in VS Code (click the `+` icon next to the terminal tab).

**Both Windows and Mac:**
```bash
cd frontend
npm install
npm run dev
```

Leave this terminal running. You should see:
```
VITE v5.x.x  ready in XXXms
Local: http://localhost:5173/
```

---

## Step 6: Use the Application

Open **http://localhost:5173** in your browser.

### Searching for Players
- Type a player name in the search bar (e.g. "Messi", "Suarez", "Neymar", "Ronaldo")
- Filter by league using the dropdown
- Click a player card to view their full profile

### Player Profile Page
- View all 42 per-90 statistics grouped by dimension
- See the role-adaptive radar chart (axes change based on the player's role)
- Read the scouting summary for the player's role archetype
- Click "Find Similar Players" to run the similarity engine
- Click "Save to Shortlist" to add a player to your personal shortlist

### Similarity Search
- Results are ranked by cosine similarity percentage
- Use the filter panel to narrow by league or minutes
- Toggle "Same role only" to restrict or expand the search
- Adjust the dimension weight sliders to prioritise what matters:
  - Attacking, Creativity, Passing, Carrying, Defending, Physicality
- Click "Save" on any result to add it to your shortlist

### Authentication
- Register at /register to create an account
- Sign in to access the shortlist feature
- Save players to your shortlist with personal scouting notes

---

## Running Tests

Open a third terminal:

**Windows:**
```powershell
cd backend
.venv\Scripts\activate
pytest tests/ -v
```

**Mac:**
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

Expected output: **45 passed**

---

## Running Evaluation Scripts

**Windows:**
```powershell
cd backend
.venv\Scripts\activate
cd ..
python evaluation/latency_benchmark.py
python evaluation/role_consistency.py
python evaluation/ablation_study.py
python evaluation/sus_analysis.py
```

**Mac:**
```bash
cd backend
source .venv/bin/activate
cd ..
python3 evaluation/latency_benchmark.py
python3 evaluation/role_consistency.py
python3 evaluation/ablation_study.py
python3 evaluation/sus_analysis.py
```

---

## Stopping the Application

- **Backend terminal:** `Ctrl+C`
- **Frontend terminal:** `Ctrl+C`

---

## Troubleshooting

**"Module not found" errors:**
Make sure the virtual environment is activated — you should see `(.venv)` in your terminal.
- Windows: `.venv\Scripts\activate`
- Mac: `source .venv/bin/activate`

**"uvicorn is not recognised":**
The virtual environment is not activated. Activate it first (see above).

**"python not found" on Mac:**
Use `python3` instead of `python` for all commands.

**Frontend shows "Failed to load results":**
The backend server is not running. Start it with `uvicorn app.main:app --reload --port 8000` in the backend terminal.

**Pipeline takes too long:**
The first run downloads ~800MB from StatsBomb's servers. Subsequent runs use cached data and complete in seconds with `--skip-ingest`.

**Permission error on Mac:**
If `pip install` fails with a permission error, make sure you're using the virtual environment (`.venv`), not the system Python.

---

## Project Summary

| Component | Description |
|-----------|-------------|
| 1,533 | Qualified outfield players across 5 leagues |
| 42 | Per-90 statistical features per player |
| 14 | Functional role archetypes |
| 6 | Feature dimensions (Attacking, Creativity, Passing, Carrying, Defending, Physical) |
| <1ms | FAISS similarity query latency (p95) |
| 45 | Automated tests |
