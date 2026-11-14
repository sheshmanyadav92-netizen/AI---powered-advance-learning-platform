import json
from typing import Any

from sqlalchemy.orm import Session

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.models import AgentTrace, Learner, Role
from backend.services.scoring import readiness_score


def record_agent_call(
    db: Session,
    learner: Learner,
    agent_name: str,
    input_data: Any,
    output_data: Any,
    handoff_to: str | None,
) -> None:
    role = db.scalar(
        select(Role)
        .options(selectinload(Role.skills))
        .where(Role.name == learner.goal_role)
    ) if learner.goal_role else None
    readiness = readiness_score(learner.skills, role) if role else None
    db.add(
        AgentTrace(
            learner_id=learner.id,
            agent_name=agent_name,
            input=json.dumps(input_data, ensure_ascii=True, default=str)[:4000],
            output=json.dumps(output_data, ensure_ascii=True, default=str)[:4000],
            handoff_to=handoff_to,
            readiness_percent=readiness,
        )
    )
