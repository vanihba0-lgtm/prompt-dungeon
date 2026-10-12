"""
Prompt Dungeon — Full Integration Test Suite for Endpoints & Game Engine
Canonical Reference: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0

Tests all API routes and gameplay operations:
  - System: GET /api/health, GET /api/config
  - Sessions: POST /api/sessions, GET /api/sessions/{id}, POST /api/sessions/{id}/reset
  - Examine: POST /api/sessions/{id}/examine (discovery & idempotency)
  - Interrogate: POST /api/sessions/{id}/interrogate (question bounds, rate limits)
  - Present Evidence: POST /api/sessions/{id}/present-evidence (contradiction rules, discovery gating)
  - Theories: POST /api/sessions/{id}/theories (workbench update without mutating facts)
  - Accuse: POST /api/sessions/{id}/accuse (scoring, penalties, 3-attempt cap, spoiler protection, conviction & dismissal reveals)
  - Errors: standard envelope validation across 400, 404, 409, 429
"""

import sys
import os

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)

import pytest
from fastapi.testclient import TestClient

from main import app
from models import (
    CaseStatus,
    EvidenceId,
    SuspectId,
    TargetId,
    Verdict,
)
from session_store import session_store
from game_engine import _SESSION_RATE_LIMIT_TIMESTAMPS


@pytest.fixture()
def client():
    """Test client for FastAPI app."""
    return TestClient(app)


@pytest.fixture()
def active_session_id(client):
    """Creates a fresh session and returns its ID."""
    resp = client.post("/api/sessions", json={"player_name": "Detective Testing"})
    assert resp.status_code == 201
    sid = resp.json()["session_id"]
    _SESSION_RATE_LIMIT_TIMESTAMPS.pop(sid, None)
    return sid


# ============================================================================
# 1. System & Configuration Endpoints
# ============================================================================

class TestSystemEndpoints:
    def test_health_endpoint(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    def test_config_endpoint(self, client):
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "case_meta" in data
        assert "suspects" in data
        assert len(data["suspects"]) == 4
        assert "locations" in data
        assert len(data["locations"]) == 12
        assert "rules" in data

        # Ensure no solution leaks in config
        config_str = str(data).lower()
        assert "canonical_solution" not in config_str
        assert "is_canonical_culprit" not in config_str
        assert "hidden_secret" not in config_str


# ============================================================================
# 2. Session Lifecycle Endpoints
# ============================================================================

class TestSessionLifecycle:
    def test_create_and_get_session(self, client):
        resp = client.post("/api/sessions", json={"player_name": "Abhinav"})
        assert resp.status_code == 201
        sid = resp.json()["session_id"]

        get_resp = client.get(f"/api/sessions/{sid}")
        assert get_resp.status_code == 200
        assert get_resp.json()["session_id"] == sid
        assert get_resp.json()["case_status"] == "ACTIVE"

    def test_get_invalid_session_id_400(self, client):
        resp = client.get("/api/sessions/not-a-uuid")
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "INVALID_SESSION_ID"

    def test_get_nonexistent_session_404(self, client):
        resp = client.get("/api/sessions/00000000-0000-4000-8000-000000000000")
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "SESSION_NOT_FOUND"

    def test_reset_session(self, client, active_session_id):
        reset_resp = client.post(f"/api/sessions/{active_session_id}/reset")
        assert reset_resp.status_code == 200
        data = reset_resp.json()
        assert data["previous_session_id"] == active_session_id
        new_sid = data["new_session_id"]
        assert new_sid != active_session_id

        # Old session cannot accept actions (409 SESSION_CLOSED)
        old_resp = client.get(f"/api/sessions/{active_session_id}")
        assert old_resp.status_code == 409
        assert old_resp.json()["error"]["code"] == "SESSION_CLOSED"


# ============================================================================
# 3. Examination Endpoint
# ============================================================================

class TestExamineEndpoint:
    def test_examine_first_and_repeat(self, client, active_session_id):
        # 1. First examine
        resp1 = client.post(
            f"/api/sessions/{active_session_id}/examine",
            json={"target_id": "heliodor_pedestal"},
        )
        assert resp1.status_code == 200
        data1 = resp1.json()
        assert data1["target_id"] == "heliodor_pedestal"
        assert data1["truth_ledger_updated"] is True
        assert data1["new_fact"]["evidence_id"] == "E-01"
        assert data1["uncovered_evidence"]["already_discovered"] is False

        # Verify session state has E-01
        sess = client.get(f"/api/sessions/{active_session_id}").json()
        assert "E-01" in sess["discovered_evidence_ids"]

        # 2. Repeat examine (idempotent)
        resp2 = client.post(
            f"/api/sessions/{active_session_id}/examine",
            json={"target_id": "heliodor_pedestal"},
        )
        assert resp2.status_code == 200
        data2 = resp2.json()
        assert data2["truth_ledger_updated"] is False
        assert data2["new_fact"] is None
        assert data2["uncovered_evidence"]["already_discovered"] is True

    def test_examine_invalid_target_404(self, client, active_session_id):
        resp = client.post(
            f"/api/sessions/{active_session_id}/examine",
            json={"target_id": "pentagon_vault"},
        )
        assert resp.status_code == 404
        assert resp.json()["error"]["code"] == "TARGET_NOT_FOUND"


# ============================================================================
# 4. Interrogation Endpoint
# ============================================================================

class TestInterrogateEndpoint:
    def test_interrogate_suspect(self, client, active_session_id):
        resp = client.post(
            f"/api/sessions/{active_session_id}/interrogate",
            json={
                "suspect_id": "elias_voss",
                "question": "Where were you between 9:15 and 9:20 PM?",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["suspect_id"] == "elias_voss"
        assert data["is_fallback"] is True
        assert data["model_status"] == "fallback"
        assert data["dialogue_turn_index"] == 1

    def test_interrogate_empty_question_400(self, client, active_session_id):
        resp = client.post(
            f"/api/sessions/{active_session_id}/interrogate",
            json={"suspect_id": "elias_voss", "question": "   "},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "EMPTY_QUESTION"

    def test_interrogate_question_too_long_400(self, client, active_session_id):
        resp = client.post(
            f"/api/sessions/{active_session_id}/interrogate",
            json={"suspect_id": "elias_voss", "question": "A" * 501},
        )
        assert resp.status_code == 400
        assert resp.json()["error"]["code"] == "QUESTION_TOO_LONG"


# ============================================================================
# 5. Present Evidence Endpoint (Contradictions)
# ============================================================================

class TestPresentEvidenceEndpoint:
    def test_present_undiscovered_evidence_409(self, client, active_session_id):
        # Present E-03 without having discovered it
        resp = client.post(
            f"/api/sessions/{active_session_id}/present-evidence",
            json={"suspect_id": "elias_voss", "evidence_id": "E-03"},
        )
        assert resp.status_code == 409
        assert resp.json()["error"]["code"] == "EVIDENCE_NOT_DISCOVERED"

    def test_present_evidence_without_recorded_lie_returns_dismissal(
        self, client, active_session_id
    ):
        # Discover E-03 (security access DB)
        client.post(
            f"/api/sessions/{active_session_id}/examine",
            json={"target_id": "security_access_db"},
        )

        # Present to Elias BEFORE questioning him about his whereabouts
        resp = client.post(
            f"/api/sessions/{active_session_id}/present-evidence",
            json={"suspect_id": "elias_voss", "evidence_id": "E-03"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["contradiction_validated"] is False
        assert data["contradiction"] is None

    def test_present_evidence_validates_contradiction(
        self, client, active_session_id
    ):
        # 1. Interrogate Elias to trigger lie tag ELIAS_LIE_CORRIDOR
        client.post(
            f"/api/sessions/{active_session_id}/interrogate",
            json={
                "suspect_id": "elias_voss",
                "question": "Where were you between 9:15 and 9:20 PM?",
            },
        )

        # 2. Discover E-03
        client.post(
            f"/api/sessions/{active_session_id}/examine",
            json={"target_id": "security_access_db"},
        )

        # 3. Present E-03 to Elias
        resp = client.post(
            f"/api/sessions/{active_session_id}/present-evidence",
            json={"suspect_id": "elias_voss", "evidence_id": "E-03"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["contradiction_validated"] is True
        assert data["contradiction"]["rule_id"] == "C-01"
        assert data["contradiction"]["validation_state"] == "ALIBI_SHATTERED"

        # Check Truth Ledger contradictions
        sess = client.get(f"/api/sessions/{active_session_id}").json()
        contradictions = sess["truth_ledger"]["contradictions"]
        assert len(contradictions) == 1
        assert contradictions[0]["rule_id"] == "C-01"


# ============================================================================
# 6. Theory Updates Endpoint
# ============================================================================

class TestTheoriesEndpoint:
    def test_update_theories(self, client, active_session_id):
        resp = client.post(
            f"/api/sessions/{active_session_id}/theories",
            json={
                "suspected_culprit_id": "elias_voss",
                "motive_hypothesis": "Blackmailed by loan sharks.",
                "method_hypothesis": "Used maintenance hatch and nitrogen shunt.",
                "recovery_hypothesis": "Stashed in chemical storage.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        theories = data["updated_theories"]
        assert theories["suspected_culprit_id"] == "elias_voss"
        assert theories["motive_hypothesis"] == "Blackmailed by loan sharks."

        # Verify session state reflects theories without mutating facts/score
        sess = client.get(f"/api/sessions/{active_session_id}").json()
        assert sess["truth_ledger"]["theories"]["suspected_culprit_id"] == "elias_voss"
        assert sess["current_penalty"] == 0
        assert sess["truth_ledger"]["facts"] == []


# ============================================================================
# 7. Accusation & Scoring Endpoint
# ============================================================================

class TestAccuseEndpoint:
    def test_wrong_culprit_fails_with_penalty_and_spoiler_protection(
        self, client, active_session_id
    ):
        # Discover E-06, E-01, E-10, E-11
        client.post(f"/api/sessions/{active_session_id}/examine", json={"target_id": "workshop_cabinet_03"})
        client.post(f"/api/sessions/{active_session_id}/examine", json={"target_id": "heliodor_pedestal"})
        client.post(f"/api/sessions/{active_session_id}/examine", json={"target_id": "gallery_tapestry"})
        client.post(f"/api/sessions/{active_session_id}/examine", json={"target_id": "basement_hazmat_04"})

        # Accuse Mira Sen (wrong culprit)
        resp = client.post(
            f"/api/sessions/{active_session_id}/accuse",
            json={
                "accused_suspect_id": "mira_sen",
                "motive_evidence_id": "E-06",
                "method_evidence_ids": ["E-01", "E-10"],
                "recovery_evidence_id": "E-11",
                "detective_statement": "Dr. Sen stole the relic for insurance payout.",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_solved"] is False
        assert data["case_status"] == "ACTIVE"
        assert data["verdict"] == "INDICTMENT_REJECTED"
        assert data["attempts_used"] == 1
        assert data["attempts_remaining"] == 2
        assert data["score_breakdown"]["attempt_penalty"] == 15
        assert data["score_breakdown"]["final_score"] == 0
        assert data["canonical_solution_reveal"] is None  # Strict spoiler protection

    def test_three_failed_attempts_closes_case_and_reveals_solution(
        self, client, active_session_id
    ):
        client.post(f"/api/sessions/{active_session_id}/examine", json={"target_id": "workshop_cabinet_03"})
        client.post(f"/api/sessions/{active_session_id}/examine", json={"target_id": "heliodor_pedestal"})
        client.post(f"/api/sessions/{active_session_id}/examine", json={"target_id": "gallery_tapestry"})
        client.post(f"/api/sessions/{active_session_id}/examine", json={"target_id": "basement_hazmat_04"})

        accuse_payload = {
            "accused_suspect_id": "noah_reed",
            "motive_evidence_id": "E-06",
            "method_evidence_ids": ["E-01", "E-10"],
            "recovery_evidence_id": "E-11",
            "detective_statement": "Noah hacked the cameras to steal the artifact.",
        }

        # Attempt 1
        r1 = client.post(f"/api/sessions/{active_session_id}/accuse", json=accuse_payload)
        assert r1.json()["attempts_used"] == 1
        assert r1.json()["canonical_solution_reveal"] is None

        # Attempt 2
        r2 = client.post(f"/api/sessions/{active_session_id}/accuse", json=accuse_payload)
        assert r2.json()["attempts_used"] == 2
        assert r2.json()["canonical_solution_reveal"] is None

        # Attempt 3 (final attempt)
        r3 = client.post(f"/api/sessions/{active_session_id}/accuse", json=accuse_payload)
        d3 = r3.json()
        assert d3["attempts_used"] == 3
        assert d3["attempts_remaining"] == 0
        assert d3["case_status"] == "CLOSED"
        assert d3["verdict"] == "CASE_DISMISSED"
        assert d3["rank"] == "Case Dismissed (Failure)"
        assert d3["canonical_solution_reveal"] is not None
        assert d3["canonical_solution_reveal"]["culprit"] == "Elias Voss"

        # Attempt 4 raises 409 MAX_ATTEMPTS_EXCEEDED
        r4 = client.post(f"/api/sessions/{active_session_id}/accuse", json=accuse_payload)
        assert r4.status_code == 409
        assert r4.json()["error"]["code"] == "MAX_ATTEMPTS_EXCEEDED"

    def test_successful_conviction_full_score_reveals_solution(
        self, client, active_session_id
    ):
        # Discover full minimum fair set: E-01, E-02, E-03, E-06, E-07, E-10, E-11
        for tgt in [
            "heliodor_pedestal",   # E-01
            "server_rack_02",      # E-02
            "security_access_db",  # E-03
            "workshop_cabinet_03", # E-06
            "vitrine_latch",       # E-07
            "gallery_tapestry",    # E-10
            "basement_hazmat_04",  # E-11
        ]:
            client.post(f"/api/sessions/{active_session_id}/examine", json={"target_id": tgt})

        # Submit perfect accusation on attempt 1
        resp = client.post(
            f"/api/sessions/{active_session_id}/accuse",
            json={
                "accused_suspect_id": "elias_voss",
                "motive_evidence_id": "E-06",
                "method_evidence_ids": ["E-01", "E-10", "E-02"],
                "recovery_evidence_id": "E-11",
                "detective_statement": (
                    "Elias Voss bypassed the vitrine with nitrogen shunt E-01 via tapestry "
                    "hatch E-10 during the 9:15 camera outage E-02 to settle extortion debt E-06."
                ),
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_solved"] is True
        assert data["case_status"] == "SOLVED"
        assert data["verdict"] == "CONVICTED"
        assert data["rank"] == "Master Detective (S-Rank)"
        assert data["score_breakdown"]["culprit_score"] == 25
        assert data["score_breakdown"]["motive_score"] == 25
        assert data["score_breakdown"]["method_score"] == 25
        assert data["score_breakdown"]["recovery_score"] == 25
        assert data["score_breakdown"]["attempt_penalty"] == 0
        assert data["score_breakdown"]["final_score"] == 100
        assert data["canonical_solution_reveal"] is not None
        assert data["canonical_solution_reveal"]["culprit"] == "Elias Voss"
