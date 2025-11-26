"""
Python Code Generator - Main Entry Point

Generate Python code from natural language descriptions.

Usage:
    python main.py                           # Uses default task
    python main.py "your task description"  # Uses your task
"""

import sys
from code_generator import generate_code, display_result, save_code


# Default tasks for quick testing
DEFAULT_TASKS = [
    "Create a function to find prime numbers up to n",
    "Write a function to calculate fibonacci numbers",
    "Create a class for a simple stack data structure",
    "Write a function to reverse a string without using slicing"
]


def main():
    """Main entry point"""

    # Get task from command line or use default
    if len(sys.argv) == 1:
        task = DEFAULT_TASKS[0]
        print(f'Using default task: "{task}"\n')
        print("Tip: Run with your own task:")
        print('  python main.py "your programming task here"\n')
    else:
        task = sys.argv[1]

    try:
        # Generate code
        code, explanation, test_result, all_outputs = generate_code(task)

        # Display results
        display_result(code, explanation, test_result, all_outputs)

        # Show summary
        print(f"\n{'='*80}")
        print("GENERATION SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Code Generated: {'Yes' if code else 'No'}")
        print(f"✅ Explanation Available: {'Yes' if explanation else 'No'}")
        print(f"✅ Test Results Available: {'Yes' if test_result else 'No'}")
        print(f"📊 Total Agent Outputs: {len(all_outputs) if all_outputs else 0}")

        # Offer to save
        if code:
            print(f"\n🎉 Success! Generated {len(code.split(chr(10)))} lines of code.")
            print("\n" + "="*80)
            save_choice = input("💾 Save generated code to file? (y/n): ").strip().lower()
            if save_choice == 'y':
                filename = input("📝 Filename (default: generated_code.py): ").strip() or "generated_code.py"
                save_code(code, filename)
                print(f"\n🚀 Tip: Run the code with: python {filename}")
        else:
            print(f"\n⚠️  Code extraction failed. Check the debug output above.")

    except KeyboardInterrupt:
        print("\n\nGeneration cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
