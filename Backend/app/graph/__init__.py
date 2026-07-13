"""LangGraph orchestration for the AI Customer Support Assistant."""

__all__ = ["run_document_graph", "AGENT_PERSONA"]


def __getattr__(name: str):
    if name == "run_document_graph":
        from app.graph.graph import run_document_graph

        return run_document_graph
    if name == "AGENT_PERSONA":
        from app.graph.prompts import AGENT_PERSONA

        return AGENT_PERSONA
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
