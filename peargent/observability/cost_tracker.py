# peargent/observability/cost_tracker.py

"""Cost tracking for LLM API calls.

Tracks token usage and calculates costs based on model pricing.
"""
    
from typing import Dict, Tuple, Optional
    
PRICING = {
    "gpt-4": {"prompt": 30.0, "completion": 60.0},
    "gpt-4.1": { "prompt": 2.0, "completion": 8.0 },
    "gpt-4.1-mini": { "prompt": 0.4, "completion": 1.6 },
    "gpt-4.1-nano": { "prompt": 0.1, "completion": 0.4 },
    "gpt-4o": { "prompt": 5.0, "completion": 15.0 },

    "claude-4.1-opus": { "prompt": 15.0, "completion": 75.0 },
    "claude-4.1-sonnet": { "prompt": 3.0, "completion": 15.0 },
    "claude-4.1-haiku": { "prompt": 1.0, "completion": 5.0 },

    "mistral-large": { "prompt": 2.0, "completion": 6.0 },
    "mistral-medium": { "prompt": 1.0, "completion": 3.0 },
    "mistral-small": { "prompt": 0.2, "completion": 0.6 },

    "llama-3.3-70b-versatile": { "prompt": 0.59, "completion": 0.79 },
    "llama-3.1-8b": { "prompt": 0.05, "completion": 0.08 },
    "mixtral-8x7b": { "prompt": 0.24, "completion": 0.24 },
    "gemma-7b": { "prompt": 0.07, "completion": 0.07 },

    "gemini-2.0-pro": { "prompt": 0.5, "completion": 1.5 },
    "gemini-2.0-vision": { "prompt": 0.5, "completion": 1.5 }
}

class CostTracker:
    """Tracks token usage and calculates API costs.
    
    Uses tiktoken for accurate token counting when available
    falls back to estimation otherwise.
    """
    
    def __init__(self, use_tiktoken: bool = True):
        """Initialize cost tracker.

        Args:
            use_tiktoken (bool, optional): Whether to use tiktoken for token counting. Defaults to True.
        """
        self.use_tiktoken = use_tiktoken
        self._tiktoken_available = False
        self._encoding_cache: Dict[str, any] = {}
        
        if use_tiktoken:
            try:
                import tiktoken
                self._tiktoken = tiktoken
                self._tiktoken_available = True
            except ImportError:
                print("Warning: tiktoken not available, falling back to estimation.")
                self._tiktoken_available = False
    
    def count_tokens(self, text: str, model: str = "gpt-4") -> int:
        """Count tokens in text.

        Args:
            text (str): Text to count tokens for
            model (str, optional): Model name. 

        Returns:
            Number of tokens in text.
        """
        if text is None or text == "":
            return 0

        if self._tiktoken_available:
            return self._count_tokens_tiktoken(text, model)
        else:
            return self._count_tokens_estimate(text)
        
    def _count_tokens_tiktoken(self, text: str, model: str) -> int:
        """Count tokens using tiktoken library."""
        try:
            encoding = self._get_encoding(model)
            return len(encoding.encode(text))
        except Exception as e:
            # print(f"Error counting tokens with tiktoken: {e}")
            return self._count_tokens_estimate(text)
    
    def _get_encoding(self, model: str):
        """Get tiktoken encoding for model, with caching."""
        if model in self._encoding_cache:
            return self._encoding_cache[model]
        
        try:
            if "gpt-4" in model or "gpt-3.5" in model:
                encoding = self._tiktoken.encoding_for_model("gpt-4")
            elif "claude" in model:
                encoding = self._tiktoken.get_encoding("gpt-4")
            else:
                encoding = self._tiktoken.get_encoding("cl100k_base")
            self._encoding_cache[model] = encoding
            return encoding
        except Exception as e:
            encoding = self._tiktoken.get_encoding("cl100k_base")
            self._encoding_cache[model] = encoding
            return encoding
    
    def _count_tokens_estimate(self, text: str) -> int:
        """Estimate token count (4 characters per token).
            Uses simple heuristic of 4 characters per token.
        """
        words = text.split()
        return int(len(text) / 4)
    
    def calculate_cost(self,  prompt_tokens: int, completion_tokens: int, model: str,) -> float:
        """Calculate cost based on token usage and model pricing.

        Args:
            model (str): Model name
            prompt_tokens (int): Number of prompt tokens
            completion_tokens (int): Number of completion tokens
        Returns:
            Cost in USD.
        """
        model_key = self._normalize_model_name(model)
        
        pricing = self._get_pricing(model_key)
        if pricing is None:
            return 0.0
        
        prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
        completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]
        
        return prompt_cost + completion_cost
    
    def count_and_calculate(
        self,
        prompt: str,
        completion: str,
        model: str
    ) -> Tuple[int, int, float]:
        """Count tokens and calculate cost for given prompt and completion.

        Args:
            prompt (str): Prompt text
            completion (str): Completion text
            model (str): Model name
            
        Returns:
            Tuple of (prompt_tokens, completion_tokens, cost)
        """
        prompt_tokens = self.count_tokens(prompt, model)
        completion_tokens = self.count_tokens(completion, model)
        cost = self.calculate_cost(prompt_tokens, completion_tokens, model)
        
        return prompt_tokens, completion_tokens, cost
    
    def _normalize_model_name(self, model: str) -> str:
        """Normalize model name for pricing lookup."""
        model_lower = model.lower()
        
        for base_model in PRICING.keys():
            if model_lower.startswith(base_model):
                return base_model
        return model_lower
    
    def _get_pricing(self, model: str) -> Optional[Dict[str, float]]:
        """Get pricing for model."""
        return PRICING.get(model)
    
    def add_custom_pricing(
        self,
        model: str,
        prompt_price: float,
        completion_price: float
    ):
        """Add or update custom pricing for a model.
        Args:
            model (str): Model name
            prompt_price (float): Price per million prompt tokens
            completion_price (float): Price per million completion tokens
        """
        PRICING[model] = {
            "prompt": prompt_price,
            "completion": completion_price
        }
    
    def get_pricing(self, model: str) -> Optional[Dict[str, float]]:
        """Get pricing for a model.
        
        Args:
            model (str): Model name
            
        Returns:
            Pricing dictionary or None if not found.
        """
        model_key = self._normalize_model_name(model)
        return self._get_pricing(model_key)
    
# Global cost tracker instance
_global_cost_tracker: Optional[CostTracker] = None

def get_cost_tracker() -> CostTracker:
    """Get global cost tracker instance."""
    global _global_cost_tracker
    if _global_cost_tracker is None:
        _global_cost_tracker = CostTracker()
    return _global_cost_tracker

def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens using global cost tracker.
    
    Args:
        text (str): Text to count tokens for
        model (str, optional): Model name. Defaults to "gpt-4".
    
    Returns:
        Number of tokens in text.    
    """
    tracker = get_cost_tracker()
    return tracker.count_tokens(text, model)

def calculate_cost(
    prompt_tokens: int,
    completion_tokens: int,
    model: str
) -> float:
    """Calculate cost using global cost tracker.
    
    Args:
        prompt_tokens (int): Number of prompt tokens
        completion_tokens (int): Number of completion tokens
        model (str): Model name
        
    Returns:
        Cost in USD.
    """
    tracker = get_cost_tracker()
    return tracker.calculate_cost(prompt_tokens, completion_tokens, model
)