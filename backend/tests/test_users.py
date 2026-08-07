"""
Integration tests for the current-user endpoints (GET/PUT /api/user).
"""



async def test_get_current_user_returns_profile(client, alice, alice_headers):
    resp = await client.get("/api/user", headers=alice_headers)
    assert resp.status_code == 200
    user = resp.json()["user"]
    assert user["username"] == alice["username"]
    assert user["email"] == alice["email"]
    assert "token" in user


async def test_get_current_user_without_token_returns_403(client):
    resp = await client.get("/api/user")
    assert resp.status_code == 403


async def test_update_user_bio(client, alice_headers):
    resp = await client.put(
        "/api/user",
        json={"user": {"bio": "I love testing"}},
        headers=alice_headers,
    )
    assert resp.status_code == 200
    user = resp.json()["user"]
    assert user["bio"] == "I love testing"


async def test_update_user_image(client, alice_headers):
    resp = await client.put(
        "/api/user",
        json={"user": {"image": "https://example.com/avatar.png"}},
        headers=alice_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["image"] == "https://example.com/avatar.png"


async def test_update_user_email(client, alice_headers):
    new_email = "alice_new@example.com"
    resp = await client.put(
        "/api/user",
        json={"user": {"email": new_email}},
        headers=alice_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["user"]["email"] == new_email


async def test_updated_values_are_persisted(client, alice_headers):
    """Update bio then GET /api/user to confirm persistence."""
    await client.put(
        "/api/user",
        json={"user": {"bio": "Persistent bio"}},
        headers=alice_headers,
    )
    resp = await client.get("/api/user", headers=alice_headers)
    assert resp.json()["user"]["bio"] == "Persistent bio"


async def test_update_without_token_returns_403(client):
    resp = await client.put(
        "/api/user",
        json={"user": {"bio": "Should not work"}},
    )
    assert resp.status_code == 403
