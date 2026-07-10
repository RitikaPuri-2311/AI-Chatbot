"""
LangGraph workflow definition for the document analysis agent.

Graph topology
--------------
                         ┌──────────────────┐
                         │  classify_route  │
                         └────────┬─────────┘
            ┌──────────┬─────────┼──────────┬────────────┐
            ▼          ▼         ▼          ▼            ▼
      normal_chat  single_doc  multi_doc  compare     metadata
            │          │         │          │            │
            │          └────┬────┴────┬─────┴────────────┘
            │               ▼         │
            │            router ◄─────┘  (tool loop)
            │               │
            ▼               ▼
      generate_answer ◄─────┘
            │
            ▼
           END
"""

from __future__ import annotations

import uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    classify_route_node,
    compare_documents_node,
    generate_answer_node,
    get_document_info_node,
    list_pages_node,
    metadata_node,
    multi_document_search_node,
    normal_chat_node,
    router_node,
    search_document_node,
    single_document_search_node,
)
from app.graph.state import AgentState, QueryMode

_compiled_graph = None
_checkpointer = MemorySaver()

ROUTER_TOOL_NODES = {
    "search_document",
    "compare_documents",
    "get_document_info",
    "list_pages",
}

MODE_ENTRY_NODES: dict[QueryMode, str] = {
    "normal_chat": "normal_chat",
    "single_document": "single_document_search",
    "multi_document": "multi_document_search",
    "compare": "compare_documents",
    "metadata": "metadata",
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

    graph.add_node("router", router_node)
    graph.add_node("search_document", search_document_node)
    graph.add_node("get_document_info", get_document_info_node)
    graph.add_node("list_pages", list_pages_node)

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
        },
    )

    graph.add_edge("normal_chat", "generate_answer")
    graph.add_edge("single_document_search", "router")
    graph.add_edge("multi_document_search", "router")
    graph.add_edge("metadata", "router")

    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {
            "search_document": "search_document",
            "compare_documents": "compare_documents",
            "get_document_info": "get_document_info",
            "list_pages": "list_pages",
            "generate_answer": "generate_answer",
        },
    )

    for tool_node in ROUTER_TOOL_NODES:
        graph.add_conditional_edges(
            tool_node,
            _route_after_tool,
            {
                "router": "router",
                "search_document": "search_document",
                "compare_documents": "compare_documents",
                "get_document_info": "get_document_info",
                "list_pages": "list_pages",
            },
        )

    graph.add_edge("generate_answer", END)

    return graph.compile(checkpointer=_checkpointer)


def get_document_graph():
    """Return the singleton compiled graph."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_document_graph()
    return _compiled_graph


async def run_document_graph(
    user_message: str,
    user_id: str,
    conversation_history: list | None = None,
    document_id: str | None = None,
    session_id: str | None = None,
    max_iterations: int = 5,
) -> dict:
    """
    Run the LangGraph document agent workflow.

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
