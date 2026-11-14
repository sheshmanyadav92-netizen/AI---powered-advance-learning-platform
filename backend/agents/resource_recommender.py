from typing import Any

from backend.agents.llm import generate_text, mock_mode
from backend.agents.state import LearnerState


class ResourceRecommenderAgent:
    name = "Resource Recommender Agent"

    def run(self, state: LearnerState, resources: list[Any]) -> list[dict[str, object]]:
        recommendations: list[dict[str, object]] = []
        gaps = state.match.get("gaps", [])
        for gap in gaps:
            skill = str(gap["skill"])
            if gap["status"] == "satisfied":
                continue
            candidates = [
                resource for resource in resources
                if resource.skill.casefold() == skill.casefold()
            ]
            if not candidates:
                continue
            current = int(gap["learner_level"] or 0)
            difficulty = "beginner" if current < 50 else "intermediate" if current < 75 else "advanced"
            candidates.sort(
                key=lambda resource: (
                    0 if resource.difficulty.casefold() == difficulty else 1,
                    0 if resource.type.casefold() in {"tutorial", "course", "doc"} else 1,
                    resource.duration_hours,
                    resource.title.casefold(),
                )
            )
            selected = []
            content = next(
                (item for item in candidates if item.type.casefold() in {"tutorial", "course", "doc"}),
                candidates[0],
            )
            selected.append(content)
            practice = next(
                (item for item in candidates if item.type.casefold() == "exercise"),
                None,
            )
            if practice is not None and practice.id != content.id:
                selected.append(practice)
            for resource in selected:
                why = (
                    f"{resource.difficulty.title()} {resource.type} for {skill}; "
                    f"matches the current proficiency level ({current}/100)."
                )
                if not mock_mode():
                    why = generate_text(
                        f"In one concise sentence, explain why this learning resource fits a learner. "
                        f"Skill: {skill}; current level: {current}/100; "
                        f"resource: {resource.title}; difficulty: {resource.difficulty}; type: {resource.type}."
                    )
                recommendations.append(
                    {
                        "resource_id": resource.id,
                        "title": resource.title,
                        "skill": resource.skill,
                        "type": resource.type,
                        "difficulty": resource.difficulty,
                        "duration_hours": resource.duration_hours,
                        "url": resource.url,
                        "why": why,
                    }
                )
        state.recommendations = recommendations
        return recommendations
