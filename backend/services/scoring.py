from collections.abc import Iterable
from math import ceil
from typing import Any

from backend.services.career_matching import calculate_role_match

STRENGTH_THRESHOLD = 70
WEAKNESS_THRESHOLD = 50
QUIZ_PASS_THRESHOLD = 60
QUIZ_EXCELLENT_THRESHOLD = 85


def readiness_score(skills: Iterable[Any], role: Any) -> float:
    levels = {skill.skill.casefold(): int(skill.level) for skill in skills}
    requirements = list(role.skills)
    total_weight = sum(float(item.weight) for item in requirements)
    if not total_weight:
        return 0.0
    weighted_level = sum(
        min(levels.get(item.skill.casefold(), 0), 100) * float(item.weight)
        for item in requirements
    )
    return round(weighted_level / total_weight, 2)


def gap_priority(gap: dict[str, Any]) -> float:
    """Prioritize large, weighted gaps while keeping the result comparable."""
    required = int(gap["required_level"])
    current = int(gap["learner_level"] or 0)
    if required <= 0:
        return 0.0
    return round(float(gap["weight"]) * max(required - current, 0) / required * 100, 2)


def rank_resource(resource: Any, priority: float) -> float:
    duration = max(float(resource.duration_hours), 0.25)
    difficulty_multiplier = {
        "beginner": 1.15,
        "intermediate": 1.0,
        "advanced": 0.85,
    }.get(resource.difficulty.casefold(), 1.0)
    return round(priority * difficulty_multiplier / duration, 4)


def completion_weeks(hours_remaining: float, weekly_hours: float) -> int:
    if hours_remaining <= 0:
        return 0
    return ceil(hours_remaining / max(weekly_hours, 0.25))


def resource_completion_level(current_level: int, duration_hours: float) -> int:
    earned = max(1, round(duration_hours * 2))
    return min(100, current_level + earned)
