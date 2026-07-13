from fastapi import (
    APIRouter, HTTPException, Depends,
    UploadFile, File
)
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import uuid
import os
import shutil
from app.database import get_db
from app.dependencies import get_current_user
from app.models.document import Document
from app.services.rag_service import (
    index_document,
    delete_document_vectors
)
from app.services.agent_service import (
    run_document_agent,
    stream_document_agent
)
from app.services.redis_service import get_history
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = "./uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class QueryRequest(BaseModel):
    question: str
    document_id: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = False
    faq_mode: bool = False
    weather_mode: bool = False

async def process_in_background(
    filepath: str,
    filename: str,
    user_id: str,
    document_id: str,
    db: AsyncSession
):
    try:
        chunk_count, page_count = index_document(
            filepath, filename, user_id, document_id
        )
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = "indexed"
            doc.chunk_count = chunk_count
            doc.page_count = page_count
            await db.commit()
        print(f"✅ Indexed {chunk_count} chunks from {filename}")
    except Exception as e:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = "failed"
            await db.commit()
        print(f"❌ Indexing failed: {e}")

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Upload a PDF and index it synchronously."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files supported")

    document_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_DIR, f"{document_id}.pdf")

    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    doc = Document(
        id=document_id,
        user_id=current_user.id,
        filename=f"{document_id}.pdf",
        original_name=file.filename,
        status="processing",
    )
    db.add(doc)
    await db.commit()

    print(f"Indexing {file.filename}...")
    try:
        chunk_count, page_count = index_document(
            file_path, file.filename, current_user.id, document_id
        )
        doc.status = "indexed"
        doc.chunk_count = chunk_count
        doc.page_count = page_count
        await db.commit()
        print(f"✅ Indexed {file.filename} — {chunk_count} chunks")
        return {
            "document_id": document_id,
            "original_filename": file.filename,
            "status": "indexed",
            "chunks_created": chunk_count,
            "page_count": page_count,
            "message": "Document uploaded and indexed successfully."
        }
    except Exception as e:
        doc.status = "failed"
        await db.commit()
        print(f"❌ Indexing failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Indexing failed: {str(e)}"
        )

@router.get("/")
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    docs = result.scalars().all()
    return {
        "documents": [
            {
                "id": d.id,
                "filename": d.original_name,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "page_count": d.page_count,
                "created_at": d.created_at.isoformat()
                if d.created_at else ""
            }
            for d in docs
        ]
    }

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    delete_document_vectors(current_user.id, document_id)
    await db.delete(doc)
    await db.commit()

    return {"message": "Document deleted", "document_id": document_id}

@router.post("/query")
async def query_documents(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    if not request.question.strip():
        raise HTTPException(400, "Question cannot be empty")

    # Get conversation history from Redis if session provided
    history = []
    if request.session_id:
        history = get_history(request.session_id) or []

    if request.stream:
        return StreamingResponse(
            stream_document_agent(
                user_message=request.question,
                user_id=current_user.id,
                conversation_history=history,
                document_id=request.document_id,
                session_id=request.session_id,
                faq_mode=request.faq_mode,
                weather_mode=request.weather_mode,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )

    result = await run_document_agent(
        user_message=request.question,
        user_id=current_user.id,
        conversation_history=history,
        document_id=request.document_id,
        session_id=request.session_id,
        faq_mode=request.faq_mode,
        weather_mode=request.weather_mode,
    )

    return result

@router.get("/{document_id}/export")
async def export_document_chat(
    document_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(Document).where(
            Document.id == document_id,
            Document.user_id == current_user.id
        )
    )
    doc = result.scalar_one_or_none()
    if not doc:
        raise HTTPException(404, "Document not found")

    return PlainTextResponse(
        content=f"Document: {doc.original_name}\nStatus: {doc.status}\nChunks: {doc.chunk_count}",
        headers={
            "Content-Disposition": f"attachment; filename={doc.original_name}-info.txt"
        }
    )