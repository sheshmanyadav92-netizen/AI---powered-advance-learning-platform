from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.agents.llm import LLMProviderError
from backend.agents.orchestrator import OrchestratorAgent
from backend.database import get_db
from backend.models import (
    AgentTrace,
    Assessment,
    AssessmentResult,
    Learner,
    LearnerSkill,
    ProgressLog,
    Resource,
    RoadmapItem,
)
from backend.schemas import DemoQuizSubmission, GoalUpdate, QuizSubmission
from backend.services.demo_data import seed_demo_activity
from backend.services.scoring import resource_completion_level

router = APIRouter(prefix="/api", tags=["learning actions"])
orchestrator = OrchestratorAgent()


def _learner(db: Session, learner_id: int) -> Learner:
    learner = db.scalar(
        select(Learner)
        .options(selectinload(Learner.skills), selectinload(Learner.roadmap_items))
        .where(Learner.id == learner_id)
    )
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner not found")
    return learner


@router.get("/learners")
def list_learners(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    learners = db.scalars(select(Learner).order_by(Learner.id))
    return [
        {
            "id": learner.id,
            "name": learner.name,
            "goal_role": learner.goal_role,
        }
        for learner in learners
    ]


@router.post("/learners/{learner_id}/goal")
def change_goal(
    learner_id: int, payload: GoalUpdate, db: Session = Depends(get_db)
) -> dict[str, object]:
    try:
        return orchestrator.change_goal(db, learner_id, payload.goal_role)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except LLMProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post("/learners/{learner_id}/resources/{resource_id}/complete")
def complete_resource(
    learner_id: int, resource_id: int, db: Session = Depends(get_db)
) -> dict[str, object]:
    learner = _learner(db, learner_id)
    resource = db.get(Resource, resource_id)
    if resource is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    item = db.scalar(
        select(RoadmapItem).where(
            RoadmapItem.learner_id == learner_id,
            RoadmapItem.resource_id == resource_id,
        )
    )
    if item is None:
        item = RoadmapItem(
            learner_id=learner_id,
            resource_id=resource_id,
            phase="Focused practice",
            order_index=max(
                (roadmap.order_index for roadmap in learner.roadmap_items), default=-1
            )
            + 1,
        )
        db.add(item)
    progress = None
    if item.status != "done":
        item.status = "done"
        skill = next(
            (
                existing
                for existing in learner.skills
                if existing.skill.casefold() == resource.skill.casefold()
            ),
            None,
        )
        if skill is None:
            skill = LearnerSkill(
                learner_id=learner.id,
                skill=resource.skill,
                level=resource_completion_level(0, resource.duration_hours),
                source="self",
            )
            db.add(skill)
            learner.skills.append(skill)
        else:
            skill.level = resource_completion_level(skill.level, resource.duration_hours)
        db.add(
            ProgressLog(
                learner_id=learner.id,
                skill=resource.skill,
                hours_spent=resource.duration_hours,
                note=f"Completed {resource.title}",
            )
        )
        progress = orchestrator.resource_completed(db, learner_id, resource)
    db.commit()
    return {
        "message": f"Resource completed: {resource.title}",
        "resource_id": resource.id,
        "readiness_percent": progress["readiness_percent"] if progress else None,
    }


def _save_quiz_result(
    db: Session, learner: Learner, assessment: Assessment, score: float
) -> dict[str, object]:
    return orchestrator.evaluate_assessment(db, learner.id, assessment, score)


@router.post(
    "/learners/{learner_id}/assessments/{assessment_id}/submit",
    status_code=status.HTTP_201_CREATED,
)
def submit_quiz(
    learner_id: int,
    assessment_id: int,
    payload: QuizSubmission,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    learner = _learner(db, learner_id)
    assessment = db.get(Assessment, assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if len(payload.answers) != len(assessment.questions):
        raise HTTPException(
            status_code=422,
            detail=f"Expected {len(assessment.questions)} answers",
        )
    if any(
        answer < 0 or answer >= len(question["options"])
        for answer, question in zip(payload.answers, assessment.questions)
    ):
        raise HTTPException(status_code=422, detail="Answer choice is out of range")
    correct = sum(
        answer == question["answer_index"]
        for answer, question in zip(payload.answers, assessment.questions)
    )
    score = round(correct / len(assessment.questions) * 100, 1)
    try:
        return _save_quiz_result(db, learner, assessment, score)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except LLMProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post("/demo/{learner_id}/quiz", status_code=status.HTTP_201_CREATED)
def simulate_demo_quiz(
    learner_id: int,
    payload: DemoQuizSubmission,
    db: Session = Depends(get_db),
) -> dict[str, object]:
    learner = _learner(db, learner_id)
    assessment = db.scalar(
        select(Assessment).where(Assessment.skill.ilike(payload.skill))
    )
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found for skill")
    try:
        return _save_quiz_result(db, learner, assessment, payload.score)
    except LookupError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except LLMProviderError as error:
        raise HTTPException(status_code=502, detail=str(error)) from error


@router.post("/demo/{learner_id}/reset")
def reset_demo(learner_id: int, db: Session = Depends(get_db)) -> dict[str, str]:
    learner = _learner(db, learner_id)
    for item in list(learner.roadmap_items):
        db.delete(item)
    for log in db.scalars(
        select(ProgressLog).where(ProgressLog.learner_id == learner_id)
    ):
        db.delete(log)
    for result in db.scalars(
        select(AssessmentResult).where(AssessmentResult.learner_id == learner_id)
    ):
        db.delete(result)
    for trace in db.scalars(
        select(AgentTrace).where(AgentTrace.learner_id == learner_id)
    ):
        db.delete(trace)
    for skill in list(learner.skills):
        db.delete(skill)
    db.flush()
    db.expire(learner, ["skills"])
    learner.name = "Aarav"
    learner.education = "Undergraduate"
    learner.goal_role = "Full Stack Developer"
    learner.weekly_hours = 8
    db.add_all(
        [
            LearnerSkill(learner_id=learner.id, skill="Python", level=70, source="self"),
            LearnerSkill(learner_id=learner.id, skill="SQL", level=60, source="self"),
            LearnerSkill(learner_id=learner.id, skill="HTML", level=40, source="self"),
        ]
    )
    db.flush()
    db.expire(learner, ["skills"])
    seed_demo_activity(db, learner)
    db.commit()
    return {"message": "Demo learner and starter progress reset"}
