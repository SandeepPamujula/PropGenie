import json
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

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
        "nobroker": {
            "locality": "Indiranagar",
            "placeName": "Indiranagar",
            "lat": 12.9783692,
            "lon": 77.6408356,
            "placeId": "ChIJkQN3GKQWrjsRNhBQJrhGD7U"
        },
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
    assert query_nb["radius"] == ["4.0"]
    assert query_nb["city"] == ["bangalore"]
    assert query_nb["locality"] == ["Indiranagar"]
    assert "searchParam" in query_nb

    # Verify searchParam decoded JSON structure
    import base64
    search_param_val = query_nb["searchParam"][0]
    decoded_json = json.loads(base64.b64decode(search_param_val).decode('utf-8'))
    assert decoded_json == [{
        "lat": 12.9783692,
        "lon": 77.6408356,
        "placeId": "ChIJkQN3GKQWrjsRNhBQJrhGD7U",
        "placeName": "Indiranagar"
    }]

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
def test_query_builder_plot_property_type(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that:
    1. If the flow is Rent and property type is 'plot', NoBroker is skipped gracefully (only 99acres generated).
    2. If the flow is Buy and property type is 'plot', NoBroker is NOT skipped and generates correct plot URL.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "nobroker": {
            "locality": "Indiranagar",
            "placeName": "Indiranagar",
            "lat": 12.9783692,
            "lon": 77.6408356,
            "placeId": "ChIJkQN3GKQWrjsRNhBQJrhGD7U"
        },
        "99acres": "indiranagar-bangalore"
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    # 1. Rent flow for plot (NoBroker does not support plot rent)
    state_rent = get_initial_state("session-qb-property-type-rent", "127.0.0.1")
    state_rent["intent"] = "Rent"
    state_rent["city"] = "Bangalore"
    state_rent["location_anchor"] = "Indiranagar"
    state_rent["property_type"] = "plot"

    updates_rent = query_builder_node(state_rent)
    urls_rent = updates_rent["generated_urls"]

    # Only 99acres URL should be generated; NoBroker should be skipped for rent plots
    assert len(urls_rent) == 1
    assert "99acres.com" in urls_rent[0]
    assert "nobroker.in" not in urls_rent[0]

    # 2. Buy flow for plot (NoBroker supports plot buy)
    state_buy = get_initial_state("session-qb-property-type-buy", "127.0.0.1")
    state_buy["intent"] = "Buy"
    state_buy["city"] = "Bangalore"
    state_buy["location_anchor"] = "Indiranagar"
    state_buy["property_type"] = "plot"
    state_buy["budget_min"] = 3400000
    state_buy["budget_max"] = 30000000

    updates_buy = query_builder_node(state_buy)
    urls_buy = updates_buy["generated_urls"]

    # Both portals should generate URLs
    assert len(urls_buy) == 2

    # Parse and validate NoBroker plot URL
    nb_url = next(u for u in urls_buy if "nobroker.in" in u)
    parsed_nb = urlparse(nb_url)
    assert parsed_nb.path == "/property/plot/bangalore/Indiranagar"
    query_nb = parse_qs(parsed_nb.query)

    # Assert filters
    assert "type" not in query_nb  # BHK should not be in the query
    assert "buildingType" not in query_nb  # buildingType should not be in the query
    assert query_nb["price"] == ["3400000,30000000"]
    assert query_nb["city"] == ["bangalore"]
    assert query_nb["locality"] == ["Indiranagar"]
    assert query_nb["radius"] == ["4.0"]
    assert "searchParam" in query_nb


@patch("agents.query_builder.ChatBedrock")
def test_query_builder_buy_house_property_type(mock_chat_bedrock: MagicMock) -> None:
    """
    Verifies that when property_type is "house" or "independent house" during a Buy flow,
    NoBroker URL is generated with 'propertyType=independent-house'.
    """
    mock_instance = MagicMock()
    mock_msg = MagicMock()
    mock_msg.content = json.dumps({
        "nobroker": {
            "locality": "Indiranagar",
            "placeName": "Indiranagar",
            "lat": 12.9783692,
            "lon": 77.6408356,
            "placeId": "ChIJkQN3GKQWrjsRNhBQJrhGD7U"
        },
        "99acres": "indiranagar-bangalore"
    })
    mock_instance.invoke.return_value = mock_msg
    mock_chat_bedrock.return_value = mock_instance

    state = get_initial_state("session-qb-buy-house", "127.0.0.1")
    state["intent"] = "Buy"
    state["city"] = "Bangalore"
    state["location_anchor"] = "Indiranagar"
    state["property_type"] = "house"
    state["bhk"] = 3
    state["budget_min"] = 10000000
    state["budget_max"] = 30000000

    updates = query_builder_node(state)
    urls = updates["generated_urls"]

    # Parse and validate NoBroker URL
    nb_url = next(u for u in urls if "nobroker.in" in u)
    parsed_nb = urlparse(nb_url)
    assert parsed_nb.path == "/property/sale/bangalore/Indiranagar"
    query_nb = parse_qs(parsed_nb.query)

    assert query_nb["type"] == ["BHK3"]
    assert query_nb["price"] == ["10000000,30000000"]
    assert query_nb["propertyType"] == ["independent-house"]
    assert query_nb["city"] == ["bangalore"]
    assert query_nb["locality"] == ["Indiranagar"]


