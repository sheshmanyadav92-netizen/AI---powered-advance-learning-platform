from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.dashboard import build_dashboard

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/{learner_id}")
def get_dashboard(learner_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    dashboard = build_dashboard(db, learner_id)
    if dashboard is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return dashboard
