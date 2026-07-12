from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Request

from auth_utils import get_optional_user, require_roles
from config import SUPPORTED_LANGUAGES
from course_utils import delete_course_related_data
from database import db
from db_utils import parse_object_id
from enrollment_utils import enroll_company_students_in_course, enroll_user_in_course
from models import CourseCreate, CourseUpdate

router = APIRouter(tags=["courses"])


async def _validate_company_ids(company_ids: Optional[list[str]]) -> list[str]:
    if not company_ids:
        return []

    normalized = []
    seen = set()
    for company_id in company_ids:
        if not company_id or company_id in seen:
            continue
        parse_object_id(company_id, "company")
        normalized.append(company_id)
        seen.add(company_id)

    existing_count = await db.companies.count_documents({
        "_id": {"$in": [parse_object_id(cid, "company") for cid in normalized]},
    })
    if existing_count != len(normalized):
        raise HTTPException(status_code=400, detail="Company not found")

    return normalized


async def _get_user_company_id(user: Optional[dict]) -> Optional[str]:
    if not user:
        return None
    user_doc = await db.users.find_one(
        {"_id": parse_object_id(user["id"], "user")},
        {"company_id": 1},
    )
    return user_doc.get("company_id") if user_doc else None


def _apply_course_translation(course_data: dict, lang: Optional[str]) -> dict:
    if not lang:
        return course_data
    translated = course_data.get("translations", {}).get(lang)
    if not translated or translated.get("error"):
        return course_data
    course_data = dict(course_data)
    course_data.update({
        "title": translated.get("title", course_data.get("title")),
        "description": translated.get("description", course_data.get("description")),
        "display_language": lang,
    })
    return course_data


@router.post("/courses")
async def create_course(data: CourseCreate, request: Request):
    user = await require_roles("admin")(request)
    if data.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported language. Supported: {SUPPORTED_LANGUAGES}",
        )

    company_ids = await _validate_company_ids(data.company_ids)
    course_doc = {
        "title": data.title,
        "description": data.description,
        "thumbnail_url": data.thumbnail_url,
        "video_url": data.video_url,
        "video_type": data.video_type,
        "price": data.price,
        "is_free": data.is_free,
        "is_private": data.is_private,
        "passing_score": data.passing_score,
        "materials": data.materials,
        "ai_assistant_enabled": data.ai_assistant_enabled,
        "ai_assistant_prompt": data.ai_assistant_prompt,
        "language": data.language,
        "category": data.category,
        "company_ids": company_ids,
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.courses.insert_one(course_doc)
    course_id = str(result.inserted_id)
    enrolled = []
    if company_ids:
        enrolled = await enroll_company_students_in_course(
            course_doc,
            course_id,
            company_ids,
            enrolled_by=user["id"],
        )
    return {
        "id": course_id,
        **{k: v for k, v in course_doc.items() if k != "_id"},
        "company_enrolled": enrolled,
    }


@router.get("/languages")
async def get_languages():
    from config import LANGUAGE_NAMES

    return {"languages": SUPPORTED_LANGUAGES, "names": LANGUAGE_NAMES}


@router.get("/courses")
async def get_courses(
    request: Request,
    include_private: bool = False,
    language: Optional[str] = None,
    lang: Optional[str] = None,
    search: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    paginate: bool = False,
):
    user = await get_optional_user(request)
    is_authenticated = user is not None

    skip = max(skip, 0)
    limit = max(1, min(limit, 100))

    filters: list[dict] = []
    category_filters: list[dict] = []
    if not is_authenticated or (user and user["role"] == "student"):
        company_filter = [
            {"company_ids": {"$exists": False}},
            {"company_ids": []},
        ]
        user_company_id = await _get_user_company_id(user)
        if user_company_id:
            company_filter.append({"company_ids": user_company_id})
        visibility = {"$and": [{"is_private": False}, {"$or": company_filter}]}
        filters.append(visibility)
        category_filters.append(visibility)
    elif include_private and user and user["role"] in ["admin", "client_manager"]:
        pass
    else:
        public_filter = {"is_private": False}
        filters.append(public_filter)
        category_filters.append(public_filter)

    if language and language in SUPPORTED_LANGUAGES:
        lang_filter = {"language": language}
        filters.append(lang_filter)
        category_filters.append(lang_filter)

    if category:
        filters.append({"category": category})

    if search:
        filters.append({"$or": [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
        ]})

    query = {"$and": filters} if filters else {}
    category_query = {"$and": category_filters} if category_filters else {}

    total = await db.courses.count_documents(query) if paginate else None

    cursor = db.courses.find(
        query,
        {
            "_id": 1,
            "title": 1,
            "description": 1,
            "thumbnail_url": 1,
            "price": 1,
            "is_free": 1,
            "is_private": 1,
            "language": 1,
            "category": 1,
            "translations": 1,
            "company_ids": 1,
            "created_at": 1,
        },
    ).sort("created_at", -1)
    if paginate:
        cursor = cursor.skip(skip).limit(limit)
    courses = await cursor.to_list(limit if paginate else 100)
    items = [_apply_course_translation(
        {"id": str(c["_id"]), **{k: v for k, v in c.items() if k != "_id"}},
        lang,
    ) for c in courses]
    if not paginate:
        return items

    categories = await db.courses.distinct("category", category_query)
    categories = sorted([c for c in categories if c])
    has_more = (skip + len(items)) < (total or 0)
    return {
        "items": items,
        "total": total or 0,
        "skip": skip,
        "limit": limit,
        "has_more": has_more,
        "categories": categories,
    }


@router.get("/courses/{course_id}")
async def get_course(course_id: str, request: Request, lang: Optional[str] = None):
    course = await db.courses.find_one(
        {"_id": parse_object_id(course_id, "course")}
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    user = await get_optional_user(request)
    if course.get("company_ids"):
        if not user:
            raise HTTPException(status_code=403, detail="Course is assigned to specific companies")
        if user["role"] == "student":
            user_company_id = await _get_user_company_id(user)
            if user_company_id not in course.get("company_ids", []):
                raise HTTPException(status_code=403, detail="Course is not assigned to your company")
            enrollment = await db.enrollments.find_one({
                "course_id": course_id,
                "user_id": user["id"],
            })
            if not enrollment:
                user_doc = await db.users.find_one(
                    {"_id": parse_object_id(user["id"], "user")}
                )
                await enroll_user_in_course(
                    course,
                    course_id,
                    user_doc,
                    source="company_assignment",
                )

    if course.get("is_private"):
        if not user:
            raise HTTPException(
                status_code=403, detail="Private course - authentication required"
            )
        if user["role"] == "student":
            enrollment = await db.enrollments.find_one({
                "course_id": course_id,
                "user_id": user["id"],
            })
            if not enrollment:
                raise HTTPException(
                    status_code=403, detail="Not enrolled in this course"
                )

    lessons = await db.lessons.find(
        {"course_id": course_id},
        {
            "_id": 1,
            "title": 1,
            "description": 1,
            "video_url": 1,
            "video_type": 1,
            "order": 1,
            "materials": 1,
        },
    ).sort("order", 1).to_list(100)

    quizzes = await db.quizzes.find(
        {"course_id": course_id}, {"_id": 1, "title": 1, "translations": 1}
    ).to_list(100)

    course_data = _apply_course_translation({
        "id": str(course["_id"]),
        **{k: v for k, v in course.items() if k != "_id"},
        "lessons": [
            {"id": str(l["_id"]), **{k: v for k, v in l.items() if k != "_id"}}
            for l in lessons
        ],
        "quizzes": [],
    }, lang)
    for q in quizzes:
        quiz_data = {"id": str(q["_id"]), "title": q.get("title")}
        if lang:
            translated = q.get("translations", {}).get(lang)
            if translated and not translated.get("error"):
                quiz_data.update({
                    "title": translated.get("title", quiz_data.get("title")),
                    "display_language": lang,
                })
        course_data["quizzes"].append(quiz_data)
    return course_data


@router.put("/courses/{course_id}")
async def update_course(course_id: str, data: CourseUpdate, request: Request):
    user = await require_roles("admin")(request)
    update_data = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if "company_ids" in update_data:
        update_data["company_ids"] = await _validate_company_ids(update_data["company_ids"])
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    result = await db.courses.update_one(
        {"_id": parse_object_id(course_id, "course")},
        {"$set": update_data},
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    enrolled = []
    if "company_ids" in update_data and update_data["company_ids"]:
        updated_course = await db.courses.find_one(
            {"_id": parse_object_id(course_id, "course")}
        )
        enrolled = await enroll_company_students_in_course(
            updated_course,
            course_id,
            update_data["company_ids"],
            enrolled_by=user["id"],
        )
    return {"message": "Course updated", "company_enrolled": enrolled}


@router.delete("/courses/{course_id}")
async def delete_course(course_id: str, request: Request):
    await require_roles("admin")(request)
    result = await db.courses.delete_one(
        {"_id": parse_object_id(course_id, "course")}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Course not found")
    await delete_course_related_data(course_id)
    return {"message": "Course deleted"}
