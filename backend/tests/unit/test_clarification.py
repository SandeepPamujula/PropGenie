from unittest.mock import MagicMock, patch

from agents.clarification import clarification_node
from models.state import get_initial_state


@patch("agents.clarification.ChatBedrock")
def test_clarification_one_question_per_turn(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that the clarification agent invokes the LLM and appends exactly one question
    to the state messages list under normal round execution.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = "Since you're looking to rent in Bangalore, what is your budget range?"
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    # Set up initial state with round = 1, and missing budget
    state = get_initial_state("session-clarify-one", "127.0.0.1")
    state["intent"] = "Rent"
    state["city"] = "Bangalore"
    state["pending_fields"] = ["budget"]
    state["clarification_round"] = 1
    state["messages"].append({
        "role": "user",
        "content": "looking to rent in bangalore"
    })

    original_message_count = len(state["messages"])
    updates = clarification_node(state)

    # Check updates
    assert updates["proceed_with_defaults"] is False
    assert len(updates["messages"]) == original_message_count + 1
    assert updates["messages"][-1]["role"] == "assistant"
    assert updates["messages"][-1]["content"] == "Since you're looking to rent in Bangalore, what is your budget range?"


@patch("agents.clarification.ChatBedrock")
def test_clarification_prioritized_question(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that the prompt design successfully prioritizes the fields.
    In the prompt, intent has the highest priority. If intent is missing, the system asks about intent.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = "Are you looking to buy or rent a property in Bangalore?"
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    state = get_initial_state("session-clarify-prioritized", "127.0.0.1")
    state["city"] = "Bangalore"
    state["pending_fields"] = ["intent", "budget"]
    state["clarification_round"] = 1

    updates = clarification_node(state)

    assert updates["proceed_with_defaults"] is False
    assert updates["messages"][-1]["content"] == "Are you looking to buy or rent a property in Bangalore?"


def test_clarification_three_round_breach() -> None:
    """
    Verifies that after 3 clarification rounds (round >= 3), the clarification agent:
    1. Returns with proceed_with_defaults: True
    2. Populates defaults (budget_min=0, budget_max=None, radius_km=4)
    3. Adds a user-facing explanation note
    4. Clears pending_fields
    """
    state = get_initial_state("session-clarify-breach", "127.0.0.1")
    state["intent"] = "Rent"
    state["city"] = "Bangalore"
    state["pending_fields"] = ["budget", "radius_km", "bhk"]
    state["clarification_round"] = 3
    state["messages"].append({
        "role": "user",
        "content": "looking to rent in bangalore"
    })

    original_message_count = len(state["messages"])
    updates = clarification_node(state)

    # Check breach state returns
    assert updates["proceed_with_defaults"] is True
    assert updates["budget_min"] == 0
    assert updates["budget_max"] is None
    assert updates["radius_km"] == 4
    assert updates["bhk"] is None
    assert updates["pending_fields"] == []

    # Check that user-facing note was added
    assert len(updates["messages"]) == original_message_count + 1
    assert updates["messages"][-1]["role"] == "assistant"
    assert "default options" in updates["messages"][-1]["content"]
    assert "unlimited budget" in updates["messages"][-1]["content"]
    assert "4 km search radius" in updates["messages"][-1]["content"]


@patch("agents.clarification.ChatBedrock")
def test_clarification_error_fallback(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that if ChatBedrock client throws an exception, clarification_node catches it gracefully,
    appends a generic/fallback question to messages, and sets the error field.
    """
    mock_instance = MagicMock()
    mock_instance.invoke.side_effect = Exception("Bedrock API is down")
    mock_chat_bedrock.return_value = mock_instance

    state = get_initial_state("session-clarify-err", "127.0.0.1")
    state["pending_fields"] = ["intent"]
    state["clarification_round"] = 1

    updates = clarification_node(state)

    assert "error" in updates
    assert "Clarification LLM invocation failed" in updates["error"]
    assert updates["messages"][-1]["role"] == "assistant"
    assert "Could you please provide more details" in updates["messages"][-1]["content"]
