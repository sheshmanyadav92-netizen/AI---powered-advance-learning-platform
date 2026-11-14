"""Recommendation Agent.
Explanation:
The Recommendation Agent generates an optimal, return-on-investment (ROI) prioritized learning roadmap.
Recognizing that human study time is finite, it ranks target resources using an efficiency formula
(Priority_s = (G_s * I_s) / T_s) where priority scales directly with skill gap magnitude and role criticality
while penalizing time commitment (T_s). When candidate resources share similar priority tiers, the agent
executes tag-based vector cosine similarity to match curricular prerequisites. Furthermore, it incorporates
pedagogical adaptivity: if the learner experiences chronic difficulty, it adjusts instructional difficulty
downward by one tier to scaffold foundational competencies within Vygotsky's Zone of Proximal Development.
"""
from typing import Dict, Any, List
from .state import LearnerState
from ..formulas.recommendation import calculate_recommendation_priority, calculate_tag_similarity

def recommendation_node(state: LearnerState) -> Dict[str, Any]:
    """LangGraph node: ranks resources based on skill gaps, priority formula, and tag similarity."""
    gap_report = state.get("gap_report") or {}
    gaps: Dict[int, float] = gap_report.get("gaps", {})
    details: List[Dict[str, Any]] = gap_report.get("details", [])
    candidate_resources: List[Dict[str, Any]] = state.get("event_payload", {}).get("candidate_resources", [])
    remediation_skills: List[int] = state.get("remediation_skills", []) or []
    skill_profile = state.get("skill_profile", {}) or {}

    # Map skill details
    skill_info_map = {d["skill_id"]: d for d in details}

    ranked_recommendations: List[Dict[str, Any]] = []

    for res in candidate_resources:
        skill_id = res.get("skill_id")
        skill_meta = skill_info_map.get(skill_id)
        if not skill_meta:
            continue

        g_s = float(skill_meta["G_s"])
        # If no gap, no recommendation needed
        if g_s <= 0.0:
            continue

        i_s = float(skill_meta["I_s"])
        t_s = float(res.get("est_hours", 10.0))
        difficulty = int(res.get("difficulty", 1))

        # Learner estimated level for this skill: 1 (0-35), 2 (36-70), 3 (71-100)
        p_s = float(skill_meta["P_s"])
        learner_level = 1 if p_s < 35 else (2 if p_s < 70 else 3)
        
        # Max allowed difficulty is learner_level + 1
        max_difficulty = learner_level + 1

        # If remediation is needed for this skill, lower allowed difficulty by 1 level
        if skill_id in remediation_skills:
            max_difficulty = max(1, max_difficulty - 1)

        # Filter out resources that are too advanced
        if difficulty > max_difficulty:
            continue

        # Priority calculation: Priority_s = (G_s * I_s) / T_s
        priority = calculate_recommendation_priority(G_s=g_s, I_s=i_s, T_s=t_s)

        # Tag-based cosine similarity between gap description / target skill and resource tags
        res_tags = [t.strip() for t in res.get("tags", "").split(",") if t.strip()]
        gap_tags = [skill_meta["skill_name"].lower(), "fundamentals", "core"]
        tag_sim = calculate_tag_similarity(gap_tags, res_tags)

        ranked_recommendations.append({
            "id": res.get("id"),
            "resource_id": res.get("id"),
            "skill_id": skill_id,
            "skill_name": skill_meta["skill_name"],
            "resource_title": res.get("title"),
            "resource_url": res.get("url"),
            "difficulty": difficulty,
            "est_hours": t_s,
            "tags": res_tags,
            "priority_score": priority,
            "tag_similarity": tag_sim,
            "status": "active"
        })

    # Sort primarily by Priority_s descending, break ties with tag_similarity descending
    ranked_recommendations.sort(
        key=lambda r: (r["priority_score"], r["tag_similarity"]),
        reverse=True
    )

    return {"recommendations": ranked_recommendations}

