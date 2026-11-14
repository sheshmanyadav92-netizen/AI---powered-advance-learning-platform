from collections.abc import Iterable
from typing import Any


def calculate_role_match(learner_skills: Iterable[Any], role: Any) -> dict[str, object]:
    """Calculate a normalized weighted score and classify role-skill gaps."""
    levels = {skill.skill.casefold(): int(skill.level) for skill in learner_skills}
    requirements = list(role.skills)
    total_weight = sum(float(item.weight) for item in requirements)
    weighted_score = 0.0
    gaps = []

    for requirement in requirements:
        skill_name = requirement.skill
        learner_level = levels.get(skill_name.casefold())
        required_level = int(requirement.required_level)
        weight = float(requirement.weight)
        weighted_score += (
            min(learner_level / required_level, 1.0) * weight
            if learner_level is not None and required_level > 0
            else 0.0
        )
        if learner_level is None:
            status = "missing"
        elif learner_level < required_level:
            status = "weak"
        else:
            status = "satisfied"
        gaps.append(
            {
                "skill": skill_name,
                "required_level": required_level,
                "learner_level": learner_level,
                "weight": weight,
                "status": status,
            }
        )

    match_percent = round(weighted_score / total_weight * 100, 2) if total_weight else 0.0
    return {
        "role_id": role.id,
        "role": role.name,
        "match_percent": match_percent,
        "gaps": gaps,
        "missing": [gap["skill"] for gap in gaps if gap["status"] == "missing"],
        "weak": [gap["skill"] for gap in gaps if gap["status"] == "weak"],
        "satisfied": [gap["skill"] for gap in gaps if gap["status"] == "satisfied"],
    }


def compare_roles(
    learner_skills: Iterable[Any], roles: Iterable[Any]
) -> list[dict[str, object]]:
    skills = list(learner_skills)
    matches = [calculate_role_match(skills, role) for role in roles]
    return sorted(matches, key=lambda match: (-float(match["match_percent"]), str(match["role"])))
