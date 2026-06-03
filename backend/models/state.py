from typing import Any, TypedDict


class AgentState(TypedDict):
    """
    Defines the shared state schema for the PropGenie LangGraph agent pipeline.
    This typed dictionary ensures strict type compliance and structural integrity
    across all nodes in the agent graph.
    """

    session_id: str
    ip: str
    intent: str | None
    city: str | None
    location_anchor: str | None
    property_type: str | None
    bhk: int | None
    budget_min: int | None
    budget_max: int | None
    radius_km: int | None
    clarification_round: int
    pending_fields: list[str]
    messages: list[dict[str, Any]]
    generated_urls: list[str]
    validated_urls: list[dict[str, Any]]
    scraped_property_urls: list[dict[str, Any]]
    validated_property_urls: list[dict[str, Any]]
    search_meta: dict[str, Any] | None
    error: str | None
    proceed_with_defaults: bool | None
    search_completed: bool | None
    start_time: float | None
    llm_calls: int
    total_input_tokens: int
    total_output_tokens: int
    trace: Any | None


def get_initial_state(session_id: str, ip: str) -> AgentState:
    """
    Constructs and returns the default initial state for a search session.
    """
    return {
        "session_id": session_id,
        "ip": ip,
        "intent": None,
        "city": None,
        "location_anchor": None,
        "property_type": None,
        "bhk": None,
        "budget_min": None,
        "budget_max": None,
        "radius_km": None,
        "clarification_round": 0,
        "pending_fields": [],
        "messages": [],
        "generated_urls": [],
        "validated_urls": [],
        "scraped_property_urls": [],
        "validated_property_urls": [],
        "search_meta": None,
        "error": None,
        "proceed_with_defaults": None,
        "search_completed": None,
        "start_time": None,
        "llm_calls": 0,
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "trace": None,
    }
