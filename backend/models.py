import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    role: str = "student"


class CompanyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    training_ids: List[str] = Field(default_factory=list)


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    training_ids: Optional[List[str]] = None


class AdminUserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    role: str = "student"
    company_id: Optional[str] = None


class AdminUserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(default=None, min_length=8)
    name: Optional[str] = None
    role: Optional[str] = None
    company_id: Optional[str] = None


class UserImportRow(BaseModel):
    name: str
    email: EmailStr
    password: Optional[str] = None
    role: str = "student"


class UserImportRequest(BaseModel):
    company_id: str
    users: List[UserImportRow]


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=20)
    new_password: str = Field(min_length=8)


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class CourseCreate(BaseModel):
    title: str
    description: str
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    video_type: str = "youtube"
    price: float = 0.0
    is_free: bool = True
    is_private: bool = False
    passing_score: int = 70
    materials: List[Dict[str, str]] = []
    ai_assistant_enabled: bool = True
    ai_assistant_prompt: Optional[str] = None
    language: str = "en"
    category: Optional[str] = None
    company_ids: List[str] = Field(default_factory=list)
    course_type: Optional[str] = None

    @field_validator("course_type")
    @classmethod
    def _validate_course_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in {"free", "payment_required"}:
            raise ValueError("course_type must be 'free' or 'payment_required'")
        return value


class CourseUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: Optional[str] = None
    video_type: Optional[str] = None
    price: Optional[float] = None
    is_free: Optional[bool] = None
    is_private: Optional[bool] = None
    passing_score: Optional[int] = None
    materials: Optional[List[Dict[str, str]]] = None
    ai_assistant_enabled: Optional[bool] = None
    ai_assistant_prompt: Optional[str] = None
    language: Optional[str] = None
    category: Optional[str] = None
    company_ids: Optional[List[str]] = None
    course_type: Optional[str] = None

    @field_validator("course_type")
    @classmethod
    def _validate_course_type(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if value not in {"free", "payment_required"}:
            raise ValueError("course_type must be 'free' or 'payment_required'")
        return value


class LessonCreate(BaseModel):
    course_id: str
    title: str
    description: str
    video_url: Optional[str] = None
    video_type: str = "youtube"
    order: int = 0
    materials: List[Dict[str, str]] = []


class LessonUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    video_url: Optional[str] = None
    video_type: Optional[str] = None
    order: Optional[int] = None
    materials: Optional[List[Dict[str, str]]] = None


class QuizCreate(BaseModel):
    course_id: str
    title: str
    questions: List[Dict[str, Any]]


class QuizUpdate(BaseModel):
    title: Optional[str] = None
    questions: Optional[List[Dict[str, Any]]] = None


class QuizAttemptCreate(BaseModel):
    quiz_id: str
    answers: List[int]


class EnrollmentCreate(BaseModel):
    course_id: str
    user_ids: List[str] = []


class ForumPostCreate(BaseModel):
    course_id: str
    content: str
    parent_id: Optional[str] = None


class ChatMessageCreate(BaseModel):
    course_id: str
    message: str


class CertificateCreate(BaseModel):
    course_id: str
    user_id: str
    score: int = Field(ge=0, le=100)
    template: str = "default"
    template_id: Optional[str] = None
    primary_color: str = "#002FA7"
    secondary_color: str = "#0A0B10"


class CertificateCustomize(BaseModel):
    template: str = "default"
    primary_color: str = "#002FA7"
    secondary_color: str = "#0A0B10"
    apply_to_course: bool = False


class PaymentCreate(BaseModel):
    course_id: str
    origin_url: str


class TranslateRequest(BaseModel):
    text: str
    source_language: str
    target_language: str


class TranslateCourseRequest(BaseModel):
    course_id: str
    target_languages: List[str]


class LessonProgressUpdate(BaseModel):
    watch_percent: Optional[int] = None
    last_position_sec: Optional[int] = None
    completed: Optional[bool] = None


class TranslateQuizRequest(BaseModel):
    quiz_id: str
    target_languages: List[str]


class AIProviderConfig(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None
    enabled: Optional[bool] = None


class AISettingsUpdate(BaseModel):
    default_provider: Optional[str] = None
    default_prompt: Optional[str] = None
    providers: Optional[Dict[str, AIProviderConfig]] = None


class AISettingsResponse(BaseModel):
    default_provider: str
    default_prompt: str
    providers: Dict[str, Dict[str, Any]]


class AITestConnectionRequest(BaseModel):
    provider: str
    api_key: Optional[str] = None


class AITestConnectionResponse(BaseModel):
    provider: str
    connected: bool
    model: Optional[str] = None
    latency_ms: Optional[int] = None
    message: Optional[str] = None
    error: Optional[str] = None


class CertificateTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    html: Optional[str] = None
    primary_color: str = "#002fa7"
    secondary_color: str = "#0a0b10"
    is_default: bool = False

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _validate_hex(cls, value: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise ValueError("Color must be a valid 6-digit hex code")
        return value.lower()


class CertificateTemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    html: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    is_default: Optional[bool] = None

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _validate_hex(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise ValueError("Color must be a valid 6-digit hex code")
        return value.lower()


class CertificateTemplateRender(BaseModel):
    primary_color: str = "#002fa7"
    secondary_color: str = "#0a0b10"

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _validate_hex(cls, value: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise ValueError("Color must be a valid 6-digit hex code")
        return value.lower()


class EmailNotificationEventUpdate(BaseModel):
    enabled: Optional[bool] = None
    subject: Optional[str] = Field(default=None, min_length=1, max_length=200)
    html_content: Optional[str] = Field(default=None, min_length=1)
    text_content: Optional[str] = None
    inactivity_days: Optional[int] = Field(default=None, ge=1, le=365)


class EmailNotificationSettingsUpdate(BaseModel):
    events: Dict[str, EmailNotificationEventUpdate]


class EmailNotificationTestRequest(BaseModel):
    event_key: str
    email: EmailStr
    name: str = "Test Learner"
