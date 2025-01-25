def verificar_fundo_investimento(dados_ticker):
    """
    Verifica se o ativo é um fundo de investimento imobiliário ou Fiagro.

    Retorna:
      - True se for um FII
      - False se não for
      - None se os dados forem inválidos ou ausentes.
    """
    # Verifica se os dados são válidos
    if not dados_ticker or not isinstance(dados_ticker, dict):
        return None

    # Verifica se os campos essenciais estão presentes
    if not dados_ticker.get("quoteType") or not dados_ticker.get("longName"):
        return None

    # Palavras-chave para identificar FII
    palavras_chave = ["fundo de investimento imobiliário", "imobiliário", "imobiliario", "fiagro"]
    campos_verificar = [
        dados_ticker.get("longBusinessSummary", "").lower(),
        dados_ticker.get("longName", "").lower(),
        dados_ticker.get("shortName", "").lower(),
    ]

    # Busca pelas palavras-chave nos campos
    for campo in campos_verificar:
        if any(palavra in campo for palavra in palavras_chave):
            return True

    return False
