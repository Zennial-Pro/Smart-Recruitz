"""Standalone auth endpoints — Google sign-in, plus email/password fallback."""

import secrets
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import get_settings
from app.core.security.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.session import get_db_session
from app.models.recruit_user import RecruitUser

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Google OAuth (primary sign-in) ─────────────────────────────────────────────

_INTENTS = {"candidate", "hiring_manager"}


def _normalize_intent(value: str | None) -> str:
    return value if value in _INTENTS else "hiring_manager"


@router.get("/google")
async def google_login(intent: str = "hiring_manager"):
    """Redirect the user to Google's consent screen.

    `intent` ("candidate" or "hiring_manager") is round-tripped via `state` so
    the callback knows which role to assign and where to send the user back.
    """
    settings = get_settings()
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "select_account",
        "state": _normalize_intent(intent),
    }
    return RedirectResponse("https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params))


@router.get("/google/callback")
async def google_callback(
    code: str | None = None,
    state: str | None = None,
    db: AsyncSession = Depends(get_db_session),
):
    """Exchange the Google code, upsert the user, and hand a JWT to the frontend."""
    settings = get_settings()
    intent = _normalize_intent(state)
    fail = RedirectResponse(f"{settings.frontend_url}/login?error=google")
    if not code:
        return fail

    async with httpx.AsyncClient(timeout=20) as client:
        token_res = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret.get_secret_value(),
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
                "code": code,
            },
        )
        access_token = token_res.json().get("access_token")
        if not access_token:
            return fail
        userinfo = (
            await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        ).json()

    email = (userinfo.get("email") or "").lower().strip()
    if not email:
        return fail

    row = await db.execute(select(RecruitUser).where(RecruitUser.email == email))
    user = row.scalar_one_or_none()
    if user is None:
        # First Google sign-in → create the account with the intent's role.
        user = RecruitUser(
            email=email,
            full_name=userinfo.get("name"),
            role="candidate" if intent == "candidate" else "hiring_manager",
            password_hash=hash_password(secrets.token_urlsafe(32)),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    jwt_token = create_access_token(user)
    # Candidates land on onboarding; hiring managers on the portal.
    dest = "/onboarding" if intent == "candidate" else "/hiring-manager"
    return RedirectResponse(
        f"{settings.frontend_url}/auth/callback?token={jwt_token}&next={dest}"
    )


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: str
    full_name: str | None = None
    role: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


def _user_out(u: RecruitUser) -> UserOut:
    return UserOut(id=str(u.id), email=u.email, full_name=u.full_name, role=u.role)


@router.post("/signup", response_model=TokenResponse, status_code=201)
async def signup(data: SignupRequest, db: AsyncSession = Depends(get_db_session)):
    email = data.email.lower().strip()
    if len(data.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")

    existing = await db.execute(select(RecruitUser).where(RecruitUser.email == email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="An account with this email already exists")

    user = RecruitUser(
        email=email,
        password_hash=hash_password(data.password),
        full_name=data.full_name,
        role="hiring_manager",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return TokenResponse(access_token=create_access_token(user), user=_user_out(user))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db_session)):
    """Mock hiring-manager login — accepts ANY email + password.

    If the email isn't known it's auto-provisioned as a hiring manager. The
    password is not verified (demo/dev convenience). Replace with a real
    password check before any production use.
    """
    email = data.email.lower().strip()
    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    row = await db.execute(select(RecruitUser).where(RecruitUser.email == email))
    user = row.scalar_one_or_none()
    if user is None:
        user = RecruitUser(
            email=email,
            full_name=email.split("@")[0],
            role="hiring_manager",
            password_hash=hash_password(data.password or secrets.token_urlsafe(16)),
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    return TokenResponse(access_token=create_access_token(user), user=_user_out(user))


@router.get("/me", response_model=UserOut)
async def me(user: RecruitUser = Depends(get_current_user)):
    return _user_out(user)
