from math import ceil
from typing import Any

from sqlalchemy.orm import Session

from backend.agents.state import LearnerState
from backend.models import Learner, Resource, RoadmapItem

FULL_STACK_CHAIN = ["JavaScript", "React", "Node.js", "Express", "Full Stack Project"]


class LearningPathPlannerAgent:
    name = "Learning Path Planner Agent"

    def run(
        self,
        db: Session,
        learner: Learner,
        state: LearnerState,
        role: Any,
        resources: list[Resource],
        *,
        remedial_skill: str | None = None,
        strong_skill: str | None = None,
    ) -> list[dict[str, object]]:
        old_items = sorted(learner.roadmap_items, key=lambda item: item.order_index)
        completed_ids = {
            item.resource_id for item in old_items if item.status == "done" and item.resource_id
        }
        mastered = state.mastered_skills | {
            resource.skill.casefold()
            for item in old_items
            if item.status == "done" and item.resource is not None
            for resource in [item.resource]
        }
        required = {item.skill: item for item in role.skills}
        ordered_skills = [item.skill for item in sorted(role.skills, key=lambda item: (-item.weight, item.skill.casefold()))]
        if role.name.casefold() == "full stack developer":
            ordered_skills = [
                skill for skill in FULL_STACK_CHAIN[:-1]
                if skill in required or skill == "Express"
            ] + [
                skill for skill in ordered_skills if skill not in FULL_STACK_CHAIN
            ] + ["Full Stack Project"]

        by_skill: dict[str, list[Resource]] = {}
        for resource in resources:
            by_skill.setdefault(resource.skill.casefold(), []).append(resource)

        recommendations = {
            int(item["resource_id"]): item
            for item in state.recommendations
            if item.get("resource_id") is not None
        }
        planned: list[tuple[str, Resource, str, bool]] = []

        def append_resources(skill_name: str, remedial: bool = False) -> None:
            skill_key = skill_name.casefold()
            candidates = by_skill.get(skill_key, [])
            if not candidates:
                return
            if remedial:
                candidates = sorted(
                    candidates,
                    key=lambda item: (
                        0 if item.difficulty.casefold() == "beginner" else 1,
                        0 if item.type.casefold() == "exercise" else 1,
                        item.duration_hours,
                    ),
                )
                selected = [
                    item for item in candidates
                    if item.difficulty.casefold() == "beginner"
                ][:2]
            elif skill_name == "Full Stack Project":
                selected = [
                    item for item in candidates if item.type.casefold() == "project"
                ][:1]
            else:
                choice = next(
                    (
                        resource for resource in candidates
                        if resource.id in recommendations
                    ),
                    None,
                )
                if choice is None:
                    choice = min(
                        candidates,
                        key=lambda item: (
                            0 if item.difficulty.casefold() == "beginner" else 1,
                            item.duration_hours,
                        ),
                    )
                selected = [choice]
            for resource in selected:
                phase = (
                    f"Remedial: {skill_name}"
                    if remedial
                    else "Capstone Project"
                    if skill_name == "Full Stack Project"
                    else f"Build {skill_name}"
                )
                planned.append((skill_name, resource, phase, remedial))

        if remedial_skill:
            append_resources(remedial_skill, remedial=True)
        for skill_name in ordered_skills:
            skill_key = skill_name.casefold()
            if remedial_skill and skill_key == remedial_skill.casefold():
                continue
            if skill_key in mastered and skill_key != (strong_skill or "").casefold():
                continue
            if skill_name in {"Express", "Full Stack Project"} and role.name.casefold() != "full stack developer":
                continue
            if skill_name not in required and skill_name not in {"Express", "Full Stack Project"}:
                continue
            if strong_skill and skill_key == strong_skill.casefold():
                candidates = by_skill.get(skill_key, [])
                advanced = next(
                    (
                        item for item in candidates
                        if item.difficulty.casefold() == "advanced"
                    ),
                    None,
                )
                if advanced is not None:
                    planned.append(
                        (skill_name, advanced, f"Advanced challenge: {skill_name}", False)
                    )
                continue
            if skill_key == (remedial_skill or "").casefold():
                append_resources(skill_name, remedial=True)
            else:
                append_resources(skill_name)

        for item in old_items:
            db.delete(item)
        db.flush()
        result = []
        hours_per_week = max(float(learner.weekly_hours), 0.25)
        for index, (skill_name, resource, phase, remedial) in enumerate(planned):
            status = "done" if resource.id in completed_ids and not remedial else "not_started"
            item = RoadmapItem(
                learner_id=learner.id,
                resource_id=resource.id,
                phase=phase,
                order_index=index,
                status=status,
            )
            db.add(item)
            result.append(
                {
                    "order": index + 1,
                    "phase": phase,
                    "skill": skill_name,
                    "resource_id": resource.id,
                    "title": resource.title,
                    "type": resource.type,
                    "difficulty": "beginner" if remedial else resource.difficulty,
                    "duration_hours": resource.duration_hours,
                    "estimated_weeks": ceil(resource.duration_hours / hours_per_week),
                    "status": status,
                    "remedial": remedial,
                    "prerequisites": (
                        FULL_STACK_CHAIN[: FULL_STACK_CHAIN.index(skill_name)]
                        if skill_name in FULL_STACK_CHAIN
                        else []
                    ),
                }
            )
        state.roadmap = result
        return result
