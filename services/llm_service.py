import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from dotenv import load_dotenv
from fastapi import HTTPException
import httpx
from ollama import Client as OllamaClient
from ollama import ResponseError as OllamaResponseError

from services.prompt_service import build_generation_prompt
from services.settings_service import get_settings_service

load_dotenv()

# Ollama: model name must be set in the environment (OLLAMA_MODEL). Host: OLLAMA_HOST or client default.
OLLAMA_TIMEOUT_SEC = float(os.getenv("OLLAMA_TIMEOUT_SEC", "300"))

# When OLLAMA is off/unset, model is always gemini-2.5-flash (cloud).
GEMINI_MODEL_NAME = "gemini-2.5-flash"

INVALID_GEMINI_KEY_MESSAGE = (
    "Gemini API key is invalid, revoked, or not allowed for this API. "
    "Set a valid GEMINI_API_KEY in your server environment (.env) and restart the app."
)
GENERIC_GEMINI_MESSAGE = (
    "The Gemini API rejected this request. Check your API key, model access, and billing, then try again."
)
GEMINI_UNAVAILABLE_MESSAGE = (
    "The Gemini API is temporarily unavailable. Please try again in a moment."
)


def _is_invalid_api_key_error(exc) -> bool:
    msg = (exc.message or "").lower()
    if "api key" in msg and ("invalid" in msg or "not valid" in msg):
        return True
    body = exc.details
    if isinstance(body, dict):
        nested = body.get("error") or {}
        for item in nested.get("details") or []:
            if isinstance(item, dict) and item.get("reason") == "API_KEY_INVALID":
                return True
    if body and "API_KEY_INVALID" in str(body):
        return True
    return False


def _raise_http_for_gemini_error(exc) -> None:
    from google.genai import errors as genai_errors

    if isinstance(exc, genai_errors.ClientError):
        if _is_invalid_api_key_error(exc):
            raise HTTPException(status_code=502, detail=INVALID_GEMINI_KEY_MESSAGE) from exc
        raise HTTPException(status_code=502, detail=GENERIC_GEMINI_MESSAGE) from exc
    if isinstance(exc, genai_errors.ServerError):
        raise HTTPException(status_code=503, detail=GEMINI_UNAVAILABLE_MESSAGE) from exc
    raise HTTPException(status_code=502, detail=GENERIC_GEMINI_MESSAGE) from exc


def _ollama_host_hint() -> str:
    """Human-readable host for errors; mirrors ollama.Client default (OLLAMA_HOST or 127.0.0.1:11434)."""
    h = os.getenv("OLLAMA_HOST", "").strip()
    return h if h else "http://127.0.0.1:11434 (Ollama default)"


def _ollama_generate(client: OllamaClient, model: str, prompt: str) -> str:
    try:
        response = client.generate(model=model, prompt=prompt, stream=False)
    except ConnectionError as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Cannot connect to Ollama at {_ollama_host_hint()}. "
                "Install Ollama, run `ollama serve`, or set OLLAMA_HOST if the daemon is elsewhere."
            ),
        ) from exc
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="The local model took too long to respond. Try again, use a smaller prompt, or pick a lighter model.",
        ) from exc
    except OllamaResponseError as exc:
        err_text = exc.error if isinstance(exc.error, str) else str(exc.error)
        if exc.status_code == 404:
            raise HTTPException(
                status_code=502,
                detail=f"Ollama model '{model}' is not available. Run: ollama pull {model}",
            ) from exc
        raise HTTPException(
            status_code=502,
            detail=f"Ollama error: {err_text}",
        ) from exc

    text = (response.response or "").strip()
    if not text:
        raise HTTPException(
            status_code=502,
            detail="Ollama returned an empty response. Check OLLAMA_MODEL and the prompt.",
        )
    return text


def _append_llm_log(provider: str, model: str, product_info: str, voice: str, output: str) -> None:
    try:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "provider": provider,
            "model": model,
            "input": product_info,
            "voice": voice,
            "output": output,
        }
        with open("llm_responses.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[Warning] Failed to log response: {e}")


class BaseAdService(ABC):
    @abstractmethod
    def generate_response(self, product_info: str, voice: str) -> str:
        pass


class OllamaAdService(BaseAdService):
    """Local model via ollama.Client().generate(); model name from OLLAMA_MODEL env only."""

    def __init__(self):
        self.model = os.getenv("OLLAMA_MODEL", "").strip()
        if not self.model:
            raise ValueError(
                "OLLAMA_MODEL is not set. Add it to your environment (e.g. OLLAMA_MODEL=llama2 in .env)."
            )
        print(f"🚀 [System] LLM: Ollama — model {self.model!r} (client.generate)")
        self._client = OllamaClient(timeout=OLLAMA_TIMEOUT_SEC)
        self.settings_svc = get_settings_service()

    def generate_response(
        self, product_info: str, voice: str = "Professional", prompt_type: str = "ad_generator"
    ) -> str:
        settings = self.settings_svc.get_settings()
        persona = settings.get("system_persona")
        prompt = build_generation_prompt(product_info, voice, persona, prompt_type)

        result = _ollama_generate(self._client, self.model, prompt)
        print("\n=== OLLAMA RESPONSE ===")
        print(result)
        print("=== END RESPONSE ===\n")

        _append_llm_log("ollama", self.model, product_info, voice, result)
        return result


class GeminiAdService(BaseAdService):
    """Google Gemini API (used when OLLAMA is not enabled)."""

    def __init__(self):
        print(f"🚀 [System] LLM: Gemini — model {GEMINI_MODEL_NAME!r} (cloud)")
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Set it when OLLAMA is not enabled, or set OLLAMA=true for local Ollama."
            )
        self.model = GEMINI_MODEL_NAME
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self.settings_svc = get_settings_service()

    def generate_response(
        self, product_info: str, voice: str = "Professional", prompt_type: str = "ad_generator"
    ) -> str:
        from google.genai import errors as genai_errors

        settings = self.settings_svc.get_settings()
        persona = settings.get("system_persona")
        prompt = build_generation_prompt(product_info, voice, persona, prompt_type)

        try:
            response = self._client.models.generate_content(
                model=self.model,
                contents=prompt,
            )
        except genai_errors.APIError as e:
            _raise_http_for_gemini_error(e)

        result = response.text.strip()
        print("\n=== GEMINI RESPONSE ===")
        print(result)
        print("=== END RESPONSE ===\n")

        _append_llm_log("gemini", self.model, product_info, voice, result)
        return result


class MockLlmService(BaseAdService):
    """Mock LLM for tests without network."""

    def generate_response(
        self, product_info: str, voice: str, prompt_type: str = "ad_generator"
    ) -> str:
        try:
            product_name = "Product"
            if "PRODUCT:" in product_info:
                product_line = product_info.split("PRODUCT:")[1].split(".")[0].strip()
                product_name = (
                    product_line.split("-")[0].strip()
                    if "-" in product_line
                    else product_line[:30]
                )
            else:
                product_name = product_info[:50].strip()

            if prompt_type == "sms_campaign":
                customer_name = "Customer"
                if "CUSTOMER:" in product_info:
                    customer_line = product_info.split("CUSTOMER:")[1].split("\n")[0].strip()
                    customer_name = customer_line
                return (
                    f"Hi {customer_name}! 🎉 Check out our {product_name}! "
                    f"Special offer just for you. Reply YES for details!"
                )

            return f"""FACEBOOK:
🎉 Introducing {product_name} - Your Perfect Choice!

Discover amazing features and unbeatable value. Limited time offer - don't miss out!

💰 Special Price Available
🚚 Free Delivery
⭐ Premium Quality

Shop now and experience the difference!

#NewArrival #SpecialOffer #ShopNow

INSTAGRAM:
✨ Say hello to {product_name}! ✨

Your lifestyle upgrade is here! 🎯

✅ Premium quality
✅ Best price guaranteed
✅ Fast delivery

Tag a friend who needs this! 👇

#Shopping #Lifestyle #MustHave #Trending

TWITTER:
🔥 {product_name} is here!

Premium quality + Great price = Perfect deal! 🎯

Limited stock available. Order now! 🛒

#Deals #Shopping #NewProduct

WHATSAPP:
Hi there! 👋

Excited to share our new {product_name} with you!

✅ Premium quality
✅ Special pricing
✅ FREE delivery

Interested? Let me know! 😊

TEXTMESSAGE:
New arrival: {product_name}! Premium quality, special price, FREE delivery. Order now! Reply YES for details."""

        except Exception as e:
            print(f"[MockLlm] Error generating response: {e}")
            return """FACEBOOK:
🎉 New Product Available!

Check out our latest offering with amazing features!

#NewArrival #ShopNow

INSTAGRAM:
✨ Something special just arrived! ✨

#Shopping #MustHave

TWITTER:
🔥 New product alert!

#Deals #Shopping

WHATSAPP:
Hi! Check out our new product!

TEXTMESSAGE:
New arrival! Order now!"""


def _ollama_env_enabled() -> bool:
    """
    True → local Ollama (OLLAMA_MODEL must be set in env when this backend is used).
    Uses OLLAMA if set (truthy: 1/true/yes/on; falsy: 0/false/no/off).
    If OLLAMA is unset/empty, falls back to legacy LLM_PROVIDER=ollama|local|llama|llama2.
    """
    raw = os.getenv("OLLAMA")
    if raw is not None and raw.strip() != "":
        return raw.strip().lower() in ("1", "true", "yes", "on")
    legacy = (os.getenv("LLM_PROVIDER") or "").strip().lower()
    return legacy in ("ollama", "local", "llama", "llama2")


def _create_backend_for_env() -> BaseAdService:
    if os.getenv("ENV_MODE", "test").strip().lower() == "test":
        return MockLlmService()

    if _ollama_env_enabled():
        return OllamaAdService()
    return GeminiAdService()


_instance = None


def get_llm_service() -> BaseAdService:
    global _instance
    if _instance is None:
        _instance = _create_backend_for_env()
    return _instance


get_gemini_service = get_llm_service
MockGeminiService = MockLlmService
