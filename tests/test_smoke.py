"""Smoke tests that prove the service boots and the chat path streams end-to-end in
mock mode (no external services, no API keys). Run: pytest"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    # Context-manager form runs the lifespan, so app.state services are wired.
    with TestClient(app) as c:
        yield c


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready_reports_mock_mode(client):
    r = client.get("/ready")
    body = r.json()
    assert body["status"] == "ready"
    assert body["llm"] == "mock"              # no GEMINI_API_KEY in tests
    assert body["memory"] == "in-memory"
    assert body["database"] == "disconnected"  # no MONGODB_URI in tests


def test_conversations_empty(client):
    r = client.get("/api/v1/tutor/conversations")
    assert r.status_code == 200
    assert r.json()["items"] == []


def test_chat_sync_returns_answer(client):
    r = client.post(
        "/api/v1/tutor/chat/sync",
        json={"course_id": "python", "message": "What is a variable?", "mode": "tutor"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["answer"].strip()
    assert body["conversation_id"]
    assert body["usage"]["model"] == "mock"


def test_chat_streams_sse(client):
    with client.stream(
        "POST",
        "/api/v1/tutor/chat",
        json={"course_id": "python", "message": "Explain loops", "mode": "tutor"},
    ) as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]
        body = "".join(chunk for chunk in r.iter_text())
    assert "data:" in body
    assert '"type":"done"' in body


def test_suggestions(client):
    r = client.get("/api/v1/tutor/suggestions", params={"lessonId": "abc"})
    assert r.status_code == 200
    assert len(r.json()["items"]) == 4
