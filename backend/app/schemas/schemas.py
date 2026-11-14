"""Pydantic schemas with strict validation for request/response payloads.
Prevents type confusion and injection vulnerabilities.
"""
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator


# --- Auth Schemas ---
class UserRegister(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="Full name")
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=100, description="Password (min 8 chars)")

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    name: str
    email: str

class UserProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    created_at: datetime


# --- Skill & Profile Schemas ---
class UserSkillItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    skill_id: int
    skill_name: str
    category: str
    A_s: float = Field(..., ge=0, le=100, description="Self-assessed level (0-100)")
    Q_s: float = Field(..., ge=0, le=100, description="Average quiz score (0-100)")
    E_s: float = Field(..., ge=0, le=100, description="Project evidence score (0-100)")
    P_s: float = Field(..., ge=0, le=100, description="Calculated proficiency score (0-100)")
    updated_at: datetime

class UserSkillUpdateRequest(BaseModel):
    skill_id: int
    A_s: Optional[float] = Field(None, ge=0, le=100)
    E_s: Optional[float] = Field(None, ge=0, le=100)

class ProfileUpdatePayload(BaseModel):
    skills: List[UserSkillUpdateRequest]

class ProfileDetailResponse(BaseModel):
    user: UserProfileResponse
    skills: List[UserSkillItem]
    active_goal: Optional[Dict[str, Any]] = None


# --- Career Goal Schemas ---
class SetCareerGoalRequest(BaseModel):
    role_id: int

class CareerRoleRequirementItem(BaseModel):
    skill_id: int
    skill_name: str
    R_s: float
    I_s: float

class CareerRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    description: Optional[str]
    requirements: List[CareerRoleRequirementItem]


# --- Assessment Schemas ---
class AssessmentCreate(BaseModel):
    skill_id: int
    score: float = Field(..., ge=0, le=100, description="Quiz/Assessment score (0-100)")

class AssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    skill_id: int
    skill_name: str
    score: float
    taken_at: datetime
    p_mastery_after: float
    remediation_flag: bool


# --- Progress & BKT Schemas ---
class ProgressCompleteRequest(BaseModel):
    resource_id: int
    time_spent_min: int = Field(default=30, ge=1, le=1000)
    assessment_score: Optional[float] = Field(default=None, ge=0, le=100)

class BKTStateItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    skill_id: int
    skill_name: str
    p_mastery: float
    attempts_count: int
    needs_remediation: bool
    updated_at: datetime

class ProgressLogItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    resource_id: int
    resource_title: str
    skill_name: str
    status: str
    time_spent_min: int
    completed_at: Optional[datetime]

class ProgressDashboardResponse(BaseModel):
    bkt_states: List[BKTStateItem]
    recent_logs: List[ProgressLogItem]
    overall_mastery: float


# --- Gap Report & Recommendations ---
class SkillGapItem(BaseModel):
    skill_id: int
    skill_name: str
    category: str
    P_s: float
    R_s: float
    I_s: float
    G_s: float

class GapReportResponse(BaseModel):
    role_id: int
    role_title: str
    readiness_percentage: float
    cosine_fit: float
    skill_gaps: List[SkillGapItem]

class ResourceRecommendationItem(BaseModel):
    id: int
    resource_id: int
    skill_id: int
    skill_name: str
    resource_title: str
    resource_url: str
    difficulty: int
    est_hours: float
    tags: List[str]
    priority_score: float
    tag_similarity: float
    status: str

class RecommendationListResponse(BaseModel):
    recommendations: List[ResourceRecommendationItem]
    mentor_message: str

