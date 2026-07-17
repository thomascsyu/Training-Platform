import importlib

from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from upload_utils import (
    ensure_certificate_background_dir,
    ensure_thumbnail_dir,
    get_uploads_root,
)
from config import logger

# Ensure Stripe global configuration is applied when the API starts.
import clients  # noqa: F401

api_router = APIRouter(prefix="/api")

# Import routers individually so one missing model/export cannot prevent the
# whole API from binding :8080 (which surfaces as frontend ECONNREFUSED).
_ROUTER_MODULES = (
    "routers.auth",
    "routers.courses",
    "routers.lessons",
    "routers.quizzes",
    "routers.enrollments",
    "routers.email_notifications",
    "routers.groups",
    "routers.certificates",
    "routers.certificate_settings",
    "routers.certificate_templates",
    "routers.forums",
    "routers.chat",
    "routers.translate",
    "routers.payments",
    "routers.progress",
    "routers.companies",
    "routers.users",
    "routers.stats",
    "routers.uploads",
    "routers.ai_settings",
    "routers.root",
)

for _module_name in _ROUTER_MODULES:
    try:
        _module = importlib.import_module(_module_name)
        api_router.include_router(_module.router)
    except Exception:
        logger.exception(
            "Failed to load %s; continuing without that router so the API stays up",
            _module_name,
        )

ensure_thumbnail_dir()
ensure_certificate_background_dir()
logger.info("Course upload storage: %s", get_uploads_root())
api_router.mount(
    "/uploads",
    StaticFiles(directory=str(get_uploads_root())),
    name="uploads",
)
