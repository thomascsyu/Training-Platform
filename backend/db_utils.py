from bson import ObjectId
from bson.errors import InvalidId
from fastapi import HTTPException


def parse_object_id(value: str, resource: str = "resource") -> ObjectId:
    """Parse a MongoDB ObjectId or raise HTTP 400."""
    try:
        return ObjectId(value)
    except (InvalidId, TypeError) as exc:
        raise HTTPException(
            status_code=400, detail=f"Invalid {resource} id"
        ) from exc
