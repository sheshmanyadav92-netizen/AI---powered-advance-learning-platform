"""Deterministic roadmap and performance metrics.
Formulas:
- Completion Rate = (Completed Resources / Assigned Resources) * 100
- Assessment Average = Sum(Assessment Scores) / Number of Assessments
- Learning Hours = Sum(Time Spent in Minutes) / 60
- Remaining Estimated Hours = Sum(Estimated Hours of Incomplete Recommended Resources)
- Mastery Achievement Rate = (Number of Required Skills with P(Ln) >= 0.80 / Number of Required Skills) * 100
"""
from typing import List, Dict, Any

def calculate_completion_rate(completed_count: int, total_assigned: int) -> float:
    if total_assigned <= 0:
        return 0.0
    return round(min(100.0, max(0.0, (completed_count / total_assigned) * 100.0)), 2)

def calculate_assessment_average(scores: List[float]) -> float:
    if not scores:
        return 0.0
    return round(sum(scores) / len(scores), 2)

def calculate_learning_hours(time_spent_minutes: List[int]) -> float:
    if not time_spent_minutes:
        return 0.0
    return round(sum(time_spent_minutes) / 60.0, 2)

def calculate_remaining_hours(incomplete_resources: List[Dict[str, Any]]) -> float:
    if not incomplete_resources:
        return 0.0
    total = sum(float(r.get("est_hours", 0.0)) for r in incomplete_resources)
    return round(total, 2)

def calculate_mastery_achievement_rate(p_mastery_values: List[float], total_required: int) -> float:
    if total_required <= 0:
        return 0.0
    mastered = sum(1 for p in p_mastery_values if float(p) >= 0.80)
    return round((mastered / total_required) * 100.0, 2)
