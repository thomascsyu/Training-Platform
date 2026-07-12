from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from auth_utils import get_current_user
from database import db
from db_utils import parse_object_id
from models import ForumPostCreate
from progress_utils import require_enrollment

router = APIRouter(tags=["forums"])


@router.post("/forums/posts")
async def create_forum_post(data: ForumPostCreate, request: Request):
    user = await get_current_user(request)
    await require_enrollment(user["id"], data.course_id)

    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Post content is required")

    if data.parent_id:
        parent = await db.forum_posts.find_one({"_id": parse_object_id(data.parent_id, "post")})
        if not parent or parent.get("course_id") != data.course_id:
            raise HTTPException(status_code=404, detail="Parent post not found")
        if parent.get("parent_id"):
            raise HTTPException(status_code=400, detail="Replies can only be added to top-level posts")

    post_doc = {
        "course_id": data.course_id,
        "content": content,
        "parent_id": data.parent_id,
        "user_id": user["id"],
        "user_name": user["name"],
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await db.forum_posts.insert_one(post_doc)
    return {
        "id": str(result.inserted_id),
        **{k: v for k, v in post_doc.items() if k != "_id"},
    }


@router.get("/forums/{course_id}")
async def get_forum_posts(course_id: str, request: Request):
    user = await get_current_user(request)
    await require_enrollment(user["id"], course_id)

    posts = await db.forum_posts.find(
        {"course_id": course_id, "parent_id": None}
    ).sort("created_at", -1).to_list(100)

    post_ids = [str(p["_id"]) for p in posts]
    replies_by_parent: dict[str, list] = {pid: [] for pid in post_ids}
    if post_ids:
        all_replies = await db.forum_posts.find(
            {"parent_id": {"$in": post_ids}}
        ).sort("created_at", 1).to_list(500)
        for reply in all_replies:
            parent = reply.get("parent_id")
            if parent in replies_by_parent:
                replies_by_parent[parent].append(reply)

    result = []
    for p in posts:
        pid = str(p["_id"])
        replies = replies_by_parent.get(pid, [])
        result.append({
            "id": pid,
            **{k: v for k, v in p.items() if k != "_id"},
            "replies": [
                {
                    "id": str(r["_id"]),
                    **{k: v for k, v in r.items() if k != "_id"},
                }
                for r in replies
            ],
        })
    return result


@router.delete("/forums/posts/{post_id}")
async def delete_forum_post(post_id: str, request: Request):
    user = await get_current_user(request)
    post = await db.forum_posts.find_one({"_id": parse_object_id(post_id, "post")})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if post["user_id"] != user["id"] and user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")

    await db.forum_posts.delete_one({"_id": parse_object_id(post_id, "post")})
    await db.forum_posts.delete_many({"parent_id": post_id})
    return {"message": "Post deleted"}
