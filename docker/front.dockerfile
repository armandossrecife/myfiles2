# Container do FRONTEND
# Aplicação Flask servida pelo gunicorn. Não guarda dados: conversa com o
# backend pelo endereço definido em MYFILES_BACKEND_URL.
#
# Build (a partir da raiz do repositório):
#   docker build -f docker/front.dockerfile -t myfiles-front .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GUNICORN_WORKERS=2

WORKDIR /app

COPY front/requirements.txt .
RUN pip install -r requirements.txt

COPY front/ .

RUN useradd --create-home --uid 10001 appuser
USER appuser

EXPOSE 5001

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:5001/health', timeout=2)"

# gunicorn: servidor WSGI de produção ("flask run" é só para desenvolvimento).
# --timeout alto para uploads e vídeos grandes passarem pelo frontend.
CMD ["sh", "-c", "exec gunicorn --bind 0.0.0.0:5001 --workers ${GUNICORN_WORKERS} --timeout 120 --access-logfile - main:app"]
