import React, { useState } from 'react';

export default function ProgressMasteryView({ progressData, skills, onSubmitAssessment, loading }) {
  const [selectedSkillId, setSelectedSkillId] = useState('');
  const [quizScore, setQuizScore] = useState(85);

  const bktStates = progressData?.bkt_states || [];
  const recentLogs = progressData?.recent_logs || [];

  const handleQuizSubmit = (e) => {
    e.preventDefault();
    if (!selectedSkillId) return;
    onSubmitAssessment(Number(selectedSkillId), Number(quizScore));
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">📈 Bayesian Knowledge Tracing (BKT)</div>
          <div className="card-subtitle">
            Probabilistic mastery model (Corbett & Anderson, 1994): P(L0)=0.30, P(T)=0.15, P(G)=0.20, P(S)=0.10
          </div>
        </div>
      </div>

      {/* Interactive Assessment Simulator */}
      <div
        style={{
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid #334155',
          borderRadius: '8px',
          padding: '14px',
          marginBottom: '20px'
        }}
      >
        <span style={{ fontSize: '0.82rem', fontWeight: 700, color: '#38bdf8' }}>
          🧪 Live Assessment Simulator (Test Pedagogical Adaptivity):
        </span>
        <form
          onSubmit={handleQuizSubmit}
          style={{ display: 'flex', gap: '10px', marginTop: '10px', flexWrap: 'wrap', alignItems: 'center' }}
        >
          <select
            value={selectedSkillId}
            onChange={(e) => setSelectedSkillId(e.target.value)}
            required
            style={{
              background: '#1e293b',
              color: '#fff',
              border: '1px solid #475569',
              padding: '6px 10px',
              borderRadius: '6px',
              fontSize: '0.85rem'
            }}
          >
            <option value="">-- Choose Skill --</option>
            {skills.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>

          <label style={{ fontSize: '0.85rem', color: '#cbd5e1' }}>
            Score:
            <input
              type="number"
              min="0"
              max="100"
              value={quizScore}
              onChange={(e) => setQuizScore(e.target.value)}
              style={{
                marginLeft: '6px',
                width: '65px',
                padding: '6px',
                background: '#1e293b',
                color: '#fff',
                border: '1px solid #475569',
                borderRadius: '6px'
              }}
            />
            %
          </label>

          <button
            type="submit"
            disabled={loading || !selectedSkillId}
            style={{
              background: '#06b6d4',
              color: '#0f172a',
              border: 'none',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '0.85rem',
              fontWeight: 700,
              cursor: 'pointer'
            }}
          >
            Submit Quiz
          </button>

          <span style={{ fontSize: '0.72rem', color: 'var(--text-dim)', width: '100%' }}>
            Tip: Submit 3 consecutive scores &lt; 60% on a skill to watch the Orchestrator trigger adaptive difficulty reduction.
          </span>
        </form>
      </div>

      {/* Mastery Bars */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
        {bktStates.map((bkt) => {
          const masteryPct = (bkt.p_mastery * 100).toFixed(1);
          const barColor = bkt.needs_remediation
            ? '#f43f5e'
            : bkt.p_mastery >= 0.75
            ? '#10b981'
            : '#38bdf8';

          return (
            <div key={bkt.skill_id}>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.88rem', marginBottom: '4px' }}>
                <span style={{ fontWeight: 600, color: '#f8fafc' }}>
                  {bkt.skill_name}
                  {bkt.needs_remediation && (
                    <span
                      style={{
                        marginLeft: '8px',
                        background: 'rgba(244, 63, 94, 0.2)',
                        color: '#fb7185',
                        border: '1px solid rgba(244, 63, 94, 0.4)',
                        fontSize: '0.7rem',
                        padding: '1px 6px',
                        borderRadius: '4px',
                        fontWeight: 700
                      }}
                    >
                      ⚠️ ADAPTATION: Remediation Active (P &lt; 0.50 after 3+ attempts)
                    </span>
                  )}
                </span>
                <span style={{ fontFamily: 'JetBrains Mono', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
                  P(Ln): <strong style={{ color: barColor }}>{bkt.p_mastery.toFixed(3)}</strong> ({masteryPct}%) | Attempts: {bkt.attempts_count}
                </span>
              </div>

              <div style={{ height: '8px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '4px', overflow: 'hidden' }}>
                <div
                  style={{
                    width: `${masteryPct}%`,
                    height: '100%',
                    background: barColor,
                    transition: 'width 0.4s ease'
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Recent Activity Log */}
      {recentLogs.length > 0 && (
        <div style={{ marginTop: '24px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: '#94a3b8', marginBottom: '8px' }}>
            Recent Learning Activity Log:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {recentLogs.slice(0, 4).map((log) => (
              <div
                key={log.id}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  fontSize: '0.78rem',
                  color: '#cbd5e1',
                  background: 'rgba(15, 23, 42, 0.3)',
                  padding: '6px 10px',
                  borderRadius: '4px'
                }}
              >
                <span>✓ {log.resource_title} ({log.skill_name})</span>
                <span style={{ fontFamily: 'JetBrains Mono', color: 'var(--text-dim)' }}>
                  {log.time_spent_min} min spent
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

