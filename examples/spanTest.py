from peargent.observability.span import Span, SpanType, SpanStatus
import time

def test_basic_span():
    """Test basic span creation and timing
    """
    print("\n=== Test 1: Basic Span ===")
    
    span = Span(
        trace_id="test_trace_123",
        span_type=SpanType.LLM_CALL,
        name="Groq LLM Call"
    )
    
    span.start()
    time.sleep(1)  # Simulate some operation
    span.end(status=SpanStatus.SUCCESS)
    
    print(f"Span: {span}")
    print(f"Duration: {span.duration:.3f}s")
    print(f"Status: {span.status.value}")
    assert span.duration is not None
    assert span.duration >= 0.1
    print(" Basic span test passed")
    
def test_llm_span():
    """Test LLM-specific span
    """
    print("\n=== Test 2: LLM Span ===")
    
    span = Span(
        trace_id="llm_trace_456",
        span_type=SpanType.LLM_CALL,
        name="LLM Call Span"
    )
    
    span.start()
    span.set_llm_data(
        prompt="Hello, how are you?",
        response="I'm fine, thank you!",
        model="groq/llama-3.3-70b-versatile"
    )
    span.set_tokens(
        prompt_tokens=10,
        completion_tokens=12,
        cost=0.0025,
    )
    span.end()
    
    print(f"Model: {span.model}")
    print(f"Tokens: {span.token_prompt} prompt, {span.token_completion} completion")
    print(f"Cost: ${span.cost}")
    
    data = span.to_dict()
    print(f" Serialized Span: {list(data.keys())[:5]}...")
    print(f"LLM span test passed")
    
def test_tool_span():
    """Test tool execution span
    """
    print("\n=== Test 3: Tool Span ===")
    
    span = Span(
        trace_id="tool_trace_789",
        span_type = SpanType.TOOL_EXECUTION,
        name="Web search"
    )    
    
    span.start()
    span.set_tool_data(
        tool_name="web_search",
        args={"query": "Latest news on AI", "Limit": 5},
        output=["result1", "result2", "result3"]
    )
    span.add_metadata("source", "Google")
    span.add_metadata("cache_hit", False)
    span.end()
    
    print(f"Tool: {span.tool_name}")
    print(f"Args: {span.tool_args}")
    print(f"Metadata: {span.metadata}")
    print(f" Tool span test passed")
    
def test_error_span():
    """Test span with Error
    """
    print("\n=== Test 4: Error Span ===")
    
    span = Span(
        trace_id="error_trace_000",
        span_type=SpanType.AGENT_RUN,
        name="Agent Execution"
    )
    
    span.start()
    try:
        raise ValueError("Test error: API key missing")
    except Exception as e:
        span.set_error(e)
    
    print(f"Status: {span.status.value}")
    print(f"Error Type: {span.error_type}")
    print(f"Error Message: {span.error_message}")
    assert span.status == SpanStatus.ERROR
    print(" Error span test passed")
    
def test_nested_spans():
      """Test parent-child relationship"""
      print("\n=== Test 5: Nested Spans ===")

      parent = Span(
          trace_id="test_trace_nested",
          span_type=SpanType.AGENT_RUN,
          name="Agent Run"
      )
      parent.start()

      child1 = Span(
          trace_id="test_trace_nested",
          span_type=SpanType.LLM_CALL,
          name="LLM Call",
          parent_id=parent.span_id
      )
      child1.start()
      time.sleep(0.05)
      child1.end()

      child2 = Span(
          trace_id="test_trace_nested",
          span_type=SpanType.TOOL_EXECUTION,
          name="Tool Call",
          parent_id=parent.span_id
      )
      child2.start()
      time.sleep(0.05)
      child2.end()

      parent.end()

      print(f"Parent: {parent.span_id}")
      print(f"Child 1: {child1.span_id} (parent: {child1.parent_id})")
      print(f"Child 2: {child2.span_id} (parent: {child2.parent_id})")
      assert child1.parent_id == parent.span_id
      assert child2.parent_id == parent.span_id
      print("✓ Nested spans test passed")


if __name__ == "__main__":
      print("Testing Span class...")
      test_basic_span()
      test_llm_span()
      test_tool_span()
      test_error_span()
      test_nested_spans()
      print("\n" + "="*50)
      print("All tests passed! ✓")
      print("="*50)
    
