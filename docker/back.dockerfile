# Container do BACKEND + BANCO DE DADOS
# A API FastAPI e o banco SQLite rodam no mesmo container. O arquivo do banco
# (/data/myfiles.db) e os arquivos enviados (/data/uploads, /data/profile)
# ficam em /data, que deve ser montado como volume para sobreviver a recriações.
#
# Build (a partir da raiz do repositório):
#   docker build -f docker/back.dockerfile -t myfiles-back .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    MYFILES_STORAGE_DIR=/data \
    MYFILES_DATABASE_URL=sqlite:////data/myfiles.db

WORKDIR /app

# Dependências primeiro: a camada fica em cache enquanto o requirements não mudar
COPY back/requirements.txt .
RUN pip install -r requirements.txt

COPY back/ .

# Usuário sem privilégios, dono da pasta de dados
RUN useradd --create-home --uid 10001 appuser \
    && mkdir -p /data \
    && chown appuser:appuser /data
USER appuser

VOLUME ["/data"]
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
