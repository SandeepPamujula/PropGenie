from urllib.parse import parse_qs, urlparse

import pytest

from utils.config_loader import load_portal_configs


def test_load_portal_configs_success() -> None:
    """Verifies that both YAML files parse correctly and pass Pydantic validation."""
    configs = load_portal_configs()

    assert isinstance(configs, dict)
    assert "nobroker" in configs
    assert "99acres" in configs

    # Verify NoBroker properties
    nb = configs["nobroker"]
    assert nb.portal_id == "nobroker"
    assert nb.portal_name == "NoBroker"
    assert nb.base_url == "https://www.nobroker.in"
    assert "bangalore" in nb.city_slug_map
    assert "mumbai" in nb.city_slug_map
    assert len(nb.city_slug_map) >= 5

    # Verify 99acres properties
    acres = configs["99acres"]
    assert acres.portal_id == "99acres"
    assert acres.portal_name == "99acres"
    assert acres.base_url == "https://www.99acres.com"
    assert "bangalore" in acres.city_slug_map
    assert "mumbai" in acres.city_slug_map
    assert len(acres.city_slug_map) >= 5


def test_generate_url_nobroker() -> None:
    """Verifies NoBroker URL generation matches real portal URL structures."""
    configs = load_portal_configs()
    nb = configs["nobroker"]

    # 1. Rent flow, default search
    rent_default = nb.generate_url(flow="rent", city="bangalore", filters={})
    assert rent_default == nb.example_urls["rent_default"]

    # 2. Rent flow, with filters
    filters = {
        "bhk": ["2", "3"],
        "price_range": [15000, 30000],
        "furnishing": "fully_furnished",
    }
    rent_with_filters = nb.generate_url(flow="rent", city="bangalore", filters=filters)

    # Validate URL structure and query params robustly (independent of query parameter order)
    parsed = urlparse(rent_with_filters)
    assert parsed.scheme == "https"
    assert parsed.netloc == "www.nobroker.in"
    assert parsed.path == "/property/rent/bangalore/Bangalore"

    query = parse_qs(parsed.query)
    assert query["type"] == ["BHK2,BHK3"]
    assert query["rent"] == ["15000,30000"]
    assert query["furnishing"] == ["FULLY_FURNISHED"]

    # 3. Buy flow, default search
    buy_default = nb.generate_url(flow="buy", city="mumbai", filters={})
    assert buy_default == nb.example_urls["buy_default"]

    # 4. Buy flow, with filters
    buy_filters = {
        "bhk": ["3"],
        "price_range": [10000000, 20000000],
    }
    buy_with_filters = nb.generate_url(flow="buy", city="mumbai", filters=buy_filters)

    parsed_buy = urlparse(buy_with_filters)
    assert parsed_buy.path == "/property/sale/mumbai/Mumbai"
    query_buy = parse_qs(parsed_buy.query)
    assert query_buy["type"] == ["BHK3"]
    assert query_buy["price"] == ["10000000,20000000"]


def test_generate_url_99acres() -> None:
    """Verifies 99acres URL generation matches real portal URL structures."""
    configs = load_portal_configs()
    acres = configs["99acres"]

    # 1. Rent flow, default search
    rent_default = acres.generate_url(flow="rent", city="bangalore", filters={})
    assert rent_default == acres.example_urls["rent_default"]

    # 2. Rent flow, with filters
    filters = {
        "bhk": ["2", "3"],
        "price_min": 15000,
        "price_max": 30000,
        "furnishing": "fully_furnished",
    }
    rent_with_filters = acres.generate_url(flow="rent", city="bangalore", filters=filters)

    parsed = urlparse(rent_with_filters)
    assert parsed.scheme == "https"
    assert parsed.netloc == "www.99acres.com"
    assert parsed.path == "/search/property/rent/bangalore"

    query = parse_qs(parsed.query)
    assert query["bedroom"] == ["2,3"]
    assert query["budget_min"] == ["15000"]
    assert query["budget_max"] == ["30000"]
    assert query["furnishing"] == ["1"]

    # 3. Buy flow, default search
    buy_default = acres.generate_url(flow="buy", city="mumbai", filters={})
    assert buy_default == acres.example_urls["buy_default"]

    # 4. Buy flow, with filters
    buy_filters = {
        "bhk": ["3"],
        "price_min": 10000000,
        "price_max": 20000000,
    }
    buy_with_filters = acres.generate_url(flow="buy", city="mumbai", filters=buy_filters)

    parsed_buy = urlparse(buy_with_filters)
    assert parsed_buy.path == "/search/property/buy/mumbai"
    query_buy = parse_qs(parsed_buy.query)
    assert query_buy["bedroom"] == ["3"]
    assert query_buy["budget_min"] == ["10000000"]
    assert query_buy["budget_max"] == ["20000000"]


def test_generate_url_validation() -> None:
    """Verifies that invalid flow types or unsupported cities correctly raise errors."""
    configs = load_portal_configs()
    nb = configs["nobroker"]

    # Invalid flow
    with pytest.raises(ValueError, match="Invalid flow type"):
        nb.generate_url(flow="pg", city="bangalore", filters={})

    # Unsupported city
    with pytest.raises(ValueError, match="not supported by portal"):
        nb.generate_url(flow="rent", city="tokyo", filters={})
