"""
Multi-Agent Code Reviewer - Main Entry Point

Simple script to run the code reviewer on any Python file.

Usage:
    python main.py                           # Reviews sample_code_to_review.py
    python main.py path/to/your/file.py     # Reviews your file
"""

import sys
from code_reviewer import review_code_file, display_review_report, CodeReviewReport


def main():
    """Main entry point for the code reviewer"""

    # Default to sample file if no argument provided
    if len(sys.argv) == 1:
        file_path = "sample_code_to_review.py"
        print("No file specified, using sample_code_to_review.py\n")
    else:
        file_path = sys.argv[1]

    try:
        # Run the code review
        print(f"Reviewing: {file_path}\n")
        report = review_code_file(file_path)

        # Display the report
        if isinstance(report, CodeReviewReport):
            display_review_report(report)
        else:
            print("Review completed:")
            print(report)

    except KeyboardInterrupt:
        print("\n\nReview cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
