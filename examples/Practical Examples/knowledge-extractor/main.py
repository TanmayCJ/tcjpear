"""
Knowledge Extractor - Main Entry Point

Extract comprehensive knowledge from folders containing .txt, .md, .py files.

Usage:
    python main.py                   # Uses sample_docs folder
    python main.py path/to/folder   # Uses your folder
"""

import sys
import os
from knowledge_extractor import extract_knowledge, display_knowledge_base, save_knowledge_base


def main():
    """Main entry point"""

    # Get folder from command line or use default
    if len(sys.argv) == 1:
        # Use sample_docs in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        folder_path = os.path.join(script_dir, "sample_docs")

        if not os.path.exists(folder_path):
            print(f"No folder specified and '{folder_path}' doesn't exist.")
            print("\nUsage: python main.py <folder_path>")
            print("Example: python main.py ./my_project")
            sys.exit(1)
        print(f"Using default folder: sample_docs\n")
    else:
        folder_path = sys.argv[1]

    # Verify folder
    if not os.path.exists(folder_path):
        print(f"ERROR: Folder '{folder_path}' does not exist.")
        sys.exit(1)

    if not os.path.isdir(folder_path):
        print(f"ERROR: '{folder_path}' is not a folder.")
        sys.exit(1)

    try:
        # Extract knowledge
        result = extract_knowledge(folder_path)

        # Display results
        display_knowledge_base(result)

        # Ask to save
        print("\n" + "="*80)
        save = input("Save knowledge base to markdown file? (y/n): ").strip().lower()
        if save == 'y':
            filename = f"{os.path.basename(folder_path)}_knowledge_base.md"
            save_knowledge_base(result, filename)

    except KeyboardInterrupt:
        print("\n\nExtraction cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
