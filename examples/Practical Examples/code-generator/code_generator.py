"""
Python Code Generator & Explainer

Generates Python code from natural language, tests it, fixes errors, and explains it.

Architecture:
- Task Analyzer: Breaks task into components
- Code Generator: Writes initial code
- Code Tester: Tests in sandbox and reports errors
- Code Fixer: Fixes errors automatically
- Code Explainer: Explains the final code

Usage:
    python code_generator.py "Create a function to find prime numbers up to n"
"""

import sys
import io
import contextlib
from pydantic import BaseModel, Field
from typing import List, Optional

from peargent import create_agent, create_pool, create_tool, RouterResult, HistoryConfig
from peargent.storage import InMemory
from peargent.models import groq


# ============================================================================
# Pydantic Models for Structured Output
# ============================================================================

class TaskComponent(BaseModel):
    """A component of the task"""
    name: str = Field(description="Component name")
    description: str = Field(description="What this component does")
    requirements: str = Field(description="Technical requirements")


class TaskAnalysis(BaseModel):
    """Output from Task Analyzer Agent"""
    agent_name: str = Field(description="Agent name", default="TaskAnalyzer")
    task_summary: str = Field(description="Summary of what needs to be built")
    components: List[TaskComponent] = Field(description="Task broken into components")
    approach: str = Field(description="Recommended approach")


class GeneratedCode(BaseModel):
    """Output from Code Generator Agent"""
    agent_name: str = Field(description="Agent name", default="CodeGenerator")
    code: str = Field(description="Complete Python code")
    functions: List[str] = Field(description="List of functions/classes created")
    dependencies: List[str] = Field(description="Required imports or libraries")


class TestResult(BaseModel):
    """Output from Code Tester Agent"""
    agent_name: str = Field(description="Agent name", default="CodeTester")
    passed: bool = Field(description="Whether code runs without errors")
    error_message: Optional[str] = Field(description="Error message if failed")
    test_output: str = Field(description="Output from running the code")


class FixedCode(BaseModel):
    """Output from Code Fixer Agent"""
    agent_name: str = Field(description="Agent name", default="CodeFixer")
    code: str = Field(description="Fixed Python code")
    changes_made: List[str] = Field(description="List of fixes applied")
    fixed: bool = Field(description="Whether errors were fixed")


class CodeExplanation(BaseModel):
    """Output from Code Explainer Agent"""
    agent_name: str = Field(description="Agent name", default="CodeExplainer")
    overview: str = Field(description="High-level explanation")
    step_by_step: List[str] = Field(description="Step-by-step breakdown")
    usage_example: str = Field(description="How to use the code")
    complexity: str = Field(description="Time/space complexity analysis")


# ============================================================================
# Tools: Code Testing
# ============================================================================

def test_python_code(code: str) -> str:
    """
    Test Python code in a safe sandbox.
    Returns execution result or error.
    """
    try:
        # Create output capture
        output = io.StringIO()

        # Execute code in isolated namespace
        namespace = {}

        with contextlib.redirect_stdout(output):
            exec(code, namespace)

        result = output.getvalue()

        if result:
            return f"SUCCESS: Code executed without errors.\n\nOutput:\n{result}"
        else:
            return "SUCCESS: Code executed without errors. (No output produced)"

    except SyntaxError as e:
        return f"SYNTAX ERROR on line {e.lineno}: {e.msg}\n{e.text}"
    except Exception as e:
        return f"RUNTIME ERROR: {type(e).__name__}: {str(e)}"


# Create tool
test_code_tool = create_tool(
    name="test_code",
    description="Test Python code in a safe sandbox and return results",
    input_parameters={"code": str},
    call_function=test_python_code
)


# ============================================================================
# Create Code Generation Agents
# ============================================================================

def create_code_agents():
    """Create all code generation agents"""

    # Task Analyzer - Breaks down the task
    analyzer_agent = create_agent(
        name="TaskAnalyzer",
        description="Analyzes task and breaks it into components",
        persona="""You are a software architect who analyzes programming tasks.

Your job is to break down a natural language task into clear components.

Analyze:
- What needs to be built
- What components are needed
- Technical requirements
- Best approach

Be specific and technical.

Return ONLY valid JSON matching the TaskAnalysis schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=TaskAnalysis
    )

    # Code Generator - Writes the code
    generator_agent = create_agent(
        name="CodeGenerator",
        description="Generates Python code based on task analysis",
        persona="""You are an expert Python programmer.

Based on the task analysis, write complete, working Python code.

Requirements:
- Write clean, readable code
- Include docstrings
- Add example usage at the end
- Use descriptive variable names
- Follow PEP 8

IMPORTANT:
1. Include a simple test/example at the end that demonstrates the code
2. Wrap test code in: if __name__ == "__main__":
3. Make sure the code actually RUNS and produces OUTPUT

Return ONLY valid JSON matching the GeneratedCode schema.

In the 'code' field, put the COMPLETE Python code as a string.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=GeneratedCode
    )

    # Code Tester - Tests the code
    tester_agent = create_agent(
        name="CodeTester",
        description="Tests generated code in a sandbox",
        persona="""You are a QA engineer who tests code.

Use the test_code tool to run the code and check for errors.

Report:
- Whether it passed or failed
- Any error messages
- Output produced

Return ONLY valid JSON matching the TestResult schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[test_code_tool],
        output_schema=TestResult
    )

    # Code Fixer - Fixes errors
    fixer_agent = create_agent(
        name="CodeFixer",
        description="Fixes errors in code automatically",
        persona="""You are a debugging expert who fixes code errors.

You will receive code and error messages from the tester.

If there are errors:
1. Analyze the error
2. Fix the code
3. List what you changed

If no errors, return the original code unchanged.

Return ONLY valid JSON matching the FixedCode schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=FixedCode
    )

    # Code Explainer - Explains the code
    explainer_agent = create_agent(
        name="CodeExplainer",
        description="Explains the final code in detail",
        persona="""You are a programming teacher who explains code clearly.

Provide:
1. High-level overview (what it does)
2. Step-by-step breakdown (how it works)
3. Usage example (how to use it)
4. Complexity analysis (performance)

Make it educational and easy to understand.

Return ONLY valid JSON matching the CodeExplanation schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=CodeExplanation
    )

    return [
        analyzer_agent,
        generator_agent,
        tester_agent,
        fixer_agent,
        explainer_agent
    ]


# ============================================================================
# Custom Sequential Router
# ============================================================================

def code_generator_router(state, call_count, last_result):
    """Sequential router for code generation"""
    agent_sequence = [
        "TaskAnalyzer",
        "CodeGenerator",
        "CodeTester",
        "CodeFixer",
        "CodeExplainer"
    ]

    if call_count >= len(agent_sequence):
        return RouterResult(None)

    return RouterResult(agent_sequence[call_count])


# ============================================================================
# Main Generation Function
# ============================================================================

def generate_code(task: str) -> tuple:
    """Generate code from natural language task"""

    print(f"\n{'='*80}")
    print(f"PYTHON CODE GENERATOR")
    print(f"{'='*80}\n")
    print(f"Task: {task}\n")

    # Create agents
    agents = create_code_agents()

    # Create pool
    pool = create_pool(
        agents=agents,
        router=code_generator_router,
        max_iter=5
    )

    # Generate code
    print("Starting generation...\n")
    print("1. TaskAnalyzer: Breaking down task...")
    print("2. CodeGenerator: Writing code...")
    print("3. CodeTester: Testing in sandbox...")
    print("4. CodeFixer: Fixing any errors...")
    print("5. CodeExplainer: Creating explanation...\n")

    result = pool.run(f"Generate Python code for: {task}")

    print(f"\n{'='*80}")
    print("GENERATION COMPLETE")
    print(f"{'='*80}\n")

    # Extract structured outputs from pool history
    code = None
    explanation = None
    test_result = None
    all_outputs = []

    # Parse agent outputs from history
    for message in pool.state.history:
        if message.get('role') == 'assistant':
            agent_name = message.get('agent')
            content = message.get('content')
            
            all_outputs.append({
                'agent': agent_name,
                'content': content
            })
            
            # Try to parse structured output based on agent
            try:
                if agent_name == 'CodeGenerator':
                    # Extract code from GeneratedCode model string representation
                    if 'code=' in content:
                        import re
                        
                        # The string contains the pydantic model representation
                        # Look for code='...' with proper handling of escaped quotes
                        code_match = re.search(r"code='(.*?)'(?:\s+[a-zA-Z_]+=|$)", content, re.DOTALL)
                        
                        if code_match:
                            code = code_match.group(1)
                            # Unescape the string properly
                            code = code.replace('\\n', '\n').replace('\\t', '\t')
                            code = code.replace("\\'", "'").replace('\\"', '"')
                            print(f"✓ Successfully extracted {len(code.split(chr(10)))} lines of code")
                
                elif agent_name == 'CodeTester':
                    # Extract test result
                    if 'passed=' in content:
                        passed = 'passed=True' in content
                        test_result = {
                            'passed': passed,
                            'agent': agent_name,
                            'content': content
                        }
                
                elif agent_name == 'CodeExplainer':
                    # Keep the explanation as is
                    explanation = content
                    
            except Exception as e:
                print(f"Warning: Could not parse output from {agent_name}: {e}")
                continue

    return code, explanation, test_result, all_outputs


# ============================================================================
# Display Functions
# ============================================================================

def display_result(code, explanation, test_result, all_outputs=None):
    """Display the generated code and explanation"""

    print(f"\n{'='*80}")
    print(f"GENERATED CODE")
    print(f"{'='*80}\n")

    if code:
        print("```python")
        print(code)
        print("```")
        print(f"\n✓ Code extracted successfully!")
    else:
        print("Code extraction failed.")
        
        # Show debugging info if code extraction failed
        if all_outputs:
            print(f"\n{'='*80}")
            print(f"DEBUG: ALL AGENT OUTPUTS")
            print(f"{'='*80}\n")

            for output in all_outputs:
                agent = output.get('agent')
                content = str(output.get('content'))

                print(f"\n--- {agent} ---")
                print(content[:800])  # Show more chars
                if len(content) > 800:
                    print(f"\n... (truncated, {len(content)} total chars)")
                print()

    print(f"\n{'='*80}")
    print(f"TEST RESULTS")
    print(f"{'='*80}\n")

    if test_result:
        if isinstance(test_result, dict):
            if test_result.get("passed"):
                print(" Code tested successfully!")
                # Try to extract test output from content
                content = test_result.get('content', '')
                if 'test_output=' in content:
                    import re
                    output_match = re.search(r"test_output='([^']*(?:'[^']*)*)'|test_output=\"([^\"]*(?:\"[^\"]*)*)\"", content)
                    if output_match:
                        test_output = output_match.group(1) or output_match.group(2)
                        test_output = test_output.replace('\\n', '\n')
                        print(f"\n Test Output:")
                        print(test_output)
            else:
                print("⚠️ Code had errors (but may have been fixed)")
                if 'error_message=' in test_result.get('content', ''):
                    import re
                    error_match = re.search(r"error_message='([^']*(?:'[^']*)*)'|error_message=\"([^\"]*(?:\"[^\"]*)*)\"", test_result['content'])
                    if error_match:
                        error_msg = error_match.group(1) or error_match.group(2)
                        print(f"Error: {error_msg}")
    else:
        print(" Test results not available.")

    print(f"\n{'='*80}")
    print(f"EXPLANATION")
    print(f"{'='*80}\n")

    if explanation and isinstance(explanation, str):
        # Try to parse explanation from string
        if 'overview=' in explanation:
            import re
            
            # Extract overview
            overview_match = re.search(r"overview='([^']*(?:'[^']*)*)'|overview=\"([^\"]*(?:\"[^\"]*)*)\"", explanation)
            if overview_match:
                overview = overview_match.group(1) or overview_match.group(2)
                overview = overview.replace('\\n', '\n')
                print(f"**Overview:**\n{overview}\n")
            
            # Extract usage example
            usage_match = re.search(r"usage_example='([^']*(?:'[^']*)*)'|usage_example=\"([^\"]*(?:\"[^\"]*)*)\"", explanation)
            if usage_match:
                usage = usage_match.group(1) or usage_match.group(2)
                usage = usage.replace('\\n', '\n')
                print(f"**Usage Example:**\n{usage}\n")
            
            # Extract complexity
            complexity_match = re.search(r"complexity='([^']*(?:'[^']*)*)'|complexity=\"([^\"]*(?:\"[^\"]*)*)\"", explanation)
            if complexity_match:
                complexity = complexity_match.group(1) or complexity_match.group(2)
                complexity = complexity.replace('\\n', '\n')
                print(f" **Complexity:**\n{complexity}")
        else:
            print(explanation)
    else:
        print(" Explanation not available.")


def save_code(code: str, filename: str = "generated_code.py"):
    """Save generated code to a file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(code)
    print(f"✓ Code saved to: {filename}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python code_generator.py \"<task description>\"")
        print("\nExample:")
        print('  python code_generator.py "Create a function to find prime numbers up to n"')
        sys.exit(1)

    task = sys.argv[1]

    try:
        # Generate code
        code, explanation, test_result, all_outputs = generate_code(task)

        # Display results
        display_result(code, explanation, test_result, all_outputs)

        # Ask to save
        if code:
            print("\n" + "="*80)
            save_choice = input("Save generated code to file? (y/n): ").strip().lower()
            if save_choice == 'y':
                filename = input("Filename (default: generated_code.py): ").strip() or "generated_code.py"
                save_code(code, filename)

    except KeyboardInterrupt:
        print("\n\nGeneration cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
