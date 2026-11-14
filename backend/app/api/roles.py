"""Endpoints for career roles and skills catalogs.
"""
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..models import get_db, CareerRole, RoleSkillRequirement, Skill
from ..schemas import CareerRoleResponse, CareerRoleRequirementItem

router = APIRouter(tags=["Catalogs & Roles"])

@router.get("/roles", response_model=List[CareerRoleResponse])
def list_career_roles(db: Session = Depends(get_db)):
    roles = db.query(CareerRole).all()
    results = []
    for r in roles:
        reqs = db.query(RoleSkillRequirement).filter_by(role_id=r.id).all()
        req_items = []
        for rq in reqs:
            skill = db.query(Skill).filter_by(id=rq.skill_id).first()
            req_items.append(
                CareerRoleRequirementItem(
                    skill_id=rq.skill_id,
                    skill_name=skill.name if skill else f"Skill #{rq.skill_id}",
                    R_s=rq.R_s,
                    I_s=rq.I_s
                )
            )
        results.append(
            CareerRoleResponse(
                id=r.id,
                title=r.title,
                description=r.description,
                requirements=req_items
            )
        )
    return results

@router.get("/skills")
def list_skills(db: Session = Depends(get_db)):
    skills = db.query(Skill).all()
    return [{"id": s.id, "name": s.name, "category": s.category} for s in skills]

@router.get("/security-controls")
def get_security_controls_overview() -> Dict[str, Any]:
    """Demonstrates security controls mapped to OWASP ASVS v4.0."""
    return {
        "platform": "AI-Powered Personalized Learning Platform",
        "compliance_standard": "OWASP Application Security Verification Standard (ASVS v4.0)",
        "controls": [
            {
                "asvs_category": "V2: Authentication Verification Standard",
                "control": "Argon2id password hashing",
                "implementation": "Argon2id with 64MB memory cost, 3 iterations, 4 parallelism lanes. Replaces legacy/vulnerable bcrypt cost defaults."
            },
            {
                "asvs_category": "V3: Session Management",
                "control": "Short TTL JWT + Refresh Token Rotation",
                "implementation": "15-minute access token lifespan, cryptographic HMAC-SHA256 signing, strict expiration verification."
            },
            {
                "asvs_category": "V5: Malicious Input Handling",
                "control": "Pydantic Schema Validation",
                "implementation": "Strict type checking, range validation (0-100), email syntax validation, regex boundaries."
            },
            {
                "asvs_category": "V5.3: SQL Injection Prevention",
                "control": "Parameterized Queries",
                "implementation": "SQLAlchemy ORM parameterized abstract syntax tree queries; zero string concatenation."
            },
            {
                "asvs_category": "V13: API & Web Service Verification",
                "control": "Rate Limiting & Credential Stuffing Defense",
                "implementation": "SlowAPI token bucket rate limiter locked to remote client addresses on auth endpoints."
            },
            {
                "asvs_category": "V8: Data Protection & Privacy",
                "control": "PII-Sanitizing Application Logging",
                "implementation": "Regex filter intercepts log streams to redact email addresses and bearer tokens before disk persistence."
            }
        ]
    }

