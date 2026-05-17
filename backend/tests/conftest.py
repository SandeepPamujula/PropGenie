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
