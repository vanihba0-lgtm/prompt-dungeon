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
  "timestamp": "2026-10-12T07:00:00.000000+00:00"
}
```

---

## 5. Project Layout

```text
prompt-dungeon/
├── backend/
│   ├── .env.example       # Template for local environment variables
│   ├── main.py            # FastAPI entry point & health endpoint
│   ├── requirements.txt   # Core Python dependencies
│   └── README.md          # Setup & developer guide
├── docs/
│   ├── api-contract.md    # Approved REST API specification
│   └── case-spec.md       # Approved canonical mystery rules
└── .gitignore             # Git ignore rules for Python & Node
```
