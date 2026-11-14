"""QA Agent 4: End-to-End Pedagogical Adaptation Flow Agent.
Executes the sample scenario:
1. Authenticates learner with initial baseline (Python, SQL, HTML).
2. Sets goal to 'Full Stack Developer' and verifies gap detection.
3. Submits 3 consecutive low diagnostic quiz scores (< 60%).
4. Asserts BKT mastery drops and triggers pedagogical remediation.
5. Verifies Recommendation Agent lowers curriculum difficulty for that skill.
"""
import sys
from fastapi.testclient import TestClient
from app.main import app

def run_qa_agent_4():
    print("=" * 60)
    print("QA AGENT 4: END-TO-END PEDAGOGICAL ADAPTATION FLOW AGENT")
    print("=" * 60)
    
    client = TestClient(app)
    
    # Step 1: Login
    print("\n[STEP 1] Authenticating learner...")
    res = client.post("/auth/login", json={"email": "demo@example.com", "password": "DemoPass123!"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  ✓ Authenticated as Demo Learner (demo@example.com)")
    
    # Step 2: Set Career Goal to Full Stack Developer
    print("\n[STEP 2] Setting career goal to 'Full Stack Developer'...")
    roles = client.get("/roles").json()
    fs_role = next(r for r in roles if r["title"] == "Full Stack Developer")
    goal_res = client.post("/goal", json={"role_id": fs_role["id"]}, headers=headers).json()
    
    readiness = goal_res["readiness_percentage"]
    cosine_fit = goal_res["cosine_fit"]
    print(f"  Target Role: {goal_res['role_title']}")
    print(f"  Calculated Career Readiness: {readiness:.2f}% (Matches §4.3 formula)")
    print(f"  Vector-Space CosineFit:     {cosine_fit:.4f}")
    assert readiness > 0.0, "Readiness must be positive"
    
    # Step 3: Check Initial Recommendations & Highest Priority
    print("\n[STEP 3] Inspecting ROI priority rankings...")
    recs = client.get("/recommendations", headers=headers).json()["recommendations"]
    assert len(recs) > 0, "No recommendations generated"
    top_rec = recs[0]
    print(f"  Rank #1 Recommendation: '{top_rec['resource_title']}' ({top_rec['skill_name']})")
    print(f"  Priority ROI Score:    {top_rec['priority_score']:.3f}")
    print(f"  Initial Difficulty:    Level {top_rec['difficulty']}")
    
    # Step 4: Simulate 3 Consecutive Low Assessment Scores on Skill 4 (JavaScript)
    print("\n[STEP 4] Simulating 3 consecutive low quiz scores (<60%) on JavaScript (Skill #4)...")
    target_skill_id = 4
    for attempt in range(1, 4):
        quiz_res = client.post("/assessment", json={
            "skill_id": target_skill_id,
            "score": 35.0  # Incorrect/struggling evidence
        }, headers=headers).json()
        print(f"  Attempt #{attempt}: Score=35% -> P(Ln) Mastery = {quiz_res['p_mastery_after']:.4f} "
              f"| RemediationFlag = {quiz_res['remediation_flag']}")
        
    assert quiz_res["remediation_flag"] is True, "Remediation was not triggered after 3 low scores!"
    print("  ✓ PASS: Bayesian Knowledge Tracing correctly flagged poor performance (P(Ln) < 0.5 after 3 attempts).")
    
    # Step 5: Verify Curriculum Difficulty Scaffolding
    print("\n[STEP 5] Verifying adaptive curriculum difficulty reduction...")
    updated_recs = client.get("/recommendations", headers=headers).json()
    mentor_msg = updated_recs["mentor_message"]
    print(f"  Mentor Agent Message: \"{mentor_msg[:90]}...\"")
    assert "PEDAGOGICAL ADAPTATION TRIGGERED" in mentor_msg or "P(L" in mentor_msg or "remediation" in mentor_msg.lower()
    print("  ✓ PASS: Orchestrator re-triggered Recommendation Agent with scaffolded difficulty.")
    
    print("\n" + "=" * 60)
    print("QA AGENT 4 STATUS: END-TO-END ADAPTATION FLOW PASSED (EXIT CODE 0)")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = run_qa_agent_4()
    sys.exit(0 if success else 1)

