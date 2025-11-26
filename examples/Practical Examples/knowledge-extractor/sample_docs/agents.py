"""
Agent System Implementation

This module contains the core agent classes and routing logic.
"""

class BaseAgent:
    """Base class for all agents"""

    def __init__(self, name, model):
        self.name = name
        self.model = model
        self.memory = []

    def process(self, input_text):
        """Process input and return response"""
        # Add to memory
        self.memory.append({"role": "user", "content": input_text})

        # Generate response
        response = self.model.generate(input_text)

        # Store response
        self.memory.append({"role": "assistant", "content": response})

        return response


class RouterAgent(BaseAgent):
    """Routes requests to appropriate agents"""

    def __init__(self, agents):
        super().__init__("Router", None)
        self.agents = agents

    def route(self, input_text):
        """Determine which agent should handle this input"""
        # Simple keyword-based routing
        if "technical" in input_text.lower():
            return self.agents["technical"]
        elif "creative" in input_text.lower():
            return self.agents["creative"]
        else:
            return self.agents["general"]


class Memory:
    """Manages conversation history"""

    def __init__(self, max_size=100):
        self.max_size = max_size
        self.history = []

    def add(self, message):
        """Add message to history"""
        self.history.append(message)
        if len(self.history) > self.max_size:
            self.history.pop(0)

    def get_context(self, n=10):
        """Get last n messages"""
        return self.history[-n:]

    def clear(self):
        """Clear all history"""
        self.history = []
