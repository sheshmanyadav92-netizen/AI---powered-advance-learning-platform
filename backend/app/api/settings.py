"""Settings endpoints for theme configuration and encrypted multi-provider LLM API key management."""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..models import get_db, User, UserSettings
from ..core.crypto import encrypt_secret, decrypt_secret, mask_key
from ..core.llm import llm_service, DEFAULT_MODELS, PROVIDER_MODELS
from .deps import get_current_user

router = APIRouter(prefix="/settings", tags=["User Settings"])


class SettingsResponse(BaseModel):
    theme: str
    llm_provider: str
    llm_model: str
    has_api_key: bool
    key_masked: str | None


class LLMConfigResponse(BaseModel):
    provider: str
    model: str
    has_api_key: bool
    key_masked: Optional[str] = None
    default_models: Dict[str, str]
    provider_models: Dict[str, List[str]]
    theme: str


class UpdateThemeRequest(BaseModel):
    theme: str = Field(..., pattern="^(dark|light)$")


class SaveLLMKeyRequest(BaseModel):
    provider: str = Field(default="groq", pattern="^(groq|openrouter|nvidia|nvidia-nim|openai|gemini|claude|anthropic)$")
    model: str = Field(default="", max_length=150)
    api_key: str = Field(..., min_length=4, max_length=500)


class SaveLLMKeyResponse(BaseModel):
    message: str
    provider: str
    model: str
    has_api_key: bool
    key_masked: str


class LLMTestRequest(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None


class LLMTestResponse(BaseModel):
    success: bool
    status_code: int
    latency_ms: float
    provider: str
    model: str
    message: str


def _get_or_create_settings(user: User, db: Session) -> UserSettings:
    settings = db.query(UserSettings).filter(UserSettings.user_id == user.id).first()
    if not settings:
        settings = UserSettings(
            user_id=user.id,
            theme="dark",
            llm_provider="groq",
            llm_model=DEFAULT_MODELS.get("groq", "qwen/qwen3.8-27b"),
            llm_api_key_encrypted=None,
            updated_at=datetime.now(timezone.utc),
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings


@router.get("", response_model=SettingsResponse)
def get_user_settings(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(user, db)
    raw_key = decrypt_secret(settings.llm_api_key_encrypted) if settings.llm_api_key_encrypted else ""
    return SettingsResponse(
        theme=settings.theme,
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model or DEFAULT_MODELS.get(settings.llm_provider, ""),
        has_api_key=bool(raw_key),
        key_masked=mask_key(raw_key) if raw_key else None,
    )


@router.get("/llm-config", response_model=LLMConfigResponse)
def get_llm_configuration(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns safe, unexposed LLM configuration for the frontend Settings dashboard."""
    settings = _get_or_create_settings(user, db)
    raw_key = decrypt_secret(settings.llm_api_key_encrypted) if settings.llm_api_key_encrypted else ""
    return LLMConfigResponse(
        provider=settings.llm_provider,
        model=settings.llm_model or DEFAULT_MODELS.get(settings.llm_provider, ""),
        has_api_key=bool(raw_key),
        key_masked=mask_key(raw_key) if raw_key else None,
        default_models=DEFAULT_MODELS,
        provider_models=PROVIDER_MODELS,
        theme=settings.theme,
    )


@router.put("/theme")
def update_theme(
    payload: UpdateThemeRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(user, db)
    settings.theme = payload.theme
    settings.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "success", "theme": settings.theme}


@router.post("/llm-key", response_model=SaveLLMKeyResponse)
def save_llm_key(
    payload: SaveLLMKeyRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    clean_key = payload.api_key.strip()
    if not clean_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="API key cannot be empty",
        )

    # Server-side Fernet encryption
    encrypted_key = encrypt_secret(clean_key)
    masked = mask_key(clean_key)

    chosen_provider = payload.provider.lower()
    chosen_model = payload.model.strip() or DEFAULT_MODELS.get(chosen_provider, "")

    settings = _get_or_create_settings(user, db)
    settings.llm_provider = chosen_provider
    settings.llm_model = chosen_model
    settings.llm_api_key_encrypted = encrypted_key
    settings.updated_at = datetime.now(timezone.utc)
    db.commit()

    return SaveLLMKeyResponse(
        message=f"Key saved (ending {masked})",
        provider=settings.llm_provider,
        model=settings.llm_model,
        has_api_key=True,
        key_masked=masked,
    )


@router.post("/llm-test", response_model=LLMTestResponse)
def test_llm_connection(
    payload: LLMTestRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Tests live connection to the specified or stored provider without exposing secrets."""
    settings = _get_or_create_settings(user, db)
    target_provider = (payload.provider or settings.llm_provider or "groq").lower()
    target_model = payload.model or settings.llm_model or DEFAULT_MODELS.get(target_provider, "")

    # Use provided key or decrypt stored key
    if payload.api_key and payload.api_key.strip():
        raw_key = payload.api_key.strip()
    else:
        raw_key = decrypt_secret(settings.llm_api_key_encrypted) if settings.llm_api_key_encrypted else ""

    if not raw_key:
        return LLMTestResponse(
            success=False,
            status_code=400,
            latency_ms=0.0,
            provider=target_provider,
            model=target_model,
            message="No API key provided or saved in settings. Please enter a key to test."
        )

    res = llm_service.test_connection(target_provider, target_model, raw_key)
    return LLMTestResponse(
        success=res["success"],
        status_code=res["status_code"],
        latency_ms=res["latency_ms"],
        provider=res["provider"],
        model=res["model"],
        message=res["message"],
    )


@router.delete("/llm-key")
def delete_llm_key(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = _get_or_create_settings(user, db)
    settings.llm_api_key_encrypted = None
    settings.updated_at = datetime.now(timezone.utc)
    db.commit()
    return {"status": "success", "message": "API key removed successfully."}
