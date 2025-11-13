"""
Test to demonstrate 6 decimal place cost formatting.

This manually creates a trace with cost data to show the improved formatting.
"""

from peargent.observability import Trace, TraceStatus, Span, SpanType
from peargent.observability.formatters import TerminalFormatter

# Create a trace with cost data
trace = Trace(
    agent_name="TestAgent",
    input_data="Test query",
    trace_id="test-trace-123"
)

trace.start()

# Create a span with specific cost
span = trace.create_span(
    span_type=SpanType.LLM_CALL,
    name="LLM Call (step 1)"
)
span.start()

# Set token and cost data
span.token_prompt = 100
span.token_completion = 50
span.model = "gpt-4"

# Small cost to demonstrate 6 decimal places
# For example, 150 tokens at $0.000001 per token = $0.000150
span.cost = 0.000150

span.end()

trace.output = "Test response"
trace.end(output="Test response", status=TraceStatus.SUCCESS)

# Update trace totals
trace.total_cost = span.cost
trace.total_tokens = span.token_prompt + span.token_completion
trace.llm_calls_count = 1

print("="*80)
print("DEMONSTRATING 6 DECIMAL PLACE COST FORMATTING")
print("="*80)
print()

# Format and print the trace
formatter = TerminalFormatter()
output = formatter.format(trace)
try:
    print(output)
except UnicodeEncodeError:
    # Fallback for terminals that don't support Unicode
    safe_output = output.encode('ascii', errors='replace').decode('ascii')
    print(safe_output)

print()
print("="*80)
print("COMPARISON")
print("="*80)
print()
print("Old format (4 decimals): $0.0001 - would show small costs as $0.0000")
print("New format (6 decimals): $0.000150 - now shows small costs accurately!")
print()
print("This is especially useful for:")
print("- Small token amounts (50-300 tokens)")
print("- Cheap models like Groq, Llama")
print("- Detailed cost tracking and optimization")
