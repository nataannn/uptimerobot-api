# Dockerfile - UptimeRobot API

# Imagem oficial e leve do Python
FROM python:3.11-slim

# Diretório de trabalho
WORKDIR /app

# Cópia de requerimetos
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do código
COPY . .

# Usuário não-root: se alguém explorar uma falha na aplicação, não sai
# rodando como root dentro do container.
RUN addgroup --system app && adduser --system --ingroup app app \
    && chown -R app:app /app
USER app

# Expõe porta que API irá utilizar
EXPOSE 5000

# Checagem de saúde nativa do Docker/Compose — usa urllib da stdlib pra não
# precisar instalar curl na imagem.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health', timeout=3)" || exit 1

# Comando que irá rodar quando o container iniciar
# gunicorn no lugar do servidor de desenvolvimento do Flask:
# - gthread com 2 threads por worker porque a maior parte do tempo é I/O
#   esperando resposta da API da UptimeRobot, não CPU
# - timeout alto (120s) porque as rotas de bulk podem demorar em listas grandes
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--worker-class", "gthread", "--threads", "2", "--timeout", "120", "app:app"]
