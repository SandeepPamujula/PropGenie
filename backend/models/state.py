from typing import Any, Optional, TypedDict


class AgentState(TypedDict):
    """
    Defines the shared state schema for the PropGenie LangGraph agent pipeline.
    This typed dictionary ensures strict type compliance and structural integrity
    across all nodes in the agent graph.
    """

    session_id: str
    ip: str
    intent: Optional[str]
    city: Optional[str]
    location_anchor: Optional[str]
    property_type: Optional[str]
    bhk: Optional[int]
    budget_min: Optional[int]
    budget_max: Optional[int]
    radius_km: Optional[int]
    clarification_round: int
    pending_fields: list[str]
    messages: list[dict[str, Any]]
    generated_urls: list[str]
    validated_urls: list[dict[str, Any]]
    search_meta: Optional[dict[str, Any]]
    error: Optional[str]
    proceed_with_defaults: Optional[bool]
    search_completed: Optional[bool]
    start_time: Optional[float]
    llm_calls: int
    total_input_tokens: int
    total_output_tokens: int
    trace: Optional[Any]


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
