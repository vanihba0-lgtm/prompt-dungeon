"""
Prompt Dungeon — Deterministic Game Engine (Step 9a: Examine Operation)
Canonical Reference: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0

This module contains the deterministic examine engine for Prompt Dungeon.
It is the SOLE place that translates examination requests into session-state
mutations and structured API responses.

Design constraints (from canonical docs):
  - No LLM calls, network calls, random output, or new dependencies.
  - No import of CANONICAL_SOLUTION or suspect guilt flags — spoiler safety.
  - All canonical data is read from case_data.CANONICAL_EVIDENCE_CATALOG and
    case_data.TARGET_NARRATIVES; all mappings come from models.TARGET_EVIDENCE_MAP.
  - Session state is mutated only through the session_store interface.
  - Repeated examination is strictly idempotent (no duplicate facts or evidence IDs).
"""

from datetime import datetime, timezone
from typing import Optional

from models import (
    DiscoveredFact,
    EvidenceCatalogItem,
    EvidenceId,
    ExamineRequest,
    ExamineResponse,
    SessionEventType,
    TargetId,
    TARGET_EVIDENCE_MAP,
)
from case_data import CANONICAL_EVIDENCE_CATALOG, TARGET_NARRATIVES
from session_store import SessionState


# ============================================================================
# 1. Fact ID Registry
# Canonical fact_id strings matching the contract example (FACT_E01_SHUNT).
# Derived from evidence short-keys; kept stable and human-readable.
# ============================================================================

_FACT_ID_MAP: dict[EvidenceId, str] = {
    EvidenceId.E_01: "FACT_E01_SHUNT",
    EvidenceId.E_02: "FACT_E02_TERMINAL_LOG",
    EvidenceId.E_03: "FACT_E03_KEYCARD_LOG",
    EvidenceId.E_04: "FACT_E04_APPRAISAL_MEMO",
    EvidenceId.E_05: "FACT_E05_GOLD_LIGHTER",
    EvidenceId.E_06: "FACT_E06_DEBT_ULTIMATUM",
    EvidenceId.E_07: "FACT_E07_FIBER_SOLVENT",
    EvidenceId.E_08: "FACT_E08_WAITER_SLIP",
    EvidenceId.E_09: "FACT_E09_USB_FORUM_LOG",
    EvidenceId.E_10: "FACT_E10_HATCH_SCUFFS",
    EvidenceId.E_11: "FACT_E11_SOLVENT_CANISTER",
    EvidenceId.E_12: "FACT_E12_DICTAPHONE_MEMO",
}

# Canonical forensic summaries for each fact (derived from case-spec §4 interpretations).
# These are player-safe: they describe physical findings without exposing the
# solution key, culprit identity, guilt flags, or hidden dossier information.
_FACT_SUMMARY_MAP: dict[EvidenceId, str] = {
    EvidenceId.E_01: (
        "Vitrine was bypassed using a custom nitrogen equalizing shunt, "
        "disproving forced entry."
    ),
    EvidenceId.E_02: (
        "Camera blackout window confirmed: 9:14:48 PM to 9:19:10 PM, "
        "caused by an internal terminal script."
    ),
    EvidenceId.E_03: (
        "Cryptographic badge log places conservator card #012 inside Service "
        "Corridor B from 21:15:30 to 21:18:22, overlapping the theft window."
    ),
    EvidenceId.E_04: (
        "Reassembled shredder fragments confirm an unauthorized off-the-books "
        "private appraisal valuing the relic at $4.2M."
    ),
    EvidenceId.E_05: (
        "Engraved 18k gold lighter monogrammed 'C.W.' recovered in the restricted "
        "West Archive corridor, placing its owner there between 9:15–9:21 PM."
    ),
    EvidenceId.E_06: (
        "Violent extortion note demands £150,000 or 'the Aztec glass' by midnight "
        "tonight, establishing an urgent criminal motive."
    ),
    EvidenceId.E_07: (
        "Purple antistatic glove fibers and Hexane-12 solvent residue found on "
        "the vitrine locking cylinder, linking conservation equipment to the breach."
    ),
    EvidenceId.E_08: (
        "Catering slip #408 documents Mrs. Ward's table empty at 21:16 and "
        "reoccupied at 21:22, corroborating a 10-minute unexplained absence."
    ),
    EvidenceId.E_09: (
        "Forum chat transcript confirms a $500 crypto bounty for live firmware "
        "testing on Switch 04 at 9:15 PM, establishing reckless negligence."
    ),
    EvidenceId.E_10: (
        "Fresh shoe scuffs and industrial grease on a concealed dumbwaiter hatch "
        "reveal an unmonitored passage between Service Corridor B and the gallery."
    ),
    EvidenceId.E_11: (
        "A 5L Hexane-12 canister weighing 5.8 kg (3.8 kg over tare) contains the "
        "Obsidian Sun inside an acid-proof silicone bladder — artifact recovered."
    ),
    EvidenceId.E_12: (
        "Dictaphone recording timestamped 21:16:10 places the curator's voice in "
        "her office, backed by the 9:15 grandfather clock chime."
    ),
}


# ============================================================================
# 2. Custom Engine Exception
# ============================================================================

class TargetNotFoundError(Exception):
    """Raised when a target_id string is not a valid TargetId enum member."""

    def __init__(self, target_id: str) -> None:
        super().__init__(
            f"Target '{target_id}' does not exist in the facility directory."
        )
        self.target_id = target_id
        self.code = "TARGET_NOT_FOUND"


# ============================================================================
# 3. Examine Engine
# ============================================================================

def _resolve_target_id(raw_target_id: str) -> TargetId:
    """
    Validates that raw_target_id is a member of the TargetId enum.
    Returns the matching TargetId or raises TargetNotFoundError.
    """
    try:
        return TargetId(raw_target_id)
    except ValueError:
        raise TargetNotFoundError(raw_target_id)


def _build_discovered_fact(
    evidence_id: EvidenceId,
    discovered_at: str,
) -> DiscoveredFact:
    """
    Constructs an immutable DiscoveredFact from canonical catalog data.
    Does NOT reference CANONICAL_SOLUTION or any hidden guilt information.
    """
    evidence = CANONICAL_EVIDENCE_CATALOG[evidence_id]
    return DiscoveredFact(
        fact_id=_FACT_ID_MAP[evidence_id],
        evidence_id=evidence_id,
        title=evidence.title,
        summary=_FACT_SUMMARY_MAP[evidence_id],
        discovered_at=discovered_at,
        category=evidence.category,
    )


def _build_evidence_catalog_item(
    evidence_id: EvidenceId,
    already_discovered: bool,
) -> EvidenceCatalogItem:
    """
    Constructs the player-safe EvidenceCatalogItem from canonical data.
    Never leaks hidden fields, guilt flags, or canonical solution keys.
    """
    evidence = CANONICAL_EVIDENCE_CATALOG[evidence_id]
    return EvidenceCatalogItem(
        evidence_id=evidence_id,
        title=evidence.title,
        description=evidence.description,
        category=evidence.category,
        is_mandatory=evidence.is_mandatory,
        already_discovered=already_discovered,
    )


def examine_target(session: SessionState, request: ExamineRequest) -> ExamineResponse:
    """
    Deterministic examine operation.

    Behaviour (from api-contract.md §4.3 and case-spec.md §12):
    1. Validates the target_id against the TargetId enum.
       - Invalid → raises TargetNotFoundError (HTTP 404 TARGET_NOT_FOUND).
    2. Resolves the target's canonical evidence item via TARGET_EVIDENCE_MAP.
    3. First discovery:
       - Adds evidence_id to session.discovered_evidence_ids (no duplicates).
       - Creates a DiscoveredFact and appends it to session.truth_ledger_facts.
       - Appends an EXAMINE event to the session event log.
       - Returns ExamineResponse with truth_ledger_updated=True and new_fact set.
    4. Repeated examination (idempotent):
       - Does NOT add duplicate evidence or fact records.
       - Does NOT append a new event log entry.
       - Returns ExamineResponse with truth_ledger_updated=False and new_fact=None.
    5. Spoiler safety: CANONICAL_SOLUTION and guilt flags are never read or returned.
    6. Session invariant safety: only the passed-in session object is mutated;
       no shared canonical data structures are modified.

    Args:
        session: The active SessionState object retrieved from session_store.
        request: The validated ExamineRequest payload.

    Returns:
        ExamineResponse compliant with api-contract.md §4.3.

    Raises:
        TargetNotFoundError: If target_id is not a valid TargetId enum member.
    """
    # Step 1 — Validate and resolve target_id
    target_id: TargetId = _resolve_target_id(request.target_id.value)

    # Step 2 — Resolve canonical evidence for this target
    # TARGET_EVIDENCE_MAP covers all 12 targets; KeyError is impossible for valid TargetId.
    evidence_id: EvidenceId = TARGET_EVIDENCE_MAP[target_id]

    # Step 3 — Retrieve narrative texts (always present for any valid TargetId)
    narrative = TARGET_NARRATIVES[target_id]

    # Step 4 — Determine first-visit vs repeat-visit
    already_discovered: bool = evidence_id in session.discovered_evidence_ids

    if already_discovered:
        # ── Idempotent repeat examination ──────────────────────────────────
        inspection_narrative: str = narrative.repeat_inspection_narrative
        truth_ledger_updated: bool = False
        new_fact: Optional[DiscoveredFact] = None
    else:
        # ── First discovery ────────────────────────────────────────────────
        now_iso: str = datetime.now(timezone.utc).isoformat()

        # Mutate session state (discovery list and truth ledger)
        session.discovered_evidence_ids.append(evidence_id)

        new_fact = _build_discovered_fact(evidence_id, now_iso)
        session.truth_ledger_facts.append(new_fact)

        # Audit log (deep-copy of the fact is not required here since
        # add_event creates a new SessionEventLog, not a reference to new_fact)
        session.add_event(
            event_type=SessionEventType.EXAMINE,
            target_id=target_id.value,
            summary=f"Examined {narrative.display_name} and recovered {evidence_id.value}.",
        )

        inspection_narrative = narrative.first_discovery_narrative
        truth_ledger_updated = True

    # Step 5 — Build the player-safe evidence catalog item
    uncovered_evidence: EvidenceCatalogItem = _build_evidence_catalog_item(
        evidence_id, already_discovered
    )

    return ExamineResponse(
        target_id=target_id,
        inspection_narrative=inspection_narrative,
        uncovered_evidence=uncovered_evidence,
        truth_ledger_updated=truth_ledger_updated,
        new_fact=new_fact,
    )


# ============================================================================
# 4. Interrogation Exceptions & Validation
# ============================================================================

class InterrogationError(Exception):
    """Base class for interrogation-related domain exceptions."""
    pass


class SuspectNotFoundError(InterrogationError):
    """Raised when suspect_id string is not a valid SuspectId enum member."""

    def __init__(self, suspect_id: str) -> None:
        super().__init__(
            f"Suspect '{suspect_id}' does not exist in the case roster."
        )
        self.suspect_id = suspect_id
        self.code = "TARGET_NOT_FOUND"


class EmptyQuestionError(InterrogationError):
    """Raised when question text is empty or contains only whitespace."""

    def __init__(self) -> None:
        super().__init__("Question cannot be empty or contain only whitespace.")
        self.code = "EMPTY_QUESTION"


class QuestionTooLongError(InterrogationError):
    """Raised when trimmed question text exceeds 500 characters."""

    def __init__(self, max_length: int = 500, provided_length: int = 0) -> None:
        super().__init__(
            f"Question exceeds maximum allowed length of {max_length} characters."
        )
        self.code = "QUESTION_TOO_LONG"
        self.max_length = max_length
        self.provided_length = provided_length


class RateLimitExceededError(InterrogationError):
    """Raised when interrogation rate limit (30 requests/minute) is exceeded."""

    def __init__(self, retry_after_seconds: int = 2, limit_per_minute: int = 30) -> None:
        super().__init__(
            f"Interrogation rate limit exceeded ({limit_per_minute} requests/minute). "
            "Please wait before asking another question."
        )
        self.code = "RATE_LIMIT_EXCEEDED"
        self.retry_after_seconds = retry_after_seconds
        self.limit_per_minute = limit_per_minute


# ============================================================================
# 5. Authored Fallback Dialogue Library & Deterministic Selection
# ============================================================================

from dataclasses import dataclass
from collections import deque
import time

from models import (
    CaseStatus,
    InterrogateRequest,
    InterrogateResponse,
    ModelDialogueStatus,
    SuspectId,
)
from session_store import DialogueTurn, SessionClosedError


@dataclass(frozen=True)
class FallbackDialogueEntry:
    """Authored fallback dialogue entry with optional lie statement tag."""
    reply: str
    recorded_statement_id: Optional[str] = None


FALLBACK_DIALOGUE_LIBRARY: dict[SuspectId, list[FallbackDialogueEntry]] = {
    SuspectId.ELIAS_VOSS: [
        FallbackDialogueEntry(
            reply=(
                "I was down in the basement restoration lab preparing mounting "
                "adhesives for tomorrow's exhibition. I never entered Service "
                "Corridor B or the gallery area after the 8:45 PM public inspection."
            ),
            recorded_statement_id="ELIAS_LIE_CORRIDOR",
        ),
        FallbackDialogueEntry(
            reply=(
                "All my specialized vitrine maintenance equipment, including the "
                "nitrogen equalizing shunts, remained locked in Cabinet 3 all evening."
            ),
            recorded_statement_id="ELIAS_LIE_TOOLS",
        ),
        FallbackDialogueEntry(
            reply=(
                "I have no financial complications whatsoever; my personal accounts "
                "are entirely in order. My sole concern is the preservation of antiquities."
            ),
            recorded_statement_id="ELIAS_LIE_FINANCES",
        ),
        FallbackDialogueEntry(
            reply=(
                "I checked the vitrine's atmospheric seal at 8:45 PM with Dr. Sen. "
                "The pressure was nominal at 1.05 atmospheres. Breaking the glass "
                "would trigger the acoustic vibration sensors instantly."
            ),
            recorded_statement_id=None,
        ),
        FallbackDialogueEntry(
            reply=(
                "As I have explained, I was in the basement conservation lab working "
                "with optical adhesive. I did not enter the gallery after 8:45 PM."
            ),
            recorded_statement_id="ELIAS_LIE_CORRIDOR",
        ),
    ],
    SuspectId.MIRA_SEN: [
        FallbackDialogueEntry(
            reply=(
                "I remained in the Grand Ballroom greeting patrons from 9:00 PM "
                "until I walked into the gallery at 9:22 PM to verify the vitrine."
            ),
            recorded_statement_id="MIRA_LIE_BALLROOM",
        ),
        FallbackDialogueEntry(
            reply=(
                "I have never discussed private commercial valuation of the "
                "Obsidian Sun with any third-party brokers. The relic belongs to the museum."
            ),
            recorded_statement_id="MIRA_LIE_APPRAISAL",
        ),
        FallbackDialogueEntry(
            reply=(
                "I did not take the artifact. It was the centerpiece of my life's "
                "academic curation. The museum would be bankrupted by scandal if this vanished."
            ),
            recorded_statement_id=None,
        ),
        FallbackDialogueEntry(
            reply=(
                "I oversee acquisition records and accession provenance. I have no "
                "knowledge of technical pressure bypasses or alarm wiring."
            ),
            recorded_statement_id=None,
        ),
    ],
    SuspectId.NOAH_REED: [
        FallbackDialogueEntry(
            reply=(
                "The camera feeds never cut out; there was just a momentary ambient "
                "lighting flicker in the display wings."
            ),
            recorded_statement_id="NOAH_LIE_CAMERAS",
        ),
        FallbackDialogueEntry(
            reply=(
                "I was actively monitoring live feeds the entire evening and ran no "
                "diagnostic operations or terminal commands from the security desk."
            ),
            recorded_statement_id="NOAH_LIE_SCRIPTS",
        ),
        FallbackDialogueEntry(
            reply=(
                "I never left the security control booth between 8:00 PM and the alarm. "
                "I monitor cables and network switches; I wouldn't even know who to sell a relic to."
            ),
            recorded_statement_id=None,
        ),
        FallbackDialogueEntry(
            reply=(
                "Look, the system is ancient. If there was a glitch, it was hardware "
                "instability, not anything I did deliberately."
            ),
            recorded_statement_id=None,
        ),
    ],
    SuspectId.CELESTE_WARD: [
        FallbackDialogueEntry(
            reply=(
                "I spent the entire evening between 9:00 PM and 9:25 PM enjoying "
                "champagne on the terrace in plain sight of the waitstaff."
            ),
            recorded_statement_id="CELESTE_LIE_TERRACE",
        ),
        FallbackDialogueEntry(
            reply=(
                "I have never stepped foot in the museum's private archive wing. "
                "I am a patron and donor, not an intruder."
            ),
            recorded_statement_id="CELESTE_LIE_ARCHIVES",
        ),
        FallbackDialogueEntry(
            reply=(
                "I offered seven million dollars legitimately. Why would I steal "
                "something I cannot legally display in my home?"
            ),
            recorded_statement_id=None,
        ),
        FallbackDialogueEntry(
            reply=(
                "I heard a faint metallic clattering inside the ventilation shaft "
                "around 9:16 PM while I was walking. Perhaps you should inspect your ductwork."
            ),
            recorded_statement_id=None,
        ),
    ],
}


# Session rate limit storage: session_id -> deque of float timestamps
_SESSION_RATE_LIMIT_TIMESTAMPS: dict[str, deque[float]] = {}


def _check_and_record_rate_limit(
    session_id: str,
    limit_per_minute: int = 30,
    window_seconds: float = 60.0,
    current_time: Optional[float] = None,
) -> None:
    """
    Enforces per-session rate limit (30 requests/minute).
    Drops rejected requests before touching session state.
    Raises RateLimitExceededError if limit is reached.
    """
    now = current_time if current_time is not None else time.time()
    if session_id not in _SESSION_RATE_LIMIT_TIMESTAMPS:
        _SESSION_RATE_LIMIT_TIMESTAMPS[session_id] = deque()

    timestamps = _SESSION_RATE_LIMIT_TIMESTAMPS[session_id]

    # Purge timestamps outside the rolling window
    cutoff = now - window_seconds
    while timestamps and timestamps[0] <= cutoff:
        timestamps.popleft()

    if len(timestamps) >= limit_per_minute:
        raise RateLimitExceededError(retry_after_seconds=2, limit_per_minute=limit_per_minute)

    timestamps.append(now)


def _resolve_suspect_id(raw_suspect: object) -> SuspectId:
    """Validates and resolves a suspect ID or raises SuspectNotFoundError."""
    if isinstance(raw_suspect, SuspectId):
        return raw_suspect
    if isinstance(raw_suspect, str):
        try:
            return SuspectId(raw_suspect)
        except ValueError:
            raise SuspectNotFoundError(raw_suspect)
    raise SuspectNotFoundError(str(raw_suspect))


def _validate_question_text(question: str) -> str:
    """Validates question bounds: 1 to 500 trimmed characters."""
    if not isinstance(question, str):
        raise EmptyQuestionError()
    trimmed = question.strip()
    if not trimmed:
        raise EmptyQuestionError()
    if len(trimmed) > 500:
        raise QuestionTooLongError(max_length=500, provided_length=len(trimmed))
    return trimmed


def _select_fallback_entry(
    suspect_id: SuspectId,
    question: str,
) -> FallbackDialogueEntry:
    """
    Deterministically selects a fallback dialogue entry for a suspect.
    Checks for thematic keywords first; if none match, falls back to hash modulo.
    """
    entries = FALLBACK_DIALOGUE_LIBRARY[suspect_id]
    q_lower = question.lower().strip()

    if suspect_id == SuspectId.ELIAS_VOSS:
        if any(w in q_lower for w in ("corridor", "where", "9:15", "blackout", "alibi", "movement", "pass")):
            return entries[0]  # ELIAS_LIE_CORRIDOR
        elif any(w in q_lower for w in ("tool", "shunt", "cabinet", "nitrogen", "vitrine", "bypass", "equipment")):
            return entries[1]  # ELIAS_LIE_TOOLS
        elif any(w in q_lower for w in ("debt", "money", "finance", "pawn", "extort", "owe", "account")):
            return entries[2]  # ELIAS_LIE_FINANCES
    elif suspect_id == SuspectId.MIRA_SEN:
        if any(w in q_lower for w in ("ballroom", "gala", "where", "alibi", "patron", "corridor", "office")):
            return entries[0]  # MIRA_LIE_BALLROOM
        elif any(w in q_lower for w in ("appraisal", "value", "vance", "sterling", "auction", "commercial", "broker")):
            return entries[1]  # MIRA_LIE_APPRAISAL
    elif suspect_id == SuspectId.NOAH_REED:
        if any(w in q_lower for w in ("camera", "feed", "blackout", "cctv", "monitor", "screen", "dark")):
            return entries[0]  # NOAH_LIE_CAMERAS
        elif any(w in q_lower for w in ("script", "terminal", "switch", "command", "forum", "bounty", "firmware")):
            return entries[1]  # NOAH_LIE_SCRIPTS
    elif suspect_id == SuspectId.CELESTE_WARD:
        if any(w in q_lower for w in ("terrace", "drink", "champagne", "martini", "bar", "where", "alibi")):
            return entries[0]  # CELESTE_LIE_TERRACE
        elif any(w in q_lower for w in ("archive", "lighter", "wing", "west", "snoop", "hallway")):
            return entries[1]  # CELESTE_LIE_ARCHIVES

    idx = hash(q_lower) % len(entries)
    return entries[idx]


# ============================================================================
# 6. Interrogation Engine
# ============================================================================

def interrogate_suspect(
    session: SessionState,
    request: InterrogateRequest,
) -> InterrogateResponse:
    """
    Deterministic interrogation operation.

    Behaviour (from api-contract.md §4.3 and case-spec.md §12):
    1. Validates session state: raises SessionClosedError if CLOSED or RESET.
    2. Validates rate limit: drops rejected requests before touching session state.
    3. Validates suspect_id: raises SuspectNotFoundError if unknown suspect.
    4. Validates question length: raises EmptyQuestionError or QuestionTooLongError.
    5. Selects deterministic authored fallback entry based on suspect & question.
    6. Identifies if the reply contains a lie (recorded_statement_id):
       - If the lie has NOT been recorded yet in session, sets recorded_statement_id
         and registers it in session.recorded_statement_ids.
       - If already recorded, returns the same reply with recorded_statement_id=None.
    7. Creates DialogueTurn with:
       - is_fallback=True
       - model_status=ModelDialogueStatus.FALLBACK
       - fallback_reason="MODEL_UNAVAILABLE" (offline MVP runtime)
       - dialogue_turn_index = previous count + 1 (monotonic ≥ 1)
    8. Appends DialogueTurn to session dialogue history (enforces 6-turn sliding window).
    9. Invariant guarantees:
       - No evidence is unlocked or added to session.discovered_evidence_ids.
       - No contradiction is added to session.truth_ledger_contradictions.
       - No facts are added to session.truth_ledger_facts.
       - CANONICAL_SOLUTION and hidden culprit flags are never referenced or leaked.
       - Suspects other than the target suspect are completely unmodified.

    Args:
        session: Active SessionState instance.
        request: InterrogateRequest payload.

    Returns:
        InterrogateResponse compliant with api-contract.md §4.3.
    """
    # Step 1 — Session status check
    if session.case_status in (CaseStatus.RESET, CaseStatus.CLOSED):
        raise SessionClosedError(session.session_id, session.case_status)

    # Step 2 — Rate limit check (drops before touching session state)
    _check_and_record_rate_limit(session.session_id)

    # Step 3 — Suspect validation
    suspect_id = _resolve_suspect_id(request.suspect_id)

    # Step 4 — Question text validation
    validated_question = _validate_question_text(request.question)

    # Step 5 — Attempt live Gemma dialogue generation, with deterministic fallback
    from gemma_provider import generate_gemma_dialogue

    gemma_reply, model_status, fallback_reason = generate_gemma_dialogue(
        suspect_id, validated_question
    )

    if gemma_reply is not None:
        final_reply = gemma_reply
        is_fallback = False
        # In live generation, check if statement tag should still attach based on topic
        statement_id_to_report = None
        fallback_entry = _select_fallback_entry(suspect_id, validated_question)
        if fallback_entry.recorded_statement_id:
            if fallback_entry.recorded_statement_id not in session.recorded_statement_ids:
                statement_id_to_report = fallback_entry.recorded_statement_id
    else:
        # Fall back to deterministic authored entry
        fallback_entry = _select_fallback_entry(suspect_id, validated_question)
        final_reply = fallback_entry.reply
        is_fallback = True
        model_status = ModelDialogueStatus.FALLBACK
        if fallback_reason is None:
            fallback_reason = "MODEL_UNAVAILABLE"

        # Step 6 — Statement recording logic (track new lies)
        statement_id_to_report = None
        if fallback_entry.recorded_statement_id:
            if fallback_entry.recorded_statement_id not in session.recorded_statement_ids:
                statement_id_to_report = fallback_entry.recorded_statement_id

    # Step 7 — Compute turn index (monotonic ≥ 1)
    next_turn_index = session.total_dialogue_turns.get(suspect_id, 0) + 1
    now_iso = datetime.now(timezone.utc).isoformat()

    # Step 8 — Construct DialogueTurn and append to session
    turn = DialogueTurn(
        suspect_id=suspect_id,
        question=validated_question,
        reply=final_reply,
        recorded_statement_id=statement_id_to_report,
        is_fallback=is_fallback,
        model_status=model_status,
        fallback_reason=fallback_reason,
        dialogue_turn_index=next_turn_index,
        timestamp=now_iso,
    )
    session.add_dialogue_turn(turn)

    # Step 9 — Return public InterrogateResponse
    return InterrogateResponse(
        suspect_id=suspect_id,
        question=validated_question,
        reply=final_reply,
        recorded_statement_id=statement_id_to_report,
        is_fallback=is_fallback,
        model_status=model_status,
        fallback_reason=fallback_reason,
        dialogue_turn_index=next_turn_index,
        timestamp=now_iso,
    )


# ============================================================================
# 7. Evidence Presentation (Contradiction Engine)
# ============================================================================

class EvidencePresentationError(Exception):
    """Base class for evidence presentation exceptions."""
    pass


class EvidenceNotDiscoveredError(EvidencePresentationError):
    """Raised when player presents evidence not yet discovered (HTTP 409)."""

    def __init__(self, evidence_id: str) -> None:
        super().__init__(
            f"Evidence '{evidence_id}' cannot be presented because it has not yet "
            "been discovered in the investigation."
        )
        self.evidence_id = evidence_id
        self.code = "EVIDENCE_NOT_DISCOVERED"


from models import (
    AccuseRequest,
    AccuseResponse,
    CanonicalSolutionReveal,
    PresentEvidenceRequest,
    PresentEvidenceResponse,
    RuleId,
    ScoreBreakdown,
    UpdateTheoriesRequest,
    UpdateTheoriesResponse,
    ValidatedContradiction,
    Verdict,
)
from case_data import CANONICAL_SOLUTION, CONTRADICTION_RULES


# Mapping from (SuspectId, EvidenceId) to applicable RuleId and required statement tag
_CONTRADICTION_TRIGGER_MAP: dict[tuple[SuspectId, EvidenceId], tuple[RuleId, Optional[str]]] = {
    # C-01: Elias Voss refuted by E-03 (swipe into corridor)
    (SuspectId.ELIAS_VOSS, EvidenceId.E_03): (RuleId.C_01, "ELIAS_LIE_CORRIDOR"),
    # C-02: Elias Voss refuted by E-01 (or E-07) regarding vitrine tools
    (SuspectId.ELIAS_VOSS, EvidenceId.E_01): (RuleId.C_02, "ELIAS_LIE_TOOLS"),
    (SuspectId.ELIAS_VOSS, EvidenceId.E_07): (RuleId.C_02, "ELIAS_LIE_TOOLS"),
    # C-03: Elias Voss refuted by E-06 regarding debt/finances
    (SuspectId.ELIAS_VOSS, EvidenceId.E_06): (RuleId.C_03, "ELIAS_LIE_FINANCES"),
    # C-04: Noah Reed refuted by E-02 regarding camera failure
    (SuspectId.NOAH_REED, EvidenceId.E_02): (RuleId.C_04, "NOAH_LIE_CAMERAS"),
    # C-05: Noah Reed refuted by E-09 regarding scripts/bounty
    (SuspectId.NOAH_REED, EvidenceId.E_09): (RuleId.C_05, "NOAH_LIE_SCRIPTS"),
    # C-06: Dr. Mira Sen refuted by E-03 regarding ballroom alibi
    (SuspectId.MIRA_SEN, EvidenceId.E_03): (RuleId.C_06, "MIRA_LIE_BALLROOM"),
    # C-07: Dr. Mira Sen refuted by E-04 (or E-12) regarding private appraisal
    (SuspectId.MIRA_SEN, EvidenceId.E_04): (RuleId.C_07, "MIRA_LIE_APPRAISAL"),
    (SuspectId.MIRA_SEN, EvidenceId.E_12): (RuleId.C_07, "MIRA_LIE_APPRAISAL"),
    # C-08: Celeste Ward refuted by E-05 (or E-08) regarding terrace alibi / archives
    (SuspectId.CELESTE_WARD, EvidenceId.E_05): (RuleId.C_08, "CELESTE_LIE_TERRACE"),
    (SuspectId.CELESTE_WARD, EvidenceId.E_08): (RuleId.C_08, "CELESTE_LIE_TERRACE"),
}

# Neutral dismissal reactions when evidence doesn't contradict or statement hasn't been uttered
_NEUTRAL_DISMISSAL_REACTIONS: dict[SuspectId, str] = {
    SuspectId.ELIAS_VOSS: (
        "Elias inspects the item with detached scholarly interest. 'An intriguing piece "
        "of material culture, Detective, but it bears no relevance to my conservation duties.'"
    ),
    SuspectId.MIRA_SEN: (
        "Dr. Sen waves her hand dismissively. 'I am the curator of antiquities, Detective. "
        "Presenting random artifacts or papers without context proves nothing about my conduct.'"
    ),
    SuspectId.NOAH_REED: (
        "Noah shrugs nervously. 'That looks like some hardware or paper I don't touch. "
        "I monitor network cables and IP cameras; I have no idea what that is.'"
    ),
    SuspectId.CELESTE_WARD: (
        "Celeste Ward laughs coldly. 'A quaint exhibit, Detective, but completely irrelevant "
        "to me. My legal team will remind you that harassment of museum patrons has consequences.'"
    ),
}


def present_evidence(
    session: SessionState,
    request: PresentEvidenceRequest,
) -> PresentEvidenceResponse:
    """
    Deterministic evidence confrontation operation.

    Rules (api-contract.md §4.3 and case-spec.md §12):
    1. Check session status: raise SessionClosedError if CLOSED or RESET.
    2. Check discovered evidence: evidence_id MUST be in session.discovered_evidence_ids.
       If not, raise EvidenceNotDiscoveredError (HTTP 409 EVIDENCE_NOT_DISCOVERED).
    3. Determine if evidence matches a contradiction rule for this suspect.
    4. If it matches, check if the suspect has uttered the corresponding lie
       (recorded_statement_id in session.recorded_statement_ids).
    5. If lie was uttered:
       - Validate contradiction rule (C-01 to C-08).
       - If not already in truth_ledger_contradictions, append ValidatedContradiction (idempotent).
       - Record SessionEventType.CONTRADICTION event if first validation.
       - Return PresentEvidenceResponse with contradiction_validated=True.
    6. If not a contradiction or statement not yet made:
       - Return PresentEvidenceResponse with contradiction_validated=False, contradiction=None,
         and suspect neutral reaction.
    """
    # 1. Session status check
    if session.case_status in (CaseStatus.RESET, CaseStatus.CLOSED):
        raise SessionClosedError(session.session_id, session.case_status)

    suspect_id = _resolve_suspect_id(request.suspect_id)
    evidence_id = request.evidence_id if isinstance(request.evidence_id, EvidenceId) else EvidenceId(request.evidence_id)

    # 2. Evidence discovery precondition
    if evidence_id not in session.discovered_evidence_ids:
        raise EvidenceNotDiscoveredError(evidence_id.value)

    # 3. Check contradiction trigger match
    key = (suspect_id, evidence_id)
    trigger = _CONTRADICTION_TRIGGER_MAP.get(key)

    if trigger is not None:
        rule_id, required_statement_id = trigger
        # 4. Check if required lie was recorded in dialogue history
        statement_made = (
            required_statement_id is None
            or required_statement_id in session.recorded_statement_ids
        )

        if statement_made:
            rule = CONTRADICTION_RULES[rule_id]
            now_iso = datetime.now(timezone.utc).isoformat()

            validated_obj = ValidatedContradiction(
                rule_id=rule.rule_id,
                suspect_id=rule.suspect_id,
                disputed_claim=rule.disputed_claim,
                refuting_evidence_id=evidence_id,
                validation_state=rule.validation_state,
                validated_at=now_iso,
            )

            # Check if this rule is already validated in the session ledger
            already_validated = any(
                c.rule_id == rule.rule_id for c in session.truth_ledger_contradictions
            )

            if not already_validated:
                session.truth_ledger_contradictions.append(validated_obj)
                session.add_event(
                    event_type=SessionEventType.PRESENT_EVIDENCE,
                    target_id=rule.rule_id.value,
                    summary=f"Contradiction {rule.rule_id.value} validated against {suspect_id.value}: {rule.validation_state}.",
                )

            return PresentEvidenceResponse(
                suspect_id=suspect_id,
                evidence_id=evidence_id,
                contradiction_validated=True,
                contradiction=validated_obj,
                suspect_reaction=rule.suspect_reaction_dialogue,
                is_fallback=True,
                model_status=ModelDialogueStatus.FALLBACK,
            )

    # 6. No contradiction or prerequisite statement not recorded
    neutral_reaction = _NEUTRAL_DISMISSAL_REACTIONS.get(
        suspect_id,
        "The suspect glances at the evidence and remains unimpressed.",
    )
    return PresentEvidenceResponse(
        suspect_id=suspect_id,
        evidence_id=evidence_id,
        contradiction_validated=False,
        contradiction=None,
        suspect_reaction=neutral_reaction,
        is_fallback=True,
        model_status=ModelDialogueStatus.FALLBACK,
    )


# ============================================================================
# 8. Theory Updating Engine
# ============================================================================

def update_player_theories(
    session: SessionState,
    request: UpdateTheoriesRequest,
) -> UpdateTheoriesResponse:
    """
    Updates player's subjective deduction workbench in the Truth Ledger.

    Rules:
    1. Check session status: raise SessionClosedError if CLOSED or RESET.
    2. Updates theory hypothesis fields without mutating facts, evidence,
       contradictions, or score.
    3. Updates theories.updated_at timestamp.
    4. Appends a THEORY event to session event log.
    """
    if session.case_status in (CaseStatus.RESET, CaseStatus.CLOSED):
        raise SessionClosedError(session.session_id, session.case_status)

    now_iso = datetime.now(timezone.utc).isoformat()

    # Update workbench fields
    if request.suspected_culprit_id is not None:
        session.theories.suspected_culprit_id = request.suspected_culprit_id
    if request.motive_hypothesis is not None:
        session.theories.motive_hypothesis = request.motive_hypothesis
    if request.method_hypothesis is not None:
        session.theories.method_hypothesis = request.method_hypothesis
    if request.recovery_hypothesis is not None:
        session.theories.recovery_hypothesis = request.recovery_hypothesis

    session.theories.updated_at = now_iso

    session.add_event(
        event_type=SessionEventType.THEORY_UPDATE,
        target_id="THEORIES",
        summary="Player deduction workbench theories updated.",
    )

    return UpdateTheoriesResponse(
        updated_theories=session.theories.model_copy(),
        message="Truth Ledger theories successfully updated.",
    )


# ============================================================================
# 9. Accusation & Scoring Engine
# ============================================================================

class MaxAttemptsExceededError(Exception):
    """Raised when an accusation is submitted for an already closed case (HTTP 409)."""

    def __init__(self) -> None:
        super().__init__(
            "This case has reached its maximum of 3 accusation attempts and is closed."
        )
        self.code = "MAX_ATTEMPTS_EXCEEDED"


def _compute_rank(final_score: int, is_solved: bool) -> Optional[str]:
    """Computes detective rank based on case-spec §10.2."""
    if not is_solved:
        return "Case Dismissed (Failure)"
    if final_score >= 90:
        return "Master Detective (S-Rank)"
    if final_score >= 75:
        return "Senior Inspector (A-Rank)"
    if final_score >= 50:
        return "Probationary Sleuth (B-Rank)"
    return "Case Dismissed (Failure)"


def accuse_suspect(
    session: SessionState,
    request: AccuseRequest,
) -> AccuseResponse:
    """
    Evaluates a formal accusation against the canonical solution key.

    Rules (api-contract.md §5 and case-spec.md §10):
    1. Check session status: raise MaxAttemptsExceededError if already CLOSED,
       or SessionClosedError if RESET.
    2. Check attempts cap: if session.accusation_attempts >= 3, raise MaxAttemptsExceededError.
    3. Increment session.accusation_attempts by 1.
    4. Culprit dimension (25 pts - Gatekeeper):
       - Elias Voss is the canonical culprit.
       - Any other suspect -> culprit_pts = 0 and entire accusation fails.
    5. Motive dimension (25 pts):
       - E-06 and E-06 in session.discovered_evidence_ids.
       - Only awarded if culprit is correct.
    6. Method dimension (25 pts full, 10 pts partial):
       - Method evidence must be in session.discovered_evidence_ids.
       - Full (25 pts): has E-01 (bypass), E-10 (hatch), and (E-02 or E-07).
       - Partial (10 pts): has E-01 or E-10.
       - Only awarded if culprit is correct.
    7. Recovery dimension (25 pts):
       - E-11 and E-11 in session.discovered_evidence_ids.
       - Only awarded if culprit is correct.
    8. Penalty computation:
       - If culprit correct: penalty = (session.accusation_attempts - 1) * 15.
       - If culprit incorrect: penalty = session.accusation_attempts * 15.
       - final_score = max(0, raw_score - penalty).
       - Update session.current_penalty = penalty.
    9. Outcome & Verdict:
       - is_solved = (is_culprit_correct and final_score >= 50).
       - If is_solved:
         * session.case_status = CaseStatus.SOLVED
         * verdict = Verdict.CONVICTED
         * rank = _compute_rank(final_score, True)
         * canonical_solution_reveal populated
       - Else if session.accusation_attempts >= 3:
         * session.case_status = CaseStatus.CLOSED
         * verdict = Verdict.CASE_DISMISSED
         * rank = "Case Dismissed (Failure)"
         * canonical_solution_reveal populated
       - Else:
         * session.case_status = CaseStatus.ACTIVE
         * verdict = Verdict.INDICTMENT_REJECTED
         * rank = None
         * canonical_solution_reveal = None (SPOILER PROTECTION)
    10. Audit logging: appends ACCUSE event to session event log.
    """
    # 1. State check
    if session.case_status == CaseStatus.RESET:
        raise SessionClosedError(session.session_id, session.case_status)
    if session.case_status == CaseStatus.CLOSED or session.case_status == CaseStatus.SOLVED:
        raise MaxAttemptsExceededError()
    if session.accusation_attempts >= session.max_accusation_attempts:
        raise MaxAttemptsExceededError()

    session.accusation_attempts += 1

    # Canonical truth mapping
    canonical_culprit_id = CANONICAL_SOLUTION.culprit_id  # SuspectId.ELIAS_VOSS

    # 1. Culprit Gatekeeper (25 pts)
    is_culprit_correct = (request.accused_suspect_id == canonical_culprit_id)
    culprit_pts = 25 if is_culprit_correct else 0

    # 2. Motive Check (25 pts)
    is_motive_correct = (
        request.motive_evidence_id == CANONICAL_SOLUTION.motive_evidence_id
        and request.motive_evidence_id in session.discovered_evidence_ids
    )
    motive_pts = 25 if (is_culprit_correct and is_motive_correct) else 0

    # 3. Method Check (25 pts full / 10 pts partial)
    discovered_methods = set(request.method_evidence_ids).intersection(
        set(session.discovered_evidence_ids)
    )
    has_bypass = EvidenceId.E_01 in discovered_methods
    has_hatch = EvidenceId.E_10 in discovered_methods
    has_timing_or_trace = (
        EvidenceId.E_02 in discovered_methods or EvidenceId.E_07 in discovered_methods
    )

    if is_culprit_correct and has_bypass and has_hatch and has_timing_or_trace:
        method_pts = 25
    elif is_culprit_correct and (has_bypass or has_hatch):
        method_pts = 10
    else:
        method_pts = 0

    # 4. Artifact Recovery Check (25 pts)
    is_recovery_correct = (
        request.recovery_evidence_id == CANONICAL_SOLUTION.recovery_evidence_id
        and request.recovery_evidence_id in session.discovered_evidence_ids
    )
    recovery_pts = 25 if (is_culprit_correct and is_recovery_correct) else 0

    # 5. Penalties and final score
    raw_score = culprit_pts + motive_pts + method_pts + recovery_pts
    penalty = (
        (session.accusation_attempts - 1) * 15
        if is_culprit_correct
        else session.accusation_attempts * 15
    )
    final_score = max(0, min(100, raw_score - penalty))
    session.current_penalty = penalty

    # 6. Outcome evaluation
    is_solved = (is_culprit_correct and final_score >= 50)

    solution_reveal: Optional[CanonicalSolutionReveal] = None

    if is_solved:
        session.case_status = CaseStatus.SOLVED
        verdict = Verdict.CONVICTED
        rank = _compute_rank(final_score, is_solved=True)
        narrative_debrief = (
            "District Magistrate approves immediate arrest. Elias Voss confesses upon "
            "being presented with the Hexane-12 canister recovered from HazMat Cabinet 4. "
            "The Obsidian Sun is secured without damage."
        )
        solution_reveal = CanonicalSolutionReveal(
            culprit=CANONICAL_SOLUTION.culprit_name,
            motive=CANONICAL_SOLUTION.canonical_motive_summary,
            method="Nitrogen atmospheric shunt E-01 coupled to vitrine; ingress/egress via tapestry hatch E-10 during Noah Reed's 9:15-9:19 camera crash.",
            recovery_location=CANONICAL_SOLUTION.recovery_location_summary,
        )
    elif session.accusation_attempts >= session.max_accusation_attempts:
        session.case_status = CaseStatus.CLOSED
        verdict = Verdict.CASE_DISMISSED
        rank = "Case Dismissed (Failure)"
        narrative_debrief = (
            "Three formal indictments have collapsed. The District Magistrate revokes "
            "your investigative authority and releases the suspects. The case is closed unsolved."
        )
        solution_reveal = CanonicalSolutionReveal(
            culprit=CANONICAL_SOLUTION.culprit_name,
            motive=CANONICAL_SOLUTION.canonical_motive_summary,
            method="Nitrogen atmospheric shunt E-01 coupled to vitrine; ingress/egress via tapestry hatch E-10.",
            recovery_location=CANONICAL_SOLUTION.recovery_location_summary,
        )
    else:
        # Case remains active
        verdict = Verdict.INDICTMENT_REJECTED
        rank = None
        narrative_debrief = (
            "The District Magistrate rejects the warrant. The evidence presented is deemed "
            "insufficient or circumstantial. The suspect remains detained for questioning, "
            "but you must solidify your proof before filing again."
        )
        solution_reveal = None  # Strict spoiler protection

    score_breakdown = ScoreBreakdown(
        culprit_score=culprit_pts,
        motive_score=motive_pts,
        method_score=method_pts,
        recovery_score=recovery_pts,
        attempt_penalty=penalty,
        final_score=final_score,
    )

    session.add_event(
        event_type=SessionEventType.ACCUSE,
        target_id=request.accused_suspect_id.value,
        summary=f"Accusation submitted against {request.accused_suspect_id.value}: verdict={verdict.value}, score={final_score}.",
    )

    attempts_remaining = max(0, session.max_accusation_attempts - session.accusation_attempts)

    return AccuseResponse(
        is_solved=is_solved,
        case_status=session.case_status,
        verdict=verdict,
        attempts_used=session.accusation_attempts,
        attempts_remaining=attempts_remaining,
        score_breakdown=score_breakdown,
        rank=rank,
        narrative_debrief=narrative_debrief,
        canonical_solution_reveal=solution_reveal,
    )


