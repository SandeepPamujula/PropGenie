from typing import Any

from graph import create_graph
from models.state import get_initial_state


def test_graph_happy_path() -> None:
    """
    Verifies that the graph routes to the query builder pipeline when
    there are no pending fields (Happy Path).
    """
    graph = create_graph()
    initial_state = get_initial_state("session-happy", "127.0.0.1")
    initial_state["pending_fields"] = []

    # Stream execution to track nodes executed
    events = list(graph.stream(initial_state))
    nodes_executed = [list(event.keys())[0] for event in events]

    assert "restore_state" in nodes_executed
    assert "orchestrator" in nodes_executed
    assert "query_builder" in nodes_executed
    assert "url_validator" in nodes_executed
    assert "property_scraper" in nodes_executed
    assert "response_formatter" in nodes_executed
    assert "save_state" in nodes_executed
    assert "clarification" not in nodes_executed

    # Verify linear sequence: restore_state -> orchestrator -> query_builder -> url_validator -> property_scraper -> response_formatter -> save_state
    expected_order = [
        "restore_state",
        "orchestrator",
        "query_builder",
        "url_validator",
        "property_scraper",
        "response_formatter",
        "save_state",
    ]
    # Filter actual nodes to just those in expected_order to check their sequence
    sequence = [n for n in nodes_executed if n in expected_order]
    assert sequence == expected_order


def test_graph_clarification_path() -> None:
    """
    Verifies that the graph routes to clarification when there are pending fields
    and the clarification round is less than 3.
    """
    graph = create_graph()
    initial_state = get_initial_state("session-clarify", "127.0.0.1")
    initial_state["pending_fields"] = ["intent", "budget"]
    initial_state["clarification_round"] = 1

    events = list(graph.stream(initial_state))
    nodes_executed = [list(event.keys())[0] for event in events]

    assert "restore_state" in nodes_executed
    assert "orchestrator" in nodes_executed
    assert "clarification" in nodes_executed
    assert "save_state" in nodes_executed
    assert "query_builder" not in nodes_executed

    expected_order = ["restore_state", "orchestrator", "clarification", "save_state"]
    sequence = [n for n in nodes_executed if n in expected_order]
    assert sequence == expected_order


def test_graph_three_round_breach_path() -> None:
    """
    Verifies that the graph bypasses clarification and routes to the query builder
    pipeline if the clarification round reaches or exceeds 3, even if there are
    pending fields (3-round breach logic).
    """
    graph = create_graph()
    initial_state = get_initial_state("session-breach", "127.0.0.1")
    initial_state["pending_fields"] = ["bhk"]
    initial_state["clarification_round"] = 3

    events = list(graph.stream(initial_state))
    nodes_executed = [list(event.keys())[0] for event in events]

    assert "restore_state" in nodes_executed
    assert "orchestrator" in nodes_executed
    assert "query_builder" in nodes_executed
    assert "url_validator" in nodes_executed
    assert "property_scraper" in nodes_executed
    assert "response_formatter" in nodes_executed
    assert "save_state" in nodes_executed
    assert "clarification" not in nodes_executed

    expected_order = [
        "restore_state",
        "orchestrator",
        "query_builder",
        "url_validator",
        "property_scraper",
        "response_formatter",
        "save_state",
    ]
    sequence = [n for n in nodes_executed if n in expected_order]
    assert sequence == expected_order
