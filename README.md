# Asset Information API

## Visão Geral

A **Asset Information API** é uma solução desenvolvida em Python que fornece dados detalhados sobre ações e ativos financeiros. Com ela, você pode consultar preços de mercado, classificar ativos e obter informações completas. Construída com Flask e Flasgger, a API conta com autenticação baseada em token e uma interface interativa via Swagger UI.

## Funcionalidades

- **Recuperação de Informações Detalhadas:** Dados como preços, volumes e médias móveis de múltiplos tickers.
- **Consulta de Preços de Mercado:** Obtenha os preços mais recentes de tickers específicos.
- **Classificação de Ativos:** Identifique se um ativo é FII, ETF ou UNIT.
- **Detalhes de Ativos:** Acesse informações completas, incluindo resumos e tipos de cotação.
- **Autenticação Segura:** Todos os endpoints exigem um token Bearer válido.
- **Documentação via Swagger UI:** Interface visual e interativa para explorar os recursos da API.

---

## Documentação da API

A documentação completa da API está disponível em `/docs`, onde você pode testar os endpoints e ver exemplos.

---

## Configuração

### Pré-requisitos
- Python 3.10 ou superior
- Redis para cache
- Docker (opcional)

### Instalação

1. Clone este repositório:
   ```bash
   git clone https://github.com/rpsouza441/asset-info-api.git
   cd asset-info-api
