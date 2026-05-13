FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
COPY uv.lock .
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/core/src packages/core/src
COPY packages/llm/pyproject.toml packages/llm/pyproject.toml
COPY packages/llm/src packages/llm/src
COPY apps/backend/pyproject.toml apps/backend/pyproject.toml
COPY apps/backend/src apps/backend/src

RUN uv pip install --system -e packages/core -e packages/llm -e apps/backend

COPY apps/backend/config.yaml apps/backend/config.yaml
COPY apps/backend/alembic apps/backend/alembic
COPY apps/backend/alembic.ini apps/backend/alembic.ini

WORKDIR /app/apps/backend

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
