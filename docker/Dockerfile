# Multi-stage build for the Heleket Python SDK.
#
# - build stage installs Poetry and resolves dependencies
# - dev stage carries source + venv so tests, examples, and the CLI run inside

FROM python:3.11-slim AS build

ENV POETRY_VERSION=2.4.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    PIP_NO_CACHE_DIR=1

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /app

# Cache dependency resolution: copy only manifests, then install with no source.
COPY pyproject.toml poetry.lock* README.md ./
RUN poetry install --no-root --with dev

COPY src ./src
COPY tests ./tests
COPY examples ./examples
COPY bin ./bin

RUN poetry install --only-root

# ----------------------------------------------------------------------------

FROM python:3.11-slim AS dev

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=build /app /app

CMD ["python", "--version"]
