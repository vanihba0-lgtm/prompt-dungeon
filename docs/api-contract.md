# Prompt Dungeon: The Last Exhibition
## REST API Contract Specification (v1.1.0)

---

## 1. Overview & Architectural Principles

This document defines the formal REST API contract for **Prompt Dungeon: The Last Exhibition**. It serves as the single interface agreement between Abhinav (Python/FastAPI backend & deterministic engine) and Vishal (React/TypeScript/Vite frontend).

### 1.1 Core Principles
1. **Deterministic Authority:** The backend is the sole source of truth. All game states (evidence discovery, contradiction validation, Truth Ledger updates, scoring, and accusation grading) are computed deterministically on the server.
2. **Client Decoupling & Mock-Friendly Design:** All endpoints feature explicit TypeScript request/response schemas, stable identifiers, and representative JSON examples so the frontend can develop against mock fixtures before the backend is complete.
3. **Information Hiding (No Solution Leaks):** Player-facing endpoints never serialize internal solution keys, true guilt flags, or spoiler clues. On failed accusations, responses describe the procedural failure without revealing missing evidence or the culprit's identity. The canonical solution is revealed only upon solving the case or final case dismissal.
4. **Honest Model & Fallback Metadata:** Every dialogue response explicitly identifies whether text was generated dynamically by a model or provided by pre-authored deterministic fallback trees (`model_status: "success" | "fallback" | "unavailable"`, `is_fallback: boolean`). Fallback dialogue is never disguised as model generation.
5. **Session Isolation & Extensibility:** Sessions are identified by UUIDv4 tokens. In the MVP, sessions are held in an in-memory dictionary behind an abstract service interface to enable a seamless migration to SQLite in future iterations.

---

## 2. Global Conventions, Identifiers & Envelopes

### 2.1 Base URL & Content Type
* **Base URL:** `http://localhost:8000/api`
* **Content-Type:** `application/json; charset=utf-8`

### 2.2 Stable Identifiers

#### Suspect IDs
| Suspect ID | Full Name | Public Role |
| :--- | :--- | :--- |
| `elias_voss` | Elias Voss | Chief Conservator & Restoration Specialist |
| `mira_sen` | Dr. Mira Sen | Lead Curator of Antiquities |
| `noah_reed` | Noah Reed | Security Systems Technician |
| `celeste_ward` | Celeste Ward | Private Antiquities Collector & Donor |

#### Evidence IDs (`E-01` to `E-12`)
| Evidence ID | Short Title | Mandatory for Conviction | Relevant Target ID |
| :--- | :--- | :--- | :--- |
| `E-01` | Severed Vitrine Sensor Shunt | **Yes** (Method) | `heliodor_pedestal` |
| `E-02` | Security Switch Terminal Log | **Yes** (Blackout Window) | `server_rack_02` |
| `E-03` | Restricted Keycard Swipe Log | **Yes** (Proximity) | `security_access_db` |
| `E-04` | Torn Appraisal Memo Fragments | No (False lead clarifier) | `curator_shredder` |
| `E-05` | Engraved Monogrammed Lighter | No (False lead clarifier) | `west_archive_floor` |
| `E-06` | Debt Ultimatum & Pawn Ticket | **Yes** (Motive) | `workshop_cabinet_03` |
| `E-07` | Antistatic Fiber & Solvent Traces | **Yes** (Method / Clue to E-11) | `vitrine_latch` |
| `E-08` | Terrace Waitstaff Order Slip #408 | No (False lead clarifier) | `terrace_catering_bar` |
| `E-09` | Encrypted USB Drive & Forum Logs | No (False lead clarifier) | `technician_locker` |
| `E-10` | Tapestry Service Hatch Scuff Marks | **Yes** (Ingress / Egress) | `gallery_tapestry` |
| `E-11` | Weighted Hexane-12 Solvent Canister | **Yes** (Artifact Recovery) | `basement_hazmat_04` |
| `E-12` | Dictaphone Audio Memo #14 | No (False lead clarifier) | `curator_desk` |

#### Contradiction Rule IDs (`C-01` to `C-08`)
* `C-01`: Elias Voss — Corridor Presence (Refuted by `E-03`)
* `C-02`: Elias Voss — Tool Locking Status (Refuted by `E-01` / `E-07`)
* `C-03`: Elias Voss — Personal Finances (Refuted by `E-06`)
* `C-04`: Noah Reed — Camera Feed Continuity (Refuted by `E-02`)
* `C-05`: Noah Reed — Terminal Diagnostic Scripts (Refuted by `E-09`)
* `C-06`: Dr. Mira Sen — Ballroom Presence (Refuted by `E-03`)
* `C-07`: Dr. Mira Sen — Third-Party Appraisal (Refuted by `E-04` / `E-12`)
* `C-08`: Celeste Ward — Terrace Continuous Presence (Refuted by `E-05` / `E-08`)

#### Investigation Targets (Locations & Physical Objects)
All examination requests must specify a valid `target_id` from this predefined catalog. The frontend presents these as selectable targets; players never guess internal IDs via free-form text.

| Target ID | Display Name | Facility Zone | Yielded Evidence | Discovery Condition / Fair Path |
| :--- | :--- | :--- | :--- | :--- |
| `heliodor_pedestal` | Heliodor Gallery — Pedestal Base | Crime Scene | `E-01` | Inspect pedestal after noting glass is intact. |
| `vitrine_latch` | Heliodor Gallery — Vitrine Rim & Lock | Crime Scene | `E-07` | Chemical/swab inspection of vitrine latch. |
| `gallery_tapestry` | Heliodor Gallery — South Tapestry & Wall | Crime Scene | `E-10` | Search perimeter or retrace Corridor B passage. |
| `server_rack_02` | Basement Server Room — Switch 04 Console | Security Hub | `E-02` | Query CCTV terminal after learning of outage. |
| `security_access_db` | Security Control Booth — Access Mainframe | Security Hub | `E-03` | Query interior card access database. |
| `curator_shredder` | Curator Office — Paper Shredder Bin | Admin Wing | `E-04` | Search office after noting Dr. Sen's absence. |
| `curator_desk` | Curator Office — Desk Drawer | Admin Wing | `E-12` | Physical search of Dr. Sen's desk drawers. |
| `west_archive_floor` | West Archive Wing — Corridor Floor | Archives | `E-05` | Sweep archive hallway floor near radiator. |
| `workshop_cabinet_03`| Conservation Lab — Locked Tool Cabinet 3 | Conservation | `E-06` | Search Elias Voss's locked workbench cabinet. |
| `basement_hazmat_04` | Basement Annex — Flammable Storage 4 | Conservation | `E-11` | Follow Hexane-12 clue (`E-07`) to chemical locker. |
| `terrace_catering_bar`| Terrace Bar — Catering Service Log | Public Gala | `E-08` | Interview catering staff regarding guest orders. |
| `technician_locker` | Guard Quarters — Noah Reed's Locker | Staff Rooms | `E-09` | Search locker after discovering script in `E-02`. |

---

### 2.3 Global Error Envelope
All error responses (HTTP 4xx and 5xx) share a uniform JSON envelope:

```typescript
interface ApiErrorEnvelope {
  error: {
    code: string;       // UPPER_SNAKE_CASE machine-readable code
    message: string;    // Clear, user-friendly explanation
    details?: Record<string, unknown>; // Optional structured context
    retryable: boolean; // Indicates if client should retry immediately
  };
}
```

#### Standard Error Codes
| HTTP Status | Error Code | Description | Retryable |
| :---: | :--- | :--- | :---: |
| `400` | `INVALID_REQUEST` | Malformed JSON or missing required fields | `false` |
| `400` | `INVALID_SESSION_ID` | Session ID is not a valid RFC 4122 UUIDv4 | `false` |
| `400` | `EMPTY_QUESTION` | Question text is empty or whitespace-only | `false` |
| `400` | `QUESTION_TOO_LONG` | Question exceeds 500 characters | `false` |
| `404` | `SESSION_NOT_FOUND` | Session ID does not exist or has expired | `false` |
| `404` | `TARGET_NOT_FOUND` | Suspect, evidence, or location ID invalid | `false` |
| `409` | `SESSION_CLOSED` | Session is marked RESET or CLOSED; cannot accept actions | `false` |
| `409` | `EVIDENCE_NOT_DISCOVERED` | Player attempted to present unverified evidence | `false` |
| `409` | `STATEMENT_NOT_RECORDED` | Contradiction attempted before suspect made false statement | `false` |
| `409` | `MAX_ATTEMPTS_EXCEEDED` | Accusation attempted after case already closed | `false` |
| `429` | `RATE_LIMIT_EXCEEDED` | Interrogation rate limit exceeded (30 req/min) | `true` |
| `503` | `MODEL_UNAVAILABLE` | Dialogue LLM offline and no fallback could respond | `true` |

---

## 3. Truth Ledger & Session State Schemas

### 3.1 The Truth Ledger Schema
The Truth Ledger strictly isolates immutable facts, engine-validated contradictions, and player theories:

```typescript
interface TruthLedger {
  // Facts: Discovered physical evidence and verified forensic records
  facts: DiscoveredFact[];
  // Contradictions: Engine-validated collisions between suspect lies and evidence
  contradictions: ValidatedContradiction[];
  // Theories: Player's subjective deduction workbench (unverified until accusation)
  theories: PlayerTheories;
}

interface DiscoveredFact {
  fact_id: string;              // e.g. "FACT_E01_SHUNT"
  evidence_id: string;          // e.g. "E-01"
  title: string;                // "Severed Vitrine Sensor Shunt"
  summary: string;              // Forensic interpretation of the item
  discovered_at: string;        // ISO-8601 timestamp
  category: "FORENSIC" | "DIGITAL_LOG" | "DOCUMENT" | "PHYSICAL_TRACE";
}

interface ValidatedContradiction {
  rule_id: string;              // e.g. "C-01"
  suspect_id: string;           // e.g. "elias_voss"
  disputed_claim: string;       // "Claims he never entered Service Corridor B after 8:45 PM."
  refuting_evidence_id: string; // "E-03"
  validation_state: string;     // "ALIBI_SHATTERED"
  validated_at: string;         // ISO-8601 timestamp
}

interface PlayerTheories {
  suspected_culprit_id: string | null;
  motive_hypothesis: string;
  method_hypothesis: string;
  recovery_hypothesis: string;
  updated_at: string;
}
```

### 3.2 Full Session State Schema
Returned by `GET /api/sessions/{session_id}` and session creation:

```typescript
interface SessionStateResponse {
  session_id: string;
  created_at: string;
  case_status: "ACTIVE" | "SOLVED" | "CLOSED" | "RESET";
  accusation_attempts: number;
  max_accusation_attempts: number;
  current_penalty: number;
  discovered_evidence_ids: string[];
  interrogated_suspect_ids: string[];
  truth_ledger: TruthLedger;
  recent_events: SessionEventLog[];
}

interface SessionEventLog {
  event_type: "EXAMINE" | "INTERROGATE" | "PRESENT_EVIDENCE" | "THEORY_UPDATE" | "ACCUSE";
  target_id: string;
  timestamp: string;
  summary: string;
}
```

---

## 4. Complete Endpoint Specifications

### 4.1 System & Configuration Endpoints

---

#### `GET /api/health`
Checks backend operational status, deterministic engine health, and LLM provider connectivity. Does not expose credentials, provider URLs, or internal secrets.

* **Method:** `GET`
* **Path:** `/api/health`
* **Request:** None
* **Success Response (`200 OK`):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "engine_status": "deterministic_ready",
  "model_status": "online",
  "timestamp": "2026-10-12T12:30:00Z"
}
```
* **Degraded Response (`200 OK`):**
```json
{
  "status": "degraded",
  "version": "1.0.0",
  "engine_status": "deterministic_ready",
  "model_status": "fallback",
  "timestamp": "2026-10-12T12:30:00Z"
}
```

---

#### `GET /api/config`
Provides static frontend configuration, including suspect rosters, searchable location directories, evidence metadata templates, and scoring rule limits. Contains zero spoiler data (no guilt flags, no solution keys).

* **Method:** `GET`
* **Path:** `/api/config`
* **Request:** None
* **Success Response (`200 OK`):**
```json
{
  "case_meta": {
    "case_id": "the_last_exhibition",
    "case_title": "The Last Exhibition",
    "incident_time": "2026-10-12T21:17:00Z",
    "facility": "Blackwood Museum of Antiquities"
  },
  "rules": {
    "max_accusation_attempts": 3,
    "penalty_per_failed_accusation": 15,
    "history_window_turns": 6,
    "rate_limit_interrogations_per_minute": 30,
    "max_question_length": 500
  },
  "suspects": [
    {
      "suspect_id": "elias_voss",
      "name": "Elias Voss",
      "role": "Chief Conservator",
      "avatar": "/assets/suspects/elias_voss.webp",
      "bio": "Veteran conservator of 14 years. Meticulous specialist in Mesoamerican glass."
    },
    {
      "suspect_id": "mira_sen",
      "name": "Dr. Mira Sen",
      "role": "Lead Curator",
      "avatar": "/assets/suspects/mira_sen.webp",
      "bio": "Academic prodigy who curated the loan of the Obsidian Sun."
    },
    {
      "suspect_id": "noah_reed",
      "name": "Noah Reed",
      "role": "Security Systems Technician",
      "avatar": "/assets/suspects/noah_reed.webp",
      "bio": "Junior technician managing the museum's digital security infrastructure."
    },
    {
      "suspect_id": "celeste_ward",
      "name": "Celeste Ward",
      "role": "Antiquities Collector",
      "avatar": "/assets/suspects/celeste_ward.webp",
      "bio": "Prominent billionaire patron whose acquisition bids were rejected."
    }
  ],
  "locations": [
    {
      "target_id": "heliodor_pedestal",
      "name": "Heliodor Gallery — Pedestal Base",
      "zone": "Crime Scene"
    },
    {
      "target_id": "vitrine_latch",
      "name": "Heliodor Gallery — Vitrine Lock Rim",
      "zone": "Crime Scene"
    },
    {
      "target_id": "gallery_tapestry",
      "name": "Heliodor Gallery — Wall Tapestry",
      "zone": "Crime Scene"
    },
    {
      "target_id": "server_rack_02",
      "name": "Basement Server Room — Switch 04",
      "zone": "Security Hub"
    },
    {
      "target_id": "security_access_db",
      "name": "Security Booth — Card Access Mainframe",
      "zone": "Security Hub"
    },
    {
      "target_id": "curator_shredder",
      "name": "Curator Office — Paper Shredder",
      "zone": "Administrative Wing"
    },
    {
      "target_id": "curator_desk",
      "name": "Curator Office — Desk Drawer",
      "zone": "Administrative Wing"
    },
    {
      "target_id": "west_archive_floor",
      "name": "West Archive Corridor — Hallway Floor",
      "zone": "Restricted Archives"
    },
    {
      "target_id": "workshop_cabinet_03",
      "name": "Conservation Workshop — Cabinet 3",
      "zone": "Conservation Lab"
    },
    {
      "target_id": "basement_hazmat_04",
      "name": "Basement Annex — Flammable Storage 4",
      "zone": "Conservation Lab"
    },
    {
      "target_id": "terrace_catering_bar",
      "name": "Terrace Bar — Catering Order Logs",
      "zone": "Public Gala"
    },
    {
      "target_id": "technician_locker",
      "name": "Staff Quarters — Noah's Locker",
      "zone": "Staff Facilities"
    }
  ]
}
```

---

### 4.2 Session Management Endpoints

---

#### `POST /api/sessions`
Creates an isolated investigation session with an initialized Truth Ledger and empty discovery history.

* **Method:** `POST`
* **Path:** `/api/sessions`
* **Headers:** `Content-Type: application/json`
* **Request Body:** `{}` (Optional `{ "player_name": string }` accepted)
* **Success Response (`201 Created`):**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-10-12T12:35:10Z",
  "case_status": "ACTIVE",
  "accusation_attempts": 0,
  "max_accusation_attempts": 3,
  "current_penalty": 0,
  "discovered_evidence_ids": [],
  "interrogated_suspect_ids": [],
  "truth_ledger": {
    "facts": [],
    "contradictions": [],
    "theories": {
      "suspected_culprit_id": null,
      "motive_hypothesis": "",
      "method_hypothesis": "",
      "recovery_hypothesis": "",
      "updated_at": "2026-10-12T12:35:10Z"
    }
  },
  "recent_events": [
    {
      "event_type": "EXAMINE",
      "target_id": "SYSTEM",
      "timestamp": "2026-10-12T12:35:10Z",
      "summary": "Case session initialized."
    }
  ]
}
```

---

#### `GET /api/sessions/{session_id}`
Retrieves the complete active session state. Validates UUID format.

* **Method:** `GET`
* **Path:** `/api/sessions/{session_id}`
* **Success Response (`200 OK`):** Same schema as `SessionStateResponse`.
* **Failure Response: Invalid UUID (`400 Bad Request`):**
```json
{
  "error": {
    "code": "INVALID_SESSION_ID",
    "message": "Session ID 'not-a-valid-uuid' must be a valid RFC 4122 UUIDv4.",
    "retryable": false
  }
}
```
* **Failure Response: Not Found (`404 Not Found`):**
```json
{
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session '550e8400-e29b-41d4-a716-446655440000' does not exist or has expired.",
    "retryable": false
  }
}
```

---

#### `POST /api/sessions/{session_id}/reset`
Marks the current session as `RESET` and returns a fresh, fully initialized session. Subsequent requests using the previous session ID will return HTTP 409 `SESSION_CLOSED`.

* **Method:** `POST`
* **Path:** `/api/sessions/{session_id}/reset`
* **Request Body:** `{}`
* **Success Response (`200 OK`):**
```json
{
  "previous_session_id": "550e8400-e29b-41d4-a716-446655440000",
  "new_session_id": "7b1341c2-c0e8-466d-926f-409191d830b1",
  "created_at": "2026-10-12T12:38:00Z",
  "message": "Investigation reset. Fresh session initialized.",
  "new_session_state": {
    "session_id": "7b1341c2-c0e8-466d-926f-409191d830b1",
    "created_at": "2026-10-12T12:38:00Z",
    "case_status": "ACTIVE",
    "accusation_attempts": 0,
    "max_accusation_attempts": 3,
    "current_penalty": 0,
    "discovered_evidence_ids": [],
    "interrogated_suspect_ids": [],
    "truth_ledger": {
      "facts": [],
      "contradictions": [],
      "theories": {
        "suspected_culprit_id": null,
        "motive_hypothesis": "",
        "method_hypothesis": "",
        "recovery_hypothesis": "",
        "updated_at": "2026-10-12T12:38:00Z"
      }
    },
    "recent_events": [
      {
        "event_type": "EXAMINE",
        "target_id": "SYSTEM",
        "timestamp": "2026-10-12T12:38:00Z",
        "summary": "Session reset; fresh investigation started."
      }
    ]
  }
}
```

---

### 4.3 Detective Investigation Endpoints

---

#### `POST /api/sessions/{session_id}/interrogate`
Submits a free-form question to a suspect. The backend validates suspect ID and question bounds (1–500 trimmed characters). Applies a configurable 30 req/min rate limit.

* **Method:** `POST`
* **Path:** `/api/sessions/{session_id}/interrogate`
* **Request Schema:**
```typescript
interface InterrogateRequest {
  suspect_id: "elias_voss" | "mira_sen" | "noah_reed" | "celeste_ward";
  question: string; // Trimmed length: 1 to 500 characters
}
```
* **Request Example:**
```json
{
  "suspect_id": "elias_voss",
  "question": "Where were you between 9:15 and 9:20 PM while the camera feed was down?"
}
```

* **Success Response (Dynamic Model Generation) (`200 OK`):**
```json
{
  "suspect_id": "elias_voss",
  "question": "Where were you between 9:15 and 9:20 PM while the camera feed was down?",
  "reply": "I was down in the basement restoration lab preparing mounting adhesives for tomorrow's exhibition. I never entered Service Corridor B or the gallery area after the 8:45 PM public inspection.",
  "recorded_statement_id": "ELIAS_LIE_CORRIDOR",
  "is_fallback": false,
  "model_status": "success",
  "dialogue_turn_index": 3,
  "timestamp": "2026-10-12T12:40:12Z"
}
```

* **Success Response (Deterministic Authored Fallback) (`200 OK`):**
```json
{
  "suspect_id": "elias_voss",
  "question": "Where were you between 9:15 and 9:20 PM while the camera feed was down?",
  "reply": "As I have explained, I was in the basement conservation lab working with optical adhesive. I did not enter the gallery after 8:45 PM.",
  "recorded_statement_id": "ELIAS_LIE_CORRIDOR",
  "is_fallback": true,
  "model_status": "fallback",
  "fallback_reason": "MODEL_TIMEOUT",
  "dialogue_turn_index": 3,
  "timestamp": "2026-10-12T12:40:15Z"
}
```

* **Error Response: Empty Question (`400 Bad Request`):**
```json
{
  "error": {
    "code": "EMPTY_QUESTION",
    "message": "Question cannot be empty or contain only whitespace.",
    "retryable": false
  }
}
```

* **Error Response: Question Too Long (`400 Bad Request`):**
```json
{
  "error": {
    "code": "QUESTION_TOO_LONG",
    "message": "Question exceeds maximum allowed length of 500 characters.",
    "details": { "max_length": 500, "provided_length": 582 },
    "retryable": false
  }
}
```

* **Error Response: Rate Limit Exceeded (`429 Too Many Requests`):**
* **Headers:** `Retry-After: 2`
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Interrogation rate limit exceeded (30 requests/minute). Please wait before asking another question.",
    "details": { "retry_after_seconds": 2, "limit_per_minute": 30 },
    "retryable": true
  }
}
```

---

#### `POST /api/sessions/{session_id}/examine`
Inspects a physical location or equipment rack from the predefined target list. Repeated examination is idempotent: it does not duplicate evidence or alter score.

* **Method:** `POST`
* **Path:** `/api/sessions/{session_id}/examine`
* **Request Schema:**
```typescript
interface ExamineRequest {
  target_id: string; // Valid location from GET /api/config
}
```
* **Request Example:**
```json
{
  "target_id": "heliodor_pedestal"
}
```
* **Success Response: First Discovery (`200 OK`):**
```json
{
  "target_id": "heliodor_pedestal",
  "inspection_narrative": "You inspect the recessed service panel at the base of the vitrine pedestal. A brass micro-bore adapter equipped with a secondary pressure-relief valve is coupled to the nitrogen intake nipple.",
  "uncovered_evidence": {
    "evidence_id": "E-01",
    "title": "Severed Vitrine Sensor Shunt",
    "description": "A brass micro-bore adapter equipped with a secondary pressure-relief valve and quick-release nitrogen coupling, currently attached to the intake nipple at the base of the vitrine pedestal.",
    "category": "FORENSIC",
    "is_mandatory": true,
    "already_discovered": false
  },
  "truth_ledger_updated": true,
  "new_fact": {
    "fact_id": "FACT_E01_SHUNT",
    "evidence_id": "E-01",
    "title": "Severed Vitrine Sensor Shunt",
    "summary": "Vitrine was bypassed using a custom nitrogen equalizing shunt, disproving forced entry.",
    "discovered_at": "2026-10-12T12:42:00Z",
    "category": "FORENSIC"
  }
}
```
* **Success Response: Repeated Examination (`200 OK`):**
```json
{
  "target_id": "heliodor_pedestal",
  "inspection_narrative": "The recessed service panel remains open. The brass bypass shunt (E-01) has already been logged into forensic inventory.",
  "uncovered_evidence": {
    "evidence_id": "E-01",
    "title": "Severed Vitrine Sensor Shunt",
    "description": "A brass micro-bore adapter...",
    "category": "FORENSIC",
    "is_mandatory": true,
    "already_discovered": true
  },
  "truth_ledger_updated": false,
  "new_fact": null
}
```
* **Error Response: Target Not Found (`404 Not Found`):**
```json
{
  "error": {
    "code": "TARGET_NOT_FOUND",
    "message": "Target 'unknown_vault' does not exist in the facility directory.",
    "retryable": false
  }
}
```

---

#### `POST /api/sessions/{session_id}/present-evidence`
Confronts a suspect with an explicitly discovered evidence item to test for contradictions (`C-01` to `C-08`). 

* **Validation Rules:**
  1. `evidence_id` must be present in `discovered_evidence_ids`. If not, returns HTTP 409 `EVIDENCE_NOT_DISCOVERED`.
  2. If the suspect has made the corresponding false statement in dialogue history, the contradiction rule is validated and added to `truth_ledger.contradictions`.
  3. If the suspect has not yet made the contradictory statement, the suspect dismisses the item and no contradiction is validated.

* **Method:** `POST`
* **Path:** `/api/sessions/{session_id}/present-evidence`
* **Request Schema:**
```typescript
interface PresentEvidenceRequest {
  suspect_id: "elias_voss" | "mira_sen" | "noah_reed" | "celeste_ward";
  evidence_id: string; // e.g. "E-03"
}
```
* **Request Example:**
```json
{
  "suspect_id": "elias_voss",
  "evidence_id": "E-03"
}
```
* **Success Response: Contradiction Validated (`200 OK`):**
```json
{
  "suspect_id": "elias_voss",
  "evidence_id": "E-03",
  "contradiction_validated": true,
  "contradiction": {
    "rule_id": "C-01",
    "suspect_id": "elias_voss",
    "disputed_claim": "Claims he never entered Service Corridor B after 8:45 PM.",
    "refuting_evidence_id": "E-03",
    "validation_state": "ALIBI_SHATTERED",
    "validated_at": "2026-10-12T12:45:00Z"
  },
  "suspect_reaction": "Elias blinks, his composure faltering. 'I... well, yes. I swiped into the corridor for two minutes to fetch specialized lint-free cleaning rags from the auxiliary bin. That is hardly a crime.'",
  "is_fallback": false,
  "model_status": "success"
}
```
* **Success Response: No Contradiction (`200 OK`):**
```json
{
  "suspect_id": "noah_reed",
  "evidence_id": "E-01",
  "contradiction_validated": false,
  "contradiction": null,
  "suspect_reaction": "Noah shrugs nervously. 'That looks like some brass plumbing valve. I monitor network cables and IP cameras; I have no idea what that is.'",
  "is_fallback": false,
  "model_status": "success"
}
```
* **Error Response: Undiscovered Evidence (`409 Conflict`):**
```json
{
  "error": {
    "code": "EVIDENCE_NOT_DISCOVERED",
    "message": "Evidence 'E-06' cannot be presented because it has not yet been discovered in the investigation.",
    "retryable": false
  }
}
```

---

#### `POST /api/sessions/{session_id}/theories`
Updates the player's deduction workbench in the Truth Ledger without submitting an accusation.

* **Method:** `POST`
* **Path:** `/api/sessions/{session_id}/theories`
* **Request Schema:**
```typescript
interface UpdateTheoriesRequest {
  suspected_culprit_id?: string | null;
  motive_hypothesis?: string;
  method_hypothesis?: string;
  recovery_hypothesis?: string;
}
```
* **Request Example:**
```json
{
  "suspected_culprit_id": "elias_voss",
  "motive_hypothesis": "Extorted by Grey Ledger syndicate over gambling debt.",
  "method_hypothesis": "Used nitrogen bypass shunt E-01 and tapestry service hatch E-10.",
  "recovery_hypothesis": "Hidden in Hexane-12 canister in basement HazMat locker."
}
```
* **Success Response (`200 OK`):**
```json
{
  "updated_theories": {
    "suspected_culprit_id": "elias_voss",
    "motive_hypothesis": "Extorted by Grey Ledger syndicate over gambling debt.",
    "method_hypothesis": "Used nitrogen bypass shunt E-01 and tapestry service hatch E-10.",
    "recovery_hypothesis": "Hidden in Hexane-12 canister in basement HazMat locker.",
    "updated_at": "2026-10-12T12:47:00Z"
  },
  "message": "Truth Ledger theories successfully updated."
}
```

---

#### `POST /api/sessions/{session_id}/accuse`
Submits a formal indictment. Evaluates the accusation against the Canonical Solution Key across four dimensions: Culprit, Motive, Method, and Recovery.

* **Method:** `POST`
* **Path:** `/api/sessions/{session_id}/accuse`
* **Request Schema:**
```typescript
interface AccuseRequest {
  accused_suspect_id: "elias_voss" | "mira_sen" | "noah_reed" | "celeste_ward";
  motive_evidence_id: string;       // Discovered evidence proving motive
  method_evidence_ids: string[];     // Discovered evidence proving method (min 2)
  recovery_evidence_id: string;     // Discovered evidence locating artifact
  detective_statement: string;      // Trimmed string: 1 to 1000 characters
}
```
* **Request Example:**
```json
{
  "accused_suspect_id": "elias_voss",
  "motive_evidence_id": "E-06",
  "method_evidence_ids": ["E-01", "E-10", "E-02"],
  "recovery_evidence_id": "E-11",
  "detective_statement": "Elias Voss took advantage of Noah's camera outage at 9:15 PM, entered via the tapestry hatch, and used the nitrogen shunt tool to extract the artifact to settle his debt."
}
```

* **Success Response: Solved Case (`200 OK`):**
```json
{
  "is_solved": true,
  "case_status": "SOLVED",
  "verdict": "CONVICTED",
  "attempts_used": 1,
  "attempts_remaining": 2,
  "score_breakdown": {
    "culprit_score": 25,
    "motive_score": 25,
    "method_score": 25,
    "recovery_score": 25,
    "attempt_penalty": 0,
    "final_score": 100
  },
  "rank": "Master Detective (S-Rank)",
  "narrative_debrief": "District Magistrate approves immediate arrest. Elias Voss confesses upon being presented with the Hexane-12 canister recovered from HazMat Cabinet 4. The Obsidian Sun is secured without damage.",
  "canonical_solution_reveal": {
    "culprit": "Elias Voss",
    "motive": "£150,000 extortion debt to the Grey Ledger syndicate due at midnight.",
    "method": "Nitrogen atmospheric shunt E-01 coupled to vitrine; ingress/egress via tapestry hatch E-10 during Noah Reed's 9:15-9:19 camera crash.",
    "recovery_location": "Padded silicone bladder inside Hexane-12 solvent canister E-11."
  }
}
```

* **Success Response: Failed Accusation (Investigation Continues) (`200 OK`):**
```json
{
  "is_solved": false,
  "case_status": "ACTIVE",
  "verdict": "INDICTMENT_REJECTED",
  "attempts_used": 1,
  "attempts_remaining": 2,
  "score_breakdown": {
    "culprit_score": 0,
    "motive_score": 0,
    "method_score": 0,
    "recovery_score": 0,
    "attempt_penalty": 15,
    "final_score": 0
  },
  "rank": null,
  "narrative_debrief": "The District Magistrate rejects the warrant. The evidence presented is deemed insufficient or circumstantial. The suspect remains detained for questioning, but you must solidify your proof before filing again.",
  "canonical_solution_reveal": null
}
```

* **Success Response: Third Failed Accusation (Case Closed / Dismissed) (`200 OK`):**
```json
{
  "is_solved": false,
  "case_status": "CLOSED",
  "verdict": "CASE_DISMISSED",
  "attempts_used": 3,
  "attempts_remaining": 0,
  "score_breakdown": {
    "culprit_score": 0,
    "motive_score": 0,
    "method_score": 0,
    "recovery_score": 0,
    "attempt_penalty": 45,
    "final_score": 0
  },
  "rank": "Case Dismissed (Failure)",
  "narrative_debrief": "Three formal indictments have collapsed. The District Magistrate revokes your investigative authority and releases the suspects. The case is closed unsolved.",
  "canonical_solution_reveal": {
    "culprit": "Elias Voss",
    "motive": "£150,000 extortion debt to the Grey Ledger syndicate due at midnight.",
    "method": "Nitrogen atmospheric shunt E-01 coupled to vitrine; ingress/egress via tapestry hatch E-10.",
    "recovery_location": "Hexane-12 canister in basement HazMat locker E-11."
  }
}
```

* **Error Response: Accusation Attempted When Case Closed (`409 Conflict`):**
```json
{
  "error": {
    "code": "MAX_ATTEMPTS_EXCEEDED",
    "message": "This case has reached its maximum of 3 accusation attempts and is closed.",
    "retryable": false
  }
}
```

---

## 5. Accusation Scoring Algorithm (Backend Engine Specification)

When `/api/sessions/{session_id}/accuse` is called, the deterministic scoring engine computes the result using this exact algorithm:

```python
# Deterministic scoring calculation
def grade_accusation(session, request):
    if session.case_status in ("CLOSED", "RESET"):
        raise MaxAttemptsExceededError()

    session.accusation_attempts += 1
    
    # 1. Check Culprit (25 pts - Gatekeeper)
    # Naming any suspect other than Elias Voss fails the accusation completely.
    is_culprit_correct = (request.accused_suspect_id == "elias_voss")
    culprit_pts = 25 if is_culprit_correct else 0
    
    # 2. Check Motive (25 pts)
    # Must provide E-06 and have verified it was discovered in session.
    is_motive_correct = (
        request.motive_evidence_id == "E-06" and 
        "E-06" in session.discovered_evidence_ids
    )
    motive_pts = 25 if (is_culprit_correct and is_motive_correct) else 0
    
    # 3. Check Method & Ingress/Egress (25 pts)
    # Filter submitted method items to those actually discovered in session.
    discovered_methods = set(request.method_evidence_ids).intersection(session.discovered_evidence_ids)
    has_bypass = "E-01" in discovered_methods
    has_hatch = "E-10" in discovered_methods
    has_timing_or_trace = ("E-02" in discovered_methods or "E-07" in discovered_methods)
    
    if is_culprit_correct and has_bypass and has_hatch and has_timing_or_trace:
        method_pts = 25  # Full method score
    elif is_culprit_correct and (has_bypass or has_hatch):
        method_pts = 10  # Partial method credit
    else:
        method_pts = 0
        
    # 4. Check Artifact Recovery (25 pts)
    # Must provide E-11 and have verified it was discovered in session.
    is_recovery_correct = (
        request.recovery_evidence_id == "E-11" and 
        "E-11" in session.discovered_evidence_ids
    )
    recovery_pts = 25 if (is_culprit_correct and is_recovery_correct) else 0
    
    # 5. Compute Penalties (-15 pts per failed attempt, min 0 score)
    # For a successful accusation on attempt N, penalty = (N - 1) * 15.
    raw_score = culprit_pts + motive_pts + method_pts + recovery_pts
    penalty = (session.accusation_attempts - 1) * 15 if is_culprit_correct else session.accusation_attempts * 15
    final_score = max(0, raw_score - penalty)
    
    # 6. Determine Outcome State
    is_solved = (is_culprit_correct and final_score >= 50)
    
    if is_solved:
        session.case_status = "SOLVED"
        verdict = "CONVICTED"
    elif session.accusation_attempts >= 3:
        session.case_status = "CLOSED"
        verdict = "CASE_DISMISSED"
    else:
        verdict = "INDICTMENT_REJECTED"
        
    return {
        "is_solved": is_solved,
        "case_status": session.case_status,
        "verdict": verdict,
        "attempts_used": session.accusation_attempts,
        "attempts_remaining": max(0, 3 - session.accusation_attempts),
        "score_breakdown": {
            "culprit_score": culprit_pts,
            "motive_score": motive_pts,
            "method_score": method_pts,
            "recovery_score": recovery_pts,
            "attempt_penalty": penalty,
            "final_score": final_score
        }
    }
```

---

## 6. Frontend Mock Fixtures (Vishal's Quickstart)

To allow Vishal to develop the React + TypeScript frontend without waiting for the FastAPI backend, the following static fixture objects should be used in the client mock service:

### 6.1 Mock Initial State
```typescript
export const MOCK_SESSION_INIT: SessionStateResponse = {
  session_id: "mock-session-001",
  created_at: "2026-10-12T12:00:00Z",
  case_status: "ACTIVE",
  accusation_attempts: 0,
  max_accusation_attempts: 3,
  current_penalty: 0,
  discovered_evidence_ids: ["E-01"],
  interrogated_suspect_ids: ["elias_voss"],
  truth_ledger: {
    facts: [
      {
        fact_id: "FACT_E01_SHUNT",
        evidence_id: "E-01",
        title: "Severed Vitrine Sensor Shunt",
        summary: "Custom nitrogen bypass shunt found on pedestal base. Proves specialized bypass.",
        discovered_at: "2026-10-12T12:05:00Z",
        category: "FORENSIC"
      }
    ],
    contradictions: [],
    theories: {
      suspected_culprit_id: null,
      motive_hypothesis: "",
      method_hypothesis: "",
      recovery_hypothesis: "",
      updated_at: "2026-10-12T12:00:00Z"
    }
  },
  recent_events: [
    {
      event_type: "EXAMINE",
      target_id: "heliodor_pedestal",
      timestamp: "2026-10-12T12:05:00Z",
      summary: "Examined vitrine pedestal and recovered E-01."
    }
  ]
};
```

---

## 7. Environment, CORS & Security Requirements

### 7.1 Local Development Environment Variables (`.env`)
The backend relies on the following environment configuration. All variables have safe local defaults and require no external cloud services to run with fallback dialogue:

```env
# Server Port & Binding
PORT=8000
HOST=127.0.0.1

# Environment Mode
ENVIRONMENT=development
LOG_LEVEL=info

# Allowed Frontend Origins (CORS)
CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]

# Dialogue Model Settings (Backend Only - NEVER expose to client)
LLM_PROVIDER="none"                     # Options: "none" (fallback only), "mock", or provider key
LLM_API_KEY=""                          # Confidential provider key
LLM_MODEL_ID="gemma-2-9b"               # Configurable model ID string
LLM_TIMEOUT_SECONDS=5.0

# Rate Limiting
RATE_LIMIT_INTERROGATIONS_PER_MINUTE=30
```

### 7.2 CORS Configuration (FastAPI)
The FastAPI application registers `CORSMiddleware` with explicit support for Vite's default development server ports:
* Allowed Origins: `http://localhost:5173`, `http://127.0.0.1:5173`
* Allowed Methods: `GET`, `POST`, `OPTIONS`
* Allowed Headers: `Content-Type`, `Authorization`

### 7.3 Security & API Key Confidentiality
* `LLM_API_KEY` must remain strictly server-side.
* No endpoint (`GET /api/config`, `GET /api/health`, etc.) serializes or echoes credentials.
* Rate limiting on `POST /interrogate` drops rejected requests before touching session state or contacting external providers.

---

## 8. Summary of Review Findings & Approved Architectural Decisions

1. **Examination Target Mapping:** Confirmed all 12 targets map directly to evidence items `E-01` through `E-12`. Repeated examination is strictly idempotent (`already_discovered: true`, no duplicate facts, no score alteration).
2. **Method Quorum Harmonization:** The method scoring algorithm now checks that `E-01` (bypass tool) and `E-10` (tapestry hatch) are present alongside at least one supporting timing/trace item (`E-02` or `E-07`), matching both Path A (digital) and Path B (forensic) from `docs/case-spec.md`. Partial credit (10 pts) is awarded if at least one core mechanical element is submitted.
3. **HTTP 429 Rate Limiting:** Formally specified HTTP 429 response structure, `RATE_LIMIT_EXCEEDED` code, and `Retry-After: 2` header, ensuring dropped requests never mutate session state.
4. **Input Validation Matrix:** Standardized validation for empty questions (`EMPTY_QUESTION`), oversized strings (`QUESTION_TOO_LONG`), malformed UUIDs (`INVALID_SESSION_ID`), and closed sessions (`SESSION_CLOSED`).
5. **Standardized Model Status:** Dialogue responses strictly return `model_status: "success" | "fallback" | "unavailable"` and `is_fallback: boolean`.
6. **Spoiler Shield:** Verified that no ordinary endpoint leaks the culprit or solution key. Solution reveal occurs exclusively upon case conviction or case dismissal (after 3 failed attempts).

---
*End of API Contract — The Last Exhibition (v1.1.0)*
