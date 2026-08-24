#!/bin/sh
# Two distinct phases, not one retry loop covering both: wait for the
# database to become reachable (bounded retry — expected at startup, e.g.
# before docker-compose's own healthcheck-gated dependency kicks in, or when
# running standalone with no such gate), then apply migrations exactly once.
# A migration failure at that point is a real problem (bad SQL, conflicting
# revision, ...), not a connectivity one — retrying it would just repeat the
# same failure forever while printing a misleading "not ready yet", so it
# fails loud immediately instead.
set -e

echo "Waiting for database to be reachable..."
attempts=0
max_attempts=30
until uv run python -c "
import asyncio
import asyncpg
from conduit.core.config import get_app_settings


async def check() -> None:
    settings = get_app_settings()
    conn = await asyncpg.connect(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        database=settings.postgres_db,
    )
    await conn.close()


asyncio.run(check())
"; do
  attempts=$((attempts + 1))
  if [ "$attempts" -ge "$max_attempts" ]; then
    echo "Database still not reachable after ${attempts} attempts, giving up." >&2
    exit 1
  fi
  echo "Database not ready yet, retrying in 2s... (attempt $attempts/$max_attempts)"
  sleep 2
done

echo "Database reachable. Applying migrations..."
uv run alembic upgrade head

echo "Migrations applied. Starting application..."
exec "$@"
