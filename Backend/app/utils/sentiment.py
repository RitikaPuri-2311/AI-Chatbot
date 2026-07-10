"""
Keyword-based sentiment classifier for support conversations.

Replace with an LLM or dedicated sentiment API in production.
"""

from __future__ import annotations

POSITIVE_KEYWORDS: tuple[str, ...] = (
    "thank",
    "thanks",
    "great",
    "awesome",
    "excellent",
    "happy",
    "pleased",
    "wonderful",
    "perfect",
    "love",
    "appreciate",
    "helpful",
    "resolved",
    "satisfied",
)

NEGATIVE_KEYWORDS: tuple[str, ...] = (
    "angry",
    "frustrated",
    "terrible",
    "awful",
    "horrible",
    "unhappy",
    "disappointed",
    "complaint",
    "worst",
    "hate",
    "broken",
    "useless",
    "ridiculous",
    "unacceptable",
    "furious",
    "upset",
)


def classify_sentiment(text: str) -> str:
    """
    Classify message sentiment as positive, neutral, or negative.

    Uses simple keyword matching — intentionally replaceable.
    """
    lower = (text or "").lower()
    if not lower.strip():
        return "neutral"

    positive_hits = sum(1 for kw in POSITIVE_KEYWORDS if kw in lower)
    negative_hits = sum(1 for kw in NEGATIVE_KEYWORDS if kw in lower)

    if negative_hits > positive_hits:
        return "negative"
    if positive_hits > negative_hits:
        return "positive"
    return "neutral"
