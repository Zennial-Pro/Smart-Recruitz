"""Zingaro / CallWhiz voice-agent client — places outbound interview calls.

Talks to the public developer API (``developer.callwhiz.ai``) with a
``cw_live_sk`` API key:

  - Place a call:   POST {base}/v1/calls
        body  {agent_id, phone_number, context, webhook_url[, did]}
        ->    {success, data: {call_id, status, ...}}
  - Get transcript: GET  {base}/v1/calls/{call_id}/transcript
        ->    {success, data: {call_id, transcript: [{speaker, text, timestamp}],
                               summary, duration}}

A single prebuilt interview agent is reused for every call; the per-candidate
questions are injected at call time by the agent's pre-call webhook (handled in
``app/api/v1/voice_webhooks.py``), not by mutating the agent prompt here.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import structlog

from app.config.settings import get_settings

logger = structlog.get_logger(__name__)


class ZingaroError(Exception):
    """Raised when the voice platform returns an unrecoverable error."""


def _headers(api_key: str) -> dict[str, str]:
    return {
        "X-API-Key": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _extract_call_id(data: dict[str, Any]) -> str | None:
    """Pull the call id from a direct-ai-call response (field name varies)."""
    return (
        data.get("sip_call_id")
        or data.get("direct_ai_call_id")
        or data.get("call_id")
        or data.get("id")
    )


async def place_call(
    phone_e164: str, context: dict[str, Any], webhook_url: str | None = None
) -> dict[str, Any]:
    """Place an outbound interview call via the direct-ai-call API.

    POST {base}/api/direct-ai-call  (auth: X-API-Key)
        body {agent_id, target_number, did[, metadata]}

    Returns a normalized dict ``{"call_id", "status", "raw"}``. ``webhook_url`` is
    accepted for signature compatibility but unused — completion is delivered by
    the agent's pre/post-call webhooks configured in the Zingaro UI.

    Retries only on connection failures / 5xx — never on a confirmed 2xx (would
    risk double-dialing) or a 4xx. Raises ZingaroError on exhausted retries / non-2xx.
    """
    settings = get_settings()
    api_key = settings.zingaro_api_key.get_secret_value()
    if not api_key:
        raise ZingaroError("Zingaro API key is not configured")
    if not settings.zingaro_agent_id:
        raise ZingaroError("Zingaro agent id is not configured")
    if not settings.zingaro_caller_did:
        raise ZingaroError("Zingaro caller DID is not configured")

    url = f"{settings.zingaro_base_url.rstrip('/')}/api/direct-ai-call"
    payload: dict[str, Any] = {
        "agent_id": settings.zingaro_agent_id,
        "target_number": phone_e164,
        "did": settings.zingaro_caller_did,
    }
    # Pass correlation ids as metadata (echoed back where the platform supports it).
    if context:
        payload["metadata"] = context

    last_error: str | None = None
    for attempt in range(settings.zingaro_max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=settings.zingaro_timeout_seconds) as client:
                resp = await client.post(url, json=payload, headers=_headers(api_key))
        except httpx.HTTPError as exc:
            last_error = f"request failed: {exc}"
            logger.warning("zingaro.place_call.retry", attempt=attempt, error=str(exc))
            await asyncio.sleep(0.5 * (attempt + 1))
            continue

        if resp.status_code >= 500:
            last_error = f"server error {resp.status_code}"
            logger.warning("zingaro.place_call.retry", attempt=attempt, status=resp.status_code)
            await asyncio.sleep(0.5 * (attempt + 1))
            continue
        if resp.status_code in (401, 403):
            raise ZingaroError(f"Zingaro auth error ({resp.status_code}): {resp.text[:200]}")
        if resp.status_code >= 400:
            raise ZingaroError(f"Zingaro error {resp.status_code}: {resp.text[:200]}")

        try:
            body = resp.json()
        except ValueError as exc:
            raise ZingaroError(f"Zingaro returned non-JSON: {exc}") from exc

        data = body.get("data") if isinstance(body, dict) and "data" in body else body
        call_id = _extract_call_id(data) if isinstance(data, dict) else None
        if not call_id:
            raise ZingaroError(f"Zingaro response missing call id: {str(body)[:200]}")

        # Log the exact response so we know which id field to store/poll on.
        logger.info(
            "zingaro.place_call.ok",
            call_id=call_id,
            status=data.get("status"),
            response_keys=sorted(data.keys()) if isinstance(data, dict) else None,
            response=str(data)[:500],
        )
        return {"call_id": call_id, "status": data.get("status"), "raw": data}

    raise ZingaroError(f"Zingaro place_call failed after retries: {last_error}")


async def get_transcript(call_id: str) -> dict[str, Any] | None:
    """Fetch a completed call's transcript. Returns the ``data`` dict, or None.

    Returns None on 404 — the transcript may not be ready immediately after the
    call ends, so the caller can retry. Raises ZingaroError on other failures.
    """
    settings = get_settings()
    api_key = settings.zingaro_api_key.get_secret_value()
    if not api_key:
        raise ZingaroError("Zingaro API key is not configured")

    # Fallback only — the agent's post-call webhook normally carries the inline
    # `conversation`, so this is reached only if that didn't happen.
    url = f"{settings.zingaro_base_url.rstrip('/')}/api/direct-ai-call/{call_id}/status"
    try:
        async with httpx.AsyncClient(timeout=settings.zingaro_timeout_seconds) as client:
            resp = await client.get(url, headers=_headers(api_key))
    except httpx.HTTPError as exc:
        raise ZingaroError(f"Zingaro transcript request failed: {exc}") from exc

    if resp.status_code == 404:
        logger.info("zingaro.transcript.not_ready", call_id=call_id)
        return None
    if resp.status_code in (401, 403):
        raise ZingaroError(f"Zingaro auth error ({resp.status_code}): {resp.text[:200]}")
    if resp.status_code >= 400:
        raise ZingaroError(f"Zingaro transcript error {resp.status_code}: {resp.text[:200]}")

    try:
        body = resp.json()
    except ValueError as exc:
        raise ZingaroError(f"Zingaro returned non-JSON: {exc}") from exc

    data = body.get("data") if isinstance(body, dict) and "data" in body else body
    # Expose turns under "transcript" regardless of the platform's key name.
    if isinstance(data, dict) and not data.get("transcript") and data.get("conversation"):
        data = {**data, "transcript": data["conversation"]}
    return data


# Map the platform's speaker labels to interview roles. Be tolerant of variants.
_SPEAKER_LABELS = {
    "agent": "Interviewer",
    "assistant": "Interviewer",
    "bot": "Interviewer",
    "customer": "Candidate",
    "user": "Candidate",
    "caller": "Candidate",
}


def flatten_transcript(turns: list[dict[str, Any]] | None) -> str:
    """Turn the ``[{speaker, text}]`` array into a speaker-labeled string.

    Produces the shape Agent 5 scores against, e.g.::

        Interviewer: Tell me about your experience with Python.
        Candidate: I've used it for five years on backend services...
    """
    if not turns:
        return ""
    lines: list[str] = []
    for turn in turns:
        # Tolerate both shapes: transcript API uses {speaker, text}; the post-call
        # webhook's `conversation` uses {role, content}.
        text = (turn.get("text") or turn.get("content") or "").strip()
        if not text:
            continue
        speaker = (turn.get("speaker") or turn.get("role") or "").strip().lower()
        label = _SPEAKER_LABELS.get(speaker, speaker.title() or "Speaker")
        lines.append(f"{label}: {text}")
    return "\n".join(lines)
