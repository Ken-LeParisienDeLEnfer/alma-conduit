"""
Integration tests for articles CRUD, feed, and filtering.
"""

from tests.conftest import SAMPLE_ARTICLE

# ---------------------------------------------------------------------------
# Create article
# ---------------------------------------------------------------------------


async def test_create_article_returns_article(client, alice_headers):
    resp = await client.post(
        "/api/articles",
        json={"article": SAMPLE_ARTICLE},
        headers=alice_headers,
    )
    assert resp.status_code == 200
    article = resp.json()["article"]
    assert article["title"] == SAMPLE_ARTICLE["title"]
    assert article["description"] == SAMPLE_ARTICLE["description"]
    assert article["body"] == SAMPLE_ARTICLE["body"]
    assert set(article["tagList"]) == set(SAMPLE_ARTICLE["tagList"])
    assert "slug" in article
    assert article["slug"]


async def test_create_article_requires_auth(client):
    resp = await client.post(
        "/api/articles",
        json={"article": SAMPLE_ARTICLE},
    )
    assert resp.status_code == 403


async def test_create_article_author_matches_current_user(client, alice, alice_headers):
    resp = await client.post(
        "/api/articles",
        json={"article": SAMPLE_ARTICLE},
        headers=alice_headers,
    )
    assert resp.json()["article"]["author"]["username"] == alice["username"]


# ---------------------------------------------------------------------------
# Get article
# ---------------------------------------------------------------------------


async def test_get_article_by_slug(client, alice_article):
    resp = await client.get(f"/api/articles/{alice_article['slug']}")
    assert resp.status_code == 200
    assert resp.json()["article"]["slug"] == alice_article["slug"]


async def test_get_nonexistent_article_returns_404(client):
    resp = await client.get("/api/articles/does-not-exist-slug")
    assert resp.status_code == 404


async def test_get_article_unauthenticated_shows_not_favorited(client, alice_article):
    resp = await client.get(f"/api/articles/{alice_article['slug']}")
    assert resp.json()["article"]["favorited"] is False


# ---------------------------------------------------------------------------
# Update article
# ---------------------------------------------------------------------------


async def test_author_can_update_article(client, alice_article, alice_headers):
    resp = await client.put(
        f"/api/articles/{alice_article['slug']}",
        json={"article": {"title": "Updated Title Right Here"}},
        headers=alice_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["article"]["title"] == "Updated Title Right Here"


async def test_non_author_cannot_update_article(client, alice_article, bob_headers):
    resp = await client.put(
        f"/api/articles/{alice_article['slug']}",
        json={"article": {"title": "Hijacked Title!!!"}},
        headers=bob_headers,
    )
    assert resp.status_code == 403


async def test_update_article_without_auth_returns_403(client, alice_article):
    resp = await client.put(
        f"/api/articles/{alice_article['slug']}",
        json={"article": {"title": "No Auth Update"}},
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Delete article
# ---------------------------------------------------------------------------


async def test_author_can_delete_article(client, alice_article, alice_headers):
    resp = await client.delete(
        f"/api/articles/{alice_article['slug']}",
        headers=alice_headers,
    )
    assert resp.status_code in (200, 204)
    # Article should be gone
    get_resp = await client.get(f"/api/articles/{alice_article['slug']}")
    assert get_resp.status_code == 404


async def test_non_author_cannot_delete_article(client, alice_article, bob_headers):
    resp = await client.delete(
        f"/api/articles/{alice_article['slug']}",
        headers=bob_headers,
    )
    assert resp.status_code == 403


async def test_delete_article_without_auth_returns_403(client, alice_article):
    resp = await client.delete(f"/api/articles/{alice_article['slug']}")
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Global article feed (filtering)
# ---------------------------------------------------------------------------


async def test_global_feed_returns_articles(client, alice_article):
    resp = await client.get("/api/articles")
    assert resp.status_code == 200
    data = resp.json()
    assert data["articlesCount"] >= 1
    slugs = [a["slug"] for a in data["articles"]]
    assert alice_article["slug"] in slugs


async def test_filter_by_tag(client, alice_article, alice_second_article):
    resp = await client.get("/api/articles?tag=testing")
    assert resp.status_code == 200
    data = resp.json()
    slugs = [a["slug"] for a in data["articles"]]
    assert alice_article["slug"] in slugs
    # alice_second_article has tag 'sqlalchemy', not 'testing'
    assert alice_second_article["slug"] not in slugs


async def test_filter_by_author(client, alice_article, bob, bob_headers):
    # Create an article as Bob so we have two authors
    bob_resp = await client.post(
        "/api/articles",
        json={
            "article": {
                "title": "Bob's Article Here",
                "description": "Written by Bob for testing",
                "body": "Bob knows his stuff about writing articles.",
                "tagList": [],
            }
        },
        headers=bob_headers,
    )
    bob_slug = bob_resp.json()["article"]["slug"]

    resp = await client.get(f"/api/articles?author={bob['username']}")
    slugs = [a["slug"] for a in resp.json()["articles"]]
    assert bob_slug in slugs
    assert alice_article["slug"] not in slugs


async def test_filter_by_favorited(client, alice_article, bob, bob_headers):
    # Bob favorites Alice's article
    await client.post(
        f"/api/articles/{alice_article['slug']}/favorite",
        headers=bob_headers,
    )
    resp = await client.get(f"/api/articles?favorited={bob['username']}")
    slugs = [a["slug"] for a in resp.json()["articles"]]
    assert alice_article["slug"] in slugs


# ---------------------------------------------------------------------------
# Personal feed
# ---------------------------------------------------------------------------


async def test_feed_returns_articles_from_followed_users(
    client, alice_article, bob_follows_alice, bob_headers
):
    resp = await client.get("/api/articles/feed", headers=bob_headers)
    assert resp.status_code == 200
    slugs = [a["slug"] for a in resp.json()["articles"]]
    assert alice_article["slug"] in slugs


async def test_feed_excludes_articles_from_not_followed_users(
    client, alice_article, bob_headers
):
    """Bob does not follow Alice – her articles should not appear in Bob's feed."""
    resp = await client.get("/api/articles/feed", headers=bob_headers)
    assert resp.status_code == 200
    slugs = [a["slug"] for a in resp.json()["articles"]]
    assert alice_article["slug"] not in slugs


async def test_feed_requires_auth(client):
    resp = await client.get("/api/articles/feed")
    assert resp.status_code == 403
