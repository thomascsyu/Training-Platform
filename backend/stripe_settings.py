"""Stripe API key / webhook secret / currency stored in platform_settings (admin-configurable)."""

import re
from datetime import datetime, timezone
from typing import Optional

import stripe

from ai_settings import _decrypt_value, _encrypt_value, _mask_key
from config import STRIPE_API_KEY, STRIPE_WEBHOOK_SECRET, logger
from database import db

SETTINGS_ID = "stripe"
DEFAULT_CURRENCY = "hkd"

# Stripe zero-decimal currencies — charge in whole units, not cents.
# https://docs.stripe.com/currencies#zero-decimal
ZERO_DECIMAL_CURRENCIES = frozenset({
    "bif", "clp", "djf", "gnf", "jpy", "kmf", "krw", "mga",
    "pyg", "rwf", "ugx", "vnd", "vuv", "xaf", "xof", "xpf",
})

_CURRENCY_RE = re.compile(r"^[a-z]{3}$")


def _env_api_key() -> str:
    return (STRIPE_API_KEY or "").strip()


def _env_webhook_secret() -> str:
    return (STRIPE_WEBHOOK_SECRET or "").strip()


def validate_stripe_api_key(api_key: Optional[str]) -> Optional[str]:
    """Return an error message if the key is unusable; None if empty or valid.

    Empty values are allowed so callers can omit/clear fields. Publishable
    keys (pk_…) are rejected — Checkout needs sk_… or rk_….
    """
    key = (api_key or "").strip()
    if not key:
        return None
    if key.startswith("pk_"):
        return (
            "Publishable keys (pk_…) cannot be used here. "
            "Use a Secret key (sk_…) or Restricted key (rk_…)."
        )
    if not (key.startswith("sk_") or key.startswith("rk_")):
        return "API key must start with sk_… or rk_…."
    return None


def validate_stripe_webhook_secret(webhook_secret: Optional[str]) -> Optional[str]:
    """Return an error message if the webhook secret looks invalid; None otherwise."""
    secret = (webhook_secret or "").strip()
    if not secret:
        return None
    if not secret.startswith("whsec_"):
        return "Webhook secret must start with whsec_…"
    return None


def normalize_currency(currency: Optional[str]) -> Optional[str]:
    """Return a lowercase ISO 4217 code, or None if empty."""
    code = (currency or "").strip().lower()
    return code or None


def validate_currency(currency: Optional[str]) -> Optional[str]:
    """Return an error message if currency is invalid; None if empty or valid."""
    code = normalize_currency(currency)
    if code is None:
        return None
    if not _CURRENCY_RE.match(code):
        return "Currency must be a 3-letter ISO 4217 code (e.g. hkd, usd)."
    return None


def to_stripe_unit_amount(amount: float, currency: str) -> int:
    """Convert a major-unit price to Stripe's integer unit_amount."""
    code = (currency or DEFAULT_CURRENCY).strip().lower() or DEFAULT_CURRENCY
    if code in ZERO_DECIMAL_CURRENCIES:
        return int(round(float(amount)))
    return int(round(float(amount) * 100))


def is_stripe_live_key(api_key: str) -> bool:
    key = (api_key or "").strip()
    return key.startswith("sk_live") or key.startswith("rk_live")


async def load_stripe_settings() -> dict:
    """Load and decrypt Stripe settings from the database (no env fallback)."""
    doc = await db.platform_settings.find_one({"_id": SETTINGS_ID})
    if not doc:
        return {"api_key": "", "webhook_secret": "", "currency": ""}
    return {
        "api_key": _decrypt_value(doc.get("api_key", "") or ""),
        "webhook_secret": _decrypt_value(doc.get("webhook_secret", "") or ""),
        "currency": normalize_currency(doc.get("currency")) or "",
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


async def resolve_payment_currency() -> dict:
    """Resolve checkout currency: database override, then environment, then hkd."""
    import os

    stored = await load_stripe_settings()
    db_currency = normalize_currency(stored.get("currency")) or ""
    if db_currency:
        return {"currency": db_currency, "currency_source": "database"}

    raw_env = (os.environ.get("STRIPE_CURRENCY") or "").strip()
    if raw_env:
        return {
            "currency": raw_env.lower(),
            "currency_source": "environment",
        }

    return {"currency": DEFAULT_CURRENCY, "currency_source": "default"}


async def get_stripe_api_key() -> str:
    creds = await resolve_stripe_credentials()
    return creds["api_key"]


async def get_stripe_webhook_secret() -> str:
    creds = await resolve_stripe_credentials()
    return creds["webhook_secret"]


async def get_payment_currency() -> str:
    resolved = await resolve_payment_currency()
    return resolved["currency"]


def apply_stripe_api_key(api_key: str) -> None:
    """Set the Stripe SDK key for the current process/request."""
    stripe.api_key = api_key


async def load_stripe_settings_masked() -> dict:
    """Return settings for the admin UI with secrets masked."""
    stored = await load_stripe_settings()
    creds = await resolve_stripe_credentials()
    currency_info = await resolve_payment_currency()

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
        "currency": currency_info["currency"],
        "currency_source": currency_info["currency_source"],
        "api_key_configured": bool(creds["api_key"]),
        "webhook_secret_configured": bool(creds["webhook_secret"]),
        "api_key_source": api_key_source,
        "webhook_secret_source": webhook_source,
    }


async def save_stripe_settings(data: dict, user_id: str) -> dict:
    """Persist Stripe settings. Omitted secrets keep the previous database value."""
    if "api_key" in data:
        api_key_error = validate_stripe_api_key(data.get("api_key"))
        if api_key_error:
            raise ValueError(api_key_error)
    if "webhook_secret" in data:
        webhook_error = validate_stripe_webhook_secret(data.get("webhook_secret"))
        if webhook_error:
            raise ValueError(webhook_error)
    if "currency" in data:
        currency_error = validate_currency(data.get("currency"))
        if currency_error:
            raise ValueError(currency_error)

    current = await load_stripe_settings()

    api_key = data.get("api_key")
    if api_key is None:
        api_key = current.get("api_key", "")

    webhook_secret = data.get("webhook_secret")
    if webhook_secret is None:
        webhook_secret = current.get("webhook_secret", "")

    if "currency" in data:
        currency = normalize_currency(data.get("currency")) or ""
    else:
        currency = current.get("currency", "") or ""

    doc = {
        "_id": SETTINGS_ID,
        "api_key": _encrypt_value((api_key or "").strip()),
        "webhook_secret": _encrypt_value((webhook_secret or "").strip()),
        "currency": currency,
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

    key_error = validate_stripe_api_key(api_key)
    if key_error:
        return {"connected": False, "error": key_error}

    previous = stripe.api_key
    apply_stripe_api_key(api_key)
    try:
        account = stripe.Account.retrieve()
        default_currency = getattr(account, "default_currency", None)
        return {
            "connected": True,
            "account_id": getattr(account, "id", None),
            "livemode": is_stripe_live_key(api_key),
            "default_currency": (
                str(default_currency).lower() if default_currency else None
            ),
            "message": "Stripe API key is valid",
        }
    except stripe.error.AuthenticationError as exc:
        logger.warning("Stripe connection test auth failed: %s", exc)
        return {"connected": False, "error": "Invalid Stripe API key"}
    except stripe.error.PermissionError as exc:
        logger.warning("Stripe connection test permission failed: %s", exc)
        return {
            "connected": False,
            "error": (
                "This restricted key is missing permissions. "
                "Allow Checkout Sessions (read/write) and Accounts (read), or use a Secret key (sk_…)."
            ),
        }
    except stripe.error.StripeError as exc:
        logger.warning("Stripe connection test failed: %s", exc)
        return {"connected": False, "error": str(exc)}
    except Exception as exc:  # pragma: no cover - unexpected SDK failures
        logger.warning("Stripe connection test unexpected error: %s", exc)
        return {"connected": False, "error": str(exc)}
    finally:
        stripe.api_key = previous
