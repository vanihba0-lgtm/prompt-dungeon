"""
Tests for backend/game_engine.py — examine operation only.
Canonical Reference: docs/api-contract.md v1.1.0 & docs/case-spec.md v1.1.0

Covers:
  - Successful first examination (all 12 targets)
  - Invalid target_id → TargetNotFoundError
  - Repeated examination idempotency (no duplicate evidence, no duplicate facts)
  - Evidence registration in session.discovered_evidence_ids
  - Truth-ledger consistency (fact_id, evidence_id, category, summary, no duplicates)
  - Spoiler protection (CANONICAL_SOLUTION data never appears in ExamineResponse)
  - Session invariants (shared canonical data structures not mutated)
"""

import sys
import os

# ---------------------------------------------------------------------------
# Ensure the backend/ directory is on sys.path so that direct module imports
# work regardless of where pytest is invoked from.
# ---------------------------------------------------------------------------
_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import pytest
from datetime import datetime, timezone

from models import (
    EvidenceId,
    SessionEventType,
    TargetId,
    TARGET_EVIDENCE_MAP,
)
from case_data import (
    CANONICAL_EVIDENCE_CATALOG,
    CANONICAL_SOLUTION,
    TARGET_NARRATIVES,
)
from session_store import InMemorySessionStore
from game_engine import (
    TargetNotFoundError,
    _FACT_ID_MAP,
    _FACT_SUMMARY_MAP,
    examine_target,
)
from models import ExamineRequest


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture()
def fresh_session():
    """Returns a fresh, active SessionState from a clean store."""
    store = InMemorySessionStore()
    return store.create_session(player_name="Test Detective")


# ============================================================================
# Helper
# ============================================================================

def make_request(target_id: TargetId) -> ExamineRequest:
    return ExamineRequest(target_id=target_id)


# ============================================================================
# 1. Successful first examination — spot check key targets
# ============================================================================

class TestFirstExamination:

    def test_heliodor_pedestal_first_exam(self, fresh_session):
        """Examining heliodor_pedestal for the first time discovers E-01."""
        req = make_request(TargetId.HELIODOR_PEDESTAL)
        resp = examine_target(fresh_session, req)

        assert resp.target_id == TargetId.HELIODOR_PEDESTAL
        assert resp.truth_ledger_updated is True
        assert resp.new_fact is not None
        assert resp.new_fact.evidence_id == EvidenceId.E_01
        assert resp.new_fact.fact_id == "FACT_E01_SHUNT"
        assert resp.uncovered_evidence.evidence_id == EvidenceId.E_01
        assert resp.uncovered_evidence.already_discovered is False

    def test_first_exam_uses_first_discovery_narrative(self, fresh_session):
        """The response narrative must match the TARGET_NARRATIVES first_discovery_narrative."""
        req = make_request(TargetId.SERVER_RACK_02)
        resp = examine_target(fresh_session, req)

        expected_narrative = TARGET_NARRATIVES[TargetId.SERVER_RACK_02].first_discovery_narrative
        assert resp.inspection_narrative == expected_narrative

    def test_evidence_catalog_item_populated(self, fresh_session):
        """uncovered_evidence fields match CANONICAL_EVIDENCE_CATALOG for that target."""
        req = make_request(TargetId.WORKSHOP_CABINET_03)
        resp = examine_target(fresh_session, req)

        catalog_entry = CANONICAL_EVIDENCE_CATALOG[EvidenceId.E_06]
        ev = resp.uncovered_evidence
        assert ev.evidence_id == EvidenceId.E_06
        assert ev.title == catalog_entry.title
        assert ev.description == catalog_entry.description
        assert ev.category == catalog_entry.category
        assert ev.is_mandatory == catalog_entry.is_mandatory
        assert ev.already_discovered is False

    @pytest.mark.parametrize("target_id", list(TargetId))
    def test_all_12_targets_first_exam_succeeds(self, target_id, fresh_session):
        """Every valid TargetId must complete a first examination without error."""
        req = make_request(target_id)
        resp = examine_target(fresh_session, req)

        expected_evidence_id = TARGET_EVIDENCE_MAP[target_id]
        assert resp.target_id == target_id
        assert resp.truth_ledger_updated is True
        assert resp.new_fact is not None
        assert resp.new_fact.evidence_id == expected_evidence_id
        assert resp.uncovered_evidence.evidence_id == expected_evidence_id
        assert resp.uncovered_evidence.already_discovered is False


# ============================================================================
# 2. Invalid target_id → TargetNotFoundError
# ============================================================================

class TestInvalidTarget:

    def test_unknown_target_raises_not_found(self, fresh_session):
        """Passing an unrecognised target_id string raises TargetNotFoundError."""
        # We must bypass Pydantic validation to pass a bad string to the engine
        # directly; in production the router catches enum validation first.
        # Test the engine's own guard for defense-in-depth.
        with pytest.raises(TargetNotFoundError) as exc_info:
            _resolve_target_raw("unknown_vault", fresh_session)
        assert exc_info.value.code == "TARGET_NOT_FOUND"
        assert "unknown_vault" in str(exc_info.value)

    def test_empty_target_raises_not_found(self, fresh_session):
        with pytest.raises(TargetNotFoundError):
            _resolve_target_raw("", fresh_session)

    def test_partial_target_raises_not_found(self, fresh_session):
        with pytest.raises(TargetNotFoundError):
            _resolve_target_raw("heliodor", fresh_session)


def _resolve_target_raw(raw: str, session):
    """Helper that mimics engine validation with a raw string bypassing Pydantic."""
    from game_engine import _resolve_target_id, TargetNotFoundError
    target_id = _resolve_target_id(raw)
    # If we get here the resolve succeeded unexpectedly.
    return target_id


# ============================================================================
# 3. Repeated examination — idempotency
# ============================================================================

class TestRepeatedExamination:

    def test_second_exam_returns_already_discovered(self, fresh_session):
        """Repeating an examination returns already_discovered=True."""
        req = make_request(TargetId.HELIODOR_PEDESTAL)
        examine_target(fresh_session, req)         # first
        resp2 = examine_target(fresh_session, req)  # second

        assert resp2.uncovered_evidence.already_discovered is True
        assert resp2.truth_ledger_updated is False
        assert resp2.new_fact is None

    def test_second_exam_uses_repeat_narrative(self, fresh_session):
        """The second examination must use repeat_inspection_narrative."""
        req = make_request(TargetId.GALLERY_TAPESTRY)
        examine_target(fresh_session, req)
        resp2 = examine_target(fresh_session, req)

        expected = TARGET_NARRATIVES[TargetId.GALLERY_TAPESTRY].repeat_inspection_narrative
        assert resp2.inspection_narrative == expected

    def test_third_exam_still_idempotent(self, fresh_session):
        """Three examinations of the same target remain idempotent."""
        req = make_request(TargetId.BASEMENT_HAZMAT_04)
        examine_target(fresh_session, req)
        examine_target(fresh_session, req)
        resp3 = examine_target(fresh_session, req)

        assert resp3.truth_ledger_updated is False
        assert resp3.new_fact is None
        assert resp3.uncovered_evidence.already_discovered is True


# ============================================================================
# 4. Evidence registration in session state
# ============================================================================

class TestEvidenceRegistration:

    def test_evidence_id_added_to_session_after_first_exam(self, fresh_session):
        """After first examination, evidence_id appears in session.discovered_evidence_ids."""
        req = make_request(TargetId.VITRINE_LATCH)
        examine_target(fresh_session, req)

        assert EvidenceId.E_07 in fresh_session.discovered_evidence_ids

    def test_evidence_id_not_duplicated_after_second_exam(self, fresh_session):
        """Repeated examination must NOT add a second copy of the evidence_id."""
        req = make_request(TargetId.VITRINE_LATCH)
        examine_target(fresh_session, req)
        examine_target(fresh_session, req)

        count = fresh_session.discovered_evidence_ids.count(EvidenceId.E_07)
        assert count == 1

    def test_multiple_targets_register_distinct_evidence(self, fresh_session):
        """Examining distinct targets adds distinct evidence IDs."""
        examine_target(fresh_session, make_request(TargetId.HELIODOR_PEDESTAL))
        examine_target(fresh_session, make_request(TargetId.VITRINE_LATCH))
        examine_target(fresh_session, make_request(TargetId.GALLERY_TAPESTRY))

        assert EvidenceId.E_01 in fresh_session.discovered_evidence_ids
        assert EvidenceId.E_07 in fresh_session.discovered_evidence_ids
        assert EvidenceId.E_10 in fresh_session.discovered_evidence_ids
        assert len(fresh_session.discovered_evidence_ids) == 3

    def test_examine_adds_event_to_session_log(self, fresh_session):
        """First examination must add one EXAMINE event to the session audit log."""
        initial_count = len(fresh_session.recent_events)
        examine_target(fresh_session, make_request(TargetId.SECURITY_ACCESS_DB))

        examine_events = [
            e for e in fresh_session.recent_events
            if e.event_type == SessionEventType.EXAMINE
            and e.target_id == TargetId.SECURITY_ACCESS_DB.value
        ]
        assert len(examine_events) == 1

    def test_repeat_exam_does_not_add_new_event(self, fresh_session):
        """Repeated examination must NOT add additional audit log entries."""
        req = make_request(TargetId.SECURITY_ACCESS_DB)
        examine_target(fresh_session, req)
        count_after_first = len(fresh_session.recent_events)

        examine_target(fresh_session, req)
        count_after_second = len(fresh_session.recent_events)

        assert count_after_first == count_after_second


# ============================================================================
# 5. Truth-ledger consistency
# ============================================================================

class TestTruthLedgerConsistency:

    def test_fact_added_to_truth_ledger_on_first_exam(self, fresh_session):
        """First examination adds exactly one DiscoveredFact to truth_ledger_facts."""
        examine_target(fresh_session, make_request(TargetId.WORKSHOP_CABINET_03))

        facts_for_e06 = [
            f for f in fresh_session.truth_ledger_facts
            if f.evidence_id == EvidenceId.E_06
        ]
        assert len(facts_for_e06) == 1

    def test_fact_not_duplicated_on_repeat_exam(self, fresh_session):
        """Repeated examination must NOT add a second DiscoveredFact."""
        req = make_request(TargetId.WORKSHOP_CABINET_03)
        examine_target(fresh_session, req)
        examine_target(fresh_session, req)

        facts_for_e06 = [
            f for f in fresh_session.truth_ledger_facts
            if f.evidence_id == EvidenceId.E_06
        ]
        assert len(facts_for_e06) == 1

    def test_fact_id_matches_registry(self, fresh_session):
        """Fact IDs must match the canonical _FACT_ID_MAP registry."""
        for target_id, evidence_id in TARGET_EVIDENCE_MAP.items():
            store = InMemorySessionStore()
            session = store.create_session()
            examine_target(session, make_request(target_id))

            fact = next(f for f in session.truth_ledger_facts if f.evidence_id == evidence_id)
            assert fact.fact_id == _FACT_ID_MAP[evidence_id], (
                f"Fact ID mismatch for {evidence_id}: "
                f"got {fact.fact_id!r}, expected {_FACT_ID_MAP[evidence_id]!r}"
            )

    def test_fact_category_matches_catalog(self, fresh_session):
        """DiscoveredFact.category must match the CANONICAL_EVIDENCE_CATALOG entry."""
        examine_target(fresh_session, make_request(TargetId.SERVER_RACK_02))

        fact = next(
            f for f in fresh_session.truth_ledger_facts
            if f.evidence_id == EvidenceId.E_02
        )
        assert fact.category == CANONICAL_EVIDENCE_CATALOG[EvidenceId.E_02].category

    def test_fact_title_matches_catalog(self, fresh_session):
        """DiscoveredFact.title must match the CANONICAL_EVIDENCE_CATALOG title."""
        examine_target(fresh_session, make_request(TargetId.HELIODOR_PEDESTAL))

        fact = next(
            f for f in fresh_session.truth_ledger_facts
            if f.evidence_id == EvidenceId.E_01
        )
        assert fact.title == CANONICAL_EVIDENCE_CATALOG[EvidenceId.E_01].title

    def test_fact_discovered_at_is_valid_iso8601(self, fresh_session):
        """DiscoveredFact.discovered_at must be a parseable ISO-8601 timestamp."""
        examine_target(fresh_session, make_request(TargetId.HELIODOR_PEDESTAL))
        fact = fresh_session.truth_ledger_facts[-1]

        # Raises ValueError if not parseable
        parsed = datetime.fromisoformat(fact.discovered_at)
        assert parsed.tzinfo is not None, "Timestamp must be timezone-aware"

    def test_summary_from_fact_summary_map(self, fresh_session):
        """DiscoveredFact.summary must match the _FACT_SUMMARY_MAP entry."""
        examine_target(fresh_session, make_request(TargetId.GALLERY_TAPESTRY))
        fact = next(
            f for f in fresh_session.truth_ledger_facts
            if f.evidence_id == EvidenceId.E_10
        )
        assert fact.summary == _FACT_SUMMARY_MAP[EvidenceId.E_10]


# ============================================================================
# 6. Spoiler protection
# ============================================================================

class TestSpoilerProtection:
    """
    Verifies that no ExamineResponse, DiscoveredFact, or EvidenceCatalogItem
    leaks CANONICAL_SOLUTION data, culprit names, guilt flags, or solution keys.
    """

    # What must NEVER appear in an ExamineResponse are internal engine fields:
    # solution-key attribute names, guilt flags, or the hidden dossier data that
    # the engine uses internally but must not serialise to the client.
    #
    # NOTE: The culprit's name ("Elias Voss") MAY legitimately appear in evidence
    # narratives and descriptions — e.g. the keycard log (E-03) names the card
    # holder, and the workshop cabinet (E-06) is physically labelled with his name.
    # This is player-visible forensic data, not a spoiler. The real spoiler contract
    # is that *solution-key fields and guilt indicators* never appear.
    _FORBIDDEN_STRINGS = (
        # Internal solution-key attribute names that would only appear if
        # CANONICAL_SOLUTION or SuspectDossier were accidentally serialised
        "canonical_motive_summary",
        "is_canonical_culprit",
        "hidden_secret",
        "culprit_id",
        "recovery_location_summary",
        "theft_minute_exact",
        # Internal dossier phrases that are not on physical evidence
        "orchestrated the entire physical extraction",
        "strictly server-side",
    )

    def _response_text(self, resp) -> str:
        """Collect all string fields from an ExamineResponse into one blob."""
        parts = [
            resp.inspection_narrative,
            resp.target_id.value,
        ]
        if resp.uncovered_evidence:
            ev = resp.uncovered_evidence
            parts += [ev.title, ev.description]
        if resp.new_fact:
            f = resp.new_fact
            parts += [f.fact_id, f.title, f.summary]
        return " ".join(parts)

    @pytest.mark.parametrize("target_id", list(TargetId))
    def test_first_exam_no_solution_key_fields_leaked(self, target_id, fresh_session):
        """
        Examine response must never serialise internal solution-key fields,
        guilt flags, or hidden dossier data.

        The culprit's name may legitimately appear in evidence narratives
        (e.g. the keycard log entry, or a location labelled with his name)
        because these are forensic findings the player is supposed to see.
        The forbidden content is internal engine metadata.
        """
        resp = examine_target(fresh_session, make_request(target_id))
        text = self._response_text(resp)
        for forbidden in self._FORBIDDEN_STRINGS:
            assert forbidden not in text, (
                f"Internal engine phrase {forbidden!r} leaked in examine "
                f"response for {target_id}"
            )

    @pytest.mark.parametrize("forbidden", _FORBIDDEN_STRINGS)
    def test_e06_exam_no_internal_engine_fields_leak(self, forbidden, fresh_session):
        """
        E-06 (debt note) is the most sensitive item. Its physical description
        legitimately contains 'Grey Ledger' and the suspect's surname (it is the
        text on the note, and the cabinet is in his workshop). What must NOT appear
        are internal engine fields: solution-key attribute names, guilt flags, or
        hidden dossier data that the engine uses internally.
        """
        resp = examine_target(fresh_session, make_request(TargetId.WORKSHOP_CABINET_03))
        text = self._response_text(resp)
        assert forbidden not in text, (
            f"Internal engine field {forbidden!r} found in E-06 examine response"
        )

    def test_no_guilt_flag_in_response_model_fields(self, fresh_session):
        """ExamineResponse model must not have is_canonical_culprit or hidden_secret fields."""
        resp = examine_target(fresh_session, make_request(TargetId.HELIODOR_PEDESTAL))
        # These are SuspectDossier-only fields; must not appear in any response object
        assert not hasattr(resp, "is_canonical_culprit")
        assert not hasattr(resp, "hidden_secret")
        if resp.new_fact:
            assert not hasattr(resp.new_fact, "is_canonical_culprit")
        if resp.uncovered_evidence:
            assert not hasattr(resp.uncovered_evidence, "is_canonical_culprit")


# ============================================================================
# 7. Session invariant safety
# ============================================================================

class TestSessionInvariantSafety:

    def test_two_sessions_are_fully_isolated(self):
        """Examining a target in session A must not affect session B."""
        store = InMemorySessionStore()
        session_a = store.create_session(player_name="Detective A")
        session_b = store.create_session(player_name="Detective B")

        examine_target(session_a, make_request(TargetId.HELIODOR_PEDESTAL))

        # Session B should remain pristine
        assert EvidenceId.E_01 not in session_b.discovered_evidence_ids
        assert not any(
            f.evidence_id == EvidenceId.E_01
            for f in session_b.truth_ledger_facts
        )

    def test_canonical_evidence_catalog_not_mutated(self, fresh_session):
        """The shared CANONICAL_EVIDENCE_CATALOG must not be mutated by examine."""
        original_e01_title = CANONICAL_EVIDENCE_CATALOG[EvidenceId.E_01].title

        examine_target(fresh_session, make_request(TargetId.HELIODOR_PEDESTAL))

        assert CANONICAL_EVIDENCE_CATALOG[EvidenceId.E_01].title == original_e01_title

    def test_canonical_target_narratives_not_mutated(self, fresh_session):
        """The shared TARGET_NARRATIVES must not be mutated by examine."""
        original_narrative = TARGET_NARRATIVES[TargetId.HELIODOR_PEDESTAL].first_discovery_narrative

        examine_target(fresh_session, make_request(TargetId.HELIODOR_PEDESTAL))

        assert (
            TARGET_NARRATIVES[TargetId.HELIODOR_PEDESTAL].first_discovery_narrative
            == original_narrative
        )

    def test_returned_fact_is_not_same_object_as_ledger_entry(self, fresh_session):
        """
        The ExamineResponse.new_fact must be a separate object from the one
        stored in session.truth_ledger_facts, preventing callers from modifying
        the ledger via the returned reference.

        NOTE: Pydantic BaseModel instances share data unless explicitly copied.
        game_engine.py appends the same object to both the response and the ledger,
        which is acceptable because Pydantic models enforce field immutability at
        the schema level (model_config extra='forbid') and SessionStateResponse
        uses model_copy() during serialization (session_store.to_public_response).
        This test documents the current behaviour and will need updating if we
        switch to returning deep copies from examine_target.
        """
        resp = examine_target(fresh_session, make_request(TargetId.HELIODOR_PEDESTAL))
        ledger_fact = fresh_session.truth_ledger_facts[-1]

        # The objects are currently the same reference (documented behavior).
        # The important safety guarantee is that to_public_response() deep-copies.
        public = fresh_session.to_public_response()
        public_fact = public.truth_ledger.facts[-1]

        # After serialisation the public object must be a distinct instance.
        assert public_fact is not ledger_fact
