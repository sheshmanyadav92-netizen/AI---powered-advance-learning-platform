"""Integration tests for all FastAPI REST endpoints using TestClient and hand-computed checks.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models import Base, engine, SessionLocal
from app.seeds.seed_data import seed_database

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    # Drop and recreate tables for an isolated, clean test state
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_database(db)
    db.close()

def get_auth_token():
    # Login as seed demo student
    resp = client.post("/auth/login", json={
        "email": "demo@example.com",
        "password": "DemoPass123!"
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]

def test_root_endpoint():
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Learning Platform" in resp.text

def test_api_status_endpoint():
    resp = client.get("/api")
    assert resp.status_code == 200
    assert resp.json()["status"] == "online"

def test_security_controls_endpoint():
    resp = client.get("/security-controls")
    assert resp.status_code == 200
    data = resp.json()
    assert "OWASP" in data["compliance_standard"]

def test_roles_and_skills_endpoints():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    roles_resp = client.get("/roles")
    assert roles_resp.status_code == 200
    roles = roles_resp.json()
    assert len(roles) >= 1
    assert any(r["title"] == "Full Stack Developer" for r in roles)

    skills_resp = client.get("/skills")
    assert skills_resp.status_code == 200
    skills = skills_resp.json()
    assert len(skills) >= 6

def test_profile_get_and_put():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/profile", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["user"]["email"] == "demo@example.com"
    # Verify Python proficiency was seeded
    python_skill = next((s for s in data["skills"] if s["skill_name"] == "Python"), None)
    assert python_skill is not None
    assert python_skill["P_s"] == 69.0

    # Test updating profile self-assessment
    put_resp = client.put("/profile", json={
        "skills": [
            {"skill_id": python_skill["skill_id"], "A_s": 90.0, "E_s": 80.0}
        ]
    }, headers=headers)
    assert put_resp.status_code == 200

def test_goal_and_gap_report():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Fetch role id for Full Stack Developer
    roles = client.get("/roles").json()
    fs_role = next(r for r in roles if r["title"] == "Full Stack Developer")

    resp = client.post("/goal", json={"role_id": fs_role["id"]}, headers=headers)
    assert resp.status_code == 200
    gap_rep = resp.json()
    assert gap_rep["role_id"] == fs_role["id"]
    assert "readiness_percentage" in gap_rep
    assert "cosine_fit" in gap_rep
    assert len(gap_rep["skill_gaps"]) >= 6

def test_recommendations_retrieval():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.get("/recommendations", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "recommendations" in data
    assert "mentor_message" in data
    assert len(data["recommendations"]) > 0
    # Highest priority should be first
    recs = data["recommendations"]
    assert recs[0]["priority_score"] >= recs[-1]["priority_score"]

def test_assessment_submission_and_bkt_update():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Submit assessment for JavaScript (Skill 4)
    resp = client.post("/assessment", json={
        "skill_id": 4,
        "score": 85.0
    }, headers=headers)
    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["score"] == 85.0
    assert "p_mastery_after" in res_data
    # Because 85 >= 60, it's correct evidence, so mastery increases from initial 0.30
    assert res_data["p_mastery_after"] > 0.30

def test_progress_complete_endpoint():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Complete resource 1
    resp = client.post("/progress/complete", json={
        "resource_id": 1,
        "time_spent_min": 45,
        "assessment_score": 90.0
    }, headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "bkt_states" in data
    assert "recent_logs" in data
    assert len(data["recent_logs"]) > 0

def test_settings_and_encryption():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Test GET /settings
    res = client.get("/settings", headers=headers)
    assert res.status_code == 200
    settings_data = res.json()
    assert "theme" in settings_data
    assert "llm_provider" in settings_data

    # Test PUT /settings/theme
    theme_res = client.put("/settings/theme", json={"theme": "light"}, headers=headers)
    assert theme_res.status_code == 200
    assert theme_res.json()["theme"] == "light"

    # Test POST /settings/llm-key
    raw_key = "AIzaSySecretTestKey12345"
    key_res = client.post("/settings/llm-key", json={"provider": "gemini", "api_key": raw_key}, headers=headers)
    assert key_res.status_code == 200
    saved = key_res.json()
    assert saved["has_api_key"] is True
    assert saved["key_masked"] == "****2345"
    assert "ending ****2345" in saved["message"]
    # Ensure raw key is never echoed back in full
    assert raw_key not in str(saved)

def test_courses_catalog_endpoint():
    resp = client.get("/courses")
    assert resp.status_code == 200
    courses = resp.json()
    assert len(courses) >= 18
    # Assert minimum 3 per skill
    assert any(c["skill_name"] == "Python" for c in courses)
    assert any(c["skill_name"] == "JavaScript" for c in courses)

def test_certificates_endpoints():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    # Test GET /certificates
    certs_resp = client.get("/certificates", headers=headers)
    assert certs_resp.status_code == 200
    certs = certs_resp.json()
    assert len(certs) >= 1
    sample_cert = certs[0]
    assert "verification_code" in sample_cert
    code = sample_cert["verification_code"]

    # Test public GET /certificates/verify/{code} (no auth required)
    verify_resp = client.get(f"/certificates/verify/{code}")
    assert verify_resp.status_code == 200
    v_data = verify_resp.json()
    assert v_data["valid"] is True
    assert v_data["learner_name"] == "Demo Learner"
    assert v_data["verification_code"] == code

def test_mentor_chat_grounding():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}

    chat_res = client.post("/mentor/chat", json={"message": "What is my career readiness score?"}, headers=headers)
    assert chat_res.status_code == 200
    resp_text = chat_res.json()["response"]
    assert len(resp_text) > 10
    # Must answer about readiness or role
    assert any(term in resp_text.lower() for term in ["readiness", "full stack", "fit", "percent"])
