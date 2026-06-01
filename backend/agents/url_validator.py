import concurrent.futures
import logging
import re
import urllib.error
import urllib.request
from typing import Any

logger = logging.getLogger(__name__)
from urllib.parse import parse_qs, urlparse

from models.state import AgentState
from observability.langfuse_tracer import create_span, end_span
from utils.constants import URLValidatorConstants


def validate_url_structure(url: str, intent: str) -> str | None:
    """
    Performs structural schema validation on a portal search URL.
    Returns None if valid, or a string describing the validation error.
    """
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path
        query = parse_qs(parsed.query)

        # 1. Base Domain Whitelist Check
        if not (netloc.endswith(URLValidatorConstants.NOBROKER_DOMAIN) or netloc.endswith(URLValidatorConstants.ACRES_DOMAIN)):
            return f"Domain '{netloc}' is not in the whitelist"

        # 2. Path segments non-empty & no consecutive slashes
        if "//" in path:
            return "URL path contains double slashes"

        segments = [s for s in path.split("/") if s]
        if not segments:
            return "URL path is empty"

        for seg in segments:
            if not seg.strip():
                return "URL contains empty path segment"

        # Determine flow (rent vs buy)
        flow = intent.lower() if intent else URLValidatorConstants.FLOW_RENT
        if URLValidatorConstants.FLOW_RENT in path.lower():
            flow = URLValidatorConstants.FLOW_RENT
        elif URLValidatorConstants.PATH_SEGMENT_SALE in path.lower() or URLValidatorConstants.FLOW_BUY in path.lower() or URLValidatorConstants.PATH_SEGMENT_PLOT in path.lower():
            flow = URLValidatorConstants.FLOW_BUY

        # 3. Budget values validation (numeric and within logical bounds)
        if URLValidatorConstants.NOBROKER_DOMAIN in netloc:
            # Check rent parameter
            rent_param = query.get(URLValidatorConstants.NOBROKER_RENT_PARAM)
            if rent_param:
                val_str = rent_param[0]
                vals = val_str.split(",")
                for val in vals:
                    if not val.strip():
                        return f"NoBroker '{URLValidatorConstants.NOBROKER_RENT_PARAM}' parameter has empty value"
                    try:
                        num = int(val)
                    except ValueError:
                        return f"NoBroker '{URLValidatorConstants.NOBROKER_RENT_PARAM}' value '{val}' is not numeric"
                    if not (URLValidatorConstants.RENT_MIN <= num <= URLValidatorConstants.RENT_MAX):
                        return f"NoBroker rent value ₹{num} is out of plausible range (₹1K - ₹5L)"

            # Check price parameter
            price_param = query.get(URLValidatorConstants.NOBROKER_PRICE_PARAM)
            if price_param:
                val_str = price_param[0]
                vals = val_str.split(",")
                for val in vals:
                    if not val.strip():
                        return f"NoBroker '{URLValidatorConstants.NOBROKER_PRICE_PARAM}' parameter has empty value"
                    try:
                        num = int(val)
                    except ValueError:
                        return f"NoBroker '{URLValidatorConstants.NOBROKER_PRICE_PARAM}' value '{val}' is not numeric"
                    if not (URLValidatorConstants.BUY_MIN <= num <= URLValidatorConstants.BUY_MAX):
                        return f"NoBroker price value ₹{num} is out of plausible range (₹1K - ₹50Cr)"

        elif URLValidatorConstants.ACRES_DOMAIN in netloc:
            budget_min_param = query.get(URLValidatorConstants.ACRES_BUDGET_MIN_PARAM)
            budget_max_param = query.get(URLValidatorConstants.ACRES_BUDGET_MAX_PARAM)

            # Check budget_min
            if budget_min_param:
                val = budget_min_param[0]
                try:
                    num = int(val)
                except ValueError:
                    return f"99acres '{URLValidatorConstants.ACRES_BUDGET_MIN_PARAM}' value '{val}' is not numeric"
                limit_max = URLValidatorConstants.BUY_MAX if flow == URLValidatorConstants.FLOW_BUY else URLValidatorConstants.RENT_MAX
                if not (URLValidatorConstants.RENT_MIN <= num <= limit_max):
                    flow_str = URLValidatorConstants.FLOW_BUY if flow == URLValidatorConstants.FLOW_BUY else URLValidatorConstants.FLOW_RENT
                    limit_str = "₹50Cr" if flow == URLValidatorConstants.FLOW_BUY else "₹5L"
                    return f"99acres budget_min ₹{num} is out of plausible range for {flow_str} (₹1K - {limit_str})"

            # Check budget_max
            if budget_max_param:
                val = budget_max_param[0]
                try:
                    num = int(val)
                except ValueError:
                    return f"99acres '{URLValidatorConstants.ACRES_BUDGET_MAX_PARAM}' value '{val}' is not numeric"
                limit_max = URLValidatorConstants.BUY_MAX if flow == URLValidatorConstants.FLOW_BUY else URLValidatorConstants.RENT_MAX
                if not (URLValidatorConstants.RENT_MIN <= num <= limit_max):
                    flow_str = URLValidatorConstants.FLOW_BUY if flow == URLValidatorConstants.FLOW_BUY else URLValidatorConstants.FLOW_RENT
                    limit_str = "₹50Cr" if flow == URLValidatorConstants.FLOW_BUY else "₹5L"
                    return f"99acres budget_max ₹{num} is out of plausible range for {flow_str} (₹1K - {limit_str})"

        return None

    except Exception as e:
        return f"Unexpected structural parsing error: {str(e)}"

def validate_property_url_structure(url: str, portal: str, search_urls: list[str]) -> str | None:
    """
    Validates a scraped property URL structurally.
    Returns None if valid, or a string describing the validation error.
    """
    if url in search_urls:
        return "URL is duplicate of the search URL"

    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path

        if portal == "NoBroker":
            if not netloc.endswith(URLValidatorConstants.NOBROKER_DOMAIN):
                return f"Domain '{netloc}' is not a NoBroker domain"
            if not (path.startswith(URLValidatorConstants.PREFIX_PROPERTY_RENT) or path.startswith(URLValidatorConstants.PREFIX_PROPERTY_SALE) or path.startswith(URLValidatorConstants.PREFIX_PROPERTY_PLOT)):
                return "Path does not start with property rent/sale/plot prefix"
            parts = [p for p in path.split('/') if p]
            if len(parts) < URLValidatorConstants.NOBROKER_MIN_PATH_SEGMENTS:
                return f"Path has insufficient segments ({len(parts)} < {URLValidatorConstants.NOBROKER_MIN_PATH_SEGMENTS})"
        elif portal == "99acres":
            if not netloc.endswith(URLValidatorConstants.ACRES_DOMAIN):
                return f"Domain '{netloc}' is not a 99acres domain"
            parts = [p for p in path.split('/') if p]
            if len(parts) < URLValidatorConstants.ACRES_MIN_PATH_SEGMENTS:
                return f"Path has insufficient segments ({len(parts)} < {URLValidatorConstants.ACRES_MIN_PATH_SEGMENTS})"
            first_seg = parts[0]
            if not re.match(URLValidatorConstants.ACRES_CITY_PATTERN, first_seg, re.IGNORECASE):
                return "First path segment does not match locality-city slug pattern"

        return None
    except Exception as e:
        return f"Unexpected structural validation error: {str(e)}"

def validate_scraped_properties(
    scraped_list: list[dict[str, Any]],
    search_urls: list[str],
    trace: Any | None = None
) -> list[dict[str, Any]]:
    """
    Validates a list of scraped property URLs structurally and checks their liveness concurrently.
    Returns a list of validated property dictionaries.
    """
    print(f"[URL Validator] Validating {len(scraped_list)} scraped property URLs")

    # 1. Structural Checks
    valid_struct_items = []
    dropped_info: dict[str, str] = {}

    for item in scraped_list:
        url = item["url"]
        portal = item["portal"]

        error = validate_property_url_structure(url, portal, search_urls)
        if error:
            logger.warning(f"[URL_VALIDATION_FAILED] Property URL '{url}' failed structural checks: {error}")
            dropped_info[url] = f"Structural Validation: {error}"
        else:
            valid_struct_items.append(item)

    # 2. Concurrent HTTP HEAD checks
    validated_list = []
    if valid_struct_items:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(valid_struct_items)) as executor:
            future_to_item = {
                executor.submit(check_liveness, item["url"]): item for item in valid_struct_items
            }

            for future in concurrent.futures.as_completed(future_to_item):
                item = future_to_item[future]
                url = item["url"]
                portal = item["portal"]
                source_search_url = item["source_search_url"]

                try:
                    status_code, err = future.result()
                    if status_code and 200 <= status_code < 300:
                        validated_list.append({
                            "url": url,
                            "portal": portal,
                            "source_search_url": source_search_url,
                            "validation": {
                                "schema_valid": True,
                                "head_status": status_code
                            }
                        })
                    else:
                        fail_reason = err or f"HTTP status {status_code}"
                        logger.warning(f"[URL_VALIDATION_FAILED] Property URL '{url}' failed liveness check: {fail_reason}")
                        dropped_info[url] = f"HEAD Check: {fail_reason}"
                except Exception as e:
                    print(f"[URL Validator] Exception checking liveness of '{url}': {e}")
                    dropped_info[url] = f"HEAD Exception: {str(e)}"

    # 3. Observability tracing for dropped property URLs
    if dropped_info and trace:
        from observability.langfuse_tracer import update_trace_metadata
        update_trace_metadata(
            trace,
            metadata={
                "hallucination_detected": True,
                "dropped_property_urls": dropped_info,
                "dropped_property_urls_count": len(dropped_info)
            },
            tags=["propgenie", "url_validator", "hallucination_detected", "property_validation_failed"]
        )

    print(f"[URL Validator] Property validation completed. Valid: {len(validated_list)}, Dropped: {len(dropped_info)}")
    return validated_list

def check_liveness(url: str) -> tuple[int | None, str | None]:
    """
    Performs an HTTP HEAD request with a 2-second timeout and custom User-Agent.
    Returns (status_code, error_message).
    """
    headers = {
        "User-Agent": URLValidatorConstants.USER_AGENT
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=URLValidatorConstants.TIMEOUT_LIVENESS) as response:
            return response.status, None
    except urllib.error.HTTPError as e:
        return e.code, str(e)
    except urllib.error.URLError as e:
        return None, f"Network error: {e.reason}"
    except Exception as e:
        return None, f"Timeout/Error: {str(e)}"

def url_validator_node(state: AgentState) -> dict[str, Any]:
    """
    Validates generated portal search URLs structurally and tests their live connection.
    Drops invalid or dead URLs and logs validation metrics.
    """
    import time
    print("[URL Validator Agent] Started execution")
    start_time = time.time()

    generated_urls = state.get("generated_urls", [])
    intent = state.get("intent") or URLValidatorConstants.FLOW_RENT

    trace = state.get("trace")
    span = create_span(trace, "url_validator", generated_urls)

    dropped_info: dict[str, str] = {}
    valid_struct_urls = []

    # 2. Step 1: Structural Checks
    for url in generated_urls:
        error = validate_url_structure(url, intent)
        if error:
            logger.warning(f"[URL_VALIDATION_FAILED] Search URL '{url}' failed structural checks: {error}")
            dropped_info[url] = f"Structural Validation: {error}"
        else:
            valid_struct_urls.append(url)

    # 3. Step 2: Concurrent HTTP HEAD checks
    validated_list = []

    if valid_struct_urls:
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(valid_struct_urls)) as executor:
            future_to_url = {executor.submit(check_liveness, url): url for url in valid_struct_urls}

            for future in concurrent.futures.as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    status_code, err = future.result()
                    if status_code and 200 <= status_code < 300:
                        portal_name = "NoBroker" if URLValidatorConstants.NOBROKER_DOMAIN in url.lower() else "99acres"
                        validated_list.append({
                            "url": url,
                            "portal": portal_name,
                            "validation": {
                                "schema_valid": True,
                                "head_status": status_code
                            }
                        })
                    else:
                        fail_reason = err or f"HTTP status {status_code}"
                        logger.warning(f"[URL_VALIDATION_FAILED] Search URL '{url}' failed liveness check: {fail_reason}")
                        dropped_info[url] = f"HEAD Check: {fail_reason}"
                except Exception as e:
                    print(f"[URL Validator] Exception checking liveness of '{url}': {e}")
                    dropped_info[url] = f"HEAD Exception: {str(e)}"

    # 4. Observability tagging for hallucinations / drops
    hallucination_detected = len(dropped_info) > 0
    if hallucination_detected:
        from observability.langfuse_tracer import update_trace_metadata
        update_trace_metadata(
            trace,
            metadata={
                "hallucination_detected": True,
                "dropped_urls": dropped_info,
                "dropped_urls_count": len(dropped_info)
            },
            tags=["propgenie", "url_validator", "hallucination_detected"]
        )

    print(f"[URL Validator Agent] Completed. Validated: {len(validated_list)}, Dropped: {len(dropped_info)}")

    # End Langfuse span
    latency_ms = int((time.time() - start_time) * 1000)
    metrics = {
        "latency": latency_ms,
        "hallucination_detected": hallucination_detected,
        "dropped_urls_count": len(dropped_info),
        "dropped_urls": dropped_info
    }

    end_span(span, validated_list, metrics)

    return {
        "validated_urls": validated_list
    }
