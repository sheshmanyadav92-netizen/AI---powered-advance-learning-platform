from typing import Any

from backend.agents.state import LearnerState
from backend.services.career_matching import calculate_role_match, compare_roles


class CareerMatchingAgent:
    name = "Career Matching Agent"

    def run(self, state: LearnerState, roles: list[Any]) -> dict[str, object]:
        if not roles:
            state.match = {"role": None, "matches": [], "gaps": []}
            return state.match
        matches = compare_roles(
            [type("Skill", (), {"skill": key, "level": value}) for key, value in state.skills.items()],
            roles,
        )
        role = next(
            (item for item in roles if item.name.casefold() == (state.goal_role or "").casefold()),
            None,
        )
        if role is None:
            role = roles[0]
            state.goal_role = role.name
        state.match = calculate_role_match(
            [type("Skill", (), {"skill": key, "level": value}) for key, value in state.skills.items()],
            role,
        )
        state.match["matches"] = matches
        return state.match
