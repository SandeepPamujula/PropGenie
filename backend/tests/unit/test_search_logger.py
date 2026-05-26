import pytest
import time
from unittest.mock import patch
from db.connection import get_database
from db.search_logger import log_search
import hashlib

def test_log_search_creates_document(auto_mock_db_client):
    """Test that log_search correctly constructs and inserts the document."""
    db = get_database()
    
    state = {
        "intent": "Rent",
        "city": "Bangalore",
        "budget_max": 25000,
        "search_meta": {
            "portals_searched": 2,
            "clarification_rounds": 1
        },
        "llm_calls": 2,
        "total_input_tokens": 1500,
        "total_output_tokens": 120,
        "start_time": time.time() - 2.5 # 2.5 seconds ago
    }
    
    ip = "192.168.1.5"
    session_id = "test-session-123"
    
    # Run the logger
    log_search(session_id, ip, state)
    
    # Verify insertion
    doc = db.search_logs.find_one({"session_id": "test-session-123"})
    assert doc is not None
    
    # Verify IP hash (raw IP should not be stored)
    assert "ip" not in doc
    expected_hash = hashlib.sha256(ip.encode('utf-8')).hexdigest()
    assert doc["ip_hash"] == expected_hash
    
    # Verify extracted entities
    assert doc["intent"] == "Rent"
    assert doc["city"] == "Bangalore"
    assert doc["budget_max"] == 25000
    
    # Verify metadata
    assert doc["portals_searched"] == 2
    assert doc["clarification_rounds"] == 1
    
    # Verify performance
    assert doc["llm_calls"] == 2
    assert doc["total_input_tokens"] == 1500
    assert doc["total_output_tokens"] == 120
    assert doc["latency_ms"] >= 2500
    assert "timestamp" in doc

@patch('db.search_logger.get_database')
def test_log_search_fails_open(mock_get_db):
    """Test that database errors during logging do not crash the agent."""
    mock_get_db.side_effect = Exception("Simulated MongoDB failure")
    
    # Should not raise exception
    log_search("test-session", "127.0.0.1", {})
