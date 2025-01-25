from flask import Flask, request, jsonify
from flasgger import Swagger
from config import create_cache
from auth_service import validate_token
from cache_service import get_from_cache, set_to_cache
from logging_service import setup_logger
from services.yahoo_service import fetch_ticker_data
from fii_verification import verificar_fundo_investimento
import yfinance as yf

# Inicialização do app e serviços
app = Flask(__name__)
cache = create_cache(app)
logger = setup_logger()

# Configuração do Flasgger
swagger_config = {
    "headers": [],
    "specs": [
        {
            "endpoint": "apispec",
            "route": "/apispec.json",
            "rule_filter": lambda rule: True,
            "model_filter": lambda tag: True,
        }
    ],
    "swagger_ui": True,
    "specs_route": "/docs/",
}
swagger = Swagger(app, config=swagger_config)

@app.before_request
def authenticate():
    """
    Middleware para validar o token antes de processar qualquer endpoint.
    """
    logger.info(f"Request path: {request.path}, Method: {request.method}")

    if request.path.startswith("/docs") or request.path.startswith("/apispec.json"):
        logger.info("Documentation access allowed without authentication")
        return  # Libera o acesso aos endpoints de documentação sem autenticação

    token = request.headers.get("Authorization")
    if not token:
        logger.info("Token is missing in the request")
        return jsonify({"error": "Token is required"}), 401

    if not validate_token(token):
        logger.info("Invalid or expired token provided")
        return jsonify({"error": "Invalid or expired token"}), 403

@app.route('/fii-check', methods=['POST'])
def check_fii():
    """
    Verifica se um ativo é um fundo de investimento imobiliário.
    ---
    parameters:
      - name: ticker
        in: body
        type: string
        required: true
        description: O ticker do ativo
    responses:
      200:
        description: Sucesso
        schema:
          type: object
          properties:
            ticker:
              type: string
            longName:
              type: string
            quoteType:
              type: string
            fii:
              type: boolean
      400:
        description: Requisição inválida
      500:
        description: Erro no servidor
    """
    data = request.get_json()
    ticker = data.get('ticker', '').strip().upper()

    if not ticker:
        return jsonify({"error": "Ticker is required"}), 400

    cache_key = f"fii-check:{ticker}"
    cached_result = get_from_cache(cache, cache_key)
    if cached_result:
        logger.info(f"Cache hit for ticker: {ticker}")
        return jsonify(cached_result)

    try:
        logger.info(f"Fetching data from Yahoo Finance for ticker: {ticker}")
        info = fetch_ticker_data(ticker)

        if not info or "quoteType" not in info:
            logger.error(f"Invalid response for ticker: {ticker}. Data: {info}")
            return jsonify({"error": f"No valid data found for ticker {ticker}"}), 404

        is_fii = verificar_fundo_investimento(info)

        response = {
            "ticker": ticker,
            "longName": info.get("longName", None),
            "quoteType": info.get("quoteType", None),
            "fii": is_fii
        }

        set_to_cache(cache, cache_key, response)
        return jsonify(response)
    except Exception as e:
        logger.error(f"Error checking FII for ticker: {ticker}. Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/fii-check-batch', methods=['POST'])
def check_fii_batch():
    """
    Verifica uma lista de ativos e determina se são fundos de investimento imobiliário.
    ---
    parameters:
      - name: tickers
        in: body
        type: array
        items:
          type: string
        required: true
        description: Lista de tickers
    responses:
      200:
        description: Sucesso
      400:
        description: Requisição inválida
      500:
        description: Erro no servidor
    """
    data = request.get_json()
    tickers = data.get('tickers', [])

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    results = []
    for ticker in tickers:
        ticker = ticker.strip().upper()
        cache_key = f"fii-check:{ticker}"
        cached_result = get_from_cache(cache, cache_key)

        if cached_result:
            logger.info(f"Cache hit for ticker: {ticker}")
            results.append(cached_result)
            continue

        try:
            logger.info(f"Fetching data from Yahoo Finance for ticker: {ticker}")
            info = fetch_ticker_data(ticker)

            if not info or "quoteType" not in info:
                logger.error(f"Invalid data for ticker: {ticker}")
                results.append({"ticker": ticker, "error": "No valid data found"})
                continue

            is_fii = verificar_fundo_investimento(info)

            result = {
                "ticker": ticker,
                "longName": info.get("longName", None),
                "quoteType": info.get("quoteType", None),
                "fii": is_fii
            }

            set_to_cache(cache, cache_key, result)
            results.append(result)

        except Exception as e:
            logger.error(f"Error checking FII for ticker: {ticker}. Error: {str(e)}")
            results.append({"ticker": ticker, "error": str(e)})

    return jsonify(results)

@app.route('/ticker', methods=['POST'])
@cache.cached(timeout=300, query_string=True)
def get_stock_info():
    """
    Obtém informações completas sobre um ticker.
    ---
    parameters:
      - name: ticker
        in: body
        type: string
        required: true
        description: O ticker do ativo
    responses:
      200:
        description: Sucesso
      400:
        description: Requisição inválida
      500:
        description: Erro no servidor
    """
    data = request.get_json()
    ticker = data.get('ticker')

    if not ticker:
        return jsonify({'error': 'Ticker is required'}), 400

    try:
        logger.info(f"Request received for ticker: {ticker}")
        stock = yf.Ticker(ticker)

        stock.history(period="1d")
        info = stock.info
        logger.info(f"Successfully fetched information for ticker: {ticker}")
        return jsonify(info)
    except Exception as e:
        logger.error(f"Error fetching information for ticker: {ticker}. Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/tickers', methods=['POST'])
@cache.cached(timeout=300, query_string=True)
def get_multiple_stock_info():
    """
    Obtém informações de vários tickers.
    ---
    parameters:
      - name: tickers
        in: body
        type: array
        items:
          type: string
        required: true
        description: Lista de tickers
    responses:
      200:
        description: Sucesso
      400:
        description: Requisição inválida
      500:
        description: Erro no servidor
    """
    data = request.get_json()
    tickers = data.get('tickers')

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    results = {}
    for ticker in tickers:
        try:
            logger.info(f"Fetching information for ticker: {ticker}")
            stock = yf.Ticker(ticker)
            stock.history(period="1d")
            info = stock.info
            results[ticker] = info
        except Exception as e:
            logger.error(f"Error fetching information for ticker: {ticker}. Error: {str(e)}")
            results[ticker] = {'error': str(e)}

    return jsonify(results)

@app.route('/preco_medio', methods=['POST'])
@cache.cached(timeout=300)
def add_sa_and_fetch():
    """
    Adiciona .SA ao final de cada string de uma lista, busca no Yahoo Finance e retorna nome e preço.
    ---
    parameters:
      - name: tickers
        in: body
        type: array
        items:
          type: string
        required: true
        description: Lista de tickers sem o sufixo .SA
    responses:
      200:
        description: Sucesso
      400:
        description: Requisição inválida
      500:
        description: Erro no servidor
    """
    data = request.get_json()
    tickers = data.get('tickers', [])

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    results = []
    for ticker in tickers:
        ticker_sa = f"{ticker.strip().upper()}.SA"

        try:
            logger.info(f"Fetching information for ticker: {ticker_sa}")
            stock = yf.Ticker(ticker_sa)
            stock.history(period="1d")  # Verifica se o ticker existe e é válido
            price = stock.info.get('currentPrice')

            if price is None:
                logger.warning(f"No price available for ticker: {ticker_sa}")
                results.append({"ticker": ticker, "error": "Price not found"})
                continue

            results.append({
                "ticker": ticker,  # Nome sem o .SA
                "price": price
            })
        except Exception as e:
            logger.error(f"Error fetching information for ticker: {ticker_sa}. Error: {str(e)}")
            results.append({"ticker": ticker, "error": str(e)})

    return jsonify(results)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
