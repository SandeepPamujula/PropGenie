import json
import logging

from utils.logger import JSONFormatter, get_ip_hash_short, set_request_id


def test_get_ip_hash_short():
    """Verifies that the IP hashing function is secure, deterministic, and shortened."""
    ip = "192.168.1.100"
    hash_val = get_ip_hash_short(ip)

    assert isinstance(hash_val, str)
    assert len(hash_val) == 8
    # Ensure it's deterministic
    assert get_ip_hash_short(ip) == hash_val
    assert get_ip_hash_short("192.168.1.101") != hash_val

    # Handle empty / null values gracefully
    assert get_ip_hash_short("") == "N/A"
    assert get_ip_hash_short(None) == "N/A"


def test_json_formatter():
    """Verifies that JSONFormatter produces valid JSON log records."""
    formatter = JSONFormatter()

    # Set request ID context
    set_request_id("test-request-id")

    # Create a dummy LogRecord
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Test log message with placeholder: %s",
        args=("value",),
        exc_info=None
    )

    # Format and parse
    log_str = formatter.format(record)
    log_data = json.loads(log_str)

    assert log_data["level"] == "INFO"
    assert log_data["message"] == "Test log message with placeholder: value"
    assert log_data["logger"] == "test_logger"
    assert log_data["request_id"] == "test-request-id"
    assert "timestamp" in log_data


def test_json_formatter_with_extra():
    """Verifies that JSONFormatter merges custom extra fields."""
    formatter = JSONFormatter()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.WARNING,
        pathname="test_file.py",
        lineno=10,
        msg="Warning message",
        args=(),
        exc_info=None
    )
    record.extra_fields = {"extra_key": "extra_value", "metric": 100}

    log_str = formatter.format(record)
    log_data = json.loads(log_str)

    assert log_data["level"] == "WARNING"
    assert log_data["message"] == "Warning message"
    assert log_data["extra_key"] == "extra_value"
    assert log_data["metric"] == 100
