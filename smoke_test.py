import sys
import os
import subprocess
import time
import urllib.request
import json

# Start uvicorn server in a subprocess
python_exe = sys.executable
cmd = [python_exe, "-m", "uvicorn", "main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8000", "--log-level", "warning"]

proc = subprocess.Popen(cmd, cwd=os.getcwd())
try:
    time.sleep(2.5)

    # 1. Health
    with urllib.request.urlopen("http://127.0.0.1:8000/api/health") as r:
        data = json.loads(r.read())
        print(f"1. GET /api/health: {r.status} {data}")

    # 2. Config
    with urllib.request.urlopen("http://127.0.0.1:8000/api/config") as r:
        cfg = json.loads(r.read())
        print(f"2. GET /api/config: {r.status} (locations={len(cfg['locations'])}, suspects={len(cfg['suspects'])})")

    # 3. Create Session
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/sessions",
        data=json.dumps({"player_name": "Detective Abhinav"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        sess = json.loads(r.read())
        sid = sess["session_id"]
        print(f"3. POST /api/sessions: {r.status} sid={sid}")

    # 4. Examine Target
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/sessions/{sid}/examine",
        data=json.dumps({"target_id": "heliodor_pedestal"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        ex = json.loads(r.read())
        print(f"4. POST /api/sessions/{{sid}}/examine: {r.status} fact={ex['new_fact']['fact_id']}")

    # 5. Interrogate Suspect
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/sessions/{sid}/interrogate",
        data=json.dumps({"suspect_id": "elias_voss", "question": "Where were you at 9:15 PM?"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        it = json.loads(r.read())
        print(f"5. POST /api/sessions/{{sid}}/interrogate: {r.status} lie_tag={it['recorded_statement_id']} is_fallback={it['is_fallback']}")

    # 6. Present Evidence (after discovering E-03)
    # First examine security_access_db to get E-03
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/sessions/{sid}/examine",
        data=json.dumps({"target_id": "security_access_db"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req):
        pass

    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/sessions/{sid}/present-evidence",
        data=json.dumps({"suspect_id": "elias_voss", "evidence_id": "E-03"}).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        pe = json.loads(r.read())
        print(f"6. POST /api/sessions/{{sid}}/present-evidence: {r.status} contradiction={pe['contradiction_validated']} rule={pe['contradiction']['rule_id']}")

    # 7. Update Theories
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/sessions/{sid}/theories",
        data=json.dumps({
            "suspected_culprit_id": "elias_voss",
            "motive_hypothesis": "Extorted over gambling debt."
        }).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        th = json.loads(r.read())
        print(f"7. POST /api/sessions/{{sid}}/theories: {r.status} msg={th['message']}")

    # 8. Accuse Suspect
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/sessions/{sid}/accuse",
        data=json.dumps({
            "accused_suspect_id": "noah_reed",
            "motive_evidence_id": "E-01",
            "method_evidence_ids": ["E-01", "E-03"],
            "recovery_evidence_id": "E-01",
            "detective_statement": "Testing rejection behavior."
        }).encode(),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        ac = json.loads(r.read())
        print(f"8. POST /api/sessions/{{sid}}/accuse: {r.status} verdict={ac['verdict']} spoiler_protected={ac['canonical_solution_reveal'] is None}")

    # 9. Reset Session
    req = urllib.request.Request(
        f"http://127.0.0.1:8000/api/sessions/{sid}/reset",
        data=b"",
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as r:
        rs = json.loads(r.read())
        new_sid = rs["new_session_id"]
        print(f"9. POST /api/sessions/{{sid}}/reset: {r.status} new_sid={new_sid} (different={new_sid != sid})")

    print("\nALL HTTP SMOKE TESTS PASSED!")

finally:
    proc.terminate()
    proc.wait()
