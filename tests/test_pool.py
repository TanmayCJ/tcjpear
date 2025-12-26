"""
Tests for the Pool class and create_pool functionality.
Tests pool creation, agent orchestration, routing, and state management.
"""

from typing import Any, Dict

import pytest

from peargent import create_agent, create_pool, create_tool, RouterResult, State


class MockModel:
    """Mock LLM model for testing without API keys."""

    def __init__(self, model_name: str = "mock-model", **kwargs):
        self.model_name = model_name
        self.kwargs = kwargs

    def generate(self, prompt: str, **kwargs) -> str:
        return f"Response from {self.model_name}"


class TestPoolCreation:
    """Test pool creation and initialization."""

    def test_create_pool_with_multiple_agents(self) -> None:
        """Test creating a pool with multiple agents."""
        agent1 = create_agent(
            name="agent1",
            description="First agent",
            persona="You are helpful",
            model=MockModel(),
        )

        agent2 = create_agent(
            name="agent2",
            description="Second agent",
            persona="You are helpful",
            model=MockModel(),
        )

        pool = create_pool(agents=[agent1, agent2])

        assert len(pool.agents_dict) == 2
        assert "agent1" in pool.agents_dict
        assert "agent2" in pool.agents_dict

    def test_pool_with_default_model(self) -> None:
        """Test pool assigns default model to agents without one."""
        default_model = MockModel("default-model")
        
        agent1 = create_agent(
            name="agent1",
            description="Agent without model",
            persona="You are helpful",
            model=None,
        )

        pool = create_pool(agents=[agent1], default_model=default_model)

        assert pool.agents_dict["agent1"].model is not None
        assert pool.agents_dict["agent1"].model.model_name == "default-model"


class TestPoolConfiguration:
    """Test pool configuration options."""

    def test_pool_respects_max_iterations(self) -> None:
        """Test that pool respects max_iter configuration."""
        agent1 = create_agent(
            name="agent1",
            description="Test agent",
            persona="You are helpful",
            model=MockModel(),
        )

        pool = create_pool(agents=[agent1], max_iter=10)

        assert pool.max_iter == 10

    def test_pool_with_tracing_enabled(self) -> None:
        """Test pool with tracing enabled."""
        agent1 = create_agent(
            name="agent1",
            description="Test agent",
            persona="You are helpful",
            model=MockModel(),
        )

        agent2 = create_agent(
            name="agent2",
            description="Test agent",
            persona="You are helpful",
            model=MockModel(),
        )

        pool = create_pool(agents=[agent1, agent2], tracing=True)

        assert pool.tracing is True


class TestPoolRouter:
    """Test pool routing functionality."""

    def test_pool_with_custom_router_function(self) -> None:
        """Test pool with custom router function."""
        agent1 = create_agent(
            name="agent1",
            description="First agent",
            persona="You are helpful",
            model=MockModel(),
        )

        agent2 = create_agent(
            name="agent2",
            description="Second agent",
            persona="You are helpful",
            model=MockModel(),
        )

        def custom_router(state, call_count, last_result):
            """Simple router that alternates between agents."""
            if call_count == 0:
                return RouterResult("agent1")
            return RouterResult(None)

        pool = create_pool(
            agents=[agent1, agent2],
            router=custom_router,
            max_iter=3,
        )

        assert pool.router is not None
        assert callable(pool.router)


class TestPoolState:
    """Test pool shared state management."""

    def test_pool_with_shared_state(self) -> None:
        """Test pool with shared state across agents."""
        agent1 = create_agent(
            name="agent1",
            description="First agent",
            persona="You are helpful",
            model=MockModel(),
        )

        agent2 = create_agent(
            name="agent2",
            description="Second agent",
            persona="You are helpful",
            model=MockModel(),
        )

        custom_state = State()
        pool = create_pool(
            agents=[agent1, agent2],
            default_state=custom_state,
        )

        assert pool.state is not None
        assert pool.state == custom_state

    def test_pool_creates_state_automatically(self) -> None:
        """Test that pool creates state automatically if not provided."""
        agent1 = create_agent(
            name="agent1",
            description="Test agent",
            persona="You are helpful",
            model=MockModel(),
        )

        pool = create_pool(agents=[agent1])

        assert pool.state is not None
        assert isinstance(pool.state, State)
