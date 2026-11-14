"""Shared LearnerState object passed across all LangGraph agent nodes.
"""
from typing import Dict, Any, List, Optional
from typing_extensions import TypedDict

class LearnerState(TypedDict, total=False):
    user_id: int
    last_event: str  # "profile_update", "goal_change", "new_assessment", "resource_completed"
    event_payload: Dict[str, Any]
    
    # Skill analysis output
    skill_profile: Dict[int, Dict[str, Any]]  # skill_id -> {name, A_s, Q_s, E_s, P_s}
    
    # Career matching output
    active_career_goal: Optional[Dict[str, Any]]  # {role_id, role_title, requirements: [...]}
    gap_report: Optional[Dict[str, Any]]  # {readiness, cosine_fit, gaps: {skill_id: G_s}}
    
    # Progress tracking / BKT output
    bkt_states: Dict[int, Dict[str, Any]]  # skill_id -> {p_mastery, attempts_count, needs_remediation}
    
    # Remediation flags
    remediation_skills: List[int]  # skill_ids needing difficulty lowered by 1
    
    # Recommendation output
    recommendations: List[Dict[str, Any]]
    
    # Mentor guidance
    mentor_notes: str
    next_step: Optional[str]

