"""Gemini function declarations for customer support tools."""

from google.genai import types

SUPPORT_TOOL_DECLARATIONS = [
    types.FunctionDeclaration(
        name="classify_intent",
        description=(
            "Classify the customer's message into a support intent category "
            "(FAQ, Order Status, Refund, Complaint, Technical Support, or General Inquiry). "
            "Use early in a conversation or when the request type is unclear."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "message": types.Schema(
                    type=types.Type.STRING,
                    description="The customer message to classify",
                ),
            },
            required=["message"],
        ),
    ),
    types.FunctionDeclaration(
        name="check_order_status",
        description=(
            "Look up the status of a customer order (e.g. Processing, Shipped, Delivered). "
            "Use when the customer asks about order tracking or delivery."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "order_id": types.Schema(
                    type=types.Type.STRING,
                    description="Order ID (e.g. ORD-10001)",
                ),
            },
            required=["order_id"],
        ),
    ),
    types.FunctionDeclaration(
        name="create_ticket",
        description=(
            "Create a support ticket for issues that need follow-up "
            "(complaints, unresolved problems, refund requests). "
            "Returns a ticket ID and Created status."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "subject": types.Schema(
                    type=types.Type.STRING,
                    description="Short summary of the issue",
                ),
                "description": types.Schema(
                    type=types.Type.STRING,
                    description="Detailed description of the customer's issue",
                ),
                "priority": types.Schema(
                    type=types.Type.STRING,
                    description="Priority: low, medium, high, or urgent",
                ),
            },
            required=["subject", "description"],
        ),
    ),
    types.FunctionDeclaration(
        name="escalate_to_human",
        description=(
            "Escalate the conversation to a human support agent when the customer "
            "requests a person, is frustrated, or the issue cannot be resolved via KB/tools."
        ),
        parameters=types.Schema(
            type=types.Type.OBJECT,
            properties={
                "reason": types.Schema(
                    type=types.Type.STRING,
                    description="Why the conversation is being escalated",
                ),
            },
            required=["reason"],
        ),
    ),
]
