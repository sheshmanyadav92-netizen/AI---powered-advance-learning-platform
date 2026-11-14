"""Multi-provider LLM service supporting Groq, NVIDIA NIM, OpenRouter, OpenAI,
Google Gemini, and Anthropic Claude via a unified interface with live LearnerState grounding.
"""
import os
import json
import time
import httpx
from typing import Dict, Any, List, Optional

OPENAI_COMPATIBLE_BASE_URLS = {
    "groq": "https://api.groq.com/openai/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "nvidia": "https://integrate.api.nvidia.com/v1",
    "nvidia-nim": "https://integrate.api.nvidia.com/v1",
    "openai": "https://api.openai.com/v1",
}

DEFAULT_MODELS = {
    "groq": "qwen/qwen3.8-27b",
    "nvidia": "minimaxai/minimax-m3.1-flash",
    "nvidia-nim": "minimaxai/minimax-m3.1-flash",
    "openrouter": "meta-llama/llama-3.3-70b-instruct",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-1.5-flash",
    "claude": "claude-3-haiku-20240307",
    "anthropic": "claude-3-haiku-20240307",
}

PROVIDER_MODELS = {
    "groq": [
        "qwen/qwen3.8-27b",
        "openai/gpt-oss-120b",
        "llama-3.3-70b-versatile",
        "allam-2-7b"
    ],
    "nvidia": [
        "minimaxai/minimax-m3.1-flash",
        "meta/llama-3.2-90b-vision-instruct",
        "mistralai/mistral-large-2-instruct",
        "deepseek-ai/deepseek-coder-6.7b-instruct"
    ],
    "openrouter": [
        "meta-llama/llama-3.3-70b-instruct",
        "deepseek/deepseek-chat",
        "google/gemini-2.0-flash-exp:free"
    ],
    "openai": [
        "gpt-4o-mini",
        "gpt-4o"
    ],
    "gemini": [
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ],
    "claude": [
        "claude-3-haiku-20240307",
        "claude-3-5-sonnet-20241022"
    ]
}


class LLMService:
    def __init__(self):
        self.provider = os.getenv("MENTOR_LLM_PROVIDER", "local").lower().strip()
        self.api_key = os.getenv("MENTOR_LLM_API_KEY", "").strip()

    def test_connection(self, provider: str, model: str, api_key: str) -> Dict[str, Any]:
        """Validates provider credentials, endpoint latency, and model availability."""
        p = provider.lower().strip()
        m = model.strip() if model else DEFAULT_MODELS.get(p, "gpt-4o-mini")
        k = api_key.strip()
        if not k:
            return {
                "success": False,
                "status_code": 400,
                "latency_ms": 0,
                "provider": p,
                "model": m,
                "message": "API key cannot be empty."
            }

        start_time = time.time()
        try:
            if p in OPENAI_COMPATIBLE_BASE_URLS:
                base_url = OPENAI_COMPATIBLE_BASE_URLS[p]
                url = f"{base_url.rstrip('/')}/chat/completions"
                headers = {
                    "Authorization": f"Bearer {k}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": m,
                    "messages": [{"role": "user", "content": "Ping test."}],
                    "max_tokens": 5
                }
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    latency = round((time.time() - start_time) * 1000, 1)
                    if resp.status_code == 200:
                        return {
                            "success": True,
                            "status_code": 200,
                            "latency_ms": latency,
                            "provider": p,
                            "model": m,
                            "message": f"Successfully connected to {p.upper()} ({m}) in {latency}ms."
                        }
                    else:
                        error_detail = resp.text[:250]
                        try:
                            err_json = resp.json()
                            if "error" in err_json:
                                error_detail = err_json["error"].get("message", error_detail)
                            elif "detail" in err_json:
                                error_detail = err_json["detail"]
                        except Exception:
                            pass
                        return {
                            "success": False,
                            "status_code": resp.status_code,
                            "latency_ms": latency,
                            "provider": p,
                            "model": m,
                            "message": f"Provider returned HTTP {resp.status_code}: {error_detail}"
                        }
            elif p == "gemini":
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={k}"
                payload = {"contents": [{"role": "user", "parts": [{"text": "Ping"}]}]}
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(url, json=payload)
                    latency = round((time.time() - start_time) * 1000, 1)
                    if resp.status_code == 200:
                        return {
                            "success": True,
                            "status_code": 200,
                            "latency_ms": latency,
                            "provider": p,
                            "model": m,
                            "message": f"Successfully connected to Google Gemini ({m}) in {latency}ms."
                        }
                    else:
                        return {
                            "success": False,
                            "status_code": resp.status_code,
                            "latency_ms": latency,
                            "provider": p,
                            "model": m,
                            "message": f"Gemini returned HTTP {resp.status_code}: {resp.text[:200]}"
                        }
            elif p in ("claude", "anthropic"):
                url = "https://api.anthropic.com/v1/messages"
                headers = {
                    "x-api-key": k,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                }
                payload = {
                    "model": m,
                    "max_tokens": 5,
                    "messages": [{"role": "user", "content": "Ping"}]
                }
                with httpx.Client(timeout=12.0) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    latency = round((time.time() - start_time) * 1000, 1)
                    if resp.status_code == 200:
                        return {
                            "success": True,
                            "status_code": 200,
                            "latency_ms": latency,
                            "provider": p,
                            "model": m,
                            "message": f"Successfully connected to Anthropic Claude ({m}) in {latency}ms."
                        }
                    else:
                        return {
                            "success": False,
                            "status_code": resp.status_code,
                            "latency_ms": latency,
                            "provider": p,
                            "model": m,
                            "message": f"Claude returned HTTP {resp.status_code}: {resp.text[:200]}"
                        }
            else:
                return {
                    "success": False,
                    "status_code": 400,
                    "latency_ms": 0,
                    "provider": p,
                    "model": m,
                    "message": f"Unsupported provider: {p}"
                }
        except httpx.TimeoutException:
            return {
                "success": False,
                "status_code": 504,
                "latency_ms": round((time.time() - start_time) * 1000, 1),
                "provider": p,
                "model": m,
                "message": f"Connection timed out while contacting {p} API."
            }
        except Exception as exc:
            return {
                "success": False,
                "status_code": 500,
                "latency_ms": round((time.time() - start_time) * 1000, 1),
                "provider": p,
                "model": m,
                "message": f"Connection error: {str(exc)}"
            }

    def generate_mentor_response(
        self,
        user_message: str,
        learner_context: Dict[str, Any],
        history: List[Dict[str, str]],
        api_key: str = "",
        provider: str = "",
        model: str = "",
    ) -> str:
        """Generates grounded mentor response across any configured provider.
        Never fabricates mock responses when an external provider call fails.
        """
        system_context = self._build_grounded_system_prompt(learner_context)
        active_key = api_key.strip() if api_key else self.api_key
        active_provider = (provider.strip().lower() if provider else self.provider).lower()
        active_model = model.strip() if model else DEFAULT_MODELS.get(active_provider, "gpt-4o-mini")

        if not active_key or active_provider == "local":
            return (
                "👋 **Welcome to your AI Academic Mentor!**\n\n"
                "To activate live AI responses grounded in your personal LearnerState, "
                "please open **Settings** (⚙️ in the left sidebar), select your preferred provider "
                "(Groq, NVIDIA NIM, or OpenRouter), and enter your API key.\n\n"
                "Your key is encrypted server-side using AES-128 Fernet cryptography and never exposed."
            )

        # 1. OpenAI-compatible providers: Groq, OpenRouter, NVIDIA NIM, OpenAI
        if active_provider in OPENAI_COMPATIBLE_BASE_URLS:
            base_url = OPENAI_COMPATIBLE_BASE_URLS[active_provider]
            return self._call_openai_compatible(
                user_message=user_message,
                sys_prompt=system_context,
                history=history,
                api_key=active_key,
                base_url=base_url,
                model=active_model,
                provider_name=active_provider
            )

        # 2. Google Gemini
        elif active_provider == "gemini":
            return self._call_gemini(
                user_msg=user_message,
                sys_prompt=system_context,
                history=history,
                api_key=active_key,
                model=active_model
            )

        # 3. Anthropic Claude
        elif active_provider in ("claude", "anthropic"):
            return self._call_claude(
                user_msg=user_message,
                sys_prompt=system_context,
                history=history,
                api_key=active_key,
                model=active_model
            )

        return f"⚠️ Unsupported provider: {active_provider}. Please configure Groq, NVIDIA, or OpenRouter in Settings."

    def _build_grounded_system_prompt(self, context: Dict[str, Any]) -> str:
        skills = context.get("skills", {})
        gap_rep = context.get("gap_report", {})
        bkt = context.get("bkt_states", {})
        recs = context.get("recommendations", [])
        role = gap_rep.get("role_title", "Full Stack Developer")
        readiness = gap_rep.get("readiness", 0.0)
        cosine = gap_rep.get("cosine_fit", 0.0)

        facts = [
            "You are the AI Academic Mentor for Demo Learner.",
            f"Target Career Goal: {role}.",
            f"Overall Career Readiness: {readiness:.2f}%. Vector-Space CosineFit: {cosine:.4f}.",
            "Current Verified Competencies (P_s):"
        ]
        for sid, s in skills.items():
            facts.append(
                f"- {s.get('name')}: P_s={float(s.get('P_s', 0.0)):.1f}% "
                f"(Self A_s={s.get('A_s')}, Quiz Q_s={s.get('Q_s')}, Evidence E_s={s.get('E_s')})"
            )

        facts.append("Skill Gaps (G_s = max(0, R_s - P_s)):")
        for g in gap_rep.get("details", []):
            facts.append(f"- {g['skill_name']}: Gap G_s={float(g['G_s']):.1f} (Required R_s={g['R_s']}, Importance I_s={g['I_s']})")

        facts.append("Bayesian Knowledge Tracing (BKT) Mastery Beliefs P(L_n):")
        for sid, b in bkt.items():
            p_m = float(b.get('p_mastery', 0.3))
            attempts = b.get('attempts_count', 0)
            remed = b.get('needs_remediation', False)
            cert_eligible = p_m >= 0.80
            facts.append(f"- Skill #{sid}: P(L_n)={p_m:.3f}, Attempts={attempts}, RemediationActive={remed}, CertificateEarned={cert_eligible}")

        facts.append("Top Priority Recommendations (ROI Priority_s = (G_s * I_s) / T_s):")
        for r in recs[:3]:
            facts.append(
                f"- {r.get('resource_title')} ({r.get('skill_name')}): "
                f"Priority={float(r.get('priority_score', 0.0)):.3f}, Est={r.get('est_hours')}h, Diff Level {r.get('difficulty')}"
            )

        facts.append(
            "\nCRITICAL PEDAGOGICAL INSTRUCTIONS:\n"
            "1. When answering questions regarding progress, readiness, gaps, scores, or what to learn next, "
            "you MUST ONLY cite the exact numbers from the LearnerState above. Never invent metrics.\n"
            "2. If remediation is active for any skill, explain that instructional difficulty has been "
            "scaffolded down by 1 level due to P(L_n) < 0.50 after 3+ attempts.\n"
            "3. If mastery P(L_n) >= 0.80, congratulate the learner on earning an official Course Certificate.\n"
            "4. For technical concepts, coding examples, or study roadmaps, provide detailed, supportive, high-quality guidance."
        )
        return "\n".join(facts)

    def _call_openai_compatible(
        self,
        user_message: str,
        sys_prompt: str,
        history: List[Dict[str, str]],
        api_key: str,
        base_url: str,
        model: str,
        provider_name: str,
    ) -> str:
        messages = [{"role": "system", "content": sys_prompt}]
        for h in history[-8:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
        messages.append({"role": "user", "content": user_message})

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 1024,
        }
        url = f"{base_url.rstrip('/')}/chat/completions"

        last_error = None
        # Up to 1 retry for transient connection timeouts or 5xx
        for attempt in range(2):
            try:
                with httpx.Client(timeout=25.0) as client:
                    resp = client.post(url, json=payload, headers=headers)
                    if resp.status_code == 200:
                        data = resp.json()
                        choice = data.get("choices", [{}])[0]
                        msg = choice.get("message", {})
                        content = msg.get("content")
                        if content:
                            return content
                        # Some models (like Minimax on NVIDIA) might put output in reasoning_content
                        if msg.get("reasoning_content"):
                            return msg["reasoning_content"]
                        return "Received empty completion response from model."
                    elif resp.status_code in (401, 403):
                        return f"⚠️ **Authentication Failed ({provider_name.upper()})**: Invalid or expired API key. Please check your credentials in Settings."
                    elif resp.status_code == 410:
                        return f"⚠️ **Model Deprecated ({provider_name.upper()} - {model})**: This model has reached end of life. Please switch to an active model (e.g. `{DEFAULT_MODELS.get(provider_name)}`) in Settings."
                    elif resp.status_code == 429:
                        return f"⚠️ **Rate Limit Exceeded ({provider_name.upper()})**: Provider quota or rate limit exceeded. Please wait a moment or switch providers."
                    else:
                        error_msg = resp.text[:250]
                        try:
                            err_json = resp.json()
                            if "error" in err_json:
                                error_msg = err_json["error"].get("message", error_msg)
                            elif "detail" in err_json:
                                error_msg = err_json["detail"]
                        except Exception:
                            pass
                        last_error = f"HTTP {resp.status_code}: {error_msg}"
                        # Do not retry 4xx errors
                        if 400 <= resp.status_code < 500:
                            break
            except httpx.TimeoutException:
                last_error = "Request timed out after 25 seconds."
            except Exception as e:
                last_error = str(e)

        return f"⚠️ **{provider_name.upper()} Error**: {last_error or 'Unknown failure'}. Please verify model `{model}` in Settings."

    def _call_gemini(
        self,
        user_msg: str,
        sys_prompt: str,
        history: List[Dict[str, str]],
        api_key: str,
        model: str,
    ) -> str:
        model_name = model or "gemini-1.5-flash"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
        contents = [{"role": "user", "parts": [{"text": sys_prompt + "\n\nUser Question: " + user_msg}]}]
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(url, json={"contents": contents})
                if resp.status_code == 200:
                    data = resp.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        return candidates[0]["content"]["parts"][0]["text"]
                return f"⚠️ **Gemini Error**: HTTP {resp.status_code} - {resp.text[:200]}"
        except Exception as e:
            return f"⚠️ **Gemini Connection Error**: {str(e)}"

    def _call_claude(
        self,
        user_msg: str,
        sys_prompt: str,
        history: List[Dict[str, str]],
        api_key: str,
        model: str,
    ) -> str:
        model_name = model or "claude-3-haiku-20240307"
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        messages = [{"role": "user", "content": user_msg}]
        body = {
            "model": model_name,
            "max_tokens": 1024,
            "system": sys_prompt,
            "messages": messages,
        }
        try:
            with httpx.Client(timeout=20.0) as client:
                resp = client.post(url, json=body, headers=headers)
                if resp.status_code == 200:
                    return resp.json()["content"][0]["text"]
                return f"⚠️ **Claude Error**: HTTP {resp.status_code} - {resp.text[:200]}"
        except Exception as e:
            return f"⚠️ **Claude Connection Error**: {str(e)}"


llm_service = LLMService()
