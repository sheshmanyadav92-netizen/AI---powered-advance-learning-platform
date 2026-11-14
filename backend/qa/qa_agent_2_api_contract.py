"""QA Agent 2: API Contract Agent.
Validates exact HTTP status codes, JSON schema models, settings & key management, and auth-rejection boundaries across all endpoints.
"""
import sys
from fastapi.testclient import TestClient
from app.main import app

def run_qa_agent_2():
    print("=" * 60)
    print("QA AGENT 2: API CONTRACT & SCHEMA VALIDATION AGENT")
    print("=" * 60)
    
    client = TestClient(app)
    
    # 1. Test Auth Login & Schema
    print("\n[CHECK 1] Testing POST /auth/login...")
    res = client.post("/auth/login", json={"email": "demo@example.com", "password": "DemoPass123!"})
    print(f"  Status: {res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    body = res.json()
    assert "access_token" in body and "refresh_token" in body, "Missing token keys"
    assert body["token_type"] == "bearer", "Token type must be bearer"
    token = body["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  ✓ PASS: Login contract valid.")
    
    # 2. Test Auth Failure Boundaries
    print("\n[CHECK 2] Testing Auth Failure Rejections...")
    # Missing token on protected endpoint
    res_no_auth = client.get("/profile")
    print(f"  No Auth Header -> Status: {res_no_auth.status_code}")
    assert res_no_auth.status_code == 401, f"Expected 401, got {res_no_auth.status_code}"
    
    # Corrupted token
    res_bad_auth = client.get("/profile", headers={"Authorization": "Bearer invalid.corrupted.token"})
    print(f"  Corrupted Token -> Status: {res_bad_auth.status_code}")
    assert res_bad_auth.status_code == 401, f"Expected 401, got {res_bad_auth.status_code}"
    
    # Invalid Login
    res_bad_login = client.post("/auth/login", json={"email": "demo@example.com", "password": "WrongPassword!"})
    print(f"  Invalid Password -> Status: {res_bad_login.status_code}")
    assert res_bad_login.status_code == 401, f"Expected 401, got {res_bad_login.status_code}"
    print("  ✓ PASS: Auth rejection boundaries enforced.")
    
    # 3. Test Validation Schema Rejection (422)
    print("\n[CHECK 3] Testing Pydantic Input Validation Boundaries...")
    res_bad_score = client.post("/assessment", json={"skill_id": 1, "score": 150.0}, headers=headers)
    print(f"  Score out of range (150 > 100) -> Status: {res_bad_score.status_code}")
    assert res_bad_score.status_code == 422, f"Expected 422, got {res_bad_score.status_code}"
    print("  ✓ PASS: Input schema range constraints (0-100) enforced.")
    
    # 4. Test All Primary Resource Endpoints
    print("\n[CHECK 4] Testing REST API Schema Responses...")
    endpoints = [
        ("GET", "/profile", 200, ["user", "skills", "active_goal"]),
        ("GET", "/goal", 200, ["role_id", "readiness_percentage", "cosine_fit", "skill_gaps"]),
        ("GET", "/recommendations", 200, ["recommendations", "mentor_message"]),
        ("GET", "/progress", 200, ["bkt_states", "recent_logs", "overall_mastery"]),
        ("GET", "/roles", 200, None),
        ("GET", "/skills", 200, None),
        ("GET", "/security-controls", 200, ["controls", "compliance_standard"]),
        ("GET", "/settings", 200, ["theme", "llm_provider", "has_api_key"]),
        ("GET", "/mentor/history", 200, None),
    ]
    
    for method, path, expected_status, expected_keys in endpoints:
        r = client.get(path, headers=headers) if method == "GET" else None
        print(f"  {method} {path} -> {r.status_code}")
        assert r.status_code == expected_status, f"{path} failed with {r.status_code}"
        if expected_keys:
            j = r.json()
            for k in expected_keys:
                assert k in j, f"Key {k} missing in {path} response"
    print("  ✓ PASS: All endpoint schemas match API specifications.")

    # 5. Test Settings & Encrypted LLM Key Management
    print("\n[CHECK 5] Testing Settings & LLM Key Contract...")
    test_key = "AIzaSyTestApiKeyContract9876"
    key_res = client.post("/settings/llm-key", json={"provider": "claude", "api_key": test_key}, headers=headers)
    assert key_res.status_code == 200, f"Expected 200, got {key_res.status_code}"
    key_data = key_res.json()
    assert key_data["has_api_key"] is True
    assert key_data["key_masked"] == "****9876"
    assert "ending ****9876" in key_data["message"]
    assert test_key not in str(key_data), "Full API key must never be echoed in response!"
    print(f"  POST /settings/llm-key -> {key_data['message']}")
    print("  ✓ PASS: Encrypted key storage contract validated.")
    
    print("\n" + "=" * 60)
    print("QA AGENT 2 STATUS: ALL CONTRACT & SCHEMA CHECKS PASSED (EXIT CODE 0)")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_qa_agent_2()
    sys.exit(0 if success else 1)
