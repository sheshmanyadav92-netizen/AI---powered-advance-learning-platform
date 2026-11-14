from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db
from backend.models import Learner, LearnerSkill
from backend.schemas import (
    LearnerCreate,
    LearnerRead,
    LearnerSkillCreate,
    LearnerSkillRead,
    LearnerUpdate,
)
from backend.services.skill_analysis import analyze_skills

router = APIRouter(prefix="/api/learners", tags=["learners"])


def _get_learner(db: Session, learner_id: int) -> Learner:
    learner = db.scalar(
        select(Learner).options(selectinload(Learner.skills)).where(Learner.id == learner_id)
    )
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return learner


@router.post("", response_model=LearnerRead, status_code=status.HTTP_201_CREATED)
def create_learner(payload: LearnerCreate, db: Session = Depends(get_db)) -> Learner:
    learner = Learner(**payload.model_dump())
    db.add(learner)
    db.commit()
    db.refresh(learner)
    return learner


@router.get("/{learner_id}", response_model=LearnerRead)
def get_learner(learner_id: int, db: Session = Depends(get_db)) -> Learner:
    return _get_learner(db, learner_id)


@router.put("/{learner_id}", response_model=LearnerRead)
def update_learner(
    learner_id: int, payload: LearnerUpdate, db: Session = Depends(get_db)
) -> Learner:
    learner = _get_learner(db, learner_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        if value is not None or field in {"education", "goal_role"}:
            setattr(learner, field, value)
    db.commit()
    db.refresh(learner)
    return learner


@router.delete("/{learner_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_learner(learner_id: int, db: Session = Depends(get_db)) -> Response:
    learner = _get_learner(db, learner_id)
    db.delete(learner)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{learner_id}/skills", response_model=list[LearnerSkillRead])
def list_skills(learner_id: int, db: Session = Depends(get_db)) -> list[LearnerSkill]:
    _get_learner(db, learner_id)
    return list(
        db.scalars(
            select(LearnerSkill)
            .where(LearnerSkill.learner_id == learner_id)
            .order_by(LearnerSkill.skill)
        )
    )


@router.post(
    "/{learner_id}/skills",
    response_model=LearnerSkillRead,
    status_code=status.HTTP_201_CREATED,
)
def create_skill(
    learner_id: int, payload: LearnerSkillCreate, db: Session = Depends(get_db)
) -> LearnerSkill:
    _get_learner(db, learner_id)
    existing = db.scalar(
        select(LearnerSkill).where(
            LearnerSkill.learner_id == learner_id,
            LearnerSkill.skill == payload.skill,
        )
    )
    if existing is not None:
        raise HTTPException(status_code=409, detail="Learner already has this skill")
    skill = LearnerSkill(learner_id=learner_id, **payload.model_dump())
    db.add(skill)
    db.commit()
    db.refresh(skill)
    return skill


@router.put("/{learner_id}/skills/{skill_id}", response_model=LearnerSkillRead)
def update_skill(
    learner_id: int,
    skill_id: int,
    payload: LearnerSkillCreate,
    db: Session = Depends(get_db),
) -> LearnerSkill:
    _get_learner(db, learner_id)
    skill = db.scalar(
        select(LearnerSkill).where(
            LearnerSkill.id == skill_id, LearnerSkill.learner_id == learner_id
        )
    )
    if skill is None:
        raise HTTPException(status_code=404, detail="Learner skill not found")
    duplicate = db.scalar(
        select(LearnerSkill).where(
            LearnerSkill.learner_id == learner_id,
            LearnerSkill.skill == payload.skill,
            LearnerSkill.id != skill_id,
        )
    )
    if duplicate is not None:
        raise HTTPException(status_code=409, detail="Learner already has this skill")
    for field, value in payload.model_dump().items():
        setattr(skill, field, value)
    db.commit()
    db.refresh(skill)
    return skill


@router.delete(
    "/{learner_id}/skills/{skill_id}", status_code=status.HTTP_204_NO_CONTENT
)
def delete_skill(
    learner_id: int, skill_id: int, db: Session = Depends(get_db)
) -> Response:
    _get_learner(db, learner_id)
    skill = db.scalar(
        select(LearnerSkill).where(
            LearnerSkill.id == skill_id, LearnerSkill.learner_id == learner_id
        )
    )
    if skill is None:
        raise HTTPException(status_code=404, detail="Learner skill not found")
    db.delete(skill)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{learner_id}/analysis")
def skill_analysis(learner_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    learner = _get_learner(db, learner_id)
    return analyze_skills(learner.skills)
