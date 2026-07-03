"""LMS integration auth.

The LMS backend mints short-lived HS256 JWTs (signed with the shared
``SR_INTEGRATION_SECRET``) for both the ported candidate chatbot and the
hiring-manager iframe. This dependency validates those tokens.

When ``feature_lms_integration`` is disabled the dependency is a no-op so the
service still runs fully standalone in local development.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.config.settings import Settings, get_settings

ALGORITHM = "HS256"


@dataclass
class IntegrationPrincipal:
    """Identity extracted from a validated LMS token."""

    user_id: str | None
    candidate_ref: str | None
    role: str  # "candidate" | "hiring_manager"


async def get_principal(
    authorization: str | None = Header(default=None),
    settings: Settings = Depends(get_settings),
) -> IntegrationPrincipal:
    """Validate the bearer token and return the caller principal.

    No-op (anonymous principal) when LMS integration is turned off.
    """
    if not settings.feature_lms_integration:
        return IntegrationPrincipal(user_id=None, candidate_ref=None, role="candidate")

    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )

    token = authorization.split(" ", 1)[1].strip()
    try:
        claims = jwt.decode(
            token,
            settings.sr_integration_secret.get_secret_value(),
            algorithms=[ALGORITHM],
        )
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    return IntegrationPrincipal(
        user_id=claims.get("sub"),
        candidate_ref=claims.get("candidate_ref"),
        role=claims.get("role", "candidate"),
    )


async def require_hiring_manager(
    principal: IntegrationPrincipal = Depends(get_principal),
) -> IntegrationPrincipal:
    """Restrict an endpoint to hiring-manager-scoped tokens (when auth is on)."""
    settings = get_settings()
    if settings.feature_lms_integration and principal.role != "hiring_manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Hiring manager scope required",
        )
    return principal
