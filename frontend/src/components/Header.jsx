import React from 'react';

export default function Header({ onOpenSecurityModal, readiness, cosineFit }) {
  return (
    <header>
      <div>
        <div className="brand-title">
          <span>⚡ AI Learning Platform</span>
          <span className="brand-badge">Multi-Agent System</span>
        </div>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginTop: '4px' }}>
          Autonomous Multi-Agent Skill Gap Analysis & Adaptive Curricula
        </p>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div className="author-pill">
          <span>🎯</span>
          <span>Target: Full Stack Developer</span>
        </div>

        <button className="btn-sec-audit" onClick={onOpenSecurityModal}>
          OWASP ASVS Audit
        </button>
      </div>
    </header>
  );
}

