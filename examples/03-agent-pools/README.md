# Agent Pools Examples

This directory contains examples demonstrating multi-agent orchestration using Peargent's Pool system.

## Examples

### 1. Basic Pool (`basic_pool.py`)
A simple example showing two agents working together:
- **Search agent** - Gathers facts using tools
- **Summary agent** - Formats and presents information

**Key concepts:**
- Creating a pool with multiple agents
- Default round-robin routing
- Agent collaboration

**Run:**
```bash
python basic_pool.py
```

---

### 2. Multi-Agent Code Reviewer (`code_reviewer.py`)
A sophisticated code review system with 6 specialized agents analyzing Python code from different perspectives.

**Agents:**
1. **StyleReviewer** - PEP 8 compliance, formatting, naming conventions
2. **SecurityReviewer** - Security vulnerabilities (SQL injection, eval, hardcoded secrets)
3. **OptimizationReviewer** - Performance issues, algorithm efficiency
4. **ReadabilityReviewer** - Code clarity, documentation, naming
5. **ComplexityReviewer** - Cyclomatic complexity, nesting, DRY violations
6. **ReportMerger** - Synthesizes all reviews into structured report

**Key concepts:**
- Custom sequential router
- Structured output with Pydantic models
- Tool usage (file reading)
- Multi-agent collaboration
- Hierarchical agent workflows

**Run:**
```bash
# Review any Python file
python code_reviewer.py path/to/your/file.py

# Review the sample file with intentional issues
python code_reviewer.py sample_code_to_review.py

# Or use the convenience scripts
./run_code_review_example.sh   # Linux/Mac
run_code_review_example.bat    # Windows
```

**Output:**
The code reviewer produces a comprehensive report with:
- Overall quality score (1-10)
- Category scores (Style, Security, Optimization, Readability, Complexity)
- Detailed issue list with severity levels (Critical, High, Medium, Low, Info)
- Line-specific recommendations
- Top actionable suggestions
- Executive summary

**See:** `code_reviewer_README.md` for detailed documentation

---

## Pool Concepts

### What is a Pool?
A Pool orchestrates multiple agents working together on a task. It manages:
- **Routing** - Deciding which agent acts next
- **State** - Sharing conversation history across agents
- **Execution** - Running agents in sequence or based on logic
- **Output** - Combining results from multiple agents

### Router Types

1. **Round-robin (default)**
   ```python
   pool = create_pool(agents=[agent1, agent2])
   # Automatically routes: agent1 → agent2 → stop
   ```

2. **Custom function**
   ```python
   def my_router(state, call_count, last_result):
       if call_count == 0:
           return RouterResult("agent1")
       elif some_condition:
           return RouterResult("agent2")
       return RouterResult(None)  # Stop

   pool = create_pool(agents=[agent1, agent2], router=my_router)
   ```

3. **RoutingAgent (LLM-based)**
   ```python
   router_agent = create_routing_agent(
       name="Router",
       model=groq("llama-3.3-70b-versatile"),
       persona="You decide which agent should act next...",
       agents=[agent1, agent2]
   )

   pool = create_pool(agents=[agent1, agent2], router=router_agent)
   ```

### When to Use Pools

Use pools when:
- ✅ Multiple specialized agents work on different aspects of a problem
- ✅ You need sequential processing (analysis → synthesis)
- ✅ Agents need to share context and build on each other's work
- ✅ You want modular, reusable agent components

Don't use pools when:
- ❌ A single agent can handle the entire task
- ❌ Agents don't need to communicate or share state
- ❌ You need true parallel execution (use async instead)

## Best Practices

1. **Keep agents focused** - Each agent should have a clear, specific role
2. **Use structured output** - Pydantic models ensure type safety and consistency
3. **Design clear routing logic** - Make sure the flow is predictable and maintainable
4. **Share context efficiently** - Use State to pass information between agents
5. **Set appropriate max_iter** - Prevent infinite loops with reasonable iteration limits

## More Examples

For more advanced routing examples, see:
- `examples/09-routing/` - Custom routers, conditional routing, state-based routing
- `examples/07-structured-output/` - Using Pydantic for type-safe outputs
- `examples/02-tools/` - Creating custom tools for agents

## Requirements

All examples require:
- Peargent framework installed
- API keys configured in `.env`:
  - `GROQ_API_KEY` (for Groq/Llama models)
  - Or `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc. depending on model choice
