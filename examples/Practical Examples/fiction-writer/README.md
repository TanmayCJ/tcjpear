# Autonomous Fiction Writer

Generates complete short stories (1500-3000 words) from a single-line prompt using 5 AI agents: Character, Plot, Worldbuilding, Dialogue, and Story Assembler.

## Quick Start

```bash
# Install
pip install peargent

# Set API key in .env (because it's free)
GROQ_API_KEY=your_key_here

# Run
python main.py                                    # Uses default prompt
python main.py "your story premise here"         # Uses your prompt
```

## Example Prompts

```bash
python main.py "A detective discovers their reflection has started solving crimes independently"

python main.py "In a world where memories can be bought and sold, one owns a memory that never happened"

python main.py "A time traveler realizes they're stuck in a loop, but each iteration they become a different person"
```

## Output

- Complete 1500-3000 word short story
- Professional formatting
- Characters with depth
- Full plot structure
- Vivid world details
- Realistic dialogue
- Option to save to file

## Customize

**Adjust length:**
Edit `fiction_writer.py` → StoryAssembler persona → Change word count

**Change style:**
Modify StoryAssembler persona → Add style instructions (noir, literary, YA, etc.)

**Use different model:**
```python
from peargent.models import anthropic
agent = create_agent(..., model=anthropic("claude-3-5-sonnet-20241022"))
```
