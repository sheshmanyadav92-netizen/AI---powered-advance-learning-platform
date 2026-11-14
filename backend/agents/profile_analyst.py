from backend.agents.state import LearnerState


class ProfileSkillAnalystAgent:
    name = "Profile & Skill Analyst Agent"

    def run(self, state: LearnerState) -> dict[str, object]:
        state.profile = {
            "learner": state.name,
            "goal_role": state.goal_role,
            "weekly_hours": state.weekly_hours,
            "strengths": sorted(name for name, level in state.skills.items() if level >= 70),
            "developing": sorted(
                name for name, level in state.skills.items() if 50 <= level < 70
            ),
            "gaps": sorted(name for name, level in state.skills.items() if level < 50),
            "mastered_skills": sorted(
                name for name, level in state.skills.items() if level >= 70
            ),
        }
        return state.profile
