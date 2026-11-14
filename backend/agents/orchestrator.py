from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.agents.assessment_evaluator import AssessmentProgressEvaluatorAgent
from backend.agents.career_matcher import CareerMatchingAgent
from backend.agents.learning_planner import LearningPathPlannerAgent
from backend.agents.llm import generate_json, mock_mode
from backend.agents.mentor import MentorAgent
from backend.agents.profile_analyst import ProfileSkillAnalystAgent
from backend.agents.resource_recommender import ResourceRecommenderAgent
from backend.agents.state import LearnerState
from backend.agents.tracing import record_agent_call
from backend.models import (
    Assessment,
    AssessmentResult,
    Learner,
    LearnerSkill,
    Resource,
    Role,
    RoadmapItem,
)
from backend.services.career_matching import calculate_role_match
from backend.services.scoring import readiness_score


class OrchestratorAgent:
    name = "Orchestrator Agent"

    def _learner(self, db: Session, learner_id: int) -> Learner:
        learner = db.scalar(
            select(Learner)
            .options(
                selectinload(Learner.skills),
                selectinload(Learner.roadmap_items).selectinload(
                    RoadmapItem.resource
                ),
            )
            .where(Learner.id == learner_id)
        )
        if learner is None:
            raise LookupError("Learner not found")
        return learner

    def _state(self, learner: Learner, event: str) -> LearnerState:
        return LearnerState(
            learner_id=learner.id,
            name=learner.name,
            goal_role=learner.goal_role,
            weekly_hours=learner.weekly_hours,
            skills={skill.skill: skill.level for skill in learner.skills},
            event=event,
        )

    def _roles(self, db: Session) -> list[Role]:
        return list(db.scalars(select(Role).options(selectinload(Role.skills)).order_by(Role.name)))

    def _resources(self, db: Session) -> list[Resource]:
        return list(db.scalars(select(Resource).order_by(Resource.title)))

    def _trace(
        self,
        db: Session,
        learner: Learner,
        agent: str,
        input_data: Any,
        output_data: Any,
        handoff: str | None,
    ) -> None:
        record_agent_call(db, learner, agent, input_data, output_data, handoff)

    def _run_profile_and_match(
        self, db: Session, learner: Learner, state: LearnerState, next_agent: str
    ) -> Role | None:
        profile = ProfileSkillAnalystAgent().run(state)
        self._trace(db, learner, ProfileSkillAnalystAgent.name, {"event": state.event}, profile, CareerMatchingAgent.name)
        roles = self._roles(db)
        match = CareerMatchingAgent().run(state, roles)
        role = next(
            (item for item in roles if item.name.casefold() == (state.goal_role or "").casefold()),
            None,
        )
        self._trace(
            db,
            learner,
            CareerMatchingAgent.name,
            {"goal_role": state.goal_role, "skills": state.skills},
            {"role": state.goal_role, "match_percent": match.get("match_percent"), "gaps": match.get("gaps", [])},
            next_agent,
        )
        return role

    def _run_planner_and_recommender(
        self,
        db: Session,
        learner: Learner,
        state: LearnerState,
        role: Role,
        *,
        remedial_skill: str | None = None,
        strong_skill: str | None = None,
        next_agent: str | None = None,
    ) -> None:
        resources = self._resources(db)
        planner = LearningPathPlannerAgent()
        roadmap = planner.run(
            db, learner, state, role, resources,
            remedial_skill=remedial_skill,
            strong_skill=strong_skill,
        )
        self._trace(
            db, learner, planner.name,
            {"role": role.name, "gaps": state.match.get("gaps", []), "remedial_skill": remedial_skill, "strong_skill": strong_skill},
            roadmap, ResourceRecommenderAgent.name,
        )
        recs = ResourceRecommenderAgent().run(state, resources)
        self._trace(
            db, learner, ResourceRecommenderAgent.name,
            {"gaps": state.match.get("gaps", []), "difficulty_target": "beginner" if remedial_skill else "adaptive"},
            recs, next_agent,
        )

    def generate_roadmap(self, db: Session, learner_id: int) -> dict[str, Any]:
        learner = self._learner(db, learner_id)
        state = self._state(learner, "roadmap_requested")
        role = self._run_profile_and_match(db, learner, state, LearningPathPlannerAgent.name)
        if role is None:
            raise LookupError("Learner has no valid goal role")
        self._run_planner_and_recommender(
            db, learner, state, role, next_agent=None
        )
        self._trace(db, learner, self.name, {"event": state.event}, {"roadmap_items": len(state.roadmap)}, None)
        db.commit()
        return {
            "learner_id": learner.id,
            "goal_role": role.name,
            "weekly_hours": learner.weekly_hours,
            "match_percent": state.match.get("match_percent"),
            "mastered_skills_reused": sorted(state.mastered_skills),
            "roadmap": state.roadmap,
            "recommendations": state.recommendations,
        }

    def change_goal(self, db: Session, learner_id: int, goal_role: str) -> dict[str, Any]:
        learner = self._learner(db, learner_id)
        role = next(
            (item for item in self._roles(db) if item.name.casefold() == goal_role.casefold()),
            None,
        )
        if role is None:
            raise LookupError("Role not found")
        old_goal = learner.goal_role
        learner.goal_role = role.name
        state = self._state(learner, "goal_changed")
        matched_role = self._run_profile_and_match(db, learner, state, LearningPathPlannerAgent.name)
        if matched_role is None:
            raise LookupError("Role not found")
        self._run_planner_and_recommender(
            db, learner, state, matched_role, next_agent=MentorAgent.name
        )
        state.event = "goal_changed"
        mentor = MentorAgent()
        advice = mentor.run(state, f"I changed my career goal from {old_goal} to {role.name}. What changed?")
        self._trace(
            db, learner, mentor.name,
            {"old_goal": old_goal, "new_goal": role.name, "profile": state.profile, "roadmap": state.roadmap},
            advice, self.name,
        )
        self._trace(db, learner, self.name, {"event": "goal_changed", "old_goal": old_goal}, {"new_goal": role.name}, None)
        db.commit()
        return {
            "message": f"Goal changed: roadmap rebuilt for {role.name}",
            "old_goal": old_goal,
            "goal_role": role.name,
            "mastered_skills_reused": sorted(state.mastered_skills),
            "roadmap": state.roadmap,
            "explanation": advice["message"],
        }

    def evaluate_assessment(
        self,
        db: Session,
        learner_id: int,
        assessment: Assessment,
        score: float,
    ) -> dict[str, Any]:
        learner = self._learner(db, learner_id)
        state = self._state(learner, "assessment_submitted")
        evaluator = AssessmentProgressEvaluatorAgent()
        result = evaluator.run(state, assessment.skill, score)
        skill = next(
            (item for item in learner.skills if item.skill.casefold() == assessment.skill.casefold()),
            None,
        )
        if skill is None:
            skill = LearnerSkill(
                learner_id=learner.id, skill=assessment.skill, level=round(score), source="assessment"
            )
            db.add(skill)
            learner.skills.append(skill)
        else:
            skill.level = round(score)
            skill.source = "assessment"
        db.add(
            AssessmentResult(
                learner_id=learner.id, assessment_id=assessment.id, score=score
            )
        )
        poor = score < 60
        strong = score > 85
        next_agent = LearningPathPlannerAgent.name if poor or strong else MentorAgent.name
        self._trace(db, learner, evaluator.name, {"skill": assessment.skill, "score": score}, result, next_agent)
        state.event = "assessment_poor" if poor else "assessment_strong" if strong else "assessment_submitted"
        if poor or strong:
            roles = self._roles(db)
            role = next(
                (item for item in roles if item.name.casefold() == (state.goal_role or "").casefold()),
                None,
            )
            if role is None:
                raise LookupError("Learner has no valid goal role")
            state.match = calculate_role_match(learner.skills, role)
            self._run_planner_and_recommender(
                db, learner, state, role,
                remedial_skill=assessment.skill if poor else None,
                strong_skill=assessment.skill if strong else None,
                next_agent=MentorAgent.name,
            )
        else:
            ProfileSkillAnalystAgent().run(state)
            self._trace(
                db, learner, ProfileSkillAnalystAgent.name,
                {"event": state.event, "skills": state.skills},
                state.profile, MentorAgent.name,
            )
            roles = self._roles(db)
            role = next(
                (item for item in roles if item.name.casefold() == (state.goal_role or "").casefold()),
                None,
            )
            if role:
                state.match = calculate_role_match(learner.skills, role)
        mentor = MentorAgent()
        advice = mentor.run(state, f"I scored {score:.1f}% on my {assessment.skill} assessment. What should I do next?")
        self._trace(
            db, learner, mentor.name,
            {"assessment": result, "profile": state.profile, "roadmap": state.roadmap},
            advice, self.name,
        )
        self._trace(
            db, learner, self.name,
            {"event": state.event, "skill": assessment.skill, "score": score},
            {"status": result["status"], "roadmap_items": len(state.roadmap), "advice": advice["message"]},
            None,
        )
        db.commit()
        return {
            **result,
            "message": "Assessment submitted",
            "roadmap": state.roadmap,
            "advice": advice["message"],
        }

    def mentor_chat(self, db: Session, learner_id: int, message: str) -> dict[str, str]:
        learner = self._learner(db, learner_id)
        state = self._state(learner, "mentor_chat")
        role = self._run_profile_and_match(db, learner, state, MentorAgent.name)
        if role is not None:
            state.roadmap = [
                {
                    "title": item.resource.title if item.resource else item.phase,
                    "skill": item.resource.skill if item.resource else None,
                    "phase": item.phase,
                    "status": item.status,
                }
                for item in sorted(learner.roadmap_items, key=lambda item: item.order_index)
            ]
        latest = db.scalar(
            select(AssessmentResult)
            .options(selectinload(AssessmentResult.assessment))
            .where(AssessmentResult.learner_id == learner.id)
            .order_by(AssessmentResult.completed_at.desc())
        )
        if latest:
            state.assessment = {
                "skill": latest.assessment.skill,
                "score": latest.score,
                "status": "struggling" if latest.score < 60 else "fast" if latest.score > 85 else "developing",
            }
        response = MentorAgent().run(state, message)
        self._trace(db, learner, MentorAgent.name, {"message": message, "profile": state.profile, "roadmap": state.roadmap, "assessment": state.assessment}, response, None)
        self._trace(db, learner, self.name, {"event": "mentor_chat"}, {"answered": True}, None)
        db.commit()
        return response

    def generate_assessment(self, db: Session, learner_id: int, skill_name: str) -> dict[str, Any]:
        learner = self._learner(db, learner_id)
        assessment = db.scalar(
            select(Assessment).where(Assessment.skill.ilike(skill_name))
        )
        if assessment is None:
            if mock_mode():
                questions = [
                    {
                        "question": f"Which choice best represents a sound foundational practice in {skill_name}?",
                        "options": [
                            f"Apply a core {skill_name} concept to solve the task",
                            "Ignore the requirements and guess",
                            "Skip validation and review",
                            "Use an unrelated tool instead",
                        ],
                        "answer_index": 0,
                    },
                    {
                        "question": f"What is the best way to improve at {skill_name}?",
                        "options": [
                            "Practice a small task and check the result",
                            "Avoid examples and feedback",
                            "Memorize unrelated terminology",
                            "Skip the fundamentals",
                        ],
                        "answer_index": 0,
                    },
                    {
                        "question": f"Before using a new {skill_name} technique, what should you do?",
                        "options": [
                            "Understand its purpose and constraints",
                            "Assume it always works",
                            "Remove all checks",
                            "Ignore the input data",
                        ],
                        "answer_index": 0,
                    },
                ]
            else:
                generated = generate_json(
                    "Generate exactly 5 beginner multiple-choice quiz questions for the skill "
                    f"{skill_name!r}. Return only JSON object {{\"questions\":[{{\"question\":\"...\","
                    "\"options\":[\"...\",\"...\",\"...\",\"...\"],\"answer_index\":0}}]}. "
                    "Each question must have exactly four options and one correct answer."
                )
                questions = generated.get("questions")
                if not isinstance(questions, list) or not questions:
                    raise ValueError("Gemini quiz response did not contain questions")
                validated = []
                for question in questions:
                    if (
                        not isinstance(question, dict)
                        or not isinstance(question.get("question"), str)
                        or not isinstance(question.get("options"), list)
                        or len(question["options"]) != 4
                        or not isinstance(question.get("answer_index"), int)
                        or not 0 <= question["answer_index"] < 4
                    ):
                        raise ValueError("Gemini generated an invalid quiz question")
                    validated.append(
                        {
                            "question": question["question"],
                            "options": question["options"],
                            "answer_index": question["answer_index"],
                        }
                    )
                questions = validated
            assessment = Assessment(
                title=f"{skill_name} generated fundamentals quiz",
                skill=skill_name,
                questions=questions,
            )
            db.add(assessment)
            db.flush()
        state = self._state(learner, "assessment_generated")
        output = {
            "assessment_id": assessment.id,
            "skill": assessment.skill,
            "title": assessment.title,
            "question_count": len(assessment.questions),
        }
        self._trace(db, learner, "Assessment & Progress Evaluator Agent", {"skill": skill_name}, output, None)
        self._trace(db, learner, self.name, {"event": "assessment_generated"}, output, None)
        db.commit()
        return {
            **output,
            "questions": [
                {"question": item["question"], "options": item["options"]}
                for item in assessment.questions
            ],
        }

    def resource_completed(
        self, db: Session, learner_id: int, resource: Resource
    ) -> dict[str, Any]:
        learner = self._learner(db, learner_id)
        role = next(
            (
                item for item in self._roles(db)
                if item.name.casefold() == (learner.goal_role or "").casefold()
            ),
            None,
        )
        readiness = (
            readiness_score(learner.skills, role) if role else None
        )
        progress = {
            "resource_id": resource.id,
            "title": resource.title,
            "skill": resource.skill,
            "readiness_percent": readiness,
        }
        self._trace(
            db, learner, "Assessment & Progress Evaluator Agent",
            {"event": "resource_completed", "resource_id": resource.id},
            progress, self.name,
        )
        self._trace(
            db, learner, self.name, {"event": "resource_completed"},
            progress, None,
        )
        db.commit()
        return progress
