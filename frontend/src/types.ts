/**
 * Prompt Dungeon — TypeScript API Types & Domain Contracts
 * Canonical Source: docs/api-contract.md v1.1.0 & backend/models.py
 */

export type SuspectId = 'elias_voss' | 'mira_sen' | 'noah_reed' | 'celeste_ward';

export type EvidenceId =
  | 'E-01'
  | 'E-02'
  | 'E-03'
  | 'E-04'
  | 'E-05'
  | 'E-06'
  | 'E-07'
  | 'E-08'
  | 'E-09'
  | 'E-10'
  | 'E-11'
  | 'E-12';

export type TargetId =
  | 'heliodor_pedestal'
  | 'vitrine_latch'
  | 'gallery_tapestry'
  | 'server_rack_02'
  | 'security_access_db'
  | 'curator_shredder'
  | 'curator_desk'
  | 'west_archive_floor'
  | 'workshop_cabinet_03'
  | 'basement_hazmat_04'
  | 'terrace_catering_bar'
  | 'technician_locker';

export type CaseStatus = 'ACTIVE' | 'SOLVED' | 'CLOSED' | 'RESET';
export type Verdict = 'CONVICTED' | 'INDICTMENT_REJECTED' | 'CASE_DISMISSED';
export type ModelDialogueStatus = 'success' | 'fallback' | 'unavailable';

export interface SuspectPublic {
  suspect_id: SuspectId;
  name: string;
  role: string;
  avatar: string;
  bio: string;
  public_statement: string;
}

export interface ExaminationTargetPublic {
  target_id: TargetId;
  name: string;
  zone: string;
}

export interface CaseMeta {
  case_id: string;
  case_title: string;
  incident_time: string;
  facility: string;
}

export interface GameRules {
  max_accusation_attempts: number;
  penalty_per_failed_accusation: number;
  history_window_turns: number;
  rate_limit_interrogations_per_minute: number;
}

export interface ConfigResponse {
  case_meta: CaseMeta;
  suspects: SuspectPublic[];
  locations: ExaminationTargetPublic[];
  rules: GameRules;
}

export interface DiscoveredFact {
  fact_id: string;
  evidence_id: EvidenceId;
  title: string;
  summary: string;
  discovered_at: string;
  category: string;
}

export interface ValidatedContradiction {
  rule_id: string;
  suspect_id: SuspectId;
  disputed_claim: string;
  refuting_evidence_id: EvidenceId;
  validation_state: string;
  validated_at: string;
}

export interface PlayerTheories {
  suspected_culprit_id?: SuspectId | null;
  motive_hypothesis?: string;
  method_hypothesis?: string;
  recovery_hypothesis?: string;
  updated_at: string;
}

export interface TruthLedger {
  facts: DiscoveredFact[];
  contradictions: ValidatedContradiction[];
  theories: PlayerTheories;
}

export interface SessionEventLog {
  event_type: string;
  target_id: string;
  timestamp: string;
  summary: string;
}

export interface SessionStateResponse {
  session_id: string;
  created_at: string;
  case_status: CaseStatus;
  accusation_attempts: number;
  max_accusation_attempts: number;
  current_penalty: number;
  discovered_evidence_ids: EvidenceId[];
  interrogated_suspect_ids: SuspectId[];
  truth_ledger: TruthLedger;
  recent_events: SessionEventLog[];
}

export interface EvidenceCatalogItem {
  evidence_id: EvidenceId;
  title: string;
  description: string;
  category: string;
  is_mandatory: boolean;
  already_discovered: boolean;
}

export interface ExamineResponse {
  target_id: TargetId;
  inspection_narrative: string;
  uncovered_evidence?: EvidenceCatalogItem | null;
  truth_ledger_updated: boolean;
  new_fact?: DiscoveredFact | null;
}

export interface InterrogateResponse {
  suspect_id: SuspectId;
  question: string;
  reply: string;
  recorded_statement_id?: string | null;
  is_fallback: boolean;
  model_status: ModelDialogueStatus;
  fallback_reason?: string | null;
  dialogue_turn_index: number;
  timestamp: string;
}

export interface PresentEvidenceResponse {
  suspect_id: SuspectId;
  evidence_id: EvidenceId;
  contradiction_validated: boolean;
  contradiction?: ValidatedContradiction | null;
  suspect_reaction: string;
  is_fallback: boolean;
  model_status: ModelDialogueStatus;
}

export interface UpdateTheoriesResponse {
  updated_theories: PlayerTheories;
  message: string;
}

export interface ScoreBreakdown {
  culprit_score: number;
  motive_score: number;
  method_score: number;
  recovery_score: number;
  attempt_penalty: number;
  final_score: number;
}

export interface CanonicalSolutionReveal {
  culprit: string;
  motive: string;
  method: string;
  recovery_location: string;
}

export interface AccuseResponse {
  is_solved: boolean;
  case_status: CaseStatus;
  verdict: Verdict;
  attempts_used: number;
  attempts_remaining: number;
  score_breakdown: ScoreBreakdown;
  rank?: string | null;
  narrative_debrief: string;
  canonical_solution_reveal?: CanonicalSolutionReveal | null;
}

export interface ResetSessionResponse {
  previous_session_id: string;
  new_session_id: string;
  created_at: string;
  message: string;
  new_session_state: SessionStateResponse;
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
  retryable: boolean;
}

export interface ApiErrorResponse {
  error: ApiError;
}
