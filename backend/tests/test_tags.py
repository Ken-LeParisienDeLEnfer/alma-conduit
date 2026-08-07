"""
Integration tests for tags (GET /api/tags).
"""

from tests.conftest import SAMPLE_ARTICLE, SECOND_ARTICLE


async def test_get_tags_returns_empty_when_no_articles(client):
    resp = await client.get("/api/tags")
    assert resp.status_code == 200
    assert resp.json()["tags"] == []


async def test_get_tags_returns_tags_from_articles(client, alice_article):
    resp = await client.get("/api/tags")
    assert resp.status_code == 200
    tags = resp.json()["tags"]
    for tag in SAMPLE_ARTICLE["tagList"]:
        assert tag in tags


async def test_get_tags_aggregates_tags_from_multiple_articles(
    client, alice_article, alice_second_article
):
    resp = await client.get("/api/tags")
    tags = resp.json()["tags"]
    expected = set(SAMPLE_ARTICLE["tagList"]) | set(SECOND_ARTICLE["tagList"])
    for tag in expected:
        assert tag in tags


async def test_get_tags_no_duplicates(client, alice_article, alice_second_article):
    """Both articles share the 'python' tag; it should appear only once."""
    resp = await client.get("/api/tags")
    tags = resp.json()["tags"]
    assert tags.count("python") == 1


async def test_get_tags_does_not_require_auth(client, alice_article):
    resp = await client.get("/api/tags")
    assert resp.status_code == 200
