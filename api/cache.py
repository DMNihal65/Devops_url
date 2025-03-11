import os
import json
import redis
from typing import Optional, Any

# Get Redis URL from environment variable or use a default
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Redis client
redis_client = redis.from_url(REDIS_URL)

def get_cache(key: str) -> Optional[Any]:
    """Get a value from the cache."""
    data = redis_client.get(key)
    if data:
        return json.loads(data)
    return None

def set_cache(key: str, value: Any, expiration: int = 3600) -> None:
    """Set a value in the cache with expiration in seconds."""
    redis_client.setex(key, expiration, json.dumps(value))

def delete_cache(key: str) -> None:
    """Delete a value from the cache."""
    redis_client.delete(key)

def increment_counter(key: str) -> int:
    """Increment a counter in Redis."""
    return redis_client.incr(key) 