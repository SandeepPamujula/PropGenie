from unittest.mock import patch

import pytest

from db.connection import get_database
from utils.constants import RateLimitConfig
from utils.rate_limiter import RateLimitException, check_rate_limit, get_next_ist_midnight_string, get_today_ist_string


def test_clean_ip():
    """Test that clean_ip correctly extracts IPs and strips ports/brackets."""
    from utils.rate_limiter import clean_ip

    # Standard IPv4
    assert clean_ip("192.168.1.1") == "192.168.1.1"
    # IPv4 with port
    assert clean_ip("192.168.1.1:54321") == "192.168.1.1"

    # Standard IPv6
    assert clean_ip("2001:db8::1") == "2001:db8::1"
    # IPv6 with brackets and port
    assert clean_ip("[2001:db8::1]:12345") == "2001:db8::1"

    # CloudFront IPv6 with port (no brackets)
    assert clean_ip("2001:db8:85a3:8d3:1319:8a2e:370:7348:54321") == "2001:db8:85a3:8d3:1319:8a2e:370:7348"

    # Empty / None
    assert clean_ip("") == "127.0.0.1"
    assert clean_ip(None) == "127.0.0.1"

def test_rate_limit_allowed(auto_mock_db_client):
    """Test that IP with < RateLimitConfig.MAX_DAILY_SEARCHES searches is allowed."""
    db = get_database()
    today_ist = get_today_ist_string()

    # Insert MAX - 1 searches for IP
    db.rate_limits.insert_one({"ip": "127.0.0.1", "date": today_ist, "count": RateLimitConfig.MAX_DAILY_SEARCHES - 1})

    # Should not raise exception
    check_rate_limit("127.0.0.1")

def test_rate_limit_exceeded(auto_mock_db_client):
    """Test that IP with MAX+ searches raises RateLimitException."""
    db = get_database()
    today_ist = get_today_ist_string()

    # Insert MAX searches for IP
    db.rate_limits.insert_one({"ip": "127.0.0.1", "date": today_ist, "count": RateLimitConfig.MAX_DAILY_SEARCHES})

    with pytest.raises(RateLimitException):
        check_rate_limit("127.0.0.1")

@patch('utils.rate_limiter.get_database')
def test_rate_limit_fail_open(mock_get_db, auto_mock_db_client):
    """Test that MongoDB connection failure allows request (fail-open)."""
    # Make get_database raise an exception
    mock_get_db.side_effect = Exception("Mock DB Connection Error")

    # Should not raise exception
    check_rate_limit("127.0.0.1")

def test_ist_date_calculation():
    """Test IST date calculations."""
    today = get_today_ist_string()
    reset_at = get_next_ist_midnight_string()

    assert isinstance(today, str)
    assert len(today) == 10  # YYYY-MM-DD

    assert isinstance(reset_at, str)
    assert "T00:00:00" in reset_at

def test_increment_rate_limit(auto_mock_db_client):
    """Test that increment_rate_limit correctly upserts and increments the count."""
    db = get_database()
    from utils.rate_limiter import increment_rate_limit

    # First increment
    increment_rate_limit("10.0.0.1")
    doc = db.rate_limits.find_one({"ip": "10.0.0.1"})
    assert doc is not None
    assert doc["count"] == 1
    assert "expires_at" in doc

    # Second increment
    increment_rate_limit("10.0.0.1")
    doc = db.rate_limits.find_one({"ip": "10.0.0.1"})
    assert doc["count"] == 2

def test_save_state_increments_only_on_completion(auto_mock_db_client):
    """Test that save_state only increments rate limit when search_completed is True."""
    from graph import save_state
    db = get_database()

    # State with search_completed = False
    state1 = {
        "session_id": "test-session-1",
        "ip": "192.168.1.1",
        "search_completed": False
    }
    save_state(state1)

    doc1 = db.rate_limits.find_one({"ip": "192.168.1.1"})
    assert doc1 is None  # Should not have incremented

    # State with search_completed = True
    state2 = {
        "session_id": "test-session-2",
        "ip": "192.168.1.1",
        "search_completed": True
    }
    save_state(state2)

    doc2 = db.rate_limits.find_one({"ip": "192.168.1.1"})
    assert doc2 is not None
    assert doc2["count"] == 1
