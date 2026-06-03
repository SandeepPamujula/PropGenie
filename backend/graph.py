import json
import logging
import os
from collections.abc import Generator
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger(__name__)

from langgraph.graph import END, StateGraph

from agents.clarification import clarification_node
from agents.orchestrator import orchestrator_node
from agents.property_scraper import property_scraper_node
from agents.query_builder import query_builder_node
from agents.response_formatter import response_formatter_node
from agents.url_validator import url_validator_node
from db.search_logger import log_search
from db.session_manager import create_session, get_session, update_session
from models.state import AgentState, get_initial_state
from observability.langfuse_tracer import create_trace, flush_traces, update_trace_metadata
from utils.constants import RateLimitConfig
from utils.rate_limiter import increment_rate_limit


def restore_state(state: AgentState) -> dict[str, Any]:
    """
    Graph node that restores/initializes session state from MongoDB.
    """
    import time
    print("[Graph Node] restore_state executed")
    session_id = state.get("session_id", "")
    if not session_id:
        return {"session_id": "", "trace": state.get("trace")}

    session = get_session(session_id)
    if session:
        # Restore state fields from the stored MongoDB document
        context = session.get("context", {})
        graph_state = session.get("graph_state", {})

        # Merge messages: append incoming message(s) if not already present
        stored_messages = list(session.get("messages", []))
        incoming_messages = state.get("messages", [])

        for msg in incoming_messages:
            # Check if this exact message is already in stored_messages to avoid duplicates
            if not any(
                m.get("content") == msg.get("content") and m.get("ts") == msg.get("ts")
                for m in stored_messages
            ):
                stored_messages.append(msg)

        return {
            "intent": context.get("intent"),
            "city": context.get("city"),
            "location_anchor": context.get("location_anchor"),
            "property_type": context.get("property_type"),
            "bhk": context.get("bhk"),
            "budget_min": context.get("budget_min"),
            "budget_max": context.get("budget_max"),
            "radius_km": context.get("radius_km"),
            "clarification_round": session.get("clarification_round", 0),
            "pending_fields": graph_state.get("pending_fields", []),
            "messages": stored_messages,
            "generated_urls": graph_state.get("generated_urls", []),
            "validated_urls": graph_state.get("validated_urls", []),
            "scraped_property_urls": graph_state.get("scraped_property_urls", []),
            "validated_property_urls": graph_state.get("validated_property_urls", []),
            "search_meta": graph_state.get("search_meta"),
            "error": graph_state.get("error"),
            "proceed_with_defaults": graph_state.get("proceed_with_defaults"),
            "start_time": graph_state.get("start_time") or time.time(),
            "llm_calls": graph_state.get("llm_calls", 0),
            "total_input_tokens": graph_state.get("total_input_tokens", 0),
            "total_output_tokens": graph_state.get("total_output_tokens", 0),
            "trace": state.get("trace"),
        }
    else:
        # Create session if it does not exist
        ip = state.get("ip", "")
        create_session(session_id, ip)
        state_update = {"session_id": session_id, "start_time": time.time(), "trace": state.get("trace")}
        update_session(session_id, state)
        return state_update


def save_state(state: AgentState) -> dict[str, Any]:
    """
    Graph node that saves/persists session state to MongoDB.
    """
    print("[Graph Node] save_state executed")
    session_id = state.get("session_id", "")

    # Check if a search was just completed and increment the rate limit
    if state.get("search_completed"):
        ip = state.get("ip", "")
        if ip:
            increment_rate_limit(ip)

        # Log custom Search completed marker
        logger.info(f"[SEARCH_COMPLETED] Search completed successfully for session {session_id}.")

        # Log the search analytics
        log_search(session_id, ip, state)

    if session_id:
        update_session(session_id, state)

    # Update Langfuse trace metadata with final stats
    trace = state.get("trace")
    if trace:
        generated = state.get("generated_urls", [])
        validated = state.get("validated_urls", [])

        # A hallucination is detected if we generated URLs but all/some failed validation/liveness
        # and got dropped.
        hallucination_detected = len(generated) > len(validated)

        metadata = {
            "clarification_rounds": state.get("clarification_round", 0),
            "hallucination_detected": hallucination_detected,
        }
        tags = ["propgenie"]
        if hallucination_detected:
            tags.append("hallucination_detected")

        update_trace_metadata(trace, metadata=metadata, tags=tags)
        flush_traces()

    return {"session_id": session_id}




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
    workflow.add_node("property_scraper", property_scraper_node)
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

    # Linear pipeline from query_builder to property_scraper to response_formatter to save_state
    workflow.add_edge("query_builder", "url_validator")
    workflow.add_edge("url_validator", "property_scraper")
    workflow.add_edge("property_scraper", "response_formatter")
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
        'timestamp': datetime.now(UTC).isoformat().replace("+00:00", "Z")
    })}\n\n"

    # 2. Compile graph and run
    compiled_graph = create_graph()
    state = get_initial_state(session_id, ip)

    # Initialize Langfuse trace
    trace = create_trace(session_id, ip)
    state["trace"] = trace

    # Add user message to state
    state["messages"].append(
        {
            "role": "user",
            "content": message,
            "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        }
    )

    try:
        # Keep track of state during execution to yield at the end
        final_state = state

        for event in compiled_graph.stream(state):
            for node_name, state_update in event.items():
                final_state = {**final_state, **state_update}

                # Yield status for each active node
                timestamp = datetime.now(UTC).isoformat().replace("+00:00", "Z")
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
                elif node_name == "property_scraper":
                    yield f"event: agent_status\ndata: {json.dumps({
                        'type': 'agent_status',
                        'agent': 'property_scraper',
                        'message': 'Fetching top property listings...',
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

            validated_props = final_state.get("validated_property_urls", []) or []
            enable_scraping = os.environ.get("ENABLE_PROPERTY_SCRAPING", "false").lower() == "true"
            property_links_count = len(validated_props) if enable_scraping else 0

            search_meta = {
                'type': 'search_meta',
                'portals_searched': len(generated),
                'portals_returned': len(validated),
                'portals_dropped': dropped,
                'property_links_count': property_links_count,
                'clarification_rounds': final_state.get('clarification_round', 0),
                'defaults_applied': defaults
            }

        yield f"event: search_meta\ndata: {json.dumps(search_meta)}\n\n"

        # Get actual search count from database dynamically
        search_count = 1
        try:
            from db.connection import get_database
            from utils.rate_limiter import get_today_ist_string
            db = get_database()
            today_ist = get_today_ist_string()
            rate_limit_doc = db.rate_limits.find_one({"ip": ip, "date": today_ist})
            if rate_limit_doc:
                search_count = rate_limit_doc.get("count", 1)
        except Exception:
            pass

        yield f"event: done\ndata: {json.dumps({
            'type': 'done',
            'session_id': session_id,
            'search_count_today': search_count,
            'search_limit': RateLimitConfig.MAX_DAILY_SEARCHES
        })}\n\n"

    except Exception as e:
        yield f"event: error\ndata: {json.dumps({
            'type': 'error',
            'message': f'An execution error occurred: {str(e)}',
            'retryable': True
        })}\n\n"
    finally:
        flush_traces()
