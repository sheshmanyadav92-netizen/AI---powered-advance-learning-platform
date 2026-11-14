"""Skill gap score formula implementation with full float precision.
Formula:
G_s = max(0, R_s - P_s)
where:
- R_s: required proficiency for the skill in the target role (0-100)
- P_s: learner's current proficiency score (0-100)
"""

def calculate_skill_gap(R_s: float, P_s: float) -> float:
    r = max(0.0, min(100.0, float(R_s)))
    p = max(0.0, min(100.0, float(P_s)))
    return max(0.0, r - p)
