"""LiteLLM client wrapper for LLM API calls."""

import json
import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings
from app.core.telemetry import get_tracer, span_set_data

logger = logging.getLogger(__name__)
tracer = get_tracer(__name__)


@dataclass
class ChatMessage:
    """Chat message structure."""

    role: str  # system, user, assistant
    content: str


@dataclass
class ChatCompletionResponse:
    """Chat completion response from LLM."""

    content: str
    role: str
    model: str
    usage: dict[str, int] | None = None


class LLMClient:
    """
    LiteLLM client wrapper using OpenAI-compatible API.

    Usage:
        client = LLMClient()
        response = await client.chat_completion([
            ChatMessage(role="user", content="Hello!")
        ])
    """

    def __init__(
        self,
        base_url: str | None = None,
        api_key: str | None = None,
        default_model: str = "gemini-2.0-flash",
        timeout: float = 120.0,
    ):
        self.base_url = (base_url or settings.litellm_api_url).rstrip("/")
        self.api_key = api_key or settings.litellm_api_key
        self.default_model = default_model
        self.timeout = timeout

    def _get_headers(self) -> dict[str, str]:
        """Get request headers."""
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _format_messages(self, messages: list[ChatMessage]) -> list[dict[str, str]]:
        """Format messages for API request."""
        return [{"role": msg.role, "content": msg.content} for msg in messages]

    async def chat_completion(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        top_p: float | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        **kwargs: Any,
    ) -> ChatCompletionResponse:
        """
        Send chat completion request (non-streaming).

        Args:
            messages: List of chat messages
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty for token repetition
            presence_penalty: Presence penalty for new topics
            **kwargs: Additional parameters

        Returns:
            ChatCompletionResponse with generated content
        """
        model = model or self.default_model
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": False,
            **kwargs,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            # Add tracing if enabled
            if tracer:
                with tracer.start_as_current_span("llm.chat_completion") as span:
                    span_set_data(span, {
                        "model": model,
                        "message_count": len(messages),
                        "temperature": temperature,
                    })

                    response = await client.post(
                        url,
                        headers=self._get_headers(),
                        json=payload,
                    )
                    response.raise_for_status()
                    data = response.json()

                    # Add usage to span
                    if "usage" in data:
                        span_set_data(span, {"usage": data["usage"]})
            else:
                response = await client.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()

        choice = data["choices"][0]
        return ChatCompletionResponse(
            content=choice["message"]["content"],
            role=choice["message"]["role"],
            model=data.get("model", model),
            usage=data.get("usage"),
        )

    async def chat_completion_stream(
        self,
        messages: list[ChatMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        top_p: float | None = None,
        frequency_penalty: float | None = None,
        presence_penalty: float | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Send chat completion request with streaming.

        Args:
            messages: List of chat messages
            model: Model to use (defaults to default_model)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            top_p: Nucleus sampling parameter
            frequency_penalty: Frequency penalty for token repetition
            presence_penalty: Presence penalty for new topics
            **kwargs: Additional parameters

        Yields:
            Content chunks as they are generated
        """
        model = model or self.default_model
        url = f"{self.base_url}/chat/completions"

        payload = {
            "model": model,
            "messages": self._format_messages(messages),
            "temperature": temperature,
            "stream": True,
            **kwargs,
        }
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        if top_p is not None:
            payload["top_p"] = top_p
        if frequency_penalty is not None:
            payload["frequency_penalty"] = frequency_penalty
        if presence_penalty is not None:
            payload["presence_penalty"] = presence_penalty

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream(
                "POST",
                url,
                headers=self._get_headers(),
                json=payload,
            ) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    # SSE format: data: {...}
                    if line.startswith("data: "):
                        data_str = line[6:]  # Remove "data: " prefix

                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            data = json.loads(data_str)
                            choices = data.get("choices", [])
                            if choices:
                                delta = choices[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse SSE data: {data_str}")
                            continue

    async def health_check(self) -> bool:
        """Check if LiteLLM is reachable."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"LiteLLM health check failed: {e}")
            return False


# Singleton instance
llm_client = LLMClient()
