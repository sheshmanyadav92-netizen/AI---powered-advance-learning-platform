"""Database models matching the exact specification schema:
- users(id, name, email, password_hash, created_at)
- skills(id, name, category)
- user_skills(user_id, skill_id, A_s, Q_s, E_s, P_s, updated_at)
- career_roles(id, title, description)
- role_skill_requirements(role_id, skill_id, R_s, I_s)
- user_career_goals(user_id, role_id, set_at, active BOOLEAN)
- learning_resources(id, title, url, skill_id, difficulty, est_hours, tags)
- assessments(id, user_id, skill_id, score, taken_at)
- bkt_state(user_id, skill_id, p_mastery, p_T, p_G, p_S, updated_at)
- recommendations(id, user_id, skill_id, resource_id, priority_score, status, created_at)
- progress_log(id, user_id, resource_id, status, time_spent_min, completed_at)
"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .database import Base

def utc_now():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    skills = relationship("UserSkill", back_populates="user", cascade="all, delete-orphan")
    career_goals = relationship("UserCareerGoal", back_populates="user", cascade="all, delete-orphan")
    assessments = relationship("Assessment", back_populates="user", cascade="all, delete-orphan")
    bkt_states = relationship("BKTState", back_populates="user", cascade="all, delete-orphan")
    recommendations = relationship("Recommendation", back_populates="user", cascade="all, delete-orphan")
    progress_logs = relationship("ProgressLog", back_populates="user", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    certificates = relationship("Certificate", back_populates="user", cascade="all, delete-orphan")
    conversations = relationship("ChatConversation", back_populates="user", cascade="all, delete-orphan")
    roadmaps = relationship("LearningRoadmap", back_populates="user", cascade="all, delete-orphan")
    question_attempts = relationship("AssessmentAttempt", back_populates="user", cascade="all, delete-orphan")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=False)

    user_skills = relationship("UserSkill", back_populates="skill")
    role_requirements = relationship("RoleSkillRequirement", back_populates="skill")
    resources = relationship("LearningResource", back_populates="skill")
    assessments = relationship("Assessment", back_populates="skill")
    bkt_states = relationship("BKTState", back_populates="skill")
    recommendations = relationship("Recommendation", back_populates="skill")
    certificates = relationship("Certificate", back_populates="skill")


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    A_s = Column(Float, default=0.0, nullable=False)  # Self-assessed level (0-100)
    Q_s = Column(Float, default=0.0, nullable=False)  # Average quiz score (0-100)
    E_s = Column(Float, default=0.0, nullable=False)  # Evidence score from projects (0-100)
    P_s = Column(Float, default=0.0, nullable=False)  # Computed proficiency score (0-100)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="skills")
    skill = relationship("Skill", back_populates="user_skills")


class CareerRole(Base):
    __tablename__ = "career_roles"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(120), unique=True, index=True, nullable=False)
    description = Column(Text, nullable=True)

    requirements = relationship("RoleSkillRequirement", back_populates="role", cascade="all, delete-orphan")
    user_goals = relationship("UserCareerGoal", back_populates="role")


class RoleSkillRequirement(Base):
    __tablename__ = "role_skill_requirements"

    role_id = Column(Integer, ForeignKey("career_roles.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    R_s = Column(Float, nullable=False)  # Required proficiency (0-100)
    I_s = Column(Float, nullable=False)  # Importance weight (0-1)

    role = relationship("CareerRole", back_populates="requirements")
    skill = relationship("Skill", back_populates="role_requirements")


class UserCareerGoal(Base):
    __tablename__ = "user_career_goals"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("career_roles.id", ondelete="CASCADE"), primary_key=True)
    set_at = Column(DateTime, default=utc_now, nullable=False)
    active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="career_goals")
    role = relationship("CareerRole", back_populates="user_goals")


class LearningResource(Base):
    __tablename__ = "learning_resources"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    provider = Column(String(100), default="Online Resource", nullable=False)
    difficulty = Column(Integer, default=1, nullable=False)  # 1: Beginner, 2: Intermediate, 3: Advanced
    est_hours = Column(Float, default=10.0, nullable=False)  # Estimated hours T_s
    tags = Column(String(255), default="", nullable=False)   # Comma-separated tags

    skill = relationship("Skill", back_populates="resources")
    recommendations = relationship("Recommendation", back_populates="resource")
    progress_logs = relationship("ProgressLog", back_populates="resource")


class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)  # 0-100
    taken_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="assessments")
    skill = relationship("Skill", back_populates="assessments")


class BKTState(Base):
    __tablename__ = "bkt_state"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True)
    p_mastery = Column(Float, default=0.30, nullable=False)  # P(Ln)
    p_T = Column(Float, default=0.15, nullable=False)
    p_G = Column(Float, default=0.20, nullable=False)
    p_S = Column(Float, default=0.10, nullable=False)
    attempts_count = Column(Integer, default=0, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="bkt_states")
    skill = relationship("Skill", back_populates="bkt_states")


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(Integer, ForeignKey("learning_resources.id", ondelete="CASCADE"), nullable=False)
    priority_score = Column(Float, default=0.0, nullable=False)
    status = Column(String(50), default="active", nullable=False)  # active, completed, dismissed
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="recommendations")
    skill = relationship("Skill", back_populates="recommendations")
    resource = relationship("LearningResource", back_populates="recommendations")


class ProgressLog(Base):
    __tablename__ = "progress_log"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(Integer, ForeignKey("learning_resources.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(50), default="in_progress", nullable=False)  # in_progress, completed
    time_spent_min = Column(Integer, default=0, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="progress_logs")
    resource = relationship("LearningResource", back_populates="progress_logs")


class ChatConversation(Base):
    __tablename__ = "chat_conversations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), default="New Mentorship Session", nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("ChatMessage", back_populates="conversation", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("chat_conversations.id", ondelete="CASCADE"), nullable=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="chat_messages")
    conversation = relationship("ChatConversation", back_populates="messages")


class UserSettings(Base):
    __tablename__ = "user_settings"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    theme = Column(String(20), default="dark", nullable=False)
    llm_provider = Column(String(50), default="gemini", nullable=False)
    llm_model = Column(String(100), default="", nullable=False)
    llm_api_key_encrypted = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    user = relationship("User", back_populates="settings")


class Certificate(Base):
    __tablename__ = "certificates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    issued_at = Column(DateTime, default=utc_now, nullable=False)
    verification_code = Column(String(64), unique=True, index=True, nullable=False)
    pdf_path = Column(String(500), nullable=False)

    user = relationship("User", back_populates="certificates")
    skill = relationship("Skill", back_populates="certificates")


class AssessmentQuestion(Base):
    __tablename__ = "assessment_questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    question_text = Column(Text, nullable=False)
    option_a = Column(String(300), nullable=False)
    option_b = Column(String(300), nullable=False)
    option_c = Column(String(300), nullable=False)
    option_d = Column(String(300), nullable=False)
    correct_option = Column(String(5), nullable=False)  # 'A', 'B', 'C', 'D'
    difficulty = Column(Integer, default=1, nullable=False)  # 1 to 3
    explanation = Column(Text, default="", nullable=False)

    skill = relationship("Skill")
    attempts = relationship("AssessmentAttempt", back_populates="question", cascade="all, delete-orphan")


class AssessmentAttempt(Base):
    __tablename__ = "assessment_attempts"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    question_id = Column(Integer, ForeignKey("assessment_questions.id", ondelete="CASCADE"), nullable=False)
    selected_option = Column(String(5), nullable=False)
    is_correct = Column(Boolean, nullable=False)
    score = Column(Float, nullable=False)
    taken_at = Column(DateTime, default=utc_now, nullable=False)

    user = relationship("User", back_populates="question_attempts")
    question = relationship("AssessmentQuestion", back_populates="attempts")


class LearningRoadmap(Base):
    __tablename__ = "learning_roadmaps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("career_roles.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(200), nullable=False)
    generated_at = Column(DateTime, default=utc_now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="roadmaps")
    role = relationship("CareerRole")
    items = relationship("RoadmapItem", back_populates="roadmap", cascade="all, delete-orphan")


class RoadmapItem(Base):
    __tablename__ = "roadmap_items"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    roadmap_id = Column(Integer, ForeignKey("learning_roadmaps.id", ondelete="CASCADE"), nullable=False)
    skill_id = Column(Integer, ForeignKey("skills.id", ondelete="CASCADE"), nullable=False)
    resource_id = Column(Integer, ForeignKey("learning_resources.id", ondelete="CASCADE"), nullable=True)
    stage_order = Column(Integer, nullable=False)
    stage_title = Column(String(200), nullable=False)
    difficulty = Column(Integer, default=1, nullable=False)
    est_hours = Column(Float, default=10.0, nullable=False)
    status = Column(String(50), default="not_started", nullable=False)  # not_started, in_progress, paused, completed, review
    prerequisites = Column(String(200), default="", nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    roadmap = relationship("LearningRoadmap", back_populates="items")
    skill = relationship("Skill")
    resource = relationship("LearningResource")


class AgentExecutionLog(Base):
    __tablename__ = "agent_execution_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agent_name = Column(String(100), nullable=False)
    trigger_event = Column(String(100), nullable=False)
    status = Column(String(50), nullable=False)  # success, error, running
    execution_time_ms = Column(Float, default=0.0, nullable=False)
    input_summary = Column(Text, default="", nullable=False)
    output_summary = Column(Text, default="", nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now, nullable=False)





