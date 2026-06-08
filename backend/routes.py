from fastapi import APIRouter

from routers.auth import router as auth_router
from routers.certificates import router as certificates_router
from routers.chat import router as chat_router
from routers.courses import router as courses_router
from routers.enrollments import router as enrollments_router
from routers.forums import router as forums_router
from routers.groups import router as groups_router
from routers.lessons import router as lessons_router
from routers.payments import router as payments_router
from routers.quizzes import router as quizzes_router
from routers.root import router as root_router
from routers.stats import router as stats_router
from routers.translate import router as translate_router
from routers.users import router as users_router

api_router = APIRouter(prefix="/api")

api_router.include_router(auth_router)
api_router.include_router(courses_router)
api_router.include_router(lessons_router)
api_router.include_router(quizzes_router)
api_router.include_router(enrollments_router)
api_router.include_router(groups_router)
api_router.include_router(certificates_router)
api_router.include_router(forums_router)
api_router.include_router(chat_router)
api_router.include_router(translate_router)
api_router.include_router(payments_router)
api_router.include_router(users_router)
api_router.include_router(stats_router)
api_router.include_router(root_router)
