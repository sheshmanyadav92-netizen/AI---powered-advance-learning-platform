from collections.abc import Iterable
from typing import Any


def analyze_skills(skills: Iterable[Any]) -> dict[str, object]:
    """Classify the learner's recorded skills using their current proficiency."""
    strengths = []
    weaknesses = []
    statuses = []

    for skill in skills:
        level = int(skill.level)
        if level >= 70:
            status = "strength"
            strengths.append(skill.skill)
        elif level < 50:
            status = "weakness"
            weaknesses.append(skill.skill)
        else:
            status = "developing"
        statuses.append({"skill": skill.skill, "level": level, "status": status})

    statuses.sort(key=lambda item: str(item["skill"]).casefold())
    return {
        "strengths": sorted(strengths, key=str.casefold),
        "weaknesses": sorted(weaknesses, key=str.casefold),
        "skills": statuses,
    }
