"""Profile management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..models import get_db, User, Skill, UserSkill, UserCareerGoal, CareerRole
from ..schemas import ProfileDetailResponse, ProfileUpdatePayload, UserProfileResponse, UserSkillItem
from .deps import get_current_user
from .agent_runner import execute_learner_agent_cycle

router = APIRouter(prefix="/profile", tags=["Profile"])

@router.get("", response_model=ProfileDetailResponse)
def get_profile(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Fetch user skills
    u_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user.id).all()
    skill_items = [
        UserSkillItem(
            skill_id=us.skill_id,
            skill_name=us.skill.name,
            category=us.skill.category,
            A_s=us.A_s,
            Q_s=us.Q_s,
            E_s=us.E_s,
            P_s=us.P_s,
            updated_at=us.updated_at
        )
        for us in u_skills
    ]

    # Active goal
    active_goal = None
    goal_record = db.query(UserCareerGoal).filter_by(user_id=user.id, active=True).first()
    if goal_record:
        role = db.query(CareerRole).filter_by(id=goal_record.role_id).first()
        if role:
            active_goal = {
                "role_id": role.id,
                "role_title": role.title,
                "description": role.description,
                "set_at": goal_record.set_at
            }

    return ProfileDetailResponse(
        user=UserProfileResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            created_at=user.created_at
        ),
        skills=skill_items,
        active_goal=active_goal
    )

@router.put("", response_model=ProfileDetailResponse)
def update_profile(
    payload: ProfileUpdatePayload,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    for update in payload.skills:
        u_skill = db.query(UserSkill).filter_by(user_id=user.id, skill_id=update.skill_id).first()
        if u_skill:
            if update.A_s is not None:
                u_skill.A_s = update.A_s
            if update.E_s is not None:
                u_skill.E_s = update.E_s
    db.commit()

    # Trigger agent cycle: SkillAnalysis -> CareerMatching -> Recommendation -> Mentor
    execute_learner_agent_cycle(user_id=user.id, event="profile_update", db=db)

    return get_profile(user=user, db=db)

