# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim

RUN groupadd -r appuser && useradd -r -g appuser appuser

WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["sh", "-c", "echo 'Starting alembic...' && alembic upgrade head && echo 'Starting uvicorn...' && python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
