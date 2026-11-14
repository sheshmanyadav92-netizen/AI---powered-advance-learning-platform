from datetime import datetime

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Learner(Base):
    __tablename__ = "learners"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    education: Mapped[str | None] = mapped_column(String(250))
    goal_role: Mapped[str | None] = mapped_column(String(120))
    weekly_hours: Mapped[float] = mapped_column(Float, default=5.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    skills: Mapped[list["LearnerSkill"]] = relationship(
        back_populates="learner", cascade="all, delete-orphan"
    )
    certifications: Mapped[list["Certification"]] = relationship(
        back_populates="learner", cascade="all, delete-orphan"
    )
    projects: Mapped[list["Project"]] = relationship(
        back_populates="learner", cascade="all, delete-orphan"
    )
    roadmap_items: Mapped[list["RoadmapItem"]] = relationship(
        back_populates="learner", cascade="all, delete-orphan"
    )
    assessment_results: Mapped[list["AssessmentResult"]] = relationship(
        back_populates="learner", cascade="all, delete-orphan"
    )
    progress_logs: Mapped[list["ProgressLog"]] = relationship(
        back_populates="learner", cascade="all, delete-orphan"
    )


class LearnerSkill(Base):
    __tablename__ = "learner_skills"
    __table_args__ = (
        CheckConstraint("level >= 0 AND level <= 100", name="check_learner_skill_level"),
        CheckConstraint("source IN ('self', 'assessment')", name="check_learner_skill_source"),
        UniqueConstraint("learner_id", "skill", name="uq_learner_skill"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), nullable=False)
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    level: Mapped[int] = mapped_column(Integer, nullable=False)
    source: Mapped[str] = mapped_column(String(20), default="self", nullable=False)

    learner: Mapped[Learner] = relationship(back_populates="skills")


class Certification(Base):
    __tablename__ = "certifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    issuer: Mapped[str | None] = mapped_column(String(150))
    awarded_at: Mapped[datetime | None] = mapped_column(DateTime)

    learner: Mapped[Learner] = relationship(back_populates="certifications")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(500))

    learner: Mapped[Learner] = relationship(back_populates="projects")


class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)

    skills: Mapped[list["RoleSkill"]] = relationship(
        back_populates="role", cascade="all, delete-orphan"
    )


class RoleSkill(Base):
    __tablename__ = "role_skills"
    __table_args__ = (
        CheckConstraint("required_level >= 0 AND required_level <= 100", name="check_required_level"),
        CheckConstraint("weight > 0", name="check_role_skill_weight"),
        UniqueConstraint("role_id", "skill", name="uq_role_skill"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"), nullable=False)
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    required_level: Mapped[int] = mapped_column(Integer, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    role: Mapped[Role] = relationship(back_populates="skills")


class Resource(Base):
    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    skill: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), nullable=False)
    duration_hours: Mapped[float] = mapped_column(Float, nullable=False)
    prerequisite_skills: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"
    __table_args__ = (UniqueConstraint("learner_id", "phase", "order_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), nullable=False)
    resource_id: Mapped[int | None] = mapped_column(ForeignKey("resources.id"))
    phase: Mapped[str] = mapped_column(String(120), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="not_started", nullable=False)

    learner: Mapped[Learner] = relationship(back_populates="roadmap_items")
    resource: Mapped[Resource | None] = relationship()


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    skill: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    questions: Mapped[list[dict[str, object]]] = mapped_column(JSON, nullable=False)


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), nullable=False)
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    learner: Mapped[Learner] = relationship(back_populates="assessment_results")
    assessment: Mapped[Assessment] = relationship()


class ProgressLog(Base):
    __tablename__ = "progress_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"), nullable=False)
    skill: Mapped[str] = mapped_column(String(100), nullable=False)
    hours_spent: Mapped[float] = mapped_column(Float, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    logged_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    learner: Mapped[Learner] = relationship(back_populates="progress_logs")


class AgentTrace(Base):
    __tablename__ = "agent_traces"

    id: Mapped[int] = mapped_column(primary_key=True)
    learner_id: Mapped[int | None] = mapped_column(ForeignKey("learners.id"))
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    input: Mapped[str | None] = mapped_column(Text)
    output: Mapped[str | None] = mapped_column(Text)
    handoff_to: Mapped[str | None] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(30), default="completed", nullable=False)
    readiness_percent: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
