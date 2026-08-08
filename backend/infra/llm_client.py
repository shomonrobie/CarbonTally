"""OpenAI/Anthropic-compatible LLM client (Backend v2.1 §7, prep-pack
``infra/llm_client.py``).

A small, typed HTTP client for chat-completions-style endpoints, used by the AI
extraction engine. The default transport performs a real HTTP request with the
standard library (executed off the event loop); a transport may be injected for
tests. Every failure — connection error, non-2xx response, malformed body —
surfaces as :class:`core.exceptions.AIExtractionFailedError` (HTTP 502).

Dependency rules: this module imports only from ``core`` (exceptions). It
contains no business logic.
"""
from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Optional

from core.exceptions import AIExtractionFailedError

#: Default timeout for a single LLM request.
DEFAULT_TIMEOUT_SECONDS = 30.0

#: The chat-completions request payload (OpenAI-compatible schema).
LLMRequest = dict[str, object]


@dataclass(frozen=True, slots=True)
class ChatCompletionResponse:
    """The parsed assistant answer from a chat-completions call."""

    text: str
    finish_reason: str = "stop"


#: A transport maps a request payload to a parsed response (synchronous; the
#: client runs it off the event loop).
LLMTransport = Callable[[LLMRequest], ChatCompletionResponse]


class LLMClient:
    """Typed client for an OpenAI/Anthropic-compatible chat-completions API.

    Args:
        base_url: Endpoint root, e.g. ``https://api.openai.com/v1``. The client
            POSTs to ``<base_url>/chat/completions``.
        api_key: Bearer token for the endpoint.
        model: Model identifier sent in the payload.
        timeout_seconds: Per-request timeout.
        transport: Optional transport override (default: real HTTP via the
            standard library). Used by tests.
    """

    def __init__(
        self,
        *,
        base_url: str,
        api_key: str,
        model: str,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        transport: Optional[LLMTransport] = None,
    ) -> None:
        if not base_url:
            raise ValueError("base_url must not be empty")
        if not api_key:
            raise ValueError("api_key must not be empty")
        if not model:
            raise ValueError("model must not be empty")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be > 0")
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._transport = transport or self._default_transport()

    @property
    def base_url(self) -> str:
        """The configured endpoint root."""
        return self._base_url

    @property
    def model(self) -> str:
        """The configured model identifier."""
        return self._model

    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: int = 512,
    ) -> str:
        """Call the chat-completions API and return the assistant text.

        Args:
            prompt: The user message.
            system: Optional system message.
            temperature: Sampling temperature (0.0 = deterministic).
            max_tokens: Maximum completion tokens.

        Returns:
            The assistant's ``content`` string.

        Raises:
            AIExtractionFailedError: On transport failure, non-2xx response or
                an unusable response body.
        """
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        payload: LLMRequest = {
            "model": self._model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        try:
            response = await asyncio.to_thread(self._transport, payload)
        except AIExtractionFailedError:
            raise
        except Exception as exc:  # noqa: BLE001 - wrap every transport failure
            raise AIExtractionFailedError(
                "LLM request failed",
                details={"error": type(exc).__name__, "message": str(exc)},
            ) from exc
        return response.text

    def _default_transport(self) -> LLMTransport:
        def transport(payload: LLMRequest) -> ChatCompletionResponse:
            url = f"{self._base_url}/chat/completions"
            body = json.dumps(payload).encode("utf-8")
            request = urllib.request.Request(
                url,
                data=body,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(
                    request, timeout=self._timeout_seconds
                ) as response:
                    raw = response.read().decode("utf-8", errors="replace")
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")[:500]
                raise AIExtractionFailedError(
                    f"LLM API returned HTTP {exc.code}",
                    details={"status": exc.code, "body": detail},
                ) from exc
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                raise AIExtractionFailedError(
                    "LLM API connection failed",
                    details={
                        "error": type(exc).__name__,
                        "message": str(exc),
                    },
                ) from exc
            try:
                data = json.loads(raw)
                text = str(data["choices"][0]["message"]["content"])
            except (KeyError, IndexError, TypeError, ValueError) as exc:
                raise AIExtractionFailedError(
                    "LLM response was not usable",
                    details={"body": raw[:500]},
                ) from exc
            return ChatCompletionResponse(text=text)

        return transport

