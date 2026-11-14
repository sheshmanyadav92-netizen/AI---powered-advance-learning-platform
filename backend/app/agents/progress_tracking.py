"""Progress Tracking Agent.
Explanation:
The Progress Tracking Agent maintains a probabilistic latent cognitive model of the learner's mastery
through Bayesian Knowledge Tracing (BKT; Corbett & Anderson, 1994). Accounting for the realistic stochasticity
of human assessment performance—specifically the probability of guessing (P(G)=0.2) when unmastered and
slipping (P(S)=0.1) when mastered—the agent updates its posterior belief of skill mastery (P(L_n)) upon
every assessment observation, subsequently applying the state transition parameter (P(T)=0.15).
This rigorous mathematical tracking protects against illusory mastery while systematically detecting persistent
deficits that trigger scaffolded remediation.
"""
from typing import Dict, Any, List
from .state import LearnerState
from ..formulas.bkt import bkt_update, is_remediation_needed, DEFAULT_P_L0, DEFAULT_P_T, DEFAULT_P_G, DEFAULT_P_S

def progress_tracking_node(state: LearnerState) -> Dict[str, Any]:
    """LangGraph node: updates BKT belief and tracks remediation flags."""
    event_payload = state.get("event_payload") or {}
    bkt_states = dict(state.get("bkt_states", {}) or {})
    remediation_skills: List[int] = list(state.get("remediation_skills", []) or [])

    # Extract assessment event details
    skill_id = event_payload.get("skill_id")
    score = event_payload.get("score")  # 0 to 100

    if skill_id is not None and score is not None:
        skill_id = int(skill_id)
        # Binary correctness threshold: score >= 60 is considered correct evidence
        is_correct = float(score) >= 60.0

        current_entry = bkt_states.get(skill_id, {
            "p_mastery": DEFAULT_P_L0,
            "p_T": DEFAULT_P_T,
            "p_G": DEFAULT_P_G,
            "p_S": DEFAULT_P_S,
            "attempts_count": 0,
            "needs_remediation": False
        })

        p_prev = float(current_entry.get("p_mastery", DEFAULT_P_L0))
        attempts = int(current_entry.get("attempts_count", 0)) + 1
        
        p_next = bkt_update(
            p_prev=p_prev,
            is_correct=is_correct,
            p_T=current_entry.get("p_T", DEFAULT_P_T),
            p_G=current_entry.get("p_G", DEFAULT_P_G),
            p_S=current_entry.get("p_S", DEFAULT_P_S)
        )

        remediation = is_remediation_needed(p_mastery=p_next, attempts_count=attempts)

        current_entry["p_mastery"] = p_next
        current_entry["attempts_count"] = attempts
        current_entry["needs_remediation"] = remediation
        bkt_states[skill_id] = current_entry

        if remediation and skill_id not in remediation_skills:
            remediation_skills.append(skill_id)
        elif not remediation and skill_id in remediation_skills:
            remediation_skills.remove(skill_id)

    return {
        "bkt_states": bkt_states,
        "remediation_skills": remediation_skills
    }

