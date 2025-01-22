import logging

def setup_logger():
    """
    Configura o logger para o app.
    """
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger(__name__)
