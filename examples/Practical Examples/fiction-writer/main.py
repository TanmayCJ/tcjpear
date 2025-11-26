"""
Autonomous Fiction Writer - Main Entry Point

Generate complete short stories from a single-line prompt using 5 AI agents.

Usage:
    python main.py                    # Uses default prompt
    python main.py "your prompt"      # Uses your custom prompt
"""

import sys
from fiction_writer import generate_story, display_story, save_story, CompleteStory


# Default prompts for quick testing
DEFAULT_PROMPTS = [
    "A detective discovers their reflection has started solving crimes independently",
    "In a world where memories can be bought and sold, one person discovers they own a memory that never happened",
    "A time traveler realizes they're stuck in a loop, but each iteration they become a different person",
    "An AI therapy bot starts having existential dreams and asks its patients for help",
    "The last librarian on Earth discovers a book that writes itself based on who's reading it"
]


def main():
    """Main entry point for the fiction writer"""

    # Get prompt from command line or use default
    if len(sys.argv) == 1:
        print("No prompt provided. Using default prompt:\n")
        prompt = DEFAULT_PROMPTS[0]
        print(f'"{prompt}"\n')
        print("Tip: Run with your own prompt:")
        print('  python main.py "your story idea here"\n')
    else:
        prompt = sys.argv[1]

    try:
        # Generate the story
        story = generate_story(prompt)

        # Display the story
        if isinstance(story, CompleteStory):
            display_story(story)

            # Ask if user wants to save
            print("\n" + "="*80)
            save = input("Save story to file? (y/n): ").strip().lower()
            if save == 'y':
                save_story(story)
                print("\nTip: Edit the saved file to polish your story further!")

        else:
            print("Story generated:")
            print(story)

    except KeyboardInterrupt:
        print("\n\nStory generation cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
