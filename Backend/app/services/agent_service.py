"""
Customer support agent service — public API for the documents router.

Orchestration is handled by LangGraph (app/graph/). This module keeps the
same function signatures so API routes and tests remain unchanged.
"""

import json

from app.graph.graph import run_document_graph
from app.services.redis_service import append_messages, is_available


def _persist_conversation(
    session_id: str | None,
    user_message: str,
    answer: str,
) -> None:
    """Save Q&A to Redis so follow-up document queries have history."""
    if not session_id or not answer:
        return
    if is_available():
        saved = append_messages(session_id, user_message, answer)
        if saved:
            print(f"✅ Document conversation saved to Redis ({session_id})")


async def run_document_agent(
    user_message: str,
    user_id: str,
    conversation_history: list = None,
    document_id: str = None,
    session_id: str = None,
    max_iterations: int = 5,
    faq_mode: bool = False,
) -> dict:
    """
    Run the customer support agent via LangGraph.

    Returns:
        answer     — final Gemini response text
        sources    — citations from knowledge base retrieval
        tool_calls — tools invoked during the run
        iterations — router loop count
    """
    result = await run_document_graph(
        user_message=user_message,
        user_id=user_id,
        conversation_history=conversation_history,
        document_id=document_id,
        session_id=session_id,
        max_iterations=max_iterations,
        faq_mode=faq_mode,
    )

    _persist_conversation(session_id, user_message, result.get("answer", ""))
    return result


async def stream_document_agent(
    user_message: str,
    user_id: str,
    conversation_history: list = None,
    document_id: str = None,
    session_id: str = None,
    faq_mode: bool = False,
):
    """
    Streaming version — yields status updates and final answer.
    Shows the user what the agent is doing in real time.
    """
    if conversation_history is None:
        conversation_history = []

    yield "data: 🤔 Looking into that for you...\n\n"

    result = await run_document_agent(
        user_message=user_message,
        user_id=user_id,
        conversation_history=conversation_history,
        document_id=document_id,
        session_id=session_id,
        faq_mode=faq_mode,
    )

    for call in result["tool_calls"]:
        if call["tool"] == "search_document":
            yield f"data: 🔍 Searching knowledge base: {call['args'].get('query', '')}\n\n"
        elif call["tool"] == "get_document_info":
            yield "data: 📄 Checking article details...\n\n"
        elif call["tool"] == "compare_documents":
            yield "data: ⚖️ Comparing knowledge base articles...\n\n"
        elif call["tool"] == "list_pages":
            yield "data: 📑 Listing article pages...\n\n"
        elif call["tool"] == "classify_intent":
            yield "data: 🏷️ Classifying your request...\n\n"
        elif call["tool"] == "check_order_status":
            yield f"data: 📦 Checking order {call['args'].get('order_id', '')}...\n\n"
        elif call["tool"] == "create_ticket":
            yield "data: 🎫 Creating support ticket...\n\n"
        elif call["tool"] == "escalate_to_human":
            yield "data: 🙋 Escalating to a human agent...\n\n"

    if result.get("query_mode") == "company_faq":
        yield "data: 📋 Searching Company FAQ for policy information...\n\n"
    elif result.get("query_mode") == "multi_document":
        yield "data: 📚 Searching the full knowledge base...\n\n"
    elif result.get("query_mode") == "single_document":
        yield "data: 📄 Searching selected article...\n\n"

    answer = result["answer"]
    words = answer.split(" ")
    chunk_size = 5

    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i : i + chunk_size]) + " "
        yield f"data: {chunk}\n\n"

    if result["sources"]:
        sources_json = json.dumps(result["sources"])
        yield f"data: [SOURCES]{sources_json}[/SOURCES]\n\n"

    yield "data: [DONE]\n\n"
