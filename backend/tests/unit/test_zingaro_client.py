"""Unit tests for the Zingaro voice client (app/core/clients/zingaro_client.py).

Mocks httpx with a small fake client (respx isn't a dependency) and fake settings.
"""

from types import SimpleNamespace

import pytest

from app.core.clients import zingaro_client as zc
from app.core.clients.zingaro_client import ZingaroError, flatten_transcript


class _FakeSecret:
    def __init__(self, val):
        self._val = val

    def get_secret_value(self):
        return self._val


def _fake_settings(**overrides):
    base = dict(
        zingaro_api_key=_FakeSecret("cw_live_sk_test"),
        zingaro_agent_id="agent_test",
        zingaro_base_url="https://api.zingaro.ai",
        zingaro_caller_did="9240075596",
        zingaro_timeout_seconds=5,
        zingaro_max_retries=2,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


class _FakeResponse:
    def __init__(self, status_code, json_body=None, text=""):
        self.status_code = status_code
        self._json = json_body
        self.text = text

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


class _FakeClient:
    """Async-context fake; replays a queue of responses for post/get."""

    queue: list = []
    calls: list = []

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, json=None, headers=None):
        _FakeClient.calls.append(("POST", url, json))
        return _next()

    async def get(self, url, headers=None):
        _FakeClient.calls.append(("GET", url, None))
        return _next()


def _next():
    item = _FakeClient.queue.pop(0)
    if isinstance(item, Exception):
        raise item
    return item


@pytest.fixture(autouse=True)
def _patch(monkeypatch):
    _FakeClient.queue = []
    _FakeClient.calls = []
    monkeypatch.setattr(zc.httpx, "AsyncClient", _FakeClient)
    monkeypatch.setattr(zc, "get_settings", _fake_settings)
    # avoid real sleeping during retry tests
    async def _no_sleep(_):
        return None
    monkeypatch.setattr(zc.asyncio, "sleep", _no_sleep)


async def test_place_call_success():
    # Real direct-ai-call response is flat with sip_call_id.
    _FakeClient.queue = [
        _FakeResponse(200, {"sip_call_id": "call_123", "status": "initiating", "room_name": "r1"})
    ]
    data = await zc.place_call("+919014583641", {"interview_ref": "INT-1"})
    assert data["call_id"] == "call_123" and data["status"] == "initiating"
    method, url, body = _FakeClient.calls[0]
    assert method == "POST" and url.endswith("/api/direct-ai-call")
    assert body["target_number"] == "+919014583641"
    assert body["did"] == "9240075596"
    assert body["agent_id"] == "agent_test"
    assert body["metadata"] == {"interview_ref": "INT-1"}
    assert "phone_number" not in body and "webhook_url" not in body


async def test_place_call_auth_error_no_retry():
    _FakeClient.queue = [_FakeResponse(401, text="bad key")]
    with pytest.raises(ZingaroError):
        await zc.place_call("+919014583641", {})
    assert len(_FakeClient.calls) == 1  # 4xx is not retried


async def test_place_call_retries_on_5xx_then_succeeds():
    _FakeClient.queue = [
        _FakeResponse(503, text="down"),
        _FakeResponse(200, {"direct_ai_call_id": "call_9", "status": "initiating"}),
    ]
    data = await zc.place_call("+919014583641", {})
    assert data["call_id"] == "call_9"
    assert len(_FakeClient.calls) == 2


async def test_place_call_missing_call_id_raises():
    _FakeClient.queue = [_FakeResponse(200, {"status": "initiating"})]
    with pytest.raises(ZingaroError):
        await zc.place_call("+919014583641", {})


async def test_place_call_no_did_raises():
    import app.core.clients.zingaro_client as mod
    mod.get_settings = lambda: _fake_settings(zingaro_caller_did="")
    with pytest.raises(ZingaroError):
        await zc.place_call("+919014583641", {})


async def test_place_call_no_api_key():
    import app.core.clients.zingaro_client as mod
    mod.get_settings = lambda: _fake_settings(zingaro_api_key=_FakeSecret(""))
    with pytest.raises(ZingaroError):
        await zc.place_call("+919014583641", {}, "https://x/wh")


async def test_get_transcript_success():
    _FakeClient.queue = [
        _FakeResponse(200, {"success": True, "data": {"call_id": "c1", "transcript": [], "summary": "ok"}})
    ]
    data = await zc.get_transcript("c1")
    assert data["summary"] == "ok"


async def test_get_transcript_404_returns_none():
    _FakeClient.queue = [_FakeResponse(404, text="not ready")]
    assert await zc.get_transcript("c1") is None


def test_flatten_transcript_maps_speakers():
    turns = [
        {"speaker": "agent", "text": "Tell me about Python."},
        {"speaker": "customer", "text": "Five years on backend."},
        {"speaker": "agent", "text": ""},  # empty skipped
    ]
    out = flatten_transcript(turns)
    assert out == "Interviewer: Tell me about Python.\nCandidate: Five years on backend."


def test_flatten_transcript_role_content_shape():
    # The post-call webhook's `conversation` uses {role, content}, not {speaker, text}.
    turns = [
        {"role": "assistant", "content": "What's your experience?"},
        {"role": "user", "content": "Five years."},
    ]
    out = flatten_transcript(turns)
    assert out == "Interviewer: What's your experience?\nCandidate: Five years."


def test_flatten_transcript_empty():
    assert flatten_transcript([]) == ""
    assert flatten_transcript(None) == ""
