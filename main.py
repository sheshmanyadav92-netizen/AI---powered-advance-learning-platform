import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text

from backend.database import Base, engine
from backend.models import (  # noqa: F401 — importing registers all ORM tables
    AgentTrace,
    Assessment,
    AssessmentResult,
    Certification,
    Learner,
    LearnerSkill,
    ProgressLog,
    Project,
    Resource,
    RoadmapItem,
    Role,
    RoleSkill,
)
from backend.routers import actions, agent_actions, dashboard, learners, matching, roles

load_dotenv()

app = FastAPI(title="SkillPath AI API", version="0.1.0")
origins = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(learners.router)
app.include_router(roles.router)
app.include_router(matching.router)
app.include_router(dashboard.router)
app.include_router(actions.router)
app.include_router(agent_actions.router)


@app.on_event("startup")
def create_tables() -> None:
    Base.metadata.create_all(bind=engine)
    if "handoff_to" not in {
        column["name"] for column in inspect(engine).get_columns("agent_traces")
    }:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE agent_traces ADD COLUMN handoff_to VARCHAR(120)"))


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}
