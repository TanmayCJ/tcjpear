# Knowledge Extractor

Processes folders containing .txt, .md, .py files and builds a comprehensive knowledge base using 5 AI agents.

## Quick Start

```bash
# Install
pip install peargent

# Set API key in .env
GROQ_API_KEY=your_key_here

# Run
python main.py                    # Analyzes sample_docs folder
python main.py path/to/folder    # Analyzes your folder
```

## What It Creates

1. **File Summaries** - Key topics and entities from each file
2. **Knowledge Map** - Overall structure and themes
3. **Q&A System** - 8-12 questions with answers
4. **Glossary** - Definitions of important terms
5. **Cross-References** - Connections between files

## Example Output

```
KNOWLEDGE BASE REPORT
================================================================================

File Summaries:
- intro.md: Overview of agent system components
- setup.txt: Installation and configuration instructions
- agents.py: Core agent class implementations
- architecture.md: System design and data flow

Knowledge Map:
Main themes: Agent Architecture, System Configuration, Data Flow
Structure: Multi-agent system with router, memory, and agents

Q&A Pairs:
Q: What are the three main components?
A: Agent System, Router, and Memory
Source: intro.md, architecture.md

Glossary:
- Router: Component that selects appropriate agent for input
- Memory: Stores conversation history with configurable size
- BaseAgent: Parent class for all agent implementations

Cross-References:
- intro.md ↔ architecture.md: Both describe system components
- setup.txt ↔ agents.py: Setup references agent configuration
```

## Customize

**Adjust number of Q&A pairs:**
Edit `knowledge_extractor.py` → QAGenerator persona → Change "8-12" to your desired count

**Add more agents:**
Create new agent in `create_extraction_agents()` → Update router sequence

**Change file types:**
Edit `list_files_in_folder()` and `read_all_files_in_folder()` → Modify `extensions` list
