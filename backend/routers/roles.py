from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.database import get_db
from backend.models import Role
from backend.schemas import RoleRead

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.get("", response_model=list[RoleRead])
def list_roles(db: Session = Depends(get_db)) -> list[Role]:
    return list(
        db.scalars(select(Role).options(selectinload(Role.skills)).order_by(Role.name))
    )


@router.get("/{role_id}", response_model=RoleRead)
def get_role(role_id: int, db: Session = Depends(get_db)) -> Role:
    role = db.scalar(
        select(Role).options(selectinload(Role.skills)).where(Role.id == role_id)
    )
    if role is None:
        raise HTTPException(status_code=404, detail="Role not found")
    return role
