"""Phase 3 — Realtime readiness probe (``GET /api/v3/health/realtime``).

The probe verifies the API-gateway Realtime route (the same path the frontend
websocket client uses). It never weakens messaging authorization — it only
reports whether the Realtime upstream is reachable.
"""

from __future__ import annotations

from api import v3_health


def test_probe_unconfigured(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    result = v3_health._probe_realtime()
    assert result["status"] == "unconfigured"
    assert result["url"] == ""


def test_probe_down_when_gateway_unreachable(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "http://127.0.0.1:9")
    result = v3_health._probe_realtime()
    assert result["status"] == "down"
    assert result["url"] == "http://127.0.0.1:9/realtime/v1/websocket"


def test_probe_down_on_503(monkeypatch):
    class _FakeResponse:
        status = 503

        def read(self):
            return b""

    class _FakeConnection:
        def __init__(self, *args, **kwargs):
            pass

        def request(self, *args, **kwargs):
            pass

        def getresponse(self):
            return _FakeResponse()

        def close(self):
            pass

    monkeypatch.setenv("SUPABASE_URL", "http://supabase.test:54425")
    monkeypatch.setattr(v3_health.http.client, "HTTPConnection", _FakeConnection)
    result = v3_health._probe_realtime()
    assert result["status"] == "down"
    assert result["http_status"] == 503


def test_probe_up_on_101_websocket_handshake(monkeypatch):
    class _FakeResponse:
        status = 101

        def read(self):
            return b""

    class _FakeConnection:
        def __init__(self, *args, **kwargs):
            pass

        def request(self, *args, **kwargs):
            pass

        def getresponse(self):
            return _FakeResponse()

        def close(self):
            pass

    monkeypatch.setenv("SUPABASE_URL", "http://supabase.test:54425")
    monkeypatch.setattr(v3_health.http.client, "HTTPConnection", _FakeConnection)
    result = v3_health._probe_realtime()
    assert result["status"] == "up"
    assert result["http_status"] == 101


def test_health_realtime_endpoint_is_structured(client, monkeypatch):
    monkeypatch.setattr(
        v3_health,
        "_probe_realtime",
        lambda: {"status": "down", "url": "http://x", "http_status": 503, "note": "n"},
    )
    response = client.get("/api/v3/health/realtime")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "down"
    assert "http_status" in body
    assert "note" in body
