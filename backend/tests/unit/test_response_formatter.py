import os
from unittest.mock import patch

from agents.response_formatter import format_currency, response_formatter_node
from models.state import get_initial_state


def test_format_currency() -> None:
    assert format_currency(20000) == "₹20K"
    assert format_currency(150000) == "₹1.5L"
    assert format_currency(10000000) == "₹1Cr"
    assert format_currency(15000000) == "₹1.5Cr"
    assert format_currency(500) == "₹500"

def test_response_formatter_happy_path() -> None:
    state = get_initial_state("session-fmt-happy", "127.0.0.1")
    state["intent"] = "rent"
    state["city"] = "Bangalore"
    state["location_anchor"] = "HSR Layout"
    state["property_type"] = "apartment"
    state["bhk"] = 3
    state["budget_min"] = 20000
    state["budget_max"] = 30000
    state["radius_km"] = 4

    state["generated_urls"] = [
        "https://www.nobroker.in/...",
        "https://www.99acres.com/..."
    ]

    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/...", "portal": "NoBroker", "validation": {"schema_valid": True, "head_status": 200}},
        {"url": "https://www.99acres.com/...", "portal": "99acres", "validation": {"schema_valid": True, "head_status": 200}}
    ]

    updates = response_formatter_node(state)

    urls = updates["validated_urls"]
    assert len(urls) == 2

    # Priority check
    assert urls[0]["portal"] == "NoBroker"
    assert urls[0]["priority"] is True
    assert urls[1]["portal"] == "99acres"
    assert urls[1]["priority"] is False

    # Summary check
    assert urls[0]["summary"] == "3BHK apartment rentals near HSR Layout, Bangalore — ₹20K to ₹30K/mo"

    # Notes check
    assert "4 km radius applied" in urls[0]["notes"]

    # Search meta check
    meta = updates["search_meta"]
    assert meta["portals_searched"] == 2
    assert meta["portals_returned"] == 2
    assert meta["portals_dropped"] == []
    assert "radius_km: 4" in meta["defaults_applied"]


def test_response_formatter_buy_flow_no_bhk() -> None:
    state = get_initial_state("session-fmt-buy", "127.0.0.1")
    state["intent"] = "buy"
    state["city"] = "Mumbai"
    state["property_type"] = "villa"
    state["budget_min"] = 10000000
    state["budget_max"] = 20000000

    state["validated_urls"] = [
        {"url": "https://www.99acres.com/...", "portal": "99acres"}
    ]

    updates = response_formatter_node(state)

    urls = updates["validated_urls"]
    assert len(urls) == 1

    # Priority check
    assert urls[0]["portal"] == "99acres"
    assert urls[0]["priority"] is True

    # Summary check
    assert urls[0]["summary"] == "Villa for sale in Mumbai — ₹1Cr to ₹2Cr"


def test_response_formatter_budget_defaults() -> None:
    state = get_initial_state("session-fmt-budget", "127.0.0.1")
    state["intent"] = "rent"
    state["city"] = "Delhi"
    state["budget_min"] = 0
    state["budget_max"] = 50000

    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/...", "portal": "NoBroker"}
    ]

    updates = response_formatter_node(state)

    urls = updates["validated_urls"]

    # Summary check
    assert urls[0]["summary"] == "Properties rentals in Delhi — Up to ₹50K/mo"

    # Notes check
    assert "Budget floor assumed as ₹0" in urls[0]["notes"]


def test_response_formatter_property_links_disabled() -> None:
    state = get_initial_state("session-fmt-links-disabled", "127.0.0.1")
    state["intent"] = "rent"
    state["city"] = "Bangalore"
    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/rent", "portal": "NoBroker"}
    ]
    state["scraped_property_urls"] = [
        {"url": "https://www.nobroker.in/prop1", "portal": "NoBroker", "source_search_url": "https://www.nobroker.in/rent"}
    ]
    state["validated_property_urls"] = [
        {"url": "https://www.nobroker.in/prop1", "portal": "NoBroker", "source_search_url": "https://www.nobroker.in/rent", "validation": {"schema_valid": True, "head_status": 200}}
    ]

    with patch.dict(os.environ, {"ENABLE_PROPERTY_SCRAPING": "false"}):
        updates = response_formatter_node(state)
        urls = updates["validated_urls"]
        assert len(urls) == 1
        assert urls[0]["property_links"] == []
        assert updates["search_meta"]["property_links_count"] == 0


def test_response_formatter_property_links_enabled_empty() -> None:
    state = get_initial_state("session-fmt-links-empty", "127.0.0.1")
    state["intent"] = "rent"
    state["city"] = "Bangalore"
    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/rent", "portal": "NoBroker"}
    ]
    state["scraped_property_urls"] = []
    state["validated_property_urls"] = []

    with patch.dict(os.environ, {"ENABLE_PROPERTY_SCRAPING": "true"}):
        updates = response_formatter_node(state)
        urls = updates["validated_urls"]
        assert len(urls) == 1
        assert urls[0]["property_links"] == []
        assert updates["search_meta"]["property_links_count"] == 0


def test_response_formatter_property_links_enabled_one() -> None:
    state = get_initial_state("session-fmt-links-one", "127.0.0.1")
    state["intent"] = "rent"
    state["city"] = "Bangalore"
    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/rent", "portal": "NoBroker"}
    ]
    state["scraped_property_urls"] = [
        {"url": "https://www.nobroker.in/prop1", "portal": "NoBroker", "source_search_url": "https://www.nobroker.in/rent"}
    ]
    state["validated_property_urls"] = [
        {"url": "https://www.nobroker.in/prop1", "portal": "NoBroker", "source_search_url": "https://www.nobroker.in/rent", "validation": {"schema_valid": True, "head_status": 200}}
    ]

    with patch.dict(os.environ, {"ENABLE_PROPERTY_SCRAPING": "true"}):
        updates = response_formatter_node(state)
        urls = updates["validated_urls"]
        assert len(urls) == 1
        links = urls[0]["property_links"]
        assert len(links) == 1
        assert links[0]["url"] == "https://www.nobroker.in/prop1"
        assert links[0]["portal"] == "NoBroker"
        assert links[0]["rank"] == 1
        assert links[0]["validation"] == {"schema_valid": True, "head_status": 200}
        assert updates["search_meta"]["property_links_count"] == 1


def test_response_formatter_property_links_enabled_multiple_sorting() -> None:
    state = get_initial_state("session-fmt-links-multi", "127.0.0.1")
    state["intent"] = "rent"
    state["city"] = "Bangalore"
    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/rent", "portal": "NoBroker"}
    ]

    # original scraped order: prop1 (rank 1), prop2 (rank 2), prop3 (rank 3)
    state["scraped_property_urls"] = [
        {"url": "https://www.nobroker.in/prop1", "portal": "NoBroker", "source_search_url": "https://www.nobroker.in/rent"},
        {"url": "https://www.nobroker.in/prop2", "portal": "NoBroker", "source_search_url": "https://www.nobroker.in/rent"},
        {"url": "https://www.nobroker.in/prop3", "portal": "NoBroker", "source_search_url": "https://www.nobroker.in/rent"}
    ]

    # validated list in arbitrary order (e.g. concurrent completion order)
    state["validated_property_urls"] = [
        {"url": "https://www.nobroker.in/prop3", "portal": "NoBroker", "source_search_url": "https://www.nobroker.in/rent", "validation": {"schema_valid": True, "head_status": 200}},
        {"url": "https://www.nobroker.in/prop1", "portal": "NoBroker", "source_search_url": "https://www.nobroker.in/rent", "validation": {"schema_valid": True, "head_status": 200}}
    ]

    with patch.dict(os.environ, {"ENABLE_PROPERTY_SCRAPING": "true"}):
        updates = response_formatter_node(state)
        urls = updates["validated_urls"]
        assert len(urls) == 1
        links = urls[0]["property_links"]
        assert len(links) == 2
        # Verify links are sorted by rank ascending (prop1 first, then prop3)
        assert links[0]["url"] == "https://www.nobroker.in/prop1"
        assert links[0]["rank"] == 1
        assert links[1]["url"] == "https://www.nobroker.in/prop3"
        assert links[1]["rank"] == 3
        assert updates["search_meta"]["property_links_count"] == 2
