import React, { useState } from 'react';

export default function ProfileView({ profile, onUpdateProfile, loading }) {
  if (!profile || !profile.skills) return null;

  const [editSkillId, setEditSkillId] = useState(null);
  const [editAs, setEditAs] = useState(0);
  const [editEs, setEditEs] = useState(0);

  const startEdit = (skill) => {
    setEditSkillId(skill.skill_id);
    setEditAs(skill.A_s);
    setEditEs(skill.E_s);
  };

  const saveEdit = (skillId) => {
    onUpdateProfile([{ skill_id: skillId, A_s: Number(editAs), E_s: Number(editEs) }]);
    setEditSkillId(null);
  };

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">👤 Learner Skill Profile</div>
          <div className="card-subtitle">
            Formula: P_s = 0.2*A_s (Self) + 0.5*Q_s (Quiz) + 0.3*E_s (Evidence)
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
        {profile.skills.map((s) => {
          const isEditing = editSkillId === s.skill_id;

          return (
            <div
              key={s.skill_id}
              style={{
                background: 'rgba(15, 23, 42, 0.5)',
                border: '1px solid var(--border-color)',
                borderRadius: '8px',
                padding: '12px 16px'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <strong style={{ color: '#f8fafc', fontSize: '0.95rem' }}>{s.skill_name}</strong>
                  <span
                    style={{
                      marginLeft: '8px',
                      fontSize: '0.72rem',
                      background: 'rgba(51, 65, 85, 0.8)',
                      padding: '2px 6px',
                      borderRadius: '4px',
                      color: '#94a3b8'
                    }}
                  >
                    {s.category}
                  </span>
                </div>
                <div style={{ fontFamily: 'JetBrains Mono', fontSize: '1.05rem', color: '#38bdf8', fontWeight: 700 }}>
                  P_s: {s.P_s.toFixed(1)}%
                </div>
              </div>

              {isEditing ? (
                <div style={{ marginTop: '12px', display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Self A_s:
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={editAs}
                      onChange={(e) => setEditAs(e.target.value)}
                      style={{
                        marginLeft: '6px',
                        width: '60px',
                        padding: '4px',
                        background: '#0f172a',
                        border: '1px solid #475569',
                        color: '#fff',
                        borderRadius: '4px'
                      }}
                    />
                  </label>
                  <label style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                    Evidence E_s:
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={editEs}
                      onChange={(e) => setEditEs(e.target.value)}
                      style={{
                        marginLeft: '6px',
                        width: '60px',
                        padding: '4px',
                        background: '#0f172a',
                        border: '1px solid #475569',
                        color: '#fff',
                        borderRadius: '4px'
                      }}
                    />
                  </label>
                  <button
                    onClick={() => saveEdit(s.skill_id)}
                    disabled={loading}
                    style={{
                      background: '#38bdf8',
                      color: '#0f172a',
                      fontWeight: 700,
                      border: 'none',
                      padding: '4px 10px',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setEditSkillId(null)}
                    style={{
                      background: 'transparent',
                      color: '#94a3b8',
                      border: '1px solid #475569',
                      padding: '4px 8px',
                      borderRadius: '4px',
                      cursor: 'pointer'
                    }}
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginTop: '8px',
                    fontSize: '0.78rem',
                    color: 'var(--text-muted)'
                  }}
                >
                  <div style={{ fontFamily: 'JetBrains Mono' }}>
                    A_s: {s.A_s} (20%) | Q_s: {s.Q_s} (50%) | E_s: {s.E_s} (30%)
                  </div>
                  <button
                    onClick={() => startEdit(s)}
                    style={{
                      background: 'transparent',
                      border: 'none',
                      color: '#38bdf8',
                      cursor: 'pointer',
                      fontSize: '0.78rem',
                      textDecoration: 'underline'
                    }}
                  >
                    Adjust inputs
                  </button>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

