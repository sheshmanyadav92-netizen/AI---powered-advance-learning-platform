# SkillPath AI — Phases 1 and 2

## Architecture

- **FastAPI app (`main.py`)**: app lifecycle, CORS, and API router registration; interactive API documentation is available at `/docs`.
- **Persistence (`backend/database.py`)**: SQLAlchemy 2.x sessions and a SQLite database at `backend/data/skillpath.db`.
- **Models (`backend/models/`)**: SQLAlchemy entities for learner profiles, career roles, learning resources, roadmaps, assessments, progress, and agent traces.
- **Services (`backend/services/`)**: deterministic skill analysis, career matching, dashboard calculations, and readiness scoring.
- **Agents (`backend/agents/`)**: shared learner state and independently contracted profile analysis, career matching, roadmap planning, resource recommendation, assessment, mentor, and orchestration agents.
- **LLM provider (`backend/agents/llm.py`)**: Gemini for mentor/explanatory text and dynamically generated quizzes; deterministic offline behavior when no key is configured or `LLM_MODE=mock`.
- **Routers (`backend/routers/`)**: learner profile and skill CRUD, role catalog, analysis, matching, dashboard, learning actions, and the agent-workflow API.
- **Seed data (`seed.py`)**: repeatable initialization of roles, prerequisite-chain resources and practice exercises, skill assessments, and the Aarav demo learner.
- **Tests (`tests/`)**: focused tests for phase ordering, adaptive goal changes, assessment interventions, skill analysis, and matching.

## Data model

- `Learner` owns `LearnerSkill`, `Certification`, `Project`, `RoadmapItem`, `AssessmentResult`, and `ProgressLog` records.
- `LearnerSkill` stores a 0–100 proficiency level and `self` or `assessment` source.
- `Role` owns weighted `RoleSkill` requirements.
- `Resource` describes a learning item, its skill and difficulty, estimated hours, URL, and prerequisite skill names.
- `Assessment` stores a skill quiz and its question bank; `AssessmentResult` stores a learner's attempt and score.
- `AgentTrace` records agent name, input/output summaries, handoff target, readiness, and timestamp. Existing SQLite databases add the handoff column at startup.
- Roadmap item order is stored as `order_index` to avoid using SQL's `ORDER` keyword as a column name.

## API list

All endpoints are under `/api`.

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/learners` | Create a learner profile |
| `GET` | `/learners/{learner_id}` | Retrieve a profile and its skills |
| `PUT` | `/learners/{learner_id}` | Update a profile |
| `DELETE` | `/learners/{learner_id}` | Delete a profile |
| `GET` | `/learners/{learner_id}/skills` | List a learner's skills |
| `POST` | `/learners/{learner_id}/skills` | Add a learner skill |
| `PUT` | `/learners/{learner_id}/skills/{skill_id}` | Update a learner skill |
| `DELETE` | `/learners/{learner_id}/skills/{skill_id}` | Delete a learner skill |
| `GET` | `/roles` | List career roles and weighted skills |
| `GET` | `/roles/{role_id}` | Retrieve a role |
| `GET` | `/learners/{learner_id}/analysis` | Analyze strengths, weaknesses, and skill statuses |
| `GET` | `/learners/{learner_id}/match/{role_id}` | Match one learner to one role |
| `POST` | `/learners/{learner_id}/compare` | Compare the learner against selected roles |
| `POST` | `/learners/{learner_id}/roadmap/generate` | Run collaborating agents and persist a personalized roadmap |
| `GET` | `/learners/{learner_id}/roadmap` | List ordered roadmap items |
| `GET` | `/learners/{learner_id}/resources` | List resources, optionally filtered by `skill` |
| `POST` | `/learners/{learner_id}/resources/{resource_id}/complete` | Complete a resource and update progress/readiness |
| `POST` | `/learners/{learner_id}/assessments/{skill}/generate` | Generate or retrieve a skill quiz |
| `POST` | `/learners/{learner_id}/assessments/{assessment_id}/submit` | Grade quiz answers and adapt the learner plan |
| `GET` | `/learners/{learner_id}/progress` | Return progress and readiness summary |
| `POST` | `/learners/{learner_id}/mentor/chat` | Chat with a data-grounded learning mentor |
| `POST` | `/learners/{learner_id}/goal` | Adapt the roadmap to a new target role |
| `GET` | `/learners/{learner_id}/agent-traces` | Inspect ordered agent handoffs |

`POST /api/demo/{learner_id}/quiz` is retained for deterministic score simulations (including percentages that cannot be represented by a short multiple-choice quiz).

## Agent and adaptation behavior

The orchestrator passes a shared learner state through profile analysis, deterministic career matching, prerequisite-aware planning, resource recommendation, and (where appropriate) mentor advice. Core matching and scores remain deterministic; Gemini is limited to explanations, mentor responses, and quiz generation. No API key is required.

On Full Stack Developer plans, JavaScript precedes React, which precedes Node.js and Express; the capstone is last. Assessments below 60% insert beginner learning and practice before dependent topics. Scores above 85% replace beginner content for that skill with an advanced challenge. A goal change rebuilds the plan while retaining mastered skills (level 70+ or completed resources).

## Matching rules

For each required role skill, proficiency contributes `min(learner_level / required_level, 1) * weight`; an absent skill contributes zero. The match percentage is the weighted sum divided by total role weight. Gaps are labeled `missing` when absent, `weak` when below the role requirement, and `satisfied` when the requirement is met. Skill analysis labels levels `strength` at 70+, `weakness` below 50, and `developing` otherwise.
