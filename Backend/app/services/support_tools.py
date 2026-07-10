"""
Mock customer support tools for the LangGraph agent.

Swap these implementations for Jira, order-management APIs, and live escalation
queues without changing the LangGraph workflow or tool names.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any, Final

SUPPORT_TOOL_NAMES: Final[frozenset[str]] = frozenset({
    "create_ticket",
    "check_order_status",
    "escalate_to_human",
    "classify_intent",
})

SUPPORT_INTENT_CATEGORIES: Final[tuple[str, ...]] = (
    "FAQ",
    "Order Status",
    "Refund",
    "Complaint",
    "Technical Support",
    "General Inquiry",
)

_MOCK_ORDER_STATUSES: Final[tuple[str, ...]] = (
    "Processing",
    "Shipped",
    "Delivered",
)

_MOCK_ORDERS: Final[dict[str, str]] = {
    "ORD-10001": "Processing",
    "ORD-10002": "Shipped",
    "ORD-10003": "Delivered",
}

_ticket_counter = 100
_escalation_counter = 200


def _next_ticket_id() -> str:
    global _ticket_counter
    _ticket_counter += 1
    return f"SUP-{_ticket_counter}"


def _next_escalation_id() -> str:
    global _escalation_counter
    _escalation_counter += 1
    return f"ESC-{_escalation_counter}"


def _mock_status_for_order(order_id: str) -> str:
    if order_id in _MOCK_ORDERS:
        return _MOCK_ORDERS[order_id]
    index = int(hashlib.md5(order_id.encode()).hexdigest(), 16) % len(_MOCK_ORDER_STATUSES)
    return _MOCK_ORDER_STATUSES[index]


def classify_intent(message: str) -> dict[str, Any]:
    """
    Classify a customer message into a support intent category.

    Mock implementation uses keyword heuristics. Replace with an LLM or
    classifier service when moving to production.
    """
    text = (message or "").strip()
    lower = text.lower()

    if any(kw in lower for kw in ("where is my order", "track", "tracking", "shipment", "delivery status")):
        category = "Order Status"
        confidence = 0.92
    elif any(kw in lower for kw in ("order", "ord-", "shipping", "delivered", "shipped")):
        category = "Order Status"
        confidence = 0.85
    elif any(kw in lower for kw in ("refund", "money back", "chargeback", "return my money")):
        if "refund policy" in lower or "return policy" in lower:
            category = "FAQ"
            confidence = 0.9
        else:
            category = "Refund"
            confidence = 0.9
    elif any(kw in lower for kw in ("complaint", "unhappy", "terrible", "awful", "frustrated", "angry")):
        category = "Complaint"
        confidence = 0.88
    elif any(kw in lower for kw in ("error", "bug", "not working", "broken", "technical", "login", "crash")):
        category = "Technical Support"
        confidence = 0.87
    elif any(kw in lower for kw in ("how do", "what is", "faq", "policy", "hours", "pricing")):
        category = "FAQ"
        confidence = 0.8
    else:
        category = "General Inquiry"
        confidence = 0.7

    return {
        "intent": category,
        "confidence": confidence,
        "message": text,
        "categories": list(SUPPORT_INTENT_CATEGORIES),
    }


def create_ticket(
    subject: str,
    description: str,
    priority: str = "medium",
    *,
    user_id: str | None = None,
) -> dict[str, Any]:
    """
    Create a support ticket.

    Mock: returns a generated ticket ID. Replace with Jira / Zendesk API calls.
    """
    ticket_id = _next_ticket_id()
    normalized_priority = (priority or "medium").lower()
    if normalized_priority not in ("low", "medium", "high", "urgent"):
        normalized_priority = "medium"

    return {
        "ticket_id": ticket_id,
        "status": "Created",
        "subject": subject,
        "description": description,
        "priority": normalized_priority,
        "user_id": user_id,
    }


def check_order_status(order_id: str) -> dict[str, Any]:
    """
    Look up order status by order ID.

    Mock: returns sample statuses. Replace with order-management API integration.
    """
    cleaned = (order_id or "").strip().upper()
    if not cleaned:
        return {
            "order_id": order_id,
            "status": "Unknown",
            "error": "order_id is required",
        }

    if not re.match(r"^ORD-\d+$", cleaned):
        cleaned = f"ORD-{re.sub(r'[^0-9]', '', cleaned) or '10001'}"

    status = _mock_status_for_order(cleaned)
    details: dict[str, Any] = {
        "order_id": cleaned,
        "status": status,
    }

    if status == "Processing":
        details["estimated_ship_date"] = "2026-07-12"
    elif status == "Shipped":
        details["carrier"] = "FedEx"
        details["tracking_number"] = "1Z999AA10123456784"
    elif status == "Delivered":
        details["delivered_at"] = "2026-07-08T14:30:00Z"

    return details


def escalate_to_human(
    reason: str,
    *,
    user_id: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Escalate the conversation to a human agent.

    Mock: returns confirmation metadata. Replace with queue / CRM integration.
    """
    escalation_id = _next_escalation_id()
    return {
        "escalated": True,
        "escalation_id": escalation_id,
        "status": "Queued",
        "reason": reason,
        "message": (
            "Your conversation has been escalated to a human support agent. "
            "Someone will follow up with you shortly."
        ),
        "estimated_wait_minutes": 15,
        "user_id": user_id,
        "session_id": session_id,
    }


def execute_support_tool(
    tool_name: str,
    args: dict[str, Any],
    *,
    user_id: str,
    session_id: str | None = None,
) -> dict[str, Any]:
    """
    Dispatch a support tool by name. Single entry point for LangGraph tool execution.
    """
    if tool_name not in SUPPORT_TOOL_NAMES:
        raise ValueError(f"Unknown support tool: {tool_name}")

    if tool_name == "classify_intent":
        return classify_intent(args.get("message", ""))
    if tool_name == "create_ticket":
        return create_ticket(
            subject=args.get("subject", "Support request"),
            description=args.get("description", ""),
            priority=args.get("priority", "medium"),
            user_id=user_id,
        )
    if tool_name == "check_order_status":
        return check_order_status(args.get("order_id", ""))
    if tool_name == "escalate_to_human":
        return escalate_to_human(
            reason=args.get("reason", "Customer requested human assistance"),
            user_id=user_id,
            session_id=session_id,
        )

    raise ValueError(f"Unhandled support tool: {tool_name}")


_ORDER_ID_PATTERN = re.compile(r"ORD-\d+", re.IGNORECASE)

_SUPPORT_KEYWORDS: Final[dict[str, tuple[str, ...]]] = {
    "check_order_status": (
        "where is my order",
        "order status",
        "track my order",
        "tracking number",
        "track order",
        "delivery status",
        "when will my order",
    ),
    "create_ticket": (
        "create a ticket",
        "create ticket",
        "support ticket",
        "open a ticket",
        "file a ticket",
        "payment failed",
    ),
    "escalate_to_human": (
        "speak to a human",
        "speak to human",
        "talk to a human",
        "talk to human",
        "human agent",
        "real person",
        "live agent",
        "transfer me",
    ),
    "classify_intent": (
        "i want a refund",
        "i need a refund",
        "get a refund",
        "request a refund",
        "want my money back",
        "return my money",
    ),
}


def detect_support_tool_request(message: str) -> dict[str, Any] | None:
    """
    Detect a support tool request from the customer message.

    Returns {"tool": str, "args": dict} when a support tool should run.
    Used for routing and proactive dispatch when Gemini skips tool calls.
    """
    text = (message or "").strip()
    if not text:
        return None

    lower = text.lower()
    order_match = _ORDER_ID_PATTERN.search(text)

    if order_match or any(kw in lower for kw in _SUPPORT_KEYWORDS["check_order_status"]):
        order_id = order_match.group(0).upper() if order_match else "ORD-10001"
        return {"tool": "check_order_status", "args": {"order_id": order_id}}

    if any(kw in lower for kw in _SUPPORT_KEYWORDS["escalate_to_human"]):
        return {
            "tool": "escalate_to_human",
            "args": {"reason": text},
        }

    if any(kw in lower for kw in _SUPPORT_KEYWORDS["create_ticket"]):
        subject = "Payment issue" if "payment" in lower else "Support request"
        return {
            "tool": "create_ticket",
            "args": {
                "subject": subject,
                "description": text,
                "priority": "high" if "payment failed" in lower else "medium",
            },
        }

    if any(kw in lower for kw in _SUPPORT_KEYWORDS["classify_intent"]):
        return {"tool": "classify_intent", "args": {"message": text}}

    return None


def is_support_request(message: str) -> bool:
    """True when the message should be handled via support tools, not plain chat."""
    from app.services.company_faq import is_company_policy_question

    if is_company_policy_question(message):
        return False
    if detect_support_tool_request(message):
        return True
    intent = classify_intent(message).get("intent")
    return intent in ("Order Status", "Refund", "Complaint", "Technical Support")


def followup_support_hint(
    classify_result: dict[str, Any],
    user_message: str,
) -> dict[str, Any] | None:
    """After classify_intent, suggest the next support tool (e.g. Refund → create_ticket)."""
    intent = classify_result.get("intent")
    if intent in ("Refund", "Complaint"):
        return {
            "tool": "create_ticket",
            "args": {
                "subject": f"{intent} request",
                "description": user_message,
                "priority": "high" if intent == "Complaint" else "medium",
            },
        }
    if intent == "Order Status":
        hint = detect_support_tool_request(user_message)
        if hint and hint["tool"] == "check_order_status":
            return hint
    return None
