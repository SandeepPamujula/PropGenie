import os
from typing import Any
from pymongo import MongoClient

_client: Any = None


def set_db_client(client: Any) -> None:
    """Sets the global database client. Useful for testing."""
    global _client
    _client = client


def get_db_client() -> Any:
    """
    Returns a connection-pooled MongoDB client.
    Reads MONGODB_URI from environment variables.
    """
    global _client
    if _client is None:
        mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/propgenie")
        max_pool_size = int(os.environ.get("MONGODB_MAX_POOL_SIZE", "50"))
        
        # We pass maxPoolSize for connection pooling
        _client = MongoClient(mongo_uri, maxPoolSize=max_pool_size)
        
    return _client


def get_database() -> Any:
    """
    Returns the MongoDB database instance.
    """
    client = get_db_client()
    mongo_uri = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/propgenie")
    db_name = "propgenie"
    if hasattr(client, "PORT") or (type(client).__name__ == "MongoClient" and "mongomock" in type(client).__module__):
        # Under mongomock, let's just return a default db name
        db_name = "propgenie_test"
    else:
        try:
            from urllib.parse import urlparse
            parsed = urlparse(mongo_uri)
            path = parsed.path.strip("/")
            if path:
                db_name = path.split("?")[0]
        except Exception:
            parts = mongo_uri.split("/")
            if len(parts) > 3:
                last_part = parts[-1].split("?")[0]
                if last_part:
                    db_name = last_part

    db = client[db_name]
    init_indexes(db)
    return db



def init_indexes(db: Any) -> None:
    """
    Creates indexes programmatically:
    - TTL index on sessions.last_active (expire after 1800s)
    - Regular index on sessions.ip
    - Compound unique index on rate_limits [ip, date]
    - TTL index on rate_limits.expires_at
    - Regular indexes on search_logs (timestamp, city, intent)
    """
    # Create TTL index on last_active
    db.sessions.create_index("last_active", expireAfterSeconds=1800)
    # Create regular index on ip
    db.sessions.create_index("ip")
    
    # Create compound unique index for rate limits
    db.rate_limits.create_index([("ip", 1), ("date", 1)], unique=True)
    # Create TTL index for automatic cleanup of rate limits
    db.rate_limits.create_index("expires_at", expireAfterSeconds=0)
    
    # Create indexes for search analytics
    db.search_logs.create_index("timestamp")
    db.search_logs.create_index("city")
    db.search_logs.create_index("intent")
