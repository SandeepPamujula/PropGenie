import concurrent.futures
import urllib.error
import urllib.request
from typing import Any
from urllib.parse import parse_qs, urlparse
from observability.langfuse_tracer import create_span, end_span
from models.state import AgentState

def validate_url_structure(url: str, intent: str) -> str | None:
    """
    Performs structural schema validation on a portal URL.
    Returns None if valid, or a string describing the validation error.
    """
    try:
        parsed = urlparse(url)
        netloc = parsed.netloc.lower()
        path = parsed.path
        query = parse_qs(parsed.query)
        
        # 1. Base Domain Whitelist Check
        if not (netloc.endswith("nobroker.in") or netloc.endswith("99acres.com")):
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
        flow = intent.lower() if intent else "rent"
        if "rent" in path.lower():
            flow = "rent"
        elif "sale" in path.lower() or "buy" in path.lower():
            flow = "buy"
            
        # 3. Budget values validation (numeric and within logical bounds)
        if "nobroker.in" in netloc:
            # Check rent parameter
            rent_param = query.get("rent")
            if rent_param:
                val_str = rent_param[0]
                vals = val_str.split(",")
                for val in vals:
                    if not val.strip():
                        return "NoBroker 'rent' parameter has empty value"
                    try:
                        num = int(val)
                    except ValueError:
                        return f"NoBroker 'rent' value '{val}' is not numeric"
                    if not (1000 <= num <= 500000):
                        return f"NoBroker rent value ₹{num} is out of plausible range (₹1K - ₹5L)"
                        
            # Check price parameter
            price_param = query.get("price")
            if price_param:
                val_str = price_param[0]
                vals = val_str.split(",")
                for val in vals:
                    if not val.strip():
                        return "NoBroker 'price' parameter has empty value"
                    try:
                        num = int(val)
                    except ValueError:
                        return f"NoBroker 'price' value '{val}' is not numeric"
                    if not (1000 <= num <= 500000000):
                        return f"NoBroker price value ₹{num} is out of plausible range (₹1K - ₹50Cr)"
                        
        elif "99acres.com" in netloc:
            budget_min_param = query.get("budget_min")
            budget_max_param = query.get("budget_max")
            
            # Check budget_min
            if budget_min_param:
                val = budget_min_param[0]
                try:
                    num = int(val)
                except ValueError:
                    return f"99acres 'budget_min' value '{val}' is not numeric"
                limit_max = 500000000 if flow == "buy" else 500000
                if not (1000 <= num <= limit_max):
                    flow_str = "buy" if flow == "buy" else "rent"
                    limit_str = "₹50Cr" if flow == "buy" else "₹5L"
                    return f"99acres budget_min ₹{num} is out of plausible range for {flow_str} (₹1K - {limit_str})"
                    
            # Check budget_max
            if budget_max_param:
                val = budget_max_param[0]
                try:
                    num = int(val)
                except ValueError:
                    return f"99acres 'budget_max' value '{val}' is not numeric"
                limit_max = 500000000 if flow == "buy" else 500000
                if not (1000 <= num <= limit_max):
                    flow_str = "buy" if flow == "buy" else "rent"
                    limit_str = "₹50Cr" if flow == "buy" else "₹5L"
                    return f"99acres budget_max ₹{num} is out of plausible range for {flow_str} (₹1K - {limit_str})"
                    
        return None
        
    except Exception as e:
        return f"Unexpected structural parsing error: {str(e)}"

def check_liveness(url: str) -> tuple[int | None, str | None]:
    """
    Performs an HTTP HEAD request with a 2-second timeout and custom User-Agent.
    Returns (status_code, error_message).
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        with urllib.request.urlopen(req, timeout=2.0) as response:
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
    intent = state.get("intent") or "rent"
    
    trace = state.get("trace")
    span = create_span(trace, "url_validator", generated_urls)
    
    # Track dropped info for internal diagnostics
    dropped_info: dict[str, str] = {}
    valid_struct_urls = []
    
    # 2. Step 1: Structural Checks
    for url in generated_urls:
        error = validate_url_structure(url, intent)
        if error:
            print(f"[URL Validator] URL '{url}' failed structural checks: {error}")
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
                        portal_name = "NoBroker" if "nobroker.in" in url.lower() else "99acres"
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
                        print(f"[URL Validator] URL '{url}' failed liveness check: {fail_reason}")
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

