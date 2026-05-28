from unittest.mock import patch
from fastapi.testclient import TestClient
from server import app

client = TestClient(app)


def test_server_health() -> None:
    """
    Verifies that the FastAPI server routes and responds to the health check correctly.
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "healthy"
    assert body["version"] == "1.0.0"


def test_server_chat() -> None:
    """
    Verifies that the FastAPI server routes chat searches and streams SSE chunks correctly.
    """
    payload = {"message": "looking for a flat in Pune"}
    headers = {"X-Session-ID": "test-fastapi-session"}
    response = client.post("/api/chat", json=payload, headers=headers)
    assert response.status_code == 200
    assert (
        "text/event-stream" in response.headers["content-type"]
    )  # FastAPI appends ; charset=utf-8
    assert response.headers["X-Session-ID"] == "test-fastapi-session"

    # Verify stream contents
    stream_content = response.text
    assert "event: agent_status" in stream_content
    assert "event: done" in stream_content


@patch("server.check_rate_limit")
def test_server_chat_rate_limited(mock_check, auto_mock_db_client) -> None:
    """
    Verifies that the FastAPI server returns a 429 when rate limit is exceeded.
    """
    from utils.rate_limiter import RateLimitException
    mock_check.side_effect = RateLimitException("Rate limit exceeded")

    payload = {"message": "looking for a flat in Pune"}
    headers = {"X-Session-ID": "test-fastapi-session"}
    response = client.post("/api/chat", json=payload, headers=headers)
    assert response.status_code == 429
    body = response.json()
    assert body["error"] == "rate_limit_exceeded"
    assert "reached your daily search limit" in body["message"]
    assert "reset_at" in body

