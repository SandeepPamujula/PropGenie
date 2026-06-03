import logging
import os
from typing import Any

from langfuse import Langfuse
from langfuse.client import StatefulSpanClient, StatefulTraceClient

# AWS Bedrock Pricing for Llama 3.1 70B Instruct (USD per token)
LLAMA_3_1_70B_INPUT_COST_PER_TOKEN = 0.00265 / 1000
LLAMA_3_1_70B_OUTPUT_COST_PER_TOKEN = 0.0035 / 1000

logger = logging.getLogger(__name__)

# Initialize Langfuse client from env variables
# Caught errors or missing keys should disable tracing gracefully without crashing the pipeline
langfuse_client: Langfuse | None = None

try:
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    host = os.environ.get("LANGFUSE_HOST", "https://cloud.langfuse.com")

    if public_key and secret_key:
        langfuse_client = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host
        )
    else:
        logger.warning("Langfuse public or secret key missing. Tracing will be disabled.")
except Exception as e:
    logger.error(f"Failed to initialize Langfuse client: {e}")
    langfuse_client = None

def create_trace(session_id: str, ip: str | None = None) -> StatefulTraceClient | None:
    """
    Creates a Langfuse trace tied to the session.
    """
    if not langfuse_client:
        return None
    try:
        return langfuse_client.trace(
            name="propgenie-search",
            session_id=session_id,
            user_id=ip,
            tags=["propgenie"]
        )
    except Exception as e:
        logger.error(f"Error creating Langfuse trace: {e}")
        return None

def create_span(trace: StatefulTraceClient | None, agent_name: str, input_data: Any) -> StatefulSpanClient | None:
    """
    Creates a span for an agent node under the given trace.
    """
    if not trace:
        return None
    try:
        return trace.span(
            name=agent_name,
            input=input_data
        )
    except Exception as e:
        logger.error(f"Error creating Langfuse span for {agent_name}: {e}")
        return None

def end_span(
    span: StatefulSpanClient | None,
    output_data: Any,
    metrics: dict[str, Any] | None = None
) -> None:
    """
    Ends a span and records latency, token counts, cost estimate.
    """
    if not span:
        return
    try:
        metadata = {}
        if metrics:
            if "latency" in metrics:
                metadata["latency_ms"] = metrics["latency"]
            if "input_tokens" in metrics:
                metadata["input_tokens"] = metrics["input_tokens"]
            if "output_tokens" in metrics:
                metadata["output_tokens"] = metrics["output_tokens"]
            if "total_tokens" in metrics:
                metadata["total_tokens"] = metrics["total_tokens"]
            if "cost" in metrics:
                metadata["cost"] = metrics["cost"]
            if "hallucination_detected" in metrics:
                metadata["hallucination_detected"] = metrics["hallucination_detected"]
            # Copy other keys that are not explicitly processed
            for k, v in metrics.items():
                if k not in ["latency", "input_tokens", "output_tokens", "total_tokens", "cost", "hallucination_detected"]:
                    metadata[k] = v

        span.end(
            output=output_data,
            metadata=metadata
        )
    except Exception as e:
        logger.error(f"Error ending Langfuse span: {e}")

def update_trace_metadata(
    trace: StatefulTraceClient | None,
    metadata: dict[str, Any],
    tags: list[str] | None = None
) -> None:
    """
    Updates trace level metadata and tags.
    """
    if not trace:
        return
    try:
        trace.update(metadata=metadata, tags=tags)
    except Exception as e:
        logger.error(f"Error updating Langfuse trace: {e}")

def flush_traces() -> None:
    """
    Flushes all buffered Langfuse traces to the server.
    """
    if not langfuse_client:
        return
    try:
        langfuse_client.flush()
    except Exception as e:
        logger.error(f"Error flushing Langfuse traces: {e}")
