"""JWT auth middleware — protects all routes except the public whitelist."""

from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import JWTError
from starlette.middleware.base import BaseHTTPMiddleware

from services.auth import decode_token

# Exact paths that do not require authentication
PUBLIC_PATHS = frozenset({
    "/", "/health", "/docs", "/redoc", "/openapi.json",
    "/api/v1/queries/demo",       # public fixture endpoint — no auth needed
    "/api/v1/queries/available",  # read-only list
})
# Path prefixes that do not require authentication
PUBLIC_PREFIXES = ("/api/v1/auth/",)


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates the Bearer token for every request not in PUBLIC_PATHS/PREFIXES."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow exact public paths and auth prefix
        if path in PUBLIC_PATHS or any(path.startswith(p) for p in PUBLIC_PREFIXES):
            return await call_next(request)

        # OPTIONS preflight — let CORS middleware handle it
        if request.method == "OPTIONS":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Not authenticated"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = auth_header.split(" ", 1)[1]
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise JWTError("wrong token type")
            request.state.user_id = payload.get("sub")
        except JWTError:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Invalid or expired token"},
                headers={"WWW-Authenticate": "Bearer"},
            )

        return await call_next(request)
