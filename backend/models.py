from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str
    role: str = "student"


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


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
    language: str = "en"
    category: Optional[str] = None


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
    language: Optional[str] = None
    category: Optional[str] = None


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
