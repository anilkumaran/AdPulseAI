import json
import os
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime
from dotenv import load_dotenv
from fastapi import HTTPException
import httpx
from ollama import Client as OllamaClient
from ollama import ResponseError as OllamaResponseError

from .prompt_service import build_generation_prompt
from .settings_service import get_settings_service

_DOTENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_DOTENV_PATH, override=True)

OLLAMA_TIMEOUT_SEC = float(os.getenv("OLLAMA_TIMEOUT_SEC", "300"))
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
        # Always write logs next to the backend package (api/llm_responses.jsonl),
        # independent of current working directory.
        log_path = Path(__file__).resolve().parents[1] / "llm_responses.jsonl"
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except OSError as e:
        print(f"[Warning] Failed to log response: {e}")


class BaseAdService(ABC):
    @abstractmethod
    def generate_response(self, product_info: str, voice: str) -> str:
        pass


class OllamaAdService(BaseAdService):
    """Local model via ollama.Client().generate()."""

    def __init__(self, model: str):
        self.model = (model or "").strip()
        if not self.model:
            raise ValueError("Ollama model name is empty.")
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
                # Keep names readable without aggressive truncation.
                # Only split on a *clear* "name - details" pattern (space-hyphen-space).
                base = product_line.split(" - ")[0].strip() if " - " in product_line else product_line
                base = " ".join(base.split())
                product_name = base if len(base) <= 70 else (base[:67].rstrip() + "…")
            else:
                base = " ".join(product_info.strip().split())
                product_name = base if len(base) <= 70 else (base[:67].rstrip() + "…")

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


def _ollama_env_raw() -> str | None:
    """Trimmed OLLAMA env or None."""
    raw = os.getenv("OLLAMA")
    if raw is None:
        return None
    s = raw.strip()
    return s if s else None


def _ollama_truthy(val: str) -> bool:
    return val.strip().lower() in ("1", "true", "yes", "on")


def _ollama_falsy(val: str) -> bool:
    return val.strip().lower() in ("0", "false", "no", "off")


def _ollama_force_local() -> bool:
    """OLLAMA=true: Ollama only."""
    raw = _ollama_env_raw()
    return raw is not None and _ollama_truthy(raw)


def _ollama_skip_local() -> bool:
    """OLLAMA=false: Gemini only."""
    raw = _ollama_env_raw()
    return raw is not None and _ollama_falsy(raw)


def _ollama_try_local_default() -> bool:
    """OLLAMA unset: try Ollama, then Gemini."""
    return _ollama_env_raw() is None


def _ollama_model_candidates() -> list[str]:
    """Ollama model order: OLLAMA_MODEL, then LLM_MODEL_CANDIDATES, else llama2."""
    candidates: list[str] = []

    env_model = (os.getenv("OLLAMA_MODEL") or "").strip()
    if env_model:
        candidates.append(env_model)

    extra = (os.getenv("LLM_MODEL_CANDIDATES") or "").strip()
    if extra:
        for part in extra.split(","):
            m = part.strip()
            if m:
                candidates.append(m)

    if not candidates:
        candidates = ["llama2"]

    out: list[str] = []
    seen: set[str] = set()
    for m in candidates:
        if m not in seen:
            out.append(m)
            seen.add(m)
    return out


def _ollama_model_name_from_obj(item) -> str | None:
    """Normalize ollama list() entries to e.g. llama2:latest."""
    if isinstance(item, str):
        return item.strip() or None
    if isinstance(item, dict):
        name = item.get("name") or item.get("model")
        return name.strip() if isinstance(name, str) and name.strip() else None
    for attr in ("model", "name"):
        v = getattr(item, attr, None)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _ollama_base_tag(model_name: str) -> str:
    """'llama2:latest' -> 'llama2' ; 'llama3.2' -> 'llama3.2'"""
    s = model_name.strip()
    if ":" in s:
        return s.split(":", 1)[0].strip()
    return s


def _ollama_pick_installed_model(installed: set[str], want: str) -> str | None:
    """Match tag-less name (e.g. llama2) to an installed model string."""
    want = want.strip()
    if not want:
        return None

    if want in installed:
        return want

    want_base = _ollama_base_tag(want)
    candidate = f"{want_base}:latest"
    if candidate in installed:
        return candidate

    for name in sorted(installed):
        if _ollama_base_tag(name) == want_base:
            return name
    return None


def _ollama_available_model_set(client: OllamaClient) -> set[str] | None:
    """Installed model names, or None if unreachable."""
    try:
        data = client.list()
    except Exception:
        return None

    models = None
    if isinstance(data, dict):
        models = data.get("models")
    else:
        models = getattr(data, "models", None)

    if models is None:
        return set()

    names: set[str] = set()
    if isinstance(models, list):
        for item in models:
            n = _ollama_model_name_from_obj(item)
            if n:
                names.add(n)
    return names


def _try_create_ollama_backend() -> BaseAdService | None:
    """Return Ollama backend or None for Gemini fallback."""
    client = OllamaClient(timeout=OLLAMA_TIMEOUT_SEC)
    available = _ollama_available_model_set(client)
    if available is None:
        print(f"⚠️  [System] Ollama not reachable at {_ollama_host_hint()} — falling back to Gemini")
        return None

    candidates = _ollama_model_candidates()
    chosen_name: str | None = None
    for want in candidates:
        picked = _ollama_pick_installed_model(available, want)
        if picked:
            chosen_name = picked
            break

    if not chosen_name:
        print(
            "⚠️  [System] No configured Ollama model is installed. "
            f"Tried: {candidates}. Installed: {sorted(available)}. Falling back to Gemini."
        )
        return None

    svc = OllamaAdService(model=chosen_name)
    svc._client = client
    return svc


def _create_ollama_backend_required() -> BaseAdService:
    """OLLAMA=true: require working Ollama + model."""
    client = OllamaClient(timeout=OLLAMA_TIMEOUT_SEC)
    available = _ollama_available_model_set(client)
    if available is None:
        raise HTTPException(
            status_code=503,
            detail=(
                f"OLLAMA=true but cannot connect to Ollama at {_ollama_host_hint()}. "
                "Start Ollama (`ollama serve`) or set OLLAMA_HOST. "
                "To use Gemini instead, set OLLAMA=false and provide GEMINI_API_KEY."
            ),
        )

    candidates = _ollama_model_candidates()
    chosen_name: str | None = None
    for want in candidates:
        picked = _ollama_pick_installed_model(available, want)
        if picked:
            chosen_name = picked
            break

    if not chosen_name:
        raise HTTPException(
            status_code=503,
            detail=(
                "OLLAMA=true but none of the configured models are installed in Ollama. "
                f"Tried: {candidates}. Installed: {sorted(available)}. "
                f"Run e.g. `ollama pull {candidates[0]}` or set OLLAMA_MODEL / LLM_MODEL_CANDIDATES."
            ),
        )

    svc = OllamaAdService(model=chosen_name)
    svc._client = client
    return svc


def _create_backend_for_env() -> BaseAdService:
    if os.getenv("ENV_MODE", "test").strip().lower() == "test":
        return MockLlmService()

    if _ollama_force_local():
        return _create_ollama_backend_required()

    if _ollama_skip_local():
        return GeminiAdService()

    if _ollama_try_local_default():
        local = _try_create_ollama_backend()
        if local is not None:
            return local

    return GeminiAdService()


_instance = None


def get_llm_service() -> BaseAdService:
    global _instance
    if _instance is None:
        _instance = _create_backend_for_env()
    return _instance


get_gemini_service = get_llm_service
MockGeminiService = MockLlmService
