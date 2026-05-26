import os
import time
import concurrent.futures
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from html.parser import HTMLParser
import re

from models.state import AgentState
from utils.constants import PropertyScraperConstants
from observability.langfuse_tracer import create_span, end_span
from agents.url_validator import validate_scraped_properties

class ALinkExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: List[str] = []

    def handle_starttag(self, tag: str, attrs: List[tuple[str, Optional[str]]]) -> None:
        if tag.lower() == "a":
            for attr, val in attrs:
                if attr.lower() == "href" and val:
                    self.links.append(val.strip())

def extract_properties_from_html(html: str, portal: str) -> List[str]:
    """
    Parses the HTML search results page and extracts property listing deep links.
    """
    parser = ALinkExtractor()
    try:
        parser.feed(html)
    except Exception as e:
        print(f"[Property Scraper] Error parsing HTML: {e}")
        return []
    
    extracted: List[str] = []
    seen = set()
    
    for href in parser.links:
        try:
            parsed = urlparse(href)
            netloc = parsed.netloc.lower()
            path = parsed.path
            
            if portal == "NoBroker":
                # Check domain compatibility (if specified, must contain nobroker.in)
                if netloc and PropertyScraperConstants.NOBROKER_DOMAIN not in netloc:
                    continue
                # Match /property/rent/<city>/<locality>/<property-id> 
                # or /property/sale/<city>/<locality>/<property-id>
                if path.startswith("/property/rent/") or path.startswith("/property/sale/"):
                    # We expect at least 3 segments after the prefix: e.g. city, locality, property-id
                    # path.split('/') yields ['', 'property', 'rent/sale', 'city', 'locality', 'property-id']
                    # removing empty strings leaves: ['property', 'rent/sale', 'city', 'locality', 'property-id'] (length >= 5)
                    parts = [p for p in path.split('/') if p]
                    if len(parts) >= PropertyScraperConstants.NOBROKER_MIN_PATH_SEGMENTS:
                        abs_url = href if netloc else f"https://www.nobroker.in{path}"
                        if abs_url not in seen:
                            seen.add(abs_url)
                            extracted.append(abs_url)
                            
            elif portal == "99acres":
                # Check domain compatibility (if specified, must contain 99acres.com)
                if netloc and PropertyScraperConstants.ACRES_DOMAIN not in netloc:
                    continue
                # Match /<locality>-<city>/.../<property-id>
                # The first non-empty segment must match locality-city slug pattern
                parts = [p for p in path.split('/') if p]
                if len(parts) >= PropertyScraperConstants.ACRES_MIN_PATH_SEGMENTS:
                    first_seg = parts[0]
                    if re.match(PropertyScraperConstants.ACRES_CITY_PATTERN, first_seg, re.IGNORECASE):
                        abs_url = href if netloc else f"https://www.99acres.com{path}"
                        if abs_url not in seen:
                            seen.add(abs_url)
                            extracted.append(abs_url)
        except Exception:
            continue
            
    return extracted

def fetch_url(url: str, timeout: float = 5.0) -> tuple[Optional[str], Optional[str]]:
    """
    Performs an HTTP GET request to fetch the HTML content.
    Returns (html_content, error_message).
    """
    headers = {
        "User-Agent": PropertyScraperConstants.USER_AGENT,
        "Accept": PropertyScraperConstants.ACCEPT_HEADER
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            if 200 <= status < 300:
                html_bytes = response.read()
                try:
                    return html_bytes.decode("utf-8"), None
                except UnicodeDecodeError:
                    return html_bytes.decode("latin-1"), None
            else:
                return None, f"HTTP status {status}"
    except urllib.error.HTTPError as e:
        return None, f"HTTPError {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return None, f"URLError: {e.reason}"
    except Exception as e:
        return None, f"Exception: {str(e)}"

def property_scraper_node(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph node to scrape individual property listing links from validated search page URLs.
    """
    print("[Property Scraper Agent] Started execution")
    start_time = time.time()
    
    # 1. Feature Flag Check
    enable_scraping = os.environ.get(PropertyScraperConstants.ENV_ENABLE_SCRAPING, "false").lower() == "true"
    if not enable_scraping:
        print(f"[Property Scraper Agent] Feature disabled ({PropertyScraperConstants.ENV_ENABLE_SCRAPING} != true)")
        return {
            "scraped_property_urls": [],
            "validated_property_urls": []
        }
        
    validated_urls = state.get("validated_urls", [])
    if not validated_urls:
        print("[Property Scraper Agent] No validated portal search URLs to scrape")
        return {
            "scraped_property_urls": [],
            "validated_property_urls": []
        }
        
    trace = state.get("trace")
    span = create_span(trace, "property_scraper", validated_urls)
    
    # Configuration
    timeout_str = os.environ.get(PropertyScraperConstants.ENV_TIMEOUT, str(PropertyScraperConstants.TIMEOUT_DEFAULT))
    try:
        timeout = float(timeout_str)
    except ValueError:
        timeout = PropertyScraperConstants.TIMEOUT_DEFAULT
        
    max_scraped_str = os.environ.get(PropertyScraperConstants.ENV_MAX_PROPERTIES, str(PropertyScraperConstants.MAX_PROPERTIES_DEFAULT))
    try:
        max_scraped = int(max_scraped_str)
    except ValueError:
        max_scraped = PropertyScraperConstants.MAX_PROPERTIES_DEFAULT
        
    scraped_results: List[Dict[str, Any]] = []
    
    # Fetch validated search URLs concurrently
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, len(validated_urls))) as executor:
        future_to_search = {
            executor.submit(fetch_url, item["url"], timeout): item for item in validated_urls
        }
        
        for future in concurrent.futures.as_completed(future_to_search):
            item = future_to_search[future]
            search_url = item["url"]
            portal = item["portal"]
            
            try:
                html_content, err = future.result()
                if err:
                    print(f"[Property Scraper Agent] Warning: Failed to fetch '{search_url}' ({portal}): {err}")
                    continue
                if not html_content:
                    print(f"[Property Scraper Agent] Warning: Empty HTML content returned for '{search_url}'")
                    continue
                    
                # Extract links
                links = extract_properties_from_html(html_content, portal)
                print(f"[Property Scraper Agent] Extracted {len(links)} raw property links from {portal}")
                
                # Take top 5 links per portal search URL
                portal_scraped_count = 0
                for link in links:
                    if portal_scraped_count >= PropertyScraperConstants.PORTAL_LIMIT:
                        break
                    scraped_results.append({
                        "url": link,
                        "portal": portal,
                        "source_search_url": search_url
                    })
                    portal_scraped_count += 1
            except Exception as e:
                print(f"[Property Scraper Agent] Warning: Exception scraping '{search_url}': {e}")
                
    # Cap total scraped results across all portals
    scraped_results = scraped_results[:max_scraped]
    
    # 2. Validation step
    search_urls = [item["url"] for item in validated_urls]
    validated_results = validate_scraped_properties(scraped_results, search_urls, trace)
    
    print(f"[Property Scraper Agent] Completed. Total scraped links: {len(scraped_results)}, Validated: {len(validated_results)}")
    
    # End Langfuse span
    latency_ms = int((time.time() - start_time) * 1000)
    metrics = {
        "latency": latency_ms,
        "scraped_count": len(scraped_results),
        "validated_count": len(validated_results),
        "urls": [item["url"] for item in scraped_results]
    }
    end_span(span, scraped_results, metrics)
    
    return {
        "scraped_property_urls": scraped_results,
        "validated_property_urls": validated_results
    }
