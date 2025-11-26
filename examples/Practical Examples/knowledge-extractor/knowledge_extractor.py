"""
Knowledge Extraction from Folders

Processes folders containing .txt, .md, .py files and creates:
- Summary per file
- Global knowledge map
- Q&A system
- Glossary
- Cross-reference graph

Architecture:
- File Summarizer Agent: Extracts key points from each file
- Knowledge Mapper Agent: Creates overall knowledge structure
- QA Generator Agent: Generates questions and answers
- Glossary Agent: Builds terminology dictionary
- Cross-Reference Agent: Maps connections between files
"""

import os
import sys
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict

from peargent import create_agent, create_pool, create_tool, RouterResult
from peargent.models import groq


# ============================================================================
# Pydantic Models for Structured Output
# ============================================================================

class FileSummary(BaseModel):
    """Summary of a single file"""
    filename: str = Field(description="Name of the file")
    file_type: str = Field(description="Type: code, documentation, or text")
    key_topics: List[str] = Field(description="Main topics covered")
    summary: str = Field(description="Brief summary of content")
    important_entities: List[str] = Field(description="Key concepts, functions, classes, or terms")


class FileSummaries(BaseModel):
    """Output from File Summarizer Agent"""
    agent_name: str = Field(description="Agent name", default="FileSummarizer")
    summaries: List[FileSummary] = Field(description="Summary for each file")
    total_files: int = Field(description="Number of files processed")


class KnowledgeMap(BaseModel):
    """Output from Knowledge Mapper Agent"""
    agent_name: str = Field(description="Agent name", default="KnowledgeMapper")
    main_themes: List[str] = Field(description="Overarching themes across all files")
    knowledge_structure: str = Field(description="Hierarchical organization of knowledge")
    key_insights: List[str] = Field(description="Important insights from the collection")


class QAPair(BaseModel):
    """A question-answer pair"""
    question: str = Field(description="Question about the knowledge base")
    answer: str = Field(description="Answer based on the files")
    source_files: List[str] = Field(description="Files used to answer this question")


class QASystem(BaseModel):
    """Output from QA Generator Agent"""
    agent_name: str = Field(description="Agent name", default="QAGenerator")
    qa_pairs: List[QAPair] = Field(description="Generated question-answer pairs")


class GlossaryEntry(BaseModel):
    """A glossary entry"""
    term: str = Field(description="The term")
    definition: str = Field(description="Clear definition")
    context: str = Field(description="How it's used in the files")
    related_terms: List[str] = Field(description="Related concepts")


class Glossary(BaseModel):
    """Output from Glossary Agent"""
    agent_name: str = Field(description="Agent name", default="GlossaryAgent")
    entries: List[GlossaryEntry] = Field(description="Glossary entries")


class CrossReference(BaseModel):
    """A connection between files"""
    file1: str = Field(description="First file")
    file2: str = Field(description="Second file")
    relationship: str = Field(description="How they relate")
    shared_concepts: List[str] = Field(description="Concepts they both discuss")


class CrossReferenceGraph(BaseModel):
    """Output from Cross-Reference Agent"""
    agent_name: str = Field(description="Agent name", default="CrossReferenceAgent")
    references: List[CrossReference] = Field(description="Connections between files")
    central_files: List[str] = Field(description="Files that connect to many others")


class KnowledgeBase(BaseModel):
    """Complete knowledge extraction result"""
    folder_path: str = Field(description="Path to analyzed folder")
    total_files: int = Field(description="Number of files processed")

    file_summaries: List[FileSummary] = Field(description="Per-file summaries")
    knowledge_map: str = Field(description="Overall knowledge structure")
    main_themes: List[str] = Field(description="Key themes")

    qa_pairs: List[QAPair] = Field(description="Q&A system")
    glossary: List[GlossaryEntry] = Field(description="Term definitions")
    cross_references: List[CrossReference] = Field(description="File connections")

    key_insights: List[str] = Field(description="Important discoveries")


# ============================================================================
# Tools: File Reading
# ============================================================================

def list_files_in_folder(folder_path: str) -> str:
    """List all .txt, .md, .py files in a folder"""
    try:
        path = Path(folder_path)
        if not path.exists():
            return f"ERROR: Folder '{folder_path}' does not exist."

        if not path.is_dir():
            return f"ERROR: '{folder_path}' is not a folder."

        # Find all relevant files
        extensions = ['.txt', '.md', '.py']
        files = []
        for ext in extensions:
            files.extend(path.glob(f'**/*{ext}'))

        if not files:
            return f"No .txt, .md, or .py files found in '{folder_path}'"

        # Format output
        result = f"Found {len(files)} files in '{folder_path}':\n\n"
        for f in sorted(files):
            result += f"- {f.name} ({f.suffix})\n"

        return result

    except Exception as e:
        return f"ERROR: {e}"


def read_file_content(file_path: str) -> str:
    """Read content of a single file"""
    try:
        path = Path(file_path)

        if not path.exists():
            return f"ERROR: File '{file_path}' does not exist."

        with open(path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        # Limit size for very large files
        if len(content) > 10000:
            content = content[:10000] + "\n\n[... file truncated ...]"

        return f"File: {path.name}\nSize: {len(content)} chars\n\n{content}"

    except Exception as e:
        return f"ERROR reading file: {e}"


def read_all_files_in_folder(folder_path: str) -> str:
    """Read all relevant files in a folder"""
    try:
        path = Path(folder_path)
        extensions = ['.txt', '.md', '.py']
        files = []

        for ext in extensions:
            files.extend(path.glob(f'**/*{ext}'))

        if not files:
            return f"No files found in '{folder_path}'"

        result = f"Reading {len(files)} files from '{folder_path}':\n\n"
        result += "="*80 + "\n\n"

        for f in sorted(files):
            try:
                with open(f, 'r', encoding='utf-8', errors='ignore') as file:
                    content = file.read()

                # Limit size
                if len(content) > 5000:
                    content = content[:5000] + "\n[... truncated ...]"

                result += f"FILE: {f.name}\n"
                result += "-"*40 + "\n"
                result += content + "\n\n"
                result += "="*80 + "\n\n"
            except:
                result += f"FILE: {f.name}\n[Could not read]\n\n"

        return result

    except Exception as e:
        return f"ERROR: {e}"


# Create tools
list_files_tool = create_tool(
    name="list_files",
    description="List all .txt, .md, .py files in a folder",
    input_parameters={"folder_path": str},
    call_function=list_files_in_folder
)

read_file_tool = create_tool(
    name="read_file",
    description="Read the content of a specific file",
    input_parameters={"file_path": str},
    call_function=read_file_content
)

read_all_files_tool = create_tool(
    name="read_all_files",
    description="Read all relevant files in a folder at once",
    input_parameters={"folder_path": str},
    call_function=read_all_files_in_folder
)


# ============================================================================
# Create Knowledge Extraction Agents
# ============================================================================

def create_extraction_agents():
    """Create all knowledge extraction agents"""

    # File Summarizer - Analyzes each file
    summarizer_agent = create_agent(
        name="FileSummarizer",
        description="Summarizes each file and extracts key information",
        persona="""You are an expert at analyzing documents and code.

Your job is to read all files in a folder and create a summary for each.

For each file, extract:
- Key topics it covers
- Brief summary (2-3 sentences)
- Important entities (concepts, functions, classes, terms)
- File type (code, documentation, or text)

Use the read_all_files tool to read the folder contents.

Return ONLY valid JSON matching the FileSummaries schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[list_files_tool, read_all_files_tool],
        output_schema=FileSummaries
    )

    # Knowledge Mapper - Creates overall structure
    mapper_agent = create_agent(
        name="KnowledgeMapper",
        description="Maps the overall knowledge structure",
        persona="""You are a knowledge architect who organizes information.

You will receive file summaries from the previous agent.

Your job is to:
- Identify main themes across all files
- Create a hierarchical knowledge structure
- Extract key insights from the collection

Think about:
- How do the files relate to each other?
- What's the big picture?
- What are the most important concepts?

Return ONLY valid JSON matching the KnowledgeMap schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=KnowledgeMap
    )

    # QA Generator - Creates question-answer pairs
    qa_agent = create_agent(
        name="QAGenerator",
        description="Generates questions and answers about the knowledge base",
        persona="""You are an expert at creating study materials.

Based on the file summaries and knowledge map, generate 8-12 useful questions and answers.

Questions should:
- Cover important topics from the files
- Be specific and answerable from the content
- Range from basic to advanced
- Help someone learn the material

For each Q&A pair, note which files contain the answer.

Return ONLY valid JSON matching the QASystem schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=QASystem
    )

    # Glossary Agent - Builds terminology dictionary
    glossary_agent = create_agent(
        name="GlossaryAgent",
        description="Creates a glossary of important terms",
        persona="""You are a technical writer who creates clear glossaries.

Based on the file summaries, create a glossary of important terms.

For each term:
- Provide a clear definition
- Explain how it's used in the files
- List related concepts

Focus on:
- Technical terms
- Key concepts
- Domain-specific vocabulary
- Anything that needs explanation

Create 10-20 glossary entries for the most important terms.

Return ONLY valid JSON matching the Glossary schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=Glossary
    )

    # Cross-Reference Agent - Maps connections
    crossref_agent = create_agent(
        name="CrossReferenceAgent",
        description="Maps connections between files",
        persona="""You are a knowledge graph expert who finds connections.

Based on the file summaries, identify how files relate to each other.

For each connection:
- Which two files are related?
- How do they relate? (depends on, extends, references, etc.)
- What concepts do they share?

Also identify central files that connect to many others.

Return ONLY valid JSON matching the CrossReferenceGraph schema.""",
        model=groq("llama-3.3-70b-versatile"),
        tools=[],
        output_schema=CrossReferenceGraph
    )

    return [
        summarizer_agent,
        mapper_agent,
        qa_agent,
        glossary_agent,
        crossref_agent
    ]


# ============================================================================
# Custom Sequential Router
# ============================================================================

def knowledge_extractor_router(state, call_count, last_result):
    """Sequential router for knowledge extraction"""
    agent_sequence = [
        "FileSummarizer",
        "KnowledgeMapper",
        "QAGenerator",
        "GlossaryAgent",
        "CrossReferenceAgent"
    ]

    if call_count >= len(agent_sequence):
        return RouterResult(None)

    return RouterResult(agent_sequence[call_count])


# ============================================================================
# Main Extraction Function
# ============================================================================

def extract_knowledge(folder_path: str) -> Dict:
    """Extract knowledge from a folder"""

    print(f"\n{'='*80}")
    print(f"KNOWLEDGE EXTRACTION")
    print(f"{'='*80}\n")
    print(f"Folder: {folder_path}\n")

    # Create agents
    agents = create_extraction_agents()

    # Create pool
    pool = create_pool(
        agents=agents,
        router=knowledge_extractor_router,
        max_iter=5
    )

    # Run extraction
    print("Starting extraction...\n")
    print("1. FileSummarizer: Analyzing each file...")
    print("2. KnowledgeMapper: Building knowledge structure...")
    print("3. QAGenerator: Creating Q&A pairs...")
    print("4. GlossaryAgent: Building glossary...")
    print("5. CrossReferenceAgent: Mapping connections...\n")

    result = pool.run(f"Extract knowledge from folder: {folder_path}")

    print(f"\n{'='*80}")
    print("EXTRACTION COMPLETE")
    print(f"{'='*80}\n")

    return result


# ============================================================================
# Display Functions
# ============================================================================

def display_knowledge_base(kb):
    """Display the extracted knowledge base"""

    print(f"\n{'='*80}")
    print(f"KNOWLEDGE BASE REPORT")
    print(f"{'='*80}\n")

    # The kb is the final result from the pool - it's a string representation
    # Try to extract meaningful information from it
    
    if isinstance(kb, str):
        # Parse the CrossReferenceGraph output
        if 'references=' in kb and 'central_files=' in kb:
            import re
            
            print("**CROSS-REFERENCE ANALYSIS**\n")
            
            # Extract central files
            central_match = re.search(r"central_files=\[(.*?)\]", kb)
            if central_match:
                central_files = [f.strip().strip("'\"") for f in central_match.group(1).split(',') if f.strip()]
                print("**Central Files** (most connected):")
                for i, file in enumerate(central_files[:5], 1):  # Show top 5
                    print(f"  {i}. {file}")
                print()
            
            # Extract some relationships
            refs_match = re.search(r"references=\[(.*?)\]", kb, re.DOTALL)
            if refs_match:
                print("**Key Relationships**:")
                # Try to extract first few relationships
                refs_text = refs_match.group(1)
                
                # Count relationships by type
                extends_count = refs_text.count("relationship='extends'")
                depends_count = refs_text.count("relationship='depends on'")
                references_count = refs_text.count("relationship='references'")
                
                if extends_count > 0:
                    print(f"  • Extension relationships: {extends_count}")
                if depends_count > 0:
                    print(f"  • Dependency relationships: {depends_count}")
                if references_count > 0:
                    print(f"  • Reference relationships: {references_count}")
                print()
            
            print("**Knowledge Structure Created Successfully!**")
            print("   - File relationships mapped")
            print("   - Central concepts identified") 
            print("   - Knowledge graph constructed")
            
        else:
            print("WARNING: Raw output (parsing needed):")
            print(kb[:500] + "..." if len(str(kb)) > 500 else kb)
    else:
        print("WARNING: Unexpected output format:")
        print(str(kb)[:500] + "..." if len(str(kb)) > 500 else str(kb))


def save_knowledge_base(kb, output_file: str = "knowledge_base.md"):
    """Save knowledge base to a markdown file"""

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# Knowledge Base Report\n\n")
        f.write(f"Generated from automated knowledge extraction\n\n")
        f.write(f"## Analysis Summary\n\n")
        
        if isinstance(kb, str) and 'central_files=' in kb:
            import re
            
            # Extract and format central files
            central_match = re.search(r"central_files=\[(.*?)\]", kb)
            if central_match:
                central_files = [f.strip().strip("'\"") for f in central_match.group(1).split(',') if f.strip()]
                f.write("### Central Files\n\n")
                f.write("Most connected files in the knowledge base:\n\n")
                for i, file in enumerate(central_files, 1):
                    f.write(f"{i}. **{file}**\n")
                f.write("\n")
            
            # Extract relationships info
            refs_match = re.search(r"references=\[(.*?)\]", kb, re.DOTALL)
            if refs_match:
                refs_text = refs_match.group(1)
                extends_count = refs_text.count("relationship='extends'")
                depends_count = refs_text.count("relationship='depends on'")
                references_count = refs_text.count("relationship='references'")
                
                f.write("### Relationship Statistics\n\n")
                f.write(f"- Extension relationships: {extends_count}\n")
                f.write(f"- Dependency relationships: {depends_count}\n") 
                f.write(f"- Reference relationships: {references_count}\n\n")
            
            f.write("### Raw Analysis Data\n\n")
            f.write("```\n")
            f.write(str(kb))
            f.write("\n```\n")
        else:
            f.write("### Raw Output\n\n")
            f.write("```\n")
            f.write(str(kb))
            f.write("\n```\n")

    print(f"Knowledge base saved to: {output_file}")


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python knowledge_extractor.py <folder_path>")
        print("\nExample:")
        print("  python knowledge_extractor.py ./my_project")
        sys.exit(1)

    folder_path = sys.argv[1]

    # Verify folder exists
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
        save = input("\nSave knowledge base to file? (y/n): ").strip().lower()
        if save == 'y':
            save_knowledge_base(result)

    except KeyboardInterrupt:
        print("\n\nExtraction cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
