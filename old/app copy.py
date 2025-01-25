from flask import Flask, request, jsonify
import logging
import yfinance as yf
from datetime import datetime
from flask_caching import Cache  # Importa o cache
from tokens import tokens  # Importa a lista de tokens

app = Flask(__name__)

# Configuração do cache com Redis
cache_config = {
    "CACHE_TYPE": "RedisCache",        # Define Redis como backend do cache
    "CACHE_REDIS_HOST": "redis",       # Nome do serviço no Docker Compose
    "CACHE_REDIS_PORT": 6379,          # Porta padrão do Redis
    "CACHE_REDIS_DB": 0,               # Banco de dados Redis (padrão é 0)
    "CACHE_REDIS_PASSWORD": None,      # Senha do Redis, se necessário
    "CACHE_DEFAULT_TIMEOUT": 1800      # Tempo de expiração do cache (30 minutos)
}
app.config.from_mapping(cache_config)
cache = Cache(app)

# Configuração de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def validate_token(token):
    """
    Valida o token recebido.
    """
    for entry in tokens:
        if entry["token"] == token:
            if entry["expiry"] >= datetime.now():
                return True
    return False

@app.before_request
def authenticate():
    """
    Middleware para validar o token antes de processar qualquer endpoint.
    """
    if request.endpoint in ["static"]:  # Permite acesso livre a recursos estáticos
        return

    # Obtém o token do cabeçalho Authorization
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"error": "Token is required"}), 401

    if not validate_token(token):
        return jsonify({"error": "Invalid or expired token"}), 403

def verificar_fundo_investimento(dados_ticker):
    """
    Verifica se o ativo está relacionado a um fundo de investimento imobiliário ou Fiagro.
    """
    palavras_chave = ["fundo de investimento imobiliário", "imobiliário", "imobiliario", "fundo de investimento imobiliario"]
    campos_verificar = [
        dados_ticker.get("longBusinessSummary", "").lower(),
        dados_ticker.get("longName", "").lower(),
        dados_ticker.get("shortName", "").lower(),
    ]
    for campo in campos_verificar:
        if any(palavra in campo for palavra in palavras_chave):
            return True
    return False

@app.route('/fii-check', methods=['POST'])
@cache.cached(timeout=1800, query_string=True)  # Cache por 30 minutos
def check_fii():
    """
    Endpoint para verificar se um ativo é um fundo de investimento imobiliário.
    """
    data = request.get_json()
    ticker = data.get('ticker')

    if not ticker:
        return jsonify({'error': 'Ticker is required'}), 400

    try:
        logger.info(f"Request received for FII check: {ticker}")
        stock = yf.Ticker(ticker)

        # Força a atualização dos dados
        stock.history(period="1d")
        info = stock.info

        # Verifica se é FII
        is_fii = verificar_fundo_investimento(info)

        # Retorna os dados solicitados
        response = {
            "longName": info.get("longName", None),
            "symbol": info.get("symbol", None),
            "quoteType": info.get("quoteType", None),
            "fii": is_fii
        }

        logger.info(f"FII check completed for ticker: {ticker}")
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error checking FII for ticker: {ticker}. Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/fii-check-batch', methods=['POST'])
@cache.cached(timeout=1800, query_string=True)  # Cache por 30 minutos
def check_fii_batch():
    """
    Endpoint para verificar uma lista de ativos e determinar se são fundos de investimento imobiliário.
    """
    data = request.get_json()
    tickers = data.get('tickers')

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    results = []

    for ticker in tickers:
        try:
            logger.info(f"Request received for FII check: {ticker}")
            stock = yf.Ticker(ticker)

            # Força a atualização dos dados
            stock.history(period="1d")
            info = stock.info

            # Verifica se é FII
            is_fii = verificar_fundo_investimento(info)

            # Adiciona o resultado para este ticker
            results.append({
                "ticker": ticker,
                "longName": info.get("longName", None),
                "symbol": info.get("symbol", None),
                "quoteType": info.get("quoteType", None),
                "fii": is_fii
            })

        except Exception as e:
            logger.error(f"Error checking FII for ticker: {ticker}. Error: {str(e)}")
            results.append({
                "ticker": ticker,
                "error": str(e)
            })

    return jsonify(results)

@app.route('/ticker', methods=['POST'])
@cache.cached(timeout=1800, query_string=True)  # Cache por 30 minutos
def get_stock_info():
    """
    Endpoint para obter informações completas sobre um ticker.
    """
    data = request.get_json()
    ticker = data.get('ticker')

    if not ticker:
        return jsonify({'error': 'Ticker is required'}), 400

    try:
        logger.info(f"Request received for ticker: {ticker}")
        stock = yf.Ticker(ticker)

        # Força a atualização dos dados
        stock.history(period="1d")
        info = stock.info

        # Retorna os dados completos do ticker
        logger.info(f"Successfully fetched information for ticker: {ticker}")
        return jsonify(info)

    except Exception as e:
        logger.error(f"Error fetching information for ticker: {ticker}. Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/tickers', methods=['POST'])
@cache.cached(timeout=1800, query_string=True)  # Cache por 30 minutos
def get_multiple_stock_info():
    """
    Endpoint para obter informações de vários tickers.
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

            # Força a atualização dos dados
            stock.history(period="1d")
            info = stock.info
            results[ticker] = info
        except Exception as e:
            logger.error(f"Error fetching information for ticker: {ticker}. Error: {str(e)}")
            results[ticker] = {'error': str(e)}

    return jsonify(results)

if __name__ == '__main__':
    # Inicializa o servidor Flask
    app.run(host='0.0.0.0', port=80, debug=True)
