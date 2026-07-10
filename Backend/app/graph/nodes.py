"""
LangGraph node implementations for the AI Customer Support Assistant.

Workflow overview
-----------------
0. classify_route   — resolve session context + pick query mode
1. normal_chat      — direct Gemini reply (no RAG)
2. single_document  — RAG search scoped to one knowledge base article
3. multi_document   — RAG search across the full knowledge base
4. compare_documents— grounded comparison of two articles
5. get_document_info / list_pages — metadata
6. router           — Gemini tool loop for complex multi-step turns
7. generate_answer  — finalize answer + source citations
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
from app.graph.prompts import (
    CUSTOMER_SUPPORT_SYSTEM_PROMPT,
    GENERATE_ANSWER_FALLBACK,
    MODEL_ACKNOWLEDGMENT,
    NO_KB_RESULTS,
    NORMAL_CHAT_FALLBACK,
    UNABLE_TO_COMPLETE,
    routing_hint_for_mode,
)
from app.graph.state import AgentState, QueryMode, SourceCitation, ToolCall
from app.graph.support_tool_defs import SUPPORT_TOOL_DECLARATIONS
from app.services.rag_service import (
    get_document_info,
    list_pages,
    list_user_documents,
    search_document,
)
from app.services.support_tools import (
    SUPPORT_TOOL_NAMES,
    detect_support_tool_request,
    execute_support_tool,
    followup_support_hint,
    is_support_request,
)
from app.services.company_faq import (
    FAQ_UNAVAILABLE_MESSAGE,
    company_faq_scope_label,
    is_company_policy_question,
    resolve_company_faq_document_id,
)

client = genai.Client(api_key=settings.GOOGLE_API_KEY)
MODEL = "gemini-3.1-flash-lite"

TOOLS = types.Tool(function_declarations=[
    types.FunctionDeclaration(
        name="search_document",
        description=(
            "Search the knowledge base for information relevant to the customer's question. "
            "Pass document_id to scope to one article; omit it to search the full knowledge base."
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
                    description="Optional knowledge base article ID to search within",
                ),
            },
            required=["query"],
        ),
    ),
    types.FunctionDeclaration(
        name="get_document_info",
        description="Get metadata about a knowledge base article (title, pages, etc.).",
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
        description="List all page numbers in a knowledge base article.",
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
        description=(
            "Compare two knowledge base articles on a specific aspect "
            "to help answer the customer's question."
        ),
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
    *SUPPORT_TOOL_DECLARATIONS,
])

SYSTEM_PROMPT = CUSTOMER_SUPPORT_SYSTEM_PROMPT


def _registered_tool_names() -> list[str]:
    return [fd.name for fd in TOOLS.function_declarations]


def _function_call_args(fc: Any) -> dict[str, Any]:
    raw = getattr(fc, "args", None)
    if raw is None:
        return {}
    if isinstance(raw, dict):
        return raw
    try:
        return dict(raw)
    except Exception:
        return {}


def _extract_function_calls(candidate: Any) -> tuple[list[Any], list[str]]:
    """Parse Gemini candidate for function calls and text parts."""
    tool_call_parts: list[Any] = []
    text_parts: list[str] = []
    content = getattr(candidate, "content", None)
    if not content or not getattr(content, "parts", None):
        return tool_call_parts, text_parts

    for part in content.parts:
        fc = getattr(part, "function_call", None)
        name = getattr(fc, "name", None) if fc else None
        if fc and name:
            args = _function_call_args(fc)
            tool_call_parts.append(fc)
            print(f"📞 Gemini function_call: {name} args={args}")
        elif getattr(part, "text", None):
            text_parts.append(part.text)
            preview = (part.text or "").strip().replace("\n", " ")[:120]
            if preview:
                print(f"💬 Gemini text (no tool call): {preview}")

    return tool_call_parts, text_parts


def _build_router_config(state: AgentState) -> types.GenerateContentConfig:
    """Build Gemini config; force function calling on support paths."""
    force_tools = (
        state.get("query_mode") == "support"
        or state.get("support_tool_hint") is not None
    )
    if force_tools:
        print("🔒 Support path: forcing Gemini function calling mode=ANY")
        return types.GenerateContentConfig(
            tools=[TOOLS],
            tool_config=types.ToolConfig(
                function_calling_config=types.FunctionCallingConfig(
                    mode=types.FunctionCallingConfigMode.ANY,
                )
            ),
        )
    return types.GenerateContentConfig(tools=[TOOLS])


def build_initial_contents(
    user_message: str,
    conversation_history: list[dict],
    document_id: str | None = None,
    routing_hint: str = "",
) -> list[dict]:
    """Build checkpoint-safe messages from system prompt, history, and user turn."""
    contents: list[dict] = [
        text_message("user", f"[System]: {SYSTEM_PROMPT}"),
        text_message("model", MODEL_ACKNOWLEDGMENT),
    ]

    for msg in conversation_history[-10:]:
        contents.append({
            "role": msg["role"],
            "parts": [msg["parts"][0]],
        })

    user_content = user_message
    if document_id:
        user_content = (
            f"[Context: Focus on knowledge base article {document_id}]\n"
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
        return NO_KB_RESULTS

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
    last_classify_payload: dict[str, Any] | None = None

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
                    f"article {doc_id[:8]}..."
                    if doc_id else "full knowledge base"
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
                        "Cannot compare: need two valid knowledge base article IDs. "
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
            elif tool_name in SUPPORT_TOOL_NAMES:
                args = dict(tool_args)
                if tool_name == "classify_intent" and not args.get("message"):
                    args["message"] = state.get("user_message", "")
                print(f"🎫 Dispatching support tool: {tool_name} args={args}")
                payload = execute_support_tool(
                    tool_name,
                    args,
                    user_id=user_id,
                    session_id=state.get("thread_id"),
                )
                result = json.dumps(payload, indent=2)
                print(f"🎫 Support tool result ({tool_name}): {result[:200]}...")
                if tool_name == "classify_intent":
                    last_classify_payload = payload
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

    batch_update: dict[str, Any] = {
        "contents": contents,
        "tool_queue": remaining_queue,
        "tool_calls_made": tool_calls_made,
        "retrieved_chunks": retrieved_chunks,
        "model_content_pending": None,
    }

    if tool_name == "classify_intent" and last_classify_payload:
        followup = followup_support_hint(
            last_classify_payload, state.get("user_message", "")
        )
        if followup:
            batch_update["support_tool_hint"] = followup
            contents.append(text_message(
                "user",
                f"[Support routing]: Intent classified. You MUST call "
                f"{followup['tool']} next with args {json.dumps(followup['args'])}.",
            ))
            batch_update["contents"] = contents
            print(f"🔁 Follow-up support hint set: {followup['tool']}")

    return batch_update


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
    support_tool_hint = None

    if state.get("force_query_mode") == "company_faq":
        query_mode = "company_faq"
        print("📋 FAQ mode forced from client → query_mode=company_faq")
    elif detect_support_tool_request(state.get("user_message", "")):
        query_mode = "support"
        support_tool_hint = detect_support_tool_request(state.get("user_message", ""))
        print(f"🎧 Support request detected → query_mode=support hint={support_tool_hint}")
    elif is_company_policy_question(state.get("user_message", "")):
        query_mode = "company_faq"
        print("📋 Company policy question detected → query_mode=company_faq")
    elif is_support_request(state.get("user_message", "")):
        query_mode = "support"
        support_tool_hint = detect_support_tool_request(state.get("user_message", ""))
        print(f"🎧 Support request detected → query_mode=support hint={support_tool_hint}")

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
    routing_hint = routing_hint_for_mode(
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
        "support_tool_hint": support_tool_hint,
        "contents": contents,
        "route": query_mode,
    }


async def support_entry_node(state: AgentState) -> dict[str, Any]:
    """
    Support entry — skip knowledge base search and route to router with tool hints.
    """
    print("🎧 Support entry node → router (no proactive RAG)")
    hint = (
        state.get("support_tool_hint")
        or detect_support_tool_request(state.get("user_message", ""))
    )
    contents = list(state.get("contents", []))
    if hint:
        contents.append(text_message(
            "user",
            f"[Support routing]: You MUST call {hint['tool']} now with args "
            f"{json.dumps(hint['args'])}. Do NOT answer without calling this tool.",
        ))
        print(f"🎧 Support tool hint injected: {hint['tool']}")
    return {
        "contents": contents,
        "support_tool_hint": hint,
        "query_mode": "support",
        "route": "router",
    }


async def company_faq_search_node(state: AgentState) -> dict[str, Any]:
    """
    Company FAQ — proactive RAG search scoped to Company_FAQ.pdf.

    Uses search_document() via _auto_search. No manual document selection required.
    """
    user_id = state["user_id"]
    faq_doc_id = resolve_company_faq_document_id(user_id)
    scope = company_faq_scope_label(faq_doc_id)

    print(f"📋 Company FAQ search → document_id={faq_doc_id or 'NOT FOUND'}")

    if not faq_doc_id:
        contents = list(state.get("contents", []))
        contents.append(text_message(
            "user",
            f"[Company FAQ unavailable]:\n{FAQ_UNAVAILABLE_MESSAGE}",
        ))
        return {
            "contents": contents,
            "query_mode": "company_faq",
            "route": "router",
        }

    return _auto_search(
        state,
        document_id=faq_doc_id,
        scope_label=scope,
    )


async def normal_chat_node(state: AgentState) -> dict[str, Any]:
    """Conversational support — answer without RAG when no knowledge lookup is needed."""
    if is_company_policy_question(state.get("user_message", "")):
        print("↪️ Redirecting policy question from normal_chat to Company FAQ")
        return await company_faq_search_node(state)

    if is_support_request(state.get("user_message", "")):
        print("↪️ Redirecting misclassified support request from normal_chat")
        return await support_entry_node(state)

    print("💬 Normal chat (no RAG)")
    response = client.models.generate_content(
        model=MODEL,
        contents=to_gemini_contents(state["contents"]),
    )
    return {
        "final_answer": response.text or NORMAL_CHAT_FALLBACK,
        "route": "generate_answer",
    }


async def single_document_search_node(state: AgentState) -> dict[str, Any]:
    """Single-document search — RAG scoped to active_document_id."""
    if is_company_policy_question(state.get("user_message", "")):
        print("↪️ Redirecting policy question from single_document to Company FAQ")
        return await company_faq_search_node(state)

    if is_support_request(state.get("user_message", "")):
        print("↪️ Skipping KB search — support request in single_document path")
        return await support_entry_node(state)

    doc_id = state.get("active_document_id")
    print(f"📄 Single-document search → {doc_id}")
    return _auto_search(
        state,
        document_id=doc_id,
        scope_label=f"knowledge base article ({doc_id[:8] if doc_id else 'none'}...)",
    )


async def multi_document_search_node(state: AgentState) -> dict[str, Any]:
    """Multi-document search — RAG across all user uploads in Chroma."""
    if is_company_policy_question(state.get("user_message", "")):
        print("↪️ Redirecting policy question from multi_document to Company FAQ")
        return await company_faq_search_node(state)

    if is_support_request(state.get("user_message", "")):
        print("↪️ Skipping KB search — support request in multi_document path")
        return await support_entry_node(state)

    print("📚 Multi-document search across all uploads")
    return _auto_search(
        state,
        document_id=None,
        scope_label="full knowledge base",
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
            f"Could not identify two knowledge base articles to compare. "
            f"Available articles: {', '.join(catalog_names) or 'none'}. "
            "Please name both articles clearly (e.g. compare X with Y)."
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
            "final_answer": state.get("final_answer") or UNABLE_TO_COMPLETE,
        }

    print(f"🔄 Agent iteration {iterations + 1}")

    tool_names = _registered_tool_names()
    print(f"🛠️ Passing {len(tool_names)} tools to Gemini: {tool_names}")

    response = client.models.generate_content(
        model=MODEL,
        contents=to_gemini_contents(state["contents"]),
        config=_build_router_config(state),
    )

    candidate = response.candidates[0]
    tool_call_parts, text_parts = _extract_function_calls(candidate)

    if not tool_call_parts:
        hint = (
            state.get("support_tool_hint")
            or detect_support_tool_request(state.get("user_message", ""))
        )
        if hint and hint["tool"] in SUPPORT_TOOL_NAMES:
            print(
                f"⚡ Proactive support dispatch (Gemini returned no tool call): "
                f"{hint['tool']} args={hint['args']}"
            )
            return {
                "route": hint["tool"],
                "tool_queue": [{"tool": hint["tool"], "args": dict(hint["args"])}],
                "iterations": iterations + 1,
            }

        print(f"✅ Agent done after {iterations + 1} iterations (text only)")
        return {
            "route": "generate_answer",
            "final_answer": "\n".join(text_parts) or GENERATE_ANSWER_FALLBACK,
            "iterations": iterations + 1,
        }

    tool_queue: list[ToolCall] = [
        {"tool": fc.name, "args": _function_call_args(fc)}
        for fc in tool_call_parts
    ]
    print(f"🔀 Router dispatching to graph node: {tool_queue[0]['tool']}")

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


def make_tool_node(tool_name: str):
    """Factory for router-initiated tool nodes (RAG and support tools)."""
    async def node(state: AgentState) -> dict[str, Any]:
        print(f"📍 Graph node executing: {tool_name}")
        return _process_tool_batch(state, tool_name)

    node.__name__ = f"{tool_name}_node"
    node.__qualname__ = f"{tool_name}_node"
    return node


# Support tool nodes — registered dynamically in graph.py via SUPPORT_TOOL_NAMES
create_ticket_node = make_tool_node("create_ticket")
check_order_status_node = make_tool_node("check_order_status")
escalate_to_human_node = make_tool_node("escalate_to_human")
classify_intent_node = make_tool_node("classify_intent")

SUPPORT_TOOL_NODE_MAP = {
    "create_ticket": create_ticket_node,
    "check_order_status": check_order_status_node,
    "escalate_to_human": escalate_to_human_node,
    "classify_intent": classify_intent_node,
}


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

    lines = ["\n\n**References:**"]
    for i, src in enumerate(sources[:5], 1):
        name = src.get("source") or src.get("document_id", "document")
        lines.append(f"{i}. {name}, page {src.get('page', '?')}")
    return answer + "\n".join(lines)


async def generate_answer_node(state: AgentState) -> dict[str, Any]:
    """Generate Answer Node — finalizes response with page + document citations."""
    sources = _build_sources(state)
    final_answer = _append_citation_footer(
        state.get("final_answer") or GENERATE_ANSWER_FALLBACK,
        sources,
    )

    return {
        "final_answer": final_answer,
        "sources": sources,
    }
