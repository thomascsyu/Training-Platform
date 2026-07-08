import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from auth_utils import require_roles
from clients import deepseek_client
from config import LANGUAGE_NAMES, SUPPORTED_LANGUAGES, logger
from database import db
from db_utils import parse_object_id
from models import TranslateCourseRequest, TranslateQuizRequest, TranslateRequest


router = APIRouter(tags=["translate"])

@router.post("/translate/text")
async def translate_text(data: TranslateRequest, request: Request):
    """Translate a single text using Deepseek AI"""
    user = await require_roles("admin")(request)
    
    if not deepseek_client:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    # Validate languages
    if data.target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported target language: {data.target_language}")
    
    source_name = LANGUAGE_NAMES.get(data.source_language, data.source_language)
    target_name = LANGUAGE_NAMES.get(data.target_language, data.target_language)
    
    try:
        response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"You are a professional translator. Translate the following text from {source_name} to {target_name}. Only output the translation, nothing else. Preserve formatting, line breaks, and any special characters."
                },
                {
                    "role": "user",
                    "content": data.text
                }
            ],
            temperature=0.3
        )
        translated = response.choices[0].message.content.strip()
        return {"translated_text": translated, "source": data.source_language, "target": data.target_language}
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail="Translation service error")

@router.post("/translate/course/{course_id}")
async def translate_course(course_id: str, data: TranslateCourseRequest, request: Request):
    """Auto-translate course title and description to multiple languages"""
    user = await require_roles("admin")(request)
    
    if not deepseek_client:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    course = await db.courses.find_one({"_id": parse_object_id(course_id, "course")})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    # Validate target languages
    for lang in data.target_languages:
        if lang not in SUPPORTED_LANGUAGES:
            raise HTTPException(status_code=400, detail=f"Unsupported language: {lang}")
    
    source_lang = course.get("language", "en")
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    
    translations = {}
    
    for target_lang in data.target_languages:
        if target_lang == source_lang:
            continue
            
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        
        try:
            # Translate title
            title_response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator specializing in educational content. Translate the following course title from {source_name} to {target_name}. Only output the translation, nothing else."
                    },
                    {"role": "user", "content": course.get("title", "")}
                ],
                temperature=0.3
            )
            translated_title = title_response.choices[0].message.content.strip()
            
            # Translate description
            desc_response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a professional translator specializing in educational content. Translate the following course description from {source_name} to {target_name}. Preserve formatting and paragraph breaks. Only output the translation, nothing else."
                    },
                    {"role": "user", "content": course.get("description", "")}
                ],
                temperature=0.3
            )
            translated_desc = desc_response.choices[0].message.content.strip()
            
            translations[target_lang] = {
                "title": translated_title,
                "description": translated_desc,
                "language_name": target_name
            }
            
        except Exception as e:
            logger.error(f"Translation error for {target_lang}: {e}")
            translations[target_lang] = {"error": str(e)}
    
    # Store translations in the course document
    await db.courses.update_one(
        {"_id": parse_object_id(course_id, "course")},
        {"$set": {"translations": translations, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {
        "course_id": course_id,
        "source_language": source_lang,
        "translations": translations
    }

@router.post("/translate/quiz/{quiz_id}")
async def translate_quiz(quiz_id: str, data: TranslateQuizRequest, request: Request):
    """Auto-translate quiz questions and options to multiple languages"""
    user = await require_roles("admin")(request)
    
    if not deepseek_client:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    quiz = await db.quizzes.find_one({"_id": parse_object_id(quiz_id, "quiz")})
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    # Get course language
    course = await db.courses.find_one({"_id": parse_object_id(quiz.get("course_id"), "course")})
    source_lang = course.get("language", "en") if course else "en"
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    
    translations = {}
    
    for target_lang in data.target_languages:
        if target_lang == source_lang or target_lang not in SUPPORTED_LANGUAGES:
            continue
            
        target_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        
        try:
            # Translate title
            title_response = deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"Translate from {source_name} to {target_name}. Only output the translation."
                    },
                    {"role": "user", "content": quiz.get("title", "")}
                ],
                temperature=0.3
            )
            translated_title = title_response.choices[0].message.content.strip()
            
            # Translate questions
            translated_questions = []
            for q in quiz.get("questions", []):
                # Translate question text
                q_response = deepseek_client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {
                            "role": "system",
                            "content": f"Translate this quiz question from {source_name} to {target_name}. Only output the translation."
                        },
                        {"role": "user", "content": q.get("question", "")}
                    ],
                    temperature=0.3
                )
                translated_q = q_response.choices[0].message.content.strip()
                
                # Translate options
                translated_opts = []
                for opt in q.get("options", []):
                    opt_response = deepseek_client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {
                                "role": "system",
                                "content": f"Translate from {source_name} to {target_name}. Only output the translation."
                            },
                            {"role": "user", "content": opt}
                        ],
                        temperature=0.3
                    )
                    translated_opts.append(opt_response.choices[0].message.content.strip())
                
                translated_questions.append({
                    "question": translated_q,
                    "options": translated_opts,
                    "correct_answer": q.get("correct_answer")  # Index stays the same
                })
            
            translations[target_lang] = {
                "title": translated_title,
                "questions": translated_questions,
                "language_name": target_name
            }
            
        except Exception as e:
            logger.error(f"Quiz translation error for {target_lang}: {e}")
            translations[target_lang] = {"error": str(e)}
    
    # Store translations in the quiz document
    await db.quizzes.update_one(
        {"_id": parse_object_id(quiz_id, "quiz")},
        {"$set": {"translations": translations}}
    )
    
    return {
        "quiz_id": quiz_id,
        "source_language": source_lang,
        "translations": translations
    }

@router.post("/courses/{course_id}/create-translation")
async def create_translated_course(course_id: str, target_language: str, request: Request):
    """Create a new course as a translation of an existing course"""
    user = await require_roles("admin")(request)
    
    if not deepseek_client:
        raise HTTPException(status_code=503, detail="AI service not configured")
    
    if target_language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {target_language}")
    
    course = await db.courses.find_one({"_id": parse_object_id(course_id, "course")})
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    source_lang = course.get("language", "en")
    source_name = LANGUAGE_NAMES.get(source_lang, source_lang)
    target_name = LANGUAGE_NAMES.get(target_language, target_language)
    
    # Check if translation already exists in stored translations
    stored_translations = course.get("translations", {})
    if target_language in stored_translations and "title" in stored_translations[target_language]:
        translated_title = stored_translations[target_language]["title"]
        translated_desc = stored_translations[target_language]["description"]
    else:
        # Translate title
        title_response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate this course title from {source_name} to {target_name}. Only output the translation."
                },
                {"role": "user", "content": course.get("title", "")}
            ],
            temperature=0.3
        )
        translated_title = title_response.choices[0].message.content.strip()
        
        # Translate description
        desc_response = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate this course description from {source_name} to {target_name}. Preserve formatting. Only output the translation."
                },
                {"role": "user", "content": course.get("description", "")}
            ],
            temperature=0.3
        )
        translated_desc = desc_response.choices[0].message.content.strip()
    
    # Create new course
    new_course = {
        "title": translated_title,
        "description": translated_desc,
        "thumbnail_url": course.get("thumbnail_url"),
        "video_url": course.get("video_url"),
        "video_type": course.get("video_type"),
        "price": course.get("price", 0),
        "is_free": course.get("is_free", True),
        "is_private": course.get("is_private", False),
        "passing_score": course.get("passing_score", 70),
        "materials": course.get("materials", []),
        "ai_assistant_enabled": course.get("ai_assistant_enabled", True),
        "ai_assistant_prompt": course.get("ai_assistant_prompt"),
        "language": target_language,
        "category": course.get("category"),
        "source_course_id": course_id,  # Reference to original course
        "created_by": user["id"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    result = await db.courses.insert_one(new_course)
    new_course_id = str(result.inserted_id)
    
    # Also translate lessons if any
    lessons = await db.lessons.find({"course_id": course_id}).to_list(100)
    for lesson in lessons:
        lesson_title_resp = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate from {source_name} to {target_name}. Only output the translation."
                },
                {"role": "user", "content": lesson.get("title", "")}
            ],
            temperature=0.3
        )
        lesson_desc_resp = deepseek_client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {
                    "role": "system",
                    "content": f"Translate from {source_name} to {target_name}. Only output the translation."
                },
                {"role": "user", "content": lesson.get("description", "")}
            ],
            temperature=0.3
        )
        
        await db.lessons.insert_one({
            "course_id": new_course_id,
            "title": lesson_title_resp.choices[0].message.content.strip(),
            "description": lesson_desc_resp.choices[0].message.content.strip(),
            "video_url": lesson.get("video_url"),
            "video_type": lesson.get("video_type"),
            "order": lesson.get("order"),
            "materials": lesson.get("materials", []),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
    
    return {
        "new_course_id": new_course_id,
        "title": translated_title,
        "language": target_language,
        "language_name": target_name
    }
