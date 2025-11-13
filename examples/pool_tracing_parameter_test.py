"""
Pool Tracing Parameter Test

This example demonstrates the new tracing parameter for pools.
When tracing=True on a pool, all agents get tracing enabled automatically,
unless an agent explicitly has tracing=False.
"""

from peargent import create_agent, create_pool, enable_tracing
from peargent.models import groq

# ============================================================================
# Setup: Enable tracing globally
# ============================================================================

tracer = enable_tracing()

# ============================================================================
# Scenario 1: Pool with tracing=True, all agents default (no explicit tracing)
# ============================================================================

print("="*80)
print("SCENARIO 1: Pool tracing=True, all agents use default")
print("="*80 + "\n")

# Create agents WITHOUT specifying tracing
agent1 = create_agent(
    name="Agent1",
    description="First agent",
    persona="You are helpful.",
    model=groq("llama-3.3-70b-versatile")
)

agent2 = create_agent(
    name="Agent2",
    description="Second agent",
    persona="You are helpful.",
    model=groq("llama-3.3-70b-versatile")
)

agent3 = create_agent(
    name="Agent3",
    description="Third agent",
    persona="You are helpful.",
    model=groq("llama-3.3-70b-versatile")
)

print("Before pool creation:")
print(f"  Agent1 tracing: {agent1.tracing}")
print(f"  Agent2 tracing: {agent2.tracing}")
print(f"  Agent3 tracing: {agent3.tracing}")

# Create pool with tracing=True - should enable tracing for all agents
def router1(state, call_count, last_result):
    from peargent.core.router import RouterResult
    agents = ["Agent1", "Agent2", "Agent3"]
    if call_count < len(agents):
        return RouterResult(agents[call_count])
    return RouterResult(None)

pool1 = create_pool(
    agents=[agent1, agent2, agent3],
    router=router1,
    max_iter=3,
    tracing=True  # Enable tracing at pool level
)

print("\nAfter pool creation with tracing=True:")
print(f"  Agent1 tracing: {agent1.tracing}")
print(f"  Agent2 tracing: {agent2.tracing}")
print(f"  Agent3 tracing: {agent3.tracing}")

result1 = pool1.run("What is 1+1?")
print(f"\nPool result: {result1[:50]}...")

# Check traces
traces = tracer.list_traces()
print(f"\nTraces captured: {len(traces)}")
tracer.print_summary()

# ============================================================================
# Scenario 2: Pool tracing=True, one agent explicitly has tracing=False
# ============================================================================

print("\n" + "="*80)
print("SCENARIO 2: Pool tracing=True, one agent explicitly opts out")
print("="*80 + "\n")

# Clear previous traces for clarity
tracer.get_store().clear_all()

# Create agents with mixed tracing settings
agent4 = create_agent(
    name="Agent4",
    description="Agent without explicit tracing",
    persona="You are helpful.",
    model=groq("llama-3.3-70b-versatile")
    # No tracing parameter - will be set by pool
)

agent5 = create_agent(
    name="Agent5",
    description="Agent that explicitly opts out",
    persona="You are helpful.",
    model=groq("llama-3.3-70b-versatile"),
    tracing=False  # Explicitly disable tracing
)

agent6 = create_agent(
    name="Agent6",
    description="Agent that explicitly opts in",
    persona="You are helpful.",
    model=groq("llama-3.3-70b-versatile"),
    tracing=True  # Explicitly enable tracing
)

print("Before pool creation:")
print(f"  Agent4 tracing: {agent4.tracing} (default)")
print(f"  Agent5 tracing: {agent5.tracing} (explicit False)")
print(f"  Agent6 tracing: {agent6.tracing} (explicit True)")

def router2(state, call_count, last_result):
    from peargent.core.router import RouterResult
    agents = ["Agent4", "Agent5", "Agent6"]
    if call_count < len(agents):
        return RouterResult(agents[call_count])
    return RouterResult(None)

pool2 = create_pool(
    agents=[agent4, agent5, agent6],
    router=router2,
    max_iter=3,
    tracing=True  # Enable tracing at pool level
)

print("\nAfter pool creation with tracing=True:")
print(f"  Agent4 tracing: {agent4.tracing} (should be True - inherited from pool)")
print(f"  Agent5 tracing: {agent5.tracing} (should be False - explicit opt-out)")
print(f"  Agent6 tracing: {agent6.tracing} (should be True - explicit opt-in)")

result2 = pool2.run("What is 2+2?")
print(f"\nPool result: {result2[:50]}...")

# Check traces
traces = tracer.list_traces()
print(f"\nTraces captured: {len(traces)}")
print("\nExpected: 2 traces (Agent4 and Agent6, but not Agent5)")

# Verify which agents were traced
traced_agents = [trace.agent_name for trace in traces]
print(f"Traced agents: {traced_agents}")

tracer.print_summary()

# ============================================================================
# Scenario 3: Pool without tracing parameter (default)
# ============================================================================

print("\n" + "="*80)
print("SCENARIO 3: Pool without tracing parameter (default behavior)")
print("="*80 + "\n")

# Clear previous traces
tracer.get_store().clear_all()

# Create agents
agent7 = create_agent(
    name="Agent7",
    description="Agent without tracing",
    persona="You are helpful.",
    model=groq("llama-3.3-70b-versatile")
)

agent8 = create_agent(
    name="Agent8",
    description="Agent with explicit tracing",
    persona="You are helpful.",
    model=groq("llama-3.3-70b-versatile"),
    tracing=True
)

print("Before pool creation:")
print(f"  Agent7 tracing: {agent7.tracing}")
print(f"  Agent8 tracing: {agent8.tracing}")

def router3(state, call_count, last_result):
    from peargent.core.router import RouterResult
    agents = ["Agent7", "Agent8"]
    if call_count < len(agents):
        return RouterResult(agents[call_count])
    return RouterResult(None)

# Create pool WITHOUT tracing parameter
pool3 = create_pool(
    agents=[agent7, agent8],
    router=router3,
    max_iter=2
    # No tracing parameter - default behavior
)

print("\nAfter pool creation (no tracing parameter):")
print(f"  Agent7 tracing: {agent7.tracing} (should be False - default)")
print(f"  Agent8 tracing: {agent8.tracing} (should be True - explicit)")

result3 = pool3.run("What is 3+3?")
print(f"\nPool result: {result3[:50]}...")

# Check traces
traces = tracer.list_traces()
print(f"\nTraces captured: {len(traces)}")
print("Expected: 1 trace (only Agent8)")

traced_agents = [trace.agent_name for trace in traces]
print(f"Traced agents: {traced_agents}")

# ============================================================================
# Summary
# ============================================================================

print("\n" + "="*80)
print("SUMMARY")
print("="*80)
print("""
NEW FEATURE: Pool-level tracing control

Usage:
    pool = create_pool(agents=[...], tracing=True)

Behavior:
1. If pool has tracing=True:
   - All agents without explicit tracing setting get tracing=True
   - Agents with explicit tracing=True stay True
   - Agents with explicit tracing=False stay False (opt-out respected)

2. If pool has no tracing parameter (default):
   - Agents keep their individual tracing settings
   - Only agents with explicit tracing=True are traced

Benefits:
- Enable tracing for entire pool with one parameter
- No need to set tracing=True on each agent individually
- Fine-grained control: agents can still opt out explicitly
- Cleaner code for multi-agent workflows
""")
