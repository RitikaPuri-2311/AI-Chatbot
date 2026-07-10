"""
Intent classification and session-context resolution for the document agent.

Uses an LLM classifier (Gemini) to route between:
  normal_chat | single_document | multi_document | compare | metadata
"""

from __future__ import annotations

import json
import re
from typing import Optional

from google import genai
from google.genai import types

from app.config import settings
from app.graph.state import AgentState, QueryMode
from app.services.rag_service import list_user_documents

client = genai.Client(api_key=settings.GOOGLE_API_KEY)
CLASSIFIER_MODEL = "gemini-2.0-flash"

UUID_PATTERN = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.IGNORECASE,
)

INTENT_TO_MODE: dict[str, QueryMode] = {
    "normal_chat": "normal_chat",
    "single_document_search": "single_document",
    "single_document": "single_document",
    "multi_document_search": "multi_document",
    "multi_document": "multi_document",
    "compare_documents": "compare",
    "compare": "compare",
    "metadata": "metadata",
}


def _extract_document_ids_from_text(text: str) -> list[str]:
    return UUID_PATTERN.findall(text or "")


def resolve_active_document_id(state: AgentState) -> Optional[str]:
    """
    Resolve the document in focus for this turn and follow-ups.

    Priority:
      1. Explicit document_id on the request
      2. Checkpointed active_document_id
      3. UUID in the current user message
      4. Context markers / UUIDs from conversation history
    """
    if state.get("document_id"):
        return state["document_id"]

    if state.get("active_document_id"):
        return state["active_document_id"]

    ids_in_message = _extract_document_ids_from_text(state.get("user_message", ""))
    if len(ids_in_message) == 1:
        return ids_in_message[0]

    for msg in reversed(state.get("conversation_history", [])):
        text = msg.get("parts", [""])[0]
        focus_match = re.search(
            r"\[Context: Focus on document ([0-9a-f-]{36})\]",
            text,
            re.IGNORECASE,
        )
        if focus_match:
            return focus_match.group(1)
        ids = _extract_document_ids_from_text(text)
        if len(ids) == 1:
            return ids[0]

    return None


_FILENAME_STOPWORDS = frozenset({
    "the", "with", "document", "documents", "pdf", "file", "files",
    "compare", "and", "versus", "vs", "between",
})


def _filename_match_score(filename: str, message: str) -> float:
    """Score how well a filename matches terms in the user message."""
    message_lower = (message or "").lower()
    stem = (filename or "").lower()
    for ext in (".pdf", ".docx", ".txt", ".md"):
        if stem.endswith(ext):
            stem = stem[: -len(ext)]
            break

    tokens = re.sub(r"[._\-\s]+", " ", stem).split()
    tokens = [
        t for t in tokens
        if len(t) > 2 and t not in _FILENAME_STOPWORDS
    ]
    if not tokens:
        return 0.0

    score = 0.0
    for token in tokens:
        if token in message_lower:
            score += len(token)

    normalized_stem = re.sub(r"[._\-\s]+", " ", stem).strip()
    if normalized_stem and normalized_stem in message_lower:
        score += 10.0

    return score


def resolve_compare_document_ids_from_names(
    user_id: str,
    user_message: str,
    hint_ids: list[str] | None = None,
) -> list[str]:
    """
    Resolve document IDs for comparison by matching filenames to the user message.
    hint_ids (UUIDs) are preserved first; remaining slots filled by best filename matches.
    """
    hints = [
        h for h in (hint_ids or [])
        if isinstance(h, str) and UUID_PATTERN.fullmatch(h)
    ]
    catalog = list_user_documents(user_id)

    scored: list[tuple[float, str]] = []
    for doc in catalog:
        score = _filename_match_score(doc["filename"], user_message)
        if score > 0:
            scored.append((score, doc["document_id"]))

    scored.sort(key=lambda item: -item[0])

    result: list[str] = []
    for hid in hints:
        if hid not in result:
            result.append(hid)

    for _, doc_id in scored:
        if doc_id not in result:
            result.append(doc_id)
        if len(result) >= 2:
            break

    return result[:2]


def resolve_compare_document_ids(state: AgentState) -> list[str]:
    """Extract up to two document IDs for comparison from state, message, history, and filenames."""
    collected: list[str] = []

    for doc_id in state.get("compare_document_ids") or []:
        if isinstance(doc_id, str) and UUID_PATTERN.fullmatch(doc_id):
            if doc_id not in collected:
                collected.append(doc_id)

    for doc_id in _extract_document_ids_from_text(state.get("user_message", "")):
        if doc_id not in collected:
            collected.append(doc_id)

    for msg in reversed(state.get("conversation_history", [])):
        for doc_id in _extract_document_ids_from_text(msg.get("parts", [""])[0]):
            if doc_id not in collected:
                collected.append(doc_id)
        if len(collected) >= 2:
            break

    active = resolve_active_document_id(state)
    if active and active not in collected:
        collected.insert(0, active)

    if len(collected) < 2 and state.get("user_id"):
        return resolve_compare_document_ids_from_names(
            state["user_id"],
            state.get("user_message", ""),
            collected,
        )

    return collected[:2]


def _history_summary(state: AgentState, limit: int = 4) -> str:
    lines = []
    for msg in state.get("conversation_history", [])[-limit:]:
        role = msg.get("role", "user")
        text = msg.get("parts", [""])[0][:200]
        lines.append(f"{role}: {text}")
    return "\n".join(lines) if lines else "(no prior turns)"


async def classify_query_mode_llm(state: AgentState) -> dict:
    """
    LLM-based intent classifier.

    Returns:
        query_mode, compare_document_ids (optional override), metadata_action
    """
    active_doc = resolve_active_document_id(state)
    compare_ids = resolve_compare_document_ids(state)

    prompt = f"""You are an intent classifier for a document analysis chatbot.
Classify the user's latest message into exactly ONE intent.

Intents:
- normal_chat: greetings, thanks, small talk, or general chat not about documents
- single_document_search: question about content in ONE specific document
- multi_document_search: question that should search across ALL uploaded documents
- compare_documents: user wants to compare two documents
- metadata: user asks about document info, page count, or page list (not content)

Context:
- Request document_id: {state.get("document_id") or "none"}
- Active document_id: {active_doc or "none"}
- Known compare document_ids: {compare_ids or "none"}
- Recent conversation:
{_history_summary(state)}

User message: {state.get("user_message", "")}

Respond with ONLY valid JSON (no markdown):
{{
  "intent": "<one of the intent names above>",
  "compare_document_ids": ["id1", "id2"] or [],
  "metadata_action": "list_pages" or "get_document_info" or null
}}"""

    try:
        response = client.models.generate_content(
            model=CLASSIFIER_MODEL,
            contents=[types.Content(
                role="user",
                parts=[types.Part(text=prompt)],
            )],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        raw = (response.text or "{}").strip()
        data = json.loads(raw)
        intent = data.get("intent", "multi_document_search")
        mode = INTENT_TO_MODE.get(intent, "multi_document")

        llm_compare = [
            d for d in data.get("compare_document_ids", [])
            if isinstance(d, str) and UUID_PATTERN.fullmatch(d)
        ]
        if len(llm_compare) >= 2:
            compare_ids = llm_compare[:2]

        metadata_action = data.get("metadata_action")
        if mode == "metadata" and metadata_action not in (
            "list_pages", "get_document_info", None
        ):
            metadata_action = "get_document_info"

        print(f"🤖 LLM intent: {intent} → {mode}")
        return {
            "query_mode": mode,
            "compare_document_ids": compare_ids,
            "metadata_action": metadata_action,
        }
    except Exception as exc:
        print(f"⚠️ LLM classifier failed ({exc}), falling back to heuristics")
        return _classify_query_mode_fallback(state, active_doc, compare_ids)


def _classify_query_mode_fallback(
    state: AgentState,
    active_doc: Optional[str],
    compare_ids: list[str],
) -> dict:
    """Minimal fallback if the LLM classifier fails."""
    message = (state.get("user_message") or "").lower()
    if any(kw in message for kw in ("compare", " versus ", " vs ", "difference")):
        mode: QueryMode = "compare"
    elif any(kw in message for kw in ("how many pages", "page count", "list pages")):
        mode = "metadata"
    elif active_doc:
        mode = "single_document"
    elif len(message) < 30 and message.startswith(("hi", "hello", "hey", "thanks")):
        mode = "normal_chat"
    else:
        mode = "multi_document"
    return {
        "query_mode": mode,
        "compare_document_ids": compare_ids,
        "metadata_action": None,
    }


def metadata_sub_route(state: AgentState) -> str:
    """Pick metadata tool from LLM metadata_action or message keywords."""
    action = state.get("metadata_action")
    if action in ("list_pages", "get_document_info"):
        return action
    message = (state.get("user_message") or "").lower()
    if "list pages" in message or "page numbers" in message:
        return "list_pages"
    return "get_document_info"
