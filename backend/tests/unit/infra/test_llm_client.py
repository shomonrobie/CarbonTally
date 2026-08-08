"""Unit tests for infra.llm_client."""
from __future__ import annotations

import pytest

from core.exceptions import AIExtractionFailedError
from infra.llm_client import ChatCompletionResponse, LLMClient


class TestLLMClient:
    async def test_complete_returns_transport_text(self) -> None:
        def transport(payload: dict[str, object]) -> ChatCompletionResponse:
            return ChatCompletionResponse(text="hello from llm")

        client = LLMClient(
            base_url="https://llm.test/v1",
            api_key="key",
            model="gpt-test",
            transport=transport,
        )
        result = await client.complete("hi")
        assert result == "hello from llm"

    async def test_payload_shape(self) -> None:
        captured: dict[str, object] = {}

        def transport(payload: dict[str, object]) -> ChatCompletionResponse:
            captured.update(payload)
            return ChatCompletionResponse(text="ok")

        client = LLMClient(
            base_url="https://llm.test/v1",
            api_key="key",
            model="gpt-test",
            transport=transport,
        )
        await client.complete("hi", system="be precise", temperature=0.0, max_tokens=128)
        assert captured["model"] == "gpt-test"
        assert captured["temperature"] == 0.0
        assert captured["max_tokens"] == 128
        messages = captured["messages"]
        assert isinstance(messages, list)
        assert messages == [
            {"role": "system", "content": "be precise"},
            {"role": "user", "content": "hi"},
        ]

    async def test_no_system_message_when_omitted(self) -> None:
        captured: dict[str, object] = {}

        def transport(payload: dict[str, object]) -> ChatCompletionResponse:
            captured.update(payload)
            return ChatCompletionResponse(text="ok")

        client = LLMClient(
            base_url="https://llm.test/v1",
            api_key="key",
            model="gpt-test",
            transport=transport,
        )
        await client.complete("hi")
        messages = captured["messages"]
        assert isinstance(messages, list)
        assert messages == [{"role": "user", "content": "hi"}]

    async def test_transport_aiextraction_error_propagates(self) -> None:
        def transport(payload: dict[str, object]) -> ChatCompletionResponse:
            raise AIExtractionFailedError("upstream failed")

        client = LLMClient(
            base_url="https://llm.test/v1",
            api_key="key",
            model="gpt-test",
            transport=transport,
        )
        with pytest.raises(AIExtractionFailedError, match="upstream failed"):
            await client.complete("hi")

    async def test_transport_generic_error_is_wrapped(self) -> None:
        def transport(payload: dict[str, object]) -> ChatCompletionResponse:
            raise RuntimeError("boom")

        client = LLMClient(
            base_url="https://llm.test/v1",
            api_key="key",
            model="gpt-test",
            transport=transport,
        )
        with pytest.raises(AIExtractionFailedError, match="LLM request failed"):
            await client.complete("hi")

    def test_constructor_validation(self) -> None:
        with pytest.raises(ValueError, match="base_url"):
            LLMClient(base_url="", api_key="k", model="m")
        with pytest.raises(ValueError, match="api_key"):
            LLMClient(base_url="https://llm.test", api_key="", model="m")
        with pytest.raises(ValueError, match="model"):
            LLMClient(base_url="https://llm.test", api_key="k", model="")
        with pytest.raises(ValueError, match="timeout_seconds"):
            LLMClient(base_url="https://llm.test", api_key="k", model="m", timeout_seconds=0)

    def test_properties(self) -> None:
        client = LLMClient(
            base_url="https://llm.test/v1/",
            api_key="k",
            model="gpt-test",
            transport=lambda payload: ChatCompletionResponse(text="x"),
        )
        assert client.base_url == "https://llm.test/v1"
        assert client.model == "gpt-test"
