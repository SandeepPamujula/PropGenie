import json
import re
from datetime import datetime, timezone
from typing import Any
from langchain_aws import ChatBedrock
from langchain_core.messages import SystemMessage
from langfuse.decorators import observe, langfuse_context
from models.state import AgentState
from utils.config_loader import load_portal_configs

# System Prompt for Location-to-Locality Mapping LLM
LOCALITY_MAPPING_PROMPT = """You are the Location Resolver Agent for PropGenie, an AI property search assistant in India.
Your job is to resolve a user's local landmark or locality (location anchor) and city into the precise, URL-compatible locality identifiers for the portals "NoBroker" and "99acres".

You must return a strictly valid JSON object with keys "nobroker" and "99acres".

Resolution rules:
1. "nobroker":
   - This should be the capitalized, URL-friendly locality name (e.g., "Indiranagar", "HSR-Layout", "Whitefield", "Bandra", "Worli", "Connaught-Place", "Dwarka", "Gachibowli", "Salt-Lake").
   - Do NOT include the city name here unless it's part of the locality name.
   - If no specific locality is specified or it cannot be resolved, return null.

2. "99acres":
   - This should be the lowercase, hyphenated locality slug appended with the city name (e.g., "indiranagar-bangalore", "hsr-layout-bangalore", "bandra-west-mumbai", "connaught-place-delhi", "gachibowli-hyderabad", "salt-lake-kolkata").
   - If no specific locality is specified or it cannot be resolved, return null.

Examples:
- City: "Bangalore", Location Anchor: "NPS Indiranagar"
  Output: {{"nobroker": "Indiranagar", "99acres": "indiranagar-bangalore"}}
- City: "Bangalore", Location Anchor: "HSR Layout"
  Output: {{"nobroker": "HSR-Layout", "99acres": "hsr-layout-bangalore"}}
- City: "Mumbai", Location Anchor: "Juhu Beach"
  Output: {{"nobroker": "Juhu", "99acres": "juhu-mumbai"}}
- City: "Delhi", Location Anchor: "Connaught Place"
  Output: {{"nobroker": "Connaught-Place", "99acres": "connaught-place-delhi"}}
- City: "Pune", Location Anchor: "Koregaon Park"
  Output: {{"nobroker": "Koregaon-Park", "99acres": "koregaon-park-pune"}}

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

@observe(name="query_builder")  # type: ignore[misc]
def query_builder_node(state: AgentState) -> dict[str, Any]:
    """
    Builds parameterized URLs for all target portals using resolved localities and configs.
    """
    print("[Query Builder Agent] Started execution")
    
    # 1. Update trace metadata in Langfuse
    langfuse_context.update_current_trace(
        session_id=state.get("session_id"),
        user_id=state.get("ip"),
        tags=["propgenie", "query_builder"]
    )
    
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
        if bhk_val is not None:
            filters["bhk"] = [str(bhk_val)]
            
        # Price/Budget normalization per portal
        budget_max_val = budget_max
        if budget_max_val is None:
            # Set high upper bounds to prevent None values being stringified
            if flow == "buy":
                budget_max_val = 500000000  # 50 Crores
            else:
                budget_max_val = 500000  # 5 Lakhs
                
        if portal_id == "nobroker":
            filters["price_range"] = [budget_min, budget_max_val]
        elif portal_id == "99acres":
            filters["price_min"] = budget_min
            if budget_max is not None:
                filters["price_max"] = budget_max
                
        # Property type support and mapping
        property_type = state.get("property_type")
        if property_type:
            property_type_lower = property_type.lower()
            if portal_id == "nobroker":
                # NoBroker does not support plots
                if property_type_lower == "plot":
                    print("[Query Builder Agent] Skipping NoBroker - 'plot' property type not supported.")
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
        resolved_loc = resolved_localities.get(portal_id)
        
        try:
            if resolved_loc:
                resolved_loc_lower = resolved_loc.lower()
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
            # Clean up temporary keys in city_slug_map
            if resolved_loc:
                resolved_loc_lower = resolved_loc.lower()
                if resolved_loc_lower in portal_config.city_slug_map:
                    if resolved_loc_lower not in ["bangalore", "mumbai", "pune", "chennai", "hyderabad", "delhi"]:
                        del portal_config.city_slug_map[resolved_loc_lower]
                        
    updates["generated_urls"] = generated_urls
    print(f"[Query Builder Agent] Completed. Generated URLs: {generated_urls}")
    
    return updates

