# Prompt Dungeon — Backend Service

Backend API and deterministic game engine for **Prompt Dungeon: The Last Exhibition**.

Built with **Python** and **FastAPI**.

---

## 1. Prerequisites

* **Python:** 3.10 or newer (tested on Python 3.14)
* **Shell:** Windows PowerShell or Command Prompt

---

## 2. Setup Instructions (Windows PowerShell)

Open PowerShell and navigate to the project directory:

```powershell
cd C:\Users\Vanih\OneDrive\Desktop\prompt-dungeon\backend
```

### Step A: Create the Virtual Environment
Create an isolated Python virtual environment named `.venv` in the backend folder:

```powershell
python -m venv .venv
```

### Step B: Activate the Virtual Environment
Allow script execution for your current session if needed, then activate `.venv`:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
.\.venv\Scripts\Activate.ps1
```

*(Your terminal prompt should now show `(.venv)` at the beginning).*

### Step C: Install Dependencies
Install the required packages from `requirements.txt`:

```powershell
pip install -r requirements.txt
```

### Step D: Create Local Environment Configuration
Copy `.env.example` to create your local `.env` configuration file:

```powershell
Copy-Item .env.example .env
```

---

## 3. Running the Server

Start the local development server with auto-reload enabled:

```powershell
uvicorn main:app --reload --port 8000
```

The server will start at:
* **API Root:** `http://localhost:8000`
* **Interactive API Docs (Swagger):** `http://localhost:8000/docs`

---

## 4. Testing the Health Endpoint

While the server is running, open a separate PowerShell window or terminal tab and run:

```powershell
Invoke-RestMethod -Uri http://localhost:8000/api/health
```

Or using `curl`:

```powershell
curl http://localhost:8000/api/health
```

**Expected JSON Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-10-12T11:00:00.000000+00:00",
  "llm_provider": "openrouter",
  "llm_configured": true,
  "llm_model": "google/gemma-3-12b-it",
  "session_store_type": "SQLiteSessionStore"
}
```

### Testing the LLM Connectivity Probe
To verify live Gemma inference connectivity without creating a full game session:

```powershell
curl http://localhost:8000/api/health/llm
```

**Expected JSON Response:**
```json
{
  "success": true,
  "status": "reachable",
  "provider": "openrouter",
  "model_id": "google/gemma-3-12b-it",
  "message": "Successfully connected to Gemma inference provider."
}
```

---

## 5. Session Persistence & Serverless Architecture

In serverless production environments (such as Vercel), ephemeral lambda containers spin up and down across requests. Prompt Dungeon uses `SQLiteSessionStore`:
- Automatically initializes `prompt_dungeon.db` (or `/tmp/prompt_dungeon.db` on serverless).
- Runs with **SQLite WAL (Write-Ahead Logging)** mode and thread-safe locking.
- Serializes and stores full game sessions (Truth Ledger, facts, contradictions, player theories, event logs, penalties) upon every state-mutating operation.
- Fully backwards-compatible with `InMemorySessionStore` if SQLite is disabled.

---

## 6. Project Layout

```text
prompt-dungeon/
├── backend/
│   ├── api/
│   │   └── index.py           # Vercel serverless function entry point
│   ├── tests/                 # 102 passing pytest tests
│   ├── case_data.py           # Canonical mystery data (The Last Exhibition)
│   ├── game_engine.py         # Deterministic mystery & contradiction engine
│   ├── gemma_provider.py      # LLM adapter with system persona builder
│   ├── main.py                # FastAPI application & REST route definitions
│   ├── models.py              # Pydantic v2 schemas matching api-contract.md
│   ├── session_store.py       # SQLiteSessionStore (WAL) & InMemorySessionStore
│   ├── vercel.json            # Standalone backend Vercel configuration
│   ├── requirements.txt       # Backend dependencies
│   ├── .env.example           # Configuration template
│   └── README.md              # Setup & developer guide
├── api/
│   └── index.py               # Monorepo root Vercel serverless entry point
├── docs/
│   ├── api-contract.md        # Approved REST API specification v1.1.0
│   └── case-spec.md           # Approved canonical mystery rules v1.1.0
├── frontend/                  # React 19 + TypeScript + Vite noir investigation UI
├── requirements.txt           # Monorepo root Python dependencies for Vercel
├── vercel.json                # Monorepo root Vercel configuration
└── .gitignore                 # Excludes .env, *.db, node_modules, dist/
```
