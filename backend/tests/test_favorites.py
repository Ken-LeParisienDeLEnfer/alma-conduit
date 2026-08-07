"""
Integration tests for article favorites (POST/DELETE /api/articles/{slug}/favorite).
"""


async def test_favorite_article_sets_favorited_true(client, alice_article, bob_headers):
    resp = await client.post(
        f"/api/articles/{alice_article['slug']}/favorite",
        headers=bob_headers,
    )
    assert resp.status_code == 200
    article = resp.json()["article"]
    assert article["favorited"] is True
    assert article["favoritesCount"] == 1


async def test_favoriting_article_increments_count(
    client, alice_article, bob_headers, charlie_headers
):
    await client.post(
        f"/api/articles/{alice_article['slug']}/favorite",
        headers=bob_headers,
    )
    resp = await client.post(
        f"/api/articles/{alice_article['slug']}/favorite",
        headers=charlie_headers,
    )
    assert resp.json()["article"]["favoritesCount"] == 2


async def test_unfavorite_article_sets_favorited_false(
    client, alice_article_favorited_by_bob, alice_article, bob_headers
):
    resp = await client.delete(
        f"/api/articles/{alice_article['slug']}/favorite",
        headers=bob_headers,
    )
    assert resp.status_code == 200
    article = resp.json()["article"]
    assert article["favorited"] is False
    assert article["favoritesCount"] == 0


async def test_unfavoriting_article_decrements_count(
    client, alice_article_favorited_by_bob, alice_article, bob_headers
):
    resp = await client.delete(
        f"/api/articles/{alice_article['slug']}/favorite",
        headers=bob_headers,
    )
    assert resp.json()["article"]["favoritesCount"] == 0


async def test_favorite_twice_returns_error(
    client, alice_article_favorited_by_bob, alice_article, bob_headers
):
    resp = await client.post(
        f"/api/articles/{alice_article['slug']}/favorite",
        headers=bob_headers,
    )
    assert resp.status_code == 400


async def test_unfavorite_not_favorited_returns_error(
    client, alice_article, bob_headers
):
    resp = await client.delete(
        f"/api/articles/{alice_article['slug']}/favorite",
        headers=bob_headers,
    )
    assert resp.status_code == 400


async def test_favorite_requires_auth(client, alice_article):
    resp = await client.post(f"/api/articles/{alice_article['slug']}/favorite")
    assert resp.status_code == 403


async def test_favorite_count_visible_unauthenticated(
    client, alice_article_favorited_by_bob, alice_article
):
    """Anyone can see the favorites count without logging in."""
    resp = await client.get(f"/api/articles/{alice_article['slug']}")
    assert resp.status_code == 200
    assert resp.json()["article"]["favoritesCount"] == 1
    assert resp.json()["article"]["favorited"] is False
