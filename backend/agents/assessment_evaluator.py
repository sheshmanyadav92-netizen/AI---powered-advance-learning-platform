from typing import Any

from backend.agents.state import LearnerState


class AssessmentProgressEvaluatorAgent:
    name = "Assessment & Progress Evaluator Agent"

    def run(
        self,
        state: LearnerState,
        skill: str,
        score: float,
        questions: list[dict[str, Any]] | None = None,
    ) -> dict[str, object]:
        previous = next(
            (level for name, level in state.skills.items() if name.casefold() == skill.casefold()),
            0,
        )
        state.skills[skill] = round(score)
        state.assessment = {
            "skill": skill,
            "score": round(score, 1),
            "previous_level": previous,
            "updated_level": round(score),
            "status": "struggling" if score < 60 else "fast" if score > 85 else "developing",
            "questions": questions or [],
        }
        return state.assessment
