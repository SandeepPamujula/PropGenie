import logging
from datetime import datetime, timezone, timedelta

from db.connection import get_database

logger = logging.getLogger(__name__)

class RateLimitExceededException(Exception):
    """Raised when an IP exceeds its daily rate limit."""
    pass

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
    Checks if the given IP has exceeded the daily rate limit (10 searches/day).
    Fails open if MongoDB connection fails.
    Raises RateLimitExceededException if limit is exceeded.
    """
    today_ist = get_today_ist_string()
    
    try:
        db = get_database()
        rate_limit_doc = db.rate_limits.find_one({"ip": ip, "date": today_ist})
        
        if rate_limit_doc and rate_limit_doc.get("count", 0) >= 10:
            logger.warning(f"[RATE_LIMIT_EXCEEDED] IP {ip} exceeded daily limit of 10.")
            raise RateLimitExceededException(f"Rate limit exceeded for IP {ip}")
            
    except RateLimitExceededException:
        raise
    except Exception as e:
        logger.error(f"Failed to check rate limit for IP {ip}. Error: {e}. Allowing request (fail-open).")
        # Fail open, so we do nothing and allow it to proceed
        pass
