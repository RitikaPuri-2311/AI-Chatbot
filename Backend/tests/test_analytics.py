import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from tests.conftest import app
from app.services.analytics_service import format_duration
from app.utils.sentiment import classify_sentiment

BASE = "http://test"

MOCK_AGENT_RESULT = {
    "answer": "Your order has been shipped.",
    "sources": [],
    "tool_calls": [{"tool": "check_order_status", "args": {"order_id": "ORD-10002"}}],
    "iterations": 1,
    "query_mode": "support",
}


async def get_token(client, suffix: str) -> str:
    email = f"analytics_{suffix}@test.com"
    reg = await client.post(
        "/api/auth/register",
        json={
            "email": email,
            "username": f"analytics_{suffix}",
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


def test_sentiment_calculation():
    assert classify_sentiment("Thank you so much, great help!") == "positive"
    assert classify_sentiment("I am furious and this is terrible") == "negative"
    assert classify_sentiment("Where is my order?") == "neutral"


def test_format_duration():
    assert format_duration(150) == "2m 30s"
    assert format_duration(45) == "45s"
    assert format_duration(0) == "0s"


@pytest.mark.asyncio
@patch(
    "app.services.conversation_service.invoke_support_agent",
    new_callable=AsyncMock,
)
async def test_conversation_count_analytics(mock_agent):
    mock_agent.return_value = MOCK_AGENT_RESULT

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE,
    ) as client:
        token = await get_token(client, "count1")

        for title in ("Order issue", "Refund request"):
            create = await client.post(
                "/api/conversations",
                json={"title": title, "persona": "support"},
                headers={"Authorization": f"Bearer {token}"},
            )
            conv_id = create.json()["id"]
            await client.post(
                f"/api/conversations/{conv_id}/messages",
                json={
                    "role": "user",
                    "content": "Where is my order ORD-10002?",
                },
                headers={"Authorization": f"Bearer {token}"},
            )

        response = await client.get(
            "/api/analytics/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_conversations"] >= 2
        assert data["most_used_persona"] == "support"
        assert data["average_messages"] >= 1


@pytest.mark.asyncio
@patch(
    "app.services.conversation_service.invoke_support_agent",
    new_callable=AsyncMock,
)
async def test_topic_aggregation(mock_agent):
    mock_agent.return_value = MOCK_AGENT_RESULT

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE,
    ) as client:
        token = await get_token(client, "topics1")
        create = await client.post(
            "/api/conversations",
            json={"title": "Order issue", "persona": "support"},
            headers={"Authorization": f"Bearer {token}"},
        )
        conv_id = create.json()["id"]
        await client.post(
            f"/api/conversations/{conv_id}/messages",
            json={
                "role": "user",
                "content": "Where is my order ORD-10002?",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.get(
            "/api/analytics/topics",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        topics = response.json()["topics"]
        assert any(t["topic"] == "Order Status" for t in topics)


@pytest.mark.asyncio
@patch(
    "app.services.conversation_service.invoke_support_agent",
    new_callable=AsyncMock,
)
async def test_sentiment_analytics_endpoint(mock_agent):
    mock_agent.return_value = MOCK_AGENT_RESULT

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE,
    ) as client:
        token = await get_token(client, "sent1")
        create = await client.post(
            "/api/conversations",
            json={"title": "Feedback", "persona": "support"},
            headers={"Authorization": f"Bearer {token}"},
        )
        conv_id = create.json()["id"]

        await client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"role": "user", "content": "Thank you, great service!"},
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"role": "user", "content": "This is terrible and I am angry"},
            headers={"Authorization": f"Bearer {token}"},
        )

        response = await client.get(
            "/api/analytics/sentiment",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["positive"] >= 1
        assert data["negative"] >= 1
        assert data["neutral"] >= 0
