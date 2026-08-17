FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY pyproject.toml README.md ./
COPY marketlab ./marketlab
COPY backend ./backend
COPY scripts ./scripts

RUN python -m pip install --upgrade pip && python -m pip install .

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=5 \
  CMD python -c "import os, urllib.request; port=os.getenv('PORT', '8000'); urllib.request.urlopen(f'http://127.0.0.1:{port}/health', timeout=3)"

CMD ["/bin/sh", "-c", "exec uvicorn backend.api.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
