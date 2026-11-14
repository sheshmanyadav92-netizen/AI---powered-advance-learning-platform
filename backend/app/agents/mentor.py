"""Mentor / Orchestrator Agent.
Explanation:
The Mentor/Orchestrator Agent acts as the central cognitive controller and dynamic router of the multi-agent system.
It ingests lifecycle events—such as new diagnostic submissions, goal pivots, or lesson completions—and orchestrates
downstream execution across the specialized agents via a state graph. By monitoring Bayesian mastery thresholds,
it enforces pedagogical adaptivity: when persistent failure patterns emerge (P(L_n) < 0.5 after 3 or more attempts),
it automatically commands the Recommendation Agent to remediate the curriculum with foundational material,
providing supportive, explainable natural-language rationales directly traceable to mathematical models.
"""
from typing import Dict, Any, List
from .state import LearnerState

def mentor_node(state: LearnerState) -> Dict[str, Any]:
    """LangGraph node: orchestrates event flow and provides transparent academic guidance."""
    last_event = state.get("last_event", "status_check")
    gap_report = state.get("gap_report") or {}
    readiness = gap_report.get("readiness", 0.0)
    role_title = gap_report.get("role_title", "your target role")
    remediation_skills: List[int] = state.get("remediation_skills", []) or []
    bkt_states = state.get("bkt_states", {}) or {}

    notes = []

    if last_event == "profile_update":
        notes.append(
            f"Profile refreshed: Verified credentials and self-assessments re-quantified. "
            f"Overall readiness for '{role_title}' stands at {readiness:.1f}%."
        )
    elif last_event == "goal_change":
        notes.append(
            f"Career target switched to '{role_title}'. "
            f"Calculated readiness is {readiness:.1f}% with CosineFit index of {gap_report.get('cosine_fit', 0.0):.4f}."
        )
    elif last_event == "new_assessment":
        notes.append(
            f"Diagnostic assessment processed. Bayesian Knowledge Tracing updated probabilistic skill mastery beliefs."
        )
    elif last_event == "resource_completed":
        notes.append(
            f"Learning activity completed and logged. Adaptive pathways updated."
        )

    # Check for adaptive remediation alerts
    if remediation_skills:
        remed_names = []
        for sid in remediation_skills:
            info = bkt_states.get(sid, {})
            p_m = info.get("p_mastery", 0.0)
            remed_names.append(f"Skill #{sid} (P(L)={p_m:.2f})")
        
        notes.append(
            f"PEDAGOGICAL ADAPTATION TRIGGERED: Persistent difficulty detected on {', '.join(remed_names)} "
            f"(P(L_n) < 0.50 after 3+ attempts). Curriculum difficulty has been dynamically scaffolded down by 1 level."
        )
    else:
        notes.append("Learning trajectory is on track with steady Bayesian mastery gains.")

    return {
        "mentor_notes": " ".join(notes)
    }

