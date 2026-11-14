"""Certificate endpoints for issuing, viewing, downloading, and publicly verifying mastery credentials.
"""
import os
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session
from typing import List

from ..models import get_db, User, Skill, Certificate, BKTState, CareerRole, UserCareerGoal
from ..core.certificate import generate_certificate_pdf
from .deps import get_current_user

router = APIRouter(prefix="/certificates", tags=["Certificates"])

class CertificateItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    skill_id: int
    skill_name: str
    issued_at: datetime
    verification_code: str
    pdf_path: str

class VerificationResponse(BaseModel):
    valid: bool
    learner_name: str
    skill_name: str
    issued_at: datetime
    verification_code: str
    target_role: str

@router.get("", response_model=List[CertificateItem])
def list_user_certificates(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    certs = (
        db.query(Certificate)
        .filter(Certificate.user_id == user.id)
        .order_by(Certificate.issued_at.desc())
        .all()
    )
    result = []
    for c in certs:
        result.append(
            CertificateItem(
                id=c.id,
                skill_id=c.skill_id,
                skill_name=c.skill.name if c.skill else f"Skill #{c.skill_id}",
                issued_at=c.issued_at,
                verification_code=c.verification_code,
                pdf_path=f"/certificates/download/{c.id}"
            )
        )
    return result

@router.get("/download/{cert_id}")
def download_certificate(
    cert_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    cert = db.query(Certificate).filter(Certificate.id == cert_id, Certificate.user_id == user.id).first()
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found")
    
    # If file does not exist on disk, regenerate it
    if not os.path.exists(cert.pdf_path):
        active_goal = db.query(UserCareerGoal).filter_by(user_id=user.id, active=True).first()
        role_title = active_goal.role.title if (active_goal and active_goal.role) else "Full Stack Developer"
        _, new_path = generate_certificate_pdf(
            learner_name=user.name,
            skill_name=cert.skill.name if cert.skill else "Software Engineering",
            role_title=role_title,
            verification_code=cert.verification_code,
            issued_at=cert.issued_at
        )
        cert.pdf_path = new_path
        db.commit()

    return FileResponse(
        cert.pdf_path,
        media_type="application/pdf",
        filename=f"certificate_{cert.verification_code}.pdf"
    )

@router.get("/verify/{verification_code}", response_model=VerificationResponse)
def verify_certificate_public(
    verification_code: str,
    db: Session = Depends(get_db)
):
    """Public verification endpoint for employers (no auth required)."""
    cert = db.query(Certificate).filter(Certificate.verification_code == verification_code).first()
    if not cert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid certificate verification code"
        )
    
    active_goal = db.query(UserCareerGoal).filter_by(user_id=cert.user_id, active=True).first()
    role_title = active_goal.role.title if (active_goal and active_goal.role) else "Full Stack Developer"
    
    return VerificationResponse(
        valid=True,
        learner_name=cert.user.name if cert.user else "Demo Learner",
        skill_name=cert.skill.name if cert.skill else "Software Competency",
        issued_at=cert.issued_at,
        verification_code=cert.verification_code,
        target_role=role_title
    )

