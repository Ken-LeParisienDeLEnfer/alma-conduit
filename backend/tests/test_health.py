"""Integration tests for the health-check endpoint."""


async def test_health_check_returns_200(client):
    resp = await client.get("/api/health-check")
    assert resp.status_code == 200
