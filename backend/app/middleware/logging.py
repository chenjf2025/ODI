import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


EXCLUDED_PATHS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
}


class OperationLogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if any(request.url.path.startswith(p) for p in EXCLUDED_PATHS) or request.url.path.startswith("/uploads"):
            return await call_next(request)

        response = await call_next(request)
        return response
