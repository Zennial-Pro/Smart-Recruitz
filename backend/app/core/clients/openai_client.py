"""Async OpenAI client singleton."""

import asyncio
import json
from functools import lru_cache

import structlog
from openai import AsyncOpenAI, RateLimitError

from app.config.settings import get_settings

logger = structlog.get_logger(__name__)


@lru_cache(maxsize=1)
def get_openai_client() -> AsyncOpenAI:
    """Return a cached AsyncOpenAI client."""
    settings = get_settings()
    return AsyncOpenAI(
        api_key=settings.openai_api_key.get_secret_value(),
        timeout=settings.openai_timeout_seconds,
        max_retries=settings.openai_max_retries,
    )


async def _chat_json(messages: list[dict], model: str | None = None) -> dict:
    """Chat completion → parsed JSON, with backoff on rate limits.

    The OpenAI SDK already retries 429s briefly; this adds a longer outer wait so a
    saturated per-minute TPM window (common on small orgs) has time to reset instead
    of failing the whole scoring / agent run.
    """
    settings = get_settings()
    client = get_openai_client()
    attempts = settings.openai_max_retries + 1
    for attempt in range(attempts):
        try:
            response = await client.chat.completions.create(
                model=model or settings.openai_model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            return json.loads(content)
        except RateLimitError:
            if attempt >= attempts - 1:
                raise
            wait = 5 * (attempt + 1)  # 5s, 10s, 15s...
            logger.warning("openai.rate_limited.retrying", attempt=attempt + 1, wait_seconds=wait)
            await asyncio.sleep(wait)
    return {}  # unreachable — loop always returns or raises


async def chat_completion(messages: list[dict], model: str | None = None) -> dict:
    """Send a chat completion request and return the parsed JSON response dict."""
    return await _chat_json(messages, model)


async def transcribe_audio(file_path: str) -> str:
    """Transcribe an audio/video file using OpenAI Whisper. Returns transcript text."""
    import asyncio
    import logging
    import tempfile
    from pathlib import Path

    logger = logging.getLogger(__name__)

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
        mp3_path = tmp.name

    proc = await asyncio.create_subprocess_exec(
        "ffmpeg", "-y", "-i", file_path, "-vn", "-ar", "16000", "-ac", "1", "-b:a", "64k", mp3_path,
        stdout=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode(errors="ignore")
        logger.error("ffmpeg failed (code %s): %s", proc.returncode, err)
        Path(mp3_path).unlink(missing_ok=True)
        raise RuntimeError(f"ffmpeg conversion failed: {err[-300:]}")

    mp3_size = Path(mp3_path).stat().st_size
    if mp3_size == 0:
        Path(mp3_path).unlink(missing_ok=True)
        raise RuntimeError("ffmpeg produced empty MP3 file")

    logger.info("Converted %s → MP3 (%d bytes)", file_path, mp3_size)

    client = get_openai_client()
    try:
        with open(mp3_path, "rb") as f:
            response = await client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                response_format="text",
            )
    finally:
        Path(mp3_path).unlink(missing_ok=True)

    return str(response)


async def text_to_speech(text: str, voice: str = "nova") -> bytes:
    """Generate spoken audio from text using OpenAI TTS. Returns MP3 bytes."""
    client = get_openai_client()
    response = await client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
        response_format="mp3",
    )
    return response.content


async def vision_completion(messages: list[dict], model: str | None = None) -> dict:
    """Send a vision chat completion (with image content blocks) and return parsed JSON."""
    return await _chat_json(messages, model)
