import base64
import hashlib
import time
from datetime import datetime, timezone
from typing import Optional

from cryptography.fernet import Fernet
from openai import AsyncOpenAI

from config import JWT_SECRET, SETTINGS_ENCRYPTION_KEY, logger
from database import db

_ENC_PREFIX = "enc:"

DEFAULT_SYSTEM_PROMPT = "You are a helpful course assistant."

_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-chat",
    },
    "xai": {
        "name": "xAI",
        "base_url": "https://api.x.ai/v1",
        "default_model": "grok-3",
    },
}


def _get_fernet() -> Optional[Fernet]:
    """Return a Fernet instance if an encryption secret is available."""
    secret = SETTINGS_ENCRYPTION_KEY or JWT_SECRET
    if not secret:
        return None
    digest = hashlib.sha256(secret.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(digest))


def _encrypt_value(value: str) -> str:
    if not value:
        return value
    fernet = _get_fernet()
    if not fernet:
        logger.warning(
            "SETTINGS_ENCRYPTION_KEY is not set; storing API key in plaintext. "
            "Set an encryption key in production."
        )
        return value
    return _ENC_PREFIX + fernet.encrypt(value.encode()).decode()


def _decrypt_value(value: str) -> str:
    if not value:
        return value
    if not value.startswith(_ENC_PREFIX):
        return value
    fernet = _get_fernet()
    if not fernet:
        logger.warning(
            "SETTINGS_ENCRYPTION_KEY is not set; returning encrypted API key as-is."
        )
        return value
    return fernet.decrypt(value[len(_ENC_PREFIX):].encode()).decode()


def _default_settings() -> dict:
    return {
        "default_provider": "deepseek",
        "default_prompt": "",
        "providers": {
            key: {
                "enabled": True,
                "model": meta["default_model"],
                "api_key": "",
                "base_url": meta["base_url"],
                "name": meta["name"],
            }
            for key, meta in _PROVIDERS.items()
        },
    }


def _normalize_provider_config(provider_key: str, stored: dict) -> dict:
    meta = _PROVIDERS.get(provider_key, {})
    return {
        "enabled": stored.get("enabled", True) if isinstance(stored, dict) else True,
        "model": (stored.get("model") if isinstance(stored, dict) else None) or meta.get("default_model", ""),
        "api_key": _decrypt_value(stored.get("api_key", "")) if isinstance(stored, dict) else "",
        "base_url": meta.get("base_url", ""),
        "name": meta.get("name", provider_key),
    }


async def load_ai_settings() -> dict:
    """Load and decrypt the AI settings singleton from the database."""
    doc = await db.platform_settings.find_one({"_id": "ai"})
    if not doc:
        return _default_settings()

    default_provider = doc.get("default_provider") or "deepseek"
    if default_provider not in _PROVIDERS:
        default_provider = "deepseek"

    stored_providers = doc.get("providers", {}) or {}
    providers = {
        key: _normalize_provider_config(key, stored_providers.get(key, {}))
        for key in _PROVIDERS
    }

    return {
        "default_provider": default_provider,
        "default_prompt": doc.get("default_prompt") or "",
        "providers": providers,
    }


def _mask_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "•" * len(key)
    return f"{key[:4]}••••{key[-4:]}"


async def load_ai_settings_masked() -> dict:
    """Return settings with API keys masked for the admin UI."""
    settings = await load_ai_settings()
    return {
        "default_provider": settings["default_provider"],
        "default_prompt": settings["default_prompt"],
        "providers": {
            key: {
                **cfg,
                "api_key": _mask_key(cfg.get("api_key", "")),
            }
            for key, cfg in settings["providers"].items()
        },
    }


async def get_provider_settings(provider: str) -> Optional[dict]:
    """Return decrypted settings for a single provider, or None if unknown."""
    if provider not in _PROVIDERS:
        return None
    settings = await load_ai_settings()
    return settings["providers"].get(provider)


async def get_active_provider() -> str:
    """Return the provider key that should be used for AI features."""
    settings = await load_ai_settings()
    return settings.get("default_provider", "deepseek")


async def get_default_prompt() -> str:
    """Return the admin-configured default system prompt, or the built-in fallback."""
    settings = await load_ai_settings()
    return settings.get("default_prompt", "").strip() or DEFAULT_SYSTEM_PROMPT


async def get_active_provider_settings() -> Optional[dict]:
    """Return decrypted settings for the currently active provider."""
    settings = await load_ai_settings()
    active = settings.get("default_provider", "deepseek")
    return settings["providers"].get(active)


def build_ai_client(settings: dict) -> Optional[AsyncOpenAI]:
    """Build an OpenAI-compatible async client from provider settings."""
    api_key = settings.get("api_key", "") if settings else ""
    base_url = settings.get("base_url", "") if settings else ""
    if not api_key or not base_url:
        return None
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


async def get_active_client() -> Optional[AsyncOpenAI]:
    """Build an OpenAI-compatible async client for the active AI provider."""
    settings = await get_active_provider_settings()
    if not settings or not settings.get("enabled", True):
        return None
    return build_ai_client(settings)


async def get_client_for_provider(provider: str) -> Optional[AsyncOpenAI]:
    """Build an OpenAI-compatible async client for a specific provider."""
    settings = await get_provider_settings(provider)
    if not settings or not settings.get("enabled", True):
        return None
    return build_ai_client(settings)


async def save_ai_settings(data: dict, user_id: str) -> dict:
    """Persist AI settings, encrypting API keys at rest."""
    current = await load_ai_settings()
    current_providers = current.get("providers", {})

    default_provider = data.get("default_provider", current.get("default_provider", "deepseek"))
    if default_provider not in _PROVIDERS:
        default_provider = "deepseek"

    default_prompt = data.get("default_prompt")
    if default_prompt is None:
        default_prompt = current.get("default_prompt", "")

    providers = {}
    for key in _PROVIDERS:
        incoming = data.get("providers", {}).get(key, {}) if isinstance(data.get("providers"), dict) else {}
        existing = current_providers.get(key, {})

        api_key = incoming.get("api_key")
        if api_key is None:
            api_key = existing.get("api_key", "")

        model = incoming.get("model") or existing.get("model") or _PROVIDERS[key]["default_model"]
        enabled = incoming.get("enabled")
        if enabled is None:
            enabled = existing.get("enabled", True)

        providers[key] = {
            "api_key": _encrypt_value(api_key),
            "model": model,
            "enabled": bool(enabled),
        }

    doc = {
        "_id": "ai",
        "default_provider": default_provider,
        "default_prompt": default_prompt,
        "providers": providers,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user_id,
    }

    await db.platform_settings.replace_one({"_id": "ai"}, doc, upsert=True)
    return await load_ai_settings()


async def test_provider_connection(provider: str, override_key: Optional[str] = None) -> dict:
    """Test connectivity to a provider by sending a tiny chat completion."""
    if provider not in _PROVIDERS:
        return {
            "provider": provider,
            "connected": False,
            "error": "Unknown provider",
        }

    settings = await get_provider_settings(provider)
    api_key = override_key or (settings.get("api_key", "") if settings else "")
    model = settings.get("model", "") if settings else ""
    if not api_key:
        return {
            "provider": provider,
            "connected": False,
            "error": "API key not configured",
        }

    if not model:
        model = _PROVIDERS[provider]["default_model"]

    client = AsyncOpenAI(api_key=api_key, base_url=_PROVIDERS[provider]["base_url"])

    start = time.time()
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Respond with the single word OK."},
                {"role": "user", "content": "Ping"},
            ],
            max_tokens=2,
            temperature=0,
        )
        content = response.choices[0].message.content or ""
        latency_ms = int((time.time() - start) * 1000)
        return {
            "provider": provider,
            "connected": True,
            "model": model,
            "latency_ms": latency_ms,
            "message": content.strip(),
        }
    except Exception as exc:  # pragma: no cover - network errors vary by provider
        latency_ms = int((time.time() - start) * 1000)
        logger.warning("AI connection test failed for %s: %s", provider, exc)
        return {
            "provider": provider,
            "connected": False,
            "model": model,
            "latency_ms": latency_ms,
            "error": str(exc),
        }
