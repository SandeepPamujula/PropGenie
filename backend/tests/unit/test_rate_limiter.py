import pytest
from unittest.mock import patch
from db.connection import get_database
from utils.rate_limiter import (
    check_rate_limit,
    RateLimitExceededException,
    get_today_ist_string,
    get_next_ist_midnight_string
)

def test_rate_limit_allowed(auto_mock_db_client):
    """Test that IP with < 10 searches is allowed."""
    db = get_database()
    today_ist = get_today_ist_string()
    
    # Insert 9 searches for IP
    db.rate_limits.insert_one({"ip": "127.0.0.1", "date": today_ist, "count": 9})
    
    # Should not raise exception
    check_rate_limit("127.0.0.1")

def test_rate_limit_exceeded(auto_mock_db_client):
    """Test that IP with 10+ searches raises RateLimitExceededException."""
    db = get_database()
    today_ist = get_today_ist_string()
    
    # Insert 10 searches for IP
    db.rate_limits.insert_one({"ip": "127.0.0.1", "date": today_ist, "count": 10})
    
    with pytest.raises(RateLimitExceededException):
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
