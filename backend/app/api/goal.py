"""Career goal selection and gap report endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..models import get_db, User, CareerRole, UserCareerGoal
from ..schemas import SetCareerGoalRequest, GapReportResponse, SkillGapItem
from .deps import get_current_user
from .agent_runner import execute_learner_agent_cycle

router = APIRouter(prefix="/goal", tags=["Career Goals"])

@router.post("", response_model=GapReportResponse)
def set_career_goal(
    payload: SetCareerGoalRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    role = db.query(CareerRole).filter_by(id=payload.role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Career role not found"
        )

    # Deactivate existing active goals
    db.query(UserCareerGoal).filter_by(user_id=user.id).update({"active": False})

    # Set new active goal
    goal_record = db.query(UserCareerGoal).filter_by(user_id=user.id, role_id=role.id).first()
    if goal_record:
        goal_record.active = True
    else:
        goal_record = UserCareerGoal(
            user_id=user.id,
            role_id=role.id,
            active=True
        )
        db.add(goal_record)

    db.commit()

    # Trigger agent cycle with event "goal_change"
    final_state = execute_learner_agent_cycle(user_id=user.id, event="goal_change", db=db)
    gap_rep = final_state.get("gap_report", {})

    skill_gaps = [
        SkillGapItem(
            skill_id=item["skill_id"],
            skill_name=item["skill_name"],
            category="",
            P_s=item["P_s"],
            R_s=item["R_s"],
            I_s=item["I_s"],
            G_s=item["G_s"]
        )
        for item in gap_rep.get("details", [])
    ]

    return GapReportResponse(
        role_id=role.id,
        role_title=role.title,
        readiness_percentage=gap_rep.get("readiness", 0.0),
        cosine_fit=gap_rep.get("cosine_fit", 0.0),
        skill_gaps=skill_gaps
    )

@router.get("", response_model=GapReportResponse)
def get_current_goal_gap_report(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    active_goal = db.query(UserCareerGoal).filter_by(user_id=user.id, active=True).first()
    if not active_goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active career goal configured. Please set a career goal first."
        )

    # Run status check cycle
    final_state = execute_learner_agent_cycle(user_id=user.id, event="status_check", db=db)
    gap_rep = final_state.get("gap_report", {})
    role = db.query(CareerRole).filter_by(id=active_goal.role_id).first()

    skill_gaps = [
        SkillGapItem(
            skill_id=item["skill_id"],
            skill_name=item["skill_name"],
            category="",
            P_s=item["P_s"],
            R_s=item["R_s"],
            I_s=item["I_s"],
            G_s=item["G_s"]
        )
        for item in gap_rep.get("details", [])
    ]

    return GapReportResponse(
        role_id=role.id,
        role_title=role.title,
        readiness_percentage=gap_rep.get("readiness", 0.0),
        cosine_fit=gap_rep.get("cosine_fit", 0.0),
        skill_gaps=skill_gaps
    )

