# peargent/observability/trace.py

"""Trace class for tracking the complete agent executions.
"""

import time
import uuid
import json
from typing import Optional, List, Dict, Any
from enum import Enum

from .span import Span, SpanType, SpanStatus

class TraceStatus(Enum):
    """Status of a trace."""    
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"
    
class Trace:
    """Represents a complete agent execution trace.
    
    A trace contains multiple spans and tracks the entire lifecycle 
    of an agent run, including all LLM calls, tool executions, timing,
    costs and errors
    """
    
    def __init__(
        self,
        agent_name: str,
        input_data: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        trace_id: Optional[str] = None,
    ):
        """Initialize a new trace.

        Args:
            agent_name: Name of the agent executing
            input_data: User input that triggered this execution
            session_id: Optional session identifier.
            user_id: Optional user identifier.
            trace_id: Optional custom trace ID.
        """
        self.trace_id = trace_id or uuid.uuid4().hex
        self.session_id = session_id
        self.user_id = user_id
        self.agent_name = agent_name
        
        #Timing
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        
        #Status
        self.status: TraceStatus = TraceStatus.RUNNING
        
        #INput/Output
        self.input = input_data
        self.output: Optional[str] = None
        
        #Spans
        self.spans: List[Span] = []
        self.root_span: Optional[Span] = None
        self._spans_by_id: Dict[str, Span] = {}
        
        #Aggregated metrics (calculated when trace ends)
        self.total_tokens: int = 0
        self.total_cost: float = 0.0
        self.llm_calls_count: int = 0
        self.tool_calls_count: int = 0
        
        #Error tracking
        self.error: Optional[Exception] = None
        self.error_message: Optional[str] = None
        self.error_type: Optional[str] = None
        
        #Metadata
        self.metadata: Dict[str, Any] = {}
        
    def start(self) -> 'Trace':
        """Start timing this trace

        Returns:
            Self for method chaining
        """
        self.start_time = time.time()
        return self
    
    def end(
        self,
        output: Optional[str] = None,
        status: TraceStatus = TraceStatus.SUCCESS
    ) -> 'Trace':
        """End timing this trace and finalize metrics.

        Args:
            output: Optional output produced by the agent.
            status: Final status of the trace.
            
        Returns:
            Self for method chaining
        """
        self.end_time = time.time()
        if self.start_time is not None:
            self.duration = self.end_time - self.start_time
            
        if output is not None:
            self.output = output
            
        if self.status != TraceStatus.ERROR:
            self.status = status
            
        self._calculate_metrics()
        
        return self
    
    def add_span(self, span: Span) -> 'Trace':
        """Add a span to this trace

        Args:
            span (Span): The span to add

        Returns:
            Self for method chaining
        """
        self.spans.append(span)
        self._spans_by_id[span.span_id] = span
        
        if span.parent_id is None and self.root_span is None:
            self.root_span = span
            
        return self
    
    def create_span(
        self,
        span_type: SpanType,
        name: str,
        parent_id: Optional[str] = None,
        ) -> Span:
        """Create and add a new span to this trace.

        Args:
            span_type (SpanType): Type of span to create
            name (str): Name of the span
            parent_id (Optional[str], optional): Optionlal parent span ID. Defaults to None.

        Returns:
            The newly create span
        """
        span = Span(
            trace_id=self.trace_id,
            span_type=span_type,
            name=name,
            parent_id=parent_id
        )
        span.agent_name = self.agent_name
        self.add_span(span)
        return span
    
    def get_span(self, span_id: str) -> Optional[Span]:
        """Retrieve a span by its ID.

        Args:
            span_id (str): The ID of the span to retrieve.

        Returns:
            The span with the given ID, or None if not found.
        """
        return self._spans_by_id.get(span_id)
    
    def get_spans_by_type(self, span_type: SpanType) -> List[Span]:
        """Get all spans of a specific type.

        Args:
            span_type (SpanType): The type of spans to retrieve.

        Returns:
            List[Span]: A list of spans matching the specified type.
        """
        return [span for span in self.spans if span.span_type == span_type]
    
    def get_child_spans(self, parent_id: str) -> List[Span]:
        """Get all child spans of a specific parent span.

        Args:
            parent_id (str): The ID of the parent span.

        Returns:
            List[Span]: A list of child spans for the specified parent span.
        """
        return [span for span in self.spans if span.parent_id == parent_id]
    
    def set_error(self, error: Exception) -> 'Trace':
        """Set an error for this trace.

        Args:
            error (Exception): The error to set.
            
        Returns:
            Self for method chaining
        """
        self.error = error
        self.error_message = str(error)
        self.error_type = type(error).__name__
        self.status = TraceStatus.ERROR
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'Trace':
        """Add metadata to this trace.

        Args:
            key (str): Metadata key.
            value (Any): Metadata value.
            
        Returns:
            Self for method chaining
        """
        self.metadata[key] = value
        return self
    
    def _calculate_metrics(self) -> None:
        """Calculate aggregated metrics from spans."""
        self.total_tokens = 0
        self.total_cost = 0.0
        self.llm_calls_count = 0
        self.tool_calls_count = 0
        
        for span in self.spans:
            if span.token_prompt is not None:
                self.total_tokens += span.token_prompt
            if span.token_completion is not None:
                self.total_tokens += span.token_completion
            if span.cost is not None:
                self.total_cost += span.cost
                
            if span.span_type == SpanType.LLM_CALL:
                self.llm_calls_count += 1
            elif span.span_type == SpanType.TOOL_EXECUTION:
                self.tool_calls_count += 1
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert the trace to a dictionary.

        Returns:
            Dict[str, Any]: Dictionary representation of the trace.
        """
        return {
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "agent_name": self.agent_name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "status": self.status.value,
            "input": self.input,
            "output": self.output,
            "spans": [span.to_dict() for span in self.spans],
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "llm_calls_count": self.llm_calls_count,
            "tool_calls_count": self.tool_calls_count,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "metadata": self.metadata,
        }
        
    def to_json(self, indent: int = 2) -> str:
        """Serialize the trace to a JSON string.

        Args:
            indent: JSON indentation level.

        Returns:
            str: JSON string representation of the trace.
        """
        return json.dumps(self.to_dict(), indent=indent)
    
    def summary(self) -> str:
        """Generate a summary of the trace.

        Returns:
            str: Summary string.
        """
        lines = []
        lines.append(f"Trace: {self.trace_id}")
        lines.append(f"Agent: {self.agent_name}")
        lines.append(f"Status: {self.status.value}")

        if self.duration:
            lines.append(f"Duration: {self.duration:.3f}s")
            
        lines.append(f"Cost: ${self.total_cost:.4f}")
        lines.append(f"Tokens: {self.total_tokens:,}")
        lines.append(f"LLM Calls: {self.llm_calls_count}")
        lines.append(f"Tool Calls: {self.tool_calls_count}")
        lines.append(f"Spans: {len(self.spans)}")

        if self.error_message:
            lines.append(f"Error: {self.error_type}: {self.error_message}")

        return "\n".join(lines)
    
    def __repr__(self) -> str:
        """Generate a string representation of the trace.

        Returns:
            str: String representation of the trace.
        """
        duration_str = f"{self.duration:.3f}s" if self.duration else "running"
        return (
              f"<Trace trace_id={self.trace_id} "
              f"agent={self.agent_name} "
              f"duration={duration_str} "
              f"spans={len(self.spans)}>"
        )