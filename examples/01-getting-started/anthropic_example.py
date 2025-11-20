from peargent import create_agent, create_tool, limit_steps
from peargent.models import anthropic, openai, groq, gemini
from peargent.tools import calculator


def test_anthropic_agent(input_text: str):
    """Example demonstrating Anthropic Claude model usage."""
    
    def fact_generator_tool(text: str) -> str:
        """Generate interesting facts about various topics."""
        return f"Did you know? {text} is connected to fascinating scientific discoveries that happened in the last decade."

    fact_generator = create_tool(
        name="fact_generator",
        description="Generates interesting facts about various topics",
        input_parameters={"text": str},
        call_function=fact_generator_tool,
    )

    # Create agent with Anthropic Claude model
    claude_agent = create_agent(
        name="claude_researcher",
        description="An AI researcher that generates insights using Claude.",
        persona="You are a knowledgeable researcher who loves to discover and share fascinating facts. Use the fact_generator tool to enhance your responses with interesting information.",
        model=anthropic("claude-3-5-sonnet-20241022"),
        tools=[fact_generator, calculator],
        stop=limit_steps(10),
    )
    
    result = claude_agent.run(input_text)
    return result


def compare_models_example():
    """Compare responses from different models."""
    
    prompt = "Explain the concept of quantum computing in simple terms."
    
    # Test with different models
    models = {
        "Claude (Anthropic)": anthropic("claude-3-5-sonnet-20241022"),
        "GPT-4o Mini (OpenAI)": openai("gpt-4o-mini"),
        "Gemini Flash": gemini("gemini-2.5-flash")
    }
    
    results = {}
    
    for model_name, model in models.items():
        try:
            agent = create_agent(
                name=f"explainer_{model_name.lower().replace(' ', '_')}",
                description="Explains complex concepts simply",
                persona="You are an expert at explaining complex topics in simple, easy-to-understand terms.",
                model=model,
                tools=[],
                stop=limit_steps(5),
            )
            
            result = agent.run(prompt)
            results[model_name] = result
            print(f"\n--- {model_name} ---")
            print(result)
            
        except Exception as e:
            results[model_name] = f"Error: {str(e)}"
            print(f"\n--- {model_name} ---")
            print(f"Error: {str(e)}")
    
    return results


if __name__ == "__main__":
    print("=== Anthropic Model Example ===")
    
    # Test basic Anthropic agent
    print("\n1. Testing Anthropic Claude Agent:")
    try:
        result = test_anthropic_agent("Tell me about artificial intelligence and use the fact generator to add some interesting information.")
        print("Claude Agent Result:")
        print(result)
    except Exception as e:
        print(f"Error with Claude: {e}")
        print("Make sure to set ANTHROPIC_API_KEY environment variable")
    
    print("\n" + "="*50)
    
    # Compare different models
    print("\n2. Comparing Different Models:")
    compare_models_example()