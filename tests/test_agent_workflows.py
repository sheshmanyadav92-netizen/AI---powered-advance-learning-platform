from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database import Base, get_db
from backend.models import Learner
from main import app
from seed import seed_assessments, seed_demo_learner, seed_resources, seed_roles


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    monkeypatch.setenv("LLM_MODE", "mock")
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    testing_sessions = sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    Base.metadata.create_all(bind=engine)
    with testing_sessions() as db:
        seed_roles(db)
        seed_resources(db)
        seed_assessments(db)
        seed_demo_learner(db)
        db.commit()
        learner_id = db.query(Learner).filter_by(name="Aarav").one().id

    def override_get_db() -> Iterator[Session]:
        with testing_sessions() as db:
            yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        test_client.headers.update({"x-test-learner-id": str(learner_id)})
        yield test_client
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def _learner_id(client: TestClient) -> str:
    return client.headers["x-test-learner-id"]


def test_generated_roadmap_orders_full_stack_prerequisites_and_capstone(
    client: TestClient,
) -> None:
    response = client.post(f"/api/learners/{_learner_id(client)}/roadmap/generate")

    assert response.status_code == 200
    roadmap = response.json()["roadmap"]
    positions = {item["skill"]: index for index, item in enumerate(roadmap)}
    assert positions["JavaScript"] < positions["React"]
    assert positions["React"] < positions["Node.js"]
    assert positions["Node.js"] < positions["Express"]
    assert positions["Express"] < positions["Full Stack Project"]
    assert roadmap[-1]["phase"] == "Capstone Project"
    assert roadmap[-1]["type"] == "project"
    assert all(item["estimated_weeks"] >= 1 for item in roadmap)


def test_goal_change_rebuilds_plan_for_data_analyst(client: TestClient) -> None:
    learner_id = _learner_id(client)
    response = client.post(
        f"/api/learners/{learner_id}/goal",
        json={"goal_role": "Data Analyst"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["goal_role"] == "Data Analyst"
    assert "Python" in data["mastered_skills_reused"]
    assert "rebuilt your plan for Data Analyst" in data["explanation"]
    assert any(item["skill"] == "Tableau" for item in data["roadmap"])
    assert all(item["skill"] != "Full Stack Project" for item in data["roadmap"])
    trace = client.get(f"/api/learners/{learner_id}/agent-traces").json()
    handoffs = {item["handoff_to"] for item in trace}
    assert "Career Matching Agent" in handoffs
    assert "Learning Path Planner Agent" in handoffs
    assert "Resource Recommender Agent" in handoffs
    assert "Mentor Agent" in handoffs


def test_poor_assessment_inserts_remediation_and_traces_handoffs(
    client: TestClient,
) -> None:
    learner_id = _learner_id(client)
    response = client.post(
        f"/api/demo/{learner_id}/quiz",
        json={"skill": "JavaScript", "score": 45},
    )

    assert response.status_code == 201
    assert response.json()["status"] == "struggling"
    roadmap = response.json()["roadmap"]
    remedial_positions = [
        index for index, item in enumerate(roadmap)
        if item["phase"] == "Remedial: JavaScript"
    ]
    assert remedial_positions
    assert all(
        roadmap[index]["difficulty"] == "beginner"
        for index in remedial_positions
    )
    positions = {item["skill"]: index for index, item in enumerate(roadmap)}
    assert max(remedial_positions) < positions["React"] < positions["Node.js"]
    trace = client.get(f"/api/learners/{learner_id}/agent-traces").json()
    evaluator = next(
        item for item in reversed(trace)
        if item["agent_name"] == "Assessment & Progress Evaluator Agent"
    )
    assert evaluator["handoff_to"] == "Learning Path Planner Agent"
    assert any(
        item["agent_name"] == "Learning Path Planner Agent"
        and item["handoff_to"] == "Resource Recommender Agent"
        for item in trace
    )
    assert any(
        item["agent_name"] == "Resource Recommender Agent"
        and item["handoff_to"] == "Mentor Agent"
        for item in trace
    )


def test_generated_quiz_and_strong_assessment_add_advanced_task(
    client: TestClient,
) -> None:
    learner_id = _learner_id(client)
    generated = client.post(
        f"/api/learners/{learner_id}/assessments/Express/generate"
    )

    assert generated.status_code == 200
    quiz = generated.json()
    assert len(quiz["questions"]) == 3
    submitted = client.post(
        f"/api/learners/{learner_id}/assessments/{quiz['assessment_id']}/submit",
        json={"answers": [0, 0, 0]},
    )

    assert submitted.status_code == 201
    assert submitted.json()["status"] == "fast"
    assert any(
        item["phase"] == "Advanced challenge: Express"
        for item in submitted.json()["roadmap"]
    )


def test_resource_completion_updates_readiness(client: TestClient) -> None:
    learner_id = _learner_id(client)
    generated = client.post(f"/api/learners/{learner_id}/roadmap/generate")
    resource_id = generated.json()["roadmap"][0]["resource_id"]

    completed = client.post(
        f"/api/learners/{learner_id}/resources/{resource_id}/complete"
    )

    assert completed.status_code == 200
    assert completed.json()["readiness_percent"] is not None
