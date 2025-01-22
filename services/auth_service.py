from flask import request, jsonify
from tokens import tokens
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def validate_token(token):
    """
    Validates the provided token against the tokens list.
    """
    for entry in tokens:
        if entry["token"] == token and entry["expiry"] >= datetime.now():
            return True
    return False


def authenticate():
    """
    Middleware para validar o token antes de processar qualquer endpoint.
    """
    logger.info(f"Request path: {request.path}, Method: {request.method}")

    # Permitir acesso à documentação e arquivos estáticos
    if (
        request.path.startswith("/docs") or 
        request.path.startswith("/apispec.json") or 
        request.path.startswith("/static")
    ):
        logger.info("Documentation or static file access allowed without authentication")
        return  # Libera o acesso às rotas específicas sem autenticação

    # Verificar token para outras rotas
    token = request.headers.get("Authorization")
    if not token:
        logger.info("Token is missing in the request")
        return jsonify({"error": "Token is required"}), 401

    if not validate_token(token):
        logger.info("Invalid or expired token provided")
        return jsonify({"error": "Invalid or expired token"}), 403
