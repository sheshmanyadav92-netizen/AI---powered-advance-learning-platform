from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db
from backend.models import Learner, Role
from backend.schemas import CompareRequest
from backend.services.career_matching import calculate_role_match, compare_roles

router = APIRouter(prefix="/api/learners", tags=["career matching"])


def _get_learner(db: Session, learner_id: int) -> Learner:
    learner = db.scalar(
        select(Learner).options(selectinload(Learner.skills)).where(Learner.id == learner_id)
    )
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return learner


@router.get("/{learner_id}/match/{role_id}")
def match_career(
    learner_id: int, role_id: int, db: Session = Depends(get_db)
) -> dict[str, object]:
    learner = _get_learner(db, learner_id)
    role = db.scalar(
        select(Role).options(selectinload(Role.skills)).where(Role.id == role_id)
    )
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return calculate_role_match(learner.skills, role)


@router.post("/{learner_id}/compare")
def compare_careers(
    learner_id: int,
    payload: CompareRequest,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    learner = _get_learner(db, learner_id)
    query = select(Role).options(selectinload(Role.skills)).order_by(Role.name)
    if payload.role_ids is not None:
        if not payload.role_ids:
            raise HTTPException(status_code=422, detail="role_ids must not be empty")
        query = query.where(Role.id.in_(set(payload.role_ids)))
    roles = list(db.scalars(query))
    if payload.role_ids is not None and len(roles) != len(set(payload.role_ids)):
        raise HTTPException(status_code=404, detail="One or more roles were not found")
    return {
        "learner_id": learner_id,
        "matches": compare_roles(learner.skills, roles),
    }
