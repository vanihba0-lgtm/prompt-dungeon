# Prompt Dungeon — The Last Exhibition

An open-source detective mystery web game built for **Hacktoberfest 2026**.

Investigate the theft of the priceless **Obsidian Sun** relic from the Blackwood Museum of Antiquities. Inspect crime scene locations, interrogate four suspects with distinct alibis and knowledge boundaries, expose lies with physical evidence, formulate deductions in your Truth Ledger, and deliver an indictment to the District Magistrate.

---

## 1. Architecture Overview

Prompt Dungeon pairs a deterministic server-side game engine with a rich noir React frontend and an optional hosted Gemma instruction model for dialogue:

```text
[ React 19 + TypeScript + Vite UI ]
                │
                ▼ (HTTP REST API /api/*)
[ FastAPI Backend / Game Engine ]
    ├── In-Memory Session Store (Isolated UUID token state)
    ├── Deterministic Truth Ledger (Facts, Contradictions, Theories)
    ├── Forensic Examine & Evidence Catalog (12 targets -> 12 items)
    ├── Contradiction Engine (Precondition lie & evidence checks)
    ├── Scoring & Solution Shield (100 pts, attempts, spoiler safety)
    └── Gemma AI Adapter (Hosted Gemma-2-9B-IT inference with safe fallback)
```

### Deterministic Integrity & Ground Truth Authority
- **The LLM is strictly conversational**: Gemma powers in-character roleplay for the suspects. It **cannot** create evidence, validate contradictions, change guilt flags, alter scores, or disclose the solution prematurely.
- **100% Offline-Playable**: If no API key is provided, the engine automatically uses pre-authored deterministic dialogue trees.

---

## 2. Quickstart: Running Locally on Windows PowerShell

### First-Time Setup
```powershell
# 1. Clone repository & enter directory
git clone https://github.com/vanihba0-lgtm/prompt-dungeon.git
cd prompt-dungeon

# 2. Set up Python virtual environment & install backend dependencies
python -m venv backend\.venv
.\backend\.venv\Scripts\pip.exe install -r backend\requirements.txt

# 3. Install frontend dependencies
cd frontend
npm install
cd ..
```

### Terminal 1 — Backend (FastAPI on Port 8000)
```powershell
# From repository root:
.\backend\.venv\Scripts\python.exe -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
* Backend starts at: `http://127.0.0.1:8000`
* Swagger API docs: `http://127.0.0.1:8000/docs`

### Terminal 2 — Frontend (Vite on Port 5173)
```powershell
# From repository root:
cd frontend
npm run dev
```
* Open your browser at: `http://localhost:5173`

---

## 3. Optional Gemma AI Configuration

By default, the backend runs in deterministic authorial fallback mode (`LLM_PROVIDER=none`). To enable live Gemma-powered suspect dialogue:

1. Copy `backend/.env.example` to `backend/.env` (never commit `.env`):
   ```powershell
   Copy-Item backend\.env.example backend\.env
   ```
2. Set your hosted Gemma inference provider key in `backend/.env`:
   ```bash
   LLM_PROVIDER=openrouter               # Options: groq, openrouter, together, none
   LLM_API_KEY=your_confidential_key
   LLM_MODEL_ID=google/gemma-3-12b-it    # e.g., gemma2-9b-it (Groq), google/gemma-3-12b-it (OpenRouter)
   LLM_TIMEOUT_SECONDS=10.0
   ```
*If the API call fails or times out, the backend seamlessly falls back to authored dialogue with zero crashes.*

---

## 4. Running the Tests

### Backend Test Suite (100 passing tests)
```powershell
cd C:\Users\Vanih\OneDrive\Desktop\prompt-dungeon
.\backend\.venv\Scripts\python.exe -m pytest backend\tests\ -v
```

### End-to-End Playthrough & Mystery Integrity Audit
```powershell
.\backend\.venv\Scripts\python.exe full_playthrough_audit.py
```

### Frontend Type-Check & Production Build
```powershell
cd C:\Users\Vanih\OneDrive\Desktop\prompt-dungeon\frontend
npm run build
```

---

## 5. Canonical Mystery Summary (Spoiler Warning)

- **Case:** *The Last Exhibition* (October 12, 2026, 9:17 PM).
- **Culprit:** **Elias Voss** (Chief Conservator).
- **Motive:** £150,000 extortion debt to "The Grey Ledger" syndicate due at midnight (`E-06`).
- **Method:** Vitrine pneumatic bypass with nitrogen shunt (`E-01`) through tapestry dumbwaiter hatch (`E-10`) during Noah Reed's 9:15–9:19 camera crash (`E-02`).
- **Recovery:** Submerged in acid-proof silicone bladder inside Hexane-12 solvent canister in Basement HazMat Locker 4 (`E-11`).
