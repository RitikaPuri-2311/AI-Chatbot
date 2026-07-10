"""
LangGraph workflow for the AI Customer Support Assistant.

The graph topology and RAG pipeline are unchanged; persona and instructions
are configured in app/graph/prompts.py.
"""

from __future__ import annotations

import uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    SUPPORT_TOOL_NODE_MAP,
    classify_route_node,
    compare_documents_node,
    company_faq_search_node,
    generate_answer_node,
    get_document_info_node,
    list_pages_node,
    metadata_node,
    multi_document_search_node,
    normal_chat_node,
    router_node,
    search_document_node,
    single_document_search_node,
    support_entry_node,
)
from app.graph.state import AgentState, QueryMode
from app.services.support_tools import SUPPORT_TOOL_NAMES

_compiled_graph = None
_checkpointer = MemorySaver()

_BASE_ROUTER_TOOL_NODES = {
    "search_document",
    "compare_documents",
    "get_document_info",
    "list_pages",
}

ROUTER_TOOL_NODES = _BASE_ROUTER_TOOL_NODES | set(SUPPORT_TOOL_NAMES)

MODE_ENTRY_NODES: dict[QueryMode, str] = {
    "normal_chat": "normal_chat",
    "single_document": "single_document_search",
    "multi_document": "multi_document_search",
    "compare": "compare_documents",
    "metadata": "metadata",
    "support": "support_entry",
    "company_faq": "company_faq_search",
}


def _route_after_classify(state: AgentState) -> str:
    """Dispatch from classify_route to the mode-specific entry node."""
    mode = state.get("query_mode", "multi_document")
    return MODE_ENTRY_NODES.get(mode, "multi_document_search")


def _route_after_router(state: AgentState) -> str:
    """Router → tool node or generate_answer."""
    route = state.get("route", "generate_answer")
    if route in ROUTER_TOOL_NODES:
        return route
    return "generate_answer"


def _route_after_tool(state: AgentState) -> str:
    """After a router-initiated tool, chain next tool or return to router."""
    tool_queue = state.get("tool_queue") or []
    if tool_queue:
        next_tool = tool_queue[0]["tool"]
        if next_tool in ROUTER_TOOL_NODES:
            return next_tool
    return "router"


def _route_after_normal_chat(state: AgentState) -> str:
    """Support misroutes to router; greetings go straight to generate_answer."""
    if state.get("route") == "router" or state.get("query_mode") == "support":
        return "router"
    return "generate_answer"


def _thread_id(session_id: str) -> str:
    """LangGraph checkpoint thread id scoped to document agent sessions."""
    return f"doc:{session_id}"


def build_document_graph():
    """Build and compile the LangGraph StateGraph with MemorySaver checkpointing."""
    graph = StateGraph(AgentState)

    graph.add_node("classify_route", classify_route_node)
    graph.add_node("normal_chat", normal_chat_node)
    graph.add_node("single_document_search", single_document_search_node)
    graph.add_node("multi_document_search", multi_document_search_node)
    graph.add_node("compare_documents", compare_documents_node)
    graph.add_node("metadata", metadata_node)
    graph.add_node("support_entry", support_entry_node)
    graph.add_node("company_faq_search", company_faq_search_node)

    graph.add_node("router", router_node)
    graph.add_node("search_document", search_document_node)
    graph.add_node("get_document_info", get_document_info_node)
    graph.add_node("list_pages", list_pages_node)

    for tool_name, tool_node in SUPPORT_TOOL_NODE_MAP.items():
        graph.add_node(tool_name, tool_node)

    graph.add_node("generate_answer", generate_answer_node)

    graph.set_entry_point("classify_route")

    graph.add_conditional_edges(
        "classify_route",
        _route_after_classify,
        {
            "normal_chat": "normal_chat",
            "single_document_search": "single_document_search",
            "multi_document_search": "multi_document_search",
            "compare_documents": "compare_documents",
            "metadata": "metadata",
            "support_entry": "support_entry",
            "company_faq_search": "company_faq_search",
        },
    )

    graph.add_conditional_edges(
        "normal_chat",
        _route_after_normal_chat,
        {
            "router": "router",
            "generate_answer": "generate_answer",
        },
    )
    graph.add_edge("support_entry", "router")
    graph.add_edge("company_faq_search", "router")
    graph.add_edge("single_document_search", "router")
    graph.add_edge("multi_document_search", "router")
    graph.add_edge("metadata", "router")

    router_conditional_targets = {
        "search_document": "search_document",
        "compare_documents": "compare_documents",
        "get_document_info": "get_document_info",
        "list_pages": "list_pages",
        "generate_answer": "generate_answer",
    }
    for tool_name in SUPPORT_TOOL_NAMES:
        router_conditional_targets[tool_name] = tool_name

    graph.add_conditional_edges(
        "router",
        _route_after_router,
        router_conditional_targets,
    )

    tool_chain_targets = {
        "router": "router",
        "search_document": "search_document",
        "compare_documents": "compare_documents",
        "get_document_info": "get_document_info",
        "list_pages": "list_pages",
    }
    for tool_name in SUPPORT_TOOL_NAMES:
        tool_chain_targets[tool_name] = tool_name

    for tool_node in ROUTER_TOOL_NODES:
        graph.add_conditional_edges(
            tool_node,
            _route_after_tool,
            tool_chain_targets,
        )

    graph.add_edge("generate_answer", END)

    return graph.compile(checkpointer=_checkpointer)


def get_document_graph():
    """Return the singleton compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_document_graph()
        support_nodes = sorted(SUPPORT_TOOL_NAMES)
        print(f"✅ LangGraph compiled — support tool nodes: {support_nodes}")
    return _compiled_graph


async def run_document_graph(
    user_message: str,
    user_id: str,
    conversation_history: list | None = None,
    document_id: str | None = None,
    session_id: str | None = None,
    max_iterations: int = 5,
    faq_mode: bool = False,
) -> dict:
    """
    Run the LangGraph customer support agent workflow.

    When session_id is provided:
      - Loads prior graph state via MemorySaver (thread_id=doc:{session_id})
      - Persists active_document_id / compare_document_ids across requests

    Returns:
      { answer, sources, tool_calls, iterations, query_mode, active_document_id }
    """
    if conversation_history is None:
        conversation_history = []

    # Per-turn input — ephemeral fields reset; session fields merge from checkpoint
    input_state: AgentState = {
        "user_message": user_message,
        "user_id": user_id,
        "conversation_history": conversation_history,
        "max_iterations": max_iterations,
        "tool_queue": [],
        "retrieved_chunks": [],
        "tool_calls_made": [],
        "final_answer": "",
        "sources": [],
        "iterations": 0,
        "contents": [],
    }
    if document_id is not None:
        input_state["document_id"] = document_id
    if session_id:
        input_state["thread_id"] = _thread_id(session_id)
    if faq_mode:
        input_state["force_query_mode"] = "company_faq"

    thread = (
        _thread_id(session_id)
        if session_id
        else f"doc:ephemeral:{uuid.uuid4()}"
    )
    config = {"configurable": {"thread_id": thread}}

    graph = get_document_graph()
    final_state = await graph.ainvoke(input_state, config)

    return {
        "answer": final_state.get("final_answer", ""),
        "sources": final_state.get("sources", []),
        "tool_calls": final_state.get("tool_calls_made", []),
        "iterations": final_state.get("iterations", 0),
        "query_mode": final_state.get("query_mode"),
        "active_document_id": final_state.get("active_document_id"),
    }
