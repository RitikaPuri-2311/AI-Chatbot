"""
Company FAQ knowledge-base routing for the Customer Support Assistant.

Automatically scopes policy questions to Company_FAQ.pdf via the existing RAG
pipeline (search_document). Swap filename matching or topic keywords here without
touching LangGraph nodes or support tools.
"""

from __future__ import annotations

import re
from typing import Final

from app.services.rag_service import list_user_documents

# Primary FAQ artifact — matched case-insensitively against indexed filenames.
COMPANY_FAQ_FILENAME: Final[str] = "Company_FAQ.pdf"

FAQ_UNAVAILABLE_MESSAGE: Final[str] = (
    "I wasn't able to find the Company FAQ document in the knowledge base right now. "
    "Please try again later or ask to speak with a human agent for policy details."
)

# Explicit policy topics (customer support persona).
_POLICY_TOPIC_PHRASES: Final[tuple[str, ...]] = (
    "return policy",
    "refund policy",
    "warranty",
    "shipping policy",
    "shipping cost",
    "free shipping",
    "how do you ship",
    "delivery policy",
    "cancellation policy",
    "cancel policy",
    "business hours",
    "opening hours",
    "hours of operation",
    "contact information",
    "contact info",
    "contact us",
    "contact support",
    "how to contact",
    "phone number",
    "support email",
    "customer service email",
)

# Policy-style questions (paired with topic keywords below).
_POLICY_QUESTION_MARKERS: Final[tuple[str, ...]] = (
    "what is",
    "what's",
    "what are",
    "tell me about",
    "explain",
    "how does",
    "how do",
    "do you offer",
    "can i return",
    "can i cancel",
)

_POLICY_TOPIC_WORDS: Final[tuple[str, ...]] = (
    "return",
    "refund",
    "warranty",
    "shipping",
    "cancellation",
    "cancel",
    "hours",
    "contact",
)

# Action requests — must NOT be treated as FAQ policy lookups.
_ACTION_PHRASES: Final[tuple[str, ...]] = (
    "i want a refund",
    "i need a refund",
    "get a refund",
    "request a refund",
    "return my money",
    "want my money back",
    "create a ticket",
    "speak to a human",
    "talk to a human",
    "where is my order",
    "track my order",
    "order status",
    "payment failed",
)

_ORDER_ID_PATTERN = re.compile(r"ORD-\d+", re.IGNORECASE)


def _normalize_filename(filename: str) -> str:
    return (filename or "").lower().replace(" ", "_").replace("-", "_")


def is_company_policy_question(message: str) -> bool:
    """
    True when the customer is asking about company policy (FAQ), not taking action.

    Policy questions are answered from Company_FAQ.pdf automatically.
    """
    text = (message or "").strip()
    if not text:
        return False

    lower = text.lower()

    if _ORDER_ID_PATTERN.search(text):
        return False

    if any(phrase in lower for phrase in _ACTION_PHRASES):
        return False

    if any(phrase in lower for phrase in _POLICY_TOPIC_PHRASES):
        return True

    # "What is your return/refund/warranty/shipping..." style questions
    has_question_marker = any(m in lower for m in _POLICY_QUESTION_MARKERS)
    has_topic_word = any(w in lower for w in _POLICY_TOPIC_WORDS)
    if has_question_marker and has_topic_word:
        return True

    # Standalone policy nouns in a question
    if lower.endswith("?") and any(w in lower for w in ("policy", "warranty", "hours")):
        return True

    return False


def resolve_company_faq_document_id(user_id: str) -> str | None:
    """
    Find the document_id for Company_FAQ.pdf in the user's indexed uploads.

    Matches exact filename or stems containing 'company_faq'.
    """
    target = _normalize_filename(COMPANY_FAQ_FILENAME)
    target_stem = target.removesuffix(".pdf")

    for doc in list_user_documents(user_id):
        filename = doc.get("filename") or ""
        normalized = _normalize_filename(filename)
        stem = normalized.removesuffix(".pdf")

        if normalized == target or stem == target_stem or "company_faq" in stem:
            return doc.get("document_id")

    return None


def company_faq_scope_label(document_id: str | None) -> str:
    """Human-readable label for retrieved FAQ context."""
    if document_id:
        return f"Company FAQ ({COMPANY_FAQ_FILENAME})"
    return "Company FAQ (unavailable)"
