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

# **1. Clonar o Repositório**

git clone https://github.com/rpsouza441/asset-info-api.git
cd asset-info-api

# **2. Configurar as Dependências**

## Certifique-se de que o Python 3.12 ou superior esteja instalado.

python3 --version

## Crie e ative um ambiente virtual (opcional, mas recomendado).

python3 -m venv venv
source venv/bin/activate # No Windows, use `venv\Scripts\activate`

## Instale as dependências listadas em `requirements.txt`.

pip install -r requirements.txt

# **3. Configurar o Redis**

## A API utiliza o Redis como cache.

## Instale o Redis conforme o sistema operacional:

# Ubuntu:

sudo apt update && sudo apt install redis

# Windows:

# Baixe o Redis para Windows: https://github.com/microsoftarchive/redis/releases

# Mac:

brew install redis

## Inicie o Redis localmente:

redis-server

# **4. Configurar Variáveis de Ambiente**

## Crie um arquivo `.env` na raiz do projeto para definir as configurações.

echo "FLASK_ENV=development
CACHE_TYPE=RedisCache
CACHE_REDIS_HOST=localhost
CACHE_REDIS_PORT=6379
CACHE_REDIS_DB=0" > .env

# **5. Inicializar o Banco de Dados (se necessário)**

# Caso haja dependência de banco de dados (não descrito), inclua comandos aqui.

# **6. Executar a API**

## Inicialize a aplicação com o Gunicorn:

gunicorn -w 4 -b 0.0.0.0:5000 main:app

# **7. Testar a API**

## Acesse a documentação Swagger para explorar os endpoints:

# Abra no navegador: http://localhost:5000/docs/

# **8. Docker (opcional)**

## Alternativamente, use Docker para executar a API.

## Certifique-se de que o Docker e Docker Compose estejam instalados.

# 8.1. Construir e subir os contêineres com Docker Compose

docker-compose up --build -d

# 8.2. Verificar os contêineres em execução

docker ps

# 8.3. Acessar a API

# A API estará disponível em:

# URL Base: http://localhost:5322

# Documentação Swagger: http://localhost:5322/docs

# 8.4. Parar e remover os contêineres (quando necessário)

docker-compose down
