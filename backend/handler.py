import base64
import json
import os
import uuid
from datetime import datetime, timezone
from typing import Any

from dotenv import load_dotenv
load_dotenv()

from graph import generate_graph_sse
from utils.rate_limiter import check_rate_limit, RateLimitException, get_next_ist_midnight_string
from utils.logger import setup_logging, set_request_id

# Configure structured JSON logging on handler load
setup_logging()


def lambda_handler(event: dict[str, Any], *args: Any) -> Any:
    """
    AWS Lambda entry point that handles routing for /api/chat and /api/health.
    Supports both traditional buffered invocations and native AWS Lambda Function URL
    Response Streaming (using dynamic argument inspection).
    """
    # 1. Parse Routing and Path Information
    raw_path = event.get("rawPath") or "/"
    request_context = event.get("requestContext", {})
    
    # Set request ID context variable
    aws_request_id = request_context.get("requestId") or str(uuid.uuid4())
    set_request_id(aws_request_id)
    http_info = request_context.get("http", {})
    method = http_info.get("method", "GET").upper()

    # Normalize path checking (route matches /api/health or /api/chat)
    path = raw_path.rstrip("/")

    # 2. GET /api/health Route
    if path == "/api/health" and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "status": "healthy",
                    "version": "1.0.0",
                    "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                }
            ),
        }

    # Default fallback for base path
    if path in ("", "/") and method == "GET":
        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(
                {
                    "message": "Welcome to the PropGenie Lambda API",
                    "status": "active",
                }
            ),
        }

    # 3. POST /api/chat Route
    if path == "/api/chat" and method == "POST":
        # Extract headers and body
        headers = event.get("headers") or {}

        # Handle case-insensitive header matching
        x_session_id = None
        cf_viewer_address = None
        x_forwarded_for = None

        for k, v in headers.items():
            k_lower = k.lower()
            if k_lower == "x-session-id":
                x_session_id = v
            elif k_lower == "cloudfront-viewer-address":
                cf_viewer_address = v
            elif k_lower == "x-forwarded-for":
                x_forwarded_for = v

        session_id = x_session_id or str(uuid.uuid4())

        # Determine IP address
        if cf_viewer_address:
            ip = cf_viewer_address
        elif x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = http_info.get("sourceIp", "127.0.0.1")

        # 3.1 Rate Limit Check
        try:
            check_rate_limit(ip)
        except RateLimitException:
            return {
                "statusCode": 429,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "rate_limit_exceeded",
                    "message": "You've reached your daily search limit of 10. Please try again tomorrow!",
                    "reset_at": get_next_ist_midnight_string()
                }),
            }

        # Parse request body (handling potential Base64 encoding from AWS API Gateway/Lambda URL)
        body_str = event.get("body") or "{}"
        if event.get("isBase64Encoded"):
            try:
                body_str = base64.b64decode(body_str).decode("utf-8")
            except Exception as decode_err:
                return {
                    "statusCode": 400,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(
                        {"error": "bad_request", "message": f"Base64 decode failed: {decode_err}"}
                    ),
                }

        try:
            body_data = json.loads(body_str)
        except Exception as json_err:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"error": "bad_request", "message": f"Malformed JSON: {json_err}"}
                ),
            }

        user_message = body_data.get("message", "")
        if not user_message:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps(
                    {"error": "bad_request", "message": "Missing 'message' in request body."}
                ),
            }

        # 4. Check if invoked with Lambda Response Streaming
        # Signature: lambda_handler(event, response_stream, context) -> args has length 2
        # where args[0] is the response_stream object
        if len(args) == 2:
            response_stream = args[0]
            # Write stream metadata headers first
            metadata = {
                "statusCode": 200,
                "headers": {
                    "Content-Type": "text/event-stream",
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Session-ID": session_id,
                },
            }
            # Delimit metadata using null byte as required by Lambda Function URL stream protocol
            response_stream.write(json.dumps(metadata).encode("utf-8") + b"\0")

            # Stream each chunk
            for chunk in generate_graph_sse(session_id, ip, user_message):
                response_stream.write(chunk.encode("utf-8"))

            return None

        # 5. Standard Buffered Invocation (Fallback & Testing)
        # Collect all stream chunks and return as a standard buffered HTTP payload
        sse_chunks = list(generate_graph_sse(session_id, ip, user_message))
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Session-ID": session_id,
            },
            "body": "".join(sse_chunks),
        }

    # 4. Route Not Found
    return {
        "statusCode": 404,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"error": "not_found", "message": f"Route not found: {method} {raw_path}"}),
    }
