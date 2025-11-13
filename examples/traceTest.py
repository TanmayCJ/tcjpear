from peargent.observability.trace import Trace, TraceStatus
from peargent.observability.span import SpanType, SpanStatus
import time

def test_basic_trace():
    """Test basic trace creation and timing
    """
    print("\n=== Test 1: Basic Trace ===")
    
    trace = Trace(
        agent_name="TestAgent",
        input_data="Hello, how are you?",
        session_id="session_123",
        user_id="user_456"
    )
    
    trace.start()
    time.sleep(1.5)  # Simulate some operations
    trace.end(output="I am doing well", status=TraceStatus.SUCCESS)
    
    print(f"Trace: {trace}")
    print(f"Duration: {trace.duration:.3f}s")
    print(f"Status: {trace.status.value}")
    assert trace.duration is not None
    assert trace.duration >= 1.0
    print(" Basic trace test passed")
    
def test_trace_with_spans():
      """Test trace with multiple spans"""
      print("\n=== Test 2: Trace with Spans ===")

      trace = Trace(
          agent_name="ResearchAgent",
          input_data="Research AI trends",
          session_id="session_789"
      )
      trace.start()

      # Add LLM span
      llm_span = trace.create_span(
          span_type=SpanType.LLM_CALL,
          name="Planning LLM Call"
      )
      llm_span.start()
      llm_span.set_llm_data(
          prompt="Research AI trends",
          response="I'll search for AI trends",
          model="gpt-4"
      )
      llm_span.set_tokens(prompt_tokens=50, completion_tokens=30, cost=0.002)
      llm_span.end()

      # Add tool span
      tool_span = trace.create_span(
          span_type=SpanType.TOOL_EXECUTION,
          name="Web Search",
          parent_id=llm_span.span_id
      )
      tool_span.start()
      tool_span.set_tool_data(
          tool_name="web_search",
          args={"query": "AI trends"},
          output=["result1", "result2"]
      )
      time.sleep(0.05)
      tool_span.end()

      # Add another LLM span
      llm_span2 = trace.create_span(
          span_type=SpanType.LLM_CALL,
          name="Response LLM Call"
      )
      llm_span2.start()
      llm_span2.set_llm_data(
          prompt="Summarize results",
          response="Here are the AI trends...",
          model="gpt-4"
      )
      llm_span2.set_tokens(prompt_tokens=100, completion_tokens=200, cost=0.015)
      llm_span2.end()

      trace.end(output="AI trends summary", status=TraceStatus.SUCCESS)

      print(f"Trace ID: {trace.trace_id}")
      print(f"Total spans: {len(trace.spans)}")
      print(f"LLM calls: {trace.llm_calls_count}")
      print(f"Tool calls: {trace.tool_calls_count}")
      print(f"Total tokens: {trace.total_tokens}")
      print(f"Total cost: ${trace.total_cost:.4f}")

      assert len(trace.spans) == 3
      assert trace.llm_calls_count == 2
      assert trace.tool_calls_count == 1
      assert trace.total_tokens == 380  # 50+30+100+200
      assert abs(trace.total_cost - 0.017) < 0.001  # 0.002 + 0.015
      print("✓ Trace with spans test passed")
    
def test_trace_queries():
      """Test querying spans within a trace"""
      print("\n=== Test 3: Trace Queries ===")

      trace = Trace(agent_name="QueryAgent", input_data="Test")
      trace.start()

      # Create various spans
      span1 = trace.create_span(SpanType.LLM_CALL, "LLM 1")
      span2 = trace.create_span(SpanType.TOOL_EXECUTION, "Tool 1")
      span3 = trace.create_span(SpanType.LLM_CALL, "LLM 2")
      span4 = trace.create_span(SpanType.TOOL_EXECUTION, "Tool 2", parent_id=span3.span_id)

      # Test get_span
      retrieved = trace.get_span(span2.span_id)
      assert retrieved == span2
      print(f"✓ Retrieved span by ID: {retrieved.name}")

      # Test get_spans_by_type
      llm_spans = trace.get_spans_by_type(SpanType.LLM_CALL)
      assert len(llm_spans) == 2
      print(f"✓ Found {len(llm_spans)} LLM spans")

      tool_spans = trace.get_spans_by_type(SpanType.TOOL_EXECUTION)
      assert len(tool_spans) == 2
      print(f"✓ Found {len(tool_spans)} tool spans")

      # Test get_child_spans
      children = trace.get_child_spans(span3.span_id)
      assert len(children) == 1
      assert children[0] == span4
      print(f"✓ Found child span: {children[0].name}")

      trace.end()
      print("✓ Trace queries test passed")


def test_trace_error():
      """Test trace with error"""
      print("\n=== Test 4: Trace Error ===")

      trace = Trace(agent_name="ErrorAgent", input_data="Test error")
      trace.start()

      # Add a span
      span = trace.create_span(SpanType.LLM_CALL, "Failing LLM Call")
      span.start()

      try:
          raise ValueError("API key invalid")
      except Exception as e:
          span.set_error(e)
          trace.set_error(e)

      trace.end()

      print(f"Status: {trace.status.value}")
      print(f"Error type: {trace.error_type}")
      print(f"Error message: {trace.error_message}")
      assert trace.status == TraceStatus.ERROR
      print("✓ Trace error test passed")


def test_trace_summary():
      """Test trace summary output"""
      print("\n=== Test 5: Trace Summary ===")

      trace = Trace(
          agent_name="SummaryAgent",
          input_data="Generate summary",
          user_id="user_123"
      )
      trace.start()

      # Add some spans with costs
      span1 = trace.create_span(SpanType.LLM_CALL, "LLM Call")
      span1.start()
      span1.set_tokens(prompt_tokens=100, completion_tokens=50, cost=0.005)
      span1.end()

      span2 = trace.create_span(SpanType.TOOL_EXECUTION, "Tool Call")
      span2.start()
      span2.end()

      trace.add_metadata("environment", "production")
      trace.add_metadata("version", "1.0.0")
      trace.end(output="Summary generated")

      print("\n" + "="*50)
      print(trace.summary())
      print("="*50)

      assert "SummaryAgent" in trace.summary()
      assert "$0.0050" in trace.summary()
      print("✓ Trace summary test passed")


def test_trace_serialization():
      """Test trace to_dict and to_json"""
      print("\n=== Test 6: Trace Serialization ===")

      trace = Trace(agent_name="SerializeAgent", input_data="Test")
      trace.start()

      span = trace.create_span(SpanType.LLM_CALL, "Test Span")
      span.start()
      span.set_tokens(prompt_tokens=10, completion_tokens=5, cost=0.001)
      span.end()

      trace.end(output="Done")

      # Test to_dict
      data = trace.to_dict()
      assert "trace_id" in data
      assert "spans" in data
      assert len(data["spans"]) == 1
      print(f"✓ to_dict() keys: {list(data.keys())[:5]}...")

      # Test to_json
      json_str = trace.to_json()
      assert isinstance(json_str, str)
      assert "trace_id" in json_str
      print(f"✓ to_json() length: {len(json_str)} chars")

      print("✓ Trace serialization test passed")


if __name__ == "__main__":
      print("Testing Trace class...")
      test_basic_trace()
      test_trace_with_spans()
      test_trace_queries()
      test_trace_error()
      test_trace_summary()
      test_trace_serialization()
      print("\n" + "="*50)
      print("All tests passed! ✓")
      print("="*50)