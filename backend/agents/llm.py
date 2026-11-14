import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from typing import Any

from dotenv import load_dotenv

load_dotenv()


class LLMProviderError(RuntimeError):
    pass


def mock_mode() -> bool:
    return os.getenv("LLM_MODE", "").strip().casefold() == "mock" or not os.getenv(
        "GEMINI_API_KEY"
    )


def generate_text(prompt: str, *, temperature: float = 0.4) -> str:
    """Generate explanatory text; without a key callers use deterministic text instead."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or os.getenv("LLM_MODE", "").strip().casefold() == "mock":
        raise LLMProviderError("Gemini is unavailable in offline mock mode")
    model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    request = Request(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}",
        data=json.dumps(
            {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"temperature": temperature},
            }
        ).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=20) as response:
            body: dict[str, Any] = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError) as error:
        raise LLMProviderError(f"Gemini request failed: {error}") from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise LLMProviderError("Gemini returned an invalid response") from error
    try:
        return str(body["candidates"][0]["content"]["parts"][0]["text"]).strip()
    except (KeyError, IndexError, TypeError) as error:
        raise LLMProviderError("Gemini response did not contain generated text") from error


def generate_json(prompt: str) -> dict[str, Any]:
    text = generate_text(prompt, temperature=0.3)
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        start, end = text.find("{"), text.rfind("}")
        if start < 0 or end <= start:
            raise LLMProviderError("Gemini did not return valid JSON")
        try:
            parsed = json.loads(text[start : end + 1])
        except json.JSONDecodeError as error:
            raise LLMProviderError("Gemini did not return valid JSON") from error
    if not isinstance(parsed, dict):
        raise LLMProviderError("Gemini JSON response must be an object")
    return parsed
