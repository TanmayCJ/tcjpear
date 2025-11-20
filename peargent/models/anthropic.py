# peargent/models/anthropic.py

import os
import requests
from typing import Optional, Dict, Iterator
from .base import BaseModel

class AnthropicModel(BaseModel):
    ENDPOINT_URL = "https://api.anthropic.com/v1/messages"
    
    def __init__(
        self,
        model_name: str = "claude-3-5-sonnet-20241022",
        parameters: Optional[Dict] = None,
        api_key: Optional[str] = None,
        endpoint_url: Optional[str] = None
    ):
        super().__init__(model_name, parameters)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise EnvironmentError("Anthropic API key not found. Set ANTHROPIC_API_KEY in environment or pass `api_key=`.")
        self.endpoint_url = endpoint_url or self.ENDPOINT_URL

    def generate(self, prompt: str) -> str:
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Build messages array
        messages = []
        
        # Add system message if provided
        system_prompt = self.parameters.get("system_prompt", "")
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        body = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.parameters.get("max_tokens", 1024),
            "temperature": self.parameters.get("temperature", 0.7)
        }
        
        # Add system prompt if provided
        if system_prompt:
            body["system"] = system_prompt
        
        response = requests.post(self.endpoint_url, headers=headers, json=body)
        
        if response.status_code != 200:
            raise RuntimeError(f"Anthropic API error: {response.status_code}, {response.text}")
        
        result = response.json()
        return result.get("content", [{}])[0].get("text", "")

    def stream(self, prompt: str) -> Iterator[str]:
        """
        Stream text completion from Anthropic API.
        """
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        # Build messages array
        messages = []
        
        # Add system message if provided
        system_prompt = self.parameters.get("system_prompt", "")
        
        # Add user message
        messages.append({"role": "user", "content": prompt})
        
        body = {
            "model": self.model_name,
            "messages": messages,
            "max_tokens": self.parameters.get("max_tokens", 1024),
            "temperature": self.parameters.get("temperature", 0.7),
            "stream": True
        }
        
        # Add system prompt if provided
        if system_prompt:
            body["system"] = system_prompt
        
        response = requests.post(self.endpoint_url, headers=headers, json=body, stream=True)
        
        if response.status_code != 200:
            raise RuntimeError(f"Anthropic API error: {response.status_code}, {response.text}")
        
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data == '[DONE]':
                        break
                    try:
                        import json
                        event = json.loads(data)
                        if event.get('type') == 'content_block_delta':
                            delta = event.get('delta', {})
                            if delta.get('type') == 'text_delta':
                                text = delta.get('text', '')
                                if text:
                                    yield text
                    except json.JSONDecodeError:
                        continue