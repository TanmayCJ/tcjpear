# peargent/core/pool.py

"""
Pool module for orchestrating multiple agents.
Manages agent execution, routing, and shared state.
"""

from typing import List, Dict, Optional, Any
from .state import State
from .router import RouterFn, RouterResult


class Pool:
    """
    Orchestrates multiple agents with intelligent routing.

    The Pool manages a collection of agents, uses a router to decide which agent
    should act next, maintains shared state across all agents, and chains agent
    outputs as inputs to subsequent agents.

    Attributes:
        agents_dict (Dict): Mapping of agent names to Agent objects
        agents_names (List[str]): List of all agent names
        default_model: Default LLM model for agents without one
        router: Function or RoutingAgent that decides next agent
        max_iter (int): Maximum number of agent executions
        state (State): Shared conversation history and key-value store
    """
    def __init__(
        self,
        agents: List,
        default_model=None,
        router: Optional[RouterFn] = None,
        max_iter: int = 5,
        default_state: Optional[State] = None,
    ):
        # Assign default model to agents that don't have one
        for agent in agents:
            if agent.model is None and default_model is not None:
                agent.model = default_model

        self.agents_dict: Dict[str, any] = {a.name: a for a in agents}
        self.agents_names = list(self.agents_dict.keys())
        self.default_model = default_model
        self.router = router or (lambda state, call_count, last: RouterResult(None))
        self.max_iter = max_iter
        self.state = default_state or State()

        # If router is a RoutingAgent, provide it with agent objects for better context
        if hasattr(self.router, "agent_objects"):
            self.router.agent_objects = self.agents_dict

    def run(self, user_input: str) -> str:
        """
        Execute the multi-agent workflow.

        Iteratively routes to agents based on router decisions, chains outputs,
        and maintains shared state until completion or max iterations reached.

        Args:
            user_input (str): The initial user request or input

        Returns:
            str: The final assistant response from the last executed agent
        """
        self.state.add_message(role="user", content=user_input, agent=None)
        
        last_result = None
        call_count = 0
        current_input = user_input
        
        while call_count < self.max_iter:
            
            if hasattr(self.router, "decide"):  # RoutingAgent-like
                route_name = self.router.decide(self.state, last_result=last_result)
                route = RouterResult(route_name)
            else:  # Old style function-based router
                route = self.router(self.state, call_count=call_count, last_result=last_result)
                
            if not route or route.next_agent_name is None:
                break
            
            agent = self.agents_dict.get(route.next_agent_name)
            if not agent:
                raise ValueError(f"Router selected unknown agent '{route.next_agent_name}'")
            
            # Execute the selected agent
            agent_input = current_input
            output = agent.run(agent_input)

            # Store agent output in shared state
            self.state.add_message("assistant", str(output), agent=agent.name)
            last_result = {
                "agent": agent.name,
                "output": output,
                "tools_used": [m['content']['name'] for m in agent.temporary_memory if m.get('role') == 'tool'] if hasattr(agent, 'temporary_memory') else []
            }
            
            # Set the output as input for the next agent
            current_input = str(output)
            call_count += 1
            
        final = next((m["content"] for m in reversed(self.state.history) if m["role"] == "assistant"), "")
        return final