# Asset Information API

## Visão Geral

A **Asset Information API** é um microserviço em Python que fornece dados financeiros de ativos listados na B3 (Brasil) por meio de chamadas HTTP. A API combina cache em Redis, busca em lote via `yfinance` e autenticação por token para entregar respostas rápidas e seguras.

## Funcionalidades

- **Consulta de Preços de Mercado** (`/fetch_market_price`): retorna preços atuais para uma lista de tickers.
- **Informações Detalhadas de Ações** (`/fetch_stock_info`): inclui metadados (`info`), recomendações de analistas, price targets e estimativas de crescimento.
- **Informações de Ativos** (`/fetch_asset_info`): agrega preço de mercado e detalhes do ativo em um único endpoint.
- **Classificação de Ativos** (`/classify_assets`): identifica se cada ativo é FII, ETF ou UNIT com base em palavras-chave no nome.
- **Recomendações de Análise** (`/fetch_recommendations`): retorna sugestões de compra/venda para cada ticker (se disponível).
- **Autenticação Segura**: todos os endpoints (exceto `/docs` e arquivos estáticos) exigem um header `Authorization: <TOKEN>` válido.
- **Documentação Interativa** via Swagger UI em `/docs`.

## Pré-requisitos

- Docker (>=20.10) e Docker Compose (>=1.29) **OU**
- Python 3.12+
- Redis (caso não use Docker Compose)

## Instalação e Execução

### 1. Usando Docker Compose

1. Clone este repositório:

   ```bash
   git clone <seu-repo-url>.git
   cd asset-info-api
   ```

2. Construa e suba os containers:

   ```bash
   docker-compose up --build -d
   ```

3. A API estará disponível em:

   - **Base URL**: `http://localhost:5322`
   - **Swagger UI**: `http://localhost:5322/docs`

4. Para parar e remover os containers:

   ```bash
   docker-compose down
   ```

### 2. Sem Docker (produção local)

1. Clone o repositório e entre na pasta:

   ```bash
   git clone <seu-repo-url>.git
   cd asset-info-api
   ```

2. Crie e ative um ambiente virtual:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

3. Instale dependências:

   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Inicie uma instância do Redis (local ou Docker):

   ```bash
   docker run -d --name redis -p 6379:6379 redis:7.0-alpine
   ```

5. Configure tokens válidos em `tokens.py` (nome, token e data de expiração).
6. Execute a aplicação:

   ```bash
   python main.py
   ```

7. Acesse a API:

   - **URL**: `http://localhost:80`
   - **Swagger UI**: `http://localhost:80/docs`

## Configuração

- **`tokens.py`**: lista de tokens permitidos e data de expiração.
- **Cache Redis**: configurado em `services/cache_service.py` (host: `redis`, porta: `6379`).
- **Timeout de Cache**: definido no `CACHE_DEFAULT_TIMEOUT` ou passado como parâmetro em `fetch_multiple_ticker_data`.

## Autenticação

Adicione o header HTTP `Authorization` com um token válido em todas as requisições POST:

```http
Authorization: <TOKEN>
Content-Type: application/json
```

## Endpoints Principais

| Rota                     | Método | Descrição                                                  |
| ------------------------ | ------ | ---------------------------------------------------------- |
| `/fetch_market_price`    | POST   | Retorna preços atuais para cada ticker informado.          |
| `/fetch_stock_info`      | POST   | Retorna `info`, `recommendations`, `price_targets` e mais. |
| `/fetch_asset_info`      | POST   | Combina preço e detalhes do ativo em um único payload.     |
| `/classify_assets`       | POST   | Classifica cada ticker como FII, ETF ou UNIT.              |
| `/fetch_recommendations` | POST   | Retorna recomendações de analistas (se disponíveis).       |

### Exemplo de Requisição

```bash
curl -X POST http://localhost:5322/fetch_market_price \
  -H 'Authorization: <TOKEN>' \
  -H 'Content-Type: application/json' \
  -d '{"tickers": ["PETR4", "VALE3"]}'
```

## Logs

- Configurados via `services/logging_service.py` com nível `INFO`.
- Saem no stdout e podem ser direcionados para arquivos conforme necessidade.

## Contribuição

1. Fork este repositório.
2. Crie uma branch para sua feature: `git checkout -b feature/nome-feature`.
3. Commit suas mudanças: `git commit -m "Adiciona nova feature"`.
4. Push para o branch: `git push origin feature/nome-feature`.
5. Abra um Pull Request.

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).
