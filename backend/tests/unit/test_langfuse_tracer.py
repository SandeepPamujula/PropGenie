from unittest.mock import MagicMock, patch

import pytest

from observability import langfuse_tracer


@pytest.fixture
def mock_langfuse_client():
    with patch("observability.langfuse_tracer.langfuse_client") as mock_client:
        yield mock_client

def test_create_trace_success(mock_langfuse_client):
    """Test that create_trace successfully calls trace() on the client."""
    mock_trace = MagicMock()
    mock_langfuse_client.trace.return_value = mock_trace

    trace = langfuse_tracer.create_trace(session_id="session-123", ip="127.0.0.1")

    assert trace == mock_trace
    mock_langfuse_client.trace.assert_called_once_with(
        name="propgenie-search",
        session_id="session-123",
        user_id="127.0.0.1",
        tags=["propgenie"]
    )

def test_create_trace_disabled_client():
    """Test that create_trace returns None if client is not initialized."""
    with patch("observability.langfuse_tracer.langfuse_client", None):
        trace = langfuse_tracer.create_trace(session_id="session-123")
        assert trace is None

def test_create_trace_exception_handled(mock_langfuse_client):
    """Test that create_trace logs error and fails gracefully on exception."""
    mock_langfuse_client.trace.side_effect = Exception("Langfuse connection error")

    # Should not raise exception
    trace = langfuse_tracer.create_trace(session_id="session-123")
    assert trace is None

def test_create_span_success():
    """Test that create_span successfully calls span() on the trace."""
    mock_trace = MagicMock()
    mock_span = MagicMock()
    mock_trace.span.return_value = mock_span

    span = langfuse_tracer.create_span(mock_trace, "orchestrator", "user query")

    assert span == mock_span
    mock_trace.span.assert_called_once_with(
        name="orchestrator",
        input="user query"
    )

def test_create_span_none_trace():
    """Test that create_span returns None if trace is None."""
    span = langfuse_tracer.create_span(None, "orchestrator", "user query")
    assert span is None

def test_create_span_exception_handled():
    """Test that create_span fails gracefully on trace.span() exception."""
    mock_trace = MagicMock()
    mock_trace.span.side_effect = Exception("Span creation failure")

    span = langfuse_tracer.create_span(mock_trace, "orchestrator", "user query")
    assert span is None

def test_end_span_success():
    """Test that end_span successfully updates metrics and calls end() on the span."""
    mock_span = MagicMock()
    metrics = {
        "latency": 150,
        "input_tokens": 100,
        "output_tokens": 50,
        "total_tokens": 150,
        "cost": 0.0005,
        "custom_metric": "value"
    }

    langfuse_tracer.end_span(mock_span, "output data", metrics)

    mock_span.end.assert_called_once()
    kwargs = mock_span.end.call_args.kwargs
    assert kwargs["output"] == "output data"
    assert kwargs["metadata"]["latency_ms"] == 150
    assert kwargs["metadata"]["input_tokens"] == 100
    assert kwargs["metadata"]["output_tokens"] == 50
    assert kwargs["metadata"]["total_tokens"] == 150
    assert kwargs["metadata"]["cost"] == 0.0005
    assert kwargs["metadata"]["custom_metric"] == "value"

def test_end_span_none_span():
    """Test that end_span handles None span gracefully."""
    # Should not raise exception
    langfuse_tracer.end_span(None, "output")

def test_end_span_exception_handled():
    """Test that end_span fails gracefully on span.end() exception."""
    mock_span = MagicMock()
    mock_span.end.side_effect = Exception("Span end failure")

    # Should not raise exception
    langfuse_tracer.end_span(mock_span, "output")

def test_update_trace_metadata_success():
    """Test that update_trace_metadata calls update on the trace."""
    mock_trace = MagicMock()
    langfuse_tracer.update_trace_metadata(mock_trace, {"key": "val"}, ["tag1"])

    mock_trace.update.assert_called_once_with(
        metadata={"key": "val"},
        tags=["tag1"]
    )

def test_update_trace_metadata_none_trace():
    """Test that update_trace_metadata handles None trace gracefully."""
    # Should not raise exception
    langfuse_tracer.update_trace_metadata(None, {"key": "val"})

def test_update_trace_metadata_exception_handled():
    """Test that update_trace_metadata fails gracefully on trace.update() exception."""
    mock_trace = MagicMock()
    mock_trace.update.side_effect = Exception("Trace update failure")

    # Should not raise exception
    langfuse_tracer.update_trace_metadata(mock_trace, {"key": "val"})

def test_flush_traces_success(mock_langfuse_client):
    """Test that flush_traces calls flush on the client."""
    langfuse_tracer.flush_traces()
    mock_langfuse_client.flush.assert_called_once()

def test_flush_traces_none_client():
    """Test that flush_traces handles None client gracefully."""
    with patch("observability.langfuse_tracer.langfuse_client", None):
        # Should not raise exception
        langfuse_tracer.flush_traces()

def test_flush_traces_exception_handled(mock_langfuse_client):
    """Test that flush_traces fails gracefully on client.flush() exception."""
    mock_langfuse_client.flush.side_effect = Exception("Flush failure")

    # Should not raise exception
    langfuse_tracer.flush_traces()
