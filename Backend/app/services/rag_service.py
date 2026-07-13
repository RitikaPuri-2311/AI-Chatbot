import fitz
import os
import uuid
import hashlib
from sentence_transformers import SentenceTransformer
from langchain_text_splitters import RecursiveCharacterTextSplitter
import chromadb

MODEL = SentenceTransformer('all-MiniLM-L6-v2')

SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=50,
    separators=["\n\n", "\n", ".", " ", ""]
)

CHROMA_PATH = "./documents_chroma_db"
_chroma_client = None


def _get_chroma_client():
    """Reuse a single PersistentClient for all collection access."""
    global _chroma_client
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _chroma_client


def _user_collection_name(user_id: str) -> str:
    """One Chroma collection per user — never use document_id as collection name."""
    return f"user_{user_id.replace('-', '_')}"


def get_chroma_collection(user_id: str):
    """Open the user's collection. User isolation is enforced at collection level."""
    client = _get_chroma_client()
    name = _user_collection_name(user_id)
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"}
    )


def _document_filter(document_id: str | None) -> dict | None:
    """
    Build a Chroma metadata filter for a specific document.
    Chroma requires exactly one top-level operator in `where`;
    document_id is metadata inside the user collection, not a collection name.
    """
    if document_id:
        return {"document_id": document_id}
    return None

def get_chunk_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]

def extract_and_chunk(
    filepath: str,
    filename: str,
    document_id: str
) -> tuple[list[dict], int]:
    doc = fitz.open(filepath)
    chunks = []
    page_count = len(doc)

    for i, page in enumerate(doc):
        text = page.get_text().strip()
        if not text:
            continue
        page_chunks = SPLITTER.split_text(text)
        for j, chunk_text in enumerate(page_chunks):
            if len(chunk_text.strip()) < 20:
                continue
            chunks.append({
                "text": chunk_text.strip(),
                "source": filename,
                "document_id": document_id,
                "page": i + 1,
                "chunk_index": j,
                "chunk_hash": get_chunk_hash(chunk_text)
            })

    doc.close()
    return chunks, page_count

def index_document(
    filepath: str,
    filename: str,
    user_id: str,
    document_id: str
) -> tuple[int, int]:
    chunks, page_count = extract_and_chunk(
        filepath, filename, document_id
    )
    if not chunks:
        return 0, page_count

    collection = get_chroma_collection(user_id)

    # SHA-256 deduplication
    try:
        existing = collection.get(include=["metadatas"])
        existing_hashes = {
            m.get("chunk_hash")
            for m in existing["metadatas"]
            if m.get("chunk_hash")
        }
    except:
        existing_hashes = set()

    new_chunks = [
        c for c in chunks
        if c["chunk_hash"] not in existing_hashes
    ]

    if not new_chunks:
        return 0, page_count

    texts = [c["text"] for c in new_chunks]
    embeddings = MODEL.encode(texts).tolist()

    collection.add(
        embeddings=embeddings,
        documents=texts,
        metadatas=[{
            "source": c["source"],
            "document_id": c["document_id"],
            "page": c["page"],
            "chunk_index": c["chunk_index"],
            "chunk_hash": c["chunk_hash"],
            "user_id": user_id
        } for c in new_chunks],
        ids=[f"{c['document_id']}_p{c['page']}_c{c['chunk_index']}"
             for c in new_chunks]
    )

    return len(new_chunks), page_count

def search_document(
    query: str,
    user_id: str,
    document_id: str = None,
    top_k: int = 5
) -> list[dict]:
    collection = get_chroma_collection(user_id)
    query_embedding = MODEL.encode(query).tolist()
    where = _document_filter(document_id)

    try:
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": top_k * 2,
            "include": ["documents", "distances", "metadatas"],
        }
        if where:
            query_kwargs["where"] = where

        results = collection.query(**query_kwargs)
    except Exception as e:
        print(f"Search error: {e}")
        return []

    chunks = []
    for doc, dist, meta in zip(
        results["documents"][0],
        results["distances"][0],
        results["metadatas"][0]
    ):
        similarity = 1 - dist
        if similarity >= 0.3:
            chunks.append({
                "text": doc,
                "similarity": round(similarity, 4),
                "source": meta.get("source"),
                "document_id": meta.get("document_id"),
                "page": meta.get("page", 0),
            })

    return chunks[:top_k]

def get_document_info(
    user_id: str,
    document_id: str
) -> dict:
    collection = get_chroma_collection(user_id)
    try:
        results = collection.get(
            where={"document_id": document_id},
            include=["metadatas"]
        )
        if not results["metadatas"]:
            return {}

        pages = sorted(set(
            m.get("page", 0)
            for m in results["metadatas"]
        ))
        source = results["metadatas"][0].get("source", "")

        return {
            "document_id": document_id,
            "source": source,
            "total_chunks": len(results["metadatas"]),
            "pages": pages,
            "page_count": max(pages) if pages else 0
        }
    except Exception as e:
        return {"error": str(e)}

def list_user_documents(user_id: str) -> list[dict]:
    """List unique documents indexed for a user (document_id + source filename)."""
    collection = get_chroma_collection(user_id)
    try:
        results = collection.get(include=["metadatas"])
        by_id: dict[str, str] = {}
        for meta in results.get("metadatas") or []:
            doc_id = meta.get("document_id")
            source = meta.get("source") or ""
            if doc_id:
                by_id.setdefault(doc_id, source)
        return [
            {"document_id": doc_id, "filename": filename}
            for doc_id, filename in by_id.items()
        ]
    except Exception as e:
        print(f"list_user_documents error: {e}")
        return []


def list_pages(
    user_id: str,
    document_id: str
) -> list[int]:
    collection = get_chroma_collection(user_id)
    try:
        results = collection.get(
            where={"document_id": document_id},
            include=["metadatas"]
        )
        pages = sorted(set(
            m.get("page", 0)
            for m in results["metadatas"]
        ))
        return pages
    except:
        return []

def delete_document_vectors(
    user_id: str,
    document_id: str
):
    collection = get_chroma_collection(user_id)
    try:
        existing = collection.get(
            where={"document_id": document_id},
            include=["metadatas"]
        )
        if existing["ids"]:
            collection.delete(ids=existing["ids"])
            print(f"Deleted {len(existing['ids'])} vectors")
    except Exception as e:
        print(f"Delete vectors error: {e}")