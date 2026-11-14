"""Career Matching Agent.
Explanation:
The Career Matching Agent evaluates learner competency vectors against enterprise role requirements.
By mapping current skill proficiencies (P_s) to target role expectations (R_s), it determines individual
skill gaps (G_s = max(0, R_s - P_s)) while calculating an importance-weighted overall readiness index
(Readiness = min(100, [sum(P_s * I_s) / sum(R_s * I_s)] * 100)). Additionally, it evaluates a
multidimensional vector cosine similarity (CareerFit = (P . R) / (||P|| * ||R||)), providing both
a human-interpretable percentage for students and an academically defensible vector-space comparison
metric for curricular validation.
"""
from typing import Dict, Any, List, Tuple
from .state import LearnerState
from ..formulas.gap import calculate_skill_gap
from ..formulas.readiness import calculate_career_readiness, calculate_cosine_fit

def career_matching_node(state: LearnerState) -> Dict[str, Any]:
    """LangGraph node: calculates G_s for each required skill, overall Readiness %, and CosineFit."""
    active_goal = state.get("active_career_goal")
    skill_profile = state.get("skill_profile", {}) or {}

    if not active_goal:
        return {
            "gap_report": {
                "role_id": None,
                "role_title": "No active career goal selected",
                "readiness": 0.0,
                "cosine_fit": 0.0,
                "gaps": {},
                "details": []
            }
        }

    requirements: List[Dict[str, Any]] = active_goal.get("requirements", [])
    
    skills_data_for_readiness: List[Tuple[float, float, float]] = []
    p_vector: List[float] = []
    r_vector: List[float] = []
    
    gaps: Dict[int, float] = {}
    details: List[Dict[str, Any]] = []

    for req in requirements:
        skill_id = req["skill_id"]
        skill_name = req["skill_name"]
        r_s = float(req["R_s"])
        i_s = float(req["I_s"])
        
        # Learner proficiency, default 0 if unlearned
        learner_info = skill_profile.get(skill_id, {})
        p_s = float(learner_info.get("P_s", 0.0))
        
        g_s = calculate_skill_gap(R_s=r_s, P_s=p_s)
        gaps[skill_id] = g_s
        
        skills_data_for_readiness.append((p_s, r_s, i_s))
        p_vector.append(p_s)
        r_vector.append(r_s)
        
        details.append({
            "skill_id": skill_id,
            "skill_name": skill_name,
            "P_s": p_s,
            "R_s": r_s,
            "I_s": i_s,
            "G_s": g_s
        })

    readiness = calculate_career_readiness(skills_data_for_readiness)
    cosine_fit = calculate_cosine_fit(p_vector, r_vector)

    return {
        "gap_report": {
            "role_id": active_goal.get("role_id"),
            "role_title": active_goal.get("role_title", "Unknown Role"),
            "readiness": readiness,
            "cosine_fit": cosine_fit,
            "gaps": gaps,
            "details": details
        }
    }

