import React from 'react';

export default function RecommendationsList({ recommendations, mentorMessage, onCompleteResource, loading }) {
  return (
    <div className="card">
      <div className="card-header">
        <div>
          <div className="card-title">📚 Priority-Ranked Curricula</div>
          <div className="card-subtitle">
            Ranked by ROI: Priority_s = (G_s * I_s) / T_s (Tie-break: Tag Cosine Sim)
          </div>
        </div>
      </div>

      {mentorMessage && (
        <div className="mentor-box">
          <div className="mentor-icon">🤖</div>
          <div className="mentor-content">
            <h4>Mentor Agent Orchestrator Guidance</h4>
            <p>{mentorMessage}</p>
          </div>
        </div>
      )}

      {recommendations.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '30px', color: 'var(--text-muted)' }}>
          🎉 All required competencies for the active target role have been achieved!
        </div>
      ) : (
        <div>
          {recommendations.map((rec, idx) => (
            <div key={rec.id || idx} className="rec-card">
              <div className="rec-top">
                <div>
                  <span
                    style={{
                      fontSize: '0.72rem',
                      fontWeight: 700,
                      color: '#38bdf8',
                      textTransform: 'uppercase',
                      letterSpacing: '0.05em'
                    }}
                  >
                    #{idx + 1} Target Skill: {rec.skill_name}
                  </span>
                  <br />
                  <a href={rec.resource_url} target="_blank" rel="noreferrer" className="rec-title">
                    {rec.resource_title} ↗
                  </a>
                </div>

                <div className="priority-badge">
                  ROI Priority: {rec.priority_score.toFixed(3)}
                </div>
              </div>

              <div className="rec-tags">
                <span className="tag-pill" style={{ background: 'rgba(56, 189, 248, 0.15)', color: '#38bdf8' }}>
                  Diff: Level {rec.difficulty}
                </span>
                <span className="tag-pill" style={{ background: 'rgba(168, 85, 247, 0.15)', color: '#c084fc' }}>
                  Est: {rec.est_hours} hrs
                </span>
                <span className="tag-pill" style={{ background: 'rgba(34, 197, 94, 0.15)', color: '#4ade80' }}>
                  Tag Match: {(rec.tag_similarity * 100).toFixed(0)}%
                </span>
                {rec.tags.map((t, i) => (
                  <span key={i} className="tag-pill">
                    #{t}
                  </span>
                ))}
              </div>

              <div className="rec-actions">
                <span style={{ fontSize: '0.75rem', color: 'var(--text-dim)' }}>
                  Formula: ({rec.skill_name} Gap * Importance) / {rec.est_hours}h
                </span>

                <button
                  className="btn-complete"
                  disabled={loading}
                  onClick={() => onCompleteResource(rec.resource_id)}
                >
                  ✓ Complete & Log
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

