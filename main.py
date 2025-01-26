import sys
import yaml
from os.path import dirname, abspath
from flask import Flask, request, jsonify
from flasgger import Swagger
from os.path import join, dirname
import pandas as pd
from services import authenticate, setup_logger, initialize_cache, fetch_multiple_ticker_data, classify_asset_list



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
        logger.warning("Invalid request: 'tickers' is either missing or not a list.")
        return jsonify({'error': 'Tickers must be provided as a list'}), 400
    
    logger.info(f"Received request to fetch stock info for tickers: {tickers}")

    try:
        # Busca os dados (cache + Yahoo para tickers ausentes)
        logger.info("Fetching data using fetch_multiple_ticker_data.")
        tickers_data = fetch_multiple_ticker_data(tickers, cache)

          # Construir a resposta com os dados `info`
        results = []
        for ticker, data in tickers_data.items():
            try:
                if data and "info" in data:
                    # Adicionar apenas o campo `info` ao resultado
                    results.append(data["info"])
                    logger.info(f"Info retrieved for ticker {ticker}.")
                else:
                    logger.warning(f"No valid data found for ticker: {ticker}")
                    results.append({"ticker": ticker, "error": "No valid data found"})
            except Exception as e:
                logger.error(f"Error processing data for ticker {ticker}: {str(e)}")
                results.append({"ticker": ticker, "error": "Processing error", "exception": str(e)})

        logger.info(f"Successfully processed stock info for tickers: {tickers}")
        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error in fetch_stock_info: {str(e)}", exc_info=True)
        return jsonify({'error': f"Failed to fetch stock info: {str(e)}"}), 500



@app.route('/fetch_market_price', methods=['POST'])
def fetch_market_price():
    # Endpoint para buscar o preço de mercado atual de múltiplos tickers.
    # Recebe uma lista de tickers no corpo da requisição.
    # Retorna o ticker e o preço de mercado correspondente.
    data = request.get_json()
    tickers = data.get('tickers', [])

    if not tickers or not isinstance(tickers, list):
        logger.warning("Invalid request: 'tickers' is either missing or not a list.")
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    logger.info(f"Received request to fetch market prices for tickers: {tickers}")

    try:
        # Busca os dados (cache + Yahoo para tickers ausentes)
        logger.info("Fetching data using fetch_multiple_ticker_data.")
        tickers_data = fetch_multiple_ticker_data(tickers, cache)

        # Construir os resultados com os preços
        results = []
        for ticker, data in tickers_data.items():
            try:
                if data:
                    # Acessar diretamente os dados serializáveis
                    info = data.get("info", {})
                    price = info.get("currentPrice", None)

                    if price is not None:
                        logger.info(f"Price retrieved for ticker {ticker}: {price}")
                        results.append({"ticker": ticker, "price": price})
                    else:
                        logger.warning(f"Price not found for ticker: {ticker}")
                        results.append({"ticker": ticker, "error": "Price not found"})
                else:
                    logger.warning(f"No valid data found for ticker: {ticker}")
                    results.append({"ticker": ticker, "error": "No valid data found"})
            except Exception as e:
                logger.error(f"Error processing data for ticker {ticker}: {str(e)}")
                results.append({"ticker": ticker, "error": "Processing error", "exception": str(e)})

        logger.info("Market price fetch completed successfully.")
        return jsonify(results), 200
    except Exception as e:
        logger.error(f"Error in fetch_market_price: {str(e)}", exc_info=True)
        return jsonify({'error': f"Failed to fetch market prices: {str(e)}"}), 500


@app.route('/classify_assets', methods=['POST'])
def classify_assets():
    # Endpoint para classificar ativos em categorias como FII, ETF ou UNIT.
    # Verifica atributos específicos nos dados do ticker para determinar a categoria.
    # Retorna o ticker, nome e a categoria identificada para cada ativo.
    data = request.get_json()
    tickers = data.get('tickers', [])

    if not tickers or not isinstance(tickers, list):
        logger.warning("Invalid request: 'tickers' is either missing or not a list.")
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    logger.info(f"Received request to classify assets for tickers: {tickers}")

    try:
        # Busca dados dos tickers (cache + Yahoo para tickers ausentes)
        logger.info("Fetching data using fetch_multiple_ticker_data.")
        tickers_data = fetch_multiple_ticker_data(tickers, cache)

        # Processar os dados para classificar os ativos
        results = []
        logger.info("Classifying tickers into categories.")
        classify_asset_list(results, tickers_data)

        logger.info("Classification completed successfully.")
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in classify_assets: {str(e)}", exc_info=True)
        return jsonify({'error': f"Failed to classify assets: {str(e)}"}), 500


@app.route('/fetch_asset_info', methods=['POST'])
def fetch_asset_info():
    # Endpoint para buscar informações detalhadas sobre ativos.
    # Retorna dados como o nome completo, nome curto, descrição e tipo do ativo (quoteType).
    # Útil para identificar informações resumidas e gerais dos ativos.
    data = request.get_json()
    tickers = data.get('tickers', [])

    if not tickers or not isinstance(tickers, list):
        logger.warning("Invalid request: 'tickers' is either missing or not a list.")
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    logger.info(f"Received request to classify assets for tickers: {tickers}")

    if not tickers or not isinstance(tickers, list):
        logger.warning("Invalid request: 'tickers' is either missing or not a list.")
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    logger.info(f"Received request to fetch asset information for tickers: {tickers}")

    try:
        # Busca os dados (cache + Yahoo para tickers ausentes)
        logger.info("Fetching data using fetch_multiple_ticker_data.")
        tickers_data = fetch_multiple_ticker_data(tickers, cache)

        # Construir os resultados com as informações detalhadas
        results = []
        for ticker, data in tickers_data.items():
            try:
                if data:
                    # Acessar diretamente o dicionário serializável
                    info = data.get("info", {})
                    results.append({
                        "ticker": ticker,
                        "longName": info.get("longName", "N/A"),
                        "shortName": info.get("shortName", "N/A"),
                        "longBusinessSummary": info.get("longBusinessSummary", "N/A"),
                        "quoteType": info.get("quoteType", "N/A"),
                    })
                    logger.info(f"Information retrieved for ticker {ticker}.")
                else:
                    results.append({"ticker": ticker, "error": "No valid data found"})
                    logger.warning(f"No valid data found for ticker {ticker}.")
            except Exception as e:
                logger.error(f"Error processing data for ticker {ticker}: {str(e)}")
                results.append({"ticker": ticker, "error": "Processing error", "exception": str(e)})

        logger.info("Asset information fetch completed successfully.")
        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error in fetch_asset_info: {str(e)}", exc_info=True)
        return jsonify({'error': f"Failed to fetch asset information: {str(e)}"}), 500
    

@app.route('/fetch_recommendations', methods=['POST'])
def fetch_recommendations():
    # Endpoint para buscar informações detalhadas de recomendações de múltiplos tickers.
    # Recebe uma lista de tickers no corpo da requisição.
    # Retorna recomendações completas de cada ticker.
    data = request.get_json()
    tickers = data.get('tickers')

    if not tickers or not isinstance(tickers, list):
        logger.warning("Invalid request: 'tickers' is either missing or not a list.")
        return jsonify({'error': 'Tickers must be provided as a list'}), 400

    logger.info(f"Received request to fetch recommendations for tickers: {tickers}")

    try:
        # Busca os dados do cache e do Yahoo Finance
        logger.info("Fetching data using fetch_multiple_ticker_data.")
        tickers_data = fetch_multiple_ticker_data(tickers, cache)

        # Construir a resposta com os dados obtidos
        results = []
        for ticker, data in tickers_data.items():
            try:
                if data:
                    recommendations = data.get("recommendations", [])
                    price_targets = data.get("price_targets", {})
                    growth_estimates = data.get("growth_estimates", {})

                    # Verifica e converte DataFrames para listas de dicionários
                    if isinstance(recommendations, pd.DataFrame):
                        recommendations = recommendations.to_dict(orient="records")
                    if isinstance(growth_estimates, pd.DataFrame):
                        growth_estimates = growth_estimates.to_dict(orient="records")

                    results.append({
                        "ticker": ticker,
                        "recommendations": recommendations,
                        "price_targets": price_targets,
                        "growth_estimates": growth_estimates
                    })
                else:
                    logger.warning(f"No valid data found for ticker: {ticker}")
                    results.append({"ticker": ticker, "error": "No valid data found"})
            except Exception as e:
                logger.error(f"Error processing data for ticker {ticker}: {str(e)}")
                results.append({"ticker": ticker, "error": "Processing error", "exception": str(e)})

        logger.info(f"Successfully processed recommendations for tickers: {tickers}")
        return jsonify(results), 200

    except Exception as e:
        logger.error(f"Error in fetch_recommendations: {str(e)}", exc_info=True)
        return jsonify({'error': f"Failed to fetch recommendations: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
