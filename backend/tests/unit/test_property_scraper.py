import os
from typing import Any
from unittest.mock import MagicMock, patch

from agents.property_scraper import extract_properties_from_html, property_scraper_node
from agents.url_validator import validate_property_url_structure
from models.state import get_initial_state

NOBROKER_HTML = """
<html>
<body>
  <a href="/property/rent/bangalore/hsr-layout/detail/prop1">Valid Link 1</a>
  <a href="/property/rent/bangalore/hsr-layout/prop2">Valid Link 2</a>
  <a href="https://www.nobroker.in/property/rent/bangalore/hsr-layout/detail/prop3">Valid Link 3</a>
  <a href="/property/sale/bangalore/hsr-layout/prop4">Valid Link 4</a>
  <a href="/property/rent/bangalore/hsr-layout/detail/prop5">Valid Link 5</a>
  <a href="/property/rent/bangalore/hsr-layout/detail/prop6">Valid Link 6 (over portal limit)</a>
  <a href="/property/rent/bangalore">Invalid Search Link (too short)</a>
  <a href="https://www.google.com">External Link</a>
</body>
</html>
"""

ACRES_HTML = """
<html>
<body>
  <a href="/hsr-layout-bangalore/spid-prop1">Valid Link 1</a>
  <a href="https://www.99acres.com/indiranagar-bangalore/detail/prop2">Valid Link 2</a>
  <a href="/whitefield-bangalore/spid-prop3">Valid Link 3</a>
  <a href="/some-other-place-mumbai/prop4">Valid Link 4</a>
  <a href="/hsr-layout-bangalore/spid-prop5">Valid Link 5</a>
  <a href="/hsr-layout-bangalore/spid-prop6">Valid Link 6 (over portal limit)</a>
  <a href="/not-matching-city/prop7">Invalid City Link</a>
  <a href="https://www.google.com">External Link</a>
</body>
</html>
"""

def test_extract_properties_nobroker() -> None:
    links = extract_properties_from_html(NOBROKER_HTML, "NoBroker")
    assert len(links) == 6
    assert all("nobroker.in" in url for url in links)
    assert "https://www.nobroker.in/property/rent/bangalore/hsr-layout/detail/prop1" in links

def test_extract_properties_99acres() -> None:
    links = extract_properties_from_html(ACRES_HTML, "99acres")
    assert len(links) == 6
    assert all("99acres.com" in url for url in links)
    assert "https://www.99acres.com/hsr-layout-bangalore/spid-prop1" in links

def test_validate_property_url_structure_cases() -> None:
    # Set up search URLs to check duplicate logic
    search_urls = ["https://www.nobroker.in/property/rent/bangalore/Hsr-layout"]

    # 1. Valid cases
    assert validate_property_url_structure("https://www.nobroker.in/property/rent/bangalore/hsr-layout/detail/prop1", "NoBroker", search_urls) is None
    assert validate_property_url_structure("https://www.99acres.com/hsr-layout-bangalore/spid-prop1", "99acres", search_urls) is None

    # 2. Duplicate check
    assert validate_property_url_structure(search_urls[0], "NoBroker", search_urls) == "URL is duplicate of the search URL"

    # 3. Invalid domains
    assert validate_property_url_structure("https://www.magicbricks.com/property-rent", "NoBroker", search_urls) == "Domain 'www.magicbricks.com' is not a NoBroker domain"
    assert validate_property_url_structure("https://www.nobroker.com/property-rent", "NoBroker", search_urls) == "Domain 'www.nobroker.com' is not a NoBroker domain"

    # 4. Insufficient path segments
    assert validate_property_url_structure("https://www.nobroker.in/property/rent/bangalore/Indiranagar", "NoBroker", search_urls) == "Path has insufficient segments (4 < 5)"
    assert validate_property_url_structure("https://www.99acres.com/hsr-layout-bangalore", "99acres", search_urls) == "Path has insufficient segments (1 < 2)"

    # 5. Invalid city prefix for 99acres
    assert validate_property_url_structure("https://www.99acres.com/hsr-layout-boston/spid-1", "99acres", search_urls) == "First path segment does not match locality-city slug pattern"

@patch("agents.property_scraper.fetch_url")
@patch("agents.url_validator.check_liveness")
def test_property_scraper_happy_path(mock_check_liveness: MagicMock, mock_fetch_url: MagicMock) -> None:
    """
    Verifies that search results are concurrently fetched, parsed, capped at 5 per portal,
    validated structurally + liveness, and capped at total max_scraped.
    """
    os.environ["ENABLE_PROPERTY_SCRAPING"] = "true"
    os.environ["MAX_SCRAPED_PROPERTIES"] = "5"

    # Mock liveness and fetching
    mock_check_liveness.return_value = (200, None)

    def side_effect(url: str, *args: Any, **kwargs: Any) -> tuple[Any, Any]:
        if "nobroker" in url:
            return NOBROKER_HTML, None
        elif "99acres" in url:
            return ACRES_HTML, None
        return "", None
    mock_fetch_url.side_effect = side_effect

    state = get_initial_state("session-scraper-happy", "127.0.0.1")
    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/property/rent/bangalore/Hsr-layout", "portal": "NoBroker"},
        {"url": "https://www.99acres.com/search/property/rent/hsr-layout-bangalore", "portal": "99acres"}
    ]

    updates = property_scraper_node(state)
    scraped = updates["scraped_property_urls"]
    validated = updates["validated_property_urls"]

    # Capped at 5 total scraped links
    assert len(scraped) == 5
    # All 5 scraped pass liveness checks, so 5 validated links
    assert len(validated) == 5

    for item in validated:
        assert "url" in item
        assert "portal" in item
        assert "source_search_url" in item
        assert "validation" in item
        assert item["validation"]["schema_valid"] is True
        assert item["validation"]["head_status"] == 200

@patch("agents.property_scraper.fetch_url")
@patch("agents.url_validator.check_liveness")
def test_property_scraper_validation_liveness(mock_check_liveness: MagicMock, mock_fetch_url: MagicMock) -> None:
    """
    Verifies that property URLs failing liveness checks (non-2xx or timeouts) are dropped from validated_property_urls.
    """
    os.environ["ENABLE_PROPERTY_SCRAPING"] = "true"
    os.environ["MAX_SCRAPED_PROPERTIES"] = "5"

    # Mock: First property URL returns 404, second times out, others return 200 OK.
    def liveness_side_effect(url: str, *args: Any, **kwargs: Any) -> tuple[Any, Any]:
        if "prop1" in url:
            return 404, "Not Found"
        elif "prop2" in url:
            return None, "Timeout"
        else:
            return 200, None
    mock_check_liveness.side_effect = liveness_side_effect

    def fetch_side_effect(url: str, *args: Any, **kwargs: Any) -> tuple[Any, Any]:
        if "nobroker" in url:
            return NOBROKER_HTML, None
        return "", None
    mock_fetch_url.side_effect = fetch_side_effect

    state = get_initial_state("session-scraper-liveness", "127.0.0.1")
    # Only scrape NoBroker search page
    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/property/rent/bangalore/Hsr-layout", "portal": "NoBroker"}
    ]

    updates = property_scraper_node(state)
    scraped = updates["scraped_property_urls"]
    validated = updates["validated_property_urls"]

    # Extracted top 5 from NoBroker
    assert len(scraped) == 5
    # Two fail liveness check (prop1 returns 404, prop2 times out) -> Only 3 validated URLs survive
    assert len(validated) == 3
    assert not any("prop1" in item["url"] or "prop2" in item["url"] for item in validated)

@patch("agents.property_scraper.fetch_url")
@patch("agents.url_validator.check_liveness")
def test_property_scraper_feature_flag_disabled(mock_check_liveness: MagicMock, mock_fetch_url: MagicMock) -> None:
    """
    Verifies that when the feature flag is disabled, no HTTP request is made and empty list returned.
    """
    os.environ["ENABLE_PROPERTY_SCRAPING"] = "false"

    state = get_initial_state("session-scraper-disabled", "127.0.0.1")
    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/property/rent/bangalore/Hsr-layout", "portal": "NoBroker"}
    ]

    updates = property_scraper_node(state)
    scraped = updates["scraped_property_urls"]
    validated = updates["validated_property_urls"]

    assert len(scraped) == 0
    assert len(validated) == 0
    assert mock_fetch_url.call_count == 0

@patch("agents.property_scraper.fetch_url")
@patch("agents.url_validator.check_liveness")
def test_property_scraper_blocked_or_empty_response(mock_check_liveness: MagicMock, mock_fetch_url: MagicMock) -> None:
    """
    Verifies that if requests time out, return 403, or return empty responses,
    the scraper logs warning and pipeline continues with empty lists.
    """
    os.environ["ENABLE_PROPERTY_SCRAPING"] = "true"

    def side_effect(url: str, *args: Any, **kwargs: Any) -> tuple[Any, Any]:
        if "nobroker" in url:
            return None, "HTTPError 403: Forbidden"
        elif "99acres" in url:
            return "", None  # Empty response
        return "", None
    mock_fetch_url.side_effect = side_effect

    state = get_initial_state("session-scraper-blocked", "127.0.0.1")
    state["validated_urls"] = [
        {"url": "https://www.nobroker.in/property/rent/bangalore/Hsr-layout", "portal": "NoBroker"},
        {"url": "https://www.99acres.com/search/property/rent/hsr-layout-bangalore", "portal": "99acres"}
    ]

    updates = property_scraper_node(state)
    scraped = updates["scraped_property_urls"]
    validated = updates["validated_property_urls"]

    assert len(scraped) == 0
    assert len(validated) == 0
