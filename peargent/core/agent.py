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
from peargent.core.history import ConversationHistory
from peargent.observability.cost_tracker import get_cost_tracker
from peargent.observability import get_tracer, SpanType


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
        history (ConversationHistory, optional): Persistent conversation history manager
        auto_manage_context (bool): Whether to automatically manage context window
        max_context_messages (int): Maximum messages before auto-management triggers
        context_strategy (str): Strategy for context management ("smart", "trim_last", "trim_first", "summarize")
        summarize_model: Model to use for summarization (falls back to main model if not provided)
    """
    def __init__(self, name, model, persona, description, tools, stop=None, history: Optional[ConversationHistory] = None, auto_manage_context: bool = False, max_context_messages: int = 20, context_strategy: str = "smart", summarize_model=None, tracing: bool = False, _tracing_explicitly_set: bool = False):
        self.name = name
        self.model = model
        self.persona = persona
        self.description = description
        self.tools = {tool.name: tool for tool in tools}
        self.stop_conditions = stop or limit_steps(5)
        self.history = history
        self.auto_manage_context = auto_manage_context
        self.max_context_messages = max_context_messages
        self.context_strategy = context_strategy
        self.summarize_model = summarize_model
        self.tracing = tracing
        self._tracing_explicitly_set = _tracing_explicitly_set

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

    def _render_no_tools_prompt(self) -> str:
        """Render the no-tools prompt template."""
        template = self.jinja_env.get_template("no_tools_prompt.j2")
        return template.render()

    def _render_follow_up_prompt(self, conversation_history: str, has_tools: bool) -> str:
        """Render the follow-up prompt template after tool execution."""
        template = self.jinja_env.get_template("follow_up_prompt.j2")
        tools_prompt = self._render_tools_prompt() if self.tools else ""
        return template.render(
            persona=self.persona,
            tools_prompt=tools_prompt,
            conversation_history=conversation_history,
            has_tools=has_tools
        )

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
            tools_prompt = self._render_no_tools_prompt()

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

    def _load_history_into_memory(self) -> None:
        """Load previous messages from persistent history into temporary memory."""
        if not self.history:
            return

        # Auto-create a thread if none exists
        if not self.history.current_thread_id:
            self.history.create_thread(metadata={"agent": self.name})

        messages = self.history.get_messages()
        for msg in messages:
            if msg.role == "tool":
                # Tool messages are stored as structured data
                self.temporary_memory.append({
                    "role": "tool",
                    "content": msg.tool_call
                })
            else:
                self.temporary_memory.append({
                    "role": msg.role,
                    "content": msg.content
                })

    def _sync_to_history(self) -> None:
        """Sync new temporary memory messages to persistent history."""
        if not self.history:
            return

        # Ensure a thread exists
        if not self.history.current_thread_id:
            self.history.create_thread(metadata={"agent": self.name})

        # Get count of messages already in history
        existing_msg_count = len(self.history.get_messages())

        # Only sync new messages (those added in this run)
        new_messages = self.temporary_memory[existing_msg_count:]

        for item in new_messages:
            role = item["role"]
            content = item["content"]

            if role == "user":
                self.history.add_user_message(content)
            elif role == "assistant":
                self.history.add_assistant_message(content, agent=self.name)
            elif role == "tool":
                self.history.add_tool_message(content, agent=self.name)

    def run(self, input_data: str) -> str:
        """
        Execute the agent with the given input.

        Handles the agent's main loop: generating responses, parsing tool calls,
        executing tools, and managing conversation flow.

        If a history manager is configured, previous conversation context will be
        loaded and all new messages will be persisted.

        Args:
            input_data (str): The user's input or previous agent's output

        Returns:
            str: The agent's final response
        """
        self.temporary_memory = []
        
        # Trace initialize
        trace = None
        tracer = get_tracer() if self.tracing else None
        if tracer and tracer.enabled:
            # Get session and user context if available
            from peargent.observability import get_session_id, get_user_id
            session_id = get_session_id()
            user_id = get_user_id()

            trace_id = tracer.start_trace(
                agent_name=self.name,
                input_data=input_data,
                session_id=session_id,
                user_id=user_id
            )
            trace = tracer.get_trace(trace_id)
        

        # Ensure a thread exists if using history
        if self.history and not self.history.current_thread_id:
            self.history.create_thread(metadata={"agent": self.name})

        # Apply automatic context management before loading history
        if self.history and self.auto_manage_context:
            try:
                # Use the configured summarize_model if available and strategy involves summarization
                management_model = self.model
                if self.summarize_model and self.context_strategy in ["smart", "summarize"]:
                    management_model = self.summarize_model

                self.history.manage_context_window(
                    model=management_model,
                    max_messages=self.max_context_messages,
                    strategy=self.context_strategy
                )
            except Exception as e:
                # Don't fail if context management fails
                print(f"Warning: Context management failed: {e}")

        # Load previous conversation history if available
        self._load_history_into_memory()

        self._add_to_memory("user", input_data)

        prompt = self._build_initial_prompt(input_data)

        step = 0

        try:
            while True:
                # Increment step counter
                step += 1
                
                #Tracing LLM call span
                if tracer and tracer.enabled:
                    with tracer.trace_llm_call(f"LLM Call (step {step})") as span:
                        response = self.model.generate(prompt)

                        # Track tokens and cost
                        if span:
                            cost_tracker = get_cost_tracker()
                            # Try to get model_name from the model object
                            model_name = getattr(self.model, 'model_name', None) or getattr(self.model, 'model', 'unknown')
                            try:
                                prompt_tokens, completion_tokens, cost = cost_tracker.count_and_calculate(
                                    prompt=prompt,
                                    completion=response,
                                    model=model_name
                                )
                                span.set_llm_data(prompt=prompt, response=response, model=model_name)
                                span.set_tokens(prompt_tokens, completion_tokens, cost)
                            except Exception:
                                # If token counting fails, still set the data without tokens
                                span.set_llm_data(prompt=prompt, response=response, model=model_name)
                else:
                    response = self.model.generate(prompt)
              # ===== END TRACING =====

                self._add_to_memory("assistant", response)

                tool_call = self._parse_tool_call(response)
                if tool_call:
                    tool_name = tool_call["tool"]
                    args = tool_call["args"]

                    if tool_name not in self.tools:
                        raise ValueError(f"Tool '{tool_name}' not found in agent's toolset.")

                    if tracer and tracer.enabled:
                        with tracer.trace_tool_execution(tool_name, args) as span:
                            tool_output = self.tools[tool_name].run(args)
                            if span:
                                span.set_tool_data(tool_name=tool_name, args=args, output=tool_output)
                    else:
                        tool_output = self.tools[tool_name].run(args)

                    # Store tool result in a structured way
                    self._add_to_memory("tool", {
                        "name": tool_name,
                        "args": args,
                        "output": tool_output
                    })

                    if self.stop_conditions.should_stop(step - 1, self.temporary_memory):
                        # Instead of returning generic message, return tool result
                        result = f"Tool result: {tool_output}"
                        self._sync_to_history()

                        if tracer and tracer.enabled and trace:
                            tracer.end_trace(trace.trace_id, output=result)

                        return result

                    # Build follow-up prompt with full memory context and separate tool result
                    conversation_history = "\n".join(
                        [f"{item['role'].capitalize()}: {item['content']}" if item['role'] != "tool"
                        else f"Tool '{item['content']['name']}' called with args:\n{item['content']['args']}\nOutput:\n{item['content']['output']}"
                        for item in self.temporary_memory]
                    )

                    # Render follow-up prompt using template
                    prompt = self._render_follow_up_prompt(
                        conversation_history=conversation_history,
                        has_tools=bool(self.tools)
                    )

                    continue  # Go to next loop iteration

                # Check if we should stop before returning (avoid returning JSON)
                if self.stop_conditions.should_stop(step, self.temporary_memory):
                    # Get the last meaningful output (not a tool call JSON)
                    for item in reversed(self.temporary_memory):
                        if item['role'] == 'tool':
                            result = f"Based on the analysis: {item['content']['output']}"
                            self._sync_to_history()

                            if tracer and tracer.enabled and trace:
                                tracer.end_trace(trace.trace_id, output=result)

                            return result
                    result = "Task completed with available information."
                    self._sync_to_history()

                    if tracer and tracer.enabled and trace:
                        tracer.end_trace(trace.trace_id, output=result)

                    return result

                # No tool call, return final answer
                self._sync_to_history()

                if tracer and tracer.enabled and trace:
                    tracer.end_trace(trace.trace_id, output=response)

                return response
        except Exception as e:
            # Sync history even on error
            self._sync_to_history()
            
            if tracer and tracer.enabled and trace:
                tracer.end_trace(trace.trace_id, error=e)
                
            raise e

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
