# peargent/observability/formatters.py

"""Formatters for displaying traces in various format.
"""
    
import json
from typing import Optional
from datetime import datetime

from .trace import Trace, TraceStatus
from .span import Span, SpanType, SpanStatus

class TerminalFormatter:
    """Formats traces for terminal output with colors and nice formatting.
    """
      # ANSI color codes
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    # Colors
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    GRAY = "\033[90m"

    def __init__(self, use_colors: bool = True):
        """Initialize formatter

        Args:
            use_colors (bool, optional): Whether to use ANSI colors. Defaults to True.
        """
        
        self.use_colors = use_colors
        
    def format(self, trace: Trace) -> str:
        """Format a trace for terminal output.

        Args:
            trace (Trace): The trace to format.
            
        Returns:
            str: The formatted trace string.
        """
        lines = []
        
        lines.append(self._color("━" * 80, self.CYAN))
        lines.append(self._format_header(trace))
        lines.append(self._color("━" * 80, self.CYAN))
        
        lines.append(self._format_io(trace))
        lines.append("")
        
        if trace.spans:
            lines.append(self._bold("Execution Steps:"))
            lines.append("")
            
            for span in trace.spans:
                if span.parent_id is None:
                    span_lines = self._format_span(span, trace, indent=0)
                    lines.extend(span_lines.split('\n'))
                    
        lines.append("")
        lines.append(self._color("━" * 80, self.CYAN))
        lines.append(self._format_metrics(trace))
        lines.append(self._color("━" * 80, self.CYAN))
        
        return "\n".join(lines)

    def _format_header(self, trace: Trace) -> str:
        """Format the header of the trace."""
        # Handle both string and enum status
        status_value = trace.status.value if hasattr(trace.status, 'value') else str(trace.status)
        status_text = self._color_status(status_value, trace.status)
        
        lines=[]
        lines.append(f"{self._bold('Trace:')} {trace.trace_id[:16]}...")
        lines.append(f"Agent: {self._color(trace.agent_name, self.BLUE)}")
        lines.append(f"Status: {status_text}")
        
        if trace.duration:
            lines.append(f"Duration: {self._color(f'{trace.duration:.3f}s', self.CYAN)}")
        
        if trace.session_id:
            lines.append(f"Session: {self._dim(trace.session_id)}")
        
        if trace.user_id:
            lines.append(f"User: {self._dim(trace.user_id)}")
            
        return "\n".join(lines)

    def _format_io(self, trace: Trace) -> str:
        """Format input/output."""
        lines = []

        if trace.input:
            lines.append(f"{self._bold('Input:')} {self._truncate(trace.input, 100)}")

        if trace.output:
            lines.append(f"{self._bold('Output:')} {self._truncate(trace.output, 100)}")

        if trace.error_message:
            error_text = f"{trace.error_type}: {trace.error_message}"
            lines.append(f"{self._color('Error:', self.RED)} {error_text}")

        return "\n".join(lines)
    
    def _format_span(self, span: Span, trace: Trace, indent: int = 0) -> str:
        """Format a span with its children."""
        lines = []
        prefix = "  " * indent

        # Span name and timing
        duration = f"{span.duration:.3f}s" if span.duration else "running"
        duration_color = self._color(duration, self.CYAN)

        # Cost if available
        cost_str = ""
        if span.cost:
            cost_str = f", {self._color(f'${span.cost:.6f}', self.GREEN)}"

        # Main line
        lines.append(f"{prefix}{self._bold(span.name)} ({duration_color}{cost_str})")

        # Details
        details = self._format_span_details(span, indent)
        if details:
            lines.append(details)

        # Children
        children = trace.get_child_spans(span.span_id)
        for child in children:
            child_output = self._format_span(child, trace, indent + 1)
            lines.extend(child_output.split('\n'))

        return "\n".join(lines)
        
    def _format_span_details(self, span: Span, indent: int) -> str:
        """Format span-specific details."""
        lines = []
        prefix = "  " * (indent + 1)

        if span.span_type == SpanType.LLM_CALL:
            if span.model:
                lines.append(f"{prefix}{self._dim('Model:')} {span.model}")
            if span.token_prompt or span.token_completion:
                tokens_str = f"{span.token_prompt or 0} → {span.token_completion or 0}"
                lines.append(f"{prefix}{self._dim('Tokens:')} {tokens_str}")
            if span.prompt:
                prompt_preview = self._truncate(span.prompt, 60)
                # Handle multi-line prompts with proper indentation
                prompt_lines = prompt_preview.split('\n')
                if len(prompt_lines) == 1:
                    lines.append(f"{prefix}{self._dim('Prompt:')} {prompt_preview}")
                else:
                    lines.append(f"{prefix}{self._dim('Prompt:')} {prompt_lines[0]}")
                    # Indent continuation lines to align with the prompt content
                    continuation_prefix = prefix + " " * len("Prompt: ")
                    for line in prompt_lines[1:]:
                        lines.append(f"{continuation_prefix}{line}")

        elif span.span_type == SpanType.TOOL_EXECUTION:
            if span.tool_args:
                args_str = json.dumps(span.tool_args, indent=None)
                args_preview = self._truncate(args_str, 60)
                lines.append(f"{prefix}{self._dim('Args:')} {args_preview}")
            if span.tool_output:
                output_preview = self._truncate(str(span.tool_output), 60)
                lines.append(f"{prefix}{self._dim('Output:')} {output_preview}")

        if span.error_message:
            lines.append(f"{prefix}{self._color('Error:', self.RED)} {span.error_message}")

        return "\n".join(lines)

    def _format_metrics(self, trace: Trace) -> str:
        """Format aggregate metrics."""
        metrics = []

        metrics.append(f"Cost: {self._color(f'${trace.total_cost:.6f}', self.GREEN)}")
        metrics.append(f"Tokens: {self._color(f'{trace.total_tokens:,}', self.CYAN)}")
        metrics.append(f" LLM Calls: {self._color(str(trace.llm_calls_count), self.BLUE)}")
        metrics.append(f"Tool Calls: {self._color(str(trace.tool_calls_count), self.YELLOW)}")
        metrics.append(f"Total Spans: {self._color(str(len(trace.spans)), self.CYAN)}")

        return "  |  ".join(metrics)

    def _get_span_icon(self, span_type: SpanType) -> str:
        """Get emoji for span type."""
        if not self.use_emojis:
            return ""

        icons = {
            SpanType.LLM_CALL: self.LLM,
            SpanType.TOOL_EXECUTION: self.TOOL,
            SpanType.AGENT_RUN: self.AGENT,
        }
        return icons.get(span_type, "�")

    def _get_status_icon(self, status) -> str:
        """Get emoji for status."""
        if not self.use_emojis:
            return ""

        if hasattr(status, 'value'):
            status_val = status.value
        else:
            status_val = str(status)

        if status_val == "success":
            return self.SUCCESS
        elif status_val == "error":
            return self.ERROR
        elif status_val == "running":
            return self.RUNNING
        return ""

    def _color_status(self, text: str, status) -> str:
        """Color text based on status."""
        if hasattr(status, 'value'):
            status_val = status.value
        else:
            status_val = str(status)

        if status_val == "success":
            return self._color(text, self.GREEN)
        elif status_val == "error":
            return self._color(text, self.RED)
        elif status_val == "running":
            return self._color(text, self.YELLOW)
        return text

    def _color(self, text: str, color: str) -> str:
        """Apply color to text."""
        if not self.use_colors:
            return text
        return f"{color}{text}{self.RESET}"

    def _bold(self, text: str) -> str:
        """Make text bold."""
        if not self.use_colors:
            return text
        return f"{self.BOLD}{text}{self.RESET}"

    def _dim(self, text: str) -> str:
        """Make text dim."""
        if not self.use_colors:
            return text
        return f"{self.DIM}{text}{self.RESET}"

    def _emoji(self, emoji: str) -> str:
        """Return emoji if enabled."""
        return emoji if self.use_emojis else ""

    def _truncate(self, text: str, max_length: int) -> str:
        """Truncate text to max length."""
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."


class JSONFormatter:
    """
    Formats traces as JSON.
    """

    def __init__(self, indent: int = 2):
        """
        Initialize formatter.

        Args:
            indent: JSON indentation level
        """
        self.indent = indent

    def format(self, trace: Trace) -> str:
        """
        Format trace as JSON.

        Args:
            trace: The trace to format

        Returns:
            JSON string
        """
        return trace.to_json(indent=self.indent)


class MarkdownFormatter:
    """
    Formats traces as Markdown for documentation.
    """

    def format(self, trace: Trace) -> str:
        """
        Format trace as Markdown.

        Args:
            trace: The trace to format

        Returns:
            Markdown string
        """
        lines = []

        # Header
        lines.append(f"# Trace: {trace.trace_id}")
        lines.append("")

        # Metadata
        lines.append("## Metadata")
        lines.append("")
        lines.append(f"- **Agent:** {trace.agent_name}")
        lines.append(f"- **Status:** {trace.status.value}")
        if trace.duration:
            lines.append(f"- **Duration:** {trace.duration:.3f}s")
        lines.append(f"- **Cost:** ${trace.total_cost:.6f}")
        lines.append(f"- **Tokens:** {trace.total_tokens:,}")
        if trace.session_id:
            lines.append(f"- **Session:** {trace.session_id}")
        if trace.user_id:
            lines.append(f"- **User:** {trace.user_id}")
        lines.append("")

        # Input/Output
        lines.append("## Input/Output")
        lines.append("")
        if trace.input:
            lines.append(f"**Input:**")
            lines.append(f"```")
            lines.append(trace.input)
            lines.append(f"```")
            lines.append("")

        if trace.output:
            lines.append(f"**Output:**")
            lines.append(f"```")
            lines.append(trace.output)
            lines.append(f"```")
            lines.append("")

        if trace.error_message:
            lines.append(f"**Error:** {trace.error_type}: {trace.error_message}")
            lines.append("")

        # Spans
        if trace.spans:
            lines.append("## Execution Steps")
            lines.append("")
            for span in trace.spans:
                if span.parent_id is None:
                    lines.append(self._format_span(span, trace, level=3))

        # Metrics
        lines.append("## Metrics")
        lines.append("")
        lines.append(f"- **LLM Calls:** {trace.llm_calls_count}")
        lines.append(f"- **Tool Calls:** {trace.tool_calls_count}")
        lines.append(f"- **Total Spans:** {len(trace.spans)}")
        lines.append(f"- **Total Cost:** ${trace.total_cost:.6f}")
        lines.append(f"- **Total Tokens:** {trace.total_tokens:,}")

        return "\n".join(lines)

    def _format_span(self, span: Span, trace: Trace, level: int = 3) -> str:
        """Format span as markdown."""
        lines = []
        header = "#" * level

        # Span header
        duration = f" ({span.duration:.3f}s)" if span.duration else ""
        cost = f" - ${span.cost:.6f}" if span.cost else ""
        lines.append(f"{header} {span.name}{duration}{cost}")
        lines.append("")

        # Details
        if span.span_type == SpanType.LLM_CALL:
            if span.model:
                lines.append(f"- **Model:** {span.model}")
            if span.token_prompt or span.token_completion:
                lines.append(f"- **Tokens:** {span.token_prompt or 0} prompt, {span.token_completion or 0} completion")
            if span.prompt:
                lines.append(f"- **Prompt:** `{span.prompt[:100]}...`")

        elif span.span_type == SpanType.TOOL_EXECUTION:
            if span.tool_args:
                lines.append(f"- **Arguments:** `{json.dumps(span.tool_args)}`")
            if span.tool_output:
                lines.append(f"- **Output:** `{str(span.tool_output)[:100]}...`")

        if span.error_message:
            lines.append(f"- **Error:** {span.error_type}: {span.error_message}")

        lines.append("")

        # Children
        children = trace.get_child_spans(span.span_id)
        for child in children:
            lines.append(self._format_span(child, trace, level + 1))

        return "\n".join(lines)


def format_trace(trace: Trace, format: str = "terminal", **kwargs) -> str:
    """
    Convenience function to format a trace.

    Args:
        trace: The trace to format
        format: Format type ("terminal", "json", "markdown")
        **kwargs: Additional arguments for the formatter

    Returns:
        Formatted string
    """
    if format == "terminal":
        formatter = TerminalFormatter(**kwargs)
    elif format == "json":
        formatter = JSONFormatter(**kwargs)
    elif format == "markdown":
        formatter = MarkdownFormatter(**kwargs)
    else:
        raise ValueError(f"Unknown format: {format}")

    return formatter.format(trace)
      
      