import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


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
    auto_issue_certificate: bool = True
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
    auto_issue_certificate: Optional[bool] = None
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
    background: str = "plain"
    language: Optional[str] = None


class CertificateCustomize(BaseModel):
    template: str = "default"
    primary_color: str = "#002FA7"
    secondary_color: str = "#0A0B10"
    background: Optional[str] = None
    language: Optional[str] = None
    apply_to_course: bool = False


class CertificatePreview(BaseModel):
    """Render a fully filled certificate without issuing or persisting it.

    Provide either a real ``course_id`` or a free-form ``course_title``, and
    either a real ``user_id`` or a free-form ``user_name``. Style fields and
    language default to the selected course / template when omitted.
    Builder fields (orientation, background_image_url, body_text) compose a
    live preview without requiring a saved template.
    """

    course_id: Optional[str] = None
    course_title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    user_id: Optional[str] = None
    user_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    score: int = Field(default=92, ge=0, le=100)
    template: str = "default"
    template_id: Optional[str] = None
    primary_color: str = "#002FA7"
    secondary_color: str = "#0A0B10"
    background: str = "plain"
    background_image_url: Optional[str] = Field(default=None, max_length=500)
    orientation: str = "landscape"
    body_text: Optional[str] = Field(default=None, max_length=4000)
    language: Optional[str] = None
    format: str = "html"
    certificate_id: Optional[str] = Field(default=None, min_length=1, max_length=120)

    @field_validator("format")
    @classmethod
    def _validate_format(cls, value: str) -> str:
        key = str(value or "").strip().lower()
        if key not in {"html", "pdf"}:
            raise ValueError("format must be 'html' or 'pdf'")
        return key

    @field_validator("orientation")
    @classmethod
    def _validate_orientation(cls, value: str) -> str:
        return _validate_orientation(value)

    @field_validator("background")
    @classmethod
    def _check_background(cls, value: str) -> str:
        return _validate_background(value)

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _validate_hex(cls, value: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise ValueError("Color must be a valid 6-digit hex code")
        return value.lower()

    @model_validator(mode="after")
    def _require_course_and_recipient(self) -> "CertificatePreview":
        has_course = bool(self.course_id) or bool(self.course_title)
        has_recipient = bool(self.user_id) or bool(self.user_name)
        if not has_course:
            raise ValueError("Provide course_id or course_title")
        if not has_recipient:
            raise ValueError("Provide user_id or user_name")
        return self


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


_CERTIFICATE_BACKGROUND_KEYS = {"plain", "geometric", "waves", "guilloche", "corners"}
_CERTIFICATE_ORIENTATIONS = {"landscape", "portrait"}
_DEFAULT_BODY_TEXT = (
    "This certifies that {{recipient_name}} has successfully completed "
    "{{course_title}} on {{completion_date}}."
)


def _validate_background(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    key = str(value).strip()
    if key not in _CERTIFICATE_BACKGROUND_KEYS:
        allowed = ", ".join(sorted(_CERTIFICATE_BACKGROUND_KEYS))
        raise ValueError(f"Background must be one of: {allowed}")
    return key


def _validate_orientation(value: Optional[str]) -> Optional[str]:
    if value is None:
        return value
    key = str(value).strip().lower()
    if key not in _CERTIFICATE_ORIENTATIONS:
        raise ValueError("orientation must be 'landscape' or 'portrait'")
    return key


class CertificateTemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    html: Optional[str] = None
    primary_color: str = "#002fa7"
    secondary_color: str = "#0a0b10"
    background: str = "plain"
    background_image_url: Optional[str] = Field(default=None, max_length=500)
    orientation: str = "landscape"
    body_text: Optional[str] = Field(default=None, max_length=4000)
    course_id: Optional[str] = None
    is_default: bool = False

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _validate_hex(cls, value: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise ValueError("Color must be a valid 6-digit hex code")
        return value.lower()

    @field_validator("background")
    @classmethod
    def _check_background(cls, value: str) -> str:
        return _validate_background(value)

    @field_validator("orientation")
    @classmethod
    def _check_orientation(cls, value: str) -> str:
        return _validate_orientation(value)

    @field_validator("body_text")
    @classmethod
    def _normalize_body_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        text = value.strip()
        if not text:
            raise ValueError("body_text cannot be empty")
        return text


class CertificateTemplateUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    html: Optional[str] = None
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    background: Optional[str] = None
    background_image_url: Optional[str] = Field(default=None, max_length=500)
    orientation: Optional[str] = None
    body_text: Optional[str] = Field(default=None, max_length=4000)
    course_id: Optional[str] = None
    is_default: Optional[bool] = None

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _validate_hex(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise ValueError("Color must be a valid 6-digit hex code")
        return value.lower()

    @field_validator("background")
    @classmethod
    def _check_background(cls, value: Optional[str]) -> Optional[str]:
        return _validate_background(value)

    @field_validator("orientation")
    @classmethod
    def _check_orientation(cls, value: Optional[str]) -> Optional[str]:
        return _validate_orientation(value)

    @field_validator("body_text")
    @classmethod
    def _normalize_body_text(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        text = value.strip()
        if not text:
            raise ValueError("body_text cannot be empty")
        return text


class CertificateTemplateRender(BaseModel):
    primary_color: str = "#002fa7"
    secondary_color: str = "#0a0b10"
    background: str = "plain"
    background_image_url: Optional[str] = Field(default=None, max_length=500)
    orientation: str = "landscape"
    body_text: Optional[str] = Field(default=None, max_length=4000)

    @field_validator("primary_color", "secondary_color")
    @classmethod
    def _validate_hex(cls, value: str) -> str:
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise ValueError("Color must be a valid 6-digit hex code")
        return value.lower()

    @field_validator("background")
    @classmethod
    def _check_background(cls, value: str) -> str:
        return _validate_background(value)

    @field_validator("orientation")
    @classmethod
    def _check_orientation(cls, value: str) -> str:
        return _validate_orientation(value)


class CertificateSettingsUpdate(BaseModel):
    id_format: Optional[str] = Field(default=None, min_length=1, max_length=120)
    default_background: Optional[str] = None
    default_primary_color: Optional[str] = None
    default_secondary_color: Optional[str] = None

    @field_validator("default_primary_color", "default_secondary_color")
    @classmethod
    def _validate_hex(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        if not re.match(r"^#[0-9A-Fa-f]{6}$", value):
            raise ValueError("Color must be a valid 6-digit hex code")
        return value.lower()

    @field_validator("default_background")
    @classmethod
    def _check_background(cls, value: Optional[str]) -> Optional[str]:
        return _validate_background(value)


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
