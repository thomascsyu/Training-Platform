from fastapi import APIRouter
from fastapi.staticfiles import StaticFiles

from routers.ai_settings import router as ai_settings_router
from routers.auth import router as auth_router
from routers.certificates import router as certificates_router
from routers.certificate_templates import router as certificate_templates_router
from routers.chat import router as chat_router
from routers.courses import router as courses_router
from routers.enrollments import router as enrollments_router
from routers.email_notifications import router as email_notifications_router
from routers.forums import router as forums_router
from routers.groups import router as groups_router
from routers.lessons import router as lessons_router
from routers.payments import router as payments_router
from routers.progress import router as progress_router
from routers.quizzes import router as quizzes_router
from routers.root import router as root_router
from routers.stats import router as stats_router
from routers.translate import router as translate_router
from routers.companies import router as companies_router
from routers.users import router as users_router
from routers.uploads import router as uploads_router
from upload_utils import ensure_thumbnail_dir, get_uploads_root
from config import logger

# Ensure Stripe global configuration is applied when the API starts.
import clients  # noqa: F401

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(courses_router)
api_router.include_router(lessons_router)
api_router.include_router(quizzes_router)
api_router.include_router(enrollments_router)
api_router.include_router(email_notifications_router)
api_router.include_router(groups_router)
api_router.include_router(certificates_router)
api_router.include_router(certificate_templates_router)
api_router.include_router(forums_router)
api_router.include_router(chat_router)
api_router.include_router(translate_router)
api_router.include_router(payments_router)
api_router.include_router(progress_router)
api_router.include_router(companies_router)
api_router.include_router(users_router)
api_router.include_router(stats_router)
api_router.include_router(uploads_router)
api_router.include_router(ai_settings_router)
api_router.include_router(root_router)

ensure_thumbnail_dir()
logger.info("Course upload storage: %s", get_uploads_root())
api_router.mount(
    "/uploads",
    StaticFiles(directory=str(get_uploads_root())),
    name="uploads",
)
