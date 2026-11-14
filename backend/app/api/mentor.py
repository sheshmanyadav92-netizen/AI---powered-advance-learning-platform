"""AI Mentor chatbot endpoints.
Grounded to current LearnerState: skill profile, gap report, BKT states, recommendations.
Supports multi-conversation management, provider status reflection, and conversational history.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from ..models import (
    get_db,
    User,
    ChatMessage,
    ChatConversation,
    UserSkill,
    Skill,
    UserCareerGoal,
    CareerRole,
    RoleSkillRequirement,
    BKTState,
    Recommendation,
    LearningResource,
    UserSettings,
)
from .deps import get_current_user
from .agent_runner import execute_learner_agent_cycle
from ..core.llm import llm_service, DEFAULT_MODELS
from ..core.crypto import decrypt_secret

router = APIRouter(prefix="/mentor", tags=["AI Mentor Chatbot"])


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="Learner message")
    conversation_id: Optional[int] = Field(None, description="Optional conversation session ID")


class ChatResponse(BaseModel):
    response: str
    created_at: datetime
    role: str = "assistant"
    provider: str
    model: str
    conversation_id: int


class ChatHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    role: str
    content: str
    created_at: datetime
    conversation_id: Optional[int] = None


class ConversationSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


def _get_or_create_conversation(user: User, conversation_id: Optional[int], first_message: str, db: Session) -> ChatConversation:
    if conversation_id:
        conv = db.query(ChatConversation).filter_by(id=conversation_id, user_id=user.id).first()
        if conv:
            return conv

    # Check for latest active conversation
    latest = (
        db.query(ChatConversation)
        .filter_by(user_id=user.id)
        .order_by(ChatConversation.updated_at.desc())
        .first()
    )
    if latest and not conversation_id:
        return latest

    # Create new conversation
    title = first_message[:40] + ("..." if len(first_message) > 40 else "")
    conv = ChatConversation(
        user_id=user.id,
        title=title,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(conv)
    db.flush()
    return conv


@router.post("/chat", response_model=ChatResponse)
def chat_with_mentor(
    payload: ChatRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    now = datetime.now(timezone.utc)
    conv = _get_or_create_conversation(user, payload.conversation_id, payload.message, db)
    conv.updated_at = now

    # 1. Fetch live learner context
    final_state = execute_learner_agent_cycle(user_id=user.id, event="status_check", db=db)
    
    # Format skills dictionary
    u_skills = db.query(UserSkill).join(Skill).filter(UserSkill.user_id == user.id).all()
    skills_context = {}
    for us in u_skills:
        skills_context[us.skill_id] = {
            "name": us.skill.name,
            "category": us.skill.category,
            "P_s": us.P_s,
            "A_s": us.A_s,
            "Q_s": us.Q_s,
            "E_s": us.E_s
        }

    learner_context = {
        "user_id": user.id,
        "skills": skills_context,
        "gap_report": final_state.get("gap_report", {}),
        "bkt_states": final_state.get("bkt_states", {}),
        "recommendations": final_state.get("recommendations", [])
    }

    # 2. Fetch conversation history for this conversation session
    past_messages = (
        db.query(ChatMessage)
        .filter_by(user_id=user.id, conversation_id=conv.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(12)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in past_messages]

    # 3. Save user message to database
    user_msg_entry = ChatMessage(
        user_id=user.id,
        conversation_id=conv.id,
        role="user",
        content=payload.message,
        created_at=now
    )
    db.add(user_msg_entry)
    db.flush()

    # 4. Resolve LLM provider, model, and API key
    u_settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    decrypted_key = ""
    provider = "groq"
    model = ""

    if u_settings and u_settings.llm_api_key_encrypted:
        decrypted_key = decrypt_secret(u_settings.llm_api_key_encrypted)
        provider = u_settings.llm_provider
        model = u_settings.llm_model

    # Environment variable fallbacks if user settings not set or empty
    if not decrypted_key:
        if os.getenv("GROQ_API_KEY"):
            decrypted_key = os.getenv("GROQ_API_KEY")
            provider = "groq"
            model = model or os.getenv("GROQ_MODEL", DEFAULT_MODELS["groq"])
        elif os.getenv("NVIDIA_API_KEY"):
            decrypted_key = os.getenv("NVIDIA_API_KEY")
            provider = "nvidia"
            model = model or os.getenv("NVIDIA_MODEL", DEFAULT_MODELS["nvidia"])
        elif os.getenv("OPENROUTER_API_KEY"):
            decrypted_key = os.getenv("OPENROUTER_API_KEY")
            provider = "openrouter"
            model = model or os.getenv("OPENROUTER_MODEL", DEFAULT_MODELS["openrouter"])

    model = model or DEFAULT_MODELS.get(provider, "qwen/qwen3.8-27b")

    # Generate response from provider
    mentor_reply_text = llm_service.generate_mentor_response(
        user_message=payload.message,
        learner_context=learner_context,
        history=history,
        api_key=decrypted_key,
        provider=provider,
        model=model,
    )

    # 5. Save assistant response
    reply_now = datetime.now(timezone.utc)
    assistant_entry = ChatMessage(
        user_id=user.id,
        conversation_id=conv.id,
        role="assistant",
        content=mentor_reply_text,
        created_at=reply_now
    )
    db.add(assistant_entry)
    db.commit()

    return ChatResponse(
        response=mentor_reply_text,
        created_at=reply_now,
        role="assistant",
        provider=provider,
        model=model,
        conversation_id=conv.id
    )


@router.get("/conversations", response_model=List[ConversationSummary])
def list_conversations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    convs = (
        db.query(ChatConversation)
        .filter_by(user_id=user.id)
        .order_by(ChatConversation.updated_at.desc())
        .all()
    )
    res = []
    for c in convs:
        count = db.query(ChatMessage).filter_by(conversation_id=c.id).count()
        res.append(ConversationSummary(
            id=c.id,
            title=c.title,
            created_at=c.created_at,
            updated_at=c.updated_at,
            message_count=count
        ))
    return res


@router.get("/conversations/{conversation_id}", response_model=List[ChatHistoryItem])
def get_conversation_messages(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(ChatConversation).filter_by(id=conversation_id, user_id=user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    messages = (
        db.query(ChatMessage)
        .filter_by(conversation_id=conversation_id, user_id=user.id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )
    return messages


@router.delete("/conversations/{conversation_id}")
def delete_conversation(
    conversation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    conv = db.query(ChatConversation).filter_by(id=conversation_id, user_id=user.id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    db.delete(conv)
    db.commit()
    return {"status": "success", "message": "Conversation deleted."}


@router.get("/chat", response_model=List[ChatHistoryItem])
@router.get("/history", response_model=List[ChatHistoryItem])
def get_chat_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    messages = (
        db.query(ChatMessage)
        .filter_by(user_id=user.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(50)
        .all()
    )
    return messages
