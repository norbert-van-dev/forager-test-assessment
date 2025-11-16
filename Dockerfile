FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY search_api ./search_api

EXPOSE 8000
CMD ["uvicorn", "search_api.main:app", "--host", "0.0.0.0", "--port", "8000"]


