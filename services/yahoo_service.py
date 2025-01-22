import yfinance as yf

def fetch_ticker_data(ticker):
    """
    Busca informações de um ticker no Yahoo Finance.
    Valida se os dados retornados são válidos.
    """
    try:
        stock = yf.Ticker(ticker)
        stock.history(period="1d")  # Força a atualização
        info = stock.info

        # Verifica se os dados básicos estão presentes
        if not info or "quoteType" not in info:
            raise ValueError(f"Invalid data returned for ticker: {ticker}")

        return info
    except Exception as e:
        raise ValueError(f"Error fetching data for ticker {ticker}: {str(e)}")
