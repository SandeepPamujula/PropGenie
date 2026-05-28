import ipaddress
import logging
from datetime import datetime, timezone, timedelta

from db.connection import get_database
from utils.constants import RateLimitConfig
from utils.logger import get_ip_hash_short

logger = logging.getLogger(__name__)

class RateLimitException(Exception):
    """Raised when an IP exceeds its daily rate limit."""
    pass

# Alias for backward compatibility
RateLimitExceededException = RateLimitException

def clean_ip(ip: str) -> str:
    """Strips port and brackets from IPv4/IPv6 addresses if present."""
    if not ip:
        return "127.0.0.1"
    ip = ip.strip()
    
    # Try parsing the IP directly. If it succeeds, it's already a clean IP.
    try:
        ipaddress.ip_address(ip)
        return ip
    except ValueError:
        pass
        
    # If not, let's strip brackets or split by colon
    if ip.startswith("[") and "]" in ip:
        cleaned = ip.split("]")[0][1:]
        try:
            ipaddress.ip_address(cleaned)
            return cleaned
        except ValueError:
            pass
            
    # Try splitting by colon from the right to strip port
    if ":" in ip:
        parts = ip.rsplit(":", 1)
        cleaned = parts[0]
        if cleaned.startswith("[") and cleaned.endswith("]"):
            cleaned = cleaned[1:-1]
        try:
            ipaddress.ip_address(cleaned)
            return cleaned
        except ValueError:
            pass
            
    return ip

def get_today_ist_string() -> str:
    """Returns today's date in IST (UTC+5:30) as a string (YYYY-MM-DD)."""
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = datetime.now(timezone.utc) + ist_offset
    return ist_time.strftime("%Y-%m-%d")

def get_next_ist_midnight_string() -> str:
    """Returns tomorrow's midnight IST string for the reset_at field."""
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = datetime.now(timezone.utc) + ist_offset
    tomorrow_ist = (ist_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return tomorrow_ist.isoformat()

def check_rate_limit(ip: str) -> None:
    """
    Checks if the given IP has exceeded the daily rate limit.
    Fails open if MongoDB connection fails.
    Raises RateLimitException if limit is exceeded.
    """
    cleaned = clean_ip(ip)
    ip_hash = get_ip_hash_short(cleaned)
    today_ist = get_today_ist_string()
    
    try:
        db = get_database()
        rate_limit_doc = db.rate_limits.find_one({"ip": cleaned, "date": today_ist})
        
        if rate_limit_doc and rate_limit_doc.get("count", 0) >= RateLimitConfig.MAX_DAILY_SEARCHES:
            logger.warning(f"[RATE_LIMIT_EXCEEDED] IP hash {ip_hash} exceeded daily limit of {RateLimitConfig.MAX_DAILY_SEARCHES}.")
            raise RateLimitException(f"Rate limit exceeded for IP")
            
    except RateLimitException:
        raise
    except Exception as e:
        logger.error(f"Failed to check rate limit for IP hash {ip_hash}. Error: {e}. Allowing request (fail-open).")
        # Fail open, so we do nothing and allow it to proceed
        pass

def increment_rate_limit(ip: str) -> None:
    """
    Increments the daily search counter for the given IP.
    Uses an atomic upsert with a 2-day TTL on expires_at.
    """
    cleaned = clean_ip(ip)
    ip_hash = get_ip_hash_short(cleaned)
    today_ist = get_today_ist_string()
    now_utc = datetime.now(timezone.utc)
    
    # Calculate midnight IST for today, then add 2 days
    ist_offset = timedelta(hours=5, minutes=30)
    ist_time = now_utc + ist_offset
    expires_at_ist = (ist_time + timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    # Convert expires_at back to UTC since MongoDB TTL indexes work best with UTC datetime objects
    expires_at_utc = expires_at_ist - ist_offset
    
    try:
        db = get_database()
        db.rate_limits.update_one(
            {"ip": cleaned, "date": today_ist},
            {
                "$inc": {"count": 1},
                "$set": {
                    "last_incremented": now_utc,
                    "expires_at": expires_at_utc
                }
            },
            upsert=True
        )
    except Exception as e:
        logger.error(f"Failed to increment rate limit for IP hash {ip_hash}. Error: {e}")

