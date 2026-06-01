from datetime import UTC, datetime
from typing import Any, cast

from db.connection import get_database


def create_session(session_id: str, ip: str) -> dict[str, Any]:
    """
    Initializes a new session document in MongoDB and returns it.
    """
    db = get_database()
    now = datetime.now(UTC)
    doc = {
        "_id": session_id,
        "ip": ip,
        "context": {
            "intent": None,
            "city": None,
            "location_anchor": None,
            "property_type": None,
            "bhk": None,
            "budget_min": None,
            "budget_max": None,
            "radius_km": None,
        },
        "graph_state": {
            "pending_fields": [],
            "generated_urls": [],
            "validated_urls": [],
            "scraped_property_urls": [],
            "validated_property_urls": [],
            "search_meta": None,
            "error": None,
            "proceed_with_defaults": None,
        },
        "clarification_round": 0,
        "messages": [],
        "last_active": now,
        "created_at": now,
    }
    # Use upsert to avoid duplicate errors on concurrent requests or re-runs
    db.sessions.update_one({"_id": session_id}, {"$setOnInsert": doc}, upsert=True)

    # Fetch the document to ensure we return it
    ret = db.sessions.find_one({"_id": session_id})
    return cast(dict[str, Any], ret if ret is not None else doc)


def get_session(session_id: str) -> dict[str, Any] | None:
    """
    Retrieves the existing session document by session_id, or returns None.
    """
    db = get_database()
    return cast(dict[str, Any] | None, db.sessions.find_one({"_id": session_id}))


def update_session(session_id: str, state: Any) -> dict[str, Any]:
    """
    Upserts the database document using fields from the AgentState.
    """
    db = get_database()
    now = datetime.now(UTC)

    # Prepare context and graph state dictionaries
    context = {
        "intent": state.get("intent"),
        "city": state.get("city"),
        "location_anchor": state.get("location_anchor"),
        "property_type": state.get("property_type"),
        "bhk": state.get("bhk"),
        "budget_min": state.get("budget_min"),
        "budget_max": state.get("budget_max"),
        "radius_km": state.get("radius_km"),
    }

    graph_state = {
        "pending_fields": state.get("pending_fields", []),
        "generated_urls": state.get("generated_urls", []),
        "validated_urls": state.get("validated_urls", []),
        "scraped_property_urls": state.get("scraped_property_urls", []),
        "validated_property_urls": state.get("validated_property_urls", []),
        "search_meta": state.get("search_meta"),
        "error": state.get("error"),
        "proceed_with_defaults": state.get("proceed_with_defaults"),
    }

    update_doc = {
        "$set": {
            "ip": state.get("ip"),
            "context": context,
            "graph_state": graph_state,
            "clarification_round": state.get("clarification_round", 0),
            "messages": state.get("messages", []),
            "last_active": now,
        },
        "$setOnInsert": {
            "created_at": now,
        },
    }

    db.sessions.update_one({"_id": session_id}, update_doc, upsert=True)

    ret = db.sessions.find_one({"_id": session_id})
    if ret is None:
        # Fallback if find fails for some reason
        return {
            "_id": session_id,
            "ip": state.get("ip"),
            "context": context,
            "graph_state": graph_state,
            "clarification_round": state.get("clarification_round", 0),
            "messages": state.get("messages", []),
            "last_active": now,
            "created_at": now,
        }
    return cast(dict[str, Any], ret)


def delete_session(session_id: str) -> bool:
    """
    Deletes the session document by session_id. Returns True if deleted, False otherwise.
    """
    db = get_database()
    res = db.sessions.delete_one({"_id": session_id})
    return cast(bool, res.deleted_count > 0)

