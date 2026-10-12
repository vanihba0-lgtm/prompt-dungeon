"""
Prompt Dungeon — Backend API Service
Canonical Case: The Last Exhibition
Reference: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0
"""

# Load environment variables from backend/.env BEFORE any module reads os.getenv().
# This is critical: gemma_provider.py reads LLM_* variables at module-level on import.
import os
from pathlib import Path
from dotenv import load_dotenv

_env_path = Path(__file__).resolve().parent / ".env"
load_dotenv(_env_path)

from datetime import datetime, timezone
import json
from typing import List, Optional

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from models import (
    ConfigResponse,
    CreateSessionRequest,
    ResetSessionResponse,
    SessionStateResponse,
)
from public_catalog import get_public_config
from session_store import (
    InvalidSessionIdError,
    SessionClosedError,
    SessionNotFoundError,
    session_store,
)


# ============================================================================
# 1. Application Initialization & CORS Configuration
# ============================================================================

app = FastAPI(
    title="Prompt Dungeon API",
    description="Backend API and deterministic game engine for The Last Exhibition",
    version="1.0.0",
)

# Parse CORS origins from environment or default to local Vite dev server
cors_origins_env = os.getenv(
    "CORS_ORIGINS",
    '["http://localhost:5173", "http://127.0.0.1:5173"]',
)

try:
    if cors_origins_env.startswith("["):
        allowed_origins: List[str] = json.loads(cors_origins_env)
    else:
        allowed_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]
except Exception:
    allowed_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


# ============================================================================
# 2. Global Exception Handlers (Standard Error Envelope)
# ============================================================================

@app.exception_handler(InvalidSessionIdError)
async def invalid_session_id_handler(request: Request, exc: InvalidSessionIdError) -> JSONResponse:
    """Handles malformed UUID strings with HTTP 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "retryable": False,
            }
        },
    )


@app.exception_handler(SessionNotFoundError)
async def session_not_found_handler(request: Request, exc: SessionNotFoundError) -> JSONResponse:
    """Handles nonexistent session queries with HTTP 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "retryable": False,
            }
        },
    )


@app.exception_handler(SessionClosedError)
async def session_closed_handler(request: Request, exc: SessionClosedError) -> JSONResponse:
    """Handles requests targeting closed or reset sessions with HTTP 409."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "retryable": False,
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handles Pydantic payload validation errors with standard HTTP 400 envelope."""
    errors = exc.errors()
    code = "INVALID_REQUEST"
    message = "Malformed JSON or invalid request parameters."
    details: dict = {}
    http_status = status.HTTP_400_BAD_REQUEST

    for err in errors:
        msg = err.get("msg", "")
        loc = err.get("loc", ())
        if "target_id" in loc:
            code = "TARGET_NOT_FOUND"
            bad_target = str(err.get("input", "unknown"))
            message = f"Target '{bad_target}' does not exist in the facility directory."
            http_status = status.HTTP_404_NOT_FOUND
            break
        elif "suspect_id" in loc or "accused_suspect_id" in loc:
            code = "TARGET_NOT_FOUND"
            bad_suspect = str(err.get("input", "unknown"))
            message = f"Suspect '{bad_suspect}' does not exist in the case roster."
            http_status = status.HTTP_404_NOT_FOUND
            break
        elif "Question cannot be empty" in msg:
            code = "EMPTY_QUESTION"
            message = "Question cannot be empty or contain only whitespace."
            break
        elif "Question exceeds maximum allowed length" in msg:
            code = "QUESTION_TOO_LONG"
            message = "Question exceeds maximum allowed length of 500 characters."
            details = {"max_length": 500, "provided_length": len(str(err.get("input", "")))}
            break

    # If details wasn't set specifically, include serializable error summaries
    if not details and http_status == status.HTTP_400_BAD_REQUEST:
        details = {
            "errors": [
                {
                    "loc": [str(x) for x in e.get("loc", ())],
                    "msg": str(e.get("msg", "")),
                    "type": str(e.get("type", "")),
                }
                for e in errors
            ]
        }

    return JSONResponse(
        status_code=http_status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details if details else None,
                "retryable": False,
            }
        },
    )


from game_engine import (
    EmptyQuestionError,
    EvidenceNotDiscoveredError,
    MaxAttemptsExceededError,
    QuestionTooLongError,
    RateLimitExceededError,
    SuspectNotFoundError,
    TargetNotFoundError,
    accuse_suspect,
    examine_target,
    interrogate_suspect,
    present_evidence,
    update_player_theories,
)
from models import (
    AccuseRequest,
    AccuseResponse,
    ExamineRequest,
    ExamineResponse,
    InterrogateRequest,
    InterrogateResponse,
    PresentEvidenceRequest,
    PresentEvidenceResponse,
    UpdateTheoriesRequest,
    UpdateTheoriesResponse,
)


@app.exception_handler(TargetNotFoundError)
async def target_not_found_handler(request: Request, exc: TargetNotFoundError) -> JSONResponse:
    """Handles invalid examine targets with HTTP 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "retryable": False,
            }
        },
    )


@app.exception_handler(SuspectNotFoundError)
async def suspect_not_found_handler(request: Request, exc: SuspectNotFoundError) -> JSONResponse:
    """Handles invalid suspect IDs with HTTP 404."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "retryable": False,
            }
        },
    )


@app.exception_handler(EmptyQuestionError)
async def empty_question_handler(request: Request, exc: EmptyQuestionError) -> JSONResponse:
    """Handles empty interrogation questions with HTTP 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "retryable": False,
            }
        },
    )


@app.exception_handler(QuestionTooLongError)
async def question_too_long_handler(request: Request, exc: QuestionTooLongError) -> JSONResponse:
    """Handles questions over 500 chars with HTTP 400."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "details": {"max_length": exc.max_length, "provided_length": exc.provided_length},
                "retryable": False,
            }
        },
    )


@app.exception_handler(RateLimitExceededError)
async def rate_limit_handler(request: Request, exc: RateLimitExceededError) -> JSONResponse:
    """Handles interrogation rate limit with HTTP 429 and Retry-After header."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(exc.retry_after_seconds)},
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "details": {
                    "retry_after_seconds": exc.retry_after_seconds,
                    "limit_per_minute": exc.limit_per_minute,
                },
                "retryable": True,
            }
        },
    )


@app.exception_handler(EvidenceNotDiscoveredError)
async def evidence_not_discovered_handler(request: Request, exc: EvidenceNotDiscoveredError) -> JSONResponse:
    """Handles presenting undiscovered evidence with HTTP 409."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "retryable": False,
            }
        },
    )


@app.exception_handler(MaxAttemptsExceededError)
async def max_attempts_exceeded_handler(request: Request, exc: MaxAttemptsExceededError) -> JSONResponse:
    """Handles accusation attempt on closed/exhausted case with HTTP 409."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": exc.code,
                "message": str(exc),
                "retryable": False,
            }
        },
    )


# ============================================================================
# 3. System & Configuration Endpoints
# ============================================================================

class HealthResponse(BaseModel):
    """Truthful health response reporting server status only."""
    status: str
    version: str
    timestamp: str


@app.get("/api/health", response_model=HealthResponse)
async def get_health() -> HealthResponse:
    """
    Health check endpoint reporting backend server status.
    Truthful, minimal, and free of secrets, model claims, or internal errors.
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
    )


@app.get("/api/config", response_model=ConfigResponse)
async def get_config() -> ConfigResponse:
    """
    Returns player-safe static game configuration and facility catalog.
    Guaranteed zero leaks: contains no solution keys or hidden guilt flags.
    """
    return get_public_config()


# ============================================================================
# 4. Session Management Endpoints
# ============================================================================

@app.post(
    "/api/sessions",
    response_model=SessionStateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session(body: Optional[CreateSessionRequest] = None) -> SessionStateResponse:
    """
    Initializes an isolated investigation session with a fresh Truth Ledger.
    Returns the initial public session state.
    """
    player_name = body.player_name if body else None
    session = session_store.create_session(player_name=player_name)
    return session.to_public_response()


@app.get("/api/sessions/{session_id}", response_model=SessionStateResponse)
async def get_session(session_id: str) -> SessionStateResponse:
    """
    Retrieves the public state of an active investigation session.
    Validates UUID format, existence, and active lifecycle status.
    """
    session = session_store.get_session(session_id, require_active=True)
    return session.to_public_response()


@app.post("/api/sessions/{session_id}/reset", response_model=ResetSessionResponse)
async def reset_session(session_id: str) -> ResetSessionResponse:
    """
    Marks the current session as RESET and returns a fresh, initialized session.
    The old session ID cannot be used for subsequent active gameplay.
    """
    old_session, new_session = session_store.reset_session(session_id)
    return ResetSessionResponse(
        previous_session_id=old_session.session_id,
        new_session_id=new_session.session_id,
        created_at=new_session.created_at,
        message="Investigation reset. Fresh session initialized.",
        new_session_state=new_session.to_public_response(),
    )


# ============================================================================
# 5. Gameplay & Investigation Action Endpoints
# ============================================================================

@app.post("/api/sessions/{session_id}/examine", response_model=ExamineResponse)
async def post_examine(session_id: str, body: ExamineRequest) -> ExamineResponse:
    """
    Inspects a physical location or equipment rack from the predefined target list.
    Repeated examination is idempotent: does not duplicate evidence or alter score.
    """
    session = session_store.get_session(session_id, require_active=True)
    return examine_target(session, body)


@app.post("/api/sessions/{session_id}/interrogate", response_model=InterrogateResponse)
async def post_interrogate(session_id: str, body: InterrogateRequest) -> InterrogateResponse:
    """
    Submits a free-form question to a suspect.
    Enforces per-session rate limits, 6-turn sliding history, and returns authored dialogue.
    """
    session = session_store.get_session(session_id, require_active=True)
    return interrogate_suspect(session, body)


@app.post("/api/sessions/{session_id}/present-evidence", response_model=PresentEvidenceResponse)
async def post_present_evidence(
    session_id: str, body: PresentEvidenceRequest
) -> PresentEvidenceResponse:
    """
    Confronts a suspect with an explicitly discovered evidence item to test for contradictions.
    """
    session = session_store.get_session(session_id, require_active=True)
    return present_evidence(session, body)


@app.post("/api/sessions/{session_id}/theories", response_model=UpdateTheoriesResponse)
async def post_theories(session_id: str, body: UpdateTheoriesRequest) -> UpdateTheoriesResponse:
    """
    Updates the player's deduction workbench in the Truth Ledger without submitting an accusation.
    """
    session = session_store.get_session(session_id, require_active=True)
    return update_player_theories(session, body)


@app.post("/api/sessions/{session_id}/accuse", response_model=AccuseResponse)
async def post_accuse(session_id: str, body: AccuseRequest) -> AccuseResponse:
    """
    Submits a formal indictment. Evaluates the accusation against the Canonical Solution Key.
    """
    # Note: require_active=False because post_accuse handles CLOSED/SOLVED internally with MAX_ATTEMPTS_EXCEEDED
    session = session_store.get_session(session_id, require_active=False)
    return accuse_suspect(session, body)

