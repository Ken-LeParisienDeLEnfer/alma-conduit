# Development image for the Conduit backend.
#
# Dependencies are installed from the committed uv.lock for reproducible
# builds. Application code is bind-mounted by docker-compose.yml at runtime
# so edits on the host are picked up by uvicorn's --reload without rebuilding
# the image; the image itself still copies the source so it also runs
# standalone (e.g. `docker run` without compose).
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    PATH="/app/.venv/bin:${PATH}"

COPY --from=ghcr.io/astral-sh/uv:0.9-python3.13-bookworm-slim /usr/local/bin/uv /usr/local/bin/uvx /usr/local/bin/

WORKDIR /app

# Install dependencies first so this layer is cached as long as the lockfile
# doesn't change, independently of application code changes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --group dev

COPY . .
RUN uv sync --frozen --group dev

# Bakes the release version into the image at build time, so the running
# app reports exactly what it was released as without ever committing that
# version to git before the image is confirmed built and pushed. Defaults
# to "dev" when no build-arg is passed (e.g. local `docker compose build`).
ARG APP_VERSION=dev
RUN sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"${APP_VERSION}\"/" version.py

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8080

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uv", "run", "uvicorn", "conduit.app:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
