# Python Code Generator & Explainer

Generates Python code from natural language, tests it in a sandbox, fixes errors automatically, and explains it using 5 AI agents.

## Quick Start

```bash
# Install
pip install peargent

# Set API key in .env
GROQ_API_KEY=your_key_here

# Run
python main.py                                          # Uses default task
python main.py "Create a function to sort a list"      # Uses your task
```

## Example Tasks

```bash
python main.py "Create a function to find prime numbers up to n"

python main.py "Write a binary search function"

python main.py "Create a class for a simple queue data structure"

python main.py "Generate fibonacci sequence using recursion"
```

## What It Does

1. **Analyzes Task** - Breaks into components and requirements
2. **Generates Code** - Writes clean Python with docstrings
3. **Tests Code** - Runs in safe sandbox to catch errors
4. **Fixes Errors** - Automatically debugs and corrects issues
5. **Explains Code** - Provides step-by-step explanation and usage

## Output Example

```python
# Generated code
def is_prime(n):
    """Check if a number is prime"""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def find_primes(n):
    """Find all prime numbers up to n"""
    return [num for num in range(2, n+1) if is_prime(num)]

# Test
if __name__ == "__main__":
    print(find_primes(20))
```

**Explanation:**
- Overview: Two functions for prime number operations
- Step-by-step: Checks divisibility, uses optimization
- Usage: Call find_primes(n) with any number
- Complexity: O(n√n) time complexity

## Customize

**Change code style:**
Edit `code_generator.py` → CodeGenerator persona → Add style requirements (type hints, specific patterns, etc.)

**Add more test cases:**
Modify CodeGenerator to include multiple test scenarios

**Adjust sandbox safety:**
Edit `test_python_code()` function to add restrictions or timeouts
