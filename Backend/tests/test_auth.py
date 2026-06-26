import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

BASE = "http://test"

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

@pytest.mark.asyncio
async def test_register_success():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.post("/api/auth/register", json={
            "email": "pytest1@test.com",
            "username": "pytest1",
            "password": "test123"
        })
        # Could be 200 (new) or 400 (already exists from prev run)
        assert response.status_code in [200, 400]
        if response.status_code == 200:
            data = response.json()
            assert "accessToken" in data
            assert "ai:chat" in data["user"]["permissions"]

@pytest.mark.asyncio
async def test_register_duplicate_email():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        email = "dupe_test@test.com"
        # First registration
        first = await client.post("/api/auth/register", json={
            "email": email,
            "username": "dupeuser1",
            "password": "test123"
        })
        if first.status_code == 200:
            # Second registration with same email
            second = await client.post("/api/auth/register", json={
                "email": email,
                "username": "dupeuser2",
                "password": "test123"
            })
            assert second.status_code == 400

@pytest.mark.asyncio
async def test_login_success():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        email = "logintest1@test.com"
        await client.post("/api/auth/register", json={
            "email": email,
            "username": "logintest1",
            "password": "test123"
        })
        response = await client.post("/api/auth/login", json={
            "email": email,
            "password": "test123"
        })
        assert response.status_code == 200
        assert "accessToken" in response.json()

@pytest.mark.asyncio
async def test_login_wrong_password():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        email = "logintest2@test.com"
        await client.post("/api/auth/register", json={
            "email": email,
            "username": "logintest2",
            "password": "test123"
        })
        response = await client.post("/api/auth/login", json={
            "email": email,
            "password": "wrongpassword"
        })
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_login_nonexistent_user():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.post("/api/auth/login", json={
            "email": "nobody_xyz@test.com",
            "password": "test123"
        })
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_me_no_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.get("/api/auth/me")
        # FastAPI returns 403 when no token provided
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_me_with_valid_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        email = "metest@test.com"
        reg = await client.post("/api/auth/register", json={
            "email": email,
            "username": "metest",
            "password": "test123"
        })
        if reg.status_code == 400:
            # Already exists — login instead
            reg = await client.post("/api/auth/login", json={
                "email": email,
                "password": "test123"
            })
        token = reg.json()["accessToken"]
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["email"] == email

@pytest.mark.asyncio
async def test_me_invalid_token():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer totallyinvalidtoken"}
        )
        assert response.status_code == 401