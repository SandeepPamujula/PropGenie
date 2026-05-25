import os
import uuid
from datetime import datetime, timezone

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from graph import generate_graph_sse
from pydantic import BaseModel
from utils.rate_limiter import check_rate_limit, RateLimitExceededException, get_next_ist_midnight_string

app = FastAPI(title="PropGenie Backend Service", version="1.0.0")

# Enable CORS for local Next.js development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    """
    Validation schema for the chat request payload.
    """

    message: str


@app.get("/")
async def root() -> dict[str, str]:
    """
    Welcome endpoint returning basic API metadata.
    """
    return {
        "message": "Welcome to the PropGenie Backend API",
        "status": "active",
    }


@app.get("/api/health")
async def health() -> dict[str, str]:
    """
    API Health check endpoint conforming to the system API contract.
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


@app.post("/api/chat")
async def chat(
    request: Request,
    chat_request: ChatRequest,
    x_session_id: str | None = Header(default=None),
) -> StreamingResponse:
    """
    Chat search endpoint. Invokes the agent pipeline and streams
    updates back to the user via Server-Sent Events (SSE).
    """
    # Extract session ID or generate a new unique identifier
    session_id = x_session_id or str(uuid.uuid4())

    # Extract client IP address
    # 1. CloudFront-Viewer-Address (for production geolocation/rate-limiting)
    # 2. X-Forwarded-For (standard reverse proxies)
    # 3. Client Host (local development fallback)
    cf_ip = request.headers.get("cloudfront-viewer-address")
    x_forwarded = request.headers.get("x-forwarded-for")

    if cf_ip:
        ip = cf_ip
    elif x_forwarded:
        ip = x_forwarded.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "127.0.0.1"

    # Rate Limit Check
    try:
        check_rate_limit(ip)
    except RateLimitExceededException:
        return JSONResponse(
            status_code=429,
            content={
                "error": "rate_limit_exceeded",
                "message": "You've reached your daily search limit of 10. Please try again tomorrow!",
                "reset_at": get_next_ist_midnight_string()
            }
        )

    # Invoke the shared agent graph generator
    sse_generator = generate_graph_sse(session_id, ip, chat_request.message)

    # Return StreamingResponse with SSE headers
    return StreamingResponse(
        sse_generator,
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Session-ID": session_id,
        },
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
