"""Integration tests for infra.llm_client against a real local HTTP server.

A real ``ThreadingHTTPServer`` serves OpenAI-compatible responses; the client
uses its default HTTP transport (no injected transport), exercising the full
request path: POST payload, Bearer auth, response parsing and error mapping.
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

import pytest

from core.exceptions import AIExtractionFailedError
from infra.llm_client import LLMClient

pytestmark = pytest.mark.asyncio


class _OkHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802 - stdlib hook
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = json.dumps(
            {"choices": [{"message": {"content": "hello from server"}}]}
        ).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


class _ErrorHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = b'{"error": "boom"}'
        self.send_response(500)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


class _MalformedHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:  # noqa: N802
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        body = b"not json"
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        pass


def _serve(
    handler_type: type[BaseHTTPRequestHandler],
) -> tuple[ThreadingHTTPServer, int]:
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_type)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, int(server.server_address[1])


def _client(port: int) -> LLMClient:
    return LLMClient(
        base_url=f"http://127.0.0.1:{port}/v1",
        api_key="test-key",
        model="gpt-test",
        timeout_seconds=5.0,
    )


async def test_complete_against_real_server() -> None:
    server, port = _serve(_OkHandler)
    try:
        client = _client(port)
        text = await client.complete("hi")
        assert text == "hello from server"
    finally:
        server.shutdown()


async def test_http_error_maps_to_aiextraction_failed() -> None:
    server, port = _serve(_ErrorHandler)
    try:
        client = _client(port)
        with pytest.raises(AIExtractionFailedError, match="HTTP 500"):
            await client.complete("hi")
    finally:
        server.shutdown()


async def test_malformed_body_maps_to_aiextraction_failed() -> None:
    server, port = _serve(_MalformedHandler)
    try:
        client = _client(port)
        with pytest.raises(AIExtractionFailedError, match="not usable"):
            await client.complete("hi")
    finally:
        server.shutdown()
