import time
from typing import Any

from db.connection import get_database, get_db_client
from db.session_manager import create_session, delete_session, get_session, update_session
from graph import restore_state, save_state
from models.state import get_initial_state


def test_connection_pooling(mock_mongo_client: Any) -> None:
    """
    Verifies that the connection pool utility retrieves the client and database correctly,
    and programmatically configures the indexes.
    """
    client = get_db_client()
    assert client == mock_mongo_client

    db = get_database()
    assert db is not None

    # Check if indexes were created programmatically
    index_info = db.sessions.index_information()
    assert len(index_info) >= 1
    # Check that ip and last_active indexes exist
    assert any("ip" in idx or idx == "ip_1" for idx in index_info)
    assert any("last_active" in idx or idx == "last_active_1" for idx in index_info)


def test_session_lifecycle() -> None:
    """
    Verifies the complete CRUD lifecycle of a session document.
    """
    session_id = "test-crud-session"
    ip = "192.168.1.100"

    # 1. Retrieve non-existent session
    assert get_session(session_id) is None

    # 2. Create session
    doc = create_session(session_id, ip)
    assert doc is not None
    assert doc["_id"] == session_id
    assert doc["ip"] == ip
    assert doc["context"]["intent"] is None
    assert doc["graph_state"]["pending_fields"] == []
    assert doc["graph_state"]["scraped_property_urls"] == []
    assert doc["graph_state"]["validated_property_urls"] == []
    assert doc["clarification_round"] == 0
    assert "last_active" in doc
    assert "created_at" in doc

    # 3. Get session
    retrieved = get_session(session_id)
    assert retrieved is not None
    assert retrieved["_id"] == session_id
    assert retrieved["ip"] == ip

    # Sleep slightly to ensure timestamps differ
    time.sleep(0.005)

    # 4. Update session
    state = get_initial_state(session_id, ip)
    state["intent"] = "Rent"
    state["city"] = "Bangalore"
    state["location_anchor"] = "Indiranagar"
    state["pending_fields"] = ["bhk"]
    state["clarification_round"] = 1
    state["messages"] = [{"role": "user", "content": "hi", "ts": "2026-05-19T18:00:00Z"}]
    state["scraped_property_urls"] = [{"url": "http://nobroker.in/prop1", "portal": "NoBroker"}]
    state["validated_property_urls"] = [{"url": "http://nobroker.in/prop1", "portal": "NoBroker", "rank": 1}]

    updated = update_session(session_id, state)
    assert updated is not None
    assert updated["context"]["intent"] == "Rent"
    assert updated["context"]["city"] == "Bangalore"
    assert updated["context"]["location_anchor"] == "Indiranagar"
    assert updated["graph_state"]["pending_fields"] == ["bhk"]
    assert updated["graph_state"]["scraped_property_urls"] == [{"url": "http://nobroker.in/prop1", "portal": "NoBroker"}]
    assert updated["graph_state"]["validated_property_urls"] == [{"url": "http://nobroker.in/prop1", "portal": "NoBroker", "rank": 1}]
    assert updated["clarification_round"] == 1
    assert len(updated["messages"]) == 1
    assert updated["messages"][0]["content"] == "hi"

    # Verify last_active is updated
    assert updated["last_active"] > doc["last_active"]

    # 5. Delete session
    assert delete_session(session_id) is True
    assert get_session(session_id) is None
    assert delete_session(session_id) is False



def test_restore_state_node_new_session() -> None:
    """
    Verifies that restore_state creates and initializes a new session when it doesn't exist.
    """
    session_id = "new-graph-session"
    ip = "127.0.0.1"

    # Make sure session is not in DB
    delete_session(session_id)

    state = get_initial_state(session_id, ip)
    state["messages"].append({"role": "user", "content": "hello", "ts": "2026-05-19T19:00:00Z"})

    result = restore_state(state)
    assert result.get("session_id") == session_id
    assert "start_time" in result

    # Verify session was created in DB
    stored = get_session(session_id)
    assert stored is not None
    assert stored["ip"] == ip
    assert len(stored["messages"]) == 1
    assert stored["messages"][0]["content"] == "hello"


def test_restore_state_node_existing_session() -> None:
    """
    Verifies that restore_state restores state from MongoDB and correctly merges messages.
    """
    session_id = "existing-graph-session"
    ip = "127.0.0.1"

    # 1. Setup existing session in DB
    existing_state = get_initial_state(session_id, ip)
    existing_state["intent"] = "Rent"
    existing_state["messages"].append({"role": "user", "content": "hi", "ts": "2026-05-19T19:00:00Z"})
    existing_state["scraped_property_urls"] = [{"url": "http://nobroker.in/prop1", "portal": "NoBroker"}]
    existing_state["validated_property_urls"] = [{"url": "http://nobroker.in/prop1", "portal": "NoBroker", "rank": 1}]
    update_session(session_id, existing_state)

    # 2. Incoming state representing a new turn
    incoming_state = get_initial_state(session_id, ip)
    incoming_state["messages"].append({"role": "user", "content": "tell me more", "ts": "2026-05-19T19:05:00Z"})

    restored = restore_state(incoming_state)
    assert restored["intent"] == "Rent"
    assert restored["scraped_property_urls"] == [{"url": "http://nobroker.in/prop1", "portal": "NoBroker"}]
    assert restored["validated_property_urls"] == [{"url": "http://nobroker.in/prop1", "portal": "NoBroker", "rank": 1}]
    assert len(restored["messages"]) == 2
    assert restored["messages"][0]["content"] == "hi"
    assert restored["messages"][1]["content"] == "tell me more"


def test_save_state_node() -> None:
    """
    Verifies that save_state persists changes to the database.
    """
    session_id = "save-node-session"
    ip = "127.0.0.1"

    state = get_initial_state(session_id, ip)
    state["intent"] = "Buy"
    state["city"] = "Mumbai"

    result = save_state(state)
    assert result == {"session_id": session_id}

    stored = get_session(session_id)
    assert stored is not None
    assert stored["context"]["intent"] == "Buy"
    assert stored["context"]["city"] == "Mumbai"
