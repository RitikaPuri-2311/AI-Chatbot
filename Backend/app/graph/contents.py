"""Serializable Gemini conversation helpers for LangGraph checkpointing."""

from __future__ import annotations

from typing import Any

from google.genai import types

# Stored in AgentState — JSON/msgpack safe
ContentMessage = dict[str, Any]


def text_message(role: str, text: str) -> ContentMessage:
    return {"role": role, "parts": [text]}


def to_gemini_contents(messages: list[ContentMessage]) -> list[types.Content]:
    """Convert checkpoint-safe messages to Gemini API Content objects."""
    contents: list[types.Content] = []
    for msg in messages:
        if isinstance(msg, types.Content):
            contents.append(msg)
            continue
        if "parts" in msg and msg["parts"] and isinstance(msg["parts"][0], str):
            contents.append(
                types.Content(
                    role=msg["role"],
                    parts=[types.Part(text=msg["parts"][0])],
                )
            )
            continue
        if "serialized" in msg:
            contents.append(types.Content.model_validate(msg["serialized"]))
    return contents


def serialize_content(content: types.Content) -> ContentMessage:
    """Serialize a Gemini Content object for checkpoint storage."""
    return {"role": content.role, "serialized": content.model_dump()}


def append_model_content(
    messages: list[ContentMessage],
    content: types.Content | ContentMessage,
) -> None:
    if isinstance(content, types.Content):
        messages.append(serialize_content(content))
    else:
        messages.append(content)
