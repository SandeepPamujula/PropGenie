import json
from typing import List
from unittest.mock import patch

from handler import lambda_handler


class MockResponseStream:
    """Helper class to mock AWS Lambda Response Streaming object."""

    def __init__(self) -> None:
        self.chunks: List[bytes] = []

    def write(self, data: bytes) -> None:
        self.chunks.append(data)


def test_lambda_handler_health() -> None:
    """
    Verifies that the Lambda handler correctly routes and responds to the health check.
    """
    event = {
        "rawPath": "/api/health",
        "requestContext": {"http": {"method": "GET"}},
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "application/json"
    body = json.loads(response["body"])
    assert body["status"] == "healthy"
    assert body["version"] == "1.0.0"


def test_lambda_handler_chat_buffered() -> None:
    """
    Verifies that the Lambda handler correctly routes and returns a standard
    buffered response when invoked without response streaming.
    """
    event = {
        "rawPath": "/api/chat",
        "requestContext": {"http": {"method": "POST", "sourceIp": "192.168.1.1"}},
        "headers": {"x-session-id": "test-session-buffered"},
        "body": json.dumps({"message": "looking for a house in bangalore"}),
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "text/event-stream"
    assert response["headers"]["X-Session-ID"] == "test-session-buffered"
    body_content = response["body"]
    assert "event: agent_status" in body_content
    assert "Understanding your search" in body_content
    assert "event: done" in body_content


def test_lambda_handler_chat_streaming() -> None:
    """
    Verifies that the Lambda handler correctly implements response streaming
    when provided with a streaming argument.
    """
    event = {
        "rawPath": "/api/chat",
        "requestContext": {"http": {"method": "POST", "sourceIp": "192.168.1.1"}},
        "headers": {"X-Session-ID": "test-session-stream"},
        "body": json.dumps({"message": "looking for a flat in chennai"}),
    }

    mock_stream = MockResponseStream()
    context = None

    # Call with 3 arguments to trigger streaming flow: event, response_stream, context
    lambda_handler(event, mock_stream, context)

    assert len(mock_stream.chunks) > 0
    # First chunk is metadata ended with \0
    metadata_chunk = mock_stream.chunks[0]
    assert metadata_chunk.endswith(b"\0")
    metadata_json = json.loads(metadata_chunk[:-1].decode("utf-8"))
    assert metadata_json["statusCode"] == 200
    assert metadata_json["headers"]["Content-Type"] == "text/event-stream"
    assert metadata_json["headers"]["X-Session-ID"] == "test-session-stream"

    # Check other chunks
    all_chunks_text = b"".join(mock_stream.chunks[1:]).decode("utf-8")
    assert "event: agent_status" in all_chunks_text
    assert "event: done" in all_chunks_text


def test_lambda_handler_not_found() -> None:
    """
    Verifies that the Lambda handler returns a 404 for unknown endpoints.
    """
    event = {
        "rawPath": "/api/unknown",
        "requestContext": {"http": {"method": "GET"}},
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 404
    body = json.loads(response["body"])
    assert body["error"] == "not_found"


@patch("handler.check_rate_limit")
def test_lambda_handler_chat_rate_limited(mock_check, auto_mock_db_client) -> None:
    """
    Verifies that the Lambda handler returns a 429 when rate limit is exceeded.
    """
    from utils.rate_limiter import RateLimitException
    mock_check.side_effect = RateLimitException("Rate limit exceeded")

    event = {
        "rawPath": "/api/chat",
        "requestContext": {"http": {"method": "POST", "sourceIp": "192.168.1.1"}},
        "headers": {"x-session-id": "test-session-rate-limited"},
        "body": json.dumps({"message": "looking for a house in bangalore"}),
    }
    response = lambda_handler(event, None)
    assert response["statusCode"] == 429
    assert response["headers"]["Content-Type"] == "application/json"
    body = json.loads(response["body"])
    assert body["error"] == "rate_limit_exceeded"
    assert "reached your daily search limit" in body["message"]
    assert "reset_at" in body

