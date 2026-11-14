import React from 'react';

export default function SecurityAuditModal({ isOpen, onClose, securityData }) {
  if (!isOpen) return null;

  const controls = securityData?.controls || [
    {
      asvs_category: 'V2: Authentication Verification Standard',
      control: 'Argon2id / PBKDF2-HMAC-SHA256 Password Hashing',
      implementation: 'Cryptographically secure memory/time-hardened key derivation with unique 16-byte salts. Complies with OWASP ASVS v4.0 password storage standards.'
    },
    {
      asvs_category: 'V3: Session Management Verification Standard',
      control: 'Short TTL JWT (15 min) + Refresh Token Rotation',
      implementation: 'Access tokens strictly limited to 15-minute lifespan with HMAC-SHA256 cryptographic signing and refresh token rotation.'
    },
    {
      asvs_category: 'V5: Malicious Input Handling & Validation',
      control: 'Strict Pydantic v2 Schemas',
      implementation: 'All FastAPI endpoint payloads validated against strongly-typed Pydantic schemas, enforcing 0-100 score bounds, string lengths, and email syntax.'
    },
    {
      asvs_category: 'V5.3: SQL Injection Prevention',
      control: 'Parameterized Queries via SQLAlchemy ORM',
      implementation: 'Complete isolation of user data from query structure through AST parameter binding; zero raw string concatenation.'
    },
    {
      asvs_category: 'V13: API & Web Service Verification',
      control: 'SlowAPI Rate Limiting',
      implementation: 'Sliding-window IP-based rate limiting on sensitive /auth/login (10/min) and /auth/register (5/min) endpoints to neutralize brute-force attacks.'
    },
    {
      asvs_category: 'V8: Data Protection & Privacy',
      control: 'PII Sanitization in Application Logging',
      implementation: 'Custom logging formatter applies regex redaction to strip user emails and authorization bearer tokens prior to persistence.'
    }
  ];

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div>
            <h2 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#38bdf8' }}>
              🛡️ Security Verification & OWASP ASVS Mapping
            </h2>
            <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
              Platform Security: <strong>AI-Powered Personalized Learning Platform</strong>
            </p>
          </div>
          <button className="btn-close" onClick={onClose}>
            &times;
          </button>
        </div>

        <div style={{ marginBottom: '18px', fontSize: '0.85rem', color: '#cbd5e1', lineHeight: 1.5 }}>
          This system was designed from the ground up with defensive security engineering principles,
          aligned with the <strong>OWASP Application Security Verification Standard (ASVS v4.0)</strong>.
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {controls.map((c, i) => (
            <div key={i} className="control-item">
              <div className="control-cat">{c.asvs_category}</div>
              <div className="control-name">{c.control}</div>
              <div className="control-impl">{c.implementation}</div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: '20px', textAlign: 'right' }}>
          <button
            onClick={onClose}
            style={{
              background: '#334155',
              color: '#fff',
              border: 'none',
              padding: '8px 18px',
              borderRadius: '6px',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  );
}

