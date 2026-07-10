"""
Shared state for the document agent LangGraph workflow.

The graph carries conversation context, pending tool calls, retrieved chunks
(for citations), routing mode, and the final answer through each node.
Follow-up turns reuse active_document_id resolved from history + request.
"""

from typing import Any, Literal, Optional, TypedDict

QueryMode = Literal[
    "normal_chat",
    "single_document",
    "multi_document",
    "compare",
    "metadata",
]


class ToolCall(TypedDict):
    tool: str
    args: dict[str, Any]


class SourceCitation(TypedDict, total=False):
    source: str
    page: int
    document_id: str
    text_snippet: str
    similarity: float


class AgentState(TypedDict, total=False):
    # --- Input (set once at graph start) ---
    user_message: str
    user_id: str
    document_id: Optional[str]
    conversation_history: list[dict]
    max_iterations: int

    # --- Session / conversation context (persists through the graph run) ---
    thread_id: Optional[str]
    active_document_id: Optional[str]
    compare_document_ids: list[str]
    query_mode: QueryMode
    routing_hint: str
    metadata_action: Optional[str]

    # --- Gemini conversation (serializable dicts for checkpointing) ---
    contents: list[dict]

    # --- Orchestration ---
    iterations: int
    route: str
    tool_queue: list[ToolCall]
    model_content_pending: Any
    tool_calls_made: list[ToolCall]

    # --- Retrieval results (used for page citations) ---
    retrieved_chunks: list[dict]

    # --- Output ---
    final_answer: str
    sources: list[SourceCitation]
