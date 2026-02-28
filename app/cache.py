import redis
from app.config import settings

# ─── Redis Client ─────────────────────────────────────────────────────────────
# decode_responses=True means Redis returns strings instead of bytes
print(settings.redis_host, settings.redis_port)
redis_client = redis.Redis(
    host=settings.redis_host,
    port=settings.redis_port,
    ssl=True,
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
)
print(redis_client)
CACHE_PREFIX = "url:"  # Redis keys look like "url:3xK9mP"


def cache_get(short_code: str) -> str | None:
    """
    Look up a short code in Redis.
    Returns the long URL if found, or None if it's not cached.
    
    This is the FAST PATH — takes ~0.1ms vs ~5ms for a DB query.
    """
    key = f"{CACHE_PREFIX}{short_code}"
    return redis_client.get(key)


def cache_set(short_code: str, long_url: str, ttl: int = settings.cache_ttl_seconds):
    """
    Store a short_code → long_url mapping in Redis with a TTL (expiry time).
    After TTL seconds, Redis automatically deletes the key.
    
    TTL prevents Redis from filling up with stale data.
    Popular links will be re-cached on next access.
    """
    key = f"{CACHE_PREFIX}{short_code}"
    redis_client.setex(key, ttl, long_url)


def cache_delete(short_code: str):
    """Remove a URL from cache (used when a URL is deleted)."""
    key = f"{CACHE_PREFIX}{short_code}"
    redis_client.delete(key)


def cache_ping() -> bool:
    """Check if Redis is reachable — used in health check endpoint."""
    try:
        return redis_client.ping()
    except Exception:
        return False