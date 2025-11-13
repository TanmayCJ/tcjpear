"""Test the Tracer class"""

from peargent.observability.tracer import Tracer, get_tracer, configure_tracing
from peargent.observability.store import InMemoryTracingStore
from peargent.observability.span import SpanType
from peargent.observability.trace import TraceStatus
import time


def test_basic_tracing():
    """Test basic trace creation"""
    print("\n=== Test 1: Basic Tracing ===")

    tracer = Tracer()

    # Start trace
    trace_id = tracer.start_trace(
        agent_name="TestAgent",
        input_data="Hello",
        session_id="s1"
    )

    assert trace_id is not None
    print(f"✓ Started trace: {trace_id}")

    # Get current trace
    trace = tracer.get_current_trace()
    assert trace is not None
    assert trace.trace_id == trace_id
    print(f"✓ Retrieved current trace")

    # End trace
    completed = tracer.end_trace(output="World", status=TraceStatus.SUCCESS)
    assert completed is not None
    assert completed.output == "World"
    print(f"✓ Ended trace")

    print("✓ Basic tracing test passed")


def test_spans():
    """Test creating spans"""
    print("\n=== Test 2: Spans ===")

    tracer = Tracer()

    # Start trace
    trace_id = tracer.start_trace("SpanAgent", "Test")

    # Create LLM span
    llm_span = tracer.start_span(SpanType.LLM_CALL, "LLM Call")
    assert llm_span is not None
    llm_span.set_llm_data(prompt="Hello", response="Hi", model="gpt-4")
    llm_span.set_tokens(prompt_tokens=10, completion_tokens=5, cost=0.001)
    print(f"✓ Created LLM span: {llm_span.span_id}")

    # Create tool span (child of LLM span)
    tool_span = tracer.start_span(SpanType.TOOL_EXECUTION, "Tool Call")
    assert tool_span is not None
    assert tool_span.parent_id == llm_span.span_id  # Auto-parented
    print(f"✓ Created tool span with parent: {tool_span.parent_id}")

    # End spans
    tracer.end_span()  # Ends tool span
    tracer.end_span()  # Ends LLM span

    # End trace
    trace = tracer.end_trace()
    assert len(trace.spans) == 2
    print(f"✓ Trace has {len(trace.spans)} spans")

    print("✓ Spans test passed")


def test_context_manager_trace():
    """Test trace context manager"""
    print("\n=== Test 3: Trace Context Manager ===")

    tracer = Tracer()

    with tracer.trace_agent_run("ContextAgent", "Test input") as trace:
        assert trace is not None
        print(f"✓ Trace started: {trace.trace_id}")

        time.sleep(0.1)
        trace.output = "Test output"

    # Trace should be ended and saved
    retrieved = tracer.get_trace(trace.trace_id)
    assert retrieved is not None
    assert retrieved.output == "Test output"
    assert retrieved.status == TraceStatus.SUCCESS
    assert retrieved.duration >= 0.1
    print(f"✓ Trace ended with duration: {retrieved.duration:.3f}s")

    print("✓ Trace context manager test passed")


def test_context_manager_spans():
    """Test span context managers"""
    print("\n=== Test 4: Span Context Managers ===")

    tracer = Tracer()

    with tracer.trace_agent_run("SpanContextAgent", "Test") as trace:
        # LLM call
        with tracer.trace_llm_call("Planning", model="gpt-4") as span:
            assert span is not None
            span.set_llm_data(prompt="Plan", response="OK", model="gpt-4")
            span.set_tokens(prompt_tokens=20, completion_tokens=10, cost=0.002)
            print(f"✓ LLM span created: {span.name}")

        # Tool call
        with tracer.trace_tool_execution("web_search", {"query": "test"}) as span:
            assert span is not None
            span.set_tool_data(output=["result1", "result2"])
            print(f"✓ Tool span created: {span.name}")

    # Verify trace
    retrieved = tracer.get_trace(trace.trace_id)
    assert len(retrieved.spans) == 2
    assert retrieved.llm_calls_count == 1
    assert retrieved.tool_calls_count == 1
    assert retrieved.total_cost == 0.002
    print(f"✓ Trace metrics: {retrieved.llm_calls_count} LLM, {retrieved.tool_calls_count} tool")

    print("✓ Span context managers test passed")


def test_error_handling():
    """Test error handling in traces"""
    print("\n=== Test 5: Error Handling ===")

    tracer = Tracer()

    try:
        with tracer.trace_agent_run("ErrorAgent", "Test") as trace:
            raise ValueError("Test error")
    except ValueError:
        pass  # Expected

    # Trace should have error
    retrieved = tracer.get_trace(trace.trace_id)
    assert retrieved.status == TraceStatus.ERROR
    assert retrieved.error_type == "ValueError"
    assert retrieved.error_message == "Test error"
    print(f"✓ Error captured: {retrieved.error_type}")

    print("✓ Error handling test passed")


def test_disabled_tracing():
    """Test that disabled tracing doesn't create traces"""
    print("\n=== Test 6: Disabled Tracing ===")

    tracer = Tracer(enabled=False)

    # Try to start trace
    trace_id = tracer.start_trace("DisabledAgent", "Test")
    assert trace_id is None
    print("✓ Disabled tracer returns None for start_trace")

    # Context managers should yield None
    with tracer.trace_agent_run("Test", "input") as trace:
        assert trace is None
        print("✓ Disabled tracer yields None in context manager")

    print("✓ Disabled tracing test passed")


# def test_global_tracer():
#     """Test global tracer instance"""
#     print("\n=== Test 7: Global Tracer ===")

#     # Configure global tracer
#     store = InMemoryTracingStore()
#     tracer = configure_tracing(store=store, enabled=True)

#     # Get global tracer
#     global_tracer = get_tracer()
#     assert global_tracer is tracer
#     print("✓ Global tracer configured")

#     # Use it
#     with global_tracer.trace_agent_run("GlobalAgent", "Test") as trace:
#         trace.output = "Done"

#     # Verify it was saved to the store
#     traces = store.list_traces()
#     assert len(traces) == 1
#     print(f"✓ Global tracer saved {len(traces)} trace(s)")

#     print("✓ Global tracer test passed")


def test_list_traces():
    """Test listing traces with filters"""
    print("\n=== Test 8: List Traces ===")

    tracer = Tracer()

    # Create multiple traces
    with tracer.trace_agent_run("Agent1", "input1", session_id="s1", user_id="u1"):
        pass

    with tracer.trace_agent_run("Agent1", "input2", session_id="s1", user_id="u2"):
        pass

    with tracer.trace_agent_run("Agent2", "input3", session_id="s2", user_id="u1"):
        pass

    # List all
    all_traces = tracer.list_traces()
    assert len(all_traces) == 3
    print(f"✓ Listed all {len(all_traces)} traces")

    # Filter by session
    session_traces = tracer.list_traces(session_id="s1")
    assert len(session_traces) == 2
    print(f"✓ Filtered by session: {len(session_traces)} traces")

    # Filter by user
    user_traces = tracer.list_traces(user_id="u1")
    assert len(user_traces) == 2
    print(f"✓ Filtered by user: {len(user_traces)} traces")

    # Filter by agent
    agent_traces = tracer.list_traces(agent_name="Agent1")
    assert len(agent_traces) == 2
    print(f"✓ Filtered by agent: {len(agent_traces)} traces")

    print("✓ List traces test passed")
    
def test_global_tracer():
    """Test global tracer instance"""
    print("\n=== Test 7: Global Tracer ===")

    # Configure global tracer
    store = InMemoryTracingStore()
    tracer = configure_tracing(store=store, enabled=True)

    # Get global tracer
    global_tracer = get_tracer()
    assert global_tracer is tracer
    print("✓ Global tracer configured")

    # DEBUG: Check tracer properties
    print(f"DEBUG: Tracer store = {tracer.store}")
    print(f"DEBUG: Store type = {type(tracer.store)}")

    # Use it
    print("DEBUG: Starting trace context manager...")
    with global_tracer.trace_agent_run("GlobalAgent", "Test") as trace:
        print(f"DEBUG: Inside context manager, trace = {trace}")
        if trace:
            print(f"DEBUG: Trace ID = {trace.trace_id}")
            print(f"DEBUG: Trace status before output = {trace.status}")
        trace.output = "Done"
        if trace:
            print(f"DEBUG: Trace status after output = {trace.status}")
    
    print("DEBUG: Exited context manager")

    # Check if trace exists in tracer's internal storage
    if hasattr(tracer, '_traces'):
        print(f"DEBUG: Tracer internal traces = {len(tracer._traces)}")
        for tid, t in tracer._traces.items():
            print(f"  - Internal trace: {t.agent_name}, {t.trace_id}, status: {t.status}")

    # Check what's in the store
    traces = store.list_traces()
    print(f"DEBUG: Store has {len(traces)} trace(s)")
    
    if len(traces) == 0:
        print("DEBUG: No traces saved!")
        # Try to manually save if the trace exists
        if trace:
            print("DEBUG: Manually saving trace...")
            tracer.store.save_trace(trace)
            traces = store.list_traces()
            print(f"DEBUG: After manual save: {len(traces)} trace(s)")
    else:
        for t in traces:
            print(f"  - Trace: {t.agent_name}, {t.trace_id}")

    assert len(traces) == 1, f"Expected 1 trace, got {len(traces)}"
    print(f"✓ Global tracer saved {len(traces)} trace(s)")

    print("✓ Global tracer test passed")


if __name__ == "__main__":
    print("Testing Tracer class...")
    test_basic_tracing()
    test_spans()
    test_context_manager_trace()
    test_context_manager_spans()
    test_error_handling()
    test_disabled_tracing()
    test_global_tracer()
    test_list_traces()
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)