import sys
import yaml
from os.path import dirname, abspath
from flask import Flask, request, jsonify
from flasgger import Swagger
from os.path import join, dirname

from services import authenticate, setup_logger, initialize_cache, get_cached_tickers, cache_ticker_data

from utils import fetch_multiple_ticker_data, classify_asset_list


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
def fetch_stock_info():
    # Endpoint para buscar informações detalhadas de múltiplos tickers.
    # Recebe uma lista de tickers no corpo da requisição.
    # Retorna informações completas de cada ticker, como nome e detalhes.
    data = request.get_json()
    tickers = data.get('tickers')

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    cached_data, missing_tickers = get_cached_tickers(cache, tickers)
    results = {}

    # Busca no Yahoo para os tickers ausentes
    if missing_tickers:
        logger.info(f"Fetching stock info for missing tickers from Yahoo: {missing_tickers}")
        tickers_data = fetch_multiple_ticker_data(missing_tickers)
        fetched_data = {}

        for ticker, stock in tickers_data.items():
            try:
                info = stock.info
                fetched_data[ticker] = info
                results[ticker] = info
            except Exception as e:
                logger.error(f"Error fetching information for ticker: {ticker}. Error: {str(e)}")
                results[ticker] = {'error': str(e)}

        # Armazenar os dados no cache
        cache_ticker_data(cache, fetched_data)

    # Adicionar dados do cache aos resultados
    for ticker, data in cached_data.items():
        logger.info(f"Fetching stock info for ticker {ticker} from cache.")
        results[ticker] = data

    return jsonify(results)



@app.route('/fetch_market_price', methods=['POST'])
def fetch_market_price():
    # Endpoint para buscar o preço de mercado atual de múltiplos tickers.
    # Recebe uma lista de tickers no corpo da requisição.
    # Retorna o ticker e o preço de mercado correspondente.
    data = request.get_json()
    tickers = data.get('tickers', [])

    if not tickers or not isinstance(tickers, list):
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    cached_data, missing_tickers = get_cached_tickers(cache, tickers)
    results = []

    # Busca no Yahoo para os tickers ausentes
    if missing_tickers:
        logger.info(f"Fetching market price for missing tickers from Yahoo: {missing_tickers}")
        tickers_data = fetch_multiple_ticker_data(missing_tickers)
        fetched_data = {}

        for ticker, stock in tickers_data.items():
            try:
                info = stock.info
                price = info.get('currentPrice', None)
                if price is None:
                    results.append({"ticker": ticker, "error": "Price not found"})
                else:
                    fetched_data[ticker] = {"price": price}
                    results.append({"ticker": ticker, "price": price})
            except Exception as e:
                logger.error(f"Error fetching market price for ticker: {ticker}. Error: {str(e)}")
                results.append({"ticker": ticker, "error": str(e)})

        # Armazenar os dados no cache
        cache_ticker_data(cache, fetched_data, timeout=60)

    # Adicionar dados do cache aos resultados
    for ticker, data in cached_data.items():
        logger.info(f"Fetching market price for ticker {ticker} from cache.")
        results.append({"ticker": ticker, "price": data.get("price"), "cached": True})

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

    cached_data, missing_tickers = get_cached_tickers(cache, tickers)
    results = []

     # Busca no Yahoo para os tickers ausentes
    if missing_tickers:
        logger.info(f"Classifying missing tickers from Yahoo: {missing_tickers}")
        tickers_data = fetch_multiple_ticker_data(missing_tickers)
        fetched_data = {}

        classify_asset_list(results, {ticker: stock.info for ticker, stock in tickers_data.items()}, fetched_data)
        
        # Armazenar os dados no cache
        cache_ticker_data(cache, fetched_data)

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

    # Dicionário para armazenar todas as informações (cache + Yahoo)
    all_tickers_data = {}

    # Verificar o cache
    cached_data, missing_tickers = get_cached_tickers(cache, tickers)
    logger.info(f"Fetching asset info for cached tickers: {list(cached_data.keys())}")

    # Adicionar os dados do cache ao dicionário
    all_tickers_data.update(cached_data)

    # Buscar informações dos tickers ausentes no Yahoo Finance
    if missing_tickers:
        logger.info(f"Fetching missing tickers from Yahoo: {missing_tickers}")
        tickers_data = fetch_multiple_ticker_data(missing_tickers)

        for ticker, stock in tickers_data.items():
            try:
                info = stock.info
                all_tickers_data[ticker] = info
            except Exception as e:
                logger.error(f"Error fetching asset info for ticker: {ticker}. Error: {str(e)}")
                all_tickers_data[ticker] = {"error": str(e)}

        # Armazenar os dados buscados no cache
        cache_ticker_data(cache, {ticker: data for ticker, data in all_tickers_data.items() if ticker in missing_tickers})

    # Construir a lista de resultados
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
