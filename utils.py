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
