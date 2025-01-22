import sys
import yaml
from os.path import dirname, abspath
from flask import Flask, request, jsonify
from flasgger import Swagger
from os.path import join, dirname

from services import initialize_cache, authenticate, setup_logger

from utils import fetch_multiple_ticker_data, normalize_text


sys.path.insert(0, dirname(abspath(__file__)))

# Inicialização do app e serviços
app = Flask(__name__)
cache = initialize_cache(app)
logger = setup_logger()


# Swagger configuration
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
swagger_docs = {"swagger": "2.0", "info": {"title": "API Documentation", "version": "1.0"}, "paths": {}}
for doc_name in ['fetch_stock_info', 'fetch_market_price', 'classify_assets', 'fetch_asset_info']:
    file_path = join(dirname(__file__), f"docs/{doc_name}.yaml")
    try:
        with open(file_path, 'r') as file:
            doc_content = yaml.safe_load(file)
            if doc_content and "paths" in doc_content:
                swagger_docs["paths"].update(doc_content["paths"])
            else:
                logger.error(f"Invalid or empty YAML content in {file_path}")
    except Exception as e:
        logger.error(f"Error loading YAML file {file_path}: {e}")

swagger = Swagger(app, config=swagger_config, template=swagger_docs)


@app.before_request
def apply_auth():
    return authenticate()


@app.route('/fetch_stock_info', methods=['POST'])
@cache.cached(timeout=60, query_string=True)
def fetch_stock_info():
    # Endpoint para buscar informações detalhadas de múltiplos tickers.
    # Recebe uma lista de tickers no corpo da requisição.
    # Retorna informações completas de cada ticker, como nome e detalhes.
    data = request.get_json()
    tickers = data.get('tickers')

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    tickers_data = fetch_multiple_ticker_data(tickers)
    results = {}

    for ticker, stock in tickers_data.items():
        try:
            info = stock.info
            results[ticker] = info
        except Exception as e:
            logger.error(f"Error fetching information for ticker: {ticker}. Error: {str(e)}")
            results[ticker] = {'error': str(e)}

    return jsonify(results)



@app.route('/fetch_market_price', methods=['POST'])
@cache.cached(timeout=60)
def fetch_market_price():
    # Endpoint para buscar o preço de mercado atual de múltiplos tickers.
    # Recebe uma lista de tickers no corpo da requisição.
    # Retorna o ticker e o preço de mercado correspondente.
    data = request.get_json()
    tickers = data.get('tickers', [])

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    tickers_data = fetch_multiple_ticker_data(tickers)
    results = []

    for ticker, stock in tickers_data.items():
        try:
            info = stock.info
            price = info.get('currentPrice', None)
            if price is None:
                results.append({"ticker": ticker, "error": "Price not found"})
                continue

            results.append({
                "ticker": ticker,
                "price": price
            })
        except Exception as e:
            logger.error(f"Error fetching information for ticker: {ticker}. Error: {str(e)}")
            results.append({"ticker": ticker, "error": str(e)})

    return jsonify(results)


@app.route('/classify_assets', methods=['POST'])
def classify_assets():
    # Endpoint para classificar ativos em categorias como FII, ETF ou UNIT.
    # Verifica atributos específicos nos dados do ticker para determinar a categoria.
    # Retorna o ticker, nome e a categoria identificada para cada ativo.
    data = request.get_json()
    tickers = data.get('tickers', [])

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    tickers_data = fetch_multiple_ticker_data(tickers)
    results = []

    for ticker, stock in tickers_data.items():
        try:
            info = stock.info
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

    return jsonify(results)


@app.route('/fetch_asset_info', methods=['POST'])
def fetch_asset_info():
    # Endpoint para buscar informações detalhadas sobre ativos.
    # Retorna dados como o nome completo, nome curto, descrição e tipo do ativo (quoteType).
    # Útil para identificar informações resumidas e gerais dos ativos.
    data = request.get_json()
    tickers = data.get('tickers', [])

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    tickers_data = fetch_multiple_ticker_data(tickers)
    results = []

    for ticker, stock in tickers_data.items():
        try:
            info = stock.info
            results.append({
                "ticker": ticker,
                "longName": info.get("longName", "N/A"),
                "shortName": info.get("shortName", "N/A"),
                "longBusinessSummary": info.get("longBusinessSummary", "N/A"),
                "quoteType": info.get("quoteType", "N/A"),
            })
        except Exception as e:
            logger.error(f"Error fetching asset info for ticker: {ticker}. Error: {str(e)}")
            results.append({"ticker": ticker, "error": str(e)})

    return jsonify(results)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
