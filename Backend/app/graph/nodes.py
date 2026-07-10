"""
LangGraph node implementations for the document agent.

Workflow overview
-----------------
0. classify_route   — resolve session context + pick query mode
1. normal_chat      — direct Gemini reply (no RAG)
2. single_document  — RAG search scoped to one document
3. multi_document   — RAG search across all user uploads
4. compare_documents— grounded comparison from both documents
5. get_document_info / list_pages — metadata
6. router           — Gemini tool loop for complex multi-step turns
7. generate_answer  — finalize answer + page/source citations
"""

from __future__ import annotations

import json
from typing import Any

from google import genai
from google.genai import types

from app.config import settings
from app.graph.contents import (
    append_model_content,
    text_message,
    to_gemini_contents,
    serialize_content,
)
from app.graph.routing import (
    UUID_PATTERN,
    classify_query_mode_llm,
    metadata_sub_route,
    resolve_active_document_id,
    resolve_compare_document_ids,
    resolve_compare_document_ids_from_names,
)
from app.graph.state import AgentState, QueryMode, SourceCitation, ToolCall
from app.services.rag_service import (
    get_document_info,
    list_pages,
    list_user_documents,
    search_document,
)

client = genai.Client(api_key=settings.GOOGLE_API_KEY)
MODEL = "gemini-3.1-flash-lite"

TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="search_document",
        description=(
            "Search uploaded documents for relevant information. "
            "Pass document_id to scope to one file; omit it to search all uploads."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "query": types.Schema(
                    type=types.Type.STRING,
                    description="The search query",
                ),
                "document_id": types.Schema(
                    type=types.Type.STRING,
                    description="Optional document ID to search within",
                ),
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="get_document_info",
        description="Get metadata about an uploaded document.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "document_id": types.Schema(
                    type=types.Type.STRING,
                    description="The document ID",
                ),
            },
            required=["document_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="list_pages",
        description="List all page numbers in a document.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "document_id": types.Schema(
                    type=types.Type.STRING,
                    description="The document ID",
                ),
            },
            required=["document_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="compare_documents",
        description="Compare two documents on a specific aspect.",
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "doc1_id": types.Schema(
                    type=types.Type.STRING,
                    description="First document ID",
                ),
                "doc2_id": types.Schema(
                    type=types.Type.STRING,
                    description="Second document ID",
                ),
                "aspect": types.Schema(
                    type=types.Type.STRING,
                    description="What aspect to compare",
                ),
            },
            required=["doc1_id", "doc2_id", "aspect"],
        ),
    ),
])

SYSTEM_PROMPT = """You are a document analysis assistant.
You help users understand and discuss their uploaded documents.

Rules:
1. Always use search_document before answering content questions
2. Always cite page numbers and source document names in your answers
3. If information is not in the documents, say so clearly
4. Never make up information — only use what the tools return
5. For comparisons, use compare_documents with both document IDs
6. For follow-up questions, stay within the active document context when set"""


def _routing_hint_for_mode(
    mode: QueryMode,
    active_document_id: str | None,
    compare_ids: list[str],
) -> str:
    if mode == "single_document" and active_document_id:
        return f"Mode: single-document search. Focus on document {active_document_id}."
    if mode == "multi_document":
        return "Mode: multi-document search. Search across all uploaded documents."
    if mode == "compare" and len(compare_ids) >= 2:
        return (
            f"Mode: document comparison. Compare {compare_ids[0]} "
            f"and {compare_ids[1]}."
        )
    if mode == "metadata":
        return "Mode: document metadata request."
    if mode == "normal_chat":
        return "Mode: normal chat. No document search required."
    return ""


def build_initial_contents(
    user_message: str,
    conversation_history: list[dict],
    document_id: str | None = None,
    routing_hint: str = "",
) -> list[dict]:
    """Build checkpoint-safe messages from system prompt, history, and user turn."""
    contents: list[dict] = [
        text_message("user", f"[System]: {SYSTEM_PROMPT}"),
        text_message("model", "Understood. I'll help analyze documents."),
    ]

    for msg in conversation_history[-10:]:
        contents.append({
            "role": msg["role"],
            "parts": [msg["parts"][0]],
        })

    user_content = user_message
    if document_id:
        user_content = (
            f"[Context: Focus on document {document_id}]\n"
            f"{user_message}"
        )
    if routing_hint:
        user_content = f"[Routing]: {routing_hint}\n{user_content}"

    contents.append(text_message("user", user_content))
    return contents


def _append_model_turn_once(state: AgentState, contents: list[dict]) -> None:
    pending = state.get("model_content_pending")
    if pending is not None:
        if isinstance(pending, dict) and "serialized" in pending:
            contents.append(pending)
        else:
            append_model_content(contents, pending)


def _format_search_results(chunks: list[dict], scope: str = "") -> str:
    if not chunks:
        return "No relevant information found in the documents."

    header = f"Search scope: {scope}\n\n" if scope else ""
    parts = []
    for i, chunk in enumerate(chunks, 1):
        doc_label = chunk.get("source") or chunk.get("document_id", "unknown")
        parts.append(
            f"[Result {i} — {doc_label}, "
            f"Page {chunk['page']}, "
            f"Relevance: {chunk['similarity']:.2f}]\n"
            f"{chunk['text']}"
        )
    return header + "\n\n---\n\n".join(parts)


def _doc_display_name(user_id: str, document_id: str) -> str:
    info = get_document_info(user_id=user_id, document_id=document_id)
    return info.get("source") or document_id[:8]


def _valid_compare_ids(doc1_id: str | None, doc2_id: str | None) -> bool:
    return bool(
        doc1_id
        and doc2_id
        and UUID_PATTERN.fullmatch(doc1_id)
        and UUID_PATTERN.fullmatch(doc2_id)
        and doc1_id != doc2_id
    )


def _resolve_compare_pair(
    state: AgentState,
) -> tuple[str | None, str | None, list[str]]:
    """Resolve two document IDs for comparison from state and filename hints."""
    resolved = resolve_compare_document_ids(state)
    doc1_id = resolved[0] if len(resolved) > 0 else None
    doc2_id = resolved[1] if len(resolved) > 1 else None
    return doc1_id, doc2_id, resolved


def _run_search(
    tool_args: dict,
    user_id: str,
    document_id: str | None,
    scope_label: str,
) -> tuple[str, list[dict]]:
    chunks = search_document(
        query=tool_args.get("query", ""),
        user_id=user_id,
        document_id=document_id,
    )
    return _format_search_results(chunks, scope_label), chunks


def _run_compare(
    tool_args: dict,
    user_id: str,
) -> tuple[str, list[dict]]:
    doc1_id = tool_args.get("doc1_id", "")
    doc2_id = tool_args.get("doc2_id", "")
    aspect = tool_args.get("aspect", tool_args.get("query", ""))

    if not _valid_compare_ids(doc1_id, doc2_id):
        raise ValueError(
            "compare_documents requires two distinct valid document IDs; "
            f"got doc1={doc1_id!r}, doc2={doc2_id!r}"
        )

    doc1_name = _doc_display_name(user_id, doc1_id)
    doc2_name = _doc_display_name(user_id, doc2_id)

    doc1_chunks = search_document(
        query=aspect, user_id=user_id, document_id=doc1_id,
    )
    doc2_chunks = search_document(
        query=aspect, user_id=user_id, document_id=doc2_id,
    )

    doc1_text = "\n".join(
        f"[{doc1_name}, Page {c['page']}] {c['text']}"
        for c in doc1_chunks[:5]
    ) or "No matching content found."
    doc2_text = "\n".join(
        f"[{doc2_name}, Page {c['page']}] {c['text']}"
        for c in doc2_chunks[:5]
    ) or "No matching content found."

    result = (
        f"Comparison aspect: {aspect}\n\n"
        f"=== {doc1_name} (id: {doc1_id[:8]}...) ===\n"
        f"{doc1_text}\n\n"
        f"=== {doc2_name} (id: {doc2_id[:8]}...) ===\n"
        f"{doc2_text}\n\n"
        "Use only the excerpts above when writing the comparison."
    )
    return result, doc1_chunks + doc2_chunks


def _auto_search(
    state: AgentState,
    document_id: str | None,
    scope_label: str,
) -> dict[str, Any]:
    """Run a proactive RAG search and append results to the Gemini conversation."""
    user_id = state["user_id"]
    tool_args = {"query": state["user_message"], "document_id": document_id}
    result, chunks = _run_search(tool_args, user_id, document_id, scope_label)

    tool_call: ToolCall = {
        "tool": "search_document",
        "args": tool_args,
    }
    tool_calls_made = list(state.get("tool_calls_made", []))
    tool_calls_made.append(tool_call)

    retrieved_chunks = list(state.get("retrieved_chunks", []))
    retrieved_chunks.extend(chunks)

    contents = list(state.get("contents", []))
    contents.append(text_message(
        "user",
        f"[Retrieved context — {scope_label}]:\n{result}",
    ))

    return {
        "contents": contents,
        "tool_calls_made": tool_calls_made,
        "retrieved_chunks": retrieved_chunks,
        "route": "router",
    }


def _process_tool_batch(
    state: AgentState,
    tool_name: str,
) -> dict[str, Any]:
    """Execute queued tool calls matching tool_name via rag_service."""
    contents = list(state.get("contents", []))
    tool_queue = list(state.get("tool_queue", []))
    tool_calls_made = list(state.get("tool_calls_made", []))
    retrieved_chunks = list(state.get("retrieved_chunks", []))
    user_id = state["user_id"]
    active_document_id = state.get("active_document_id")

    _append_model_turn_once(state, contents)

    tool_result_texts: list[str] = []
    remaining_queue: list[ToolCall] = []

    for item in tool_queue:
        if item["tool"] != tool_name:
            remaining_queue.append(item)
            continue

        tool_args = item["args"]
        print(f"🔧 Executing tool: {tool_name} with args: {tool_args}")

        try:
            if tool_name == "search_document":
                doc_id = tool_args.get("document_id") or active_document_id
                scope = (
                    f"document {doc_id[:8]}..."
                    if doc_id else "all user documents"
                )
                result, chunks = _run_search(
                    tool_args, user_id, doc_id, scope
                )
                retrieved_chunks.extend(chunks)
            elif tool_name == "compare_documents":
                args = dict(tool_args)
                hints = [
                    h for h in (args.get("doc1_id"), args.get("doc2_id"))
                    if h and UUID_PATTERN.fullmatch(str(h))
                ]
                resolved = resolve_compare_document_ids_from_names(
                    user_id,
                    state.get("user_message", ""),
                    hints,
                )
                if len(resolved) >= 2:
                    args["doc1_id"], args["doc2_id"] = resolved[0], resolved[1]
                if not _valid_compare_ids(args.get("doc1_id"), args.get("doc2_id")):
                    catalog = list_user_documents(user_id)
                    result = (
                        "Cannot compare: need two valid document IDs. "
                        f"Resolved: {resolved}. "
                        f"Available: {[d['filename'] for d in catalog]}"
                    )
                    chunks = []
                else:
                    result, chunks = _run_compare(args, user_id)
                    retrieved_chunks.extend(chunks)
            elif tool_name == "get_document_info":
                doc_id = (
                    tool_args.get("document_id") or active_document_id or ""
                )
                info = get_document_info(user_id=user_id, document_id=doc_id)
                result = json.dumps(info, indent=2)
            elif tool_name == "list_pages":
                doc_id = (
                    tool_args.get("document_id") or active_document_id or ""
                )
                pages = list_pages(user_id=user_id, document_id=doc_id)
                result = f"Document has {len(pages)} pages: {pages}"
            else:
                result = f"Unknown tool: {tool_name}"

            tool_calls_made.append(item)
            print(f"📋 Tool result preview: {result[:100]}...")
            tool_result_texts.append(
                f"[Tool {tool_name} result]:\n{result}"
            )
        except Exception as exc:
            tool_calls_made.append(item)
            tool_result_texts.append(
                f"[Tool {tool_name} error]: {exc}"
            )

    if tool_result_texts:
        contents.append(text_message("user", "\n\n".join(tool_result_texts)))

    return {
        "contents": contents,
        "tool_queue": remaining_queue,
        "tool_calls_made": tool_calls_made,
        "retrieved_chunks": retrieved_chunks,
        "model_content_pending": None,
    }


async def classify_route_node(state: AgentState) -> dict[str, Any]:
    """
    Router entry — resolves conversation context and classifies query mode
    using the LLM intent classifier.
    """
    active_document_id = resolve_active_document_id(state)
    classification = await classify_query_mode_llm({
        **state,
        "active_document_id": active_document_id,
    })
    query_mode = classification["query_mode"]
    compare_document_ids = classification.get(
        "compare_document_ids",
        resolve_compare_document_ids({
            **state,
            "active_document_id": active_document_id,
        }),
    )
    if query_mode == "compare":
        compare_document_ids = resolve_compare_document_ids({
            **state,
            "active_document_id": active_document_id,
            "compare_document_ids": compare_document_ids,
        })
    metadata_action = classification.get("metadata_action")
    routing_hint = _routing_hint_for_mode(
        query_mode, active_document_id, compare_document_ids
    )

    print(f"🧭 Route classified: {query_mode} | active_doc={active_document_id}")

    contents = build_initial_contents(
        state["user_message"],
        state.get("conversation_history", []),
        active_document_id,
        routing_hint,
    )

    return {
        "active_document_id": active_document_id,
        "compare_document_ids": compare_document_ids,
        "query_mode": query_mode,
        "metadata_action": metadata_action,
        "routing_hint": routing_hint,
        "contents": contents,
        "route": query_mode,
    }


async def normal_chat_node(state: AgentState) -> dict[str, Any]:
    """Normal chat — answer without RAG when no document search is needed."""
    print("💬 Normal chat (no RAG)")
    response = client.models.generate_content(
        model=MODEL,
        contents=to_gemini_contents(state["contents"]),
    )
    return {
        "final_answer": response.text or "Hello! How can I help with your documents?",
        "route": "generate_answer",
    }


async def single_document_search_node(state: AgentState) -> dict[str, Any]:
    """Single-document search — RAG scoped to active_document_id."""
    doc_id = state.get("active_document_id")
    print(f"📄 Single-document search → {doc_id}")
    return _auto_search(
        state,
        document_id=doc_id,
        scope_label=f"single document ({doc_id[:8] if doc_id else 'none'}...)",
    )


async def multi_document_search_node(state: AgentState) -> dict[str, Any]:
    """Multi-document search — RAG across all user uploads in Chroma."""
    print("📚 Multi-document search across all uploads")
    return _auto_search(
        state,
        document_id=None,
        scope_label="all user documents",
    )


async def compare_documents_node(state: AgentState) -> dict[str, Any]:
    """
    Compare Documents — retrieves grounded excerpts from both documents,
    then hands off to the router for a cited comparison answer.
    """
    user_id = state["user_id"]
    catalog = list_user_documents(user_id)
    catalog_names = [d["filename"] for d in catalog]

    tool_queue = state.get("tool_queue") or []
    if tool_queue and tool_queue[0]["tool"] == "compare_documents":
        print(
            f"⚖️ [compare ENTER batch] tool_queue={len(tool_queue)}, "
            f"catalog={catalog_names}"
        )
        item = tool_queue[0]
        args = dict(item["args"])
        hints = [
            h for h in (args.get("doc1_id"), args.get("doc2_id"))
            if h and UUID_PATTERN.fullmatch(str(h))
        ]
        resolved = resolve_compare_document_ids_from_names(
            user_id,
            state.get("user_message", ""),
            hints,
        )
        if len(resolved) >= 2:
            args["doc1_id"], args["doc2_id"] = resolved[0], resolved[1]
            item = {"tool": "compare_documents", "args": args}
            state = {**state, "tool_queue": [item] + tool_queue[1:]}

        batch_result = _process_tool_batch(state, "compare_documents")
        print(
            f"⚖️ [compare EXIT batch] chunks={len(batch_result.get('retrieved_chunks', []))}, "
            f"remaining_queue={len(batch_result.get('tool_queue', []))}"
        )
        return batch_result

    compare_ids = state.get("compare_document_ids") or []
    doc1_id, doc2_id, resolved = _resolve_compare_pair(state)

    print(
        f"⚖️ [compare ENTER] compare_ids={compare_ids}, "
        f"resolved=({doc1_id}, {doc2_id}), catalog={catalog_names}"
    )

    if not _valid_compare_ids(doc1_id, doc2_id):
        err = (
            f"Could not identify two documents to compare. "
            f"Available files: {', '.join(catalog_names) or 'none'}. "
            "Please name both documents clearly (e.g. compare X with Y)."
        )
        contents = list(state.get("contents", []))
        contents.append(text_message("user", f"[Comparison error]:\n{err}"))
        print(
            f"⚖️ [compare EXIT] FAILED resolution — "
            f"resolved=({doc1_id}, {doc2_id}), catalog={catalog_names}"
        )
        return {
            "contents": contents,
            "compare_document_ids": resolved,
            "route": "router",
        }

    d1_name = next(
        (d["filename"] for d in catalog if d["document_id"] == doc1_id),
        doc1_id[:8],
    )
    d2_name = next(
        (d["filename"] for d in catalog if d["document_id"] == doc2_id),
        doc2_id[:8],
    )

    tool_args = {
        "doc1_id": doc1_id,
        "doc2_id": doc2_id,
        "aspect": state["user_message"],
    }
    print(
        f"⚖️ [compare] running compare: {d1_name} ({doc1_id}) "
        f"vs {d2_name} ({doc2_id})"
    )

    result, chunks = _run_compare(tool_args, user_id)
    tool_call: ToolCall = {"tool": "compare_documents", "args": tool_args}

    contents = list(state.get("contents", []))
    contents.append(text_message("user", f"[Comparison context]:\n{result}"))

    tool_calls_made = list(state.get("tool_calls_made", []))
    tool_calls_made.append(tool_call)

    prior_chunks = list(state.get("retrieved_chunks", []))
    all_chunks = prior_chunks + chunks

    print(
        f"⚖️ [compare EXIT] doc1={d1_name} ({doc1_id}), "
        f"doc2={d2_name} ({doc2_id}), chunks={len(all_chunks)}"
    )

    return {
        "contents": contents,
        "tool_calls_made": tool_calls_made,
        "retrieved_chunks": all_chunks,
        "compare_document_ids": [doc1_id, doc2_id],
        "route": "router",
    }


async def metadata_node(state: AgentState) -> dict[str, Any]:
    """Document metadata — routes to get_document_info or list_pages."""
    sub_route = metadata_sub_route(state)
    doc_id = state.get("active_document_id") or ""
    tool_args = {"document_id": doc_id}

    print(f"📋 Metadata request → {sub_route}")

    user_id = state["user_id"]
    if sub_route == "list_pages":
        pages = list_pages(user_id=user_id, document_id=doc_id)
        result = f"Document has {len(pages)} pages: {pages}"
    else:
        info = get_document_info(user_id=user_id, document_id=doc_id)
        result = json.dumps(info, indent=2)

    tool_call: ToolCall = {"tool": sub_route, "args": tool_args}
    contents = list(state.get("contents", []))
    contents.append(text_message("user", f"[Metadata result]:\n{result}"))

    return {
        "contents": contents,
        "tool_calls_made": list(state.get("tool_calls_made", [])) + [tool_call],
        "route": "router",
    }


async def router_node(state: AgentState) -> dict[str, Any]:
    """
    Router Node — Gemini synthesizes a grounded answer from retrieved context.
    May call additional tools for multi-step reasoning.
    """
    iterations = state.get("iterations", 0)
    max_iterations = state.get("max_iterations", 5)

    if iterations >= max_iterations:
        return {
            "route": "generate_answer",
            "final_answer": state.get("final_answer")
            or "I was unable to complete the analysis. Please try again.",
        }

    print(f"🔄 Agent iteration {iterations + 1}")

    response = client.models.generate_content(
        model=MODEL,
        contents=to_gemini_contents(state["contents"]),
        config=types.GenerateContentConfig(tools=[TOOLS]),
    )

    candidate = response.candidates[0]
    tool_call_parts: list[Any] = []
    text_parts: list[str] = []

    for part in candidate.content.parts:
        if hasattr(part, "function_call") and part.function_call:
            tool_call_parts.append(part.function_call)
        elif hasattr(part, "text") and part.text:
            text_parts.append(part.text)

    if not tool_call_parts:
        print(f"✅ Agent done after {iterations + 1} iterations")
        return {
            "route": "generate_answer",
            "final_answer": "\n".join(text_parts),
            "iterations": iterations + 1,
        }

    tool_queue: list[ToolCall] = [
        {"tool": fc.name, "args": dict(fc.args)} for fc in tool_call_parts
    ]

    return {
        "route": tool_queue[0]["tool"],
        "tool_queue": tool_queue,
        "model_content_pending": serialize_content(candidate.content),
        "iterations": iterations + 1,
    }


async def search_document_node(state: AgentState) -> dict[str, Any]:
    """Search Document Node — RAG via rag_service (router-initiated)."""
    return _process_tool_batch(state, "search_document")


async def get_document_info_node(state: AgentState) -> dict[str, Any]:
    """Get Document Info Node — metadata from Chroma."""
    return _process_tool_batch(state, "get_document_info")


async def list_pages_node(state: AgentState) -> dict[str, Any]:
    """List Pages Node — page numbers for a document."""
    return _process_tool_batch(state, "list_pages")


def _build_sources(state: AgentState) -> list[SourceCitation]:
    """Build deduplicated citations with source names and page numbers."""
    sources: list[SourceCitation] = []
    seen: set[tuple[str, int, str]] = set()

    for chunk in state.get("retrieved_chunks", []):
        key = (
            chunk.get("source", ""),
            chunk.get("page", 0),
            chunk.get("document_id", ""),
        )
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "source": chunk.get("source", ""),
            "page": chunk.get("page", 0),
            "document_id": chunk.get("document_id", ""),
            "text_snippet": chunk.get("text", "")[:200] + "...",
            "similarity": chunk.get("similarity", 0.0),
        })

    if not sources:
        user_id = state["user_id"]
        active_doc = state.get("active_document_id")
        for call in state.get("tool_calls_made", []):
            if call["tool"] not in ("search_document", "compare_documents"):
                continue
            if call["tool"] == "compare_documents":
                for doc_key in ("doc1_id", "doc2_id"):
                    chunks = search_document(
                        query=call["args"].get("aspect", ""),
                        user_id=user_id,
                        document_id=call["args"].get(doc_key),
                    )
                    for chunk in chunks[:3]:
                        key = (
                            chunk.get("source", ""),
                            chunk.get("page", 0),
                            chunk.get("document_id", ""),
                        )
                        if key not in seen:
                            seen.add(key)
                            sources.append({
                                "source": chunk.get("source", ""),
                                "page": chunk.get("page", 0),
                                "document_id": chunk.get("document_id", ""),
                                "text_snippet": chunk.get("text", "")[:200] + "...",
                                "similarity": chunk.get("similarity", 0.0),
                            })
            else:
                chunks = search_document(
                    query=call["args"].get("query", ""),
                    user_id=user_id,
                    document_id=call["args"].get("document_id") or active_doc,
                )
                for chunk in chunks[:3]:
                    key = (
                        chunk.get("source", ""),
                        chunk.get("page", 0),
                        chunk.get("document_id", ""),
                    )
                    if key not in seen:
                        seen.add(key)
                        sources.append({
                            "source": chunk.get("source", ""),
                            "page": chunk.get("page", 0),
                            "document_id": chunk.get("document_id", ""),
                            "text_snippet": chunk.get("text", "")[:200] + "...",
                            "similarity": chunk.get("similarity", 0.0),
                        })

    return sources


def _append_citation_footer(
    answer: str,
    sources: list[SourceCitation],
) -> str:
    """Append a grounded sources footer when citations are available."""
    if not sources:
        return answer

    lines = ["\n\n**Sources:**"]
    for i, src in enumerate(sources[:5], 1):
        name = src.get("source") or src.get("document_id", "document")
        lines.append(f"{i}. {name}, page {src.get('page', '?')}")
    return answer + "\n".join(lines)


async def generate_answer_node(state: AgentState) -> dict[str, Any]:
    """Generate Answer Node — finalizes response with page + document citations."""
    sources = _build_sources(state)
    final_answer = _append_citation_footer(
        state.get("final_answer")
        or "I was unable to complete the analysis. Please try again.",
        sources,
    )

    return {
        "final_answer": final_answer,
        "sources": sources,
    }
