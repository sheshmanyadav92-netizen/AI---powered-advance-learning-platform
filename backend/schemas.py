from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class LearnerSkillCreate(BaseModel):
    skill: str = Field(min_length=1, max_length=100)
    level: int = Field(ge=0, le=100)
    source: Literal["self", "assessment"] = "self"


class LearnerSkillRead(LearnerSkillCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int


class LearnerCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    education: str | None = Field(default=None, max_length=250)
    goal_role: str | None = Field(default=None, max_length=120)
    weekly_hours: float = Field(default=5, gt=0, le=168)


class LearnerUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    education: str | None = Field(default=None, max_length=250)
    goal_role: str | None = Field(default=None, max_length=120)
    weekly_hours: float | None = Field(default=None, gt=0, le=168)


class LearnerRead(LearnerCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    skills: list[LearnerSkillRead] = []


class RoleSkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    skill: str
    required_level: int
    weight: float


class RoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: str
    skills: list[RoleSkillRead] = []


class CompareRequest(BaseModel):
    role_ids: list[int] | None = None


class GoalUpdate(BaseModel):
    goal_role: str = Field(min_length=1, max_length=120)


class QuizSubmission(BaseModel):
    answers: list[int] = Field(min_length=1, max_length=50)


class DemoQuizSubmission(BaseModel):
    skill: str = Field(min_length=1, max_length=100)
    score: float = Field(ge=0, le=100)


class MentorChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
