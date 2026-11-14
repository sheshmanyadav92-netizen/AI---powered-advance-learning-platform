from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import (
    AgentTrace,
    Assessment,
    AssessmentResult,
    Learner,
    ProgressLog,
    Resource,
    RoadmapItem,
    Role,
)
from backend.services.scoring import readiness_score


def seed_demo_activity(db: Session, learner: Learner) -> None:
    if db.scalar(
        select(RoadmapItem.id).where(RoadmapItem.learner_id == learner.id).limit(1)
    ):
        return
    resources = {
        resource.skill: resource
        for resource in db.scalars(select(Resource).order_by(Resource.id))
    }
    phase_skills = [
        ("Foundations", ["Python", "HTML", "CSS", "JavaScript"]),
        ("Frontend craft", ["React", "Git"]),
        ("Backend & ship", ["Node.js", "REST APIs", "Testing"]),
    ]
    order_index = 0
    for phase, skill_names in phase_skills:
        for skill_name in skill_names:
            resource = resources.get(skill_name)
            if resource is None:
                continue
            db.add(
                RoadmapItem(
                    learner_id=learner.id,
                    resource_id=resource.id,
                    phase=phase,
                    order_index=order_index,
                    status="done" if skill_name == "Python" else "not_started",
                )
            )
            order_index += 1
    role = db.scalar(
        select(Role).where(Role.name == learner.goal_role)
    )
    current_score = readiness_score(learner.skills, role) if role else 0.0
    now = datetime.utcnow()
    log_data = [
        ("Python", 1.5, "Completed Python practice", 2),
        ("SQL", 1.0, "Practiced querying and filtering data", 1),
        ("HTML", 1.0, "Built a semantic page layout", 0),
    ]
    for skill, hours, note, days_ago in log_data:
        db.add(
            ProgressLog(
                learner_id=learner.id,
                skill=skill,
                hours_spent=hours,
                note=note,
                logged_at=now - timedelta(days=days_ago),
            )
        )
    assessments = {
        item.skill: item for item in db.scalars(select(Assessment))
    }
    for skill_name, score, days_ago in [
        ("Python", 80, 5),
        ("SQL", 60, 3),
        ("HTML", 40, 1),
    ]:
        assessment = assessments.get(skill_name)
        if assessment is not None:
            db.add(
                AssessmentResult(
                    learner_id=learner.id,
                    assessment_id=assessment.id,
                    score=score,
                    completed_at=now - timedelta(days=days_ago),
                )
            )
    prior_events = [
        ("Learning Agent", "resource_completed:Python", "Completed a Python practice resource", -12, -6.0),
        ("Assessment Agent", "quiz_submitted:SQL", "SQL fundamentals check-in completed", -8, -4.0),
        ("Progress Agent", "resource_completed:HTML", "Practiced semantic HTML foundations", -4, -2.0),
    ]
    for agent, action_input, output, days_ago, score_delta in prior_events:
        db.add(
            AgentTrace(
                learner_id=learner.id,
                agent_name=agent,
                input=action_input,
                output=output,
                readiness_percent=max(0.0, round(current_score + score_delta, 1)),
                created_at=now + timedelta(days=days_ago),
            )
        )
