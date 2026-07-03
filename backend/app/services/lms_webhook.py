"""Outbound approval webhook into the LMS.

When a hiring manager approves/rejects a candidate, notify the LMS so it can
flip the candidate's ``recruitment_status`` and unlock (or block) the dashboard.

The payload is authenticated with an HMAC-SHA256 signature over
``{candidate_ref}.{decision}`` using the shared ``LMS_WEBHOOK_SECRET`` — the
same scheme the LMS verifies on its side.

Gated behind the ``feature_webhook_outbound`` flag so it stays inert in
standalone development.
"""

from __future__ import annotations

import hmac
from hashlib import sha256

import httpx
import structlog

from app.config.settings import get_settings

logger = structlog.get_logger(__name__)


def _sign(candidate_ref: str, decision: str, secret: str) -> str:
    return hmac.new(
        secret.encode(),
        f"{candidate_ref}.{decision}".encode(),
        sha256,
    ).hexdigest()


async def notify_lms_decision(
    candidate_ref: str,
    decision: str,
    scored_result: dict | None = None,
) -> bool:
    """POST the approval decision to the LMS. Returns True on a 2xx response.

    Never raises — a webhook failure must not break the admin's approve action;
    the LMS can reconcile via its own status poll if needed.
    """
    settings = get_settings()
    if not settings.feature_webhook_outbound:
        logger.info("lms_webhook.skipped", reason="feature_disabled", candidate_ref=candidate_ref)
        return False

    signature = _sign(candidate_ref, decision, settings.lms_webhook_secret.get_secret_value())
    payload = {
        "candidate_ref": candidate_ref,
        "decision": decision,
        "scored_result": scored_result,
    }

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                settings.lms_webhook_url,
                json=payload,
                headers={"X-SR-Signature": signature},
            )
        if resp.status_code // 100 == 2:
            logger.info("lms_webhook.delivered", candidate_ref=candidate_ref, decision=decision)
            return True
        logger.warning(
            "lms_webhook.bad_status",
            candidate_ref=candidate_ref,
            status_code=resp.status_code,
            body=resp.text[:500],
        )
        return False
    except Exception as exc:  # noqa: BLE001 — never propagate webhook failures
        logger.error("lms_webhook.error", candidate_ref=candidate_ref, error=str(exc))
        return False
