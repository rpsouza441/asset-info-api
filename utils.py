import unicodedata
import yfinance as yf
import logging

logger = logging.getLogger(__name__)

def ensure_sa_suffix(tickers):
    """
    Adiciona o sufixo '.SA' aos tickers que não possuem.
    """
    return [ticker.strip().upper() + ".SA" if not ticker.strip().upper().endswith(".SA") else ticker.strip().upper() for ticker in tickers]

def fetch_multiple_ticker_data(tickers):
    """
    Busca os dados de múltiplos tickers de uma só vez usando yfinance.
    """
    logger.info("Fetching data for multiple tickers.")
    tickers_with_sa = ensure_sa_suffix(tickers)
    yf_tickers = yf.Tickers(" ".join(tickers_with_sa))
    return yf_tickers.tickers

def normalize_text(text):
    """Remove acentos e converte o texto para minúsculas."""
    return ''.join(
        c for c in unicodedata.normalize('NFKD', text)
        if not unicodedata.combining(c)
    ).lower()

def classify_asset_list(results, tickers_data, fetched_data=None):
    fetched_data = fetched_data or {}


    for ticker, info in tickers_data.items():
        try:
                # Normalizar textos
            long_name = normalize_text(info.get("longName", "N/A"))
            short_name = normalize_text(info.get("shortName", "N/A"))
            long_business_summary = normalize_text(info.get("longBusinessSummary", "N/A"))

                # Listas de palavras-chave
            fii_keywords = ["fii", "imobiliario", "imobiliario", "fundo de investimento imobiliario", "fiagro"]
            etf_keywords = ["index", "ishare", "etf", "indice"]
            unit_keywords = ["unt", "unit"]

                # Campos a verificar
            campos_verificar = [long_name, short_name, long_business_summary]   

                # Classificação por categoria
            category = "Unknown"
            if any(term in campo for campo in campos_verificar for term in fii_keywords):
                category = "FII"
            elif any(term in campo for campo in campos_verificar for term in etf_keywords):
                category = "ETF"
            elif any(term in campo for campo in campos_verificar for term in unit_keywords):
                category = "UNIT"

            fetched_data[ticker] = info
            results.append({
                    "ticker": ticker,
                    "shortName": short_name,
                    "longName": long_name,
                    "longBusinessSummary": long_business_summary,
                    "category": category
                })
        except Exception as e:
            logger.error(f"Error classifying ticker: {ticker}. Error: {str(e)}")
            results.append({"ticker": ticker, "error": str(e)})
