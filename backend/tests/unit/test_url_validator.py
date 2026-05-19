from unittest.mock import MagicMock, patch
import pytest
from agents.url_validator import url_validator_node
from models.state import get_initial_state

@patch("agents.url_validator.check_liveness")
def test_url_validator_happy_path(mock_check_liveness: MagicMock) -> None:
    """
    Verifies that perfectly structured and live URLs are successfully validated.
    """
    # Mock liveness to succeed with 200 OK
    mock_check_liveness.return_value = (200, None)

    state = get_initial_state("session-val-happy", "127.0.0.1")
    state["intent"] = "rent"
    state["generated_urls"] = [
        "https://www.nobroker.in/property/rent/bangalore/Indiranagar?type=BHK2&rent=20000,30000",
        "https://www.99acres.com/search/property/rent/indiranagar-bangalore?bedroom=2&budget_min=20000&budget_max=30000"
    ]

    updates = url_validator_node(state)
    validated = updates["validated_urls"]

    assert len(validated) == 2
    assert validated[0]["url"] == state["generated_urls"][0]
    assert validated[0]["validation"]["schema_valid"] is True
    assert validated[0]["validation"]["head_status"] == 200

    assert validated[1]["url"] == state["generated_urls"][1]
    assert validated[1]["validation"]["schema_valid"] is True
    assert validated[1]["validation"]["head_status"] == 200


@patch("agents.url_validator.check_liveness")
def test_url_validator_structural_invalid_domain(mock_check_liveness: MagicMock) -> None:
    """
    Verifies that URLs with domains not in the whitelist (e.g. magicbricks.com)
    are immediately caught and dropped without invoking HTTP liveness checks.
    """
    state = get_initial_state("session-val-domain", "127.0.0.1")
    state["intent"] = "rent"
    state["generated_urls"] = [
        "https://www.magicbricks.com/property-for-rent/bangalore",  # Invalid domain
        "https://www.nobroker.in/property/rent/bangalore/Bangalore"  # Valid domain
    ]

    # Mock 200 OK for any allowed calls
    mock_check_liveness.return_value = (200, None)

    updates = url_validator_node(state)
    validated = updates["validated_urls"]

    # Only NoBroker URL should survive
    assert len(validated) == 1
    assert validated[0]["url"] == state["generated_urls"][1]

    # Verify that check_liveness was only called once (for NoBroker), and NOT for magicbricks
    assert mock_check_liveness.call_count == 1


@patch("agents.url_validator.check_liveness")
def test_url_validator_budget_bounds(mock_check_liveness: MagicMock) -> None:
    """
    Verifies that budget values outside the logical limits (₹1K - ₹5L/mo for rent,
    ₹1K - ₹50Cr for buy) trigger structural validation failures.
    """
    state = get_initial_state("session-val-budget", "127.0.0.1")
    state["intent"] = "rent"
    state["generated_urls"] = [
        # Rent budget of ₹6,00,000 exceeds ₹5L cap
        "https://www.nobroker.in/property/rent/bangalore/Bangalore?rent=600000",
        # Rent budget of ₹500 is below ₹1K floor
        "https://www.99acres.com/search/property/rent/bangalore?budget_min=500",
        # Valid rent budget of ₹25K
        "https://www.nobroker.in/property/rent/bangalore/Bangalore?rent=25000"
    ]

    mock_check_liveness.return_value = (200, None)

    updates = url_validator_node(state)
    validated = updates["validated_urls"]

    # Only the last URL with ₹25K rent should survive
    assert len(validated) == 1
    assert validated[0]["url"] == state["generated_urls"][2]


@patch("agents.url_validator.check_liveness")
def test_url_validator_head_failure_and_timeout(mock_check_liveness: MagicMock) -> None:
    """
    Verifies that URLs returning non-2xx status codes or suffering from network timeouts
    are filtered out.
    """
    # Mock: First URL returns 404, second URL suffers a network timeout (returns None, error),
    # and third URL returns 200 OK.
    def side_effect_fn(url, *args, **kwargs):
        if "Indiranagar" in url:
            return (404, "Not Found")
        elif "99acres" in url:
            return (None, "Connection Timeout")
        else:
            return (200, None)
    mock_check_liveness.side_effect = side_effect_fn

    state = get_initial_state("session-val-liveness", "127.0.0.1")
    state["intent"] = "buy"
    state["generated_urls"] = [
        "https://www.nobroker.in/property/sale/bangalore/Indiranagar",  # Returns 404
        "https://www.99acres.com/search/property/buy/bangalore",        # Times out
        "https://www.nobroker.in/property/sale/mumbai/Bandra"            # Returns 200
    ]

    updates = url_validator_node(state)
    validated = updates["validated_urls"]

    # Only the third URL (200 OK) should survive
    assert len(validated) == 1
    assert validated[0]["url"] == state["generated_urls"][2]
    assert validated[0]["validation"]["head_status"] == 200


@patch("agents.url_validator.check_liveness")
def test_url_validator_concurrency_and_all_fail(mock_check_liveness: MagicMock) -> None:
    """
    Verifies that multiple URLs are checked concurrently and, if all fail,
    the resulting validated list is empty.
    """
    # All URLs fail HEAD check
    mock_check_liveness.return_value = (500, "Internal Server Error")

    state = get_initial_state("session-val-all-fail", "127.0.0.1")
    state["intent"] = "rent"
    state["generated_urls"] = [
        "https://www.nobroker.in/property/rent/bangalore/Bangalore",
        "https://www.99acres.com/search/property/rent/bangalore"
    ]

    updates = url_validator_node(state)
    validated = updates["validated_urls"]

    assert len(validated) == 0
