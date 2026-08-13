"""
Integration tests for user registration and login (POST /api/users, POST
/api/users/login).
"""

from tests.conftest import ALICE


async def test_register_returns_user_with_token(client):
    resp = await client.post(
        "/api/users",
        json={
            "user": {
                "username": "alice",
                "email": "alice@example.com",
                "password": "password123",
            }
        },
    )
    assert resp.status_code == 200
    user = resp.json()["user"]
    assert user["username"] == "alice"
    assert user["email"] == "alice@example.com"
    assert "token" in user
    assert user["token"]  # non-empty


async def test_register_duplicate_email_returns_error(client):
    payload = {
        "user": {
            "username": "alice",
            "email": "alice@example.com",
            "password": "password123",
        }
    }
    await client.post("/api/users", json=payload)
    resp = await client.post(
        "/api/users",
        json={
            "user": {
                "username": "alice2",
                "email": "alice@example.com",  # same email
                "password": "password123",
            }
        },
    )
    assert resp.status_code == 400


async def test_register_duplicate_username_returns_error(client):
    await client.post(
        "/api/users",
        json={
            "user": {
                "username": "alice",
                "email": "alice@example.com",
                "password": "password123",
            }
        },
    )
    resp = await client.post(
        "/api/users",
        json={
            "user": {
                "username": "alice",  # same username
                "email": "alice2@example.com",
                "password": "password123",
            }
        },
    )
    assert resp.status_code == 400


async def test_register_short_password_is_rejected(client):
    resp = await client.post(
        "/api/users",
        json={
            "user": {
                "username": "alice",
                "email": "alice@example.com",
                "password": "short",  # < 8 chars
            }
        },
    )
    assert resp.status_code == 422


async def test_login_with_correct_credentials_returns_token(client, alice):
    resp = await client.post(
        "/api/users/login",
        json={"user": {"email": ALICE["email"], "password": ALICE["password"]}},
    )
    assert resp.status_code == 200
    user = resp.json()["user"]
    assert user["email"] == ALICE["email"]
    assert "token" in user
    assert user["token"]


async def test_login_with_wrong_password_returns_error(client, alice):
    resp = await client.post(
        "/api/users/login",
        json={"user": {"email": ALICE["email"], "password": "wrongpassword"}},
    )
    assert resp.status_code in (400, 422)


async def test_login_with_unknown_email_returns_error(client):
    resp = await client.post(
        "/api/users/login",
        json={"user": {"email": "nobody@example.com", "password": "password123"}},
    )
    assert resp.status_code in (400, 404, 422)
