"""
Configuration classes for peargent.

This module provides configuration classes for agents and history management.
"""

from typing import Optional, Union, Any
from peargent.core.history import ConversationHistory, StorageType, InMemory, HistoryStore


class HistoryConfig:
    """
    Configuration for agent history management.

    This class provides a clean DSL for configuring conversation history with
    automatic context management. It intelligently handles which parameters are
    needed based on the strategy.

    Examples:
        # Simple trim strategy (no summarize_model needed)
        config = HistoryConfig(
            auto_manage_context=True,
            max_context_messages=15,
            strategy="trim_last",
            store=File(storage_dir="./conversations")
        )

        # Smart or summarize strategy (summarize_model auto-inferred or explicit)
        config = HistoryConfig(
            auto_manage_context=True,
            max_context_messages=20,
            strategy="smart",  # Will use agent's model if summarize_model not provided
            store=Memory()
        )

        # Explicit summarize model for smart/summarize strategies
        config = HistoryConfig(
            auto_manage_context=True,
            strategy="summarize",
            summarize_model=groq("llama-3.1-8b-instant"),  # Use faster model for summaries
            store=Sqlite(database_path="./chat.db")
        )

        # Use existing history instance
        history = create_history(Memory())
        config = HistoryConfig(
            auto_manage_context=True,
            store=history  # Pass existing ConversationHistory
        )
    """

    def __init__(
        self,
        auto_manage_context: bool = False,
        max_context_messages: int = 20,
        strategy: str = "smart",
        summarize_model: Optional[Any] = None,
        store: Union[StorageType, ConversationHistory, HistoryStore, None] = None
    ):
        """
        Initialize history configuration.

        Args:
            auto_manage_context: Enable automatic context window management (default: False)
            max_context_messages: Maximum messages before auto-management triggers (default: 20)
            strategy: Context management strategy (default: "smart")
                     Options:
                     - "smart": Intelligently chooses between trim and summarize
                     - "trim_last": Remove oldest messages (fast, no LLM needed)
                     - "trim_first": Keep oldest messages
                     - "summarize": Summarize old messages (requires LLM)
            summarize_model: Optional LLM model for summarization (only needed for "summarize" strategy)
                           If not provided and strategy needs it, agent's model will be used
            store: Storage backend configuration or existing history instance
                  Can be:
                  - StorageType instance: InMemory(), File(), Sqlite(), Postgresql(), Redis()
                  - HistoryStore instance: Custom storage backend (e.g., CustomHistoryStore())
                  - ConversationHistory instance: Existing history object
                  - None: Defaults to InMemory()

        Notes:
            - summarize_model is ONLY used when strategy is "summarize" or "smart" (and smart decides to summarize)
            - For "trim_last" or "trim_first", summarize_model is ignored (trim doesn't need an LLM)
            - If strategy needs summarization and summarize_model is None, the agent's model will be used
        """
        self.auto_manage_context = auto_manage_context
        self.max_context_messages = max_context_messages
        self.strategy = strategy
        self.summarize_model = summarize_model
        self.store = store

        # Validate strategy
        valid_strategies = ["smart", "trim_last", "trim_first", "summarize", "first_last"]
        if strategy not in valid_strategies:
            raise ValueError(
                f"Invalid strategy '{strategy}'. Must be one of: {', '.join(valid_strategies)}"
            )

        # Warn if summarize_model is provided but not needed
        if summarize_model is not None and strategy in ["trim_last", "trim_first", "first_last"]:
            import warnings
            warnings.warn(
                f"summarize_model is provided but will be ignored with strategy='{strategy}'. "
                f"Trim strategies don't use LLMs. Remove summarize_model to clean up your config.",
                UserWarning
            )

    def create_history(self) -> ConversationHistory:
        """
        Create a ConversationHistory instance from this configuration.

        Returns:
            ConversationHistory instance

        Raises:
            ValueError: If store configuration is invalid
        """
        # If store is already a ConversationHistory, return it
        if isinstance(self.store, ConversationHistory):
            return self.store

        # If store is None, default to InMemory
        if self.store is None:
            self.store = InMemory()

        # If store is a HistoryStore (custom storage), wrap it in ConversationHistory
        if isinstance(self.store, HistoryStore):
            return ConversationHistory(store=self.store)

        # If store is a StorageType, create history from it
        if isinstance(self.store, StorageType):
            from peargent import create_history
            return create_history(store_type=self.store)

        raise ValueError(
            f"store must be a StorageType instance, HistoryStore instance, ConversationHistory instance, or None. "
            f"Got: {type(self.store)}"
        )

    def __repr__(self) -> str:
        """String representation of the config."""
        return (
            f"HistoryConfig("
            f"auto_manage_context={self.auto_manage_context}, "
            f"max_context_messages={self.max_context_messages}, "
            f"strategy='{self.strategy}', "
            f"summarize_model={self.summarize_model}, "
            f"store={self.store})"
        )
