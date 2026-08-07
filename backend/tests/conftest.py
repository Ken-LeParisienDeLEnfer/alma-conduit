"""
Integration test suite for the Conduit API.

Environment setup: tests run against a real PostgreSQL database (conduit_test).
The database is created fresh each session and truncated between each test.
The APP_ENV=test env var must be set before any conduit module is imported so
that the module-level `container` singleton picks up TestAppSettings.
"""

import os

# Must be set before any conduit import so the module-level container singleton
# picks up TestAppSettings (which reads from .env.test).
os.environ["APP_ENV"] = "test"

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from conduit.app import create_app
from conduit.core.config import get_app_settings
from conduit.infrastructure.models import Base

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

BASE_URL = "http://testserver"

# ---------------------------------------------------------------------------
# Session-scoped: create / drop tables once for the whole test run
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(scope="session")
async def db_engine():
    """Create the test schema once and drop it after the session."""
    # Clear lru_cache so we always get TestAppSettings here.
    get_app_settings.cache_clear()
    settings = get_app_settings()

    engine = create_async_engine(**settings.sqlalchemy_engine_props)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ---------------------------------------------------------------------------
# Function-scoped: truncate all data between every test
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture(autouse=True)
async def clean_db(db_engine):
    """Truncate every table (cascade) before yielding to the test."""
    yield
    async with db_engine.connect() as conn:
        # RESTART IDENTITY resets auto-increment sequences too.
        await conn.execute(
            text(
                'TRUNCATE "user", tag, article, article_tag, comment, favorite, follower'
                " RESTART IDENTITY CASCADE"
            )
        )


# ---------------------------------------------------------------------------
# HTTP client – wired to the ASGI app (no real network)
# ---------------------------------------------------------------------------


@pytest_asyncio.fixture
async def client(db_engine):
    """Async HTTP client connected to the FastAPI app via ASGI transport."""
    get_app_settings.cache_clear()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as ac:
        yield ac


# ---------------------------------------------------------------------------
# Scenario fixtures: reusable pre-built state
# ---------------------------------------------------------------------------

ALICE = {
    "username": "alice",
    "email": "alice@example.com",
    "password": "password123",
}

BOB = {
    "username": "bob",
    "email": "bob@example.com",
    "password": "password123",
}

CHARLIE = {
    "username": "charlie",
    "email": "charlie@example.com",
    "password": "password123",
}


async def _register(client: AsyncClient, user_data: dict) -> dict:
    """Register a user and return the full response payload."""
    resp = await client.post("/api/users", json={"user": user_data})
    assert resp.status_code == 200, resp.text
    return resp.json()["user"]


async def _login(client: AsyncClient, user_data: dict) -> dict:
    """Log in a user and return the full response payload."""
    resp = await client.post(
        "/api/users/login",
        json={"user": {"email": user_data["email"], "password": user_data["password"]}},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["user"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Token {token}"}


@pytest_asyncio.fixture
async def alice(client):
    """Registered Alice user dict (includes token)."""
    return await _register(client, ALICE)


@pytest_asyncio.fixture
async def bob(client):
    """Registered Bob user dict (includes token)."""
    return await _register(client, BOB)


@pytest_asyncio.fixture
async def charlie(client):
    """Registered Charlie user dict (includes token)."""
    return await _register(client, CHARLIE)


@pytest_asyncio.fixture
async def alice_headers(alice):
    """Authorization headers for Alice."""
    return _auth_headers(alice["token"])


@pytest_asyncio.fixture
async def bob_headers(bob):
    """Authorization headers for Bob."""
    return _auth_headers(bob["token"])


@pytest_asyncio.fixture
async def charlie_headers(charlie):
    """Authorization headers for Charlie."""
    return _auth_headers(charlie["token"])


SAMPLE_ARTICLE = {
    "title": "Integration Testing Tips",
    "description": "How to write great integration tests",
    "body": "Start from the outside and work your way in.",
    "tagList": ["testing", "python"],
}

SECOND_ARTICLE = {
    "title": "Advanced SQLAlchemy Patterns",
    "description": "Async patterns with SQLAlchemy 2.0",
    "body": "Use async sessions for scalable database access.",
    "tagList": ["sqlalchemy", "python"],
}


@pytest_asyncio.fixture
async def alice_article(client, alice_headers):
    """An article authored by Alice."""
    resp = await client.post(
        "/api/articles",
        json={"article": SAMPLE_ARTICLE},
        headers=alice_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["article"]


@pytest_asyncio.fixture
async def alice_second_article(client, alice_headers):
    """A second article authored by Alice."""
    resp = await client.post(
        "/api/articles",
        json={"article": SECOND_ARTICLE},
        headers=alice_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["article"]


@pytest_asyncio.fixture
async def alice_article_with_comment(client, alice_article, bob_headers):
    """Alice's article with one comment left by Bob."""
    resp = await client.post(
        f"/api/articles/{alice_article['slug']}/comments",
        json={"comment": {"body": "Great article!"}},
        headers=bob_headers,
    )
    assert resp.status_code == 200, resp.text
    return {
        "article": alice_article,
        "comment": resp.json()["comment"],
    }


@pytest_asyncio.fixture
async def bob_follows_alice(client, bob_headers, alice):
    """Bob follows Alice – yields the follow response."""
    resp = await client.post(
        f"/api/profiles/{alice['username']}/follow",
        headers=bob_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["profile"]


@pytest_asyncio.fixture
async def alice_article_favorited_by_bob(client, alice_article, bob_headers):
    """Alice's article favorited by Bob."""
    resp = await client.post(
        f"/api/articles/{alice_article['slug']}/favorite",
        headers=bob_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["article"]
