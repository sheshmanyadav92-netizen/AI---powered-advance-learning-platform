import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import GoalSelector from './components/GoalSelector';
import GapChart from './components/GapChart';
import ProfileView from './components/ProfileView';
import RecommendationsList from './components/RecommendationsList';
import ProgressMasteryView from './components/ProgressMasteryView';
import SecurityAuditModal from './components/SecurityAuditModal';

const API_BASE = '';

export default function App() {
  const [token, setToken] = useState(localStorage.getItem('token') || '');
  const [roles, setRoles] = useState([]);
  const [skills, setSkills] = useState([]);
  const [profile, setProfile] = useState(null);
  const [gapReport, setGapReport] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [mentorMessage, setMentorMessage] = useState('');
  const [progressData, setProgressData] = useState(null);
  const [securityData, setSecurityData] = useState(null);
  const [activeRoleId, setActiveRoleId] = useState(null);
  const [isSecurityModalOpen, setIsSecurityModalOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');

  // 1. Initial Login & Bootstrap
  useEffect(() => {
    async function init() {
      try {
        let currentToken = token;
        if (!currentToken) {
          // Log in with seed demo student account
          const loginResp = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              email: 'demo@example.com',
              password: 'DemoPass123!'
            })
          });

          if (loginResp.ok) {
            const data = await loginResp.json();
            currentToken = data.access_token;
            setToken(currentToken);
            localStorage.setItem('token', currentToken);
          }
        }

        // Fetch catalogs
        const [rolesResp, skillsResp, secResp] = await Promise.all([
          fetch(`${API_BASE}/roles`),
          fetch(`${API_BASE}/skills`),
          fetch(`${API_BASE}/security-controls`)
        ]);

        if (rolesResp.ok) {
          const rolesData = await rolesResp.json();
          setRoles(rolesData);
          if (rolesData.length > 0) setActiveRoleId(rolesData[0].id);
        }
        if (skillsResp.ok) setSkills(await skillsResp.json());
        if (secResp.ok) setSecurityData(await secResp.json());

        if (currentToken) {
          await loadDashboard(currentToken);
        }
      } catch (err) {
        console.error('Initialization error:', err);
      }
    }

    init();
  }, []);

  async function loadDashboard(authToken) {
    const headers = { Authorization: `Bearer ${authToken}` };
    setLoading(true);
    try {
      const [profileRes, goalRes, recsRes, progRes] = await Promise.all([
        fetch(`${API_BASE}/profile`, { headers }),
        fetch(`${API_BASE}/goal`, { headers }),
        fetch(`${API_BASE}/recommendations`, { headers }),
        fetch(`${API_BASE}/progress`, { headers })
      ]);

      if (profileRes.ok) {
        const pData = await profileRes.json();
        setProfile(pData);
        if (pData.active_goal) setActiveRoleId(pData.active_goal.role_id);
      }
      if (goalRes.ok) setGapReport(await goalRes.json());
      if (recsRes.ok) {
        const rData = await recsRes.json();
        setRecommendations(rData.recommendations);
        setMentorMessage(rData.mentor_message);
      }
      if (progRes.ok) setProgressData(await progRes.json());
    } catch (e) {
      console.error('Dashboard load error:', e);
    } finally {
      setLoading(false);
    }
  }

  // Handle changing career goal
  const handleSelectRole = async (roleId) => {
    setActiveRoleId(roleId);
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/goal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ role_id: roleId })
      });

      if (resp.ok) {
        const data = await resp.json();
        setGapReport(data);
        // Refresh recommendations
        const recResp = await fetch(`${API_BASE}/recommendations`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (recResp.ok) {
          const rData = await recResp.json();
          setRecommendations(rData.recommendations);
          setMentorMessage(rData.mentor_message);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle updating profile skills
  const handleUpdateProfile = async (skillsUpdate) => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ skills: skillsUpdate })
      });

      if (resp.ok) {
        await loadDashboard(token);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle quiz submission
  const handleSubmitAssessment = async (skillId, score) => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/assessment`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ skill_id: skillId, score: score })
      });

      if (resp.ok) {
        await loadDashboard(token);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Handle completing a resource
  const handleCompleteResource = async (resourceId) => {
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/progress/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          resource_id: resourceId,
          time_spent_min: 45,
          assessment_score: 85.0
        })
      });

      if (resp.ok) {
        await loadDashboard(token);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const readiness = gapReport?.readiness_percentage ?? 0;
  const cosineFit = gapReport?.cosine_fit ?? 0;

  return (
    <div className="container">
      <Header
        onOpenSecurityModal={() => setIsSecurityModalOpen(true)}
        readiness={readiness}
        cosineFit={cosineFit}
      />

      {/* Stats KPI Banner */}
      <div className="stats-banner">
        <div className="stat-box">
          <div className="stat-label">Career Readiness</div>
          <div className="stat-value">{readiness.toFixed(1)}%</div>
          <div className="stat-sub">Formula: sum(P_s*I_s)/sum(R_s*I_s)</div>
        </div>

        <div className="stat-box">
          <div className="stat-label">Vector Space Fit</div>
          <div className="stat-value" style={{ color: '#c084fc' }}>
            {cosineFit.toFixed(4)}
          </div>
          <div className="stat-sub">CosineFit: (P · R)/(||P||*||R||)</div>
        </div>

        <div className="stat-box">
          <div className="stat-label">Bayesian Average Mastery</div>
          <div className="stat-value" style={{ color: '#34d399' }}>
            {(progressData?.overall_mastery ?? 0).toFixed(1)}%
          </div>
          <div className="stat-sub">Latent Cognitive Model P(Ln)</div>
        </div>

        <div className="stat-box">
          <div className="stat-label">Active Goal</div>
          <div className="stat-value" style={{ fontSize: '1.25rem', color: '#f1f5f9', paddingTop: '6px' }}>
            {gapReport?.role_title || 'Full Stack Developer'}
          </div>
          <div className="stat-sub">6 Core Skill Requirements</div>
        </div>
      </div>

      <GoalSelector
        roles={roles}
        activeRoleId={activeRoleId}
        onSelectRole={handleSelectRole}
        loading={loading}
      />

      {/* Main Two-Column Layout */}
      <div className="grid-main">
        {/* Left Column: Skill Analysis & Career Matching */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <GapChart gapReport={gapReport} />
          <ProfileView
            profile={profile}
            onUpdateProfile={handleUpdateProfile}
            loading={loading}
          />
        </div>

        {/* Right Column: Recommendations & BKT Progress */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          <RecommendationsList
            recommendations={recommendations}
            mentorMessage={mentorMessage}
            onCompleteResource={handleCompleteResource}
            loading={loading}
          />
          <ProgressMasteryView
            progressData={progressData}
            skills={skills}
            onSubmitAssessment={handleSubmitAssessment}
            loading={loading}
          />
        </div>
      </div>

      {/* Security Controls & OWASP Audit Modal */}
      <SecurityAuditModal
        isOpen={isSecurityModalOpen}
        onClose={() => setIsSecurityModalOpen(false)}
        securityData={securityData}
      />
    </div>
  );
}

