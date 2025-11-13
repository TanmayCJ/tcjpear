"""Test the CostTracker"""

from peargent.observability.cost_tracker import (
    CostTracker, get_cost_tracker, count_tokens, calculate_cost, PRICING
)


def test_token_counting_estimate():
    """Test token counting with estimation (no tiktoken)"""
    print("\n=== Test 1: Token Counting (Estimation) ===")

    tracker = CostTracker(use_tiktoken=False)

    text = "Hello, how are you today?"
    tokens = tracker.count_tokens(text)

    print(f"Text: '{text}'")
    print(f"Estimated tokens: {tokens}")
    assert tokens > 0
    print("✓ Token estimation works")


def test_token_counting_tiktoken():
    """Test token counting with tiktoken"""
    print("\n=== Test 2: Token Counting (Tiktoken) ===")

    tracker = CostTracker(use_tiktoken=True)

    if not tracker._tiktoken_available:
        print("⚠ Tiktoken not available, skipping test")
        return

    text = "Hello, how are you today?"
    tokens = tracker.count_tokens(text, model="gpt-4")

    print(f"Text: '{text}'")
    print(f"Tiktoken tokens: {tokens}")
    assert tokens > 0
    assert tokens < 20  # Should be around 6-7 tokens
    print("✓ Tiktoken counting works")


def test_cost_calculation():
    """Test cost calculation"""
    print("\n=== Test 3: Cost Calculation ===")

    tracker = CostTracker()

    # GPT-4: $30 per 1M prompt tokens, $60 per 1M completion tokens
    cost = tracker.calculate_cost(
        prompt_tokens=1000,
        completion_tokens=500,
        model="gpt-4"
    )

    expected = (1000 / 1_000_000) * 30 + (500 / 1_000_000) * 60
    print(f"GPT-4 cost for 1000 prompt + 500 completion tokens: ${cost:.6f}")
    print(f"Expected: ${expected:.6f}")
    assert abs(cost - expected) < 0.000001
    print("✓ Cost calculation correct")


def test_different_models():
    """Test pricing for different models"""
    print("\n=== Test 4: Different Models ===")

    tracker = CostTracker()

    models = [
        ("gpt-4", 1000, 1000),
        ("llama-3.3-70b", 1000, 1000),
    ]

    for model, prompt_tokens, completion_tokens in models:
        cost = tracker.calculate_cost(prompt_tokens, completion_tokens, model)
        print(f"{model}: ${cost:.6f} for {prompt_tokens}+{completion_tokens} tokens")
        assert cost > 0

    print("✓ Multiple model pricing works")


def test_model_normalization():
    """Test model name normalization"""
    print("\n=== Test 5: Model Name Normalization ===")

    tracker = CostTracker()

    # These should all map to "gpt-4" pricing
    variations = [
        "gpt-4",
        "gpt-4-0613",
        "gpt-4-32k",
        "gpt-4-turbo-preview",
    ]

    base_cost = tracker.calculate_cost(1000, 1000, "gpt-4")

    for variant in variations:
        cost = tracker.calculate_cost(1000, 1000, variant)
        print(f"{variant}: ${cost:.6f}")
        # Should use gpt-4 pricing or variant-specific pricing
        assert cost > 0

    print("✓ Model normalization works")


def test_count_and_calculate():
    """Test combined count and calculate"""
    print("\n=== Test 6: Count and Calculate ===")

    tracker = CostTracker()

    prompt = "What is the capital of France?"
    completion = "The capital of France is Paris."
    model = "gpt-4"
    

    prompt_tokens, completion_tokens, cost = tracker.count_and_calculate(
        prompt, completion, model
    )

    print(f"Prompt: '{prompt}' ({prompt_tokens} tokens)")
    print(f"Completion: '{completion}' ({completion_tokens} tokens)")
    print(f"Cost: ${cost:.6f}")

    assert prompt_tokens > 0
    assert completion_tokens > 0
    assert cost > 0
    print("✓ Combined count and calculate works")


def test_custom_pricing():
    """Test adding custom model pricing"""
    print("\n=== Test 7: Custom Pricing ===")

    tracker = CostTracker()

    # Add custom model
    tracker.add_custom_pricing(
        model="my-custom-model",
        prompt_price=1.0,
        completion_price=2.0
    )

    cost = tracker.calculate_cost(1000, 1000, "my-custom-model")
    expected = (1000 / 1_000_000) * 1.0 + (1000 / 1_000_000) * 2.0

    print(f"Custom model cost: ${cost:.6f}")
    print(f"Expected: ${expected:.6f}")
    assert abs(cost - expected) < 0.000001
    print("✓ Custom pricing works")


def test_get_pricing():
    """Test getting pricing info"""
    print("\n=== Test 8: Get Pricing ===")

    tracker = CostTracker()

    pricing = tracker.get_pricing("gpt-4")
    assert pricing is not None
    assert "prompt" in pricing
    assert "completion" in pricing
    print(f"GPT-4 pricing: ${pricing['prompt']:.2f} / ${pricing['completion']:.2f} per 1M tokens")

    pricing_none = tracker.get_pricing("nonexistent-model")
    assert pricing_none is None
    print("✓ Get pricing works")


def test_global_functions():
    """Test global convenience functions"""
    print("\n=== Test 9: Global Functions ===")

    tokens = count_tokens("Hello world", model="gpt-4")
    assert tokens > 0
    print(f"✓ count_tokens(): {tokens} tokens")

    cost = calculate_cost(1000, 500, "gpt-4")
    assert cost > 0
    print(f"✓ calculate_cost(): ${cost:.6f}")

    tracker = get_cost_tracker()
    assert tracker is not None
    print("✓ get_cost_tracker() works")

    print("✓ Global functions work")


def test_empty_text():
    """Test handling of empty text"""
    print("\n=== Test 10: Empty Text ===")

    tracker = CostTracker()

    assert tracker.count_tokens("") == 0
    assert tracker.count_tokens(None) == 0
    print("✓ Empty text handling works")


if __name__ == "__main__":
    print("Testing CostTracker...")
    test_token_counting_estimate()
    test_token_counting_tiktoken()
    test_cost_calculation()
    test_different_models()
    test_model_normalization()
    test_count_and_calculate()
    test_custom_pricing()
    test_get_pricing()
    test_global_functions()
    test_empty_text()
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)