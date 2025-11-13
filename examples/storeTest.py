"""Test storage backends"""

from peargent.observability.store import InMemoryTracingStore, FileTracingStore
from peargent.observability.trace import Trace
from peargent.observability.span import SpanType
import tempfile
import shutil


def test_inmemory_store():
    """Test in-memory storage"""
    print("\n=== Test 1: InMemory Store ===")

    store = InMemoryTracingStore()

    # Create and save trace
    trace = Trace(agent_name="TestAgent", input_data="Hello", session_id="s1")
    trace.start()

    span = trace.create_span(SpanType.LLM_CALL, "Test Span")
    span.start()
    span.set_tokens(prompt_tokens=10, completion_tokens=5, cost=0.001)
    span.end()

    trace.end(output="World")

    store.save_trace(trace)

    # Retrieve trace
    retrieved = store.get_trace(trace.trace_id)
    assert retrieved is not None
    assert retrieved.trace_id == trace.trace_id
    assert retrieved.agent_name == "TestAgent"
    print(f"✓ Saved and retrieved trace: {retrieved.trace_id}")

    # List traces
    traces = store.list_traces()
    assert len(traces) == 1
    print(f"✓ Listed {len(traces)} trace(s)")

    # Delete trace
    deleted = store.delete_trace(trace.trace_id)
    assert deleted is True
    assert store.get_trace(trace.trace_id) is None
    print("✓ Deleted trace")

    print("✓ InMemory store test passed")


def test_file_store():
    """Test file-based storage"""
    print("\n=== Test 2: File Store ===")

    # Create temp directory
    temp_dir = tempfile.mkdtemp()

    try:
        store = FileTracingStore(storage_dir=temp_dir)

        # Create and save trace
        trace = Trace(
            agent_name="FileAgent",
            input_data="Test input",
            session_id="session_123",
            user_id="user_456"
        )
        trace.start()

        span1 = trace.create_span(SpanType.LLM_CALL, "LLM Span")
        span1.start()
        span1.set_llm_data(prompt="Hello", response="Hi", model="gpt-4")
        span1.set_tokens(prompt_tokens=50, completion_tokens=30, cost=0.005)
        span1.end()

        span2 = trace.create_span(SpanType.TOOL_EXECUTION, "Tool Span")
        span2.start()
        span2.set_tool_data(tool_name="search", args={"q": "test"},
output=["result"])
        span2.end()

        trace.end(output="Test output")

        store.save_trace(trace)

        # Retrieve trace
        retrieved = store.get_trace(trace.trace_id)
        assert retrieved is not None
        assert retrieved.trace_id == trace.trace_id
        assert retrieved.agent_name == "FileAgent"
        assert retrieved.session_id == "session_123"
        assert retrieved.user_id == "user_456"
        assert len(retrieved.spans) == 2
        print(f"✓ Retrieved trace with {len(retrieved.spans)} spans")
        
        # Verify span data
        llm_spans = retrieved.get_spans_by_type(SpanType.LLM_CALL)
        assert len(llm_spans) == 1
        assert llm_spans[0].model == "gpt-4"

        # Debug: print the actual value
        print(f"DEBUG: tokens_prompt = {llm_spans[0].token_prompt}")
        print(f"DEBUG: tokens_completion = {llm_spans[0].token_completion}")
        print(f"DEBUG: cost = {llm_spans[0].cost}")

        assert llm_spans[0].token_prompt == 50

        # Verify span data
        llm_spans = retrieved.get_spans_by_type(SpanType.LLM_CALL)
        assert len(llm_spans) == 1
        assert llm_spans[0].model == "gpt-4"
        assert llm_spans[0].token_prompt == 50
        print("✓ Verified LLM span data")

        tool_spans = retrieved.get_spans_by_type(SpanType.TOOL_EXECUTION)
        assert len(tool_spans) == 1
        assert tool_spans[0].tool_name == "search"
        print("✓ Verified tool span data")

        # List traces
        traces = store.list_traces()
        assert len(traces) == 1
        print(f"✓ Listed {len(traces)} trace(s)")

        # Delete trace
        deleted = store.delete_trace(trace.trace_id)
        assert deleted is True
        assert store.get_trace(trace.trace_id) is None
        print("✓ Deleted trace file")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)

    print("✓ File store test passed")


def test_store_filtering():
    """Test filtering traces by session/user/agent"""
    print("\n=== Test 3: Store Filtering ===")

    store = InMemoryTracingStore()

    # Create multiple traces with different attributes
    trace1 = Trace("Agent1", "input1", session_id="s1", user_id="u1")
    trace1.start().end(output="out1")
    store.save_trace(trace1)

    trace2 = Trace("Agent1", "input2", session_id="s1", user_id="u2")
    trace2.start().end(output="out2")
    store.save_trace(trace2)

    trace3 = Trace("Agent2", "input3", session_id="s2", user_id="u1")
    trace3.start().end(output="out3")
    store.save_trace(trace3)

    # Filter by session
    session_traces = store.list_traces(session_id="s1")
    assert len(session_traces) == 2
    print(f"✓ Filtered by session: {len(session_traces)} traces")

    # Filter by user
    user_traces = store.list_traces(user_id="u1")
    assert len(user_traces) == 2
    print(f"✓ Filtered by user: {len(user_traces)} traces")

    # Filter by agent
    agent_traces = store.list_traces(agent_name="Agent1")
    assert len(agent_traces) == 2
    print(f"✓ Filtered by agent: {len(agent_traces)} traces")

    # Multiple filters
    filtered = store.list_traces(session_id="s1", user_id="u1")
    assert len(filtered) == 1
    assert filtered[0].trace_id == trace1.trace_id
    print(f"✓ Filtered by session+user: {len(filtered)} trace")

    print("✓ Store filtering test passed")


def test_clear_all():
    """Test clearing all traces"""
    print("\n=== Test 4: Clear All ===")

    store = InMemoryTracingStore()

    # Add multiple traces
    for i in range(5):
        trace = Trace(f"Agent{i}", f"input{i}")
        trace.start().end(output=f"out{i}")
        store.save_trace(trace)

    assert len(store) == 5
    print(f"✓ Created {len(store)} traces")

    # Clear all
    count = store.clear_all()
    assert count == 5
    assert len(store) == 0
    print(f"✓ Cleared {count} traces")

    print("✓ Clear all test passed")


if __name__ == "__main__":
    print("Testing storage backends...")
    test_inmemory_store()
    test_file_store()
    test_store_filtering()
    test_clear_all()
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)