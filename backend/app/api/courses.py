"""Courses endpoint providing the complete catalog of learning resources, filterable by skill or category.
"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from typing import List, Optional

from ..models import get_db, LearningResource, Skill

router = APIRouter(prefix="/courses", tags=["Course Catalog"])

class CourseItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    url: str
    provider: str
    skill_id: int
    skill_name: str
    category: str
    difficulty: int
    est_hours: float
    tags: str

@router.get("", response_model=List[CourseItem])
def list_courses(
    skill_id: Optional[int] = Query(None, description="Filter by skill ID"),
    category: Optional[str] = Query(None, description="Filter by skill category"),
    db: Session = Depends(get_db)
):
    query = db.query(LearningResource).join(Skill)
    if skill_id:
        query = query.filter(LearningResource.skill_id == skill_id)
    if category:
        query = query.filter(Skill.category.ilike(f"%{category}%"))
    
    courses = query.order_by(Skill.name.asc(), LearningResource.difficulty.asc()).all()
    
    result = []
    for c in courses:
        result.append(CourseItem(
            id=c.id,
            title=c.title,
            url=c.url,
            provider=c.provider,
            skill_id=c.skill_id,
            skill_name=c.skill.name if c.skill else "General",
            category=c.skill.category if c.skill else "General",
            difficulty=c.difficulty,
            est_hours=c.est_hours,
            tags=c.tags
        ))
    return result

