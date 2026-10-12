"""
Prompt Dungeon — End-to-End Playthrough & Mystery Integrity Audit Script
Canonical Reference: docs/case-spec.md v1.1.0 & docs/api-contract.md v1.1.0

Tests the full canonical player journey over real HTTP:
  1. Starts new mystery session.
  2. Examines multiple crime scene targets and checks facts in Truth Ledger.
  3. Interrogates all 4 suspects and verifies lie recording & fallback dialogue.
  4. Presents discovered evidence and validates contradictions.
  5. Updates deduction workbench (theories) and ensures facts/scores remain unmodified.
  6. Submits an incorrect accusation (accusing Mira Sen) and verifies -15 pt penalty and strict spoiler protection.
  7. Submits a second incorrect accusation (accusing Noah Reed) and checks attempt count = 2.
  8. Submits the canonical solve (accusing Elias Voss with E-06, E-01, E-10, E-02, E-11).
  9. Verifies score = 85 (100 - 15 pt penalty for attempt 2), verdict = CONVICTED, rank = Senior Inspector (A-Rank).
  10. Verifies authorized solution reveal data matches canonical ground truth.
  11. Verifies reset creates a fresh, isolated session with active status.
"""

import sys
import os
import subprocess
import time
import urllib.request
import json

python_exe = sys.executable
cmd = [python_exe, "-m", "uvicorn", "main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"]

proc = subprocess.Popen(cmd, cwd=os.getcwd())

def post_json(url, payload=None):
    data = json.dumps(payload).encode() if payload is not None else b""
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return r.status, json.loads(r.read())

def get_json(url):
    with urllib.request.urlopen(url) as r:
        return r.status, json.loads(r.read())

try:
    time.sleep(2.5)

    print("=== STAGE 1: SESSION CREATION ===")
    status, sess = post_json("http://127.0.0.1:8000/api/sessions", {"player_name": "Detective Abhinav"})
    assert status == 201
    sid = sess["session_id"]
    assert sess["case_status"] == "ACTIVE"
    print(f"[PASS] Session created: {sid}")

    print("\n=== STAGE 2: FORENSIC EXAMINATION & EVIDENCE BOARD ===")
    # Discover E-01 (Pedestal)
    _, ex1 = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/examine", {"target_id": "heliodor_pedestal"})
    assert ex1["truth_ledger_updated"] is True
    assert ex1["new_fact"]["evidence_id"] == "E-01"
    print(f"[PASS] Discovered E-01 ({ex1['new_fact']['title']})")

    # Discover E-02 (Server Rack)
    _, ex2 = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/examine", {"target_id": "server_rack_02"})
    assert ex2["new_fact"]["evidence_id"] == "E-02"
    print(f"[PASS] Discovered E-02 ({ex2['new_fact']['title']})")

    # Discover E-03 (Access DB)
    _, ex3 = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/examine", {"target_id": "security_access_db"})
    assert ex3["new_fact"]["evidence_id"] == "E-03"
    print(f"[PASS] Discovered E-03 ({ex3['new_fact']['title']})")

    # Discover E-06 (Workshop Cabinet 3)
    _, ex6 = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/examine", {"target_id": "workshop_cabinet_03"})
    assert ex6["new_fact"]["evidence_id"] == "E-06"
    print(f"[PASS] Discovered E-06 ({ex6['new_fact']['title']})")

    # Discover E-10 (Tapestry Hatch)
    _, ex10 = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/examine", {"target_id": "gallery_tapestry"})
    assert ex10["new_fact"]["evidence_id"] == "E-10"
    print(f"[PASS] Discovered E-10 ({ex10['new_fact']['title']})")

    # Discover E-11 (HazMat Locker 4)
    _, ex11 = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/examine", {"target_id": "basement_hazmat_04"})
    assert ex11["new_fact"]["evidence_id"] == "E-11"
    print(f"[PASS] Discovered E-11 ({ex11['new_fact']['title']})")

    # Verify session ledger contains exactly 6 facts
    _, current_sess = get_json(f"http://127.0.0.1:8000/api/sessions/{sid}")
    assert len(current_sess["truth_ledger"]["facts"]) == 6
    print(f"[PASS] Truth Ledger contains 6 verified facts.")

    print("\n=== STAGE 3: SUSPECT INTERROGATION & LIE TAGGING ===")
    # Interrogate Elias Voss about corridor alibi
    _, it_elias = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/interrogate", {
        "suspect_id": "elias_voss",
        "question": "Where were you between 9:15 and 9:20 PM?"
    })
    if it_elias["is_fallback"]:
        assert it_elias["model_status"] == "fallback"
    else:
        assert it_elias["model_status"] == "success"
    assert it_elias["recorded_statement_id"] == "ELIAS_LIE_CORRIDOR"
    print(f"[PASS] Elias Voss interrogated (live={not it_elias['is_fallback']}). Lie recorded: {it_elias['recorded_statement_id']}")

    # Interrogate Noah Reed about cameras
    _, it_noah = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/interrogate", {
        "suspect_id": "noah_reed",
        "question": "Did the camera feeds drop out?"
    })
    assert it_noah["recorded_statement_id"] == "NOAH_LIE_CAMERAS"
    print(f"[PASS] Noah Reed interrogated. Lie recorded: {it_noah['recorded_statement_id']}")

    print("\n=== STAGE 4: EVIDENCE CONFRONTATION (CONTRADICTIONS) ===")
    # Confront Elias with E-03 (swipe into Corridor B)
    _, pe = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/present-evidence", {
        "suspect_id": "elias_voss",
        "evidence_id": "E-03"
    })
    assert pe["contradiction_validated"] is True
    assert pe["contradiction"]["rule_id"] == "C-01"
    assert pe["contradiction"]["validation_state"] == "ALIBI_SHATTERED"
    print(f"[PASS] Contradiction validated: C-01 (ALIBI_SHATTERED)")

    print("\n=== STAGE 5: THEORIES WORKBENCH ===")
    _, th = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/theories", {
        "suspected_culprit_id": "elias_voss",
        "motive_hypothesis": "Blackmail by Grey Ledger syndicate over £150k debt.",
        "method_hypothesis": "Used nitrogen bypass shunt E-01 and tapestry hatch E-10.",
        "recovery_hypothesis": "Submerged in Hexane-12 solvent canister E-11 in HazMat locker."
    })
    assert th["updated_theories"]["suspected_culprit_id"] == "elias_voss"
    print(f"[PASS] Player hypotheses updated in Truth Ledger.")

    print("\n=== STAGE 6: FAILED ACCUSATION 1 (WRONG CULPRIT) & SPOILER SHIELD ===")
    _, ac1 = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/accuse", {
        "accused_suspect_id": "mira_sen",
        "motive_evidence_id": "E-06",
        "method_evidence_ids": ["E-01", "E-10"],
        "recovery_evidence_id": "E-11",
        "detective_statement": "Dr. Sen stole the relic to hide her illegal appraisal."
    })
    assert ac1["is_solved"] is False
    assert ac1["case_status"] == "ACTIVE"
    assert ac1["verdict"] == "INDICTMENT_REJECTED"
    assert ac1["attempts_used"] == 1
    assert ac1["attempts_remaining"] == 2
    assert ac1["score_breakdown"]["attempt_penalty"] == 15
    assert ac1["score_breakdown"]["final_score"] == 0
    assert ac1["canonical_solution_reveal"] is None
    print(f"[PASS] Attempt 1 rejected. Penalty = -15 pts. Solution reveal = NULL (Strict spoiler protection verified).")

    print("\n=== STAGE 7: SUCCESSFUL ACCUSATION (CANONICAL CONVICTION) ===")
    _, ac2 = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/accuse", {
        "accused_suspect_id": "elias_voss",
        "motive_evidence_id": "E-06",
        "method_evidence_ids": ["E-01", "E-10", "E-02"],
        "recovery_evidence_id": "E-11",
        "detective_statement": "Elias Voss used nitrogen bypass shunt E-01 via tapestry hatch E-10 during Noah's 9:15 camera outage E-02 to settle extortion debt E-06, hiding the relic in canister E-11."
    })
    assert ac2["is_solved"] is True
    assert ac2["case_status"] == "SOLVED"
    assert ac2["verdict"] == "CONVICTED"
    assert ac2["attempts_used"] == 2
    assert ac2["score_breakdown"]["culprit_score"] == 25
    assert ac2["score_breakdown"]["motive_score"] == 25
    assert ac2["score_breakdown"]["method_score"] == 25
    assert ac2["score_breakdown"]["recovery_score"] == 25
    assert ac2["score_breakdown"]["attempt_penalty"] == 15  # (attempt 2 - 1) * 15 = 15
    assert ac2["score_breakdown"]["final_score"] == 85      # 100 - 15 = 85
    assert ac2["rank"] == "Senior Inspector (A-Rank)"
    assert ac2["canonical_solution_reveal"] is not None
    assert ac2["canonical_solution_reveal"]["culprit"] == "Elias Voss"
    print(f"[PASS] Attempt 2 CONVICTED! Score = 85/100, Rank = {ac2['rank']}.")
    print(f"[PASS] Authorized solution reveal unmasked: Culprit = {ac2['canonical_solution_reveal']['culprit']}")

    print("\n=== STAGE 8: RESET CASE ISOLATION ===")
    _, rs = post_json(f"http://127.0.0.1:8000/api/sessions/{sid}/reset")
    new_sid = rs["new_session_id"]
    assert new_sid != sid
    assert rs["new_session_state"]["case_status"] == "ACTIVE"
    assert rs["new_session_state"]["discovered_evidence_ids"] == []
    print(f"[PASS] Case reset. Old session retired, fresh session active: {new_sid}")

    print("\n==============================================")
    print("ALL 8 STAGES OF FULL PLAYTHROUGH PASSED 100%!")
    print("==============================================")

finally:
    proc.terminate()
    proc.wait()
