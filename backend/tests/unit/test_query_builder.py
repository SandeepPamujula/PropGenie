import json
from typing import Any
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse
import pytest
from agents.query_builder import query_builder_node
from models.state import get_initial_state

@patch("agents.query_builder.ChatBedrock")
def test_query_builder_happy_path_bangalore(mock_chat_bedrock: MagicMock) -> None:
    """
    Given a complete entity set for a Bangalore rental,
    verifies that both NoBroker and 99acres URLs are generated with correct parameters.
    """
    # Mock LLM location mapping response
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "nobroker": "Indiranagar",
        "99acres": "indiranagar-bangalore"
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    # Complete rent state
    state = get_initial_state("session-happy-qb", "127.0.0.1")
    state["intent"] = "Rent"
    state["city"] = "Bangalore"
    state["location_anchor"] = "NPS Indiranagar"
    state["property_type"] = "apartment"
    state["bhk"] = 3
    state["budget_min"] = 25000
    state["budget_max"] = 35000

    updates = query_builder_node(state)
    urls = updates["generated_urls"]

    assert len(urls) == 2

    # Parse and validate NoBroker URL
    nb_url = next(u for u in urls if "nobroker.in" in u)
    parsed_nb = urlparse(nb_url)
    assert parsed_nb.path == "/property/rent/bangalore/Indiranagar"
    query_nb = parse_qs(parsed_nb.query)
    assert query_nb["type"] == ["BHK3"]
    assert query_nb["rent"] == ["25000,35000"]
    assert query_nb["buildingType"] == ["AP"]

    # Parse and validate 99acres URL
    acres_url = next(u for u in urls if "99acres.com" in u)
    parsed_acres = urlparse(acres_url)
    assert parsed_acres.path == "/search/property/rent/indiranagar-bangalore"
    query_acres = parse_qs(parsed_acres.query)
    assert query_acres["bedroom"] == ["3"]
    assert query_acres["budget_min"] == ["25000"]
    assert query_acres["budget_max"] == ["35000"]


@patch("agents.query_builder.ChatBedrock")
def test_query_builder_apply_defaults(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that defaults (radius = 4 km, budget_min = 0) are applied
    before constructing the search URLs.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "nobroker": None,
        "99acres": None
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    state = get_initial_state("session-qb-defaults", "127.0.0.1")
    state["intent"] = "Rent"
    state["city"] = "Bangalore"
    # radius_km and budget_min are left as None to test default application

    updates = query_builder_node(state)

    assert updates["radius_km"] == 4
    assert updates["budget_min"] == 0
    assert len(updates["generated_urls"]) == 2

    # Verify that default budget min (0) was passed to the URLs
    nb_url = next(u for u in updates["generated_urls"] if "nobroker.in" in u)
    query_nb = parse_qs(urlparse(nb_url).query)
    assert "0" in query_nb["rent"][0]

    acres_url = next(u for u in updates["generated_urls"] if "99acres.com" in u)
    query_acres = parse_qs(urlparse(acres_url).query)
    assert query_acres["budget_min"] == ["0"]


@patch("agents.query_builder.ChatBedrock")
def test_query_builder_skip_unsupported_city(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that if a city is not supported in the portal's slug map (e.g. Kochi),
    the portal is skipped gracefully instead of raising an error.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "nobroker": "Kakkanad",
        "99acres": "kakkanad-kochi"
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    state = get_initial_state("session-qb-skip-city", "127.0.0.1")
    state["intent"] = "Buy"
    state["city"] = "Kochi"  # Not present in NoBroker / 99acres YAML slug maps
    state["location_anchor"] = "Kakkanad"

    updates = query_builder_node(state)

    # Both portals should be skipped since Kochi is not in either of their slug maps
    assert len(updates["generated_urls"]) == 0


@patch("agents.query_builder.ChatBedrock")
def test_query_builder_skip_unsupported_property_type(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that if a portal doesn't support a property type (e.g., NoBroker does not support plots),
    it is skipped gracefully.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "nobroker": "Indiranagar",
        "99acres": "indiranagar-bangalore"
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    state = get_initial_state("session-qb-property-type", "127.0.0.1")
    state["intent"] = "Buy"
    state["city"] = "Bangalore"
    state["location_anchor"] = "Indiranagar"
    state["property_type"] = "plot"  # NoBroker does not support plots; 99acres supports it (not filtered)

    updates = query_builder_node(state)
    urls = updates["generated_urls"]

    # Only 99acres URL should be generated; NoBroker should be skipped
    assert len(urls) == 1
    assert "99acres.com" in urls[0]
    assert "nobroker.in" not in urls[0]
