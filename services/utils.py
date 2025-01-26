import unicodedata
import yfinance as yf
import logging
from services.cache_service import get_cached_tickers, cache_ticker_data

logger = logging.getLogger(__name__)

def ensure_sa_suffix(tickers):
    """
    Adiciona o sufixo '.SA' aos tickers que não possuem.
    """
    return [ticker.strip().upper() + ".SA" if not ticker.strip().upper().endswith(".SA") else ticker.strip().upper() for ticker in tickers]

def fetch_multiple_ticker_data(tickers, cache, timeout=300):
    """
    Busca os dados de múltiplos tickers. Primeiro verifica o cache,
    e para os tickers ausentes, busca no Yahoo Finance e salva no cache.

    Args:
        tickers (list): Lista de tickers a serem buscados.
        cache (Cache): Instância do cache.
        timeout (int): Tempo para expiração do cache em segundos (default: 300).

    Returns:
        dict: Um dicionário com os dados serializáveis dos tickers.
    """

    logger.info("Fetching data for multiple tickers.")
    normalized_tickers = ensure_sa_suffix(tickers)

    cached_data, missing_tickers = get_cached_tickers(cache, normalized_tickers)
    
    # Se todos os tickers já estiverem no cache, retorna diretamente
    if not missing_tickers:
        logger.info("All tickers found in cache.")
        return cached_data
    
    # Busca os tickers faltantes no Yahoo Finance
    logger.info(f"Fetching data for missing tickers from Yahoo: {missing_tickers}")
    tickers_with_sa = ensure_sa_suffix(tickers)
    yf_tickers = yf.Tickers(" ".join(tickers_with_sa))
    
    # Processa os resultados do Yahoo Finance
    fetched_data = {}
    for ticker, stock in yf_tickers.tickers.items():
        try:
            stock.history(period="1d")  # Verifica se o ticker é válido
            fetched_data[ticker] = serialize_stock_data(stock)
        except Exception as e:
            logger.error(f"Error fetching data for ticker {ticker}: {str(e)}")

    # Salva os dados buscados no cache
    cache_ticker_data(cache, fetched_data, timeout=timeout)

    # Combina os dados do cache com os dados recém-buscados
    combined_data = {**cached_data, **fetched_data}
    return combined_data


def normalize_text(text):
    """Remove acentos e converte o texto para minúsculas."""
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    ).lower()

def classify_asset_list(results, tickers_data, fetched_data=None):
    """
    Classifica os ativos em categorias como FII, ETF ou UNIT e atualiza os resultados.
    """
    fetched_data = fetched_data or {}
    
    for ticker, data in tickers_data.items():
        try:
            # Acessar o campo `info` dos dados serializáveis
            info = data.get("info", {})

            # Normalizar textos
            long_name = normalize_text(info.get("longName", "N/A"))
            short_name = normalize_text(info.get("shortName", "N/A"))
            long_business_summary = normalize_text(info.get("longBusinessSummary", "N/A"))

            # Listas de palavras-chave
            fii_keywords = ["fii", "imobiliario", "fundo de investimento imobiliario", "fiagro"]
            etf_keywords = ["index", "ishare", "etf", "indice"]
            unit_keywords = ["unt", "unit"]

            # Campos a verificar
            campos_verificar = [long_name, short_name]

            # Classificação por categoria
            category = "Unknown"
            if any(term in campo for campo in campos_verificar for term in fii_keywords):
                category = "FII"
            elif any(term in campo for campo in campos_verificar for term in etf_keywords):
                category = "ETF"
            elif any(term in campo for campo in campos_verificar for term in unit_keywords):
                category = "UNIT"

            # Armazenar o resultado processado
            fetched_data[ticker] = data  # Atualiza os dados no cache (se necessário)
            results.append({
                "ticker": ticker,
                "shortName": short_name,
                "longName": long_name,
                "longBusinessSummary": long_business_summary,
                "category": category
            })
        except Exception as e:
            logger.error(f"Error classifying ticker: {ticker}. Error: {str(e)}")
            results.append({"ticker": ticker, "error": "Processing error", "exception": str(e)})


def serialize_stock_data(stock):
    """
    Serializa os dados de um objeto `yfinance.Ticker` para um formato armazenável e reutilizável.

    Args:
        stock (yfinance.Ticker): Objeto Ticker retornado pelo yfinance.

    Returns:
        dict: Dados serializáveis do ticker.
    """
    try:
        return {
            "info": stock.info,
            "recommendations": stock.recommendations.to_dict() if hasattr(stock, "recommendations") else [],
            "price_targets": stock.analyst_price_targets if hasattr(stock, "analyst_price_targets") else {},
            "growth_estimates": stock.growth_estimates if hasattr(stock, "growth_estimates") else {}
        }
    except Exception as e:
        logger.error(f"Error serializing stock data: {str(e)}")
        return {}
