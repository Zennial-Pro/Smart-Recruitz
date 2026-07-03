# Stage 1: Builder
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir .

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

RUN adduser --disabled-password --no-create-home appuser

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY app/ ./app/
COPY seeds/ ./seeds/
COPY alembic.ini .

RUN mkdir -p /app/uploads && chown appuser:appuser /app/uploads

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.asgi:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
