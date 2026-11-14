import React from 'react';

export default function GoalSelector({ roles, activeRoleId, onSelectRole, loading }) {
  return (
    <div className="card" style={{ marginBottom: '24px' }}>
      <div className="card-header">
        <div>
          <div className="card-title">🎯 Target Career Role</div>
          <div className="card-subtitle">
            Triggers Career Matching Agent & dynamic requirement vector loading
          </div>
        </div>

        <select
          value={activeRoleId || ''}
          onChange={(e) => onSelectRole(Number(e.target.value))}
          disabled={loading}
          style={{
            background: '#0f172a',
            color: '#f8fafc',
            border: '1px solid #475569',
            padding: '8px 14px',
            borderRadius: '8px',
            fontSize: '0.9rem',
            fontWeight: 600,
            cursor: 'pointer'
          }}
        >
          {roles.map((r) => (
            <option key={r.id} value={r.id}>
              {r.title}
            </option>
          ))}
        </select>
      </div>

      {roles.find((r) => r.id === activeRoleId)?.description && (
        <p style={{ fontSize: '0.86rem', color: '#cbd5e1', fontStyle: 'italic' }}>
          "{roles.find((r) => r.id === activeRoleId).description}"
        </p>
      )}
    </div>
  );
}

