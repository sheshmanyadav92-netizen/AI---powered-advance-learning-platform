from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.agents.llm import LLMProviderError
from backend.agents.orchestrator import OrchestratorAgent
from backend.database import get_db
from backend.models import AgentTrace, Learner, Resource, RoadmapItem
from backend.schemas import MentorChatRequest
from backend.services.dashboard import build_dashboard

router = APIRouter(prefix="/api/learners", tags=["agent workflows"])
orchestrator = OrchestratorAgent()


def _handle_error(error: Exception) -> HTTPException:
    if isinstance(error, LookupError):
        return HTTPException(status_code=404, detail=str(error))
    if isinstance(error, LLMProviderError):
        return HTTPException(status_code=502, detail=str(error))
    return HTTPException(status_code=502, detail=str(error))


@router.post("/{learner_id}/roadmap/generate")
def generate_roadmap(learner_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    try:
        return orchestrator.generate_roadmap(db, learner_id)
    except (LookupError, LLMProviderError) as error:
        raise _handle_error(error) from error


@router.get("/{learner_id}/roadmap")
def list_roadmap(learner_id: int, db: Session = Depends(get_db)) -> list[dict[str, Any]]:
    if db.get(Learner, learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    items = db.scalars(
        select(RoadmapItem)
        .options(selectinload(RoadmapItem.resource))
        .where(RoadmapItem.learner_id == learner_id)
        .order_by(RoadmapItem.order_index)
    )
    return [
        {
            "id": item.id,
            "order": item.order_index + 1,
            "phase": item.phase,
            "resource_id": item.resource_id,
            "title": item.resource.title if item.resource else item.phase,
            "skill": item.resource.skill if item.resource else None,
            "status": item.status,
            "duration_hours": item.resource.duration_hours if item.resource else 0,
            "type": item.resource.type if item.resource else None,
            "difficulty": item.resource.difficulty if item.resource else None,
        }
        for item in items
    ]


@router.get("/{learner_id}/resources")
def list_resources(
    learner_id: int,
    skill: str | None = Query(default=None, min_length=1, max_length=100),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if db.get(Learner, learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    query = select(Resource).order_by(Resource.skill, Resource.difficulty, Resource.type, Resource.title)
    if skill:
        query = query.where(Resource.skill.ilike(skill))
    resources = db.scalars(query)
    return [
        {
            "id": item.id,
            "title": item.title,
            "skill": item.skill,
            "type": item.type,
            "difficulty": item.difficulty,
            "duration_hours": item.duration_hours,
            "prerequisite_skills": item.prerequisite_skills,
            "url": item.url,
        }
        for item in resources
    ]


@router.post("/{learner_id}/assessments/{skill}/generate")
def generate_assessment(
    learner_id: int, skill: str, db: Session = Depends(get_db)
) -> dict[str, Any]:
    try:
        return orchestrator.generate_assessment(db, learner_id, skill)
    except (LookupError, LLMProviderError, ValueError) as error:
        raise _handle_error(error) from error


@router.get("/{learner_id}/progress")
def progress_summary(learner_id: int, db: Session = Depends(get_db)) -> dict[str, Any]:
    summary = build_dashboard(db, learner_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return summary


@router.post("/{learner_id}/mentor/chat")
def mentor_chat(
    learner_id: int, payload: MentorChatRequest, db: Session = Depends(get_db)
) -> dict[str, str]:
    try:
        return orchestrator.mentor_chat(db, learner_id, payload.message)
    except (LookupError, LLMProviderError) as error:
        raise _handle_error(error) from error


@router.get("/{learner_id}/agent-traces")
def agent_trace_log(
    learner_id: int, limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[dict[str, Any]]:
    if db.get(Learner, learner_id) is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    traces = db.scalars(
        select(AgentTrace)
        .where(AgentTrace.learner_id == learner_id)
        .order_by(AgentTrace.created_at.desc(), AgentTrace.id.desc())
        .limit(limit)
    )
    return [
        {
            "id": item.id,
            "agent_name": item.agent_name,
            "input_summary": item.input,
            "output_summary": item.output,
            "handoff_to": item.handoff_to,
            "timestamp": item.created_at.isoformat(),
            "status": item.status,
        }
        for item in reversed(list(traces))
    ]
