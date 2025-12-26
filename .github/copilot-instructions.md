# Peargent Python Agent Framework – Copilot Code Review Guidelines

## Purpose & Scope

These guidelines define how GitHub Copilot must review Pull Requests for the **Peargent Python Agent Framework**.

Peargent is an open-source (MIT) PyPI package targeting **Python 3.9–3.12**, focused on building AI agents with multi-LLM support.  
PR reviews must prioritize **correctness, API safety, and maintainability**, while keeping PRs **readable and low-noise**.

---

## Review Philosophy (IMPORTANT)

- Prefer **one single high-level summary comment** over multiple inline comments.
- Inline comments are **allowed ONLY** for:
  - Bugs
  - Security issues
  - Broken imports
  - Violations of **Critical Rules** listed below
- Avoid over-reviewing. If code is acceptable, say so.

**The goal is signal, not volume.**

---

## Mandatory Comment Formatting

### Collapsible Comments (REQUIRED)

- Any review comment longer than **3 lines** MUST be wrapped in a collapsible section.
- Multiple related issues MUST be grouped into **one** collapsible comment.

### Required Format

```markdown
<details>
<summary>⚠️ Issue: Missing type hints</summary>

The function `calculate_result` is missing type hints.

**Suggested fix:**
```python
def calculate_result(x: int, y: int) -> int:
    return x + y
````

</details>
```

---

## Do NOT Comment On (STRICT)

Copilot MUST NOT comment on:

* Formatting, spacing, or line length (handled by Black)
* Variable or function naming unless misleading or incorrect
* Suggestions to “add comments” or “improve readability”
* Minor refactors or stylistic preferences
* Suggestions already enforced by CI
* Hypothetical future improvements
* Personal preferences or alternative designs without bugs

---

## Blocking vs Non-Blocking Issues

### Blocking Issues (require changes)

* Failing tests
* Broken imports
* Violations of public API rules
* Missing type hints on **public** APIs
* Importing internal/private modules
* Breaking backward compatibility

### Non-Blocking Issues

* Optional refactors
* Performance ideas
* Code organization suggestions

👉 Non-blocking issues MUST appear **only in the summary**, not as inline comments.

---

## Critical Build Requirements

### Environment Setup (ALWAYS REQUIRED FIRST)

```bash
venv\Scripts\activate      # Windows
source venv/bin/activate  # Linux/macOS
pip install -e .
```

### Validation Commands

```bash
# Verify imports
python -c "from peargent import create_agent, create_tool, create_pool; print('OK')"

# Run tests (MUST use python -m pytest)
python -m pytest tests/

# Format & lint
black peargent/
flake8 peargent/

# Build & validate distribution
python -m build
twine check dist/*
```

### Known Issues (DO NOT FLAG)

* `pytest` must be run as `python -m pytest` (import errors otherwise)
* Tests requiring API keys may skip/fail without `.env`
* License deprecation warnings during build are non-blocking

---

## CI Pipeline Awareness

The PR CI workflow runs:

* Python 3.9, 3.10, 3.11, 3.12 test matrix
* Import validation
* Package build & distribution check

**Rules:**

* Do NOT restate CI failures unless additional context is required
* Assume contributors will read CI logs
* All versions must pass before merge

---

## Code Style Rules

* PEP 8 compliance (Black + Flake8)
* Type hints on all function signatures
* Docstrings for public APIs
* Conventional commits required:

  * `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`

---

## Import Rules (CRITICAL)

### ✅ Correct (Public API only)

```python
from peargent import create_agent, create_tool, create_pool
from peargent.models import groq, anthropic, openai
```

### ❌ Incorrect (NEVER allowed)

```python
from peargent._core.agent import Agent
from peargent._core.tool import Tool
```

Importing internal modules is a **blocking issue**.

---

## Example Patterns

### Tool Definition

```python
@create_tool(description="Calculate expression")
def calculator(expression: str) -> str:
    return str(eval(expression))
```

### Agent Creation

```python
agent = create_agent(
    name="assistant",
    persona="You are helpful.",
    model=groq("llama-3.3-70b-versatile"),
    tools=[calculator]
)
```

---

## Project Structure Awareness

Key files:

* `peargent/__init__.py` – Public API exports
* `peargent/_core/agent.py` – Core agent logic
* `peargent/_core/tool.py` – Tool system
* `peargent/models/*.py` – LLM providers
* `pyproject.toml` – Build configuration

Tests:

* `tests/test_tool.py`
* `tests/test_smoke.py`
* `tests/test_persona.py`
* `tests/test_anthropic.py`

---

## Common Review Scenarios

### Adding a New Tool

1. Add file in `peargent/tools/`
2. Export in `peargent/tools/__init__.py`
3. Register in `get_tool_by_name()` if built-in
4. Add tests to `tests/test_tool.py`
5. Add example in `examples/02-tools/`

### Adding a New Model Provider

1. Create `peargent/models/newprovider.py` following `base.py`
2. Export from `peargent/models/__init__.py`
3. Add example in `examples/01-getting-started/`
4. Update `README.md`

---

## Review Checklist (Before Approval)

* [ ] Virtual environment activated
* [ ] `pip install -e .` run
* [ ] `black peargent/`
* [ ] `flake8 peargent/`
* [ ] `python -m pytest tests/`
* [ ] Imports verified
* [ ] `python -m build && twine check dist/*`
* [ ] Conventional commit message
* [ ] Type hints added
* [ ] Public APIs documented

---

## Final Instruction to Reviewer (MANDATORY)

If **no blocking issues** are found:

* Respond with **one short approval summary**
* Do NOT leave inline comments
* Do NOT suggest optional improvements

Silence is acceptable when the PR meets all requirements.