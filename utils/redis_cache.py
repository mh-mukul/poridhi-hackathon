import os
import redis
import hashlib
from dotenv import load_dotenv

load_dotenv()
# Load Redis configuration from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

# Initialize Redis
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0)


def get_query_cache_key(collection_name: str, query: str, limit: int) -> str:
    """Generate a Redis cache key based on collection, query, and limit."""
    normalized_query = query.strip().lower()
    query_hash = hashlib.sha256(
        f"{collection_name}:{normalized_query}:{limit}".encode('utf-8')
    ).hexdigest()
    return f"search_cache:{query_hash}"
