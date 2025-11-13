# peargent/observability/tracer.py

"""Tracer class for managing traces and spans.
"""

import threading
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

from .trace import Trace, TraceStatus
from .span import Span, SpanType, SpanStatus
from .store import TracingStore, InMemoryTracingStore

class TracerContext:
    """Thread-local context for tracking the current trace and span.
    
    This allows nested spans and multiple concurrent traces in different threads.
    """
    
    def __init__(self):
        self._local = threading.local()
        
    @property
    def current_trace(self) -> Optional[Trace]:
        """Get the current trace for this thread."""
        return getattr(self._local, 'trace', None)
    
    @current_trace.setter
    def current_trace(self, trace: Optional[Trace]):
        """Set the current trace for this thread."""
        self._local.trace = trace
        
    @property
    def current_span(self) -> Optional[Span]:
        """Get the current span for this thread."""
        return getattr(self._local, 'span', None)
    
    @current_span.setter
    def current_span(self, span: Optional[Span]):
        """Set the current span for this thread."""
        self._local.span = span
        
    def clear(self):
        """Clear the current trace and span for this thread."""
        self._local.trace = None
        self._local.span = None
        
class Tracer:
    """
    Core tracing engine for creating and managing traces.
    
    The tracer provides context manager for instrumenting agent operations
    and automatically tracks timing, costs and errors.
    """
    
    def __init__(
        self,
        store: Optional[TracingStore] = None,
        enabled: bool = True,
        auto_save: bool = True,
    ):
        """Initialize the tracer

        Args:
            store (Optional[TracingStore], optional): Storage backend for traces.
            enabled (bool, optional): Wether tracing is enabled.
            auto_save (bool, optional): Wether to automatically save traces when they end.
        """
        self.store = store if store is not None else InMemoryTracingStore()
        self.enabled = enabled
        self.auto_save = auto_save
        self.context = TracerContext()
        
        # Track al traces (for queries)
        self._traces: Dict[str, Trace] = {}
        self._lock = threading.Lock()
        
    def start_trace(
        self,
        agent_name: str,
        input_data: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Optional[str]:
        """Start a new trace.

        Args:
            agent_name (str): Name of the agent
            input_data (str): User input
            session_id (Optional[str], optional): Optional session ID. Defaults to None.
            user_id (Optional[str], optional): Optional user ID. Defaults to None.
            trace_id (Optional[str], optional): Optional custom trace ID. Defaults to None.

        Returns:
            The trace ID, or None if tracing is disabled.
        """
        if not self.enabled:
            return None
        
        trace = Trace(
            agent_name=agent_name,
            input_data=input_data,
            session_id=session_id,
            user_id=user_id,
            trace_id=trace_id,
        )
        trace.start()
        
        #Store Trace
        with self._lock:
            self._traces[trace.trace_id] = trace
            
        self.context.current_trace = trace
        
        return trace.trace_id
    
    def end_trace(
        self,
        trace_id: Optional[str] = None,
        output: Optional[str] = None,
        status: TraceStatus = TraceStatus.SUCCESS,
        error: Optional[Exception] = None,
    ) -> Optional[Trace]:
        """End a trace

        Args:
            trace_id (Optional[str], optional): ID of trace to end (uses current trace if None). Defaults to None.
            output (Optional[str], optional): Final output from agent. Defaults to None.
            status (TraceStatus, optional): Final status. Defaults to TraceStatus.SUCCESS.
            error (Optional[Exception], optional): Final error if any. Defaults to None.

        Returns:
            The ended trace or None if not found.
        """
        if not self.enabled:
            return None
        
        # Get trace
        if trace_id is None:
            trace = self.context.current_trace
        else:
            trace = self._traces.get(trace_id)
            
        if trace is None:
            return None
        
        if error is not None:
            trace.set_error(error)
            status = TraceStatus.ERROR
            
        trace.end(output=output, status=status)
        
        if self.auto_save and self.store is not None:
            self.store.save_trace(trace)
            
        if self.context.current_trace == trace:
            self.context.clear()
        
        return trace
    
    def start_span(
        self,
        span_type: SpanType,
        name: str,
        parent_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ) -> Optional[Span]:
        """Start a new span.

        Args:
            span_type (SpanType): Type of span
            name (str): Name of the span
            parent_id (Optional[str], optional): Parent span ID. Defaults to None.
            trace_id (Optional[str], optional): Trace ID. Defaults to None.

        Returns:
            The created span, or None if tracing is disabled.
        """
        if not self.enabled:
            return None
        
        # Get trace
        if trace_id is None:
            trace = self.context.current_trace
        else:
            trace = self._traces.get(trace_id)
        
        if trace is None:
            return None
        
        if parent_id is None and self.context.current_span is not None:
            parent_id = self.context.current_span.span_id
            
        span = trace.create_span(
            span_type=span_type,
            name=name,
            parent_id=parent_id,
        )
        span.start()
        
        self.context.current_span = span
        
        return span
    
    def end_span(
        self,
        span_id: Optional[str] = None,
        status: SpanStatus = SpanStatus.SUCCESS,
        error: Optional[Exception] = None,
    ) -> Optional[Span]:
        """End a span.

        Args:
            span_id (Optional[str], optional): ID of the span to end. Defaults to None.
            status (SpanStatus, optional): Final status of the span. Defaults to SpanStatus.SUCCESS.
            error (Optional[Exception], optional): Final error if any. Defaults to None.

        Returns:
            The ended span or None if not found.
        """
        if not self.enabled:
            return None
        
        if span_id is None:
            span = self.context.current_span
        else:
            trace = self.context.current_trace
            if trace:
                span = trace.get_span(span_id)
            else:
                span = None
        
        if span is None:
            return None
        
        if error is not None:
            span.set_error(error)
            return span
        
        span.end(status=status)
        
        if self.context.current_span == span:
            if span.parent_id:
                trace = self.context.current_trace
                if trace:
                    parent_span = trace.get_span(span.parent_id)
                    self.context.current_span = parent_span
                else:
                    self.context.current_span = None
            else:
                self.context.current_span = None
                
        return span
    
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get a trace by ID"""
        
        trace = self._traces.get(trace_id)
        if trace:
            return trace
        return self.store.get_trace(trace_id)
    
    def get_current_trace(self) -> Optional[Trace]:
        """Get the current trace in this context."""
        return self.context.current_trace
    
    def get_current_span(self) -> Optional[Span]:
        """Get the current span in this context."""
        return self.context.current_span
    
    def list_traces(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[Trace]:
        """List traces from storage."""
        return self.store.list_traces(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            limit=limit,
        )

    def get_store(self) -> TracingStore:
        """Get the underlying storage backend.

        This is useful if you need direct access to the store,
        but most operations can be done through the tracer itself.
        """
        return self.store

    def print_traces(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 10,
        format: str = "terminal",
    ) -> None:
        """Print traces in a formatted way.

        Args:
            session_id: Filter by session ID
            user_id: Filter by user ID
            agent_name: Filter by agent name
            limit: Maximum number of traces to print
            format: Output format ("terminal", "json", "markdown")
        """
        from .formatters import format_trace
        import sys

        traces = self.list_traces(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            limit=limit,
        )

        if not traces:
            print("No traces found.")
            return

        for trace in traces:
            output = format_trace(trace, format=format)
            try:
                print(output)
            except UnicodeEncodeError:
                # Fallback to safe ASCII encoding if terminal doesn't support Unicode
                safe_output = output.encode('ascii', errors='replace').decode('ascii')
                print(safe_output)
            print("\n" + "="*80 + "\n")

    def get_aggregate_stats(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """Get aggregate statistics across multiple traces.

        This is useful for analyzing pool executions, sessions, or user activity.

        Args:
            session_id: Filter by session ID
            user_id: Filter by user ID
            agent_name: Filter by agent name
            limit: Maximum number of traces to include

        Returns:
            Dictionary with aggregate statistics including:
            - total_cost: Sum of all costs
            - total_tokens: Sum of all tokens
            - total_llm_calls: Sum of all LLM calls
            - total_tool_calls: Sum of all tool calls
            - total_traces: Number of traces
            - total_duration: Sum of all durations
            - avg_cost_per_trace: Average cost per trace
            - avg_tokens_per_trace: Average tokens per trace
            - agents_used: List of unique agent names
        """
        traces = self.list_traces(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            limit=limit,
        )

        if not traces:
            return {
                "total_cost": 0.0,
                "total_tokens": 0,
                "total_llm_calls": 0,
                "total_tool_calls": 0,
                "total_traces": 0,
                "total_duration": 0.0,
                "avg_cost_per_trace": 0.0,
                "avg_tokens_per_trace": 0.0,
                "agents_used": [],
            }

        total_cost = sum(trace.total_cost for trace in traces)
        total_tokens = sum(trace.total_tokens for trace in traces)
        total_llm_calls = sum(trace.llm_calls_count for trace in traces)
        total_tool_calls = sum(trace.tool_calls_count for trace in traces)
        total_duration = sum(trace.duration or 0.0 for trace in traces)
        num_traces = len(traces)
        agents_used = list(set(trace.agent_name for trace in traces))

        return {
            "total_cost": total_cost,
            "total_tokens": total_tokens,
            "total_llm_calls": total_llm_calls,
            "total_tool_calls": total_tool_calls,
            "total_traces": num_traces,
            "total_duration": total_duration,
            "avg_cost_per_trace": total_cost / num_traces if num_traces > 0 else 0.0,
            "avg_tokens_per_trace": total_tokens / num_traces if num_traces > 0 else 0.0,
            "agents_used": sorted(agents_used),
        }

    def print_summary(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100,
    ) -> None:
        """Print an aggregate summary of traces.

        This is especially useful for pool executions to see total costs
        and metrics across all agents.

        Args:
            session_id: Filter by session ID
            user_id: Filter by user ID
            agent_name: Filter by agent name
            limit: Maximum number of traces to include
        """
        stats = self.get_aggregate_stats(
            session_id=session_id,
            user_id=user_id,
            agent_name=agent_name,
            limit=limit,
        )

        # ANSI color codes
        CYAN = "\033[36m"
        GREEN = "\033[32m"
        BLUE = "\033[34m"
        YELLOW = "\033[33m"
        BOLD = "\033[1m"
        RESET = "\033[0m"

        try:
            print(f"{CYAN}{'━' * 80}{RESET}")
            print(f"{BOLD}AGGREGATE SUMMARY{RESET}")
            print(f"{CYAN}{'━' * 80}{RESET}")
            print()
            print(f"  {BOLD}Traces:{RESET} {BLUE}{stats['total_traces']}{RESET}")
            print(f"  {BOLD}Agents:{RESET} {', '.join(stats['agents_used'])}")
            print()
            print(f"  {BOLD}Total Cost:{RESET} {GREEN}${stats['total_cost']:.6f}{RESET}")
            print(f"  {BOLD}Total Tokens:{RESET} {CYAN}{stats['total_tokens']:,}{RESET}")
            print(f"  {BOLD}Total Duration:{RESET} {CYAN}{stats['total_duration']:.3f}s{RESET}")
            print()
            print(f"  {BOLD}LLM Calls:{RESET} {BLUE}{stats['total_llm_calls']}{RESET}")
            print(f"  {BOLD}Tool Calls:{RESET} {YELLOW}{stats['total_tool_calls']}{RESET}")
            print()
            print(f"  {BOLD}Avg Cost/Trace:{RESET} {GREEN}${stats['avg_cost_per_trace']:.6f}{RESET}")
            print(f"  {BOLD}Avg Tokens/Trace:{RESET} {CYAN}{stats['avg_tokens_per_trace']:.1f}{RESET}")
            print()
            print(f"{CYAN}{'━' * 80}{RESET}")
        except UnicodeEncodeError:
            # Fallback for terminals that don't support Unicode
            print("=" * 80)
            print("AGGREGATE SUMMARY")
            print("=" * 80)
            print()
            print(f"  Traces: {stats['total_traces']}")
            print(f"  Agents: {', '.join(stats['agents_used'])}")
            print()
            print(f"  Total Cost: ${stats['total_cost']:.6f}")
            print(f"  Total Tokens: {stats['total_tokens']:,}")
            print(f"  Total Duration: {stats['total_duration']:.3f}s")
            print()
            print(f"  LLM Calls: {stats['total_llm_calls']}")
            print(f"  Tool Calls: {stats['total_tool_calls']}")
            print()
            print(f"  Avg Cost/Trace: ${stats['avg_cost_per_trace']:.6f}")
            print(f"  Avg Tokens/Trace: {stats['avg_tokens_per_trace']:.1f}")
            print()
            print("=" * 80)
        
    # context manager 
    @contextmanager
    def trace_agent_run(
        self,
        agent_name: str,
        input_data: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ):
        """Context manager for tracing an entire agent eun.

        Usage:
              with tracer.trace_agent_run("MyAgent", "user input") as trace:
                  # Agent execution
                  result = agent.run(input)
                  trace.output = result
        """
        
        if not self.enabled:
            yield None
            return
        
        trace_id = self.start_trace(
            agent_name=agent_name,
            input_data=input_data,
            session_id=session_id,
            user_id=user_id,
        )
        
        try:
            trace = self.get_trace(trace_id)
            yield trace
            self.end_trace(trace_id=trace_id, status=TraceStatus.SUCCESS)
        except Exception as e:
            self.end_trace(trace_id=trace_id, status=TraceStatus.ERROR, error=e)
            raise
        
    @contextmanager
    def trace_llm_call(
        self,
        name: str = "LLM Call",
        model: Optional[str] = None,
    ):
        """Context manager for tracing an LLM API call.

        Usage:
              with tracer.trace_llm_call("Planning", model="gpt-4") as span:
                  response = llm.generate(prompt)
                  span.set_llm_data(prompt=prompt, response=response, model=model)
                  span.set_tokens(prompt_tokens=100, completion_tokens=50, cost=0.01)
        """
        if not self.enabled:
            yield None
            return
        
        span = self.start_span(
            SpanType.LLM_CALL,
            name=name,
        )
        if span and model:
            span.model = model
        
        try:
            yield span
            self.end_span(status=SpanStatus.SUCCESS)
        except Exception as e:
            self.end_span(error=e)
            raise
    
    @contextmanager
    def trace_tool_execution(
        self,
        tool_name: str,
        args: Optional[Dict] = None,
    ):
        """Context manager for tracing a tool execution.

        Usage:
              with tracer.trace_tool_execution("web_search", {"query": "AI"}) as span:
                  result = tool.run(args)
                  span.set_tool_data(tool_name=tool_name, args=args, output=result)
        """
        if not self.enabled:
            yield None
            return
        
        span = self.start_span(
            SpanType.TOOL_EXECUTION,
            name=f"Tool: {tool_name}",
        )
        if span:
            span.tool_name = tool_name
            span.tool_args = args
        
        try:
            yield span
            self.end_span(status=SpanStatus.SUCCESS)
        except Exception as e:
            self.end_span(error=e)
            raise

# Global tracer instance
_global_tracer: Optional[Tracer] = None

def get_tracer() -> Tracer:
    """Get the global tracer instance."""
    global _global_tracer
    if _global_tracer is None:
        _global_tracer = Tracer( enabled=True )
    return _global_tracer

def configure_tracing(
    store: Optional[TracingStore] = None,
    enabled: bool = True,
    auto_save: bool = True,
) -> Tracer:
    """Configure the global tracer instance.

    Args:
        store: Storage backend for traces. If None, uses InMemoryTracingStore.
        enabled: Whether tracing is enabled.
        auto_save: Whether to automatically save traces when they end.

    Returns:
        The configured global tracer instance.

    Example:
        # Basic usage with in-memory store
        tracer = configure_tracing(enabled=True)
        traces = tracer.list_traces()

        # With file store
        from peargent.observability import FileTracingStore
        store = FileTracingStore("./traces")
        tracer = configure_tracing(store=store)
    """
    global _global_tracer
    _global_tracer = Tracer(
        store=store,
        enabled=enabled,
        auto_save=auto_save,
    )
    if store is not None:
        assert _global_tracer.store is store, "Tracer should use the provided store"
    return _global_tracer


def enable_tracing(
    store_type: str = "memory",
    storage_dir: str = "./traces",
    enabled: bool = True,
    auto_save: bool = True,
) -> Tracer:
    """Simplified tracing setup - configures and returns a tracer in one call.

    This is a convenience function that handles store creation and tracer
    configuration in a single call.

    Args:
        store_type: Type of storage backend ("memory" or "file").
        storage_dir: Directory for file storage (only used if store_type="file").
        enabled: Whether tracing is enabled.
        auto_save: Whether to automatically save traces when they end.

    Returns:
        Configured tracer instance.

    Example:
        # In-memory tracing (default)
        tracer = enable_tracing()

        # File-based tracing
        tracer = enable_tracing(store_type="file", storage_dir="./my_traces")

        # Use the tracer
        traces = tracer.list_traces()
        tracer.print_traces(limit=5)
    """
    if store_type == "memory":
        store = InMemoryTracingStore()
    elif store_type == "file":
        from .store import FileTracingStore
        store = FileTracingStore(storage_dir)
    else:
        raise ValueError(f"Unknown store_type: {store_type}. Use 'memory' or 'file'.")

    return configure_tracing(
        store=store,
        enabled=enabled,
        auto_save=auto_save,
    )