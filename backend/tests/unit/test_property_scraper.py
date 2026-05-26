import os
from typing import Any
from unittest.mock import MagicMock, patch
import pytest
from agents.property_scraper import property_scraper_node, extract_properties_from_html
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
    # Should extract valid relative/absolute property URLs
    # Links matching: /property/rent/bangalore/hsr-layout/detail/prop1, /property/rent/bangalore/hsr-layout/prop2, ...
    assert len(links) == 6
    assert all("nobroker.in" in url for url in links)
    assert "https://www.nobroker.in/property/rent/bangalore/hsr-layout/detail/prop1" in links
    assert "https://www.nobroker.in/property/rent/bangalore/hsr-layout/prop2" in links
    assert "https://www.nobroker.in/property/rent/bangalore/hsr-layout/detail/prop3" in links
    assert "https://www.nobroker.in/property/sale/bangalore/hsr-layout/prop4" in links
    assert "https://www.nobroker.in/property/rent/bangalore/hsr-layout/detail/prop5" in links
    assert "https://www.nobroker.in/property/rent/bangalore/hsr-layout/detail/prop6" in links

def test_extract_properties_99acres() -> None:
    links = extract_properties_from_html(ACRES_HTML, "99acres")
    # Links starting with supported cities: bangalore, mumbai, pune, chennai, hyderabad, delhi-ncr, delhi
    assert len(links) == 6
    assert all("99acres.com" in url for url in links)
    assert "https://www.99acres.com/hsr-layout-bangalore/spid-prop1" in links
    assert "https://www.99acres.com/indiranagar-bangalore/detail/prop2" in links
    assert "https://www.99acres.com/whitefield-bangalore/spid-prop3" in links
    assert "https://www.99acres.com/some-other-place-mumbai/prop4" in links
    assert "https://www.99acres.com/hsr-layout-bangalore/spid-prop5" in links
    assert "https://www.99acres.com/hsr-layout-bangalore/spid-prop6" in links

@patch("agents.property_scraper.fetch_url")
def test_property_scraper_happy_path(mock_fetch_url: MagicMock) -> None:
    """
    Verifies that search results are concurrently fetched, parsed, capped at 5 per portal,
    and capped at total max_scraped across all portals.
    """
    os.environ["ENABLE_PROPERTY_SCRAPING"] = "true"
    os.environ["MAX_SCRAPED_PROPERTIES"] = "5"
    
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
    
    # Each portal has 6 valid links. We cap at 5 per portal and then cap at 5 total max across all portals.
    assert len(scraped) == 5
    
    # Ensure structure matches spec: url, portal, source_search_url
    for item in scraped:
        assert "url" in item
        assert "portal" in item
        assert "source_search_url" in item
        assert item["portal"] in ["NoBroker", "99acres"]
        if item["portal"] == "NoBroker":
            assert item["source_search_url"] == "https://www.nobroker.in/property/rent/bangalore/Hsr-layout"
        else:
            assert item["source_search_url"] == "https://www.99acres.com/search/property/rent/hsr-layout-bangalore"

@patch("agents.property_scraper.fetch_url")
def test_property_scraper_feature_flag_disabled(mock_fetch_url: MagicMock) -> None:
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
    
    assert len(scraped) == 0
    assert mock_fetch_url.call_count == 0

@patch("agents.property_scraper.fetch_url")
def test_property_scraper_blocked_or_empty_response(mock_fetch_url: MagicMock) -> None:
    """
    Verifies that if requests time out, return 403, or return empty responses, 
    the scraper logs warning and pipeline continues with empty list.
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
    
    assert len(scraped) == 0
