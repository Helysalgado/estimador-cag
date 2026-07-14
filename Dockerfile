FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md alembic.ini ./
COPY app ./app
COPY alembic ./alembic
COPY scripts ./scripts
COPY data ./data

# Note: sentence-transformers pulls torch (large image). Prefer local API +
# Postgres for S10 measurement if rebuild time is prohibitive.
RUN uv sync --frozen --no-dev

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
