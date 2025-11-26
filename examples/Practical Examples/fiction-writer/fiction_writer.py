"""
Autonomous Fiction Writer

A multi-agent system that generates complete short stories from a single-line prompt.

Architecture:
- Character Agent: Creates detailed character profiles
- Plot Agent: Designs story structure and plot points
- Worldbuilding Agent: Develops setting and atmosphere
- Dialogue Agent: Crafts realistic conversations
- Story Assembler Agent: Weaves everything into a cohesive narrative

Usage:
    python fiction_writer.py "A detective discovers their reflection has started solving crimes independently"
"""

import sys
from pydantic import BaseModel, Field
from typing import List

from peargent import create_agent, create_pool, RouterResult
from peargent.models import groq


# ============================================================================
# Pydantic Models for Structured Output
# ============================================================================

class Character(BaseModel):
    """A character in the story"""
    name: str = Field(description="Character's name")
    role: str = Field(description="Role in story: protagonist, antagonist, supporting, minor")
    age: int = Field(description="Character's age", ge=1, le=150)
    personality: str = Field(description="Key personality traits")
    background: str = Field(description="Relevant backstory")
    motivation: str = Field(description="What drives this character")
    appearance: str = Field(description="Physical description")


class CharacterDevelopment(BaseModel):
    """Output from Character Agent"""
    agent_name: str = Field(description="Agent name", default="CharacterAgent")
    characters: List[Character] = Field(description="List of story characters")
    relationship_dynamics: str = Field(description="How characters interact and relate")
    character_arcs: str = Field(description="How characters will change/develop")


class PlotStructure(BaseModel):
    """Output from Plot Agent"""
    agent_name: str = Field(description="Agent name", default="PlotAgent")
    genre: str = Field(description="Story genre")
    theme: str = Field(description="Central theme or message")
    hook: str = Field(description="Opening hook to grab reader attention")
    inciting_incident: str = Field(description="Event that starts the story")
    rising_action: List[str] = Field(description="Key plot points building tension")
    climax: str = Field(description="Peak of tension/conflict")
    falling_action: str = Field(description="Events after climax")
    resolution: str = Field(description="How the story concludes")
    plot_twists: List[str] = Field(description="Unexpected turns in the story")


class WorldBuilding(BaseModel):
    """Output from Worldbuilding Agent"""
    agent_name: str = Field(description="Agent name", default="WorldbuildingAgent")
    setting_time: str = Field(description="When the story takes place")
    setting_place: str = Field(description="Where the story takes place")
    atmosphere: str = Field(description="Overall mood and tone")
    key_locations: List[str] = Field(description="Important places in the story")
    world_rules: str = Field(description="How this world works (physics, magic, society, etc.)")
    sensory_details: str = Field(description="Sights, sounds, smells, textures to make world vivid")


class DialogueElement(BaseModel):
    """A single dialogue exchange"""
    character: str = Field(description="Character speaking")
    line: str = Field(description="What they say")
    subtext: str = Field(description="Hidden meaning or emotion")


class DialogueDevelopment(BaseModel):
    """Output from Dialogue Agent"""
    agent_name: str = Field(description="Agent name", default="DialogueAgent")
    key_conversations: List[DialogueElement] = Field(description="Important dialogue moments")
    character_voices: str = Field(description="How each character speaks differently")
    dialogue_purpose: str = Field(description="How dialogue reveals character and advances plot")


class CompleteStory(BaseModel):
    """Final assembled story"""
    title: str = Field(description="Story title")
    genre: str = Field(description="Story genre")
    word_count: int = Field(description="Approximate word count", ge=0)

    full_text: str = Field(description="Complete story text, professionally formatted")

    # Metadata
    characters_featured: List[str] = Field(description="Names of characters in story")
    key_themes: List[str] = Field(description="Major themes explored")
    story_summary: str = Field(description="One-paragraph summary")


# ============================================================================
# Create Specialized Writing Agents
# ============================================================================

def create_writing_agents():
    """Create all specialized fiction writing agents"""

    # Character Agent - Creates compelling characters
    character_agent = create_agent(
        name="CharacterAgent",
        description="Creates detailed, compelling characters with depth and motivation",
        persona="""You are a master character designer for fiction writing.

Your job is to create vivid, memorable characters based on the story premise.

For each story, create:
- A protagonist (main character) with clear goals and flaws
- An antagonist or source of conflict
- 1-3 supporting characters who add depth
- Character relationships and dynamics
- Character arcs showing how they'll change

Make characters:
- Three-dimensional with strengths AND weaknesses
- Believable with realistic motivations
- Distinct from each other (different voices, goals, personalities)
- Relevant to the story premise

Return ONLY valid JSON matching the CharacterDevelopment schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=CharacterDevelopment
    )

    # Plot Agent - Designs story structure
    plot_agent = create_agent(
        name="PlotAgent",
        description="Designs compelling plot structure with clear beginning, middle, and end",
        persona="""You are an expert story architect and plot designer.

Your job is to create a well-structured, engaging plot from the premise.

Design a plot with:
- Clear three-act structure (setup, confrontation, resolution)
- Inciting incident that launches the story
- Rising tension through escalating conflicts
- A powerful climax that resolves the central conflict
- Satisfying resolution
- At least one surprising twist

The plot should:
- Build naturally from the premise
- Create emotional investment
- Feature cause-and-effect progression (not random events)
- Include both external conflicts (events) and internal conflicts (character growth)

Return ONLY valid JSON matching the PlotStructure schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=PlotStructure
    )

    # Worldbuilding Agent - Creates setting and atmosphere
    worldbuilding_agent = create_agent(
        name="WorldbuildingAgent",
        description="Develops rich, immersive world setting and atmosphere",
        persona="""You are a worldbuilding expert who creates vivid, believable settings.

Your job is to establish the world where the story takes place.

Create:
- Specific time and place (when/where)
- Atmospheric details that evoke mood
- Key locations where important scenes occur
- Rules of how this world works (even if realistic, what defines it?)
- Sensory details (sights, sounds, smells, textures)

Make the world:
- Consistent and believable
- Atmospheric and immersive
- Relevant to the story (not just background)
- Detailed enough to feel real, but focused on what matters

Return ONLY valid JSON matching the WorldBuilding schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=WorldBuilding
    )

    # Dialogue Agent - Crafts character voices
    dialogue_agent = create_agent(
        name="DialogueAgent",
        description="Creates realistic, character-driven dialogue",
        persona="""You are a dialogue specialist who writes how people really talk.

Your job is to create key dialogue moments for the story.

Design dialogue that:
- Reveals character personality through how they speak
- Advances the plot (every line has purpose)
- Includes subtext (what's unsaid is as important as what's said)
- Sounds natural and authentic to each character
- Creates tension, humor, or emotion

Key conversations to develop:
- First major interaction between protagonist and antagonist
- A revelation or confession scene
- The confrontation/climax dialogue
- Any other pivotal conversations

Make each character sound distinct - different vocabulary, sentence structure, speaking patterns.

Return ONLY valid JSON matching the DialogueDevelopment schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=DialogueDevelopment
    )

    return [
        character_agent,
        plot_agent,
        worldbuilding_agent,
        dialogue_agent
    ]


# ============================================================================
# Create Story Assembler Agent
# ============================================================================

def create_assembler_agent():
    """Create the agent that assembles everything into a complete story"""

    assembler_agent = create_agent(
        name="StoryAssembler",
        description="Weaves all elements into a complete, polished short story",
        persona="""You are a master storyteller who assembles complete, publishable stories.

You will receive detailed elements from specialist agents:
1. CharacterAgent - Character profiles, relationships, arcs
2. PlotAgent - Story structure, plot points, twists
3. WorldbuildingAgent - Setting, atmosphere, world details
4. DialogueAgent - Key conversations and character voices

Your job is to weave ALL these elements into a complete, cohesive short story (1500-3000 words).

CRITICAL REQUIREMENTS:
- Use EVERY character created (don't ignore supporting characters)
- Follow the plot structure from beginning to end
- Incorporate the world details to make setting vivid
- Use the dialogue moments at appropriate points
- Write in a polished, literary style
- Show, don't tell (use scenes, not summary)
- Include vivid sensory details
- Maintain consistent tone and atmosphere
- Create a satisfying narrative arc

Format:
- Start with a compelling hook
- Use proper paragraphing and formatting
- Include dialogue formatted correctly with quote marks
- Build to the climax
- End with a resonant conclusion

Write a complete story that feels like it could be published in a literary magazine.

Return ONLY valid JSON matching the CompleteStory schema.
Put the entire story in the 'full_text' field.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=CompleteStory
    )

    return assembler_agent


# ============================================================================
# Custom Sequential Router
# ============================================================================

def fiction_writer_router(state, call_count, last_result):
    """
    Sequential router that runs each agent in order.

    Order:
    0. CharacterAgent
    1. PlotAgent
    2. WorldbuildingAgent
    3. DialogueAgent
    4. StoryAssembler (final)
    """
    agent_sequence = [
        "CharacterAgent",
        "PlotAgent",
        "WorldbuildingAgent",
        "DialogueAgent",
        "StoryAssembler"
    ]

    if call_count >= len(agent_sequence):
        return RouterResult(None)  # Stop after all agents

    return RouterResult(agent_sequence[call_count])


# ============================================================================
# Main Story Generation Function
# ============================================================================

def generate_story(prompt: str) -> CompleteStory:
    """
    Generate a complete short story from a one-line prompt.

    Args:
        prompt: One-line story premise

    Returns:
        CompleteStory: Structured story with all elements
    """
    print(f"\n{'='*80}")
    print(f"AUTONOMOUS FICTION WRITER")
    print(f"{'='*80}\n")
    print(f"Prompt: {prompt}\n")

    # Create all agents
    writing_agents = create_writing_agents()
    assembler = create_assembler_agent()
    all_agents = writing_agents + [assembler]

    # Create pool with sequential router
    pool = create_pool(
        agents=all_agents,
        router=fiction_writer_router,
        max_iter=5  # 4 specialists + 1 assembler
    )

    # Generate the story
    print("Starting story generation...\n")
    print("1. CharacterAgent: Creating characters...")
    print("2. PlotAgent: Designing plot structure...")
    print("3. WorldbuildingAgent: Building the world...")
    print("4. DialogueAgent: Crafting dialogue...")
    print("5. StoryAssembler: Weaving final story...\n")

    result = pool.run(f"Write a short story based on this premise: {prompt}")

    print(f"\n{'='*80}")
    print("STORY GENERATION COMPLETE")
    print(f"{'='*80}\n")

    return result


# ============================================================================
# Display Functions
# ============================================================================

def display_story(story: CompleteStory):
    """Display the generated story in a beautiful format"""

    print(f"\n{'='*80}")
    print(f"{'='*80}")
    print(f"{story.title.upper():^80}")
    print(f"{'='*80}")
    print(f"{'='*80}\n")

    # Display metadata
    print(f"Genre: {story.genre}")
    print(f"Word Count: ~{story.word_count:,}")
    print(f"Characters: {', '.join(story.characters_featured)}")
    print(f"Themes: {', '.join(story.key_themes)}")

    print(f"\n{'-'*80}")
    print("SUMMARY")
    print(f"{'-'*80}")
    print(f"{story.story_summary}\n")

    print(f"{'-'*80}")
    print("FULL STORY")
    print(f"{'-'*80}\n")

    # Display the story text with proper formatting
    print(story.full_text)

    print(f"\n{'='*80}")
    print(f"END OF STORY")
    print(f"{'='*80}\n")


def save_story(story: CompleteStory, filename: str = None):
    """Save the story to a text file"""
    if filename is None:
        # Create filename from title
        filename = story.title.lower().replace(' ', '_').replace("'", '') + '.txt'

    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"{story.title}\n")
        f.write(f"{'='*len(story.title)}\n\n")
        f.write(f"Genre: {story.genre}\n")
        f.write(f"Word Count: ~{story.word_count:,}\n\n")
        f.write(f"{'-'*80}\n\n")
        f.write(story.full_text)
        f.write(f"\n\n{'-'*80}\n")
        f.write(f"Generated by Autonomous Fiction Writer\n")

    print(f"✓ Story saved to: {filename}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Check command-line arguments
    if len(sys.argv) != 2:
        print("Usage: python fiction_writer.py \"<your story premise>\"")
        print("\nExample:")
        print('  python fiction_writer.py "A detective discovers their reflection has started solving crimes independently"')
        sys.exit(1)

    prompt = sys.argv[1]

    # Generate the story
    try:
        story = generate_story(prompt)

        # Display the story
        if isinstance(story, CompleteStory):
            display_story(story)

            # Ask if user wants to save
            save = input("\nSave story to file? (y/n): ").strip().lower()
            if save == 'y':
                save_story(story)
        else:
            # Fallback if somehow we didn't get structured output
            print("Story generated, but output format is unexpected:")
            print(story)

    except KeyboardInterrupt:
        print("\n\nStory generation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR during generation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
