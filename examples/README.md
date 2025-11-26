# Practical Examples

##  Complete Applications

**Location:** `Practical Examples/`

** Start here if you want complete applications!**

Full-featured examples that solve real-world problems. Unlike the tutorial-style examples below, these are complete applications you can use as-is or adapt for your projects.

###  Multi-Agent Code Reviewer

A sophisticated code review system using 6 specialized AI agents to analyze Python code from multiple perspectives.

**What it does:**

- Analyzes code for style, security, optimization, readability, and complexity
- Provides detailed, line-specific feedback
- Generates structured reports with severity levels
- Offers actionable recommendations

**Key Features:**

- 6 specialized agents (Style, Security, Optimization, Readability, Complexity, Merger)
- Type-safe structured output with Pydantic
- Sequential routing pattern
- Custom file reading tools
- Comprehensive documentation and tests

**Quick Start:**

```bash
cd "Practical Examples/code-reviewer"
python main.py
```

**Perfect for:**

- Pre-commit hooks
- CI/CD quality gates
- Learning code review patterns
- Educational demonstrations

###  Autonomous Fiction Writer

Creative writing system that generates complete short stories (1500-3000 words) from a single-line prompt using 5 specialized AI agents.

**What it does:**

- Creates detailed characters with motivations and arcs
- Designs compelling plot structure with twists
- Builds immersive worlds and settings
- Crafts realistic dialogue
- Assembles everything into a polished story

**Key Features:**

- 5 creative writing specialists (Character, Plot, Worldbuilding, Dialogue, Assembler)
- Complete narrative generation
- Literary quality output
- Save stories to files
- Works with any creative premise

**Quick Start:**

```bash
cd "Practical Examples/fiction-writer"
python main.py
```

**Example Prompts:**

```bash
python main.py "A detective discovers their reflection has started solving crimes independently"
python main.py "In a world where memories can be bought, one owns a memory that never happened"
```

**Perfect for:**

- Creative writing practice
- Story structure education
- Game narrative generation
- Content brainstorming

###  Python Code Generator

An intelligent code generation system using 5 specialized AI agents that converts natural language descriptions into complete, tested Python code.

**What it does:**

- Analyzes programming tasks and breaks them into components
- Generates complete Python code with proper documentation
- Automatically tests code in a safe sandbox environment
- Fixes errors and optimizes the implementation
- Provides detailed explanations of how the code works

**Key Features:**

- 5 specialized agents (TaskAnalyzer, CodeGenerator, CodeTester, CodeFixer, CodeExplainer)
- Automatic code testing and error fixing
- Structured output with proper formatting
- Code explanation and complexity analysis
- Safe sandbox execution environment

**Quick Start:**

```bash
cd "Practical Examples/code-generator"
python main.py "Create a function to find prime numbers up to n"
```

**Example Tasks:**

```bash
python main.py "Create a binary search algorithm"
python main.py "Build a simple REST API with Flask"
python main.py "Implement a data structure for a stack"
```

**Perfect for:**

- Learning programming concepts
- Rapid prototyping
- Code generation automation
- Educational demonstrations

###  Knowledge Extractor

A comprehensive knowledge extraction system that analyzes documents and extracts structured information using multiple AI agents working in sequence.

**What it does:**

- Processes various document formats (PDF, text, web pages)
- Extracts key concepts, entities, and relationships
- Generates structured summaries and insights
- Creates knowledge graphs from unstructured data
- Provides contextual analysis and recommendations

**Key Features:**

- Multi-format document processing
- Entity recognition and relationship mapping
- Structured knowledge extraction
- Configurable extraction templates
- Export to multiple formats (JSON, CSV, markdown)

**Quick Start:**

```bash
cd "Practical Examples/knowledge-extractor"
python main.py document.pdf
```

**Perfect for:**

- Research and academic work
- Document analysis automation
- Knowledge base creation
- Information extraction pipelines

📖 **See:** `Practical Examples/README.md` for all practical examples