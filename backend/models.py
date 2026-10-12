"""
Prompt Dungeon — Domain Models & API Schemas
Canonical Reference: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0
"""

from enum import StrEnum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# 1. Canonical Enumerations & Stable Identifiers
# ============================================================================

class CaseStatus(StrEnum):
    """Lifecycle status of an active investigation session."""
    ACTIVE = "ACTIVE"
    SOLVED = "SOLVED"
    CLOSED = "CLOSED"
    RESET = "RESET"


class Verdict(StrEnum):
    """Magistrate verdict resulting from an accusation attempt."""
    CONVICTED = "CONVICTED"
    INDICTMENT_REJECTED = "INDICTMENT_REJECTED"
    CASE_DISMISSED = "CASE_DISMISSED"


class SuspectId(StrEnum):
    """Stable identifiers for the four case suspects."""
    ELIAS_VOSS = "elias_voss"
    MIRA_SEN = "mira_sen"
    NOAH_REED = "noah_reed"
    CELESTE_WARD = "celeste_ward"


class EvidenceId(StrEnum):
    """Stable identifiers for the 12 canonical case evidence items (E-01 through E-12)."""
    E_01 = "E-01"
    E_02 = "E-02"
    E_03 = "E-03"
    E_04 = "E-04"
    E_05 = "E-05"
    E_06 = "E-06"
    E_07 = "E-07"
    E_08 = "E-08"
    E_09 = "E-09"
    E_10 = "E-10"
    E_11 = "E-11"
    E_12 = "E-12"


class RuleId(StrEnum):
    """Stable identifiers for the 8 contradiction rules (C-01 through C-08)."""
    C_01 = "C-01"
    C_02 = "C-02"
    C_03 = "C-03"
    C_04 = "C-04"
    C_05 = "C-05"
    C_06 = "C-06"
    C_07 = "C-07"
    C_08 = "C-08"


class TargetId(StrEnum):
    """Predefined facility targets for player examinations."""
    HELIODOR_PEDESTAL = "heliodor_pedestal"
    VITRINE_LATCH = "vitrine_latch"
    GALLERY_TAPESTRY = "gallery_tapestry"
    SERVER_RACK_02 = "server_rack_02"
    SECURITY_ACCESS_DB = "security_access_db"
    CURATOR_SHREDDER = "curator_shredder"
    CURATOR_DESK = "curator_desk"
    WEST_ARCHIVE_FLOOR = "west_archive_floor"
    WORKSHOP_CABINET_03 = "workshop_cabinet_03"
    BASEMENT_HAZMAT_04 = "basement_hazmat_04"
    TERRACE_CATERING_BAR = "terrace_catering_bar"
    TECHNICIAN_LOCKER = "technician_locker"


# Canonical 1-to-1 mapping from physical targets to yielded evidence items (docs/api-contract.md §2.2)
TARGET_EVIDENCE_MAP: Dict[TargetId, EvidenceId] = {
    TargetId.HELIODOR_PEDESTAL: EvidenceId.E_01,
    TargetId.SERVER_RACK_02: EvidenceId.E_02,
    TargetId.SECURITY_ACCESS_DB: EvidenceId.E_03,
    TargetId.CURATOR_SHREDDER: EvidenceId.E_04,
    TargetId.WEST_ARCHIVE_FLOOR: EvidenceId.E_05,
    TargetId.WORKSHOP_CABINET_03: EvidenceId.E_06,
    TargetId.VITRINE_LATCH: EvidenceId.E_07,
    TargetId.TERRACE_CATERING_BAR: EvidenceId.E_08,
    TargetId.TECHNICIAN_LOCKER: EvidenceId.E_09,
    TargetId.GALLERY_TAPESTRY: EvidenceId.E_10,
    TargetId.BASEMENT_HAZMAT_04: EvidenceId.E_11,
    TargetId.CURATOR_DESK: EvidenceId.E_12,
}


class EvidenceCategory(StrEnum):
    """Forensic classifications of evidence items."""
    FORENSIC = "FORENSIC"
    DIGITAL_LOG = "DIGITAL_LOG"
    DOCUMENT = "DOCUMENT"
    PHYSICAL_TRACE = "PHYSICAL_TRACE"


class ModelDialogueStatus(StrEnum):
    """Standardized model generation status for dialogue interactions."""
    SUCCESS = "success"
    FALLBACK = "fallback"
    UNAVAILABLE = "unavailable"


class SessionEventType(StrEnum):
    """Auditable session timeline event types."""
    EXAMINE = "EXAMINE"
    INTERROGATE = "INTERROGATE"
    PRESENT_EVIDENCE = "PRESENT_EVIDENCE"
    THEORY_UPDATE = "THEORY_UPDATE"
    ACCUSE = "ACCUSE"


# ============================================================================
# 2. Standard API Error Envelope
# ============================================================================

class ApiErrorDetails(BaseModel):
    """Structured machine-readable error payload."""
    code: str = Field(..., description="UPPER_SNAKE_CASE error code")
    message: str = Field(..., description="Human-readable explanation of error")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Optional structured context")
    retryable: bool = Field(default=False, description="Whether client may retry immediately")

    model_config = ConfigDict(extra="forbid")


class ApiErrorEnvelope(BaseModel):
    """Top-level error envelope for HTTP 4xx and 5xx responses."""
    error: ApiErrorDetails

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# 3. Truth Ledger Models (Facts, Contradictions, Theories)
# ============================================================================

class DiscoveredFact(BaseModel):
    """Immutable ground-truth fact verified by discovered evidence."""
    fact_id: str = Field(..., description="Unique fact identifier, e.g. FACT_E01_SHUNT")
    evidence_id: EvidenceId = Field(..., description="Associated evidence identifier")
    title: str = Field(..., description="Title of the discovered item")
    summary: str = Field(..., description="Objective forensic interpretation")
    discovered_at: str = Field(..., description="ISO-8601 discovery timestamp")
    category: EvidenceCategory = Field(..., description="Forensic category")

    model_config = ConfigDict(extra="forbid")


class ValidatedContradiction(BaseModel):
    """Engine-validated contradiction between a suspect statement and evidence."""
    rule_id: RuleId = Field(..., description="Canonical contradiction rule ID (C-01 to C-08)")
    suspect_id: SuspectId = Field(..., description="Suspect caught in contradiction")
    disputed_claim: str = Field(..., description="The false claim made by the suspect")
    refuting_evidence_id: EvidenceId = Field(..., description="Discovered evidence refuting claim")
    validation_state: str = Field(..., description="Validation result state, e.g. ALIBI_SHATTERED")
    validated_at: str = Field(..., description="ISO-8601 validation timestamp")

    model_config = ConfigDict(extra="forbid")


class PlayerTheories(BaseModel):
    """Subjective player hypothesis workbench. Distinct from ground-truth Facts."""
    suspected_culprit_id: Optional[SuspectId] = Field(default=None, description="Current suspect chosen by player")
    motive_hypothesis: str = Field(default="", description="Player's working hypothesis on motive")
    method_hypothesis: str = Field(default="", description="Player's working hypothesis on method")
    recovery_hypothesis: str = Field(default="", description="Player's working hypothesis on hiding spot")
    updated_at: str = Field(..., description="ISO-8601 update timestamp")

    model_config = ConfigDict(extra="forbid")


class TruthLedger(BaseModel):
    """The central state ledger isolating facts, contradictions, and theories."""
    facts: List[DiscoveredFact] = Field(default_factory=list, description="Verified forensic facts")
    contradictions: List[ValidatedContradiction] = Field(default_factory=list, description="Validated contradictions")
    theories: PlayerTheories = Field(..., description="Player's unverified hypothesis")

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# 4. Session State & Event Logging Models
# ============================================================================

class SessionEventLog(BaseModel):
    """Audit log entry of player investigation actions."""
    event_type: SessionEventType = Field(..., description="Category of player action")
    target_id: str = Field(..., description="Target or suspect acted upon")
    timestamp: str = Field(..., description="ISO-8601 action timestamp")
    summary: str = Field(..., description="Human-readable event summary")

    model_config = ConfigDict(extra="forbid")


class SessionStateResponse(BaseModel):
    """Complete active session state returned by GET /api/sessions/{session_id}."""
    session_id: str = Field(..., description="UUIDv4 session token")
    created_at: str = Field(..., description="ISO-8601 creation timestamp")
    case_status: CaseStatus = Field(default=CaseStatus.ACTIVE, description="Current investigation status")
    accusation_attempts: int = Field(default=0, ge=0, le=3, description="Accusation attempts used")
    max_accusation_attempts: int = Field(default=3, description="Maximum allowed attempts")
    current_penalty: int = Field(default=0, ge=0, description="Cumulative score penalty accrued")
    discovered_evidence_ids: List[EvidenceId] = Field(default_factory=list, description="Discovered evidence IDs")
    interrogated_suspect_ids: List[SuspectId] = Field(default_factory=list, description="Interrogated suspect IDs")
    truth_ledger: TruthLedger = Field(..., description="Active Truth Ledger")
    recent_events: List[SessionEventLog] = Field(default_factory=list, description="Audit event log")

    model_config = ConfigDict(extra="forbid")


class CreateSessionRequest(BaseModel):
    """Optional payload for initializing a new session."""
    player_name: Optional[str] = Field(default=None, max_length=100, description="Optional detective display name")

    model_config = ConfigDict(extra="forbid")


class ResetSessionResponse(BaseModel):
    """Response returned upon resetting a session."""
    previous_session_id: str = Field(..., description="Invalidated session ID")
    new_session_id: str = Field(..., description="Fresh UUIDv4 session ID")
    created_at: str = Field(..., description="ISO-8601 creation timestamp")
    message: str = Field(..., description="Human-readable reset confirmation")
    new_session_state: SessionStateResponse = Field(..., description="Fresh initialized session state")

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# 5. Interrogation & Dialogue Models
# ============================================================================

class InterrogateRequest(BaseModel):
    """Request payload for suspect questioning."""
    suspect_id: SuspectId = Field(..., description="Target suspect to question")
    question: str = Field(..., description="Free-form question text (1 to 500 characters)")

    model_config = ConfigDict(extra="forbid")

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Question cannot be empty or contain only whitespace.")
        if len(trimmed) > 500:
            raise ValueError("Question exceeds maximum allowed length of 500 characters.")
        return trimmed


class InterrogateResponse(BaseModel):
    """Dialogue response returned by POST /interrogate."""
    suspect_id: SuspectId = Field(..., description="Suspect responding")
    question: str = Field(..., description="Question that was asked")
    reply: str = Field(..., description="Suspect's conversational reply")
    recorded_statement_id: Optional[str] = Field(default=None, description="Statement tag if lie recorded")
    is_fallback: bool = Field(..., description="Whether reply originated from fallback dialogue")
    model_status: ModelDialogueStatus = Field(..., description="Model status (success, fallback, unavailable)")
    fallback_reason: Optional[str] = Field(default=None, description="Reason fallback was invoked, if applicable")
    dialogue_turn_index: int = Field(..., ge=1, description="Sequential dialogue turn index")
    timestamp: str = Field(..., description="ISO-8601 timestamp")

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# 6. Physical Examination & Evidence Models
# ============================================================================

class EvidenceCatalogItem(BaseModel):
    """Metadata for an evidence item as cataloged during inspection."""
    evidence_id: EvidenceId = Field(..., description="Canonical evidence ID")
    title: str = Field(..., description="Name of the evidence item")
    description: str = Field(..., description="Detailed forensic description")
    category: EvidenceCategory = Field(..., description="Forensic category")
    is_mandatory: bool = Field(..., description="Whether mandatory for conviction")
    already_discovered: bool = Field(default=False, description="Whether previously discovered")

    model_config = ConfigDict(extra="forbid")


class ExamineRequest(BaseModel):
    """Request payload for inspecting a physical location/object."""
    target_id: TargetId = Field(..., description="Facility target identifier from catalog")

    model_config = ConfigDict(extra="forbid")


class ExamineResponse(BaseModel):
    """Response returned upon examining a target."""
    target_id: TargetId = Field(..., description="Target that was inspected")
    inspection_narrative: str = Field(..., description="Narrative description of what was observed")
    uncovered_evidence: Optional[EvidenceCatalogItem] = Field(default=None, description="Evidence item found")
    truth_ledger_updated: bool = Field(..., description="Whether a new Fact was recorded")
    new_fact: Optional[DiscoveredFact] = Field(default=None, description="Newly established Fact, if any")

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# 7. Evidence Presentation Models (Contradiction Testing)
# ============================================================================

class PresentEvidenceRequest(BaseModel):
    """Request payload for presenting evidence to a suspect."""
    suspect_id: SuspectId = Field(..., description="Target suspect")
    evidence_id: EvidenceId = Field(..., description="Discovered evidence ID presented")

    model_config = ConfigDict(extra="forbid")


class PresentEvidenceResponse(BaseModel):
    """Response returned after confronting suspect with evidence."""
    suspect_id: SuspectId = Field(..., description="Suspect confronted")
    evidence_id: EvidenceId = Field(..., description="Evidence that was presented")
    contradiction_validated: bool = Field(..., description="Whether a contradiction rule was validated")
    contradiction: Optional[ValidatedContradiction] = Field(default=None, description="Validated contradiction")
    suspect_reaction: str = Field(..., description="Suspect's behavioral reaction")
    is_fallback: bool = Field(..., description="Whether reaction text came from fallback")
    model_status: ModelDialogueStatus = Field(..., description="Model status")

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# 8. Theory Updating Models
# ============================================================================

class UpdateTheoriesRequest(BaseModel):
    """Request payload for updating player hypothesis notes."""
    suspected_culprit_id: Optional[SuspectId] = Field(default=None, description="Suspect chosen by player")
    motive_hypothesis: Optional[str] = Field(default=None, max_length=1000, description="Motive theory notes")
    method_hypothesis: Optional[str] = Field(default=None, max_length=1000, description="Method theory notes")
    recovery_hypothesis: Optional[str] = Field(default=None, max_length=1000, description="Recovery theory notes")

    model_config = ConfigDict(extra="forbid")


class UpdateTheoriesResponse(BaseModel):
    """Response returned after updating theories."""
    updated_theories: PlayerTheories = Field(..., description="Current player theory workbench")
    message: str = Field(..., description="Confirmation message")

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# 9. Accusation & Scoring Models
# ============================================================================

class AccuseRequest(BaseModel):
    """Request payload submitting a formal indictment."""
    accused_suspect_id: SuspectId = Field(..., description="Indicted suspect")
    motive_evidence_id: EvidenceId = Field(..., description="Discovered evidence proving motive")
    method_evidence_ids: List[EvidenceId] = Field(..., min_length=2, description="Discovered evidence proving method (min 2)")
    recovery_evidence_id: EvidenceId = Field(..., description="Discovered evidence proving artifact recovery")
    detective_statement: str = Field(..., description="Formal rationale statement (1 to 1000 characters)")

    model_config = ConfigDict(extra="forbid")

    @field_validator("detective_statement")
    @classmethod
    def validate_statement(cls, value: str) -> str:
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Detective statement cannot be empty.")
        if len(trimmed) > 1000:
            raise ValueError("Detective statement exceeds 1000 characters.")
        return trimmed


class ScoreBreakdown(BaseModel):
    """Detailed score component breakdown (Base 100)."""
    culprit_score: int = Field(..., ge=0, le=25, description="Points awarded for culprit (0 or 25)")
    motive_score: int = Field(..., ge=0, le=25, description="Points awarded for motive (0 or 25)")
    method_score: int = Field(..., ge=0, le=25, description="Points awarded for method (0, 10, or 25)")
    recovery_score: int = Field(..., ge=0, le=25, description="Points awarded for artifact recovery (0 or 25)")
    attempt_penalty: int = Field(..., ge=0, description="Points deducted for failed attempts")
    final_score: int = Field(..., ge=0, le=100, description="Final score clamped to range [0, 100]")

    model_config = ConfigDict(extra="forbid")


class CanonicalSolutionReveal(BaseModel):
    """Canonical ground truth debrief. Only returned on case completion."""
    culprit: str = Field(..., description="Canonical culprit name")
    motive: str = Field(..., description="Canonical motive summary")
    method: str = Field(..., description="Canonical bypass & route summary")
    recovery_location: str = Field(..., description="Canonical hiding location")

    model_config = ConfigDict(extra="forbid")


class AccuseResponse(BaseModel):
    """Response returned upon submitting an accusation."""
    is_solved: bool = Field(..., description="Whether accusation successfully solved the case")
    case_status: CaseStatus = Field(..., description="Updated case status (ACTIVE, SOLVED, CLOSED)")
    verdict: Verdict = Field(..., description="Verdict issued by Magistrate")
    attempts_used: int = Field(..., ge=1, le=3, description="Total attempts used so far")
    attempts_remaining: int = Field(..., ge=0, le=2, description="Remaining attempts before dismissal")
    score_breakdown: ScoreBreakdown = Field(..., description="Score points breakdown")
    rank: Optional[str] = Field(default=None, description="Final detective rank if case completed")
    narrative_debrief: str = Field(..., description="Magistrate decision narrative")
    canonical_solution_reveal: Optional[CanonicalSolutionReveal] = Field(
        default=None,
        description="Ground truth reveal; strictly null unless case is SOLVED or CLOSED",
    )

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# 10. Static Configuration Models (GET /api/config)
# ============================================================================

class CaseMeta(BaseModel):
    """Static metadata describing the mystery case."""
    case_id: str
    case_title: str
    incident_time: str
    facility: str

    model_config = ConfigDict(extra="forbid")


class GameRules(BaseModel):
    """Static gameplay constraints and limits."""
    max_accusation_attempts: int = 3
    penalty_per_failed_accusation: int = 15
    history_window_turns: int = 6
    rate_limit_interrogations_per_minute: int = 30
    max_question_length: int = 500

    model_config = ConfigDict(extra="forbid")


class SuspectProfile(BaseModel):
    """Public suspect card for frontend display."""
    suspect_id: SuspectId
    name: str
    role: str
    avatar: str
    bio: str

    model_config = ConfigDict(extra="forbid")


class LocationProfile(BaseModel):
    """Public facility location target for frontend exploration."""
    target_id: TargetId
    name: str
    zone: str

    model_config = ConfigDict(extra="forbid")


class ConfigResponse(BaseModel):
    """Static configuration bundle returned by GET /api/config."""
    case_meta: CaseMeta
    rules: GameRules
    suspects: List[SuspectProfile]
    locations: List[LocationProfile]

    model_config = ConfigDict(extra="forbid")
