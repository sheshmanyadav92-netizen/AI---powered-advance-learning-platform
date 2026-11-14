"""Recommendations retrieval endpoint.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models import get_db, User, Recommendation, LearningResource, Skill
from ..schemas import RecommendationListResponse, ResourceRecommendationItem
from .deps import get_current_user
from .agent_runner import execute_learner_agent_cycle
from ..formulas.recommendation import calculate_tag_similarity

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("", response_model=RecommendationListResponse)
def get_recommendations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Execute cycle to ensure recommendations are freshly aligned with latest state
    final_state = execute_learner_agent_cycle(user_id=user.id, event="status_check", db=db)
    
    recs_from_state = final_state.get("recommendations", [])
    mentor_message = final_state.get("mentor_notes", "Recommendations calibrated to your active goals and skill gaps.")

    items = []
    for r in recs_from_state:
        items.append(
            ResourceRecommendationItem(
                id=r["resource_id"],
                resource_id=r["resource_id"],
                skill_id=r["skill_id"],
                skill_name=r["skill_name"],
                resource_title=r["resource_title"],
                resource_url=r["resource_url"],
                difficulty=r["difficulty"],
                est_hours=r["est_hours"],
                tags=r["tags"] if isinstance(r["tags"], list) else [t.strip() for t in r["tags"].split(",") if t.strip()],
                priority_score=r["priority_score"],
                tag_similarity=r.get("tag_similarity", 0.0),
                status=r.get("status", "active")
            )
        )

    return RecommendationListResponse(
        recommendations=items,
        mentor_message=mentor_message
    )

