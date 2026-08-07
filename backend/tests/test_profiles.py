"""
Integration tests for profiles and follow/unfollow (GET/POST/DELETE /api/profiles).
"""


async def test_get_profile_unauthenticated(client, alice):
    resp = await client.get(f"/api/profiles/{alice['username']}")
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert profile["username"] == alice["username"]
    assert profile["following"] is False


async def test_get_profile_unknown_user_returns_404(client):
    resp = await client.get("/api/profiles/nobody")
    assert resp.status_code == 404


async def test_follow_user(client, bob_headers, alice):
    resp = await client.post(
        f"/api/profiles/{alice['username']}/follow",
        headers=bob_headers,
    )
    assert resp.status_code == 200
    profile = resp.json()["profile"]
    assert profile["username"] == alice["username"]
    assert profile["following"] is True


async def test_follow_reflected_on_get_profile(client, bob_headers, alice):
    """After following, GET profile must show following=True."""
    await client.post(
        f"/api/profiles/{alice['username']}/follow",
        headers=bob_headers,
    )
    resp = await client.get(
        f"/api/profiles/{alice['username']}",
        headers=bob_headers,
    )
    assert resp.json()["profile"]["following"] is True


async def test_unfollow_user(client, bob_follows_alice, bob_headers, alice):
    resp = await client.delete(
        f"/api/profiles/{alice['username']}/follow",
        headers=bob_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["profile"]["following"] is False


async def test_unfollow_reflected_on_get_profile(
    client, bob_follows_alice, bob_headers, alice
):
    """After unfollowing, GET profile must show following=False."""
    await client.delete(
        f"/api/profiles/{alice['username']}/follow",
        headers=bob_headers,
    )
    resp = await client.get(
        f"/api/profiles/{alice['username']}",
        headers=bob_headers,
    )
    assert resp.json()["profile"]["following"] is False


async def test_follow_requires_auth(client, alice):
    resp = await client.post(f"/api/profiles/{alice['username']}/follow")
    assert resp.status_code == 403


async def test_unfollow_requires_auth(client, alice):
    resp = await client.delete(f"/api/profiles/{alice['username']}/follow")
    assert resp.status_code == 403
