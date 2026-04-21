"""Integration tests for the FastAPI endpoints.

Uses httpx.AsyncClient against the real app instance.
Does not require a running database — tests the app startup,
health check, and schema validation.
"""

from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture()
def client():
    """Async test client that talks directly to the ASGI app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ── Health check ─────────────────────────────────────────────────────


class TestHealth:

    @pytest.mark.asyncio
    async def test_health_endpoint(self, client):
        async with client as c:
            resp = await c.get("/api/v1/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert isinstance(body["players_cached"], int)
        assert isinstance(body["index_loaded"], bool)


# ── Auth endpoints ───────────────────────────────────────────────────


class TestAuthSchemas:
    """Validate request/response schemas without a live database."""

    @pytest.mark.asyncio
    async def test_register_requires_body(self, client):
        async with client as c:
            resp = await c.post("/api/v1/auth/register")
        assert resp.status_code == 422  # validation error

    @pytest.mark.asyncio
    async def test_login_requires_body(self, client):
        async with client as c:
            resp = await c.post("/api/v1/auth/login")
        assert resp.status_code == 422


# ── Player search ────────────────────────────────────────────────────


class TestPlayerSearch:

    @pytest.mark.asyncio
    async def test_search_requires_query(self, client):
        async with client as c:
            resp = await c.get("/api/v1/search")
        # Missing required 'q' param
        assert resp.status_code == 422


# ── Similarity ───────────────────────────────────────────────────────


class TestSimilarity:

    @pytest.mark.asyncio
    async def test_similar_requires_body(self, client):
        async with client as c:
            resp = await c.post("/api/v1/similar/1")
        # Should process (empty body uses defaults) or 404 if player not in DB
        assert resp.status_code in (200, 404, 422)


# ── Shortlist ────────────────────────────────────────────────────────


class TestShortlist:

    @pytest.mark.asyncio
    async def test_shortlist_requires_auth(self, client):
        async with client as c:
            resp = await c.get("/api/v1/shortlist")
        assert resp.status_code in (401, 403)  # no bearer token


# ── OpenAPI docs ─────────────────────────────────────────────────────


class TestDocs:

    @pytest.mark.asyncio
    async def test_openapi_schema_loads(self, client):
        async with client as c:
            resp = await c.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "ScoutLens API"
        # Verify key paths exist
        paths = schema["paths"]
        assert "/api/v1/search" in paths
        assert "/api/v1/health" in paths
        assert "/api/v1/auth/register" in paths
        assert "/api/v1/auth/login" in paths
