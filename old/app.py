from flask import Flask, request, jsonify
from flasgger import Swagger
from config import create_cache
from app.auth_service import validate_token
from app.cache_service import get_from_cache, set_to_cache
from app.logging_service import setup_logger
from app.yahoo_service import fetch_ticker_data
from app.fii_verification import verificar_fundo_investimento

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
    if request.endpoint in ["swagger_ui", "apispec"]:
        return  # Permite acesso aos endpoints do Swagger sem autenticação
    
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token is required"}), 401

    if not validate_token(token):
        return jsonify({"error": "Invalid or expired token"}), 403

@app.route('/fii-check', methods=['POST'])
def check_fii():
    """
    Endpoint para verificar se um ativo é um fundo de investimento imobiliário.
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

        # Valida o retorno do Yahoo Finance
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
    Endpoint para verificar uma lista de ativos e determinar se são fundos de investimento imobiliário.
    """
    data = request.get_json()
    tickers = data.get('tickers', [])

    # Valida se a lista de tickers foi fornecida corretamente
    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    results = []

    for ticker in tickers:
        ticker = ticker.strip().upper()  # Normaliza o ticker
        cache_key = f"fii-check:{ticker}"
        cached_result = get_from_cache(cache, cache_key)

        if cached_result:
            # Se o resultado estiver no cache
            logger.info(f"Cache hit for ticker: {ticker}")
            results.append(cached_result)
            continue

        try:
            # Busca os dados do Yahoo Finance
            logger.info(f"Fetching data from Yahoo Finance for ticker: {ticker}")
            info = fetch_ticker_data(ticker)

            # Valida se os dados retornados são válidos
            if not info or "quoteType" not in info:
                logger.error(f"Invalid data for ticker: {ticker}")
                results.append({"ticker": ticker, "error": "No valid data found"})
                continue

            # Verifica se é um FII
            is_fii = verificar_fundo_investimento(info)

            # Cria o resultado
            result = {
                "ticker": ticker,
                "longName": info.get("longName", None),
                "quoteType": info.get("quoteType", None),
                "fii": is_fii
            }

            # Armazena no cache
            set_to_cache(cache, cache_key, result)
            results.append(result)

        except Exception as e:
            # Em caso de erro, registra e retorna o erro no resultado
            logger.error(f"Error checking FII for ticker: {ticker}. Error: {str(e)}")
            results.append({"ticker": ticker, "error": str(e)})

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
