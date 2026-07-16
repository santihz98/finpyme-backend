from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.middleware.tenant import TenantMiddleware
from app.routers import analisis, auth, empresas, periodos

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="API financiera con IA para pymes colombianas",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── Middleware (order matters: CORS first, then tenant) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://finpyme-dashboard.vercel.app",
        "https://finpyme-dashboard-*.vercel.app",
        "http://localhost:3000",
        "http://localhost:3001",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)
app.add_middleware(TenantMiddleware)

# ── Routers ──
app.include_router(auth.router)
app.include_router(empresas.router)
app.include_router(periodos.router)
app.include_router(analisis.router)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "app": settings.APP_NAME}
