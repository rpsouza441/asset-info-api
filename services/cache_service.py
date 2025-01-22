from flask_caching import Cache

def create_cache(app):
    """
    Configures and creates a cache instance for the Flask app.
    """
    cache_config = {
        "CACHE_TYPE": "RedisCache",
        "CACHE_REDIS_HOST": "redis",  # Redis container hostname
        "CACHE_REDIS_PORT": 6379,
        "CACHE_REDIS_DB": 0,
        "CACHE_REDIS_PASSWORD": None,
        "CACHE_DEFAULT_TIMEOUT": 1800,  # 30 minutes timeout
    }
    app.config.from_mapping(cache_config)
    return Cache(app)

def initialize_cache(app):
    """
    Alias for create_cache to maintain backward compatibility.
    """
    return create_cache(app)

def get_from_cache(cache, key):
    """
    Retrieves a value from the cache.
    """
    return cache.get(key)

def set_to_cache(cache, key, value, timeout=300):
    """
    Stores a value in the cache.
    """
    cache.set(key, value, timeout=timeout)
