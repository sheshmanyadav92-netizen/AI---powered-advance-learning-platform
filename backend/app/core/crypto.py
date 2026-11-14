import base64
import hashlib
from cryptography.fernet import Fernet
from .config import settings

def _get_fernet() -> Fernet:
    # Deterministically derive 32-byte urlsafe base64 key from secret key
    derived_bytes = hashlib.sha256(settings.SECRET_KEY.encode("utf-8")).digest()
    key = base64.urlsafe_b64encode(derived_bytes)
    return Fernet(key)

def encrypt_secret(raw: str) -> str:
    """Encrypt a secret string using Fernet."""
    if not raw:
        return ""
    f = _get_fernet()
    return f.encrypt(raw.encode("utf-8")).decode("utf-8")

def decrypt_secret(encrypted: str) -> str:
    """Decrypt a Fernet encrypted string."""
    if not encrypted:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(encrypted.encode("utf-8")).decode("utf-8")
    except Exception:
        return ""

def mask_key(raw_key: str) -> str:
    """Produce a safe masked preview of an API key, e.g. ****1234."""
    if not raw_key:
        return ""
    if len(raw_key) <= 4:
        return "****"
    return f"****{raw_key[-4:]}"

