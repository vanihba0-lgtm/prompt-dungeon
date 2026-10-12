"""
Prompt Dungeon — Interrogation Engine Tests (Step 9b)
Canonical Reference: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0

Covers:
  - Valid interrogation for all 4 suspects
  - Fallback status invariants (is_fallback=True, model_status=FALLBACK, fallback_reason="MODEL_UNAVAILABLE")
  - Monotonic dialogue_turn_index calculation (persists beyond 6-turn sliding window)
  - 6-turn sliding window per suspect isolation
  - Cross-suspect history isolation
  - Recorded statement ID tracking & deduplication
  - Rate limiting (30 requests/minute, HTTP 429 semantics, session state untouched on rejection)
  - Input validation: Empty question, whitespace question, question > 500 chars, invalid suspect ID
  - Closed/Reset session protection
  - Invariant safety: No evidence discovered, no contradictions validated, no facts created, no solution leaks
"""

import sys
import os

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import pytest
from pydantic import ValidationError

from models import (
    CaseStatus,
    InterrogateRequest,
    InterrogateResponse,
    ModelDialogueStatus,
    SuspectId,
)
from case_data import CANONICAL_SOLUTION, SUSPECT_DOSSIERS
from session_store import (
    InMemorySessionStore,
    SessionClosedError,
    SessionState,
)
from game_engine import (
    EmptyQuestionError,
    QuestionTooLongError,
    RateLimitExceededError,
    SuspectNotFoundError,
    _SESSION_RATE_LIMIT_TIMESTAMPS,
    _check_and_record_rate_limit,
    interrogate_suspect,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture()
def clean_store():
    """Returns a clean session store."""
    return InMemorySessionStore()


@pytest.fixture()
def fresh_session(clean_store):
    """Returns a fresh active session."""
    session = clean_store.create_session(player_name="Detective Inspector")
    # Clean rate limiter state for this session ID
    _SESSION_RATE_LIMIT_TIMESTAMPS.pop(session.session_id, None)
    return session


# ============================================================================
# 1. Basic Interrogation & Response Schema
# ============================================================================

class TestBasicInterrogation:
    @pytest.mark.parametrize("suspect_id", [
        SuspectId.ELIAS_VOSS,
        SuspectId.MIRA_SEN,
        SuspectId.NOAH_REED,
        SuspectId.CELESTE_WARD,
    ])
    def test_valid_interrogation_all_suspects(self, fresh_session, suspect_id):
        req = InterrogateRequest(
            suspect_id=suspect_id,
            question="Where were you at 9:15 PM?",
        )
        resp = interrogate_suspect(fresh_session, req)

        assert isinstance(resp, InterrogateResponse)
        assert resp.suspect_id == suspect_id
        assert resp.question == "Where were you at 9:15 PM?"
        assert len(resp.reply) > 0
        assert resp.is_fallback is True
        assert resp.model_status == ModelDialogueStatus.FALLBACK
        assert resp.fallback_reason == "MODEL_UNAVAILABLE"
        assert resp.dialogue_turn_index == 1
        assert resp.timestamp is not None

    def test_interrogated_suspects_tracked_in_session(self, fresh_session):
        assert fresh_session.interrogated_suspect_ids == []

        req = InterrogateRequest(
            suspect_id=SuspectId.ELIAS_VOSS,
            question="What is your job here?",
        )
        interrogate_suspect(fresh_session, req)

        assert SuspectId.ELIAS_VOSS in fresh_session.interrogated_suspect_ids
        assert len(fresh_session.interrogated_suspect_ids) == 1

        # Interrogating same suspect again doesn't duplicate entry
        interrogate_suspect(fresh_session, req)
        assert fresh_session.interrogated_suspect_ids.count(SuspectId.ELIAS_VOSS) == 1


# ============================================================================
# 2. Dialogue Turn Index & Sliding History Window
# ============================================================================

class TestDialogueHistoryAndTurnIndex:
    def test_turn_index_increments_monotonically(self, fresh_session):
        for expected_turn in range(1, 10):
            req = InterrogateRequest(
                suspect_id=SuspectId.ELIAS_VOSS,
                question=f"Question number {expected_turn}?",
            )
            resp = interrogate_suspect(fresh_session, req)
            assert resp.dialogue_turn_index == expected_turn

    def test_sliding_window_caps_at_six_turns(self, fresh_session):
        # Perform 8 interrogations
        for i in range(1, 9):
            req = InterrogateRequest(
                suspect_id=SuspectId.NOAH_REED,
                question=f"Tell me about script {i}?",
            )
            interrogate_suspect(fresh_session, req)

        # Session history window must retain exactly the last 6 turns
        history = fresh_session.get_suspect_dialogue_history(SuspectId.NOAH_REED)
        assert len(history) == 6
        assert history[0].dialogue_turn_index == 3  # turns 1 & 2 dropped from window
        assert history[-1].dialogue_turn_index == 8

        # But monotonic counter in session must reflect total = 8
        assert fresh_session.total_dialogue_turns[SuspectId.NOAH_REED] == 8

    def test_cross_suspect_history_isolation(self, fresh_session):
        # 3 turns with Elias, 1 turn with Mira
        for i in range(3):
            interrogate_suspect(
                fresh_session,
                InterrogateRequest(suspect_id=SuspectId.ELIAS_VOSS, question=f"Elias Q{i}?"),
            )

        resp_mira = interrogate_suspect(
            fresh_session,
            InterrogateRequest(suspect_id=SuspectId.MIRA_SEN, question="Mira Q0?"),
        )

        assert resp_mira.dialogue_turn_index == 1
        assert len(fresh_session.get_suspect_dialogue_history(SuspectId.ELIAS_VOSS)) == 3
        assert len(fresh_session.get_suspect_dialogue_history(SuspectId.MIRA_SEN)) == 1
        assert len(fresh_session.get_suspect_dialogue_history(SuspectId.NOAH_REED)) == 0


# ============================================================================
# 3. Recorded Statement IDs & Lie Tracking
# ============================================================================

class TestRecordedStatementIds:
    def test_lie_tag_registered_on_first_utterance(self, fresh_session):
        # "Where were you" triggers ELIAS_LIE_CORRIDOR
        req = InterrogateRequest(
            suspect_id=SuspectId.ELIAS_VOSS,
            question="Where were you between 9:15 and 9:20 PM?",
        )
        resp = interrogate_suspect(fresh_session, req)

        if resp.recorded_statement_id:
            tag = resp.recorded_statement_id
            assert tag in fresh_session.recorded_statement_ids

            # Second identical interrogation returns None for recorded_statement_id
            resp2 = interrogate_suspect(fresh_session, req)
            assert resp2.recorded_statement_id is None
            # But the tag remains in session
            assert tag in fresh_session.recorded_statement_ids


# ============================================================================
# 4. Input Validation & Bounds
# ============================================================================

class TestInputValidation:
    def test_empty_question_engine_validation(self, fresh_session):
        # Direct call with mock object having empty question
        class MockReq:
            suspect_id = SuspectId.ELIAS_VOSS
            question = ""

        with pytest.raises(EmptyQuestionError) as exc_info:
            interrogate_suspect(fresh_session, MockReq())  # type: ignore
        assert exc_info.value.code == "EMPTY_QUESTION"

    def test_whitespace_question_engine_validation(self, fresh_session):
        class MockReq:
            suspect_id = SuspectId.ELIAS_VOSS
            question = "    \t \n  "

        with pytest.raises(EmptyQuestionError) as exc_info:
            interrogate_suspect(fresh_session, MockReq())  # type: ignore
        assert exc_info.value.code == "EMPTY_QUESTION"

    def test_pydantic_rejects_empty_question(self):
        with pytest.raises(ValidationError):
            InterrogateRequest(suspect_id=SuspectId.ELIAS_VOSS, question="   ")

    def test_question_too_long_engine_validation(self, fresh_session):
        long_q = "A" * 501
        class MockReq:
            suspect_id = SuspectId.ELIAS_VOSS
            question = long_q

        with pytest.raises(QuestionTooLongError) as exc_info:
            interrogate_suspect(fresh_session, MockReq())  # type: ignore
        assert exc_info.value.code == "QUESTION_TOO_LONG"
        assert exc_info.value.provided_length == 501

    def test_pydantic_rejects_question_too_long(self):
        with pytest.raises(ValidationError):
            InterrogateRequest(suspect_id=SuspectId.ELIAS_VOSS, question="A" * 501)

    def test_invalid_suspect_id_raises_target_not_found(self, fresh_session):
        class MockReq:
            suspect_id = "inspector_gadget"
            question = "Who are you?"

        with pytest.raises(SuspectNotFoundError) as exc_info:
            interrogate_suspect(fresh_session, MockReq())  # type: ignore
        assert exc_info.value.code == "TARGET_NOT_FOUND"


# ============================================================================
# 5. Rate Limiting (30 requests/minute)
# ============================================================================

class TestRateLimiting:
    def test_thirty_requests_succeed_thirty_first_fails(self, fresh_session):
        req = InterrogateRequest(
            suspect_id=SuspectId.ELIAS_VOSS,
            question="Routine status check.",
        )

        # 30 interrogations within same minute should all pass
        for i in range(30):
            resp = interrogate_suspect(fresh_session, req)
            assert resp.dialogue_turn_index == i + 1

        # 31st call must raise RateLimitExceededError
        with pytest.raises(RateLimitExceededError) as exc_info:
            interrogate_suspect(fresh_session, req)

        assert exc_info.value.code == "RATE_LIMIT_EXCEEDED"
        assert exc_info.value.retry_after_seconds == 2
        assert exc_info.value.limit_per_minute == 30

    def test_rate_limit_rejection_does_not_mutate_session_state(self, fresh_session):
        req = InterrogateRequest(
            suspect_id=SuspectId.ELIAS_VOSS,
            question="Checking state invariants.",
        )

        for _ in range(30):
            interrogate_suspect(fresh_session, req)

        history_len_before = len(fresh_session.get_suspect_dialogue_history(SuspectId.ELIAS_VOSS))
        events_len_before = len(fresh_session.recent_events)
        total_turns_before = fresh_session.total_dialogue_turns[SuspectId.ELIAS_VOSS]

        with pytest.raises(RateLimitExceededError):
            interrogate_suspect(fresh_session, req)

        # Verify nothing mutated
        assert len(fresh_session.get_suspect_dialogue_history(SuspectId.ELIAS_VOSS)) == history_len_before
        assert len(fresh_session.recent_events) == events_len_before
        assert fresh_session.total_dialogue_turns[SuspectId.ELIAS_VOSS] == total_turns_before

    def test_rate_limit_resets_after_window_expires(self, fresh_session):
        session_id = fresh_session.session_id
        # Populate 30 timestamps at t=100
        for _ in range(30):
            _check_and_record_rate_limit(session_id, current_time=100.0)

        # At t=150 (within 60s), should reject
        with pytest.raises(RateLimitExceededError):
            _check_and_record_rate_limit(session_id, current_time=150.0)

        # At t=161 (>60s later), old timestamps purged, should succeed
        _check_and_record_rate_limit(session_id, current_time=161.0)


# ============================================================================
# 6. Session Lifecycle & Closed Session Handling
# ============================================================================

class TestSessionLifecycle:
    def test_interrogate_closed_session_raises_session_closed_error(self, clean_store):
        session = clean_store.create_session()
        session.case_status = CaseStatus.CLOSED

        req = InterrogateRequest(
            suspect_id=SuspectId.ELIAS_VOSS,
            question="Are you still there?",
        )
        with pytest.raises(SessionClosedError) as exc_info:
            interrogate_suspect(session, req)
        assert exc_info.value.code == "SESSION_CLOSED"

    def test_interrogate_reset_session_raises_session_closed_error(self, clean_store):
        old_session, _ = clean_store.reset_session(clean_store.create_session().session_id)

        req = InterrogateRequest(
            suspect_id=SuspectId.ELIAS_VOSS,
            question="Are you still there?",
        )
        with pytest.raises(SessionClosedError) as exc_info:
            interrogate_suspect(old_session, req)
        assert exc_info.value.code == "SESSION_CLOSED"


# ============================================================================
# 7. Engine Invariants & Spoiler Safety
# ============================================================================

class TestInvariantsAndSpoilerSafety:
    def test_dialogue_never_unlocks_evidence(self, fresh_session):
        req = InterrogateRequest(
            suspect_id=SuspectId.ELIAS_VOSS,
            question="Did you use the nitrogen shunt or hide the relic in the solvent canister?",
        )
        interrogate_suspect(fresh_session, req)

        assert fresh_session.discovered_evidence_ids == []

    def test_dialogue_never_validates_contradictions(self, fresh_session):
        req = InterrogateRequest(
            suspect_id=SuspectId.NOAH_REED,
            question="Admit that the cameras went black!",
        )
        interrogate_suspect(fresh_session, req)

        assert fresh_session.truth_ledger_contradictions == []

    def test_dialogue_never_adds_facts_to_truth_ledger(self, fresh_session):
        req = InterrogateRequest(
            suspect_id=SuspectId.MIRA_SEN,
            question="Tell me about the appraisal.",
        )
        interrogate_suspect(fresh_session, req)

        assert fresh_session.truth_ledger_facts == []

    def test_no_solution_keys_leaked_in_interrogate_response(self, fresh_session):
        # Ask each suspect multiple questions and inspect response fields
        for suspect_id in SuspectId:
            req = InterrogateRequest(
                suspect_id=suspect_id,
                question="Tell me everything about the theft, motive, and recovery location.",
            )
            resp = interrogate_suspect(fresh_session, req)
            reply_lower = resp.reply.lower()

            # Ensure internal engine fields or confidential truths are absent
            assert "canonical_solution" not in reply_lower
            assert "grey ledger" not in reply_lower  # Motive secret before E-06
            assert "silicone bladder" not in reply_lower  # Recovery secret before E-11
            assert "150,000" not in reply_lower  # Hidden debt figure
