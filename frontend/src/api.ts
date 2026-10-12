/**
 * Prompt Dungeon — Centralized Typed API Client
 * Canonical Reference: docs/api-contract.md v1.1.0
 */

import type {
  AccuseResponse,
  ApiErrorResponse,
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

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

export class ApiClientError extends Error {
  code: string;
  details?: Record<string, unknown> | null;
  retryable: boolean;
  status: number;

  constructor(status: number, errorData: ApiErrorResponse['error']) {
    super(errorData.message || 'API request failed');
    this.name = 'ApiClientError';
    this.status = status;
    this.code = errorData.code || 'UNKNOWN_ERROR';
    this.details = errorData.details;
    this.retryable = !!errorData.retryable;
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${path}`;
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 25_000);
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, { ...options, headers, signal: controller.signal });
    if (!res.ok) {
      let errPayload: ApiErrorResponse['error'];
      try {
        const body: ApiErrorResponse = await res.json();
        errPayload = body.error || {
          code: `HTTP_${res.status}`,
          message: res.statusText || 'Unknown server error',
          retryable: false,
        };
      } catch {
        errPayload = {
          code: `HTTP_${res.status}`,
          message: res.statusText || 'Non-JSON server error',
          retryable: false,
        };
      }
      throw new ApiClientError(res.status, errPayload);
    }
    return (await res.json()) as T;
  } catch (err) {
    if (err instanceof ApiClientError) {
      throw err;
    }
    if (err instanceof DOMException && err.name === 'AbortError') {
      throw new ApiClientError(0, {
        code: 'REQUEST_TIMEOUT',
        message: 'The server did not respond in time. Refresh server state before repeating an action.',
        retryable: true,
      });
    }
    if (err instanceof SyntaxError) {
      throw new ApiClientError(0, {
        code: 'INVALID_RESPONSE',
        message: 'The server returned an unreadable response. Refresh server state before repeating an action.',
        retryable: true,
      });
    }
    throw new ApiClientError(0, {
      code: 'NETWORK_ERROR',
      message: err instanceof Error ? err.message : 'Network request failed. Is the server running?',
      retryable: true,
    });
  } finally {
    window.clearTimeout(timeout);
  }
}

export const api = {
  getHealth: () => request<{ status: string; version: string; timestamp: string }>('/api/health'),

  getConfig: () => request<ConfigResponse>('/api/config'),

  createSession: (playerName?: string) =>
    request<SessionStateResponse>('/api/sessions', {
      method: 'POST',
      body: JSON.stringify({ player_name: playerName || 'Detective' }),
    }),

  getSession: (sessionId: string) =>
    request<SessionStateResponse>(`/api/sessions/${sessionId}`),

  resetSession: (sessionId: string) =>
    request<ResetSessionResponse>(`/api/sessions/${sessionId}/reset`, {
      method: 'POST',
    }),

  examineTarget: (sessionId: string, targetId: TargetId) =>
    request<ExamineResponse>(`/api/sessions/${sessionId}/examine`, {
      method: 'POST',
      body: JSON.stringify({ target_id: targetId }),
    }),

  interrogate: (sessionId: string, suspectId: SuspectId, question: string) =>
    request<InterrogateResponse>(`/api/sessions/${sessionId}/interrogate`, {
      method: 'POST',
      body: JSON.stringify({ suspect_id: suspectId, question }),
    }),

  presentEvidence: (sessionId: string, suspectId: SuspectId, evidenceId: EvidenceId) =>
    request<PresentEvidenceResponse>(`/api/sessions/${sessionId}/present-evidence`, {
      method: 'POST',
      body: JSON.stringify({ suspect_id: suspectId, evidence_id: evidenceId }),
    }),

  updateTheories: (
    sessionId: string,
    theories: {
      suspected_culprit_id?: SuspectId | null;
      motive_hypothesis?: string;
      method_hypothesis?: string;
      recovery_hypothesis?: string;
    }
  ) =>
    request<UpdateTheoriesResponse>(`/api/sessions/${sessionId}/theories`, {
      method: 'POST',
      body: JSON.stringify(theories),
    }),

  accuse: (
    sessionId: string,
    payload: {
      accused_suspect_id: SuspectId;
      motive_evidence_id: EvidenceId;
      method_evidence_ids: EvidenceId[];
      recovery_evidence_id: EvidenceId;
      detective_statement: string;
    }
  ) =>
    request<AccuseResponse>(`/api/sessions/${sessionId}/accuse`, {
      method: 'POST',
      body: JSON.stringify(payload),
    }),
};
