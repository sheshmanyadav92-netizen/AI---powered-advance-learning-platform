from backend.agents.llm import generate_text, mock_mode
from backend.agents.state import LearnerState


class MentorAgent:
    name = "Mentor Agent"

    def run(self, state: LearnerState, message: str) -> dict[str, str]:
        context = {
            "profile": state.profile,
            "career_match": state.match,
            "skill_gaps": state.match.get("gaps", []),
            "roadmap": state.roadmap,
            "latest_assessment": state.assessment,
        }
        prompt = (
            "You are a supportive, practical learning mentor. Answer based only on the supplied learner data. "
            "If the data does not answer something, say so. Keep it concise.\n"
            f"Learner data: {context}\nLearner message: {message}"
        )
        if mock_mode():
            if state.assessment.get("status") == "struggling":
                answer = (
                    f"Your {state.assessment['skill']} score was {state.assessment['score']:.0f}%. "
                    "I added a beginner refresher and practice before dependent topics. "
                    "Work through those, then retake the quiz."
                )
            elif state.event == "goal_changed":
                answer = (
                    f"I rebuilt your plan for {state.goal_role}. Skills at 70% or higher are reused, "
                    "and the remaining roadmap now focuses on this goal."
                )
            elif state.event == "assessment_strong":
                answer = (
                    f"Strong work on {state.assessment.get('skill', 'this skill')}! "
                    "I condensed its beginner content and added a stretch task."
                )
            elif state.roadmap:
                answer = (
                    f"Your plan targets {state.goal_role or 'your selected role'} at "
                    f"{state.weekly_hours:g} hours per week. "
                    f"Start with {state.roadmap[0]['title']}."
                )
            else:
                answer = f"I can help with {state.goal_role or 'your learning goal'}. Tell me what you would like to focus on."
        else:
            answer = generate_text(prompt)
        return {"message": answer}
