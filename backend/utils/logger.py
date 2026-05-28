import contextvars
import hashlib
import json
import logging
from datetime import datetime, timezone
from typing import Any, Optional

# Context variable to hold the request/session ID globally for current execution context
request_id_var = contextvars.ContextVar("request_id", default="N/A")


class JSONFormatter(logging.Formatter):
    """
    Custom logging Formatter that outputs log records as JSON strings.
    """

    def format(self, record: logging.LogRecord) -> str:
        # Determine the level name
        level = record.levelname

        # Build standard log payload
        log_payload = {
            "timestamp": datetime.fromtimestamp(record.created, timezone.utc)
            .isoformat()
            .replace("+00:00", "Z"),
            "level": level,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": request_id_var.get(),
        }

        # Format exception info if present
        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        # Merge extra fields if any were passed via extra
        if hasattr(record, "extra_fields"):
            log_payload.update(record.extra_fields)

        return json.dumps(log_payload)


def setup_logging(default_level: int = logging.INFO) -> None:
    """
    Configures the root logging handler to output JSON format to standard output.
    Cleans up any existing default root handlers.
    """
    root = logging.getLogger()

    # Remove existing handlers to avoid duplicate output or incorrect formats
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    # Attach JSON stream handler
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JSONFormatter())
    root.addHandler(stream_handler)
    root.setLevel(default_level)


def set_request_id(request_id: str) -> None:
    """
    Sets the request_id context variable for the current execution context.
    """
    request_id_var.set(request_id)


def get_ip_hash_short(ip: str) -> str:
    """
    Generates a secure, shortened SHA-256 hash prefix for the client IP address.
    Never stores or logs the raw IP address (compliance with PII regulations).
    """
    if not ip:
        return "N/A"
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()[:8]
