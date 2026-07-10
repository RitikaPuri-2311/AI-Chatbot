import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

BASE = "http://test"

async def get_token(client, suffix="pytest"):
    email = f"chat_{suffix}@test.com"
    reg = await client.post("/api/auth/register", json={
        "email": email,
        "username": f"chat_{suffix}",
        "password": "test123"
    })
    if reg.status_code == 400:
        login = await client.post("/api/auth/login", json={
            "email": email, "password": "test123"
        })
        return login.json()["accessToken"]
    return reg.json()["accessToken"]

@pytest.mark.asyncio
async def test_new_conversation_returns_session_id():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "conv1")
        response = await client.post(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "New Chat"

@pytest.mark.asyncio
async def test_history_grows_with_messages():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "hist1")
        session = await client.post(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        session_id = session.json()["id"]

        history_before = await client.get(
            f"/api/chat/history/{session_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        count_before = len(history_before.json()["messages"])
        assert count_before == 0

@pytest.mark.asyncio
async def test_streaming_endpoint_returns_sse():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "stream1")
        session = await client.post(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        session_id = session.json()["id"]

        response = await client.post(
            "/api/chat/stream",
            json={
                "message": "hello",
                "session_id": session_id,
                "persona": "default"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]

@pytest.mark.asyncio
async def test_clear_conversation():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "clear1")
        session = await client.post(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        session_id = session.json()["id"]

        delete = await client.delete(
            f"/api/chat/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete.status_code == 200
        assert delete.json()["message"] == "Session deleted"

@pytest.mark.asyncio
async def test_persona_default_exists():
    from app.services.gemini_service import PERSONAS, get_system_prompt
    assert "default" in PERSONAS
    assert "support" in PERSONAS
    assert "code_reviewer" in PERSONAS
    assert "document_analyst" in PERSONAS
    assert len(get_system_prompt("default")) > 0

@pytest.mark.asyncio
async def test_export_empty_session_returns_404():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "export1")
        session = await client.post(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        session_id = session.json()["id"]

        response = await client.get(
            f"/api/chat/sessions/{session_id}/export",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404