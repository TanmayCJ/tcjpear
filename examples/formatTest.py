"""Test formatters"""

from peargent.observability.formatters import (
    TerminalFormatter, JSONFormatter, MarkdownFormatter, format_trace
)
from peargent.observability.trace import Trace, TraceStatus
from peargent.observability.span import SpanType


def create_sample_trace():
    """Create a sample trace for testing."""
    trace = Trace(
        agent_name="TestAgent",
        input_data="Research AI trends and calculate market size",
        session_id="session_123",
        user_id="user_456"
    )
    trace.start()

    # LLM span
    llm1 = trace.create_span(SpanType.LLM_CALL, "Planning LLM Call")
    llm1.start()
    llm1.set_llm_data(
        prompt="Research AI trends",
        response="I'll search for AI trends",
        model="gpt-4"
    )
    llm1.set_tokens(prompt_tokens=50, completion_tokens=30, cost=0.005)
    llm1.end()

    # Tool span
    tool = trace.create_span(SpanType.TOOL_EXECUTION, "Web Search")
    tool.start()
    tool.set_tool_data(
        tool_name="web_search",
        args={"query": "AI trends 2024"},
        output=["article1", "article2", "article3"]
    )
    tool.end()

    # Another LLM span
    llm2 = trace.create_span(SpanType.LLM_CALL, "Response LLM Call")
    llm2.start()
    llm2.set_llm_data(
        prompt="Summarize AI trends",
        response="AI market is growing...",
        model="gpt-4"
    )
    llm2.set_tokens(prompt_tokens=100, completion_tokens=200, cost=0.015)
    llm2.end()

    trace.end(output="AI market size is estimated at $150B", status=TraceStatus.SUCCESS)

    return trace


def test_terminal_formatter():
    """Test terminal formatting"""
    print("\n=== Test 1: Terminal Formatter ===")

    trace = create_sample_trace()
    formatter = TerminalFormatter(use_colors=True)

    output = formatter.format(trace)

    print(output)

    assert "TestAgent" in output
    assert "Planning LLM Call" in output
    assert "Web Search" in output
    assert "$0.0200" in output  # Total cost

    print("\n✓ Terminal formatter test passed")


def test_terminal_formatter_no_colors():
    """Test terminal formatting without colors"""
    print("\n=== Test 2: Terminal Formatter (No Colors) ===")

    trace = create_sample_trace()
    formatter = TerminalFormatter(use_colors=False)

    output = formatter.format(trace)

    # Should not contain ANSI codes
    assert "\033[" not in output
    assert "TestAgent" in output

    print("✓ Terminal formatter (no colors) test passed")


def test_json_formatter():
    """Test JSON formatting"""
    print("\n=== Test 3: JSON Formatter ===")

    trace = create_sample_trace()
    formatter = JSONFormatter(indent=2)

    output = formatter.format(trace)

    # Should be valid JSON
    import json
    data = json.loads(output)

    assert data["agent_name"] == "TestAgent"
    assert len(data["spans"]) == 3
    assert data["total_cost"] == 0.02

    print(f"JSON output length: {len(output)} chars")
    print("✓ JSON formatter test passed")


def test_markdown_formatter():
    """Test Markdown formatting"""
    print("\n=== Test 4: Markdown Formatter ===")

    trace = create_sample_trace()
    formatter = MarkdownFormatter()

    output = formatter.format(trace)

    print("\n--- Markdown Output ---")
    print(output)
    print("--- End ---\n")

    assert "# Trace:" in output
    assert "## Metadata" in output
    assert "## Input/Output" in output
    assert "## Execution Steps" in output
    assert "TestAgent" in output

    print("✓ Markdown formatter test passed")


def test_format_trace_convenience():
    """Test convenience function"""
    print("\n=== Test 5: format_trace() Convenience Function ===")

    trace = create_sample_trace()

    # Terminal
    terminal_output = format_trace(trace, format="terminal")
    assert "TestAgent" in terminal_output
    print("✓ format_trace(terminal) works")

    # JSON
    json_output = format_trace(trace, format="json")
    import json
    data = json.loads(json_output)
    assert data["agent_name"] == "TestAgent"
    print("✓ format_trace(json) works")

    # Markdown
    md_output = format_trace(trace, format="markdown")
    assert "# Trace:" in md_output
    print("✓ format_trace(markdown) works")

    print("✓ format_trace() convenience function test passed")


def test_error_trace():
    """Test formatting trace with error"""
    print("\n=== Test 6: Error Trace ===")

    trace = Trace("ErrorAgent", "Test error handling")
    trace.start()

    span = trace.create_span(SpanType.LLM_CALL, "Failing LLM Call")
    span.start()

    try:
        raise ValueError("API key missing")
    except Exception as e:
        span.set_error(e)
        trace.set_error(e)

    trace.end()

    formatter = TerminalFormatter()
    output = formatter.format(trace)

    print(output)

    assert "ValueError" in output
    assert "API key missing" in output
    assert "error" in output.lower()

    print("\n✓ Error trace formatting test passed")


if __name__ == "__main__":
    print("Testing formatters...")
    test_terminal_formatter()
    test_terminal_formatter_no_colors()
    test_json_formatter()
    test_markdown_formatter()
    test_format_trace_convenience()
    test_error_trace()
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)