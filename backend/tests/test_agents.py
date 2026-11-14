"""Unit tests for LangGraph agent workflow execution and state transitions.
"""
import pytest
from app.agents.graph import run_agent_workflow
from app.agents.state import LearnerState

def test_full_agent_workflow_sample_scenario():
    # Setup sample scenario:
    # Student target: Full Stack Developer
    # Python (R=70, I=0.8), SQL (R=60, I=0.6), HTML (R=50, I=0.5),
    # JS (R=80, I=1.0), React (R=75, I=1.0), Node.js (R=70, I=0.9)
    # Learner has:
    # Python: A=80, Q=70, E=60 -> P = 0.2*80 + 0.5*70 + 0.3*60 = 69.0
    # SQL:    A=60, Q=60, E=60 -> P = 60.0
    # HTML:   A=50, Q=50, E=50 -> P = 50.0
    # Missing: JS, React, Node.js -> P = 0.0
    initial_state: LearnerState = {
        "user_id": 1,
        "last_event": "profile_update",
        "event_payload": {
            "candidate_resources": [
                {
                    "id": 101,
                    "skill_id": 4,  # JavaScript
                    "title": "Modern JavaScript From The Beginning",
                    "url": "https://example.com/js",
                    "difficulty": 1,
                    "est_hours": 20.0,
                    "tags": "javascript, web, frontend"
                },
                {
                    "id": 102,
                    "skill_id": 5,  # React
                    "title": "React - The Complete Guide",
                    "url": "https://example.com/react",
                    "difficulty": 2,
                    "est_hours": 25.0,
                    "tags": "react, frontend, javascript"
                },
                {
                    "id": 103,
                    "skill_id": 6,  # Node.js
                    "title": "Node.js API Masterclass",
                    "url": "https://example.com/node",
                    "difficulty": 2,
                    "est_hours": 30.0,
                    "tags": "nodejs, backend, javascript"
                }
            ]
        },
        "skill_profile": {
            1: {"name": "Python", "A_s": 80.0, "Q_s": 70.0, "E_s": 60.0, "P_s": 0.0},
            2: {"name": "SQL", "A_s": 60.0, "Q_s": 60.0, "E_s": 60.0, "P_s": 0.0},
            3: {"name": "HTML", "A_s": 50.0, "Q_s": 50.0, "E_s": 50.0, "P_s": 0.0},
            4: {"name": "JavaScript", "A_s": 0.0, "Q_s": 0.0, "E_s": 0.0, "P_s": 0.0},
            5: {"name": "React", "A_s": 0.0, "Q_s": 0.0, "E_s": 0.0, "P_s": 0.0},
            6: {"name": "Node.js", "A_s": 0.0, "Q_s": 0.0, "E_s": 0.0, "P_s": 0.0},
        },
        "active_career_goal": {
            "role_id": 1,
            "role_title": "Full Stack Developer",
            "requirements": [
                {"skill_id": 1, "skill_name": "Python", "R_s": 70.0, "I_s": 0.8},
                {"skill_id": 2, "skill_name": "SQL", "R_s": 60.0, "I_s": 0.6},
                {"skill_id": 3, "skill_name": "HTML", "R_s": 50.0, "I_s": 0.5},
                {"skill_id": 4, "skill_name": "JavaScript", "R_s": 80.0, "I_s": 1.0},
                {"skill_id": 5, "skill_name": "React", "R_s": 75.0, "I_s": 1.0},
                {"skill_id": 6, "skill_name": "Node.js", "R_s": 70.0, "I_s": 0.9},
            ]
        },
        "bkt_states": {},
        "remediation_skills": []
    }

    final_state = run_agent_workflow(initial_state)

    # 1. Skill analysis check
    skill_profile = final_state["skill_profile"]
    assert skill_profile[1]["P_s"] == 69.0  # Python: 0.2*80 + 0.5*70 + 0.3*60 = 69.0
    assert skill_profile[2]["P_s"] == 60.0
    assert skill_profile[3]["P_s"] == 50.0
    assert skill_profile[4]["P_s"] == 0.0

    # 2. Career matching check
    gap_report = final_state["gap_report"]
    # Python gap = max(0, 70 - 69) = 1.0
    assert gap_report["gaps"][1] == 1.0
    # SQL gap = max(0, 60 - 60) = 0.0
    assert gap_report["gaps"][2] == 0.0
    # HTML gap = max(0, 50 - 50) = 0.0
    assert gap_report["gaps"][3] == 0.0
    # JS gap = max(0, 80 - 0) = 80.0
    assert gap_report["gaps"][4] == 80.0
    # React gap = max(0, 75 - 0) = 75.0
    assert gap_report["gaps"][5] == 75.0
    # Node.js gap = max(0, 70 - 0) = 70.0
    assert gap_report["gaps"][6] == 70.0

    # 3. Recommendations check
    recs = final_state["recommendations"]
    assert len(recs) > 0
    # JavaScript should be ranked #1 because:
    # Priority_JS = (80 * 1.0) / 20 = 4.0
    # Priority_React = (75 * 1.0) / 25 = 3.0
    # Priority_Node = (70 * 0.9) / 30 = 2.1
    assert recs[0]["skill_id"] == 4
    assert recs[0]["priority_score"] == 4.0

    # 4. Mentor check
    assert "mentor_notes" in final_state
    assert len(final_state["mentor_notes"]) > 0

