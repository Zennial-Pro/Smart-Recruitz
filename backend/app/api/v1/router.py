"""Combine all v1 API routers."""

from fastapi import APIRouter, Depends

from app.api.v1.agents import router as agents_router
from app.api.v1.auth import router as auth_router
from app.api.v1.candidates import router as candidates_router
from app.api.v1.hiring_manager import router as hiring_manager_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.voice_webhooks import router as voice_webhooks_router
from app.core.security.auth import get_current_user, require_roles

api_router = APIRouter(prefix="/api/v1")

# Auth (signup / login / me / google) — open.
api_router.include_router(auth_router)

# Voice-interview webhooks — called by Zingaro (server-to-server), NOT a logged-in
# user. No JWT; each handler verifies a shared secret / HMAC signature instead.
api_router.include_router(voice_webhooks_router)

# Candidate onboarding flow — requires a logged-in user (candidate signs in first).
api_router.include_router(candidates_router, dependencies=[Depends(get_current_user)])
api_router.include_router(agents_router, dependencies=[Depends(get_current_user)])
api_router.include_router(tasks_router, dependencies=[Depends(get_current_user)])

# Hiring-manager portal — requires a logged-in hiring manager / admin.
api_router.include_router(
    hiring_manager_router,
    dependencies=[Depends(require_roles("hiring_manager", "admin"))],
)
