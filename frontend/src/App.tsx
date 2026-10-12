import React, { useEffect, useState } from 'react';
import './App.css';
import { api, ApiClientError } from './api';
import type {
  AccuseResponse,
  ConfigResponse,
  EvidenceId,
  ExamineResponse,
  InterrogateResponse,
  PresentEvidenceResponse,
  SessionStateResponse,
  SuspectId,
  TargetId,
} from './types';

type ActiveTab = 'suspects' | 'locations' | 'theories' | 'accuse';

interface ChatMessage {
  sender: 'player' | 'suspect';
  text: string;
  timestamp: string;
  statementId?: string | null;
  isFallback?: boolean;
  modelStatus?: string;
}

export default function App() {
  const [config, setConfig] = useState<ConfigResponse | null>(null);
  const [session, setSession] = useState<SessionStateResponse | null>(null);
  const [activeTab, setActiveTab] = useState<ActiveTab>('suspects');
  const [selectedSuspect, setSelectedSuspect] = useState<SuspectId>('elias_voss');

  // Interrogation Chat State
  const [questionText, setQuestionText] = useState('');
  const [chatHistories, setChatHistories] = useState<Record<SuspectId, ChatMessage[]>>({
    elias_voss: [],
    mira_sen: [],
    noah_reed: [],
    celeste_ward: [],
  });

  // UI status states
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Examination feedback
  const [lastExamResult, setLastExamResult] = useState<ExamineResponse | null>(null);

  // Evidence Presentation
  const [selectedEvidenceToPresent, setSelectedEvidenceToPresent] = useState<EvidenceId | ''>('');
  const [presentationResult, setPresentationResult] = useState<PresentEvidenceResponse | null>(null);

  // Theories State
  const [theories, setTheories] = useState({
    suspected_culprit_id: '' as SuspectId | '',
    motive_hypothesis: '',
    method_hypothesis: '',
    recovery_hypothesis: '',
  });

  // Accusation State
  const [accusePayload, setAccusePayload] = useState({
    accused_suspect_id: 'elias_voss' as SuspectId,
    motive_evidence_id: '' as EvidenceId | '',
    method_evidence_ids: [] as EvidenceId[],
    recovery_evidence_id: '' as EvidenceId | '',
    detective_statement: '',
  });
  const [accuseResult, setAccuseResult] = useState<AccuseResponse | null>(null);

  // Load config & active session on mount
  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const cfg = await api.getConfig();
        setConfig(cfg);

        // Check localStorage for existing session ID
        const savedSid = localStorage.getItem('prompt_dungeon_sid');
        if (savedSid) {
          try {
            const sess = await api.getSession(savedSid);
            setSession(sess);
            syncTheoriesFromSession(sess);
            return;
          } catch {
            localStorage.removeItem('prompt_dungeon_sid');
          }
        }

        // Otherwise create fresh session
        const fresh = await api.createSession('Lead Detective');
        setSession(fresh);
        localStorage.setItem('prompt_dungeon_sid', fresh.session_id);
        syncTheoriesFromSession(fresh);
      } catch (err) {
        handleError(err);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, []);

  function syncTheoriesFromSession(sess: SessionStateResponse) {
    if (sess.truth_ledger?.theories) {
      setTheories({
        suspected_culprit_id: sess.truth_ledger.theories.suspected_culprit_id || '',
        motive_hypothesis: sess.truth_ledger.theories.motive_hypothesis || '',
        method_hypothesis: sess.truth_ledger.theories.method_hypothesis || '',
        recovery_hypothesis: sess.truth_ledger.theories.recovery_hypothesis || '',
      });
    }
  }

  function handleError(err: unknown) {
    if (err instanceof ApiClientError) {
      setErrorMsg(`[${err.code}] ${err.message}`);
    } else if (err instanceof Error) {
      setErrorMsg(err.message);
    } else {
      setErrorMsg('An unexpected error occurred.');
    }
  }

  function clearAlerts() {
    setErrorMsg(null);
    setSuccessMsg(null);
  }

  // Handle Session Reset
  async function handleResetSession() {
    if (!session) return;
    if (!window.confirm('Reset investigation? All progress will start fresh.')) return;
    try {
      clearAlerts();
      setLoading(true);
      const res = await api.resetSession(session.session_id);
      setSession(res.new_session_state);
      localStorage.setItem('prompt_dungeon_sid', res.new_session_id);
      syncTheoriesFromSession(res.new_session_state);
      setChatHistories({
        elias_voss: [],
        mira_sen: [],
        noah_reed: [],
        celeste_ward: [],
      });
      setLastExamResult(null);
      setPresentationResult(null);
      setAccuseResult(null);
      setSuccessMsg('Investigation has been reset. Fresh session started.');
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }

  // Handle Target Examination
  async function handleExamine(targetId: TargetId) {
    if (!session) return;
    try {
      clearAlerts();
      setLoading(true);
      const res = await api.examineTarget(session.session_id, targetId);
      setLastExamResult(res);

      // Refresh session state
      const updatedSess = await api.getSession(session.session_id);
      setSession(updatedSess);

      if (res.truth_ledger_updated && res.new_fact) {
        setSuccessMsg(`Discovered new evidence: ${res.new_fact.title} (${res.new_fact.evidence_id})!`);
      } else {
        setSuccessMsg(`Inspected target: Already documented in evidence log.`);
      }
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }

  // Handle Question Submission
  async function handleInterrogate(e: React.FormEvent) {
    e.preventDefault();
    if (!session || !questionText.trim()) return;
    const q = questionText.trim();
    setQuestionText('');
    clearAlerts();

    // Optimistic player message
    const playerMsg: ChatMessage = {
      sender: 'player',
      text: q,
      timestamp: new Date().toLocaleTimeString(),
    };
    setChatHistories((prev) => ({
      ...prev,
      [selectedSuspect]: [...prev[selectedSuspect], playerMsg],
    }));

    try {
      setLoading(true);
      const res: InterrogateResponse = await api.interrogate(session.session_id, selectedSuspect, q);

      const suspectMsg: ChatMessage = {
        sender: 'suspect',
        text: res.reply,
        timestamp: new Date(res.timestamp).toLocaleTimeString(),
        statementId: res.recorded_statement_id,
        isFallback: res.is_fallback,
        modelStatus: res.model_status,
      };

      setChatHistories((prev) => ({
        ...prev,
        [selectedSuspect]: [...prev[selectedSuspect], suspectMsg],
      }));

      // Refresh session state to sync turn counts and interrogated IDs
      const updated = await api.getSession(session.session_id);
      setSession(updated);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }

  // Handle Evidence Presentation
  async function handlePresentEvidence() {
    if (!session || !selectedEvidenceToPresent) return;
    try {
      clearAlerts();
      setLoading(true);
      const res = await api.presentEvidence(
        session.session_id,
        selectedSuspect,
        selectedEvidenceToPresent
      );
      setPresentationResult(res);

      // Refresh session state to sync truth ledger contradictions
      const updated = await api.getSession(session.session_id);
      setSession(updated);

      if (res.contradiction_validated) {
        setSuccessMsg(
          `CONTRADICTION EXPOSED! Rule ${res.contradiction?.rule_id}: ${res.contradiction?.validation_state}`
        );
      } else {
        setSuccessMsg(`Suspect deflected: The evidence did not establish a direct contradiction.`);
      }
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }

  // Handle Theory Update
  async function handleUpdateTheories(e: React.FormEvent) {
    e.preventDefault();
    if (!session) return;
    try {
      clearAlerts();
      setLoading(true);
      const res = await api.updateTheories(session.session_id, {
        suspected_culprit_id: theories.suspected_culprit_id || null,
        motive_hypothesis: theories.motive_hypothesis,
        method_hypothesis: theories.method_hypothesis,
        recovery_hypothesis: theories.recovery_hypothesis,
      });
      setSuccessMsg(res.message);
      const updated = await api.getSession(session.session_id);
      setSession(updated);
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }

  // Handle Formal Accusation
  async function handleAccuse(e: React.FormEvent) {
    e.preventDefault();
    if (!session) return;
    if (
      !accusePayload.motive_evidence_id ||
      accusePayload.method_evidence_ids.length < 2 ||
      !accusePayload.recovery_evidence_id ||
      !accusePayload.detective_statement.trim()
    ) {
      setErrorMsg('Please select motive, at least 2 method items, recovery evidence, and write a statement.');
      return;
    }

    try {
      clearAlerts();
      setLoading(true);
      const res = await api.accuse(session.session_id, {
        accused_suspect_id: accusePayload.accused_suspect_id,
        motive_evidence_id: accusePayload.motive_evidence_id as EvidenceId,
        method_evidence_ids: accusePayload.method_evidence_ids,
        recovery_evidence_id: accusePayload.recovery_evidence_id as EvidenceId,
        detective_statement: accusePayload.detective_statement.trim(),
      });
      setAccuseResult(res);

      const updated = await api.getSession(session.session_id);
      setSession(updated);

      if (res.is_solved) {
        setSuccessMsg(`CASE SOLVED! Verdict: ${res.verdict} | Rank: ${res.rank}`);
      } else {
        setErrorMsg(`Accusation Rejected: Verdict: ${res.verdict} | Penalty: -${res.score_breakdown.attempt_penalty} pts`);
      }
    } catch (err) {
      handleError(err);
    } finally {
      setLoading(false);
    }
  }

  const currentSuspectObj = config?.suspects.find((s) => s.suspect_id === selectedSuspect);

  return (
    <div className="app-container">
      {/* Top Header */}
      <header className="app-header">
        <div className="brand-section">
          <span className="brand-icon">🏛️</span>
          <div>
            <h1 className="brand-title">PROMPT DUNGEON</h1>
            <p className="brand-subtitle">
              The Last Exhibition — Heliodor Gallery Theft Investigation (2026)
            </p>
          </div>
        </div>

        <div className="header-status-panel">
          {session && (
            <>
              <div
                className={`badge ${
                  session.case_status === 'SOLVED'
                    ? 'badge-solved'
                    : session.case_status === 'CLOSED'
                    ? 'badge-closed'
                    : 'badge-active'
                }`}
              >
                ● {session.case_status}
              </div>

              <div className="header-stat">
                <span>ATTEMPTS</span>
                <span className="header-stat-val">
                  {session.accusation_attempts} / {session.max_accusation_attempts}
                </span>
              </div>

              <div className="header-stat">
                <span>EVIDENCE</span>
                <span className="header-stat-val">
                  {session.discovered_evidence_ids.length} / 12
                </span>
              </div>

              <button className="btn-reset" onClick={handleResetSession} disabled={loading}>
                🔄 Reset Case
              </button>
            </>
          )}
        </div>
      </header>

      {/* Case Overview Intro Banner */}
      <section className="case-banner">
        <div className="case-banner-text">
          <h2>THE OBSIDIAN SUN HAS DISAPPEARED</h2>
          <p>
            At 9:17 PM during a 4-minute camera blackout, the 14th-century Aztec relic vanished from its
            pressurized vitrine. No glass broken, no alarms tripped. Four suspects had proximity.
            Uncover physical proof, break their lies, and submit an indictment to the Magistrate.
          </p>
        </div>
      </section>

      {/* Global Alerts */}
      {errorMsg && (
        <div className="alert alert-error fade-in">
          <span>⚠️</span> <span>{errorMsg}</span>
        </div>
      )}
      {successMsg && (
        <div className="alert alert-success fade-in">
          <span>✨</span> <span>{successMsg}</span>
        </div>
      )}

      {/* Navigation Tabs */}
      <nav className="nav-tabs">
        <button
          className={`tab-btn ${activeTab === 'suspects' ? 'active' : ''}`}
          onClick={() => setActiveTab('suspects')}
        >
          🕵️ Suspects & Interrogation
        </button>
        <button
          className={`tab-btn ${activeTab === 'locations' ? 'active' : ''}`}
          onClick={() => setActiveTab('locations')}
        >
          🔍 Crime Scene & Locations ({session?.discovered_evidence_ids.length || 0}/12)
        </button>
        <button
          className={`tab-btn ${activeTab === 'theories' ? 'active' : ''}`}
          onClick={() => setActiveTab('theories')}
        >
          📋 Deduction Workbench
        </button>
        <button
          className={`tab-btn ${activeTab === 'accuse' ? 'active' : ''}`}
          onClick={() => setActiveTab('accuse')}
        >
          ⚖️ Formal Indictment
        </button>
      </nav>

      {/* Main Two-Column View */}
      <div className="main-view">
        {/* Left Primary Screen */}
        <div className="primary-content">
          {/* TAB 1: SUSPECTS & INTERROGATION */}
          {activeTab === 'suspects' && (
            <>
              <div className="suspects-grid">
                {config?.suspects.map((s) => {
                  const isInterrogated = session?.interrogated_suspect_ids.includes(s.suspect_id);
                  return (
                    <div
                      key={s.suspect_id}
                      className={`suspect-card ${selectedSuspect === s.suspect_id ? 'selected' : ''}`}
                      onClick={() => setSelectedSuspect(s.suspect_id)}
                    >
                      <div className="suspect-header">
                        <div className="suspect-avatar">
                          {s.suspect_id === 'elias_voss' ? '🔬' : s.suspect_id === 'mira_sen' ? '📜' : s.suspect_id === 'noah_reed' ? '💻' : '💎'}
                        </div>
                        <div>
                          <div className="suspect-name">{s.name}</div>
                          <div className="suspect-role">{s.role}</div>
                        </div>
                      </div>
                      <p className="suspect-quote">"{s.public_statement}"</p>
                      {isInterrogated && (
                        <div style={{ fontSize: '11px', color: 'var(--accent-emerald)', marginTop: '4px' }}>
                          ✓ Questioned
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>

              {/* Chat & Confrontation Panel */}
              <div className="card">
                <div className="card-title">
                  <span>INTERROGATING: {currentSuspectObj?.name?.toUpperCase()}</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                    {chatHistories[selectedSuspect].length} turn(s) recorded
                  </span>
                </div>

                {/* Evidence Confrontation Bar */}
                <div style={{ display: 'flex', gap: '10px', marginBottom: '14px', alignItems: 'center' }}>
                  <select
                    style={{ flex: 1 }}
                    value={selectedEvidenceToPresent}
                    onChange={(e) => setSelectedEvidenceToPresent(e.target.value as EvidenceId)}
                  >
                    <option value="">-- Present discovered evidence to confront suspect --</option>
                    {session?.discovered_evidence_ids.map((eid) => {
                      const fact = session.truth_ledger.facts.find((f) => f.evidence_id === eid);
                      return (
                        <option key={eid} value={eid}>
                          {eid}: {fact?.title || 'Discovered Item'}
                        </option>
                      );
                    })}
                  </select>
                  <button
                    className="btn-primary"
                    disabled={!selectedEvidenceToPresent || loading}
                    onClick={handlePresentEvidence}
                  >
                    Confront with Evidence
                  </button>
                </div>

                {presentationResult && (
                  <div
                    style={{
                      padding: '12px',
                      borderRadius: '8px',
                      marginBottom: '12px',
                      background: presentationResult.contradiction_validated
                        ? 'rgba(16, 185, 129, 0.15)'
                        : 'rgba(255, 255, 255, 0.04)',
                      border: '1px solid var(--border-subtle)',
                      fontSize: '13px',
                    }}
                  >
                    <div style={{ fontWeight: 700, marginBottom: '4px', color: 'var(--accent-gold)' }}>
                      SUSPECT REACTION:
                    </div>
                    <div>"{presentationResult.suspect_reaction}"</div>
                  </div>
                )}

                {/* Chat Log */}
                <div className="chat-window">
                  <div className="chat-history">
                    {chatHistories[selectedSuspect].length === 0 ? (
                      <div style={{ color: 'var(--text-faint)', textAlign: 'center', marginTop: '40px' }}>
                        No questions asked to {currentSuspectObj?.name} yet. Type a question below.
                      </div>
                    ) : (
                      chatHistories[selectedSuspect].map((msg, i) => (
                        <div key={i} className={`chat-msg ${msg.sender} fade-in`}>
                          <div>{msg.text}</div>
                          <div className="chat-meta">
                            <span>{msg.timestamp}</span>
                            {msg.statementId && (
                              <span style={{ color: 'var(--accent-crimson)', fontWeight: 600 }}>
                                ⚠️ Lie Uttered: {msg.statementId}
                              </span>
                            )}
                            {msg.isFallback && (
                              <span style={{ color: 'var(--text-faint)' }}>• {msg.modelStatus}</span>
                            )}
                          </div>
                        </div>
                      ))
                    )}
                  </div>

                  <form className="chat-input-bar" onSubmit={handleInterrogate}>
                    <input
                      type="text"
                      placeholder={`Ask ${currentSuspectObj?.name} about whereabouts, tools, finances... (max 500 chars)`}
                      value={questionText}
                      maxLength={500}
                      onChange={(e) => setQuestionText(e.target.value)}
                      disabled={loading || session?.case_status === 'CLOSED'}
                    />
                    <button
                      type="submit"
                      className="btn-primary"
                      disabled={!questionText.trim() || loading || session?.case_status === 'CLOSED'}
                    >
                      Question
                    </button>
                  </form>
                </div>
              </div>
            </>
          )}

          {/* TAB 2: LOCATIONS & PHYSICAL EXAMINATION */}
          {activeTab === 'locations' && (
            <div className="card">
              <div className="card-title">
                <span>FACILITY EXAMINATION DIRECTORY</span>
                <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  12 Forensic Targets
                </span>
              </div>

              {lastExamResult && (
                <div
                  style={{
                    padding: '16px',
                    borderRadius: '10px',
                    background: 'rgba(229, 184, 92, 0.1)',
                    border: '1px solid var(--border-gold)',
                    marginBottom: '16px',
                  }}
                >
                  <div style={{ fontWeight: 700, color: 'var(--accent-gold-bright)', marginBottom: '4px' }}>
                    FORENSIC INSPECTION REPORT:
                  </div>
                  <p style={{ fontSize: '14px', marginBottom: '8px' }}>
                    {lastExamResult.inspection_narrative}
                  </p>
                  {lastExamResult.uncovered_evidence && (
                    <div style={{ fontSize: '13px', color: 'var(--text-main)' }}>
                      <strong>Evidence Logged:</strong> [{lastExamResult.uncovered_evidence.evidence_id}] —{' '}
                      {lastExamResult.uncovered_evidence.title} ({lastExamResult.uncovered_evidence.category})
                    </div>
                  )}
                </div>
              )}

              <div className="targets-grid">
                {config?.locations.map((loc) => {
                  const isExamined = session?.recent_events.some(
                    (e) => e.event_type === 'EXAMINE' && e.target_id === loc.target_id
                  );
                  return (
                    <div key={loc.target_id} className="target-card">
                      <div>
                        <div className="target-zone">{loc.zone}</div>
                        <div className="target-name">{loc.name}</div>
                      </div>
                      <button
                        className="btn-primary"
                        onClick={() => handleExamine(loc.target_id)}
                        disabled={loading || session?.case_status === 'CLOSED'}
                      >
                        {isExamined ? 'Inspect Again' : 'Search & Examine'}
                      </button>
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* TAB 3: THEORIES WORKBENCH */}
          {activeTab === 'theories' && (
            <div className="card">
              <div className="card-title">
                <span>PLAYER DEDUCTION WORKBENCH</span>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  Truth Ledger Hypotheses
                </span>
              </div>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '16px' }}>
                Organize your thoughts and hypotheses before filing a formal indictment. Updating
                theories does not alter score or consume accusation attempts.
              </p>

              <form className="accuse-form" onSubmit={handleUpdateTheories}>
                <div className="form-group">
                  <label className="form-label">SUSPECTED PRIME CULPRIT</label>
                  <select
                    value={theories.suspected_culprit_id}
                    onChange={(e) =>
                      setTheories({ ...theories, suspected_culprit_id: e.target.value as SuspectId })
                    }
                  >
                    <option value="">-- Unassigned --</option>
                    {config?.suspects.map((s) => (
                      <option key={s.suspect_id} value={s.suspect_id}>
                        {s.name} ({s.role})
                      </option>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">MOTIVE HYPOTHESIS</label>
                  <textarea
                    rows={2}
                    placeholder="Why did they steal the relic? Extortion, academic scandal, greed?"
                    value={theories.motive_hypothesis}
                    onChange={(e) => setTheories({ ...theories, motive_hypothesis: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">METHOD & BYPASS HYPOTHESIS</label>
                  <textarea
                    rows={2}
                    placeholder="How did they open the vitrine and enter/exit the locked gallery?"
                    value={theories.method_hypothesis}
                    onChange={(e) => setTheories({ ...theories, method_hypothesis: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">ARTIFACT RECOVERY HYPOTHESIS</label>
                  <textarea
                    rows={2}
                    placeholder="Where is the Obsidian Sun hidden right now?"
                    value={theories.recovery_hypothesis}
                    onChange={(e) => setTheories({ ...theories, recovery_hypothesis: e.target.value })}
                  />
                </div>

                <button type="submit" className="btn-primary" disabled={loading}>
                  Save Hypotheses to Ledger
                </button>
              </form>
            </div>
          )}

          {/* TAB 4: ACCUSATION & SCORING */}
          {activeTab === 'accuse' && (
            <div className="card">
              <div className="card-title">
                <span>SUBMIT FORMAL INDICTMENT TO DISTRICT MAGISTRATE</span>
                <span style={{ fontSize: '12px', color: 'var(--accent-crimson)' }}>
                  {3 - (session?.accusation_attempts || 0)} attempts remaining
                </span>
              </div>

              {accuseResult && (
                <div
                  style={{
                    padding: '20px',
                    borderRadius: '12px',
                    marginBottom: '20px',
                    background: accuseResult.is_solved
                      ? 'rgba(16, 185, 129, 0.15)'
                      : 'rgba(225, 29, 72, 0.15)',
                    border: `1px solid ${accuseResult.is_solved ? 'var(--accent-emerald)' : 'var(--accent-crimson)'}`,
                  }}
                >
                  <h3
                    style={{
                      fontFamily: 'var(--font-serif)',
                      fontSize: '20px',
                      color: accuseResult.is_solved ? 'var(--accent-gold-bright)' : '#fda4af',
                      marginBottom: '8px',
                    }}
                  >
                    VERDICT: {accuseResult.verdict}
                  </h3>
                  <p style={{ fontSize: '14px', marginBottom: '14px' }}>
                    {accuseResult.narrative_debrief}
                  </p>

                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
                    <div className="header-stat">
                      <span>CULPRIT (25)</span>
                      <span className="header-stat-val">{accuseResult.score_breakdown.culprit_score}</span>
                    </div>
                    <div className="header-stat">
                      <span>MOTIVE (25)</span>
                      <span className="header-stat-val">{accuseResult.score_breakdown.motive_score}</span>
                    </div>
                    <div className="header-stat">
                      <span>METHOD (25)</span>
                      <span className="header-stat-val">{accuseResult.score_breakdown.method_score}</span>
                    </div>
                    <div className="header-stat">
                      <span>RECOVERY (25)</span>
                      <span className="header-stat-val">{accuseResult.score_breakdown.recovery_score}</span>
                    </div>
                  </div>

                  <div
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      marginTop: '14px',
                      paddingTop: '10px',
                      borderTop: '1px solid var(--border-subtle)',
                      fontWeight: 700,
                    }}
                  >
                    <span>PENALTY DEDUCTION: -{accuseResult.score_breakdown.attempt_penalty} pts</span>
                    <span style={{ fontSize: '18px', color: 'var(--accent-gold-bright)' }}>
                      FINAL SCORE: {accuseResult.score_breakdown.final_score} / 100
                    </span>
                  </div>

                  {/* AUTHORIZED SOLUTION REVEAL */}
                  {accuseResult.canonical_solution_reveal && (
                    <div className="solution-box fade-in">
                      <div className="solution-title">🔍 CANONICAL CASE SOLUTION REVEAL</div>
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '14px' }}>
                        <div>
                          <strong>Culprit:</strong> {accuseResult.canonical_solution_reveal.culprit}
                        </div>
                        <div>
                          <strong>Motive:</strong> {accuseResult.canonical_solution_reveal.motive}
                        </div>
                        <div>
                          <strong>Method:</strong> {accuseResult.canonical_solution_reveal.method}
                        </div>
                        <div>
                          <strong>Recovery Location:</strong>{' '}
                          {accuseResult.canonical_solution_reveal.recovery_location}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )}

              {session?.case_status !== 'CLOSED' && session?.case_status !== 'SOLVED' ? (
                <form className="accuse-form" onSubmit={handleAccuse}>
                  <div className="form-group">
                    <label className="form-label">1. ACCUSED PRIME SUSPECT (25 pts)</label>
                    <select
                      value={accusePayload.accused_suspect_id}
                      onChange={(e) =>
                        setAccusePayload({
                          ...accusePayload,
                          accused_suspect_id: e.target.value as SuspectId,
                        })
                      }
                    >
                      {config?.suspects.map((s) => (
                        <option key={s.suspect_id} value={s.suspect_id}>
                          {s.name} ({s.role})
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">2. EVIDENCE PROVING MOTIVE (25 pts)</label>
                    <select
                      value={accusePayload.motive_evidence_id}
                      onChange={(e) =>
                        setAccusePayload({
                          ...accusePayload,
                          motive_evidence_id: e.target.value as EvidenceId,
                        })
                      }
                    >
                      <option value="">-- Select discovered evidence item --</option>
                      {session?.discovered_evidence_ids.map((eid) => (
                        <option key={eid} value={eid}>
                          {eid}: {session.truth_ledger.facts.find((f) => f.evidence_id === eid)?.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      3. EVIDENCE PROVING BYPASS & ROUTE METHOD (25 pts, min 2 items)
                    </label>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
                      {session?.discovered_evidence_ids.map((eid) => {
                        const isChecked = accusePayload.method_evidence_ids.includes(eid);
                        return (
                          <label
                            key={eid}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px',
                              fontSize: '13px',
                              background: 'rgba(255,255,255,0.03)',
                              padding: '6px 10px',
                              borderRadius: '6px',
                            }}
                          >
                            <input
                              type="checkbox"
                              checked={isChecked}
                              onChange={(e) => {
                                if (e.target.checked) {
                                  setAccusePayload({
                                    ...accusePayload,
                                    method_evidence_ids: [...accusePayload.method_evidence_ids, eid],
                                  });
                                } else {
                                  setAccusePayload({
                                    ...accusePayload,
                                    method_evidence_ids: accusePayload.method_evidence_ids.filter(
                                      (id) => id !== eid
                                    ),
                                  });
                                }
                              }}
                            />
                            {eid}: {session.truth_ledger.facts.find((f) => f.evidence_id === eid)?.title}
                          </label>
                        );
                      })}
                    </div>
                  </div>

                  <div className="form-group">
                    <label className="form-label">4. EVIDENCE PROVING RECOVERY LOCATION (25 pts)</label>
                    <select
                      value={accusePayload.recovery_evidence_id}
                      onChange={(e) =>
                        setAccusePayload({
                          ...accusePayload,
                          recovery_evidence_id: e.target.value as EvidenceId,
                        })
                      }
                    >
                      <option value="">-- Select discovered evidence item locating relic --</option>
                      {session?.discovered_evidence_ids.map((eid) => (
                        <option key={eid} value={eid}>
                          {eid}: {session.truth_ledger.facts.find((f) => f.evidence_id === eid)?.title}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div className="form-group">
                    <label className="form-label">5. FORMAL INDICTMENT RATIONALE</label>
                    <textarea
                      rows={3}
                      placeholder="Explain how the suspect exploited the camera outage, bypassed the vitrine, and stashed the piece..."
                      value={accusePayload.detective_statement}
                      maxLength={1000}
                      onChange={(e) =>
                        setAccusePayload({ ...accusePayload, detective_statement: e.target.value })
                      }
                    />
                  </div>

                  <button
                    type="submit"
                    className="btn-primary"
                    style={{ background: 'linear-gradient(135deg, #e11d48, #be123c)', color: '#fff' }}
                    disabled={loading}
                  >
                    ⚖️ Deliver Formal Indictment
                  </button>
                </form>
              ) : (
                <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>
                  This case is officially {session.case_status}. No further accusations may be filed.
                  Reset case to investigate again.
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right Sidebar: Immutable Truth Ledger */}
        <aside className="sidebar-panel">
          <div className="card">
            <div className="card-title">
              <span>TRUTH LEDGER</span>
              <span style={{ fontSize: '11px', color: 'var(--accent-gold)' }}>VERIFIED FACTS</span>
            </div>

            <div className="evidence-list">
              {session?.truth_ledger.facts.length === 0 ? (
                <div style={{ fontSize: '13px', color: 'var(--text-faint)' }}>
                  No physical evidence discovered yet. Inspect examination targets to uncover clues.
                </div>
              ) : (
                session?.truth_ledger.facts.map((f) => (
                  <div key={f.fact_id} className="evidence-badge mandatory">
                    <div className="evidence-header">
                      <span className="evidence-code">{f.evidence_id}</span>
                      <span className="evidence-category">{f.category}</span>
                    </div>
                    <div style={{ fontWeight: 600, fontSize: '13px', marginBottom: '2px' }}>
                      {f.title}
                    </div>
                    <div className="evidence-desc">{f.summary}</div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="card">
            <div className="card-title">
              <span>CONTRADICTIONS</span>
              <span style={{ fontSize: '11px', color: 'var(--accent-crimson)' }}>SHATTERED LIES</span>
            </div>

            <div className="evidence-list">
              {session?.truth_ledger.contradictions.length === 0 ? (
                <div style={{ fontSize: '13px', color: 'var(--text-faint)' }}>
                  No suspect lies exposed yet. Catch suspects in a lie and present refuting evidence.
                </div>
              ) : (
                session?.truth_ledger.contradictions.map((c) => (
                  <div
                    key={c.rule_id}
                    className="evidence-badge"
                    style={{ borderLeft: '3px solid var(--accent-crimson)' }}
                  >
                    <div className="evidence-header">
                      <span className="evidence-code" style={{ color: 'var(--accent-crimson)' }}>
                        {c.rule_id}: {c.validation_state}
                      </span>
                      <span className="evidence-category">{c.refuting_evidence_id}</span>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                      "{c.disputed_claim}"
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </aside>
      </div>
    </div>
  );
}
