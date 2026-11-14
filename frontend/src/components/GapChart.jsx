import React from 'react';

export default function GapChart({ gapReport }) {
  if (!gapReport || !gapReport.skill_gaps) {
    return (
      <div className="card">
        <div className="card-title">📊 Competency Gap Analysis</div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem', marginTop: '10px' }}>
          Select an active career role to compute real-time skill gaps.
        </p>
      </div>
    );
  }

  const { skill_gaps, readiness_percentage, cosine_fit, role_title } = gapReport;

  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">📊 Skill Gap Vector Analysis</div>
          <div className="card-subtitle">
            G_s = max(0, R_s - P_s) vs Target: <strong>{role_title}</strong>
          </div>
        </div>
      </div>

      <div className="gap-list">
        {skill_gaps.map((item) => {
          const maxScale = 100;
          const pWidth = Math.min(100, (item.P_s / maxScale) * 100);
          const gapWidth = Math.min(100 - pWidth, (item.G_s / maxScale) * 100);

          return (
            <div key={item.skill_id} className="gap-item">
              <div className="gap-label-row">
                <span className="gap-skill-name">
                  {item.skill_name}{' '}
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontWeight: 400 }}>
                    (Weight I_s = {item.I_s})
                  </span>
                </span>
                <span className="gap-values">
                  P_s: <strong style={{ color: '#38bdf8' }}>{item.P_s.toFixed(1)}</strong> / Req R_s:{' '}
                  <strong>{item.R_s}</strong> {item.G_s > 0 ? (
                    <span style={{ color: '#f43f5e', marginLeft: '6px' }}>(-{item.G_s.toFixed(1)})</span>
                  ) : (
                    <span style={{ color: '#10b981', marginLeft: '6px' }}>(Met)</span>
                  )}
                </span>
              </div>

              <div className="gap-bar-container" title={`Current P_s: ${item.P_s}, Gap G_s: ${item.G_s}`}>
                <div className="bar-proficiency" style={{ width: `${pWidth}%` }} />
                <div className="bar-gap" style={{ width: `${gapWidth}%` }} />
              </div>
            </div>
          );
        })}
      </div>

      <div style={{ marginTop: '16px', display: 'flex', gap: '16px', fontSize: '0.78rem', color: 'var(--text-muted)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '12px', height: '12px', background: '#38bdf8', borderRadius: '2px' }} />
          <span>Current Verified Proficiency (P_s)</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <div style={{ width: '12px', height: '12px', background: '#f43f5e', opacity: 0.6, borderRadius: '2px' }} />
          <span>Missing Competency Gap (G_s)</span>
        </div>
      </div>
    </div>
  );
}

