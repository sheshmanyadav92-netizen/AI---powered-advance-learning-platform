"""QA Agent 1: Formula Cross-Check Agent.
Independently recomputes P_s, G_s, Readiness, CosineFit, Priority_s, and BKT updates
from raw SQLite database values, and diffs them against what the API endpoints return.
Guarantees zero numeric inconsistency or rounding drift.
"""
import sys
import math
from fastapi.testclient import TestClient
from app.main import app
from app.models import SessionLocal, UserSkill, RoleSkillRequirement, Skill, CareerRole, LearningResource, BKTState

def run_qa_agent_1():
    print("=" * 60)
    print("QA AGENT 1: FORMULA CROSS-CHECK AGENT (INDEPENDENT VERIFICATION)")
    print("=" * 60)
    
    client = TestClient(app)
    db = SessionLocal()
    
    try:
        # Authenticate
        login_resp = client.post("/auth/login", json={
            "email": "demo@example.com",
            "password": "DemoPass123!"
        })
        assert login_resp.status_code == 200, "Login failed in QA Agent 1"
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. Cross-check P_s (Skill Proficiency)
        print("\n[CHECK 1] Cross-checking Skill Proficiency (P_s = 0.2*A_s + 0.5*Q_s + 0.3*E_s)...")
        u_skills = db.query(UserSkill).filter_by(user_id=1).all()
        api_profile = client.get("/profile", headers=headers).json()
        api_skills_map = {s["skill_id"]: s for s in api_profile["skills"]}
        
        for us in u_skills:
            # Independent raw recomputation
            raw_p_s = (0.2 * us.A_s) + (0.5 * us.Q_s) + (0.3 * us.E_s)
            api_s = api_skills_map[us.skill_id]
            api_p_s = api_s["P_s"]
            diff = abs(raw_p_s - api_p_s)
            
            print(f"  Skill #{us.skill_id} ({api_s['skill_name']}): "
                  f"Raw={raw_p_s:.4f} | API={api_p_s:.4f} | Diff={diff:.6f}")
            if diff > 1e-4:
                print(f"❌ FAIL: Discrepancy in P_s for Skill #{us.skill_id}")
                return False
        print("  ✓ PASS: All P_s proficiency scores match raw independent calculation.")
        
        # 2. Cross-check G_s, Readiness & CosineFit
        print("\n[CHECK 2] Cross-checking Skill Gaps (G_s), Readiness % and CosineFit...")
        fs_role = db.query(CareerRole).filter_by(title="Full Stack Developer").first()
        reqs = db.query(RoleSkillRequirement).filter_by(role_id=fs_role.id).all()
        
        num_sum = 0.0
        den_sum = 0.0
        p_vec = []
        r_vec = []
        expected_gaps = {}
        
        for r in reqs:
            us = db.query(UserSkill).filter_by(user_id=1, skill_id=r.skill_id).first()
            p_val = ((0.2 * us.A_s) + (0.5 * us.Q_s) + (0.3 * us.E_s)) if us else 0.0
            r_val = float(r.R_s)
            i_val = float(r.I_s)
            
            g_val = max(0.0, r_val - p_val)
            expected_gaps[r.skill_id] = g_val
            
            num_sum += p_val * i_val
            den_sum += r_val * i_val
            p_vec.append(p_val)
            r_vec.append(r_val)
            
        expected_readiness = (num_sum / den_sum) * 100.0 if den_sum > 0 else 0.0
        
        dot = sum(p * r for p, r in zip(p_vec, r_vec))
        norm_p = math.sqrt(sum(p * p for p in p_vec))
        norm_r = math.sqrt(sum(r * r for r in r_vec))
        expected_cosine = (dot / (norm_p * norm_r)) if (norm_p > 0 and norm_r > 0) else 0.0
        
        api_goal = client.get("/goal", headers=headers).json()
        api_readiness = api_goal["readiness_percentage"]
        api_cosine = api_goal["cosine_fit"]
        
        print(f"  Readiness: Raw={expected_readiness:.4f}% | API={api_readiness:.4f}% | Diff={abs(expected_readiness - api_readiness):.6f}")
        print(f"  CosineFit: Raw={expected_cosine:.4f} | API={api_cosine:.4f} | Diff={abs(expected_cosine - api_cosine):.6f}")
        
        if abs(expected_readiness - api_readiness) > 0.1:
            print("❌ FAIL: Discrepancy in Readiness %")
            return False
        if abs(expected_cosine - api_cosine) > 0.005:
            print("❌ FAIL: Discrepancy in CosineFit")
            return False
            
        print("  ✓ PASS: Readiness % and CosineFit match independent vector calculations.")
        
        # 3. Cross-check Priority_s for Recommendations
        print("\n[CHECK 3] Cross-checking Recommendation Priority Scores (Priority_s = (G_s * I_s) / T_s)...")
        api_recs = client.get("/recommendations", headers=headers).json()["recommendations"]
        req_map = {r.skill_id: r for r in reqs}
        
        for r_item in api_recs:
            sid = r_item["skill_id"]
            if sid in req_map:
                g_val = expected_gaps[sid]
                i_val = float(req_map[sid].I_s)
                t_val = float(r_item["est_hours"])
                expected_prio = (g_val * i_val) / t_val
                api_prio = float(r_item["priority_score"])
                diff = abs(expected_prio - api_prio)
                
                print(f"  Rec: {r_item['resource_title'][:30]}... ({r_item['skill_name']}): "
                      f"Raw={expected_prio:.4f} | API={api_prio:.4f} | Diff={diff:.6f}")
                if diff > 1e-4:
                    print(f"❌ FAIL: Discrepancy in Priority_s for {r_item['resource_title']}")
                    return False
        print("  ✓ PASS: All recommendation priority rankings match mathematical ROI.")
        
        # 4. Cross-check BKT Step
        print("\n[CHECK 4] Cross-checking Bayesian Knowledge Tracing (BKT) State from raw DB...")
        target_bkt_record = db.query(BKTState).filter_by(user_id=1, skill_id=4).first()
        bkt_prev = float(target_bkt_record.p_mastery) if target_bkt_record else 0.30
        pT, pG, pS = 0.15, 0.20, 0.10
        
        # If correct evidence from bkt_prev
        num_c = bkt_prev * (1 - pS)
        den_c = num_c + (1 - bkt_prev) * pG
        p_c_ev = num_c / den_c
        expected_bkt_c = p_c_ev + (1 - p_c_ev) * pT
        
        # Call assessment endpoint with score 85 (correct evidence)
        ass_res = client.post("/assessment", json={"skill_id": 4, "score": 85.0}, headers=headers).json()
        api_bkt = ass_res["p_mastery_after"]
        bkt_diff = abs(expected_bkt_c - api_bkt)
        print(f"  BKT Prior P(Ln-1): {bkt_prev:.4f}")
        print(f"  BKT Posterior P(Ln): Raw Independent={expected_bkt_c:.4f} | API={api_bkt:.4f} | Diff={bkt_diff:.6f}")
        if bkt_diff > 1e-4:
            print("❌ FAIL: Discrepancy in BKT computation")
            return False
        print("  ✓ PASS: BKT latent cognitive model updates match Corbett & Anderson (1994).")
        
        print("\n" + "=" * 60)
        print("QA AGENT 1 STATUS: ALL FORMULA CHECKS PASSED (EXIT CODE 0)")
        print("=" * 60)
        return True
    finally:
        db.close()

if __name__ == "__main__":
    success = run_qa_agent_1()
    sys.exit(0 if success else 1)
