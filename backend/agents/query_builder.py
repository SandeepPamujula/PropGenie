import json
import re
from datetime import datetime, timezone
from typing import Any
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage
from observability.langfuse_tracer import (
    create_span,
    end_span,
    LLAMA_3_1_70B_INPUT_COST_PER_TOKEN,
    LLAMA_3_1_70B_OUTPUT_COST_PER_TOKEN
)
from models.state import AgentState
from utils.config_loader import load_portal_configs

# System Prompt for Location-to-Locality Mapping LLM
LOCALITY_MAPPING_PROMPT = """You are the Location Resolver Agent for PropGenie, an AI property search assistant in India.
Your job is to resolve a user's local landmark or locality (location anchor) and city into the precise, URL-compatible locality identifiers for the portals "NoBroker" and "99acres".

You must return a strictly valid JSON object with keys "nobroker" and "99acres".

Resolution rules:
1. "nobroker":
   - This must be a JSON object containing:
     - "locality": the capitalized, URL-friendly locality name (e.g., "Indiranagar", "HSR-Layout", "Whitefield", "Bandra", "Worli", "Connaught-Place", "Dwarka", "Gachibowli", "Salt-Lake"). Do NOT include the city name here unless it's part of the locality name.
     - "placeName": a human-readable display name for the locality (e.g., "Indiranagar", "HSR Layout", "Whitefield", "Bandra West", "Worli", "Connaught Place", "Dwarka", "Gachibowli", "Salt Lake City").
     - "lat": approximate latitude decimal coordinate (e.g. 12.9783692)
     - "lon": approximate longitude decimal coordinate (e.g. 77.6408356)
     - "placeId": Google Maps Place ID for this locality/landmark. If you know the exact Google Place ID (e.g., "ChIJkQN3GKQWrjsRNhBQJrhGD7U" for Indiranagar), return it. Otherwise, output a plausible unique Google place ID format (e.g., starting with "ChIJ" followed by 23 alphanumeric characters).
   - If no specific locality is specified or it cannot be resolved, return null.

2. "99acres":
   - This should be the lowercase, hyphenated locality slug appended with the city name (e.g., "indiranagar-bangalore", "hsr-layout-bangalore", "bandra-west-mumbai", "connaught-place-delhi", "gachibowli-hyderabad", "salt-lake-kolkata").
   - If no specific locality is specified or it cannot be resolved, return null.

Examples:
- City: "Bangalore", Location Anchor: "NPS Indiranagar"
  Output: {{"nobroker": {{"locality": "Indiranagar", "placeName": "Indiranagar", "lat": 12.9783692, "lon": 77.6408356, "placeId": "ChIJkQN3GKQWrjsRNhBQJrhGD7U"}}, "99acres": "indiranagar-bangalore"}}
- City: "Bangalore", Location Anchor: "HSR Layout"
  Output: {{"nobroker": {{"locality": "HSR-Layout", "placeName": "HSR Layout", "lat": 12.9141, "lon": 77.6413, "placeId": "ChIJ5_q2v0sUrjsR5Lz3mZt3P1Y"}}, "99acres": "hsr-layout-bangalore"}}
- City: "Mumbai", Location Anchor: "Juhu Beach"
  Output: {{"nobroker": {{"locality": "Juhu", "placeName": "Juhu", "lat": 19.1075, "lon": 72.8263, "placeId": "ChIJ2e2-v3sUrjsR6Lz3mZt3P2A"}}, "99acres": "juhu-mumbai"}}

Input:
- City: "{city}"
- Location Anchor: "{location_anchor}"

Return ONLY a JSON object. Do not include any explanations or markdown formatting outside the JSON.
"""

def extract_json(text: str) -> dict[str, Any]:
    """
    Robustly extracts and parses JSON content from the LLM's raw text response.
    """
    text_clean = text.strip()
    
    # Try finding markdown JSON block
    match = re.search(r"```json\s*(.*?)\s*```", text_clean, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            res = json.loads(match.group(1).strip())
            if isinstance(res, dict):
                return res
        except json.JSONDecodeError:
            pass
            
    # Try finding any triple backticks block
    match = re.search(r"```\s*(.*?)\s*```", text_clean, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            res = json.loads(match.group(1).strip())
            if isinstance(res, dict):
                return res
        except json.JSONDecodeError:
            pass
            
    # Try parsing the whole text
    try:
        res = json.loads(text_clean)
        if isinstance(res, dict):
            return res
    except json.JSONDecodeError:
        pass
        
    # Find first '{' and last '}' and parse that segment
    start = text_clean.find("{")
    end = text_clean.rfind("}")
    if start != -1 and end != -1:
        try:
            res = json.loads(text_clean[start:end + 1])
            if isinstance(res, dict):
                return res
        except json.JSONDecodeError:
            pass
            
    raise ValueError(f"Could not parse valid JSON from LLM response: {text}")

def query_builder_node(state: AgentState) -> dict[str, Any]:
    """
    Builds parameterized URLs for all target portals using resolved localities and configs.
    """
    import time
    print("[Query Builder Agent] Started execution")
    start_time = time.time()
    
    resolved_entities = {
        "city": state.get("city"),
        "location_anchor": state.get("location_anchor"),
        "property_type": state.get("property_type"),
        "bhk": state.get("bhk"),
        "budget_min": state.get("budget_min"),
        "budget_max": state.get("budget_max"),
        "radius_km": state.get("radius_km")
    }
    
    trace = state.get("trace")
    span = create_span(trace, "query_builder", resolved_entities)
    
    updates: dict[str, Any] = {}
    
    # 2. Apply defaults before URL construction
    # Default radius = 4 km if not specified
    radius_km = state.get("radius_km")
    if radius_km is None:
        radius_km = 4
        updates["radius_km"] = 4
        
    # Default budget floor = 0 if not specified
    budget_min = state.get("budget_min")
    if budget_min is None:
        budget_min = 0
        updates["budget_min"] = 0
        
    budget_max = state.get("budget_max")
    
    # 3. Perform location-to-locality mapping using Bedrock LLM if anchor is present
    location_anchor = state.get("location_anchor")
    city = state.get("city")
    
    resolved_localities = {"nobroker": None, "99acres": None}
    
    if location_anchor and city:
        try:
            prompt = LOCALITY_MAPPING_PROMPT.format(
                city=city,
                location_anchor=location_anchor
            )
            
            # Initialize Bedrock Client
            import os
            model_id = os.environ.get("BEDROCK_MODEL_ID", "us.meta.llama3-1-70b-instruct-v1:0")
            region_name = os.environ.get("AWS_REGION", "us-east-1")
            llm = ChatBedrock(  # type: ignore[call-arg]
                model_id=model_id,
                region_name=region_name,
                model_kwargs={"temperature": 0.0}
            )
            
            # Invoke model
            response = llm.invoke([SystemMessage(content=prompt)])
            content = response.content if hasattr(response, "content") else response
            response_text = str(content).strip()
            print(f"[Query Builder Agent] LLM Raw Mapping Response: {response_text}")
            
            # Accumulate usage statistics
            updates["llm_calls"] = state.get("llm_calls", 0) + 1
            if hasattr(response, "response_metadata") and "usage" in response.response_metadata:
                usage = response.response_metadata["usage"]
                updates["total_input_tokens"] = state.get("total_input_tokens", 0) + usage.get("input_tokens", 0)
                updates["total_output_tokens"] = state.get("total_output_tokens", 0) + usage.get("output_tokens", 0)
            elif hasattr(response, "usage_metadata") and response.usage_metadata:
                usage = response.usage_metadata
                updates["total_input_tokens"] = state.get("total_input_tokens", 0) + usage.get("input_tokens", 0)
                updates["total_output_tokens"] = state.get("total_output_tokens", 0) + usage.get("output_tokens", 0)
            
            extracted = extract_json(response_text)
            resolved_localities["nobroker"] = extracted.get("nobroker")
            resolved_localities["99acres"] = extracted.get("99acres")
            
        except Exception as e:
            print(f"[Query Builder Agent] Error resolving locality via LLM: {e}")
            updates["error"] = f"Locality mapping LLM invocation failed: {str(e)}"
            
    # 4. Build parameterized URLs for each portal using static configs
    generated_urls = []
    
    try:
        portal_configs = load_portal_configs()
    except Exception as e:
        print(f"[Query Builder Agent] Error loading portal configs: {e}")
        updates["error"] = f"Failed to load portal configs: {str(e)}"
        portal_configs = {}
        
    for portal_id, portal_config in portal_configs.items():
        if not city:
            continue
            
        city_lower = city.lower()
        
        # Skip gracefully if city is not in slug map
        city_slug = portal_config.city_slug_map.get(city_lower)
        if not city_slug:
            print(f"[Query Builder Agent] Skipping portal '{portal_id}' - city '{city}' not supported.")
            continue
            
        # Determine intent flow
        intent = state.get("intent")
        flow = "rent"
        if intent is not None and str(intent).strip().lower() == "buy":
            flow = "buy"
            
        # Build portal-specific filters
        filters: dict[str, Any] = {}
        
        # BHK
        bhk_val = state.get("bhk")
        property_type = state.get("property_type")
        property_type_lower = property_type.lower() if property_type else None
        if bhk_val is not None and not (portal_id == "nobroker" and property_type_lower == "plot"):
            filters["bhk"] = [str(bhk_val)]
            
        # Price/Budget normalization per portal
        budget_max_val = budget_max
        if budget_max_val is None:
            # Set high upper bounds to prevent None values being stringified
            if flow == "buy":
                budget_max_val = 500000000  # 50 Crores
            else:
                budget_max_val = 500000  # 5 Lakhs
                
        resolved_loc = resolved_localities.get(portal_id)
        resolved_loc_str = None
        if resolved_loc:
            if isinstance(resolved_loc, dict):
                resolved_loc_str = resolved_loc.get("locality")
            else:
                resolved_loc_str = str(resolved_loc)
                
        if portal_id == "nobroker":
            filters["price_range"] = [budget_min, budget_max_val]
            filters["city_name"] = city_lower
            if isinstance(resolved_loc, dict):
                locality = resolved_loc.get("locality")
                lat = resolved_loc.get("lat")
                lon = resolved_loc.get("lon")
                place_id = resolved_loc.get("placeId")
                place_name = resolved_loc.get("placeName") or locality
                
                if locality:
                    filters["locality_name"] = locality
                if lat is not None and lon is not None:
                    import base64
                    param_obj = [{
                        "lat": float(lat),
                        "lon": float(lon),
                        "placeId": place_id or "ChIJdummyLocationID12345678",
                        "placeName": place_name or "Location"
                    }]
                    json_str = json.dumps(param_obj, separators=(',', ':'))
                    search_param_b64 = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
                    filters["search_param"] = search_param_b64
                    filters["radius"] = float(radius_km)
            elif resolved_loc_str:
                filters["locality_name"] = resolved_loc_str
        elif portal_id == "99acres":
            filters["price_min"] = budget_min
            if budget_max is not None:
                filters["price_max"] = budget_max
                
        # Property type support and mapping
        if property_type_lower:
            if portal_id == "nobroker":
                # NoBroker does not support plots for rent (only buy flow)
                if property_type_lower == "plot" and flow != "buy":
                    print("[Query Builder Agent] Skipping NoBroker - 'plot' property type not supported for rent.")
                    continue
                    
                # Map standard property_type to building_type
                building_type = None
                if property_type_lower == "apartment":
                    building_type = ["apartment"]
                elif property_type_lower in ["house", "independent house", "villa"]:
                    building_type = ["independent"]
                elif property_type_lower == "gated_community":
                    building_type = ["gated_community"]
                    
                if building_type:
                    filters["building_type"] = building_type
                    
        # Construct parameterized URL
        original_buy_template = None
        is_plot_buy = (portal_id == "nobroker" and flow == "buy" and property_type_lower == "plot")
        if is_plot_buy:
            original_buy_template = portal_config.buy_url_template
            portal_config.buy_url_template = "{base_url}/property/plot/{city_slug}/{city_capitalized}"

        try:
            if resolved_loc_str:
                resolved_loc_lower = resolved_loc_str.lower()
                if portal_id == "nobroker":
                    # Temporarily add resolved locality to city slug map to capitalise in path segment
                    portal_config.city_slug_map[resolved_loc_lower] = city_slug
                    url = portal_config.generate_url(flow=flow, city=resolved_loc_lower, filters=filters)
                elif portal_id == "99acres":
                    # Temporarily add resolved locality-inclusive slug to city slug map
                    portal_config.city_slug_map[resolved_loc_lower] = resolved_loc_lower
                    url = portal_config.generate_url(flow=flow, city=resolved_loc_lower, filters=filters)
            else:
                # Fallback to default city URL
                url = portal_config.generate_url(flow=flow, city=city_lower, filters=filters)
                
            generated_urls.append(url)
            
        except Exception as e:
            print(f"[Query Builder Agent] Error building URL for portal '{portal_id}': {e}")
            
        finally:
            if is_plot_buy and original_buy_template is not None:
                portal_config.buy_url_template = original_buy_template
            # Clean up temporary keys in city_slug_map
            if resolved_loc_str:
                resolved_loc_lower = resolved_loc_str.lower()
                if resolved_loc_lower in portal_config.city_slug_map:
                    if resolved_loc_lower not in ["bangalore", "mumbai", "pune", "chennai", "hyderabad", "delhi"]:
                        del portal_config.city_slug_map[resolved_loc_lower]
                        
    updates["generated_urls"] = generated_urls
    print(f"[Query Builder Agent] Completed. Generated URLs: {generated_urls}")
    
    # End Langfuse span
    latency_ms = int((time.time() - start_time) * 1000)
    init_input_tokens = state.get("total_input_tokens", 0)
    init_output_tokens = state.get("total_output_tokens", 0)
    added_input_tokens = updates.get("total_input_tokens", init_input_tokens) - init_input_tokens
    added_output_tokens = updates.get("total_output_tokens", init_output_tokens) - init_output_tokens
    
    metrics = {
        "latency": latency_ms,
        "input_tokens": added_input_tokens,
        "output_tokens": added_output_tokens,
        "total_tokens": added_input_tokens + added_output_tokens,
        "cost": added_input_tokens * LLAMA_3_1_70B_INPUT_COST_PER_TOKEN + added_output_tokens * LLAMA_3_1_70B_OUTPUT_COST_PER_TOKEN
    }
    
    end_span(span, generated_urls, metrics)
    
    return updates

