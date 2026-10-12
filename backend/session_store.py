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
# 5. Session Store Interface & In-Memory Implementation
# ============================================================================

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
    def reset_session(self, session_id: str) -> Tuple[SessionState, SessionState]:
        """Marks old session as RESET and initializes a fresh replacement."""
        pass


class InMemorySessionStore(BaseSessionStore):
    """
    In-memory session store implementation for Prompt Dungeon MVP.
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
        """
        Retrieves a session by ID.
        Raises:
            InvalidSessionIdError: If session_id is not a valid UUIDv4.
            SessionNotFoundError: If session_id does not exist.
            SessionClosedError: If require_active=True and session is RESET or CLOSED.
        """
        normalized_id = validate_uuid4(session_id)

        session = self._sessions.get(normalized_id)
        if session is None:
            raise SessionNotFoundError(normalized_id)

        if require_active and session.case_status in (CaseStatus.RESET, CaseStatus.CLOSED):
            raise SessionClosedError(normalized_id, session.case_status)

        return session

    def reset_session(self, session_id: str) -> Tuple[SessionState, SessionState]:
        """
        Resets an existing investigation.
        Marks previous session as RESET and creates a fresh replacement session.
        Returns (old_session, new_session).
        """
        old_session = self.get_session(session_id, require_active=False)

        if old_session.case_status in (CaseStatus.RESET, CaseStatus.CLOSED):
            raise SessionClosedError(old_session.session_id, old_session.case_status)

        # Invalidate old session
        old_session.case_status = CaseStatus.RESET
        old_session.add_event(SessionEventType.EXAMINE, "SYSTEM", "Session marked as reset.")

        # Create fresh session, preserving player name
        new_session = self.create_session(player_name=old_session.player_name)
        new_session.add_event(SessionEventType.EXAMINE, "SYSTEM", "Session reset; fresh investigation started.")

        return old_session, new_session

    def count(self) -> int:
        """Returns total number of sessions currently stored."""
        return len(self._sessions)


# Global singleton instance for MVP backend runtime
session_store = InMemorySessionStore()
