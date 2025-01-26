from flask_caching import Cache
import logging

logger = logging.getLogger(__name__)

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
    Retrieves a value from the cache, with error handling.
    """
    try:
        return cache.get(key)
    except Exception as e:
        logger.error(f"Error retrieving key '{key}' from cache: {str(e)}")
        return None

def set_to_cache(cache, key, value, timeout=300):
    """
    Stores a value in the cache, with error handling.
    """
    try:
        cache.set(key, value, timeout=timeout)
        logger.info(f"Key '{key}' successfully set in cache.")
    except Exception as e:
        logger.error(f"Error setting key '{key}' in cache: {str(e)}")

def get_cached_tickers(cache, tickers):
    """
    Retrieve cached stock objects for a list of tickers.
    Returns a tuple with two lists: cached_data and missing_tickers.

    Args:
        cache (Cache): Instância do cache.
        tickers (list): Lista de tickers fornecida pelo usuário.

    Returns:
        tuple: (cached_data, missing_tickers)
    """

    cached_data = {}
    missing_tickers = []


    for ticker in tickers:
        try:
            data = cache.get(ticker)
            if data:
                cached_data[ticker] = data
                logger.info(f"Cache hit for ticker: {ticker}")
            else:
                missing_tickers.append(ticker)
                logger.info(f"Cache miss for ticker: {ticker}")
        except Exception as e:
            logger.error(f"Error retrieving ticker {ticker} from cache: {str(e)}")
            missing_tickers.append(ticker)

    logger.info(f"Total tickers found in cache: {len(cached_data)}")
    logger.info(f"Total missing tickers: {len(missing_tickers)}")   

    return cached_data, missing_tickers

def cache_ticker_data(cache, ticker_data, timeout=300):
    """
    Salva dados serializáveis dos tickers no cache.

    Args:
        cache (Cache): Instância do cache.
        ticker_data (dict): Dados dos tickers no formato {ticker: serializable_data}.
        timeout (int): Tempo de expiração do cache em segundos (default: 300).
    """
    if not isinstance(ticker_data, dict):
        logger.error("Invalid ticker_data format. Expected a dictionary.")
        return

    for ticker, data in ticker_data.items():
        if data:  # Apenas cacheia dados válidos
            cache.set(ticker, data, timeout=timeout)
            logger.info(f"Cached data for ticker: {ticker}")
        else:
            logger.warning(f"Skipping caching for ticker {ticker} due to missing data.")

