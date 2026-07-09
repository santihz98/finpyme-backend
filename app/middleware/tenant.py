from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config import settings

# Paths that don't require a valid token
_PUBLIC = frozenset({"/", "/health", "/docs", "/redoc", "/openapi.json"})


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path

        # Auth routes and static paths are always public
        if path in _PUBLIC or path.startswith("/auth/"):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        request.state.empresa_id = None
        request.state.user_id = None

        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            try:
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
                )
                request.state.empresa_id = payload.get("empresa_id")
                request.state.user_id = payload.get("sub")
            except JWTError:
                pass  # FastAPI deps will reject with 401 if token is required

        return await call_next(request)
