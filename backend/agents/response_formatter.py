import json
import os
from typing import Any
from observability.langfuse_tracer import create_span, end_span
from models.state import AgentState
from utils.constants import PropertyScraperConstants

def format_currency(value: int) -> str:
    """Formats an integer into Indian currency format (e.g. 1.5Cr, 25K)."""
    if value >= 10000000:
        val = value / 10000000
        return f"₹{val:g}Cr"
    elif value >= 100000:
        val = value / 100000
        return f"₹{val:g}L"
    elif value >= 1000:
        val = value / 1000
        return f"₹{val:g}K"
    return f"₹{value}"

def response_formatter_node(state: AgentState) -> dict[str, Any]:
    """
    Synthesizes search results into a clean, markdown chat response and portal cards.
    """
    import time
    print("[Response Formatter Agent] Started execution")
    start_time = time.time()
    
    validated_urls = state.get("validated_urls", [])
    intent = str(state.get("intent") or "rent").lower()
    
    trace = state.get("trace")
    span = create_span(trace, "response_formatter", validated_urls)
    city = state.get("city") or ""
    location_anchor = state.get("location_anchor") or ""
    property_type = state.get("property_type") or ""
    bhk = state.get("bhk")
    budget_min = state.get("budget_min")
    budget_max = state.get("budget_max")
    radius_km = state.get("radius_km")

    # Generate summary string
    parts = []
    if bhk is not None:
        parts.append(f"{bhk}BHK")
    if property_type:
        if property_type.lower() == "gated_community":
            parts.append("gated community")
        else:
            parts.append(property_type.lower())
            
    prop_desc = " ".join(parts) if parts else "properties"
    # Capitalize the first letter while keeping the rest as is (like BHK)
    prop_desc = prop_desc[:1].upper() + prop_desc[1:] if prop_desc else ""

    intent_str = "rentals" if intent == "rent" else "for sale"
    location_str = f"near {location_anchor}, {city}" if location_anchor else f"in {city}"
    
    budget_str = ""
    if budget_min is not None and budget_max is not None:
        if budget_min == 0:
            budget_str = f" — Up to {format_currency(budget_max)}"
        else:
            budget_str = f" — {format_currency(budget_min)} to {format_currency(budget_max)}"
    elif budget_max is not None:
        budget_str = f" — Up to {format_currency(budget_max)}"
    elif budget_min is not None and budget_min > 0:
        budget_str = f" — From {format_currency(budget_min)}"
        
    if intent == "rent" and budget_str:
        budget_str += "/mo"
        
    summary = f"{prop_desc} {intent_str} {location_str}{budget_str}"
    
    notes_parts = []
    if radius_km == 4:
        loc = location_anchor or city
        notes_parts.append(f"4 km radius applied around {loc}")
    if budget_min == 0:
        notes_parts.append("budget floor assumed as ₹0")
        
    notes = " and ".join(notes_parts)
    notes = notes[:1].upper() + notes[1:] if notes else ""

    validated_urls = state.get("validated_urls", [])
    formatted_urls = []
    
    scraped_props = state.get("scraped_property_urls", []) or []
    validated_props = state.get("validated_property_urls", []) or []
    enable_scraping = os.environ.get(PropertyScraperConstants.ENV_ENABLE_SCRAPING, "false").lower() == "true"
    
    for card in validated_urls:
        portal = card.get("portal", "")
        card_url = card.get("url")
        
        # Priority: NoBroker prioritized for rentals, 99acres for purchases
        priority = False
        if intent == "rent" and portal.lower() == "nobroker":
            priority = True
        elif intent == "buy" and portal.lower() == "99acres":
            priority = True
            
        property_links = []
        if enable_scraping:
            # Match property links for this portal card
            scraped_for_card = [s for s in scraped_props if s.get("source_search_url") == card_url]
            url_to_rank = {s["url"]: idx + 1 for idx, s in enumerate(scraped_for_card)}
            validated_for_card = [v for v in validated_props if v.get("source_search_url") == card_url]
            for val_prop in validated_for_card:
                property_links.append({
                    "url": val_prop["url"],
                    "portal": val_prop["portal"],
                    "rank": url_to_rank.get(val_prop["url"], 99),
                    "validation": val_prop["validation"]
                })
            property_links.sort(key=lambda x: x["rank"])
            
        formatted_card = {
            "type": "portal_card",
            "portal": portal,
            "priority": priority,
            "url": card_url,
            "summary": summary,
            "notes": notes,
            "validation": card.get("validation", {}),
            "property_links": property_links
        }
        formatted_urls.append(formatted_card)
        
    # Generate search meta to inject into the state
    generated = state.get("generated_urls", [])
    dropped = [url for url in generated if url not in [c["url"] for c in formatted_urls]]
    
    defaults_applied = []
    if radius_km == 4:
        defaults_applied.append("radius_km: 4")
    if budget_min == 0:
        defaults_applied.append("budget_min: 0")
        
    property_links_count = sum(len(c["property_links"]) for c in formatted_urls)
    
    search_meta = {
        "type": "search_meta",
        "portals_searched": len(generated),
        "portals_returned": len(formatted_urls),
        "portals_dropped": dropped,
        "property_links_count": property_links_count,
        "clarification_rounds": state.get("clarification_round", 0),
        "defaults_applied": defaults_applied
    }

    print(f"[Response Formatter Agent] Completed. Formatted {len(formatted_urls)} URLs.")
    
    # End Langfuse span
    latency_ms = int((time.time() - start_time) * 1000)
    metrics = {
        "latency": latency_ms
    }
    
    end_span(span, formatted_urls, metrics)
    
    return {
        "validated_urls": formatted_urls,
        "search_meta": search_meta,
        "search_completed": True
    }
