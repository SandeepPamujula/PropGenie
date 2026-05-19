import json
from datetime import datetime, timezone
from typing import Any, Generator

from agents.clarification import clarification_node
from agents.orchestrator import orchestrator_node
from agents.query_builder import query_builder_node
from agents.response_formatter import response_formatter_node
from agents.url_validator import url_validator_node
from langgraph.graph import END, StateGraph
from models.state import AgentState, get_initial_state


def restore_state(state: AgentState) -> dict[str, Any]:
    """
    Graph node that restores/initializes session state.
    In US-12, this will load from MongoDB.
    """
    print("[Graph Node] restore_state executed")
    return {"session_id": state.get("session_id", "")}


def save_state(state: AgentState) -> dict[str, Any]:
    """
    Graph node that saves/persists session state.
    In US-12, this will save to MongoDB.
    """
    print("[Graph Node] save_state executed")
    return {"session_id": state.get("session_id", "")}


def route_orchestrator(state: AgentState) -> str:
    """
    Conditional routing function for orchestrator node.
    Routes to 'clarification' if there are pending fields,
    otherwise routes to 'query_builder'.
    """
    pending = state.get("pending_fields", [])
    round_count = state.get("clarification_round", 0)
    if pending and round_count < 3:
        print(
            f"[Routing] Orchestrator -> Clarification (pending: {pending}, round: {round_count})"
        )
        return "clarification"

    if round_count >= 3:
        print(
            f"[Routing] Orchestrator -> QueryBuilder due to 3-round breach (round: {round_count})"
        )
    else:
        print("[Routing] Orchestrator -> QueryBuilder (all resolved)")
    return "query_builder"


def create_graph() -> Any:
    """
    Initializes and compiles the LangGraph state machine.
    """
    # Create the state graph with our AgentState schema
    workflow = StateGraph(AgentState)

    # Register all nodes
    workflow.add_node("restore_state", restore_state)
    workflow.add_node("orchestrator", orchestrator_node)
    workflow.add_node("clarification", clarification_node)
    workflow.add_node("query_builder", query_builder_node)
    workflow.add_node("url_validator", url_validator_node)
    workflow.add_node("response_formatter", response_formatter_node)
    workflow.add_node("save_state", save_state)

    # Define edges
    # Entry point
    workflow.set_entry_point("restore_state")

    # Linear edge to orchestrator
    workflow.add_edge("restore_state", "orchestrator")

    # Conditional edge from orchestrator
    workflow.add_conditional_edges(
        "orchestrator",
        route_orchestrator,
        {
            "clarification": "clarification",
            "query_builder": "query_builder",
        },
    )

    # Linear edge from clarification to save_state
    workflow.add_edge("clarification", "save_state")

    # Linear pipeline from query_builder to response_formatter to save_state
    workflow.add_edge("query_builder", "url_validator")
    workflow.add_edge("url_validator", "response_formatter")
    workflow.add_edge("response_formatter", "save_state")

    # Terminal edge from save_state to the end of execution
    workflow.add_edge("save_state", END)

    # Compile the graph into a runnable component
    return workflow.compile()


def generate_graph_sse(
    session_id: str, ip: str, message: str
) -> Generator[str, None, None]:
    """
    Shared utility that executes the compiled LangGraph and generates a stream of
    Server-Sent Events (SSE) formatted strings. Adheres to the DRY principle.
    """
    # 1. Yield initial status
    yield f"event: agent_status\ndata: {json.dumps({
        'type': 'agent_status',
        'agent': 'orchestrator',
        'message': 'Understanding your search...',
        'timestamp': datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    })}\n\n"

    # 2. Compile graph and run
    compiled_graph = create_graph()
    state = get_initial_state(session_id, ip)

    # Add user message to state
    state["messages"].append(
        {
            "role": "user",
            "content": message,
            "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    )

    try:
        # Keep track of state during execution to yield at the end
        final_state = state

        for event in compiled_graph.stream(state):
            for node_name, state_update in event.items():
                final_state = {**final_state, **state_update}

                # Yield status for each active node
                timestamp = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                if node_name == "orchestrator":
                    yield f"event: agent_status\ndata: {json.dumps({
                        'type': 'agent_status',
                        'agent': 'orchestrator',
                        'message': 'Classifying query intent and extracting fields...',
                        'timestamp': timestamp
                    })}\n\n"
                elif node_name == "clarification":
                    yield f"event: agent_status\ndata: {json.dumps({
                        'type': 'agent_status',
                        'agent': 'clarification',
                        'message': 'Generating clarification question...',
                        'timestamp': timestamp
                    })}\n\n"

                    # Yield clarification event
                    clarifying_msg = (
                        "Could you please specify your budget and BHK requirements?"
                    )
                    if final_state.get("messages"):
                        last_msg = final_state["messages"][-1]
                        if last_msg.get("role") == "assistant":
                            clarifying_msg = last_msg.get(
                                "content", clarifying_msg
                            )

                    resolved = {}
                    state_dict = dict(final_state)
                    for k in [
                        "intent",
                        "city",
                        "location_anchor",
                        "property_type",
                        "bhk",
                        "budget_min",
                        "budget_max",
                        "radius_km",
                    ]:
                        if state_dict.get(k) is not None:
                            resolved[k] = state_dict[k]

                    yield f"event: clarification\ndata: {json.dumps({
                        'type': 'clarification',
                        'message': clarifying_msg,
                        'round': final_state.get('clarification_round', 1),
                        'max_rounds': 3,
                        'resolved_fields': resolved,
                        'missing_fields': final_state.get('pending_fields', [])
                    })}\n\n"
                elif node_name == "query_builder":
                    yield f"event: agent_status\ndata: {json.dumps({
                        'type': 'agent_status',
                        'agent': 'query_builder',
                        'message': 'Building portal search queries...',
                        'timestamp': timestamp
                    })}\n\n"
                elif node_name == "url_validator":
                    yield f"event: agent_status\ndata: {json.dumps({
                        'type': 'agent_status',
                        'agent': 'url_validator',
                        'message': 'Validating search URLs...',
                        'timestamp': timestamp
                    })}\n\n"
                elif node_name == "response_formatter":
                    yield f"event: agent_status\ndata: {json.dumps({
                        'type': 'agent_status',
                        'agent': 'response_formatter',
                        'message': 'Formatting search results...',
                        'timestamp': timestamp
                    })}\n\n"

                    # Yield portal cards
                    validated_urls = final_state.get("validated_urls", [])
                    for card in validated_urls:
                        yield f"event: portal_card\ndata: {json.dumps(card)}\n\n"

        # After stream finishes, yield search_meta and done events
        generated = final_state.get("generated_urls", [])
        validated = final_state.get("validated_urls", [])
        dropped = [
            url
            for url in generated
            if url not in [v.get("url") for v in validated]
        ]

        search_meta = final_state.get("search_meta")
        if not search_meta:
            defaults = []
            if final_state.get("radius_km") == 4:
                defaults.append("radius_km: 4")
            if final_state.get("budget_min") == 0:
                defaults.append("budget_min: 0")
            search_meta = {
                'type': 'search_meta',
                'portals_searched': len(generated),
                'portals_returned': len(validated),
                'portals_dropped': dropped,
                'clarification_rounds': final_state.get('clarification_round', 0),
                'defaults_applied': defaults
            }
        
        yield f"event: search_meta\ndata: {json.dumps(search_meta)}\n\n"

        yield f"event: done\ndata: {json.dumps({
            'type': 'done',
            'session_id': session_id,
            'search_count_today': 1,
            'search_limit': 10
        })}\n\n"

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({
            'type': 'error',
            'message': f'An execution error occurred: {str(e)}',
            'retryable': True
        })}\n\n"
