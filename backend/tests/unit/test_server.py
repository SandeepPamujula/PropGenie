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
