import pytest
import os
import io
from httpx import AsyncClient, ASGITransport
from app.main import app

BASE = "http://test"

async def get_token(client, suffix="doctest"):
    email = f"doc_{suffix}@test.com"
    reg = await client.post("/api/auth/register", json={
        "email": email,
        "username": f"doc_{suffix}",
        "password": "test123"
    })
    if reg.status_code == 400:
        login = await client.post("/api/auth/login", json={
            "email": email, "password": "test123"
        })
        return login.json()["accessToken"]
    return reg.json()["accessToken"]

def create_test_pdf() -> bytes:
    """Create a minimal valid PDF for testing"""
    return b"""%PDF-1.4
1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj
2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj
3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Parent 2 0 R
/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj
4 0 obj<</Length 44>>stream
BT /F1 12 Tf 100 700 Td (Test document content) Tj ET
endstream endobj
5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000274 00000 n
0000000368 00000 n
trailer<</Size 6/Root 1 0 R>>
startxref
441
%%EOF"""

@pytest.mark.asyncio
async def test_upload_returns_202():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "upload1")
        pdf_content = create_test_pdf()

        response = await client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", io.BytesIO(pdf_content),
                            "application/pdf")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "document_id" in data
        assert data["status"] == "indexed"

@pytest.mark.asyncio
async def test_list_documents():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "list1")
        response = await client.get(
            "/api/documents/",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert "documents" in response.json()
        
@pytest.mark.asyncio
async def test_query_not_found_response():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "query1")
        response = await client.post(
            "/api/documents/query",
            json={
                "question": "What is the population of Mars in 2099?",
                "document_id": "nonexistent-doc-id"
            },
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data

@pytest.mark.asyncio
async def test_delete_nonexistent_document():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "del1")
        response = await client.delete(
            "/api/documents/nonexistent-id",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_upload_non_pdf_rejected():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "pdf1")
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("test.txt",
                            io.BytesIO(b"hello"),
                            "text/plain")},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_query_empty_question_rejected():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token = await get_token(client, "empty1")
        response = await client.post(
            "/api/documents/query",
            json={"question": "   "},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_upload_requires_auth():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        response = await client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf",
                            io.BytesIO(b"fake pdf"),
                            "application/pdf")}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_document_isolation_between_users():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=BASE
    ) as client:
        token1 = await get_token(client, "iso1")
        token2 = await get_token(client, "iso2")

        # User 1 uploads a document
        pdf = create_test_pdf()
        upload = await client.post(
            "/api/documents/upload",
            files={"file": ("doc1.pdf",
                            io.BytesIO(pdf),
                            "application/pdf")},
            headers={"Authorization": f"Bearer {token1}"}
        )
        doc_id = upload.json()["document_id"]

        # User 2 tries to delete user 1's document
        delete = await client.delete(
            f"/api/documents/{doc_id}",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert delete.status_code == 404