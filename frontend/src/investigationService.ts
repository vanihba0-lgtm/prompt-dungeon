import { api } from './api';
import type {
  AccuseResponse,
  ConfigResponse,
  EvidenceId,
  ExamineResponse,
  InterrogateResponse,
  PresentEvidenceResponse,
  ResetSessionResponse,
  SessionStateResponse,
  SuspectId,
  TargetId,
  UpdateTheoriesResponse,
} from './types';

/** UI-facing service contract. It describes this frontend's needs, not a new backend contract. */
export interface InvestigationService {
  getConfig(): Promise<ConfigResponse>;
  createSession(playerName?: string): Promise<SessionStateResponse>;
  getSession(sessionId: string): Promise<SessionStateResponse>;
  resetSession(sessionId: string): Promise<ResetSessionResponse>;
  examineTarget(sessionId: string, targetId: TargetId): Promise<ExamineResponse>;
  interrogate(sessionId: string, suspectId: SuspectId, question: string): Promise<InterrogateResponse>;
  presentEvidence(sessionId: string, suspectId: SuspectId, evidenceId: EvidenceId): Promise<PresentEvidenceResponse>;
  updateTheories(
    sessionId: string,
    theories: {
      suspected_culprit_id?: SuspectId | null;
      motive_hypothesis?: string;
      method_hypothesis?: string;
      recovery_hypothesis?: string;
    },
  ): Promise<UpdateTheoriesResponse>;
  accuse(
    sessionId: string,
    payload: {
      accused_suspect_id: SuspectId;
      motive_evidence_id: EvidenceId;
      method_evidence_ids: EvidenceId[];
      recovery_evidence_id: EvidenceId;
      detective_statement: string;
    },
  ): Promise<AccuseResponse>;
}

/** Live adapter over the existing typed HTTP client. There is no implicit mock fallback. */
export const investigationService: InvestigationService = api;
