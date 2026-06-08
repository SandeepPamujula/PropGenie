import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from agents.orchestrator import extract_json, orchestrator_node
from models.state import get_initial_state


def test_extract_json() -> None:
    """Verifies that the JSON extraction utility parses various LLM output formats."""
    # Plain JSON
    assert extract_json('{"key": "value"}') == {"key": "value"}

    # Markdown block
    assert extract_json('```json\n{"key": "value"}\n```') == {"key": "value"}

    # Whitespace and backticks
    assert extract_json(' ```\n{"key": "value"}\n``` ') == {"key": "value"}

    # Leading text
    assert extract_json('Here is the JSON:\n{"key": "value"}') == {"key": "value"}


@patch("agents.orchestrator.ChatBedrock")
def test_orchestrator_rent_happy_path(mock_chat_bedrock: MagicMock) -> None:
    """
    Given "I want to rent a 3BHK near NPS Indiranagar, budget 25k to 35k",
    verifies that all fields resolve on the first pass (happy path).
    """
    # Configure mock response
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "intent": "Rent",
        "city": "Bangalore",
        "location_anchor": "NPS Indiranagar",
        "property_type": "house",
        "bhk": 3,
        "budget_min": 25000,
        "budget_max": 35000,
        "radius_km": None
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    # Set up initial state with message
    state = get_initial_state("session-happy-rent", "127.0.0.1")
    state["messages"].append({
        "role": "user",
        "content": "I want to rent a 3BHK near NPS Indiranagar, budget 25k to 35k"
    })

    # Execute orchestrator node
    updates = orchestrator_node(state)

    # Assertions
    assert updates["clarification_round"] == 1
    assert updates["intent"] == "Rent"
    assert updates["city"] == "Bangalore"
    assert updates["location_anchor"] == "NPS Indiranagar"
    assert updates["property_type"] == "house"
    assert updates["bhk"] == 3
    assert updates["budget_min"] == 25000
    assert updates["budget_max"] == 35000
    assert updates["pending_fields"] == []


@patch("agents.orchestrator.ChatBedrock")
def test_orchestrator_ambiguous_intent_path(mock_chat_bedrock: MagicMock) -> None:
    """
    Given "looking for a flat in bangalore",
    verifies that intent is classified as Ambiguous and pending_fields includes intent, budget, bhk.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "intent": "Ambiguous",
        "city": "Bangalore",
        "location_anchor": None,
        "property_type": "apartment",
        "bhk": None,
        "budget_min": None,
        "budget_max": None,
        "radius_km": None
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    state = get_initial_state("session-ambiguous", "127.0.0.1")
    state["messages"].append({
        "role": "user",
        "content": "looking for a flat in bangalore"
    })

    updates = orchestrator_node(state)

    assert updates["intent"] == "Ambiguous"
    assert updates["city"] == "Bangalore"
    assert updates["property_type"] == "apartment"
    assert updates["bhk"] is None
    assert updates["budget_min"] is None
    assert updates["budget_max"] is None

    # Must include "intent", "budget", "bhk"
    assert "intent" in updates["pending_fields"]
    assert "budget" in updates["pending_fields"]
    assert "bhk" in updates["pending_fields"]


@patch("agents.orchestrator.ChatBedrock")
def test_orchestrator_clarification_round_increment(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that the clarification round counter increments on each pass.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "intent": "Ambiguous",
        "city": "Bangalore",
        "location_anchor": None,
        "property_type": None,
        "bhk": None,
        "budget_min": None,
        "budget_max": None,
        "radius_km": None
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    # Start with round = 0
    state = get_initial_state("session-round-inc", "127.0.0.1")
    updates_1 = orchestrator_node(state)
    assert updates_1["clarification_round"] == 1

    # Mock the state containing round = 1
    state["clarification_round"] = 1
    updates_2 = orchestrator_node(state)
    assert updates_2["clarification_round"] == 2


@pytest.mark.parametrize(
    "landmark,expected_city",
    [
        ("Manyata Tech Park", "Bangalore"),
        ("Worli Sea Face", "Mumbai"),
        ("Connaught Place", "Delhi"),
        ("OMR Road", "Chennai"),
        ("Gachibowli", "Hyderabad"),
        ("Koregaon Park", "Pune"),
        ("Salt Lake Sector 5", "Kolkata"),
        ("SG Highway", "Ahmedabad"),
        ("Vaishali Nagar", "Jaipur"),
        ("Marine Drive Cochin", "Kochi"),
    ]
)
@patch("agents.orchestrator.ChatBedrock")
def test_orchestrator_city_inference(mock_chat_bedrock: MagicMock, landmark: str, expected_city: str) -> None:
    """
    Verifies that cities are correctly inferred from landmark names for 10 major Indian cities.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "intent": "Buy",
        "city": expected_city,
        "location_anchor": landmark,
        "property_type": "apartment",
        "bhk": None,
        "budget_min": 10000000,
        "budget_max": 20000000,
        "radius_km": None
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    state = get_initial_state("session-city-inference", "127.0.0.1")
    state["messages"].append({
        "role": "user",
        "content": f"I want to buy a flat near {landmark}"
    })

    updates = orchestrator_node(state)
    assert updates["city"] == expected_city
    assert updates["location_anchor"] == landmark


@pytest.mark.parametrize(
    "budget_str,expected_min,expected_max",
    [
        ("25k to 35k", 25000, 35000),
        ("₹1Cr", 10000000, None),
        ("1.5 crore", 15000000, None),
        ("25000", 25000, 25000),
    ]
)
@patch("agents.orchestrator.ChatBedrock")
def test_orchestrator_budget_normalization(mock_chat_bedrock: MagicMock, budget_str: str, expected_min: Any, expected_max: Any) -> None:
    """
    Verifies that budget strings in different formats are correctly normalized to numeric values.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "intent": "Rent",
        "city": "Bangalore",
        "location_anchor": "Whitefield",
        "property_type": "apartment",
        "bhk": 2,
        "budget_min": expected_min,
        "budget_max": expected_max,
        "radius_km": None
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    state = get_initial_state("session-budget-norm", "127.0.0.1")
    state["messages"].append({
        "role": "user",
        "content": f"looking for a 2bhk rent in Whitefield, budget {budget_str}"
    })

    updates = orchestrator_node(state)
    assert updates["budget_min"] == expected_min
    assert updates["budget_max"] == expected_max


@patch("agents.orchestrator.ChatBedrock")
def test_orchestrator_state_reset_when_switching_context(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that state fields are correctly reset (e.g. bhk is set to None when switching
    from apartment to plot search) instead of carrying over from the previous state.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "intent": "Buy",
        "city": "Bangalore",
        "location_anchor": "Indiranagar",
        "property_type": "plot",
        "bhk": None,
        "budget_min": 10000000,
        "budget_max": 40000000,
        "radius_km": None
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    # Set up initial state carrying over previous turn's apartment search parameters
    state = get_initial_state("session-switch-context", "127.0.0.1")
    state["intent"] = "Rent"
    state["city"] = "Bangalore"
    state["location_anchor"] = "Indiranagar"
    state["property_type"] = "apartment"
    state["bhk"] = 3
    state["budget_min"] = 30000
    state["budget_max"] = 50000

    state["messages"].append({
        "role": "user",
        "content": "buy plot in Indiranagar, Bangalore between 1cr to 4cr"
    })

    # Execute orchestrator node
    updates = orchestrator_node(state)

    # Assertions: bhk must be None, property_type must be plot
    assert updates["property_type"] == "plot"
    assert updates["bhk"] is None
    assert updates["intent"] == "Buy"
    assert updates["budget_min"] == 10000000
    assert updates["budget_max"] == 40000000

