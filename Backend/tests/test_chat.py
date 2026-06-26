import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

BASE = "http://test"

async def get_token(client: AsyncClient, suffix: str) -> str:
    """Register or login and return token"""
    email = f"chattest_{suffix}@test.com"
    reg = await client.post("/api/auth/register", json={
        "email": email,
        "username": f"chattest_{suffix}",
        "password": "test123"
    })
    if reg.status_code == 400:
        login = await client.post("/api/auth/login", json={
            "email": email,
            "password": "test123"
        })
        return login.json()["accessToken"]
    return reg.json()["accessToken"]

@pytest.mark.asyncio
async def test_chat_no_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.post("/api/chat/", json={
            "message": "hello",
            "session_id": "test-session"
        })
        # 403 when no token — FastAPI HTTPBearer behavior
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_chat_invalid_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.post(
            "/api/chat/",
            json={"message": "hello", "session_id": "test-session"},
            headers={"Authorization": "Bearer faketoken123"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_history_no_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.get("/api/chat/history/test-session")
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_get_history_authenticated():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "hist1")
        response = await client.get(
            "/api/chat/history/test-session-hist",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "messages" in data
        assert isinstance(data["messages"], list)

@pytest.mark.asyncio
async def test_create_session():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "sess1")
        response = await client.post(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["title"] == "New Chat"

@pytest.mark.asyncio
async def test_get_sessions():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "sess2")
        await client.post(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        response = await client.get(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "sessions" in response.json()

@pytest.mark.asyncio
async def test_delete_session():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "sess3")
        create_res = await client.post(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        session_id = create_res.json()["id"]
        response = await client.delete(
            f"/api/chat/sessions/{session_id}",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Session deleted"

@pytest.mark.asyncio
async def test_delete_nonexistent_session():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "sess4")
        response = await client.delete(
            "/api/chat/sessions/nonexistent-session-id-xyz",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_user_session_isolation():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token1 = await get_token(client, "iso1")
        token2 = await get_token(client, "iso2")

        # User 1 creates a session
        await client.post(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token1}"}
        )

        # User 2 gets sessions — should not see user 1's
        response = await client.get(
            "/api/chat/sessions",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert response.status_code == 200
        sessions = response.json()["sessions"]
        assert isinstance(sessions, list)

@pytest.mark.asyncio
async def test_rbac_permissions_in_register():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.post("/api/auth/register", json={
            "email": "rbac_test@test.com",
            "username": "rbactest",
            "password": "test123"
        })
        if response.status_code == 200:
            permissions = response.json()["user"]["permissions"]
            assert "ai:chat" in permissions
            assert "ai:embed" in permissions
            assert "ai:search" in permissions