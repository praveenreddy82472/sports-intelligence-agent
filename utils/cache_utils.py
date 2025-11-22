import time
import logging

logger = logging.getLogger(__name__)

def ttl_cache(ttl=300):
    """Simple time-based cache decorator to avoid frequent API calls."""
    def decorator(func):
        cache = {}
        def wrapper(*args):
            key = args
            now = time.time()
            if key in cache:
                value, ts = cache[key]
                if now - ts < ttl:
                    logger.debug(f"[CACHE] Hit for {func.__name__} with args {args}")
                    return value
            result = func(*args)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator
