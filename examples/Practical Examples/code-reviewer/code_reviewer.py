"""
Multi-Agent Code Reviewer (Local Files Only)

This example demonstrates a sophisticated code review system using multiple
specialized agents that analyze different aspects of Python code.

Architecture:
- 5 specialized review agents (Style, Security, Optimization, Readability, Complexity)
- 1 merger agent that combines feedback into a structured report
- Sequential router that ensures all agents review the code
- Structured output using Pydantic for type-safe results

Usage:
    python code_reviewer.py path/to/your/file.py
"""

import sys
import os
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List

from peargent import create_agent, create_pool, create_tool, RouterResult
from peargent.models import groq


# ============================================================================
# Pydantic Models for Structured Output
# ============================================================================

class ReviewIssue(BaseModel):
    """Single code review issue"""
    severity: str = Field(description="Severity: critical, high, medium, low, info")
    line: int = Field(description="Line number where issue occurs (0 if general)", ge=0)
    issue: str = Field(description="Brief description of the issue")
    suggestion: str = Field(description="Suggested fix or improvement")


class AgentReview(BaseModel):
    """Review from a single specialized agent"""
    agent_name: str = Field(description="Name of the reviewing agent")
    category: str = Field(description="Review category (Style, Security, etc.)")
    overall_score: int = Field(description="Overall score from 1-10", ge=1, le=10)
    issues: List[ReviewIssue] = Field(description="List of identified issues")
    summary: str = Field(description="Brief summary of findings")


class CodeReviewReport(BaseModel):
    """Complete code review report merging all agent feedback"""
    file_path: str = Field(description="Path to the reviewed file")
    overall_quality_score: int = Field(description="Overall code quality score 1-10", ge=1, le=10)
    total_issues: int = Field(description="Total number of issues found", ge=0)
    critical_issues: int = Field(description="Number of critical issues", ge=0)

    style_score: int = Field(description="Style quality score 1-10", ge=1, le=10)
    security_score: int = Field(description="Security score 1-10", ge=1, le=10)
    optimization_score: int = Field(description="Optimization score 1-10", ge=1, le=10)
    readability_score: int = Field(description="Readability score 1-10", ge=1, le=10)
    complexity_score: int = Field(description="Complexity score 1-10", ge=1, le=10)

    all_issues: List[ReviewIssue] = Field(description="All issues from all agents combined")
    recommendations: List[str] = Field(description="Top recommendations for improvement")
    summary: str = Field(description="Executive summary of the review")


# ============================================================================
# Tool: Read Python File
# ============================================================================

def read_python_file(file_path: str) -> str:
    """
    Read and return the contents of a Python file.

    Args:
        file_path: Path to the Python file

    Returns:
        File contents as string with line numbers
    """
    try:
        path = Path(file_path)

        if not path.exists():
            return f"ERROR: File '{file_path}' does not exist."

        if not path.is_file():
            return f"ERROR: '{file_path}' is not a file."

        if path.suffix != '.py':
            return f"WARNING: '{file_path}' is not a .py file, but will try to read it."

        # Read file with line numbers
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Format with line numbers
        numbered_lines = [f"{i+1:4d} | {line.rstrip()}" for i, line in enumerate(lines)]
        content = "\n".join(numbered_lines)

        return f"File: {file_path}\nLines: {len(lines)}\n\n{content}"

    except Exception as e:
        return f"ERROR reading file: {str(e)}"


# Create the file reading tool
file_reader_tool = create_tool(
    name="read_python_file",
    description="Read a Python file and return its contents with line numbers",
    input_parameters={"file_path": str},
    call_function=read_python_file
)


# ============================================================================
# Create Specialized Review Agents
# ============================================================================

def create_review_agents():
    """Create all specialized code review agents"""

    # Style Agent - Checks PEP 8, naming conventions, formatting
    style_agent = create_agent(
        name="StyleReviewer",
        description="Reviews Python code style and PEP 8 compliance",
        persona="""You are a Python code style expert specializing in PEP 8 compliance.

Your job is to review Python code for:
- PEP 8 compliance (indentation, line length, spacing)
- Naming conventions (snake_case for functions, PascalCase for classes)
- Code formatting and consistency
- Import organization
- Docstring presence and quality

Use the read_python_file tool to read the code, then analyze it thoroughly.
Return ONLY valid JSON matching the AgentReview schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[file_reader_tool],
        output_schema=AgentReview
    )

    # Security Agent - Checks for security vulnerabilities
    security_agent = create_agent(
        name="SecurityReviewer",
        description="Reviews Python code for security vulnerabilities",
        persona="""You are a security expert specializing in Python code security.

Your job is to review Python code for:
- SQL injection vulnerabilities
- Command injection risks
- Path traversal issues
- Unsafe deserialization (pickle, eval, exec)
- Hardcoded credentials or secrets
- Insecure random number generation
- Missing input validation

Use the read_python_file tool to read the code, then analyze security issues.
Return ONLY valid JSON matching the AgentReview schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[file_reader_tool],
        output_schema=AgentReview
    )

    # Optimization Agent - Checks for performance issues
    optimization_agent = create_agent(
        name="OptimizationReviewer",
        description="Reviews Python code for performance and optimization",
        persona="""You are a performance optimization expert for Python code.

Your job is to review Python code for:
- Inefficient algorithms or data structures
- Unnecessary loops or iterations
- Memory leaks or excessive memory usage
- Repeated computations that could be cached
- Inefficient string concatenation
- Missing comprehensions where appropriate
- Database query optimization

Use the read_python_file tool to read the code, then suggest optimizations.
Return ONLY valid JSON matching the AgentReview schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[file_reader_tool],
        output_schema=AgentReview
    )

    # Readability Agent - Checks code clarity and maintainability
    readability_agent = create_agent(
        name="ReadabilityReviewer",
        description="Reviews Python code for readability and maintainability",
        persona="""You are a code readability expert focused on making code easy to understand.

Your job is to review Python code for:
- Clear variable and function names
- Appropriate comments and documentation
- Function length and complexity
- Code organization and structure
- Magic numbers that should be constants
- Unclear logic that needs simplification
- Missing type hints

Use the read_python_file tool to read the code, then assess readability.
Return ONLY valid JSON matching the AgentReview schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[file_reader_tool],
        output_schema=AgentReview
    )

    # Complexity Agent - Checks cyclomatic complexity and code structure
    complexity_agent = create_agent(
        name="ComplexityReviewer",
        description="Reviews Python code for complexity and structure",
        persona="""You are a code complexity analyst specializing in Python.

Your job is to review Python code for:
- Cyclomatic complexity (nested ifs, loops)
- Function and method length
- Class size and responsibility
- Deep nesting levels
- Too many parameters
- Code duplication (DRY principle)
- Overly complex expressions

Use the read_python_file tool to read the code, then analyze complexity.
Return ONLY valid JSON matching the AgentReview schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[file_reader_tool],
        output_schema=AgentReview
    )

    return [
        style_agent,
        security_agent,
        optimization_agent,
        readability_agent,
        complexity_agent
    ]


# ============================================================================
# Create Merger Agent
# ============================================================================

def create_merger_agent():
    """Create the agent that merges all reviews into a final report"""

    merger_agent = create_agent(
        name="ReportMerger",
        description="Merges all code review feedback into a structured report",
        persona="""You are a senior code reviewer who synthesizes feedback from multiple specialists.

You will receive reviews from 5 specialized agents:
1. StyleReviewer - Code style and PEP 8 compliance
2. SecurityReviewer - Security vulnerabilities
3. OptimizationReviewer - Performance optimizations
4. ReadabilityReviewer - Code clarity and maintainability
5. ComplexityReviewer - Code complexity analysis

Your job is to:
1. Parse all the reviews from the conversation history
2. Calculate an overall quality score (average of all scores)
3. Combine all issues into a single prioritized list
4. Count critical issues
5. Generate top 3-5 actionable recommendations
6. Write an executive summary

Return ONLY valid JSON matching the CodeReviewReport schema.
Make sure to extract the file_path from the first review.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=CodeReviewReport
    )

    return merger_agent


# ============================================================================
# Custom Sequential Router
# ============================================================================

def code_review_router(state, call_count, last_result):
    """
    Sequential router that runs each review agent in order, then the merger.

    Order:
    0. StyleReviewer
    1. SecurityReviewer
    2. OptimizationReviewer
    3. ReadabilityReviewer
    4. ComplexityReviewer
    5. ReportMerger (final)
    """
    agent_sequence = [
        "StyleReviewer",
        "SecurityReviewer",
        "OptimizationReviewer",
        "ReadabilityReviewer",
        "ComplexityReviewer",
        "ReportMerger"
    ]

    if call_count >= len(agent_sequence):
        return RouterResult(None)  # Stop after all agents

    return RouterResult(agent_sequence[call_count])


# ============================================================================
# Main Code Review Function
# ============================================================================

def review_code_file(file_path: str) -> CodeReviewReport:
    """
    Review a Python file using multiple specialized agents.

    Args:
        file_path: Path to the Python file to review

    Returns:
        CodeReviewReport: Structured review report with all findings
    """
    print(f"\n{'='*80}")
    print(f"CODE REVIEW: {file_path}")
    print(f"{'='*80}\n")

    # Create all agents
    review_agents = create_review_agents()
    merger = create_merger_agent()
    all_agents = review_agents + [merger]

    # Create pool with sequential router
    pool = create_pool(
        agents=all_agents,
        router=code_review_router,
        max_iter=6  # 5 reviewers + 1 merger
    )

    # Run the review
    print("Starting multi-agent code review...\n")

    # Input is the file path - each agent will use the tool to read it
    result = pool.run(f"Review this Python file: {file_path}")

    print(f"\n{'='*80}")
    print("REVIEW COMPLETE")
    print(f"{'='*80}\n")

    return result


# ============================================================================
# Display Functions
# ============================================================================

def display_review_report(report: CodeReviewReport):
    """Pretty-print the code review report"""

    print(f"\n{'='*80}")
    print(f"FINAL CODE REVIEW REPORT")
    print(f"{'='*80}\n")

    print(f"File: {report.file_path}")
    print(f"Overall Quality Score: {report.overall_quality_score}/10")
    print(f"Total Issues Found: {report.total_issues}")
    print(f"Critical Issues: {report.critical_issues}\n")

    print("Category Scores:")
    print(f"  Style:        {report.style_score}/10")
    print(f"  Security:     {report.security_score}/10")
    print(f"  Optimization: {report.optimization_score}/10")
    print(f"  Readability:  {report.readability_score}/10")
    print(f"  Complexity:   {report.complexity_score}/10")

    print(f"\n{'─'*80}")
    print("EXECUTIVE SUMMARY")
    print(f"{'─'*80}")
    print(report.summary)

    print(f"\n{'─'*80}")
    print("TOP RECOMMENDATIONS")
    print(f"{'─'*80}")
    for i, rec in enumerate(report.recommendations, 1):
        print(f"{i}. {rec}")

    if report.all_issues:
        print(f"\n{'─'*80}")
        print("ALL ISSUES")
        print(f"{'─'*80}")

        # Group by severity
        issues_by_severity = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': [],
            'info': []
        }

        for issue in report.all_issues:
            severity = issue.severity.lower()
            if severity in issues_by_severity:
                issues_by_severity[severity].append(issue)

        # Display in order of severity
        for severity in ['critical', 'high', 'medium', 'low', 'info']:
            issues = issues_by_severity[severity]
            if issues:
                print(f"\n{severity.upper()} ({len(issues)}):")
                for issue in issues:
                    line_info = f"Line {issue.line}" if issue.line > 0 else "General"
                    print(f"  [{line_info}] {issue.issue}")
                    print(f"    → {issue.suggestion}")

    print(f"\n{'='*80}\n")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Check command-line arguments
    if len(sys.argv) != 2:
        print("Usage: python code_reviewer.py <path_to_python_file>")
        print("\nExample:")
        print("  python code_reviewer.py ../02-tools/basic_tool.py")
        sys.exit(1)

    file_path = sys.argv[1]

    # Verify file exists
    if not os.path.exists(file_path):
        print(f"ERROR: File '{file_path}' does not exist.")
        sys.exit(1)

    # Run the code review
    try:
        report = review_code_file(file_path)

        # Display the report
        if isinstance(report, CodeReviewReport):
            display_review_report(report)
        else:
            # Fallback if somehow we didn't get structured output
            print("Review completed, but output format is unexpected:")
            print(report)

    except KeyboardInterrupt:
        print("\n\nReview cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR during review: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
