from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from ai_settings import get_active_client, get_active_provider_settings, get_default_prompt
from auth_utils import get_current_user
from config import logger
from database import db
from db_utils import parse_object_id
from models import ChatMessageCreate
from progress_utils import require_enrollment

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat_with_ai(data: ChatMessageCreate, request: Request):
    user = await get_current_user(request)

    settings = await get_active_provider_settings()
    client = await get_active_client()
    if not client or not settings:
        raise HTTPException(status_code=503, detail="AI service not configured")

    model = settings.get("model", "deepseek-chat")

    await require_enrollment(user["id"], data.course_id)

    course = await db.courses.find_one(
        {"_id": parse_object_id(data.course_id, "course")}
    )
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.get("ai_assistant_enabled", True):
        raise HTTPException(status_code=403, detail="AI assistant is disabled for this course")
    course_context = (
        f"Course: {course.get('title', 'Unknown')}\nDescription: {course.get('description', '')}"
    )
    custom_prompt = (course.get("ai_assistant_prompt") or "").strip()
    prompt_suffix = (
        f"\n\nAdditional instructor guidance:\n{custom_prompt}"
        if custom_prompt
        else ""
    )

    history = await db.chat_messages.find({
        "course_id": data.course_id,
        "user_id": user["id"],
    }).sort("created_at", -1).limit(10).to_list(10)
    history.reverse()

    default_prompt = await get_default_prompt()
    messages = [
        {
            "role": "system",
            "content": (
                f"{default_prompt} {course_context}\n\n"
                "Help students understand the course material and answer their questions."
                f"{prompt_suffix}"
            ),
        }
    ]
    for h in history:
        messages.append({
            "role": h.get("role", "user"),
            "content": h.get("content", ""),
        })
    messages.append({"role": "user", "content": data.message})

    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7,
        )
        ai_response = response.choices[0].message.content

        now = datetime.now(timezone.utc).isoformat()
        await db.chat_messages.insert_one({
            "course_id": data.course_id,
            "user_id": user["id"],
            "role": "user",
            "content": data.message,
            "created_at": now,
        })
        await db.chat_messages.insert_one({
            "course_id": data.course_id,
            "user_id": user["id"],
            "role": "assistant",
            "content": ai_response,
            "created_at": now,
        })

        return {"response": ai_response}
    except Exception as e:
        logger.error("AI chat error: %s", e)
        raise HTTPException(status_code=500, detail="AI service error") from e


@router.get("/chat/{course_id}/history")
async def get_chat_history(course_id: str, request: Request):
    user = await get_current_user(request)
    await require_enrollment(user["id"], course_id)
    course = await db.courses.find_one({"_id": parse_object_id(course_id, "course")})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    if not course.get("ai_assistant_enabled", True):
        raise HTTPException(status_code=403, detail="AI assistant is disabled for this course")

    history = await db.chat_messages.find({
        "course_id": course_id,
        "user_id": user["id"],
    }).sort("created_at", 1).to_list(100)
    return [
        {
            "role": h.get("role"),
            "content": h.get("content"),
            "created_at": h.get("created_at"),
        }
        for h in history
    ]
