"""
Test file for Anthropic model implementation.
Run this to verify the Anthropic model is working correctly.
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import peargent
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from peargent.models.anthropic import AnthropicModel


def test_anthropic_model():
    """Test basic functionality of the Anthropic model."""
    
    # Check if API key is available
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not found in environment variables.")
        print("   Set it with: set ANTHROPIC_API_KEY=your_api_key_here")
        return False
    
    try:
        # Test model initialization
        print("🧪 Testing Anthropic model initialization...")
        model = AnthropicModel(
            model_name="claude-3-5-sonnet-20241022",
            parameters={
                "temperature": 0.3,
                "max_tokens": 100,
                "system_prompt": "You are a helpful assistant. Keep responses brief."
            }
        )
        print("✅ Model initialized successfully")
        
        # Test basic generation
        print("\n🧪 Testing text generation...")
        prompt = "What is 2+2? Answer briefly."
        response = model.generate(prompt)
        
        if response and len(response.strip()) > 0:
            print("✅ Text generation successful")
            print(f"📝 Response: {response}")
        else:
            print("❌ Text generation failed - empty response")
            return False
        
        # Test streaming (if supported)
        print("\n🧪 Testing streaming...")
        stream_prompt = "Count from 1 to 3, one number per line."
        stream_chunks = list(model.stream(stream_prompt))
        
        if stream_chunks:
            print("✅ Streaming successful")
            print(f"📝 Stream chunks: {len(stream_chunks)}")
            print(f"📝 Combined response: {''.join(stream_chunks)}")
        else:
            print("⚠️  Streaming returned no chunks (might not be supported)")
        
        print("\n🎉 All tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        return False


def test_model_parameters():
    """Test different model parameters."""
    
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        print("⚠️  ANTHROPIC_API_KEY not found. Skipping parameter tests.")
        return
    
    print("\n🧪 Testing different model parameters...")
    
    # Test different temperature values
    temperatures = [0.0, 0.5, 1.0]
    prompt = "Write a creative one-sentence story."
    
    for temp in temperatures:
        try:
            model = AnthropicModel(
                parameters={"temperature": temp, "max_tokens": 50}
            )
            response = model.generate(prompt)
            print(f"🌡️  Temperature {temp}: {response[:50]}...")
        except Exception as e:
            print(f"❌ Temperature {temp} failed: {e}")


if __name__ == "__main__":
    print("🚀 Testing Anthropic Model Implementation")
    print("=" * 50)
    
    success = test_anthropic_model()
    
    if success:
        test_model_parameters()
    
    print("\n" + "=" * 50)
    print("🏁 Test completed!")