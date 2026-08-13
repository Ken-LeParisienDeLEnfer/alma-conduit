#!/bin/sh
# Applies pending Alembic migrations, retrying until the database is
# reachable, then hands off to the container's main command (uvicorn).
# Retrying here removes the need for a separate wait-for-it script: Alembic
# itself is the readiness probe for "is the schema in the state the app
# expects".
set -e

echo "Applying database migrations..."
until uv run alembic upgrade head; do
  echo "Database not ready yet, retrying in 2s..."
  sleep 2
done

echo "Migrations applied. Starting application..."
exec "$@"
