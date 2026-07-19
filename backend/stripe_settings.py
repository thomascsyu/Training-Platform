"""Stripe API key / webhook secret stored in platform_settings (admin-configurable)."""

from datetime import datetime, timezone
from typing import Optional

import stripe

from ai_settings import _decrypt_value, _encrypt_value, _mask_key
from config import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, logger
from database import db

SETTINGS_ID = "stripe"


def _env_api_key() -> str:
    return (STRIPE_API_KEY or "").strip()


def _env_webhook_secret() -> str:
    return (STRIPE_WEBHOOK_SECRET or "").strip()


async def load_stripe_settings() -> dict:
    """Load and decrypt Stripe settings from the database (no env fallback)."""
    doc = await db.platform_settings.find_one({"_id": SETTINGS_ID})
    if not doc:
        return {"api_key": "", "webhook_secret": ""}
    return {
        "api_key": _decrypt_value(doc.get("api_key", "") or ""),
        "webhook_secret": _decrypt_value(doc.get("webhook_secret", "") or ""),
    }


def _source(db_value: str, env_value: str) -> str:
    if (db_value or "").strip():
        return "database"
    if (env_value or "").strip():
        return "environment"
    return "none"


async def resolve_stripe_credentials() -> dict:
    """Resolve effective credentials: database override, then environment."""
    stored = await load_stripe_settings()
    db_key = (stored.get("api_key") or "").strip()
    db_secret = (stored.get("webhook_secret") or "").strip()
    env_key = _env_api_key()
    env_secret = _env_webhook_secret()
    return {
        "api_key": db_key or env_key,
        "webhook_secret": db_secret or env_secret,
        "api_key_source": _source(db_key, env_key),
        "webhook_secret_source": _source(db_secret, env_secret),
    }


async def get_stripe_api_key() -> str:
    creds = await resolve_stripe_credentials()
    return creds["api_key"]


async def get_stripe_webhook_secret() -> str:
    creds = await resolve_stripe_credentials()
    return creds["webhook_secret"]


def apply_stripe_api_key(api_key: str) -> None:
    """Set the Stripe SDK key for the current process/request."""
    stripe.api_key = api_key


async def load_stripe_settings_masked() -> dict:
    """Return settings for the admin UI with secrets masked."""
    stored = await load_stripe_settings()
    creds = await resolve_stripe_credentials()

    api_key_source = creds["api_key_source"]
    webhook_source = creds["webhook_secret_source"]

    if api_key_source == "database":
        masked_api_key = _mask_key(stored.get("api_key", ""))
    elif api_key_source == "environment":
        masked_api_key = _mask_key(_env_api_key())
    else:
        masked_api_key = ""

    if webhook_source == "database":
        masked_webhook = _mask_key(stored.get("webhook_secret", ""))
    elif webhook_source == "environment":
        masked_webhook = _mask_key(_env_webhook_secret())
    else:
        masked_webhook = ""

    return {
        "api_key": masked_api_key,
        "webhook_secret": masked_webhook,
        "api_key_configured": bool(creds["api_key"]),
        "webhook_secret_configured": bool(creds["webhook_secret"]),
        "api_key_source": api_key_source,
        "webhook_secret_source": webhook_source,
    }


async def save_stripe_settings(data: dict, user_id: str) -> dict:
    """Persist Stripe settings. Omitted secrets keep the previous database value."""
    current = await load_stripe_settings()

    api_key = data.get("api_key")
    if api_key is None:
        api_key = current.get("api_key", "")

    webhook_secret = data.get("webhook_secret")
    if webhook_secret is None:
        webhook_secret = current.get("webhook_secret", "")

    doc = {
        "_id": SETTINGS_ID,
        "api_key": _encrypt_value((api_key or "").strip()),
        "webhook_secret": _encrypt_value((webhook_secret or "").strip()),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "updated_by": user_id,
    }
    await db.platform_settings.replace_one({"_id": SETTINGS_ID}, doc, upsert=True)
    return await load_stripe_settings()


async def test_stripe_connection(override_key: Optional[str] = None) -> dict:
    """Verify a Stripe secret key by calling Account.retrieve."""
    api_key = (override_key or "").strip() or await get_stripe_api_key()
    if not api_key:
        return {
            "connected": False,
            "error": "API key not configured",
        }

    previous = stripe.api_key
    apply_stripe_api_key(api_key)
    try:
        account = stripe.Account.retrieve()
        return {
            "connected": True,
            "account_id": getattr(account, "id", None),
            "livemode": api_key.startswith("sk_live"),
            "message": "Stripe API key is valid",
        }
    except stripe.error.AuthenticationError as exc:
        logger.warning("Stripe connection test auth failed: %s", exc)
        return {"connected": False, "error": "Invalid Stripe API key"}
    except stripe.error.StripeError as exc:
        logger.warning("Stripe connection test failed: %s", exc)
        return {"connected": False, "error": str(exc)}
    except Exception as exc:  # pragma: no cover - unexpected SDK failures
        logger.warning("Stripe connection test unexpected error: %s", exc)
        return {"connected": False, "error": str(exc)}
    finally:
        stripe.api_key = previous
