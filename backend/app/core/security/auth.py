"""Standalone authentication for SmartRecruitz.

Email/password accounts (hiring managers / admins) with argon2-hashed
passwords and HS256 JWT access tokens. Independent of the LMS.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import Settings, get_settings
from app.db.session import get_db_session
from app.models.recruit_user import RecruitUser

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


# ── Password hashing ─────────────────────────────────────────────────────────

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return pwd_context.verify(plain, hashed)
    except Exception:
        return False


# ── JWT ──────────────────────────────────────────────────────────────────────

def create_access_token(user: RecruitUser) -> str:
    settings = get_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    claims = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
        "exp": expire,
    }
    return jwt.encode(
        claims,
        settings.jwt_secret.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


# ── Dependencies ───────────────────────────────────────────────────────────────

async def get_current_user(
    authorization: str | None = Header(default=None),
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> RecruitUser:
    """Resolve the logged-in user from the bearer token, or 401."""
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = jwt.decode(
            token,
            settings.jwt_secret.get_secret_value(),
            algorithms=[settings.jwt_algorithm],
        )
        user_id = claims.get("sub")
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    row = await db.execute(select(RecruitUser).where(RecruitUser.id == user_id))
    user = row.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )
    return user


def require_roles(*roles: str):
    """Dependency factory: require the current user to hold one of `roles`."""

    async def _checker(user: RecruitUser = Depends(get_current_user)) -> RecruitUser:
        if roles and user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return user

    return _checker
