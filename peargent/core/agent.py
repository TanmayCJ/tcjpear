# peargent/core/agent.py

"""
Agent module for peargent framework.
Provides the Agent class that represents an AI agent with tools and persona.
"""

import json
import os
import re
from typing import Optional, Dict, List, Any

from jinja2 import Environment, FileSystemLoader
from peargent.core.stopping import limit_steps


class Agent:
    """
    An AI agent that can use tools and maintain conversation memory.

    Attributes:
        name (str): Unique identifier for the agent
        model: LLM model instance for generating responses
        persona (str): System prompt defining agent's role and behavior
        description (str): High-level description of agent's purpose
        tools (dict): Dictionary of available tools (name -> Tool object)
        stop_conditions: Conditions that determine when agent should stop iterating
        temporary_memory (list): Conversation history for current run session
    """
    def __init__(self, name, model, persona, description, tools, stop=None):
        self.name = name
        self.model = model
        self.persona = persona
        self.description = description
        self.tools = {tool.name: tool for tool in tools}
        self.stop_conditions = stop or limit_steps(5)

        self.tool_schemas = [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": {
                    k: v.__name__ if isinstance(v, type) else str(v)
                    for k, v in tool.input_parameters.items()
                },
            }
            for tool in tools
        ]

        self.jinja_env = Environment(
            loader=FileSystemLoader(
                os.path.join(os.path.dirname(__file__), "..", "templates")
            )
        )

    def _render_tools_prompt(self) -> str:
        """Render the tools prompt template with available tools."""
        template = self.jinja_env.get_template("tools_prompt.j2")
        return template.render(tools=self.tool_schemas)

    def _build_initial_prompt(self, user_input: str) -> str:
        """
        Build the initial prompt for the LLM.

        Includes persona, tools (if available), and conversation memory.
        For agents without tools, explicitly instructs to not use JSON.
        """
        # Only include tool prompt if agent has tools
        if self.tools:
            tools_prompt = self._render_tools_prompt()
        else:
            tools_prompt = "IMPORTANT: You do not have access to any tools. Respond directly in natural language only. Do NOT output JSON."

        memory_str = "\n".join(
            [
                f"{item['role'].capitalize()}: {item['content']}"
                for item in self.temporary_memory
            ]
        )
        return f"{self.persona}\n\n{tools_prompt}\n\n{memory_str}\n\nAssistant:"

    def _add_to_memory(self, role: str, content: Any) -> None:
        """Add a message to the agent's temporary memory."""
        self.temporary_memory.append({"role": role, "content": content})

    def run(self, input_data: str) -> str:
        """
        Execute the agent with the given input.

        Handles the agent's main loop: generating responses, parsing tool calls,
        executing tools, and managing conversation flow.

        Args:
            input_data (str): The user's input or previous agent's output

        Returns:
            str: The agent's final response
        """
        self.temporary_memory = []

        self._add_to_memory("user", input_data)

        prompt = self._build_initial_prompt(input_data)

        step = 0

        while True:
            # Increment step counter
            step += 1

            response = self.model.generate(prompt)

            self._add_to_memory("assistant", response)

            tool_call = self._parse_tool_call(response)
            if tool_call:
                tool_name = tool_call["tool"]
                args = tool_call["args"]

                if tool_name not in self.tools:
                    raise ValueError(f"Tool '{tool_name}' not found in agent's toolset.")

                tool_output = self.tools[tool_name].run(args)
                
                # Store tool result in a structured way
                self._add_to_memory("tool", {
                    "name": tool_name,
                    "args": args,
                    "output": tool_output
                })

                if self.stop_conditions.should_stop(step - 1, self.temporary_memory):
                    # Instead of returning generic message, return tool result
                    return f"Tool result: {tool_output}"

                # Build follow-up prompt with full memory context and separate tool result
                tools_prompt = self._render_tools_prompt() if self.tools else ""
                conversation_history = "\n".join(
                    [f"{item['role'].capitalize()}: {item['content']}" if item['role'] != "tool"
                    else f"Tool '{item['content']['name']}' called with args:\n{item['content']['args']}\nOutput:\n{item['content']['output']}"
                    for item in self.temporary_memory]
                )

                # Create different instructions based on whether agent has more tools available
                if self.tools:
                    assistant_instruction = (
                        f"Assistant: The tool has executed successfully. Based on the tool output above:\n"
                        f"1. If you need to use another tool, respond with the tool JSON.\n"
                        f"2. Otherwise, provide your final response that INCLUDES the actual tool results/data.\n"
                        f"3. Do NOT just describe what you did - show the actual results. Unless mentioned otherwise.\n"
                        f"DO NOT output JSON unless calling a tool."
                    )
                else:
                    assistant_instruction = (
                        f"Assistant: Based on the information above, provide your response in natural language."
                    )

                prompt = (
                    f"{self.persona}\n\n{tools_prompt}\n\n"
                    f"Conversation History:\n{conversation_history}\n\n"
                    f"{assistant_instruction}"
                )

                continue  # Go to next loop iteration

            # Check if we should stop before returning (avoid returning JSON)
            if self.stop_conditions.should_stop(step, self.temporary_memory):
                # Get the last meaningful output (not a tool call JSON)
                for item in reversed(self.temporary_memory):
                    if item['role'] == 'tool':
                        return f"Based on the analysis: {item['content']['output']}"
                return "Task completed with available information."

            # No tool call, return final answer
            return response

    def _parse_tool_call(self, llm_output: str) -> Optional[Dict[str, Any]]:
        """
        Parse LLM output to detect and extract tool call JSON.

        Supports multiple formats:
        1. Pure JSON object
        2. JSON in markdown code blocks
        3. JSON embedded in prose text

        Args:
            llm_output (str): Raw output from the LLM

        Returns:
            Optional[Dict]: Parsed tool call dict with 'tool' and 'args' keys,
                           or None if no tool call detected
        """

        # First try to parse as plain JSON
        try:
            structured_response = json.loads(llm_output.strip())
            if (
                isinstance(structured_response, dict)
                and "tool" in structured_response
                and "args" in structured_response
            ):
                return structured_response
        except (json.JSONDecodeError, TypeError):
            pass

        # Try to find JSON in code blocks
        json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(json_pattern, llm_output, re.DOTALL)

        if match:
            json_content = match.group(1)
            try:
                structured_response = json.loads(json_content)
                if (
                    isinstance(structured_response, dict)
                    and "tool" in structured_response
                    and "args" in structured_response
                ):
                    return structured_response
            except (json.JSONDecodeError, TypeError):
                pass

        # Try to extract JSON object from text (even if mixed with prose)
        # Find the start of a JSON object that might contain tool call
        # Look for `{` followed by content that includes "tool" and "args"
        try:
            # Find all potential JSON objects in the text
            brace_stack = []
            start_idx = None

            for i, char in enumerate(llm_output):
                if char == '{':
                    if not brace_stack:
                        start_idx = i
                    brace_stack.append(i)
                elif char == '}':
                    if brace_stack:
                        brace_stack.pop()
                        if not brace_stack and start_idx is not None:
                            # Found a complete JSON object
                            potential_json = llm_output[start_idx:i+1]
                            if '"tool"' in potential_json and '"args"' in potential_json:
                                try:
                                    structured_response = json.loads(potential_json)
                                    if (
                                        isinstance(structured_response, dict)
                                        and "tool" in structured_response
                                        and "args" in structured_response
                                    ):
                                        return structured_response
                                except (json.JSONDecodeError, TypeError):
                                    pass
                            start_idx = None
        except Exception:
            pass

        return None  # Not a tool call
