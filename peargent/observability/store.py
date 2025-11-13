#peargent/observability/store.py

"""Storage backends for persisting traces and spans.
"""

import os
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path

from .trace import Trace, TraceStatus
from .span import Span, SpanType, SpanStatus

class TracingStore(ABC):
    """Abstract base class for tracing storage backends.

    Implementations should provide methods to save, retrieve, list
    and delete traces and spans.
    """
    
    @abstractmethod
    def save_trace(self, trace: Trace) -> None:
        """Persist a trace to the storage backend.

        Args:
            trace (Trace): The trace object to be saved.
        """
        pass
    
    @abstractmethod
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Retrieve a trace by its ID.

        Args:
            trace_id (str): The ID of the trace to retrieve.

        Returns:
            The trace with the given ID, or None if not found.
        """
        pass
    
    @abstractmethod
    def list_traces(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Trace]:
        """List traces with optional filtering.

            Args:
                session_id (Optional[str]): Filter by session ID.
                user_id (Optional[str]): Filter by user ID.
                agent_name (Optional[str]): Filter by agent name.
                limit (int): Maximum number of traces to return.

            Returns:
                List[Trace]: A list of traces matching the filters.
            """
        pass
    
    @abstractmethod
    def delete_trace(self, trace_id: str) -> bool:
        """Delete a trace by its ID.

        Args:
            trace_id (str): The ID of the trace to delete.
        
        Returns:
            bool: True if deletion was successful, False otherwise.
        """
        pass
    
    @abstractmethod
    def clear_all(self) -> int:
        """Clear all traces and spans from the storage backend.
        """
        pass
    
class InMemoryTracingStore(TracingStore):
    """In-memory implementation of the TracingStore.

    Stores traces and spans in memory using dictionaries.
    Suitable for testing and development purposes.
    """
    
    def __init__(self):
        """Initialize the in-memory store."""
        self._traces: Dict[str, Trace] = {}
    
    def save_trace(self, trace: Trace) -> None:
        """Save trace to memory"""
        self._traces[trace.trace_id] = trace
        
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Retrieve trace from memory"""
        return self._traces.get(trace_id)
    
    def list_traces(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[Trace]:
        """List traces with optional filtering"""
        traces = list(self._traces.values())
        
        if session_id is not None:
            traces = [t for t in traces if t.session_id == session_id]
        if user_id is not None:
            traces = [t for t in traces if t.user_id == user_id]
        if agent_name is not None:
            traces = [t for t in traces if t.agent_name == agent_name]
        
        traces.sort(key=lambda t: t.start_time or 0, reverse=True)
        
        return traces[:limit]
    
    def delete_trace(self, trace_id: str) -> bool:
        """Delete trace from memory"""
        if trace_id in self._traces:
            del self._traces[trace_id]
            return True
        return False
    
    def clear_all(self) -> int:
        """Clear all traces from memory"""
        count = len(self._traces)
        self._traces.clear()
        return count
    
    def __len__(self) -> int:
        """Return number of stored traces"""
        return len(self._traces)
    
class FileTracingStore(TracingStore):
    """File-based implementation of the TracingStore.

    Stores traces and spans as JSON files in a specified directory.
    Suitable for simple persistence without a database.
    """
    def __init__(self, storage_dir: str = "./traces"):
        """Initialize the file-based store.

        Args:
            storage_dir (str): Directory to store trace files.
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
    def _get_trace_path(self, trace_id: str) -> Path:
        """Get file path for a given trace ID."""
        return self.storage_dir / f"{trace_id}.json"
    
    def save_trace(self, trace: Trace) -> None:
        """Save trace to file"""
        trace_path = self._get_trace_path(trace.trace_id)
        with open(trace_path, "w", encoding="utf-8") as f:
            json.dump(trace.to_dict(), f, indent=2, ensure_ascii=False)
        
    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Load trace from JSON file"""
        trace_path = self._get_trace_path(trace_id)
        
        if not trace_path.exists():
            return None

        try:
            with open(trace_path, "r", encoding="utf-8") as f:
                trace_data = json.load(f)
            return self._dict_to_trace(trace_data)
        except Exception as e:
            print(f"Error loading trace {trace_id}: {e}")
            import traceback
            traceback.print_exc()
            return None
        
    def list_traces(
        self, 
        session_id: Optional[str] = None,
        user_id: Optional[str] = None, 
        agent_name: Optional[str] = None, 
        limit: int = 100
    ) -> List[Trace]:
        """List traces with optional filtering"""    
        traces = []
        
        for trace_file in self.storage_dir.glob("*.json"):
            try:
                with open(trace_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                if session_id is not None and data.get("session_id") != session_id:
                    continue
                if user_id is not None and data.get("user_id") != user_id:
                    continue
                if agent_name is not None and data.get("agent_name") != agent_name:
                    continue
                
                trace = self._dict_to_trace(data)
                traces.append(trace)
            except Exception as e:
                # print(f"Error loading trace from {trace_file}: {e}")
                continue
            
        traces.sort(key=lambda t: t.start_time or 0, reverse=True)
        
        return traces[:limit]
    
    def delete_trace(self, trace_id: str) -> bool:
        """Delete trace file"""
        trace_path = self._get_trace_path(trace_id)
        
        if trace_path.exists():
            trace_path.unlink()
            return True
        return False
    
    def clear_all(self) -> int:
        """Clear all trace files from storage directory"""
        count = 0
        for trace_file in self.storage_dir.glob("*.json"):
            trace_file.unlink()
            count += 1
        return count
    
    def _dict_to_trace(self, data: Dict[str, Any]) -> Trace:
        """Reconstruct Trace object from dictionary.

        Args:
            data (Dict[str, Any]): Dictionary representation of a trace.

        Returns:
            Trace: Reconstructed Trace object.
        """
        trace = Trace(
            agent_name=data["agent_name"],
            input_data=data["input"],
            session_id=data.get("session_id"),
            user_id=data.get("user_id"),
            trace_id=data["trace_id"]
        )
        
        # Set timing
        trace.start_time = data.get("start_time")
        trace.end_time = data.get("end_time")
        trace.duration = data.get("duration")
        
        # Set status
        status_str = data.get("status", "running")
        trace.status = TraceStatus(status_str)
        
        # Set output
        trace.output = data.get("output")
        
        #Set error info
        trace.error_message = data.get("error_message")
        trace.error_type = data.get("error_type")
        
        # Set metrics
        trace.total_tokens = data.get("total_tokens", 0)
        trace.total_cost = data.get("total_cost", 0.0)
        trace.llm_calls_count = data.get("llm_calls_count", 0)
        trace.tool_calls_count = data.get("tool_calls_count", 0)
        
        # Set metadata
        trace.metadata = data.get("metadata", {})
        
        # Reconstruct spans
        for span_data in data.get("spans", []):
            span = self._dict_to_span(span_data)
            trace.add_span(span)
            
        return trace
    
    def _dict_to_span(self, data: Dict[str, Any]) -> Span:
        """
        Reconstruct a Span object from dictionary.

        Args:
            data: Dictionary representation of span

        Returns:
            Reconstructed Span object
        """
        # Create span (this will auto-generate a new span_id)
        span = Span(
            trace_id=data["trace_id"],
            span_type=SpanType(data["span_type"]),
            name=data["name"],
            parent_id=data.get("parent_id")
        )

        # Now overwrite the auto-generated span_id with the stored one
        span.span_id = data["span_id"]

        # Set timing
        span.start_time = data.get("start_time")
        span.end_time = data.get("end_time")
        span.duration = data.get("duration")

        # Set status
        status_str = data.get("status", "running")
        span.status = SpanStatus(status_str)

        # Set agent data
        span.agent_name = data.get("agent_name")
        span.prompt = data.get("prompt")
        span.response = data.get("response")
        span.model = data.get("model")

        # Set tool data
        span.tool_name = data.get("tool_name")
        span.tool_args = data.get("tool_args")
        span.tool_output = data.get("tool_output")

        # Set cost data
        span.token_prompt = data.get("token_prompt")
        span.token_completion = data.get("token_completion")
        span.cost = data.get("cost")

        # Set error data
        span.error_message = data.get("error_message")
        span.error_type = data.get("error_type")

        # Set metadata
        span.metadata = data.get("metadata", {})

        return span