# peargent/observability/__init__.py

"""
Observability module for tracing agent executions.

This module provides comprehensive tracing capabilities for agent operations,
including timing, cost tracking, and detailed execution logs.

Usage:
    from peargent.observability import configure_tracing, get_tracer

    # Configure tracing
    configure_tracing(enabled=True)

    # Use in agent code
    tracer = get_tracer()
    with tracer.trace_agent_run("MyAgent", "user input") as trace:
        # Agent execution
        pass
"""

# Core classes
from .span import Span, SpanType, SpanStatus
from .trace import Trace, TraceStatus
from .tracer import Tracer, TracerContext, get_tracer, configure_tracing, enable_tracing

# Storage
from .store import (
    TracingStore,
    InMemoryTracingStore,
    FileTracingStore,
)

# Cost tracking
from .cost_tracker import (
    CostTracker,
    get_cost_tracker,
    count_tokens,
    calculate_cost,
    PRICING,
)

# Formatters
from .formatters import (
    TerminalFormatter,
    JSONFormatter,
    MarkdownFormatter,
    format_trace,
)

# Context management (for advanced users)
try:
    from .context import (
        set_session_id,
        set_user_id,
        get_session_id,
        get_user_id,
        clear_context,
    )
except Exception:
    set_session_id = None
    set_user_id = None
    get_session_id = None
    get_user_id = None
    clear_context = None  # Context module not yet created


__all__ = [
    # Core
    "Span",
    "SpanType",
    "SpanStatus",
    "Trace",
    "TraceStatus",
    "Tracer",
    "TracerContext",
    "get_tracer",
    "configure_tracing",
    "enable_tracing",

    # Storage
    "TracingStore",
    "InMemoryTracingStore",
    "FileTracingStore",

    # Cost tracking
    "CostTracker",
    "get_cost_tracker",
    "count_tokens",
    "calculate_cost",
    "PRICING",

    # Formatters
    "TerminalFormatter",
    "JSONFormatter",
    "MarkdownFormatter",
    "format_trace",
]