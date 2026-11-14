from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.models import (
    AgentTrace,
    Assessment,
    AssessmentResult,
    Learner,
    LearnerSkill,
    ProgressLog,
    Resource,
    RoadmapItem,
    Role,
)
from backend.services.career_matching import calculate_role_match, compare_roles
from backend.services.scoring import (
    QUIZ_EXCELLENT_THRESHOLD,
    QUIZ_PASS_THRESHOLD,
    STRENGTH_THRESHOLD,
    WEAKNESS_THRESHOLD,
    completion_weeks,
    gap_priority,
    rank_resource,
    readiness_score,
)


def _learner(db: Session, learner_id: int) -> Learner | None:
    return db.scalar(
        select(Learner)
        .options(
            selectinload(Learner.skills),
            selectinload(Learner.roadmap_items).selectinload(RoadmapItem.resource),
        )
        .where(Learner.id == learner_id)
    )


def _role(db: Session, name: str | None) -> Role | None:
    if not name:
        return None
    return db.scalar(
        select(Role).options(selectinload(Role.skills)).where(Role.name == name)
    )


def _distinct_streak(logs: list[ProgressLog], today: datetime) -> int:
    active_dates = {log.logged_at.date() for log in logs}
    day = today.date()
    if day not in active_dates:
        day -= timedelta(days=1)
    streak = 0
    while day in active_dates:
        streak += 1
        day -= timedelta(days=1)
    return streak


def build_dashboard(db: Session, learner_id: int) -> dict[str, Any] | None:
    learner = _learner(db, learner_id)
    if learner is None:
        return None

    roles = list(
        db.scalars(select(Role).options(selectinload(Role.skills)).order_by(Role.name))
    )
    target_role = _role(db, learner.goal_role)
    now = datetime.utcnow()
    skills_by_name = {skill.skill.casefold(): skill for skill in learner.skills}

    match = calculate_role_match(learner.skills, target_role) if target_role else None
    readiness = readiness_score(learner.skills, target_role) if target_role else 0.0
    role_requirements = list(target_role.skills) if target_role else []
    gaps = list(match["gaps"]) if match else []
    for gap in gaps:
        gap["priority"] = gap_priority(gap)
    gaps.sort(key=lambda gap: (-float(gap["priority"]), str(gap["skill"])))

    resource_catalog = list(db.scalars(select(Resource).order_by(Resource.title)))
    completed_resource_ids = {
        item.resource_id
        for item in learner.roadmap_items
        if item.resource_id is not None and item.status == "done"
    }
    ranked_resources = []
    for gap in gaps:
        if gap["status"] == "satisfied":
            continue
        candidates = [
            resource
            for resource in resource_catalog
            if resource.skill.casefold() == str(gap["skill"]).casefold()
            and resource.id not in completed_resource_ids
        ]
        if not candidates:
            continue
        resource = max(candidates, key=lambda item: rank_resource(item, float(gap["priority"])))
        gap["recommended_resource"] = {
            "id": resource.id,
            "title": resource.title,
            "url": resource.url,
            "duration_hours": resource.duration_hours,
        }
        ranked_resources.append(
            {
                "resource": resource,
                "gap": gap,
                "rank": rank_resource(resource, float(gap["priority"])),
            }
        )
    ranked_resources.sort(
        key=lambda item: (-float(item["rank"]), str(item["resource"].title))
    )
    best_action = None
    if ranked_resources:
        chosen = ranked_resources[0]
        resource = chosen["resource"]
        gap = chosen["gap"]
        current = gap["learner_level"]
        reason = (
            f"{gap['skill']} has the largest weighted gap"
            if current is None
            else f"Build {gap['skill']} from {current} toward the role target of {gap['required_level']}"
        )
        best_action = {
            "resource_id": resource.id,
            "title": resource.title,
            "type": resource.type,
            "skill": resource.skill,
            "difficulty": resource.difficulty,
            "duration_hours": resource.duration_hours,
            "url": resource.url,
            "reason": reason,
            "rank_score": chosen["rank"],
        }

    roadmap = sorted(
        learner.roadmap_items,
        key=lambda item: (item.order_index, item.id),
    )
    total_hours = sum(
        float(item.resource.duration_hours)
        for item in roadmap
        if item.resource is not None
    )
    completed_hours = sum(
        float(item.resource.duration_hours)
        for item in roadmap
        if item.resource is not None and item.status == "done"
    )
    remaining_hours = max(total_hours - completed_hours, 0.0)
    roadmap_completion = (
        round(completed_hours / total_hours * 100, 1) if total_hours else 0.0
    )
    weeks_remaining = completion_weeks(remaining_hours, learner.weekly_hours)

    phase_items: dict[str, list[RoadmapItem]] = defaultdict(list)
    for item in roadmap:
        phase_items[item.phase].append(item)
    phases = []
    current_phase_found = False
    for phase_name, items in phase_items.items():
        phase_hours = sum(
            float(item.resource.duration_hours)
            for item in items
            if item.resource is not None
        )
        phase_done_hours = sum(
            float(item.resource.duration_hours)
            for item in items
            if item.resource is not None and item.status == "done"
        )
        completed = bool(items) and all(item.status == "done" for item in items)
        if completed:
            phase_status = "completed"
        elif not current_phase_found:
            phase_status = "current"
            current_phase_found = True
        else:
            phase_status = "upcoming"
        phases.append(
            {
                "name": phase_name,
                "completion_percent": (
                    round(phase_done_hours / phase_hours * 100)
                    if phase_hours
                    else 0
                ),
                "status": phase_status,
                "items": [
                    {
                        "id": item.id,
                        "resource_id": item.resource_id,
                        "title": item.resource.title if item.resource else item.phase,
                        "skill": item.resource.skill if item.resource else None,
                        "status": item.status,
                        "remedial": item.phase.casefold().startswith("remedial"),
                    }
                    for item in items
                ],
            }
        )

    start_of_week = now - timedelta(days=7)
    progress_logs = list(
        db.scalars(
            select(ProgressLog)
            .where(ProgressLog.learner_id == learner_id)
            .order_by(ProgressLog.logged_at.desc())
        )
    )
    recent_logs = [log for log in progress_logs if log.logged_at >= start_of_week]
    hours_this_week = round(sum(float(log.hours_spent) for log in recent_logs), 1)
    results = list(
        db.scalars(
            select(AssessmentResult)
            .options(selectinload(AssessmentResult.assessment))
            .where(AssessmentResult.learner_id == learner_id)
            .order_by(AssessmentResult.completed_at.desc())
        )
    )
    average_quiz_score = (
        round(sum(float(result.score) for result in results) / len(results), 1)
        if results
        else None
    )
    mastered_count = sum(
        skill.level >= STRENGTH_THRESHOLD for skill in learner.skills
    )
    streak_days = _distinct_streak(progress_logs, now)

    traces = list(
        db.scalars(
            select(AgentTrace)
            .where(AgentTrace.learner_id == learner_id)
            .order_by(AgentTrace.created_at.desc(), AgentTrace.id.desc())
            .limit(30)
        )
    )
    traces.reverse()
    history = [
        {
            "date": trace.created_at.isoformat(),
            "readiness": round(
                float(trace.readiness_percent)
                if trace.readiness_percent is not None
                else readiness,
                1,
            ),
            "event": trace.output or trace.agent_name,
            "kind": (
                "goal_changed"
                if "goal" in (trace.input or "").casefold()
                else "resource_completed"
                if "resource" in (trace.input or "").casefold()
                else "quiz"
                if "quiz" in (trace.input or "").casefold()
                else "activity"
            ),
        }
        for trace in traces
    ]
    if not history:
        history = [{"date": now.isoformat(), "readiness": readiness, "event": "Current readiness", "kind": "current"}]

    recent_quizzes = [
        {
            "assessment_id": result.assessment_id,
            "title": result.assessment.title,
            "skill": result.assessment.skill,
            "score": round(float(result.score), 1),
            "completed_at": result.completed_at.isoformat(),
        }
        for result in results[:8]
    ]
    assessments = list(
        db.scalars(select(Assessment).order_by(Assessment.skill))
    )
    quiz_catalog = [
        {
            "id": assessment.id,
            "title": assessment.title,
            "skill": assessment.skill,
            "questions": [
                {"question": question["question"], "options": question["options"]}
                for question in assessment.questions
            ],
        }
        for assessment in assessments
    ]
    struggling_skills = []
    for skill in sorted(
        learner.skills,
        key=lambda item: (item.level, item.skill.casefold()),
    ):
        if skill.level < WEAKNESS_THRESHOLD:
            assessment = next(
                (
                    item
                    for item in assessments
                    if item.skill.casefold() == skill.skill.casefold()
                ),
                None,
            )
            struggling_skills.append(
                {
                    "skill": skill.skill,
                    "level": skill.level,
                    "assessment_id": assessment.id if assessment else None,
                }
            )
    for gap in gaps:
        if gap["status"] == "missing" and not any(
            item["skill"].casefold() == str(gap["skill"]).casefold()
            for item in struggling_skills
        ):
            assessment = next(
                (
                    item
                    for item in assessments
                    if item.skill.casefold() == str(gap["skill"]).casefold()
                ),
                None,
            )
            struggling_skills.append(
                {
                    "skill": gap["skill"],
                    "level": None,
                    "assessment_id": assessment.id if assessment else None,
                }
            )

    top_gap = next((gap for gap in gaps if gap["status"] != "satisfied"), None)
    insight = (
        f"You're {readiness:.0f}% ready for {target_role.name}. "
        f"{top_gap['skill']} is your highest-impact skill this week."
        if target_role and top_gap
        else f"You're {readiness:.0f}% ready for {target_role.name}."
        if target_role
        else "Choose a target role to see your personalized learning insight."
    )
    readiness_values = [float(point["readiness"]) for point in history]
    readiness_change = (
        round(readiness_values[-1] - readiness_values[-2], 1)
        if len(readiness_values) > 1
        else 0.0
    )
    trend = (
        "improving"
        if readiness_change > 0
        else "declining"
        if readiness_change < 0
        else "stable"
    )

    return {
        "learner": {
            "id": learner.id,
            "name": learner.name,
            "education": learner.education,
            "goal_role": learner.goal_role,
            "weekly_hours": learner.weekly_hours,
        },
        "roles": [{"id": role.id, "name": role.name} for role in roles],
        "target_role": (
            {"id": target_role.id, "name": target_role.name} if target_role else None
        ),
        "metrics": {
            "career_match_percent": float(match["match_percent"]) if match else 0.0,
            "readiness_score": readiness,
            "readiness_change": readiness_change,
            "readiness_trend": trend,
            "roadmap_completion_percent": roadmap_completion,
            "roadmap_hours_done": round(completed_hours, 1),
            "roadmap_hours_total": round(total_hours, 1),
            "weeks_remaining": weeks_remaining,
            "estimated_completion_date": (
                (now + timedelta(weeks=weeks_remaining)).date().isoformat()
                if weeks_remaining
                else now.date().isoformat()
            ),
            "learning_streak_days": streak_days,
            "hours_this_week": hours_this_week,
            "average_quiz_score": average_quiz_score,
            "skills_mastered_count": mastered_count,
        },
        "metric_calculations": {
            "career_match": {
                "weighted_skill_points": round(
                    sum(
                        min(
                            int(gap["learner_level"] or 0) / int(gap["required_level"])
                            if int(gap["required_level"]) > 0
                            else 0,
                            1,
                        )
                        * float(gap["weight"])
                        for gap in gaps
                    ),
                    2,
                ),
                "total_weight": round(
                    sum(float(gap["weight"]) for gap in gaps), 2
                ),
            },
            "readiness": {
                "weighted_proficiency_points": round(
                    sum(
                        min(int(gap["learner_level"] or 0), 100)
                        * float(gap["weight"])
                        for gap in gaps
                    ),
                    2,
                ),
                "total_weight": round(
                    sum(float(gap["weight"]) for gap in gaps), 2
                ),
            },
            "roadmap": {
                "completed_hours": round(completed_hours, 1),
                "total_hours": round(total_hours, 1),
            },
            "completion": {
                "remaining_hours": round(remaining_hours, 1),
                "weekly_hours": learner.weekly_hours,
            },
            "mastery_threshold": STRENGTH_THRESHOLD,
        },
        "insight": insight,
        "skill_analysis": {
            "skills": [
                {
                    "skill": skill.skill,
                    "level": skill.level,
                    "status": (
                        "strong"
                        if skill.level >= STRENGTH_THRESHOLD
                        else "struggling"
                        if skill.level < WEAKNESS_THRESHOLD
                        else "developing"
                    ),
                }
                for skill in learner.skills
            ],
            "strengths": [
                skill.skill
                for skill in learner.skills
                if skill.level >= STRENGTH_THRESHOLD
            ],
            "weaknesses": [
                skill.skill
                for skill in learner.skills
                if skill.level < WEAKNESS_THRESHOLD
            ],
        },
        "radar": [
            {
                "skill": requirement.skill,
                "current": skills_by_name.get(requirement.skill.casefold()).level
                if skills_by_name.get(requirement.skill.casefold())
                else 0,
                "required": requirement.required_level,
            }
            for requirement in role_requirements
        ],
        "readiness_history": history,
        "gaps": gaps,
        "next_best_action": best_action,
        "roadmap": phases,
        "recent_quizzes": recent_quizzes,
        "assessment_thresholds": {
            "pass": QUIZ_PASS_THRESHOLD,
            "excellent": QUIZ_EXCELLENT_THRESHOLD,
        },
        "struggling_skills": struggling_skills,
        "assessments": quiz_catalog,
        "agent_activity": [
            {
                "id": trace.id,
                "agent": trace.agent_name,
                "action": trace.output or "Reviewed learner progress",
                "input": trace.input or "",
                "status": trace.status,
                "created_at": trace.created_at.isoformat(),
            }
            for trace in reversed(traces[-6:])
        ],
        "role_comparison": compare_roles(learner.skills, roles),
    }
