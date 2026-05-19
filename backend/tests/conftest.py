import os
from typing import Any
from unittest.mock import MagicMock

import mongomock
import pytest


@pytest.fixture(autouse=True)
def aws_credentials() -> None:
    """Mocked AWS Credentials for testing."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-test"
    os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-test"
    os.environ["LANGFUSE_HOST"] = "http://localhost:3000"


@pytest.fixture
def mock_mongo_client() -> Any:
    """
    Returns a mocked MongoDB client for unit testing database operations.
    Uses mongomock to simulate MongoDB behavior in-memory.
    """
    return mongomock.MongoClient()


@pytest.fixture
def mock_bedrock_client() -> Any:
    """
    Returns a mocked boto3 Bedrock runtime client.
    Can be used to mock LLM interactions without calling live AWS services.
    """
    client = MagicMock()

    # Pre-configure mock response for invoke_model
    mock_response = MagicMock()
    mock_response.read.return_value = b'{"generation": "Mocked LLM Response"}'
    client.invoke_model.return_value = {"body": mock_response}

    # Pre-configure mock response for streaming (invoke_model_with_response_stream)
    client.invoke_model_with_response_stream.return_value = {
        "body": [
            {"chunk": {"bytes": b'{"generation": "Mocked "}'}},
            {"chunk": {"bytes": b'{"generation": "LLM "}'}},
            {"chunk": {"bytes": b'{"generation": "Response"}'}},
        ]
    }

    return client


@pytest.fixture(autouse=True)
def mock_chat_bedrock() -> Any:
    """
    Autouse fixture to mock ChatBedrock to prevent network calls and return simulated LLM responses.
    """
    import sys
    import json
    from unittest.mock import MagicMock, patch

    with patch("agents.orchestrator.ChatBedrock") as mock_class:
        mock_instance = MagicMock()
        mock_class.return_value = mock_instance

        def mock_invoke(messages: list[Any], **kwargs: Any) -> Any:
            # Try to find 'state' in call stack to customize response for specific tests
            state = None
            frame: Any = sys._getframe()
            while frame:
                # Search for any dict or state object that has 'session_id'
                for val in frame.f_locals.values():
                    if isinstance(val, dict) and "session_id" in val:
                        state = val
                        break
                if state:
                    break
                frame = frame.f_back

            # Default: completed search entity set
            resp_dict = {
                "intent": "Rent",
                "city": "Bangalore",
                "location_anchor": "NPS Indiranagar",
                "property_type": "house",
                "bhk": 3,
                "budget_min": 25000,
                "budget_max": 35000,
                "radius_km": 4
            }

            if state:
                session_id = state.get("session_id", "")
                if session_id == "session-clarify":
                    resp_dict = {
                        "intent": "Ambiguous",
                        "city": "Bangalore",
                        "location_anchor": None,
                        "property_type": "apartment",
                        "bhk": None,
                        "budget_min": None,
                        "budget_max": None,
                        "radius_km": None
                    }
                elif session_id == "session-breach":
                    resp_dict = {
                        "intent": "Rent",
                        "city": "Bangalore",
                        "location_anchor": "NPS Indiranagar",
                        "property_type": "house",
                        "bhk": None,
                        "budget_min": 25000,
                        "budget_max": 35000,
                        "radius_km": None
                    }

            # If there is a user message, check its content for specific unit/integration test assertions
            user_msg = ""
            for m in reversed(messages):
                if m.__class__.__name__ == "HumanMessage":
                    user_msg = m.content
                    break

            if user_msg:
                user_msg_lower = user_msg.lower()
                if "looking for a flat in bangalore" in user_msg_lower or "flat in bangalore" in user_msg_lower:
                    resp_dict = {
                        "intent": "Ambiguous",
                        "city": "Bangalore",
                        "location_anchor": None,
                        "property_type": "apartment",
                        "bhk": None,
                        "budget_min": None,
                        "budget_max": None,
                        "radius_km": None
                    }
                elif "looking for a house in bangalore" in user_msg_lower:
                    resp_dict = {
                        "intent": "Ambiguous",
                        "city": "Bangalore",
                        "location_anchor": None,
                        "property_type": "house",
                        "bhk": None,
                        "budget_min": None,
                        "budget_max": None,
                        "radius_km": None
                    }
                elif "looking for a flat in chennai" in user_msg_lower:
                    resp_dict = {
                        "intent": "Ambiguous",
                        "city": "Chennai",
                        "location_anchor": None,
                        "property_type": "apartment",
                        "bhk": None,
                        "budget_min": None,
                        "budget_max": None,
                        "radius_km": None
                    }

            mock_msg = MagicMock()
            mock_msg.content = json.dumps(resp_dict)
            return mock_msg

        mock_instance.invoke.side_effect = mock_invoke
        yield mock_class


@pytest.fixture(autouse=True)
def auto_mock_db_client(mock_mongo_client: Any) -> Any:
    """
    Automatically configures the DB connection client to use mock_mongo_client.
    """
    from db.connection import set_db_client
    set_db_client(mock_mongo_client)
    yield mock_mongo_client
    set_db_client(None)


