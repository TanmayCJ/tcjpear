# Multi-Agent Code Reviewer

Analyzes Python code using 6 specialized AI agents: Style, Security, Optimization, Readability, Complexity, and Report Merger.

## Quick Start

```bash
# Install
pip install peargent

# Set API key in .env
GROQ_API_KEY=your_key_here

# Run
python main.py                    # Reviews sample file
python main.py path/to/file.py   # Reviews your file
```

## Output

- Overall quality score (1-10)
- Category scores (Style, Security, Optimization, Readability, Complexity)
- Issues by severity (Critical, High, Medium, Low, Info)
- Line-specific recommendations
- Executive summary

## Customize

**Change model:**
```python
from peargent.models import openai
agent = create_agent(..., model=openai("gpt-4o"))
```

**Add more agents:**
Edit `code_reviewer.py` → `create_review_agents()` → Add your agent → Update router sequence

**Modify criteria:**
Edit agent personas in `create_review_agents()`
