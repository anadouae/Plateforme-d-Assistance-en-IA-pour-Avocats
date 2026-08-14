"""Health endpoints — /health et alias /api/health."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_live_root_and_api_alias():
    r1 = client.get("/health/live")
    r2 = client.get("/api/health/live")
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert r1.json().get("status") == "ok"
    assert r2.json().get("status") == "ok"


def test_health_stt_alias():
    r = client.get("/api/health/stt")
    assert r.status_code == 200
    body = r.json()
    assert "enabled" in body
    assert "model" in body
