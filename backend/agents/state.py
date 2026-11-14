from dataclasses import dataclass, field
from typing import Any


@dataclass
class LearnerState:
    learner_id: int
    name: str
    goal_role: str | None
    weekly_hours: float
    skills: dict[str, int]
    profile: dict[str, Any] = field(default_factory=dict)
    match: dict[str, Any] = field(default_factory=dict)
    roadmap: list[dict[str, Any]] = field(default_factory=list)
    recommendations: list[dict[str, Any]] = field(default_factory=list)
    assessment: dict[str, Any] = field(default_factory=dict)
    event: str = "roadmap_requested"
    messages: list[dict[str, str]] = field(default_factory=list)

    @property
    def mastered_skills(self) -> set[str]:
        return {name.casefold() for name, level in self.skills.items() if level >= 70}
