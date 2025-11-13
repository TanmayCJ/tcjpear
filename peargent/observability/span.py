#peargent/observability/span.py

    # - Tracer (main class)
    # - Trace (one execution)
    # - Span (one step)

import time
import uuid
from typing import Optional, Dict, Any
from enum import Enum

class SpanType(Enum):
    AGENT_RUN = "agent_run"
    LLM_CALL = "llm_call"
    TOOL_EXECUTION = "tool_execution"
    CONTEXT_MANAGEMENT = "context_management"
    HISTRORY_SYNC = "history_sync"
    
class SpanStatus(Enum):
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    
class Span:
    def __init__(self, trace_id: str, span_type: SpanType, name: str, parent_id: Optional[str] = None):
        self.span_id = uuid.uuid4().hex[:16]
        self.parent_id = parent_id
        self.trace_id = trace_id
        self.span_type = span_type
        self.name = name
        self.status = SpanStatus.RUNNING
        
        #Timing
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.duration: Optional[float] = None
        
        # Agent-specific data
        self.agent_name: Optional[str] = None
        self.prompt: Optional[str] = None
        self.response: Optional[str] = None
        self.model: Optional[str] = None
        
        #Tool-specific data
        self.tool_name: Optional[str] = None
        self.tool_args: Optional[Dict] = None
        self.tool_output: Optional[Any] = None
        
        # Cost Tracking
        self.token_prompt: Optional[int] = None
        self.token_completion: Optional[int] = None
        self.cost: Optional[float] = None
        
        # Error Tracking
        self.error: Optional[Exception] = None
        self.error_message: Optional[str] = None
        self.error_type: Optional[str] = None
        
        # Metadata
        self.metadata: Dict[str, Any] = {}
        
    def start(self):
        """
        Start timing this span.
        Returns:
            Self for method chaining.
        """
        self.start_time = time.time()
        return self
    
    def end(self, status: SpanStatus = SpanStatus.SUCCESS) -> 'Span':
        """
        End timing this span and calculate the duration.

        Args:
            status: Final status of the span.

        Returns:
            Self for method chaining.
        """
        self.end_time = time.time()
        if self.start_time is not None:
            self.duration = self.end_time - self.start_time
        self.status = status
        return self
    
    def set_error(self, error: Exception) -> 'Span':
        """
        Record an error in this span.

        Args:
            error (Exception): The exception that occured

        Returns:
            Self for method chaining
        """
        self.error = error
        self.error_message = str(error)
        self.error_type = type(error).__name__
        self.status = SpanStatus.ERROR
        
        if self.end_time is None:
            self.end_time = time.time()
            if self.start_time is not None:
                self.duration = self.end_time - self.start_time
        
        return self
    
    def set_llm_data(
        self,
        prompt: Optional[str] = None,
        response: Optional[str] = None,
        model: Optional[str] = None,
    ) -> 'Span':
        """
        Set LLM-specific data for this span.

        Args:
            prompt : The prompt sent to the LLM.
            response : The response from the LLM.
            model : the Model identifier.

        Returns:
            Self for the method chaining.
        """
        if prompt is not None:
            self.prompt = prompt
        if response is not None:
            self.response = response
        if model is not None:
            self.model = model
        return self
    
    def set_tool_data(
        self,
        tool_name: Optional[str] = None,
        args: Optional[Dict] = None,
        output: Optional[Any] = None,
    ):
        """
        Set tool-specific data for this span.

        Args:
            tool_name : Name of the tool executed.
            args : Arguments passed to the tool.
            output : Output returned by the tool.
            
        Returns:
            Self for method chaining.
        """
        if tool_name is not None:
            self.tool_name = tool_name
        if args is not None:
            self.tool_args = args
        if output is not None:
            self.tool_output = output
        return self
    
    def set_tokens(
        self,
        prompt_tokens: Optional[int] = None,
        completion_tokens: Optional[int] = None,
        cost: Optional[float] = None,
    ):
        """
        Set token usage and cost data.

        Args:
            prompt_tokens: Number of tokens in the prompt.
            completion_tokens: Number of tokens in the completion.
            cost: Cost in USD for this operation.
        
        Returns:
            Self for method chaining.
        """
        if prompt_tokens is not None:
            self.token_prompt = prompt_tokens
        if completion_tokens is not None:
            self.token_completion = completion_tokens
        if cost is not None:
            self.cost = cost
        return self
    
    def add_metadata(self, key: str, value: Any) -> 'Span':
        """
        Add custom metadata to this span.

        Args:
            key (str): Metadata key
            value (Any): Metadata value

        Returns:
            Self for method chaining.
        """
        self.metadata[key] = value
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert span to dictionary for serialization.

        Returns:
            Dictionary representation of the span.
        """
        return {
            "span_id": self.span_id,
            "parent_id": self.parent_id,
            "trace_id": self.trace_id,
            "span_type": self.span_type.value,
            "name": self.name,
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.duration,
            "agent_name": self.agent_name,
            "prompt": self.prompt,
            "response": self.response,
            "model": self.model,
            "tool_name": self.tool_name,
            "tool_args": self.tool_args,
            "tool_output": self.tool_output,
            "token_prompt": self.token_prompt,
            "token_completion": self.token_completion,
            "cost": self.cost,
            "error_message": self.error_message,
            "error_type": self.error_type,
            "metadata": self.metadata,
        }
        
    def __repr__(self) -> str:
        """
        String representation of the span.

        Returns:
            str: String representation of the span.
        """
        duration_str = f"{self.duration:.3f}s" if self.duration else "running"
        return f"<Span span_id={self.span_id} type={self.span_type.value} duration={duration_str}>"