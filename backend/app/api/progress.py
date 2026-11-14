"""Progress tracking and mastery dashboard endpoints.
"""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import get_db, User, Skill, LearningResource, BKTState, ProgressLog, Assessment, UserSkill
from ..schemas import ProgressCompleteRequest, ProgressDashboardResponse, BKTStateItem, ProgressLogItem
from .deps import get_current_user
from .agent_runner import execute_learner_agent_cycle

router = APIRouter(prefix="/progress", tags=["Progress & Mastery"])

@router.get("", response_model=ProgressDashboardResponse)
def get_progress_dashboard(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    bkt_records = db.query(BKTState).filter_by(user_id=user.id).all()
    bkt_items = []
    total_mastery = 0.0

    for b in bkt_records:
        skill = db.query(Skill).filter_by(id=b.skill_id).first()
        needs_rem = (b.attempts_count >= 3) and (b.p_mastery < 0.50)
        bkt_items.append(
            BKTStateItem(
                skill_id=b.skill_id,
                skill_name=skill.name if skill else f"Skill #{b.skill_id}",
                p_mastery=b.p_mastery,
                attempts_count=b.attempts_count,
                needs_remediation=needs_rem,
                updated_at=b.updated_at
            )
        )
        total_mastery += b.p_mastery

    avg_mastery = round((total_mastery / len(bkt_records)) * 100.0, 2) if bkt_records else 0.0

    # Recent progress logs
    logs = (
        db.query(ProgressLog)
        .filter_by(user_id=user.id)
        .order_by(ProgressLog.completed_at.desc())
        .limit(10)
        .all()
    )
    log_items = []
    for l in logs:
        res = db.query(LearningResource).filter_by(id=l.resource_id).first()
        skill_name = res.skill.name if res and res.skill else "General"
        log_items.append(
            ProgressLogItem(
                id=l.id,
                resource_id=l.resource_id,
                resource_title=res.title if res else f"Resource #{l.resource_id}",
                skill_name=skill_name,
                status=l.status,
                time_spent_min=l.time_spent_min,
                completed_at=l.completed_at
            )
        )

    return ProgressDashboardResponse(
        bkt_states=bkt_items,
        recent_logs=log_items,
        overall_mastery=avg_mastery
    )

@router.post("/complete", response_model=ProgressDashboardResponse)
def complete_resource(
    payload: ProgressCompleteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    resource = db.query(LearningResource).filter_by(id=payload.resource_id).first()
    if not resource:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning resource not found"
        )

    now = datetime.now(timezone.utc)

    # 1. Add progress log
    log_entry = ProgressLog(
        user_id=user.id,
        resource_id=payload.resource_id,
        status="completed",
        time_spent_min=payload.time_spent_min,
        completed_at=now
    )
    db.add(log_entry)

    # 2. If quiz score is submitted with completion, log assessment
    score_to_pass = payload.assessment_score if payload.assessment_score is not None else 85.0
    assessment = Assessment(
        user_id=user.id,
        skill_id=resource.skill_id,
        score=score_to_pass,
        taken_at=now
    )
    db.add(assessment)
    db.commit()

    # 3. Trigger LangGraph agent pipeline: ProgressTracking -> Recommendation -> Mentor
    event_payload = {
        "skill_id": resource.skill_id,
        "score": score_to_pass,
        "resource_id": payload.resource_id
    }
    execute_learner_agent_cycle(
        user_id=user.id,
        event="resource_completed",
        db=db,
        event_payload=event_payload
    )

    return get_progress_dashboard(user=user, db=db)

