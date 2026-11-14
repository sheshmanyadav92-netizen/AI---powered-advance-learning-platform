"""Authentication routes: registration, login with argon2id verification and JWT issuance.
Rate limiting applied to mitigate credential stuffing.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..models import get_db, User, Skill, UserSkill, BKTState
from ..schemas import UserRegister, UserLogin, TokenResponse
from ..core.security import hash_password, verify_password, create_access_token, create_refresh_token
from ..core.logging_config import logger

limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def register(request: Request, payload: UserRegister, db: Session = Depends(get_db)):
    # Check if user already exists
    existing = db.query(User).filter_by(email=payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email address already exists"
        )

    # Hash password with argon2id
    hashed = hash_password(payload.password)
    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hashed
    )
    db.add(user)
    db.flush()

    # Initialize user skill slots for all available skills
    all_skills = db.query(Skill).all()
    for s in all_skills:
        u_skill = UserSkill(
            user_id=user.id,
            skill_id=s.id,
            A_s=0.0,
            Q_s=0.0,
            E_s=0.0,
            P_s=0.0
        )
        db.add(u_skill)
        
        bkt = BKTState(
            user_id=user.id,
            skill_id=s.id,
            p_mastery=0.30,
            attempts_count=0
        )
        db.add(bkt)

    db.commit()
    db.refresh(user)

    logger.info(f"Registered new user ID {user.id}")

    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        name=user.name,
        email=user.email
    )

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter_by(email=payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        logger.warning(f"Failed login attempt for user email {payload.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    access_token = create_access_token({"sub": str(user.id), "email": user.email})
    refresh_token = create_refresh_token({"sub": str(user.id), "email": user.email})

    logger.info(f"Successful login for user ID {user.id}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id,
        name=user.name,
        email=user.email
    )

