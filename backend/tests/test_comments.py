"""
Integration tests for article comments (GET/POST/DELETE /api/articles/{slug}/comments).
"""


async def test_add_comment_to_article(client, alice_article, bob_headers):
    resp = await client.post(
        f"/api/articles/{alice_article['slug']}/comments",
        json={"comment": {"body": "Great article!"}},
        headers=bob_headers,
    )
    assert resp.status_code == 200
    comment = resp.json()["comment"]
    assert comment["body"] == "Great article!"
    assert "id" in comment
    assert comment["author"]["username"] == "bob"


async def test_add_comment_requires_auth(client, alice_article):
    resp = await client.post(
        f"/api/articles/{alice_article['slug']}/comments",
        json={"comment": {"body": "Anonymous comment"}},
    )
    assert resp.status_code == 403


async def test_list_comments_returns_all_comments(client, alice_article_with_comment):
    slug = alice_article_with_comment["article"]["slug"]
    resp = await client.get(f"/api/articles/{slug}/comments")
    assert resp.status_code == 200
    comments = resp.json()["comments"]
    assert len(comments) >= 1
    bodies = [c["body"] for c in comments]
    assert "Great article!" in bodies


async def test_list_comments_unauthenticated(client, alice_article_with_comment):
    """GET comments should work without authentication."""
    slug = alice_article_with_comment["article"]["slug"]
    resp = await client.get(f"/api/articles/{slug}/comments")
    assert resp.status_code == 200


async def test_comment_author_can_delete_comment(
    client, alice_article_with_comment, bob_headers
):
    slug = alice_article_with_comment["article"]["slug"]
    comment_id = alice_article_with_comment["comment"]["id"]
    resp = await client.delete(
        f"/api/articles/{slug}/comments/{comment_id}",
        headers=bob_headers,
    )
    assert resp.status_code in (200, 204)
    # Comment should no longer appear in the list
    list_resp = await client.get(f"/api/articles/{slug}/comments")
    ids = [c["id"] for c in list_resp.json()["comments"]]
    assert comment_id not in ids


async def test_non_author_cannot_delete_comment(
    client, alice_article_with_comment, charlie_headers
):
    slug = alice_article_with_comment["article"]["slug"]
    comment_id = alice_article_with_comment["comment"]["id"]
    resp = await client.delete(
        f"/api/articles/{slug}/comments/{comment_id}",
        headers=charlie_headers,
    )
    assert resp.status_code == 403


async def test_delete_comment_requires_auth(client, alice_article_with_comment):
    slug = alice_article_with_comment["article"]["slug"]
    comment_id = alice_article_with_comment["comment"]["id"]
    resp = await client.delete(
        f"/api/articles/{slug}/comments/{comment_id}",
    )
    assert resp.status_code == 403


async def test_multiple_comments_on_same_article(
    client, alice_article, alice_headers, bob_headers
):
    slug = alice_article["slug"]
    await client.post(
        f"/api/articles/{slug}/comments",
        json={"comment": {"body": "First comment here"}},
        headers=bob_headers,
    )
    await client.post(
        f"/api/articles/{slug}/comments",
        json={"comment": {"body": "Second comment here"}},
        headers=alice_headers,
    )
    resp = await client.get(f"/api/articles/{slug}/comments")
    assert len(resp.json()["comments"]) == 2
