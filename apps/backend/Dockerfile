FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
COPY packages/core/pyproject.toml packages/core/pyproject.toml
COPY packages/core/src packages/core/src

RUN uv pip install --system -e packages/core -e apps/backend

COPY apps/backend/src apps/backend/src
COPY apps/backend/config.yaml apps/backend/config.yaml
COPY apps/backend/alembic apps/backend/alembic
COPY apps/backend/alembic.ini apps/backend/alembic.ini

WORKDIR /app/apps/backend

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
