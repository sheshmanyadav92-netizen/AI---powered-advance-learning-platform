"""Assessment submission endpoint.
Triggers multi-agent pipeline: ProgressTracking -> SkillAnalysis -> CareerMatching -> Recommendation -> Mentor.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models import get_db, User, Skill, Assessment, UserSkill
from ..schemas import AssessmentCreate, AssessmentResponse
from .deps import get_current_user
from .agent_runner import execute_learner_agent_cycle

router = APIRouter(prefix="/assessment", tags=["Assessments"])

@router.post("", response_model=AssessmentResponse)
def submit_assessment(
    payload: AssessmentCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    skill = db.query(Skill).filter_by(id=payload.skill_id).first()
    if not skill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Skill not found"
        )

    # 1. Save assessment record
    assessment = Assessment(
        user_id=user.id,
        skill_id=payload.skill_id,
        score=payload.score
    )
    db.add(assessment)
    db.flush()

    # 2. Update average quiz score Q_s for this skill
    avg_score = db.query(func.avg(Assessment.score)).filter(
        Assessment.user_id == user.id,
        Assessment.skill_id == payload.skill_id
    ).scalar() or payload.score

    u_skill = db.query(UserSkill).filter_by(user_id=user.id, skill_id=payload.skill_id).first()
    if u_skill:
        u_skill.Q_s = round(float(avg_score), 2)
    db.commit()

    # 3. Trigger LangGraph agent pipeline
    event_payload = {
        "skill_id": payload.skill_id,
        "score": payload.score
    }
    final_state = execute_learner_agent_cycle(
        user_id=user.id,
        event="new_assessment",
        db=db,
        event_payload=event_payload
    )

    bkt_data = final_state.get("bkt_states", {}).get(payload.skill_id, {})
    p_mastery = bkt_data.get("p_mastery", 0.30)
    remediation = bkt_data.get("needs_remediation", False)

    return AssessmentResponse(
        id=assessment.id,
        user_id=user.id,
        skill_id=payload.skill_id,
        skill_name=skill.name,
        score=payload.score,
        taken_at=assessment.taken_at,
        p_mastery_after=p_mastery,
        remediation_flag=remediation
    )

