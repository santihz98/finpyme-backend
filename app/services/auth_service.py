from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.empresa import Empresa
from app.models.usuario import Usuario

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
bearer_scheme = HTTPBearer()

# In-memory blacklist for invalidated refresh token JTIs.
# Production: replace with Redis SADD/SISMEMBER or a DB table.
_refresh_blacklist: set[str] = set()


# ── Password helpers ────────────────────────────────────────────────────────

def _truncate(password: str) -> str:
    return password.encode("utf-8")[:72].decode("utf-8", errors="ignore")


def hash_password(password: str) -> str:
    return pwd_context.hash(_truncate(password))


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(_truncate(plain), hashed)
    except Exception:
        return False


# ── Token creation ──────────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: UUID) -> str:
    jti = str(uuid4())
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": str(user_id),
        "jti": jti,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


# ── Token decoding ──────────────────────────────────────────────────────────

def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def invalidate_refresh_token(token: str) -> None:
    payload = decode_token(token)
    if payload and payload.get("type") == "refresh":
        jti = payload.get("jti")
        if jti:
            _refresh_blacklist.add(jti)


def is_refresh_token_valid(token: str) -> dict | None:
    payload = decode_token(token)
    if not payload or payload.get("type") != "refresh":
        return None
    if payload.get("jti") in _refresh_blacklist:
        return None
    return payload


# ── FastAPI dependencies ────────────────────────────────────────────────────

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    _unauth = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise _unauth

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise _unauth

    try:
        uid = UUID(user_id)
    except ValueError:
        raise _unauth

    result = await db.execute(select(Usuario).where(Usuario.id == uid))
    user = result.scalar_one_or_none()
    if user is None or not user.activo:
        raise _unauth
    return user


async def get_current_empresa(
    current_user: Usuario = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Empresa:
    """
    Core multi-tenant guard. Every protected endpoint that touches tenant data
    should depend on this — it verifies the empresa exists and is active,
    ensuring a disabled empresa can't access data even with a valid JWT.
    """
    result = await db.execute(
        select(Empresa).where(Empresa.id == current_user.empresa_id)
    )
    empresa = result.scalar_one_or_none()
    if empresa is None or not empresa.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Empresa no encontrada o inactiva",
        )
    return empresa
