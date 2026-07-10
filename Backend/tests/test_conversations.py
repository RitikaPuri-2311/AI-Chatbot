import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from tests.conftest import app
from app.utils.sentiment import classify_sentiment

BASE = "http://test"

MOCK_AGENT_RESULT = {
    "answer": "Your order ORD-10002 has been shipped.",
    "sources": [
        {
            "source": "Company_FAQ.pdf",
            "page": 1,
            "text_snippet": "Shipping takes 3-5 days.",
            "similarity": 0.91,
        }
    ],
    "tool_calls": [{"tool": "check_order_status", "args": {"order_id": "ORD-10002"}}],
    "iterations": 1,
    "query_mode": "support",
}


async def get_token(client: AsyncClient, suffix: str) -> str:
    email = f"conv_{suffix}@test.com"
    reg = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": f"conv_{suffix}",
            "password": "test123",
        },
    )
    if reg.status_code == 200:
        return reg.json()["accessToken"]

    login = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "test123"},
    )
    assert login.status_code == 200, login.text
    return login.json()["accessToken"]


@pytest.mark.asyncio
async def test_create_conversation():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE,
    ) as client:
        token = await get_token(client, "create1")
        response = await client.post(
            "/api/conversations",
            json={"title": "Order issue", "persona": "support"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "Order issue"
        assert data["persona"] == "support"
        assert "id" in data
        assert "created_at" in data


@pytest.mark.asyncio
@patch(
    "app.services.conversation_service.invoke_support_agent",
    new_callable=AsyncMock,
)
async def test_add_message(mock_agent):
    mock_agent.return_value = MOCK_AGENT_RESULT

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE,
    ) as client:
        token = await get_token(client, "msg1")
        create = await client.post(
            "/api/conversations",
            json={"title": "Order issue", "persona": "support"},
            headers={"Authorization": f"Bearer {token}"},
        )
        conversation_id = create.json()["id"]

        response = await client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "content": "Where is my order ORD-10002?",
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["conversation_id"] == conversation_id
        assert data["message"]["role"] == "assistant"
        assert "ORD-10002" in data["message"]["content"]
        assert len(data["message"]["sources"]) == 1
        mock_agent.assert_awaited_once()


@pytest.mark.asyncio
@patch(
    "app.services.conversation_service.invoke_support_agent",
    new_callable=AsyncMock,
)
async def test_get_conversation_history(mock_agent):
    mock_agent.return_value = MOCK_AGENT_RESULT

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE,
    ) as client:
        token = await get_token(client, "hist1")
        create = await client.post(
            "/api/conversations",
            json={"title": "Order issue", "persona": "support"},
            headers={"Authorization": f"Bearer {token}"},
        )
        conversation_id = create.json()["id"]

        await client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "content": "Where is my order ORD-10002?",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.get(
            f"/api/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conversation_id
        assert data["persona"] == "support"
        assert len(data["messages"]) == 2
        assert data["messages"][0]["role"] == "user"
        assert data["messages"][1]["role"] == "assistant"
        assert "timestamp" in data["messages"][0]


@pytest.mark.asyncio
@patch(
    "app.services.conversation_service.invoke_support_agent",
    new_callable=AsyncMock,
)
async def test_delete_conversation(mock_agent):
    mock_agent.return_value = MOCK_AGENT_RESULT

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE,
    ) as client:
        token = await get_token(client, "del1")
        create = await client.post(
            "/api/conversations",
            json={"title": "Order issue", "persona": "support"},
            headers={"Authorization": f"Bearer {token}"},
        )
        conversation_id = create.json()["id"]

        await client.post(
            f"/api/conversations/{conversation_id}/messages",
            json={
                "role": "user",
                "content": "Where is my order ORD-10002?",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        delete = await client.delete(
            f"/api/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert delete.status_code == 200

        fetch = await client.get(
            f"/api/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert fetch.status_code == 404


@pytest.mark.asyncio
async def test_conversation_requires_auth():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE,
    ) as client:
        response = await client.post(
            "/api/conversations",
            json={"title": "Order issue", "persona": "support"},
        )
        assert response.status_code == 401
