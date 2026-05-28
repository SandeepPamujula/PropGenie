class URLValidatorConstants:
    """
    Constants for search and property URL validation.
    """
    TIMEOUT_LIVENESS = 2.0
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    NOBROKER_DOMAIN = "nobroker.in"
    ACRES_DOMAIN = "99acres.com"
    
    NOBROKER_MIN_PATH_SEGMENTS = 5
    ACRES_MIN_PATH_SEGMENTS = 2
    
    ACRES_CITY_PATTERN = r"^[a-zA-Z0-9-]+-(?:bangalore|mumbai|pune|chennai|hyderabad|delhi-ncr|delhi)$"
    
    # Plausible budget ranges
    RENT_MIN = 1000
    RENT_MAX = 500000
    BUY_MIN = 1000
    BUY_MAX = 500000000
    
    # Intent / parameters
    FLOW_RENT = "rent"
    FLOW_BUY = "buy"
    NOBROKER_RENT_PARAM = "rent"
    NOBROKER_PRICE_PARAM = "price"
    ACRES_BUDGET_MIN_PARAM = "budget_min"
    ACRES_BUDGET_MAX_PARAM = "budget_max"
    
    PATH_SEGMENT_SALE = "sale"
    PATH_SEGMENT_PLOT = "plot"
    PREFIX_PROPERTY_RENT = "/property/rent/"
    PREFIX_PROPERTY_SALE = "/property/sale/"
    PREFIX_PROPERTY_PLOT = "/property/plot/"


class PropertyScraperConstants:
    """
    Constants for property HTML scraping and parsing.
    """
    TIMEOUT_DEFAULT = 5.0
    MAX_PROPERTIES_DEFAULT = 5
    PORTAL_LIMIT = 5
    
    ENV_ENABLE_SCRAPING = "ENABLE_PROPERTY_SCRAPING"
    ENV_TIMEOUT = "PROPERTY_SCRAPING_TIMEOUT"
    ENV_MAX_PROPERTIES = "MAX_SCRAPED_PROPERTIES"
    
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ACCEPT_HEADER = "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
    
    NOBROKER_DOMAIN = "nobroker.in"
    ACRES_DOMAIN = "99acres.com"
    
    NOBROKER_MIN_PATH_SEGMENTS = 5
    ACRES_MIN_PATH_SEGMENTS = 2
    
    ACRES_CITY_PATTERN = r"^[a-zA-Z0-9-]+-(?:bangalore|mumbai|pune|chennai|hyderabad|delhi-ncr|delhi)$"
    
    PREFIX_PROPERTY_RENT = "/property/rent/"
    PREFIX_PROPERTY_SALE = "/property/sale/"
    PREFIX_PROPERTY_PLOT = "/property/plot/"
    PORTAL_NOBROKER = "NoBroker"
    PORTAL_99ACRES = "99acres"


class RateLimitConfig:
    """
    Constants for API rate limiting.
    """
    MAX_DAILY_SEARCHES = 10



