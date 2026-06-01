import hashlib
import logging
import time
from datetime import UTC, datetime
from typing import Any

from db.connection import get_database
from models.state import AgentState

logger = logging.getLogger(__name__)

def log_search(session_id: str, ip: str, state: AgentState) -> None:
    """
    Logs the completed search into the search_logs collection.
    Captures intent, extracted entities, performance metrics, and outcome metadata.
    Fails open (catches and logs errors without raising).
    """
    try:
        # Calculate secure IP hash to avoid storing raw PII
        ip_hash = hashlib.sha256(ip.encode('utf-8')).hexdigest()

        # Calculate latency in ms
        start_time = state.get("start_time") or time.time()
        latency_ms = int((time.time() - start_time) * 1000)

        # Get search meta
        search_meta = state.get("search_meta") or {}

        # Construct the document
        log_doc: dict[str, Any] = {
            "session_id": session_id,
            "ip_hash": ip_hash,

            # Entities
            "intent": state.get("intent"),
            "city": state.get("city"),
            "location_anchor": state.get("location_anchor"),
            "property_type": state.get("property_type"),
            "bhk": state.get("bhk"),
            "budget_min": state.get("budget_min"),
            "budget_max": state.get("budget_max"),
            "radius_km": state.get("radius_km"),

            # Graph Outcomes
            "portals_searched": search_meta.get("portals_searched", 0),
            "portals_returned": search_meta.get("portals_returned", 0),
            "portals_dropped": search_meta.get("portals_dropped", []),
            "clarification_rounds": search_meta.get("clarification_rounds", 0),
            "defaults_applied": search_meta.get("defaults_applied", []),

            # Performance
            "latency_ms": latency_ms,
            "llm_calls": state.get("llm_calls", 0),
            "total_input_tokens": state.get("total_input_tokens", 0),
            "total_output_tokens": state.get("total_output_tokens", 0),

            # Timestamp
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z")
        }

        # Insert into database
        db = get_database()
        db.search_logs.insert_one(log_doc)

    except Exception as e:
        logger.error(f"Failed to log search analytics for session {session_id}. Error: {e}")
