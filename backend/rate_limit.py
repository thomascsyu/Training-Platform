import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

# path prefix -> (max_requests, window_seconds)
DEFAULT_LIMITS: dict[str, tuple[int, int]] = {
    "/api/auth/login": (10, 60),
    "/api/auth/register": (5, 60),
    "/api/chat": (30, 60),
}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, limits: dict[str, tuple[int, int]] | None = None):
        super().__init__(app)
        self.limits = limits or DEFAULT_LIMITS
        self._hits: dict[str, list[float]] = defaultdict(list)

    def _client_key(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"

    def _is_limited(self, key: str, path: str) -> bool:
        for prefix, (max_requests, window) in self.limits.items():
            if path.startswith(prefix):
                now = time.time()
                window_start = now - window
                hits = [t for t in self._hits[key] if t > window_start]
                if len(hits) >= max_requests:
                    self._hits[key] = hits
                    return True
                hits.append(now)
                self._hits[key] = hits
                return False
        return False

    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        if request.method == "POST" and self._is_limited(
            f"{self._client_key(request)}:{path}", path
        ):
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please try again later."},
            )
        return await call_next(request)
