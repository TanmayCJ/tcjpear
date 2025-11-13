"""
Pool Tracing Example

This example demonstrates how the improved tracing DSL works with agent pools.
Now you can enable tracing for ALL agents in a pool with a single parameter!
"""

from peargent import create_agent, create_pool, enable_tracing
from peargent.models import groq

# ============================================================================
# Enable tracing once for all agents
# ============================================================================

tracer = enable_tracing()

# ============================================================================
# Create multiple agents WITHOUT setting tracing individually
# ============================================================================

# Agent 1: Research specialist
researcher = create_agent(
    name="Researcher",
    description="Expert at gathering and analyzing information",
    persona="You are a research specialist. Provide detailed, factual information.",
    model=groq("llama-3.3-70b-versatile")
    # No tracing parameter - will be set by pool
)

# Agent 2: Writer specialist
writer = create_agent(
    name="Writer",
    description="Expert at creating clear, engaging content",
    persona="You are a professional writer. Take information and make it clear and engaging.",
    model=groq("llama-3.3-70b-versatile")
    # No tracing parameter - will be set by pool
)

# Agent 3: Reviewer specialist
reviewer = create_agent(
    name="Reviewer",
    description="Expert at reviewing and improving content",
    persona="You are a content reviewer. Provide final polish and improvements.",
    model=groq("llama-3.3-70b-versatile")
    # No tracing parameter - will be set by pool
)

# ============================================================================
# Create a pool with these agents - NEW: use tracing=True at pool level!
# ============================================================================

# Simple router that goes through all agents in sequence
def sequential_router(state, call_count, last_result):
    from peargent.core.router import RouterResult

    agents_sequence = ["Researcher", "Writer", "Reviewer"]

    if call_count < len(agents_sequence):
        return RouterResult(agents_sequence[call_count])
    return RouterResult(None)  # Done

pool = create_pool(
    agents=[researcher, writer, reviewer],
    router=sequential_router,
    max_iter=3,
    tracing=True  # NEW: Enable tracing for all agents in the pool!
)

# ============================================================================
# Run the pool - all agents will be traced
# ============================================================================

print("Running pool with multiple agents...")
print("="*80 + "\n")

result = pool.run("Explain what quantum computing is in simple terms")

print(f"\nFinal Result:\n{result}\n")

# ============================================================================
# View all traces from all agents in the pool
# ============================================================================

print("\n" + "="*80)
print("TRACES FROM ALL AGENTS IN THE POOL")
print("="*80 + "\n")

traces = tracer.list_traces()
print(f"Total traces captured: {len(traces)}\n")

# Print summary of each trace
for i, trace in enumerate(traces, 1):
    print(f"{i}. Agent: {trace.agent_name}")
    print(f"   Status: {trace.status.value}")
    print(f"   Duration: {trace.duration:.3f}s")
    print(f"   LLM Calls: {trace.llm_calls_count}")
    print(f"   Input: {trace.input[:50]}...")
    print(f"   Output: {trace.output[:50] if trace.output else 'N/A'}...")
    print()

# ============================================================================
# Filter traces by agent name
# ============================================================================

print("\n" + "="*80)
print("TRACES FROM RESEARCHER AGENT ONLY")
print("="*80 + "\n")

researcher_traces = tracer.list_traces(agent_name="Researcher")
tracer.print_traces(agent_name="Researcher", limit=1, format="terminal")

# ============================================================================
# Get aggregate statistics across all agents in the pool
# ============================================================================

print("\n" + "="*80)
print("AGGREGATE METRICS FOR THE ENTIRE POOL")
print("="*80 + "\n")

# Get stats programmatically
stats = tracer.get_aggregate_stats()

print("Programmatic access to stats:")
print(f"  Total Cost: ${stats['total_cost']:.6f}")
print(f"  Total Tokens: {stats['total_tokens']:,}")
print(f"  Total LLM Calls: {stats['total_llm_calls']}")
print(f"  Agents Used: {stats['agents_used']}")
print()

# Print a nice formatted summary
print("Formatted summary:")
print()
tracer.print_summary()

print("\n" + "="*80)
print("SUMMARY - NEW POOL TRACING FEATURE")
print("="*80)
print("""
The improved tracing DSL now makes pool tracing even easier!

OLD WAY (verbose):
    agent1 = create_agent(..., tracing=True)
    agent2 = create_agent(..., tracing=True)
    agent3 = create_agent(..., tracing=True)
    pool = create_pool(agents=[agent1, agent2, agent3])

NEW WAY (simple):
    agent1 = create_agent(...)  # No tracing parameter
    agent2 = create_agent(...)  # No tracing parameter
    agent3 = create_agent(...)  # No tracing parameter
    pool = create_pool(agents=[...], tracing=True)  # One parameter!

Key features:
1. Enable tracing once with enable_tracing()
2. Create agents WITHOUT setting tracing individually
3. Use pool's tracing=True to enable for all agents at once
4. Use tracer.list_traces() to see all traces from all agents
5. Filter by agent_name to see traces from specific agents
6. Each agent execution gets its own trace

Aggregate metrics across all agents:
7. Use tracer.get_aggregate_stats() to get totals programmatically
8. Use tracer.print_summary() to see a formatted summary
   - Total cost across all agents
   - Total tokens used
   - Total LLM/tool calls
   - Average cost and tokens per agent
   - List of all agents used

Advanced: Fine-grained control
- If an agent explicitly has tracing=False, it will NOT be traced
  even if the pool has tracing=True (opt-out is respected)
- Example:
    agent1 = create_agent(..., tracing=False)  # Will NOT be traced
    agent2 = create_agent(...)  # Will be traced
    pool = create_pool(agents=[agent1, agent2], tracing=True)

This gives you complete visibility into multi-agent workflows!
""")
