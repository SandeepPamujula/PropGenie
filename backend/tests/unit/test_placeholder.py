from typing import Any

from agents.clarification import clarification_node
from agents.orchestrator import orchestrator_node
from agents.query_builder import query_builder_node
from agents.response_formatter import response_formatter_node
from agents.url_validator import url_validator_node


def test_placeholder_agents() -> None:
    """Verifies that all agent stubs are importable and return state correctly."""
    state = {"query": "hello"}
    assert clarification_node(state) == state
    assert query_builder_node(state) == state
    assert url_validator_node(state) == state
    assert response_formatter_node(state) == state


def test_mongo_fixture(mock_mongo_client: Any) -> None:
    """Verifies that the mock MongoDB client fixture is working."""
    db = mock_mongo_client.get_database("test_db")
    collection = db.get_collection("test_col")
    collection.insert_one({"test_key": "test_val"})
    doc = collection.find_one({"test_key": "test_val"})
    assert doc is not None
    assert doc["test_key"] == "test_val"


def test_bedrock_fixture(mock_bedrock_client: Any) -> None:
    """Verifies that the mock Bedrock client fixture returns mocked values."""
    response = mock_bedrock_client.invoke_model(modelId="amazon.titan-text-express-v1", body=b"{}")
    assert response is not None
    body_data = response["body"].read().decode("utf-8")
    assert "Mocked LLM Response" in body_data
