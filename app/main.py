import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from fastapi import FastAPI

from app.config import settings
from app.middleware.tenant import TenantMiddleware
from app.routers import analisis, auth, empresas, periodos, reportes

# ── CORS config ──────────────────────────────────────────────────────────────

_ALLOWED_ORIGINS = [
    "https://finpyme-dashboard.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
]

_VERCEL_PREVIEW = re.compile(r"https://finpyme-dashboard-[^.]+\.vercel\.app")


def _is_allowed(origin: str) -> bool:
    return origin in _ALLOWED_ORIGINS or bool(_VERCEL_PREVIEW.match(origin))


_CORS_HEADERS = {
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
    "Access-Control-Allow-Headers": "*",
}


class DynamicCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin", "")

        if request.method == "OPTIONS" and _is_allowed(origin):
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Max-Age"] = "3600"
            response.headers.update(_CORS_HEADERS)
            return response

        response = await call_next(request)

        if _is_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers.update(_CORS_HEADERS)

        return response


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API financiera con IA para pymes colombianas",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Order matters: CORS first, then tenant
app.add_middleware(DynamicCORSMiddleware)
app.add_middleware(TenantMiddleware)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth.router)
app.include_router(empresas.router)
app.include_router(periodos.router)
app.include_router(analisis.router)
app.include_router(reportes.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}
