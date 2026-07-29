"""Unified LLM provider abstraction supporting Groq and Anthropic.

This module provides a unified interface for LLM calls, supporting both
Groq (primary, for speed) and Anthropic (fallback, for reasoning).

Usage:
    provider = get_llm_provider()

    # Completions
    response = provider.message(
        model="groq",  # or "claude"
        messages=[{"role": "user", "content": "..."}],
        system="...",
        max_tokens=1024,
    )

    # Tool use
    response = provider.message(
        model="groq",
        messages=[...],
        tools=[...],
        tool_choice="auto",
    )
"""

import os
from typing import Any, Optional
from enum import Enum


class LLMProvider(Enum):
    """Supported LLM providers."""
    GROQ = "groq"
    ANTHROPIC = "anthropic"


def get_llm_provider() -> "UnifiedLLMProvider":
    """Get the unified LLM provider (Groq primary, Anthropic fallback)."""
    groq_key = os.getenv("GROQ_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    # Priority: Groq > Anthropic
    if groq_key:
        return GroqProvider(groq_key)
    elif anthropic_key:
        return AnthropicProvider(anthropic_key)
    else:
        raise ValueError(
            "No LLM API key found. Set GROQ_API_KEY or ANTHROPIC_API_KEY in .env"
        )


class UnifiedLLMProvider:
    """Base class for unified LLM provider interface."""

    def message(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
    ) -> dict:
        """Send a message to the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model to use (provider-specific)
            system: System prompt
            max_tokens: Max response tokens
            tools: Optional list of tool definitions
            tool_choice: Tool selection strategy ("auto", "required", tool name, or None)
            temperature: Sampling temperature

        Returns:
            Response dict with 'content', 'stop_reason', 'usage' keys
        """
        raise NotImplementedError


class GroqProvider(UnifiedLLMProvider):
    """Groq LLM provider (primary for speed)."""

    def __init__(self, api_key: str):
        """Initialize Groq provider."""
        try:
            import groq
        except ImportError:
            raise ImportError("groq package not installed. Install with: pip install groq")

        self.client = groq.Groq(api_key=api_key)
        self.provider = LLMProvider.GROQ

    def message(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
    ) -> dict:
        """Send message to Groq."""
        # Groq defaults to mixtral (fast, good reasoning)
        model = model or "mixtral-8x7b-32768"

        # Build request
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            # Groq doesn't have native system param; inject into first message
            if messages and messages[0]["role"] == "system":
                messages[0]["content"] = system
            else:
                messages.insert(0, {"role": "system", "content": system})

        if tools:
            kwargs["tools"] = [{"type": "function", "function": tool} for tool in tools]
            if tool_choice:
                if tool_choice == "required":
                    kwargs["tool_choice"] = "any"
                elif tool_choice == "auto":
                    kwargs["tool_choice"] = "auto"
                else:
                    # Specific tool
                    kwargs["tool_choice"] = {"type": "function", "function": {"name": tool_choice}}

        # Call Groq
        response = self.client.chat.completions.create(**kwargs)

        # Normalize response
        return self._normalize_response(response)

    def _normalize_response(self, response: Any) -> dict:
        """Normalize Groq response to common format."""
        content = ""
        tool_use = None
        stop_reason = response.choices[0].finish_reason

        if response.choices[0].message.content:
            content = response.choices[0].message.content

        # Handle tool calls
        if response.choices[0].message.tool_calls:
            tool_call = response.choices[0].message.tool_calls[0]
            tool_use = {
                "type": "tool_use",
                "id": tool_call.id,
                "name": tool_call.function.name,
                "input": tool_call.function.arguments,
            }

        return {
            "content": content,
            "tool_use": tool_use,
            "stop_reason": stop_reason,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            },
        }


class AnthropicProvider(UnifiedLLMProvider):
    """Anthropic LLM provider (fallback for reasoning)."""

    def __init__(self, api_key: str):
        """Initialize Anthropic provider."""
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package not installed. Install with: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.provider = LLMProvider.ANTHROPIC

    def message(
        self,
        messages: list[dict],
        model: Optional[str] = None,
        system: Optional[str] = None,
        max_tokens: int = 1024,
        tools: Optional[list[dict]] = None,
        tool_choice: Optional[str] = None,
        temperature: float = 0.7,
    ) -> dict:
        """Send message to Anthropic."""
        # Anthropic defaults to Sonnet (better reasoning)
        model = model or "claude-3-5-sonnet-20241022"

        # Build request
        kwargs = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if system:
            kwargs["system"] = system

        if tools:
            # Convert to Anthropic format
            anthropic_tools = []
            for tool in tools:
                anthropic_tools.append({
                    "name": tool.get("name", ""),
                    "description": tool.get("description", ""),
                    "input_schema": tool.get("input_schema", {}),
                })
            kwargs["tools"] = anthropic_tools

            if tool_choice:
                if tool_choice == "required":
                    kwargs["tool_choice"] = {"type": "auto"}
                elif tool_choice == "auto":
                    kwargs["tool_choice"] = {"type": "auto"}
                else:
                    # Specific tool
                    kwargs["tool_choice"] = {"type": "tool", "name": tool_choice}

        # Call Anthropic
        response = self.client.messages.create(**kwargs)

        # Normalize response
        return self._normalize_response(response)

    def _normalize_response(self, response: Any) -> dict:
        """Normalize Anthropic response to common format."""
        content = ""
        tool_use = None
        stop_reason = response.stop_reason

        for block in response.content:
            if hasattr(block, "text"):
                content = block.text
            elif block.type == "tool_use":
                tool_use = {
                    "type": "tool_use",
                    "id": block.id,
                    "name": block.name,
                    "input": block.input,
                }

        return {
            "content": content,
            "tool_use": tool_use,
            "stop_reason": stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        }
