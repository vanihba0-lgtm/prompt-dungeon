"""
Prompt Dungeon — In-Memory Session Store
Canonical Reference: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0

This module implements the internal session state and in-memory store for Prompt Dungeon.
Sessions are identified by UUIDv4 tokens and maintain isolated, independent mutable state.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Tuple
import uuid

from models import (
    CaseStatus,
    DiscoveredFact,
    EvidenceId,
    ModelDialogueStatus,
    PlayerTheories,
    SessionEventLog,
    SessionEventType,
    SessionStateResponse,
    SuspectId,
    TruthLedger,
    ValidatedContradiction,
)


# ============================================================================
# 1. Custom Session Exceptions
# ============================================================================

class SessionError(Exception):
    """Base class for session-related domain exceptions."""
    pass


class InvalidSessionIdError(SessionError):
    """Raised when a session ID is not a valid RFC 4122 UUIDv4 string (HTTP 400)."""
    def __init__(self, session_id: str):
        super().__init__(f"Session ID '{session_id}' must be a valid RFC 4122 UUIDv4.")
        self.session_id = session_id
        self.code = "INVALID_SESSION_ID"


class SessionNotFoundError(SessionError):
    """Raised when a session ID does not exist or has expired (HTTP 404)."""
    def __init__(self, session_id: str):
        super().__init__(f"Session '{session_id}' does not exist or has expired.")
        self.session_id = session_id
        self.code = "SESSION_NOT_FOUND"


class SessionClosedError(SessionError):
    """Raised when attempting actions on a session marked RESET or CLOSED (HTTP 409)."""
    def __init__(self, session_id: str, status: CaseStatus):
        super().__init__(f"Session '{session_id}' is marked as {status.value} and cannot accept new actions.")
        self.session_id = session_id
        self.status = status
        self.code = "SESSION_CLOSED"


# ============================================================================
# 2. UUID Validation Utility
# ============================================================================

def validate_uuid4(session_id: str) -> str:
    """
    Validates that a string is a well-formed RFC 4122 UUIDv4.
    Returns normalized lowercase UUID string or raises InvalidSessionIdError.
    """
    if not isinstance(session_id, str):
        raise InvalidSessionIdError(str(session_id))
    try:
        parsed = uuid.UUID(session_id, version=4)
        normalized = str(parsed).lower()
        if session_id.lower() != normalized:
            raise ValueError()
        return normalized
    except (ValueError, AttributeError, TypeError):
        raise InvalidSessionIdError(session_id)


# ============================================================================
# 3. Dialogue Turn History Model
# ============================================================================

@dataclass
class DialogueTurn:
    """Internal record of a single question-reply dialogue exchange."""
    suspect_id: SuspectId
    question: str
    reply: str
    recorded_statement_id: Optional[str]
    is_fallback: bool
    model_status: ModelDialogueStatus
    fallback_reason: Optional[str]
    dialogue_turn_index: int
    timestamp: str


# ============================================================================
# 4. Internal Mutable Session State
# ============================================================================

@dataclass
class SessionState:
    """
    Internal mutable session state representing an active investigation.
    Maintains complete isolation from other sessions and internal ground truth.
    """
    session_id: str
    created_at: str
    case_status: CaseStatus = CaseStatus.ACTIVE
    player_name: Optional[str] = None
    accusation_attempts: int = 0
    max_accusation_attempts: int = 3
    current_penalty: int = 0

    # Discovered evidence and interrogation tracking
    discovered_evidence_ids: List[EvidenceId] = field(default_factory=list)
    interrogated_suspect_ids: List[SuspectId] = field(default_factory=list)

    # Truth Ledger: facts, contradictions, and player theories
    truth_ledger_facts: List[DiscoveredFact] = field(default_factory=list)
    truth_ledger_contradictions: List[ValidatedContradiction] = field(default_factory=list)
    theories: PlayerTheories = field(default_factory=lambda: PlayerTheories(updated_at=datetime.now(timezone.utc).isoformat()))

    # Auditable event timeline
    recent_events: List[SessionEventLog] = field(default_factory=list)

    # Per-suspect sliding dialogue window (max 6 turns per suspect)
    dialogue_history: Dict[SuspectId, List[DialogueTurn]] = field(default_factory=lambda: {s: [] for s in SuspectId})

    # Monotonic total turn counter per suspect (never capped by the window).
    # Used by the engine to compute InterrogateResponse.dialogue_turn_index (≥ 1).
    total_dialogue_turns: Dict[SuspectId, int] = field(default_factory=lambda: {s: 0 for s in SuspectId})

    # Set of recorded false statement IDs uttered in this session
    recorded_statement_ids: Set[str] = field(default_factory=set)

    def add_event(self, event_type: SessionEventType, target_id: str, summary: str) -> None:
        """Appends an auditable event to the session event timeline."""
        event = SessionEventLog(
            event_type=event_type,
            target_id=target_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            summary=summary,
        )
        self.recent_events.append(event)

    def add_dialogue_turn(self, turn: DialogueTurn) -> None:
        """
        Records a dialogue turn for a specific suspect.
        Enforces the documented 6-turn sliding window per suspect.
        Updates interrogated suspects, total turn counts, and recorded statement sets.
        """
        suspect_id = turn.suspect_id
        if suspect_id not in self.dialogue_history:
            self.dialogue_history[suspect_id] = []

        self.dialogue_history[suspect_id].append(turn)

        # Enforce bounded history window (last 6 turns per suspect)
        if len(self.dialogue_history[suspect_id]) > 6:
            self.dialogue_history[suspect_id] = self.dialogue_history[suspect_id][-6:]

        # Increment monotonic total turn counter (never capped by window)
        self.total_dialogue_turns[suspect_id] = self.total_dialogue_turns.get(suspect_id, 0) + 1

        # Track interrogated suspects
        if suspect_id not in self.interrogated_suspect_ids:
            self.interrogated_suspect_ids.append(suspect_id)

        # Track recorded statement tag if suspect uttered a lie
        if turn.recorded_statement_id:
            self.recorded_statement_ids.add(turn.recorded_statement_id)

    def get_suspect_dialogue_history(self, suspect_id: SuspectId) -> List[DialogueTurn]:
        """Returns the bounded dialogue turns for a specific suspect."""
        return list(self.dialogue_history.get(suspect_id, []))

    def to_public_response(self) -> SessionStateResponse:
        """
        Serializes internal session state into the public SessionStateResponse.
        Guaranteed to contain zero solution keys or internal engine metadata.
        Deeply decouples models to prevent client mutations from modifying session state.
        """
        ledger = TruthLedger(
            facts=[f.model_copy() for f in self.truth_ledger_facts],
            contradictions=[c.model_copy() for c in self.truth_ledger_contradictions],
            theories=self.theories.model_copy(),
        )
        return SessionStateResponse(
            session_id=self.session_id,
            created_at=self.created_at,
            case_status=self.case_status,
            accusation_attempts=self.accusation_attempts,
            max_accusation_attempts=self.max_accusation_attempts,
            current_penalty=self.current_penalty,
            discovered_evidence_ids=list(self.discovered_evidence_ids),
            interrogated_suspect_ids=list(self.interrogated_suspect_ids),
            truth_ledger=ledger,
            recent_events=[e.model_copy() for e in self.recent_events],
        )


# ============================================================================
# 5. Session Store Interface, Serialization, and Implementations
# ============================================================================

def turn_to_dict(turn: DialogueTurn) -> dict:
    """Serializes DialogueTurn dataclass to JSON-compatible dictionary."""
    return {
        "suspect_id": turn.suspect_id.value if hasattr(turn.suspect_id, "value") else str(turn.suspect_id),
        "question": turn.question,
        "reply": turn.reply,
        "recorded_statement_id": turn.recorded_statement_id,
        "is_fallback": turn.is_fallback,
        "model_status": turn.model_status.value if hasattr(turn.model_status, "value") else str(turn.model_status),
        "fallback_reason": turn.fallback_reason,
        "dialogue_turn_index": turn.dialogue_turn_index,
        "timestamp": turn.timestamp,
    }


def turn_from_dict(data: dict) -> DialogueTurn:
    """Deserializes dictionary into a DialogueTurn dataclass."""
    return DialogueTurn(
        suspect_id=SuspectId(data["suspect_id"]),
        question=data["question"],
        reply=data["reply"],
        recorded_statement_id=data.get("recorded_statement_id"),
        is_fallback=bool(data.get("is_fallback", False)),
        model_status=ModelDialogueStatus(data["model_status"]),
        fallback_reason=data.get("fallback_reason"),
        dialogue_turn_index=int(data["dialogue_turn_index"]),
        timestamp=str(data["timestamp"]),
    )


def session_to_dict(s: SessionState) -> dict:
    """Serializes complete mutable SessionState to dictionary."""
    return {
        "session_id": s.session_id,
        "created_at": s.created_at,
        "case_status": s.case_status.value,
        "player_name": s.player_name,
        "accusation_attempts": s.accusation_attempts,
        "max_accusation_attempts": s.max_accusation_attempts,
        "current_penalty": s.current_penalty,
        "discovered_evidence_ids": [e.value if hasattr(e, "value") else str(e) for e in s.discovered_evidence_ids],
        "interrogated_suspect_ids": [sus.value if hasattr(sus, "value") else str(sus) for sus in s.interrogated_suspect_ids],
        "truth_ledger_facts": [f.model_dump() for f in s.truth_ledger_facts],
        "truth_ledger_contradictions": [c.model_dump() for c in s.truth_ledger_contradictions],
        "theories": s.theories.model_dump(),
        "recent_events": [e.model_dump() for e in s.recent_events],
        "dialogue_history": {
            k.value if hasattr(k, "value") else str(k): [turn_to_dict(t) for t in turns]
            for k, turns in s.dialogue_history.items()
        },
        "total_dialogue_turns": {
            k.value if hasattr(k, "value") else str(k): v
            for k, v in s.total_dialogue_turns.items()
        },
        "recorded_statement_ids": list(s.recorded_statement_ids),
    }


def session_from_dict(data: dict) -> SessionState:
    """Reconstructs SessionState from dictionary representation."""
    return SessionState(
        session_id=str(data["session_id"]),
        created_at=str(data["created_at"]),
        case_status=CaseStatus(data["case_status"]),
        player_name=data.get("player_name"),
        accusation_attempts=int(data.get("accusation_attempts", 0)),
        max_accusation_attempts=int(data.get("max_accusation_attempts", 3)),
        current_penalty=int(data.get("current_penalty", 0)),
        discovered_evidence_ids=[EvidenceId(e) for e in data.get("discovered_evidence_ids", [])],
        interrogated_suspect_ids=[SuspectId(sus) for sus in data.get("interrogated_suspect_ids", [])],
        truth_ledger_facts=[DiscoveredFact(**f) for f in data.get("truth_ledger_facts", [])],
        truth_ledger_contradictions=[ValidatedContradiction(**c) for c in data.get("truth_ledger_contradictions", [])],
        theories=PlayerTheories(**data["theories"]) if "theories" in data else PlayerTheories(),
        recent_events=[SessionEventLog(**e) for e in data.get("recent_events", [])],
        dialogue_history={
            SuspectId(k): [turn_from_dict(t) for t in turns]
            for k, turns in data.get("dialogue_history", {}).items()
        },
        total_dialogue_turns={
            SuspectId(k): int(v)
            for k, v in data.get("total_dialogue_turns", {}).items()
        },
        recorded_statement_ids=set(data.get("recorded_statement_ids", [])),
    )


class BaseSessionStore(ABC):
    """Abstract interface defining required session storage operations."""

    @abstractmethod
    def create_session(self, player_name: Optional[str] = None) -> SessionState:
        """Initializes and persists a fresh session."""
        pass

    @abstractmethod
    def get_session(self, session_id: str, require_active: bool = True) -> SessionState:
        """Retrieves a session by UUID, validating state and format."""
        pass

    @abstractmethod
    def save_session(self, session: SessionState) -> None:
        """Persists updated session state."""
        pass

    @abstractmethod
    def reset_session(self, session_id: str) -> Tuple[SessionState, SessionState]:
        """Marks old session as RESET and initializes a fresh replacement."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Returns total number of sessions currently stored."""
        pass


class InMemorySessionStore(BaseSessionStore):
    """
    In-memory session store implementation for Prompt Dungeon MVP and unit testing.
    Stores sessions in a Python dictionary keyed by UUIDv4 string.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, SessionState] = {}

    def create_session(self, player_name: Optional[str] = None) -> SessionState:
        """Creates a fresh, isolated session with a unique UUIDv4."""
        session_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        session = SessionState(
            session_id=session_id,
            created_at=now_iso,
            case_status=CaseStatus.ACTIVE,
            player_name=player_name,
            accusation_attempts=0,
            max_accusation_attempts=3,
            current_penalty=0,
            theories=PlayerTheories(updated_at=now_iso),
        )
        session.add_event(SessionEventType.EXAMINE, "SYSTEM", "Case session initialized.")

        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str, require_active: bool = True) -> SessionState:
        """Retrieves a session by ID."""
        normalized_id = validate_uuid4(session_id)

        session = self._sessions.get(normalized_id)
        if session is None:
            raise SessionNotFoundError(normalized_id)

        if require_active and session.case_status in (CaseStatus.RESET, CaseStatus.CLOSED):
            raise SessionClosedError(normalized_id, session.case_status)

        return session

    def save_session(self, session: SessionState) -> None:
        """Stores the session reference in memory."""
        self._sessions[session.session_id] = session

    def reset_session(self, session_id: str) -> Tuple[SessionState, SessionState]:
        """Resets an existing investigation."""
        old_session = self.get_session(session_id, require_active=False)

        if old_session.case_status in (CaseStatus.RESET, CaseStatus.CLOSED):
            raise SessionClosedError(old_session.session_id, old_session.case_status)

        old_session.case_status = CaseStatus.RESET
        old_session.add_event(SessionEventType.EXAMINE, "SYSTEM", "Session marked as reset.")

        new_session = self.create_session(player_name=old_session.player_name)
        new_session.add_event(SessionEventType.EXAMINE, "SYSTEM", "Session reset; fresh investigation started.")

        return old_session, new_session

    def count(self) -> int:
        """Returns total number of sessions currently stored."""
        return len(self._sessions)


class SQLiteSessionStore(BaseSessionStore):
    """
    SQLite-backed session store for persistent deployment (Vercel Serverless, Docker, VM).
    Durable across independent requests and warm serverless invocations.
    Uses SQLite WAL mode with standard library sqlite3 (zero external dependencies).
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        import os
        import tempfile

        if db_path is None:
            env_path = os.getenv("SESSION_DB_PATH")
            if env_path:
                db_path = env_path
            elif os.getenv("VERCEL") == "1":
                db_path = os.path.join(tempfile.gettempdir(), "prompt_dungeon_sessions.db")
            else:
                db_dir = os.path.dirname(os.path.abspath(__file__))
                # Fallback to temp if directory is not writable
                if os.access(db_dir, os.W_OK):
                    db_path = os.path.join(db_dir, "sessions.db")
                else:
                    db_path = os.path.join(tempfile.gettempdir(), "prompt_dungeon_sessions.db")

        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        import sqlite3
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    case_status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

    def save_session(self, session: SessionState) -> None:
        import json
        now_iso = datetime.now(timezone.utc).isoformat()
        payload = json.dumps(session_to_dict(session))
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO sessions (session_id, data, case_status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    data = excluded.data,
                    case_status = excluded.case_status,
                    updated_at = excluded.updated_at
                """,
                (session.session_id, payload, session.case_status.value, session.created_at, now_iso),
            )

    def create_session(self, player_name: Optional[str] = None) -> SessionState:
        session_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        session = SessionState(
            session_id=session_id,
            created_at=now_iso,
            case_status=CaseStatus.ACTIVE,
            player_name=player_name,
            accusation_attempts=0,
            max_accusation_attempts=3,
            current_penalty=0,
            theories=PlayerTheories(updated_at=now_iso),
        )
        session.add_event(SessionEventType.EXAMINE, "SYSTEM", "Case session initialized.")
        self.save_session(session)
        return session

    def get_session(self, session_id: str, require_active: bool = True) -> SessionState:
        import json
        normalized_id = validate_uuid4(session_id)

        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT data FROM sessions WHERE session_id = ?",
                (normalized_id,),
            )
            row = cur.fetchone()

        if row is None:
            raise SessionNotFoundError(normalized_id)

        session = session_from_dict(json.loads(row[0]))

        if require_active and session.case_status in (CaseStatus.RESET, CaseStatus.CLOSED):
            raise SessionClosedError(normalized_id, session.case_status)

        return session

    def reset_session(self, session_id: str) -> Tuple[SessionState, SessionState]:
        old_session = self.get_session(session_id, require_active=False)

        if old_session.case_status in (CaseStatus.RESET, CaseStatus.CLOSED):
            raise SessionClosedError(old_session.session_id, old_session.case_status)

        old_session.case_status = CaseStatus.RESET
        old_session.add_event(SessionEventType.EXAMINE, "SYSTEM", "Session marked as reset.")
        self.save_session(old_session)

        new_session = self.create_session(player_name=old_session.player_name)
        new_session.add_event(SessionEventType.EXAMINE, "SYSTEM", "Session reset; fresh investigation started.")
        self.save_session(new_session)

        return old_session, new_session

    def count(self) -> int:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT COUNT(*) FROM sessions")
            return cur.fetchone()[0]


def create_session_store() -> BaseSessionStore:
    """Factory creating the appropriate store based on runtime environment."""
    import os
    store_type = os.getenv("SESSION_STORE_TYPE", "sqlite").lower()
    if store_type == "memory":
        return InMemorySessionStore()
    try:
        return SQLiteSessionStore()
    except Exception:
        return InMemorySessionStore()


# Global singleton instance for backend runtime
session_store = create_session_store()

