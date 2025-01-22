FROM python:3.12.8-alpine3.21

# Configura o diretório de trabalho
WORKDIR /app

# Instala dependências do sistema
RUN apk add --no-cache build-base libpng-dev freetype-dev musl-dev jpeg-dev zlib-dev tcl-dev tk-dev

# Instala as dependências do Python
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Define o comando padrão para o contêiner
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:80", "main:app"]
