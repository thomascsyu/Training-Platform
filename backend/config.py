import os
import secrets
import logging

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def _get_int_env(name: str, default: int) -> int:
    raw_value = os.environ.get(name)
    if raw_value is None or raw_value.strip() == "":
        return default
    try:
        return int(raw_value.strip())
    except ValueError:
        logger.warning(
            "%s must be an integer, got %r; falling back to %s",
            name,
            raw_value,
            default,
        )
        return default


def _get_positive_int_env(name: str, default: int) -> int:
    value = _get_int_env(name, default)
    if value <= 0:
        logger.warning(
            "%s must be greater than 0, got %r; falling back to %s",
            name,
            value,
            default,
        )
        return default
    return value


# Connection-string env vars in priority order. MONGO_URL is preferred, but
# different platforms expose different names: Zeabur's prebuilt MongoDB service
# injects MONGO_CONNECTION_STRING, and Emergent-imported apps commonly use
# MONGO_URI. Accepting all of them means "add a MongoDB service" works without
# manually wiring an extra MONGO_URL variable.
_MONGO_URL_ENV_VARS = (
    "MONGO_URL",
    "MONGODB_URI",
    "MONGO_CONNECTION_STRING",
    "MONGO_URI",
)


def _get_mongo_url() -> str:
    for name in _MONGO_URL_ENV_VARS:
        value = os.environ.get(name)
        if value and value.strip():
            if name != "MONGO_URL":
                logger.info("MONGO_URL not set; using %s", name)
            return value.strip()

    logger.warning(
        "No MongoDB connection string set (checked %s); "
        "defaulting to mongodb://localhost:27017",
        ", ".join(_MONGO_URL_ENV_VARS),
    )
    return "mongodb://localhost:27017"


MONGO_URL = _get_mongo_url()

DB_NAME = os.environ.get("DB_NAME", "learnhub")
if "DB_NAME" not in os.environ:
    logger.warning("DB_NAME not set; defaulting to learnhub")

MONGO_SERVER_SELECTION_TIMEOUT_MS = _get_int_env("MONGO_SERVER_SELECTION_TIMEOUT_MS", 5000)

_jwt_from_env = os.environ.get("JWT_SECRET")
if _jwt_from_env:
    JWT_SECRET = _jwt_from_env
else:
    JWT_SECRET = secrets.token_hex(32)
    logger.warning(
        "JWT_SECRET not set — using an ephemeral secret; tokens invalidate on restart"
    )
JWT_ALGORITHM = "HS256"

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
XAI_API_KEY = os.environ.get("XAI_API_KEY")
SETTINGS_ENCRYPTION_KEY = os.environ.get("SETTINGS_ENCRYPTION_KEY")
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@learnhub.com")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "LearnHub")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")
RESET_PASSWORD_TOKEN_TTL_MINUTES = _get_positive_int_env(
    "RESET_PASSWORD_TOKEN_TTL_MINUTES",
    30,
)

def _normalize_admin_email(email: str) -> str:
    return email.lower().strip()


ADMIN_EMAIL = _normalize_admin_email(
    os.environ.get("ADMIN_EMAIL", "admin@learnhub.com")
)
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")

ADMIN2_EMAIL = _normalize_admin_email(os.environ.get("ADMIN2_EMAIL", ""))
ADMIN2_PASSWORD = os.environ.get("ADMIN2_PASSWORD")


def get_seeded_admin_accounts() -> list[tuple[str, str, str | None]]:
    """Return (display_name, email, password) tuples for startup admin seeding."""
    admin_email = _normalize_admin_email(
        os.environ.get("ADMIN_EMAIL", "admin@learnhub.com")
    )
    admin_password = os.environ.get("ADMIN_PASSWORD")
    admin2_email = _normalize_admin_email(os.environ.get("ADMIN2_EMAIL", ""))
    admin2_password = os.environ.get("ADMIN2_PASSWORD")

    accounts: list[tuple[str, str, str | None]] = [
        ("Admin", admin_email, admin_password),
    ]
    if admin2_email and admin2_password:
        accounts.append(("Admin 2", admin2_email, admin2_password))
    elif admin2_email or admin2_password:
        logger.warning(
            "ADMIN2_EMAIL and ADMIN2_PASSWORD must both be set; skipping second admin"
        )
    return accounts

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

# The browser only stores/sends auth cookies from a cross-site XHR response when
# the cookie is SameSite=None; Secure. A cross-domain deployment (SPA on one
# site calling the API on another, e.g. via REACT_APP_BACKEND_URL) therefore
# needs SameSite=none — otherwise the default (lax) cookie is silently dropped,
# every request 401s, and the user is bounced back to the login page in a loop.
# When COOKIE_SAMESITE is not set explicitly, pick a safe default: 'none' for a
# secure production deployment (so cross-site login works out of the box) and
# 'lax' for local/insecure development.
_COOKIE_SAMESITE_RAW = os.environ.get("COOKIE_SAMESITE")
if _COOKIE_SAMESITE_RAW is None or _COOKIE_SAMESITE_RAW.strip() == "":
    COOKIE_SAMESITE = "none" if (ENVIRONMENT == "production" and COOKIE_SECURE) else "lax"
    if COOKIE_SAMESITE == "none":
        logger.info(
            "COOKIE_SAMESITE not set; defaulting to 'none' for secure production "
            "so cross-site (cross-domain) login cookies are not dropped. Set "
            "COOKIE_SAMESITE=lax explicitly if the SPA and API share a site."
        )
else:
    _normalized_samesite = _COOKIE_SAMESITE_RAW.strip().lower()
    COOKIE_SAMESITE = _normalized_samesite if _normalized_samesite in (
        "lax",
        "strict",
        "none",
    ) else "lax"

if COOKIE_SAMESITE == "none" and not COOKIE_SECURE:
    COOKIE_SECURE = True
    logger.warning(
        "COOKIE_SAMESITE=none requires Secure; forcing COOKIE_SECURE=true"
    )

REQUIRE_STRIPE_WEBHOOK_SECRET = (
    os.environ.get("REQUIRE_STRIPE_WEBHOOK_SECRET", "false").lower() == "true"
    or ENVIRONMENT == "production"
)

# Default to the frontend URL so cookie-based auth works out of the box.
# Using '*' with allow_credentials=True is forbidden by browsers, so '*' turns
# credentials off and breaks login sessions.
CORS_ORIGINS_STR = os.environ.get("CORS_ORIGINS", FRONTEND_URL)
if CORS_ORIGINS_STR == "*":
    CORS_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = False
    logger.warning(
        "CORS_ORIGINS=* disables credentials; cookie auth will not work across origins"
    )
else:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",") if origin.strip()]
    CORS_ALLOW_CREDENTIALS = True

# A credentialed cross-origin CORS setup with SameSite=lax cookies is the classic
# "login succeeds then bounces back to login in a loop" trap: the browser accepts
# the login response but never stores the SameSite=lax auth cookie sent from a
# cross-site XHR, so /auth/me and every protected call 401s. Warn loudly so the
# misconfiguration is obvious in the logs.
if ENVIRONMENT == "production" and CORS_ALLOW_CREDENTIALS and COOKIE_SAMESITE != "none":
    logger.warning(
        "Production CORS is configured for credentialed cross-origin requests but "
        "COOKIE_SAMESITE=%s. If the SPA is served from a different site than "
        "the API, browsers will drop the auth cookie and login will loop. Use "
        "the same-origin /api proxy (BACKEND_PROXY_URL, do not set "
        "REACT_APP_BACKEND_URL) or set COOKIE_SAMESITE=none with COOKIE_SECURE=true.",
        COOKIE_SAMESITE,
    )

SUPPORTED_LANGUAGES = ["en", "zh-TW", "zh-CN", "ja", "ko"]
LANGUAGE_NAMES = {
    "en": "English",
    "zh-TW": "香港繁體中文",
    "zh-CN": "简体中文",
    "ja": "日本語",
    "ko": "한국어",
}
