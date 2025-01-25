from flask_caching import Cache
from utils import ensure_sa_suffix

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

def get_cached_tickers(cache, tickers):
    """
    Retrieve cached data for a list of tickers.
    Returns a tuple with two lists: cached_data and missing_tickers.
    """
    cached_data = {}
    missing_tickers = []

    # Normalizar tickers para incluir o sufixo .SA
    normalized_tickers = ensure_sa_suffix(tickers)

    for ticker in normalized_tickers:
        data = cache.get(ticker)
        if data:
            cached_data[ticker] = data
        else:
            missing_tickers.append(ticker)
    
    return cached_data, missing_tickers

def cache_ticker_data(cache, ticker_data, timeout=300):
    """
    Caches data for multiple tickers.
    """
    for ticker, data in ticker_data.items():
        cache.set(ticker, data, timeout=timeout)
