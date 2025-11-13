"""Test agent with tracing enabled"""

from peargent import create_agent
from peargent.models import groq
from peargent.observability import configure_tracing, get_tracer, format_trace
from peargent.observability.store import InMemoryTracingStore

# Configure tracing
store = InMemoryTracingStore()
configure_tracing(enabled=True, store=store)

# Create agent with tracing enabled
agent = create_agent(
    name="TestAgent",
    description="A test agent",
    persona="You are a helpful assistant.",
    model=groq("llama-3.3-70b-versatile"),
    tracing=True  # Enable tracing
)

# Run agent
print("Running agent...")
result = agent.run("What is 2+2?")
result = agent.run("What is 2+4?")
print(f"Result: {result}")

# Get the trace
tracer = get_tracer()
traces = store.list_traces()

if traces:
    print(f"\n✓ Captured {len(traces)} trace(s)")

    # Display the trace
    trace = traces[0]
    print("\n" + "="*80)
    print(format_trace(trace, format="terminal"))
    print("="*80)

    # Show metrics
    print(f"\nMetrics:")
    print(f"  Duration: {trace.duration:.3f}s")
    print(f"  Cost: ${trace.total_cost:.6f}")
    print(f"  Tokens: {trace.total_tokens}")
    print(f"  LLM Calls: {trace.llm_calls_count}")
    print(f"  Tool Calls: {trace.tool_calls_count}")
else:
    print("❌ No traces captured")