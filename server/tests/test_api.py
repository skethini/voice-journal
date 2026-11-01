import os

import pytest
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("LLM_MODEL", "mock")
os.environ.setdefault("PASSCODE_HASH", "")

from app.main import app


@pytest.mark.asyncio
async def test_health():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/health")
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_guidance_crud():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post("/guidance", json={"text": "help me stay accountable"})
        assert r.status_code == 200
        r = await client.get("/guidance")
        assert len(r.json()["items"]) == 1
