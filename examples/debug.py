"""Debug token storage issue"""

from peargent.observability.store import FileTracingStore, InMemoryTracingStore
from peargent.observability.trace import Trace
from peargent.observability.span import SpanType
from peargent.observability.tracer import Tracer, configure_tracing, get_tracer
import tempfile
import shutil
import json

def test_store_debug():
    """Debug the store saving issue"""
    print("\n=== Store Debug Test ===")
    
    # Test the store directly
    store = InMemoryTracingStore()
    
    # Create a simple trace manually
    from peargent.observability.trace import Trace
    
    trace = Trace(agent_name="TestAgent", input_data="Test")
    trace.start()
    trace.end(output="Done")
    
    print(f"DEBUG: Created trace {trace.trace_id}")
    print(f"DEBUG: Trace status = {trace.status}")
    print(f"DEBUG: Store length before save = {len(store)}")
    
    # Try to save it
    try:
        result = store.save_trace(trace)
        print(f"DEBUG: save_trace returned = {result}")
    except Exception as e:
        print(f"DEBUG: save_trace failed with error = {e}")
        import traceback
        traceback.print_exc()
    
    print(f"DEBUG: Store length after save = {len(store)}")
    
    # Check what's actually in the store
    if hasattr(store, '_traces'):
        print(f"DEBUG: Store._traces = {store._traces}")
    elif hasattr(store, 'traces'):
        print(f"DEBUG: Store.traces = {store.traces}")
    else:
        print(f"DEBUG: Store attributes = {dir(store)}")
    
    # Try to list traces
    try:
        traces = store.list_traces()
        print(f"DEBUG: list_traces() returned {len(traces)} traces")
    except Exception as e:
        print(f"DEBUG: list_traces() failed = {e}")

def test_tracer_auto_save():
    """Test tracer auto-save mechanism"""
    print("\n=== Tracer Auto-Save Test ===")
    
    store = InMemoryTracingStore() 
    tracer = Tracer(store=store, auto_save=True)
    
    print(f"DEBUG: Tracer auto_save = {tracer.auto_save}")
    print(f"DEBUG: Tracer store = {tracer.store}")
    print(f"DEBUG: Store is same object = {tracer.store is store}")
    
    # Test manual trace lifecycle
    trace_id = tracer.start_trace("ManualAgent", "Test")
    print(f"DEBUG: Started trace {trace_id}")
    
    # Check store before end_trace
    traces_before = store.list_traces()
    print(f"DEBUG: Store has {len(traces_before)} traces before end_trace")
    
    trace = tracer.end_trace(output="Done")
    print(f"DEBUG: Ended trace, status = {trace.status}")
    
    # Check store immediately after end_trace
    traces_after = store.list_traces()
    print(f"DEBUG: Store has {len(traces_after)} traces after end_trace")
    
    # Check tracer's internal state
    if hasattr(tracer, '_traces'):
        print(f"DEBUG: Tracer internal traces = {len(tracer._traces)}")
        for tid, t in tracer._traces.items():
            print(f"  - Internal: {t.trace_id}, status: {t.status}")

def test_tracer_context_manager():
    """Test tracer context manager"""
    print("\n=== Tracer Context Manager Test ===")
    
    store = InMemoryTracingStore()
    tracer = Tracer(store=store, auto_save=True)
    
    print(f"DEBUG: Before context manager, store has {len(store.list_traces())} traces")
    
    with tracer.trace_agent_run("ContextAgent", "Test") as trace:
        print(f"DEBUG: Inside context, trace = {trace}")
        print(f"DEBUG: Inside context, trace.trace_id = {trace.trace_id}")
        trace.output = "Done"
        print(f"DEBUG: Set output, trace.status = {trace.status}")
    
    print(f"DEBUG: After context manager")
    print(f"DEBUG: Store has {len(store.list_traces())} traces")
    
    # Check what's in the store
    traces = store.list_traces()
    if traces:
        for t in traces:
            print(f"  - Store trace: {t.trace_id}, status: {t.status}")
    else:
        print("  - No traces in store!")
    
    # Check tracer internal state
    if hasattr(tracer, '_traces'):
        print(f"DEBUG: Tracer has {len(tracer._traces)} internal traces")
        for tid, t in tracer._traces.items():
            print(f"  - Internal trace: {t.trace_id}, status: {t.status}")

def test_global_tracer_debug():
    """Debug the global tracer issue"""
    print("\n=== Global Tracer Debug Test ===")
    
    # Create fresh store and tracer
    store = InMemoryTracingStore()
    tracer = configure_tracing(store=store, enabled=True)
    
    print(f"DEBUG: Configured tracer auto_save = {tracer.auto_save}")
    print(f"DEBUG: Configured tracer store = {tracer.store}")
    print(f"DEBUG: Store is same object = {tracer.store is store}")
    
    global_tracer = get_tracer()
    print(f"DEBUG: Global tracer is same = {global_tracer is tracer}")
    
    # Test the specific failing case
    with global_tracer.trace_agent_run("GlobalAgent", "Test") as trace:
        print(f"DEBUG: Context trace = {trace}")
        trace.output = "Done"
    
    print(f"DEBUG: Store after context = {len(store.list_traces())}")
    print(f"DEBUG: Tracer internal after context = {len(tracer._traces) if hasattr(tracer, '_traces') else 'no _traces attr'}")

if __name__ == "__main__":
    test_store_debug()
    test_tracer_auto_save()
    test_tracer_context_manager()
    test_global_tracer_debug()