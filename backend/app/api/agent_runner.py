"""Bridge connecting the database state, SQLAlchemy transactions, and the LangGraph multi-agent graph.
"""
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models import (
    User, Skill, UserSkill, CareerRole, RoleSkillRequirement,
    UserCareerGoal, LearningResource, BKTState, Recommendation, Certificate
)
from ..agents import LearnerState, run_agent_workflow
from ..core.certificate import generate_certificate_pdf

def execute_learner_agent_cycle(
    user_id: int,
    event: str,
    db: Session,
    event_payload: Optional[Dict[str, Any]] = None
) -> LearnerState:
    """Extracts database state for learner, runs multi-agent cycle, and persists outputs."""
    # 1. Fetch user skills
    u_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user_id).all()
    skill_profile: Dict[int, Dict[str, Any]] = {}
    for us in u_skills:
        skill_profile[us.skill_id] = {
            "name": us.skill.name,
            "category": us.skill.category,
            "A_s": us.A_s,
            "Q_s": us.Q_s,
            "E_s": us.E_s,
            "P_s": us.P_s
        }

    # 2. Fetch active career goal
    active_goal_record = (
        db.query(UserCareerGoal)
        .filter_by(user_id=user_id, active=True)
        .first()
    )
    
    active_career_goal = None
    if active_goal_record:
        role = db.query(CareerRole).filter_by(id=active_goal_record.role_id).first()
        if role:
            reqs = db.query(RoleSkillRequirement).filter_by(role_id=role.id).all()
            requirements_list = []
            for r in reqs:
                skill_obj = db.query(Skill).filter_by(id=r.skill_id).first()
                requirements_list.append({
                    "skill_id": r.skill_id,
                    "skill_name": skill_obj.name if skill_obj else f"Skill #{r.skill_id}",
                    "R_s": r.R_s,
                    "I_s": r.I_s
                })
            active_career_goal = {
                "role_id": role.id,
                "role_title": role.title,
                "requirements": requirements_list
            }

    # 3. Fetch BKT states
    bkt_records = db.query(BKTState).filter_by(user_id=user_id).all()
    bkt_states: Dict[int, Dict[str, Any]] = {}
    remediation_skills = []
    for b in bkt_records:
        needs_rem = (b.attempts_count >= 3) and (b.p_mastery < 0.50)
        bkt_states[b.skill_id] = {
            "p_mastery": b.p_mastery,
            "p_T": b.p_T,
            "p_G": b.p_G,
            "p_S": b.p_S,
            "attempts_count": b.attempts_count,
            "needs_remediation": needs_rem
        }
        if needs_rem:
            remediation_skills.append(b.skill_id)

    # 4. Fetch candidate learning resources
    all_resources = db.query(LearningResource).all()
    candidate_resources = []
    for r in all_resources:
        candidate_resources.append({
            "id": r.id,
            "skill_id": r.skill_id,
            "title": r.title,
            "url": r.url,
            "difficulty": r.difficulty,
            "est_hours": r.est_hours,
            "tags": r.tags
        })

    payload = dict(event_payload or {})
    payload["candidate_resources"] = candidate_resources

    # Formulate state
    state: LearnerState = {
        "user_id": user_id,
        "last_event": event,
        "event_payload": payload,
        "skill_profile": skill_profile,
        "active_career_goal": active_career_goal,
        "bkt_states": bkt_states,
        "remediation_skills": remediation_skills
    }

    # 5. Execute LangGraph workflow
    final_state = run_agent_workflow(state)

    # 6. Persist results back to database
    # Persist updated P_s
    for skill_id, s_data in final_state.get("skill_profile", {}).items():
        us_record = db.query(UserSkill).filter_by(user_id=user_id, skill_id=skill_id).first()
        if us_record:
            us_record.P_s = s_data.get("P_s", us_record.P_s)

    # Persist updated BKT states
    for skill_id, b_data in final_state.get("bkt_states", {}).items():
        b_rec = db.query(BKTState).filter_by(user_id=user_id, skill_id=skill_id).first()
        if b_rec:
            b_rec.p_mastery = b_data.get("p_mastery", b_rec.p_mastery)
            b_rec.attempts_count = b_data.get("attempts_count", b_rec.attempts_count)
        else:
            new_b = BKTState(
                user_id=user_id,
                skill_id=skill_id,
                p_mastery=b_data.get("p_mastery", 0.30),
                attempts_count=b_data.get("attempts_count", 0)
            )
            db.add(new_b)

    # Auto-issue Certificate when P(Ln) >= 0.80
    for skill_id, b_data in final_state.get("bkt_states", {}).items():
        if b_data.get("p_mastery", 0.0) >= 0.80:
            existing_cert = db.query(Certificate).filter_by(user_id=user_id, skill_id=skill_id).first()
            if not existing_cert:
                user_obj = db.query(User).filter_by(id=user_id).first()
                skill_obj = db.query(Skill).filter_by(id=skill_id).first()
                role_title = active_career_goal["role_title"] if active_career_goal else "Full Stack Developer"
                code, pdf_path = generate_certificate_pdf(
                    learner_name=user_obj.name if user_obj else "Demo Learner",
                    skill_name=skill_obj.name if skill_obj else f"Skill #{skill_id}",
                    role_title=role_title,
                    issued_at=datetime.now(timezone.utc)
                )
                new_cert = Certificate(
                    user_id=user_id,
                    skill_id=skill_id,
                    issued_at=datetime.now(timezone.utc),
                    verification_code=code,
                    pdf_path=pdf_path
                )
                db.add(new_cert)

    # Persist recommendations
    db.query(Recommendation).filter_by(user_id=user_id).delete()
    for rec in final_state.get("recommendations", []):
        r_entry = Recommendation(
            user_id=user_id,
            skill_id=rec["skill_id"],
            resource_id=rec["resource_id"],
            priority_score=rec["priority_score"],
            status="active"
        )
        db.add(r_entry)

    db.commit()
    return final_state

