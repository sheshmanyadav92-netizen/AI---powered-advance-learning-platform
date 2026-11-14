"""Skill Analysis Agent.
Explanation:
The Skill Analysis Agent is responsible for continuous multi-source competency quantification.
Rather than relying solely on self-reported proficiencies which are prone to Dunning-Kruger cognitive bias,
this agent synthesizes subjective self-assessments (A_s), objective assessment/quiz performance (Q_s),
and verifiable project or credential evidence (E_s) via an empirically weighted linear combination:
P_s = w1 * A_s + w2 * Q_s + w3 * E_s (with w1=0.2, w2=0.5, w3=0.3).
This ensures the learner's baseline proficiency profile (P_s) reflects grounded, validated capability.
"""
from typing import Dict, Any
from .state import LearnerState
from ..formulas.proficiency import calculate_skill_proficiency

def skill_analysis_node(state: LearnerState) -> Dict[str, Any]:
    """LangGraph node: calculates P_s for all learner skills."""
    current_profile = state.get("skill_profile", {}) or {}
    updated_profile: Dict[int, Dict[str, Any]] = {}

    for skill_id, data in current_profile.items():
        a_s = float(data.get("A_s", 0.0))
        q_s = float(data.get("Q_s", 0.0))
        e_s = float(data.get("E_s", 0.0))
        
        p_s = calculate_skill_proficiency(A_s=a_s, Q_s=q_s, E_s=e_s)
        
        updated_entry = dict(data)
        updated_entry["P_s"] = p_s
        updated_profile[skill_id] = updated_entry

    return {"skill_profile": updated_profile}

