"""Langfuse observability wiring."""

import os
from contextlib import contextmanager
from datetime import datetime

from langfuse import Langfuse

# Lazy init: only if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY are set
_client = None


def get_langfuse_client() -> Langfuse | None:
    """Get or initialize Langfuse client."""
    global _client
    if _client is None:
        pk = os.getenv("LANGFUSE_PUBLIC_KEY")
        sk = os.getenv("LANGFUSE_SECRET_KEY")
        host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        if pk and sk:
            _client = Langfuse(
                public_key=pk,
                secret_key=sk,
                host=host,
            )
    return _client


@contextmanager
def trace_agent_call(agent_name: str, input_data: dict):
    """Context manager to trace an agent invocation.

    Usage:
        with trace_agent_call("research_agent", {"domain": "linear.app"}):
            profile = await research_agent.enrich("linear.app")
    """
    client = get_langfuse_client()
    if not client:
        # No-op if Langfuse not configured
        yield
        return

    trace = client.trace(
        name=agent_name,
        input=input_data,
        start_time=datetime.utcnow(),
    )

    try:
        yield trace
    except Exception as e:
        trace.event(
            name="error",
            input={
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
        )
        raise
    finally:
        trace.end(end_time=datetime.utcnow())


def log_generation(
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    cost_usd: float,
    output: str,
    trace_id: str | None = None,
):
    """Log an LLM call to Langfuse."""
    client = get_langfuse_client()
    if not client:
        return

    client.generation(
        name=f"generation-{model}",
        model=model,
        input={"prompt_tokens": prompt_tokens},
        output=output,
        usage={
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
        },
        metadata={
            "cost_usd": cost_usd,
        },
        trace_id=trace_id,
    )
