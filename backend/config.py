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

MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]

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
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
BREVO_API_KEY = os.environ.get("BREVO_API_KEY")
EMAIL_FROM = os.environ.get("EMAIL_FROM", "noreply@learnhub.com")
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "LearnHub")
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:3000")

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@learnhub.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"
REQUIRE_STRIPE_WEBHOOK_SECRET = (
    os.environ.get("REQUIRE_STRIPE_WEBHOOK_SECRET", "false").lower() == "true"
    or ENVIRONMENT == "production"
)

CORS_ORIGINS_STR = os.environ.get("CORS_ORIGINS", "*")
if CORS_ORIGINS_STR == "*":
    CORS_ORIGINS = ["*"]
    CORS_ALLOW_CREDENTIALS = False
else:
    CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]
    CORS_ALLOW_CREDENTIALS = True

SUPPORTED_LANGUAGES = ["en", "zh-TW", "zh-CN", "ja", "ko"]
LANGUAGE_NAMES = {
    "en": "English",
    "zh-TW": "繁體中文",
    "zh-CN": "简体中文",
    "ja": "日本語",
    "ko": "한국어",
}
