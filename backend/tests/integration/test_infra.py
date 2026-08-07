"""Integration tests for infra/supabase.py."""
from __future__ import annotations

import pytest

from infra.supabase import (
    create_service_client,
    get_service_client,
    reset_service_client,
)


def test_service_client_is_singleton() -> None:
    reset_service_client()
    first = get_service_client()
    second = get_service_client()
    assert first is second
    reset_service_client()


def test_create_service_client_fresh() -> None:
    reset_service_client()
    client = create_service_client()
    assert client is not None
    reset_service_client()


def test_get_service_client_after_reset() -> None:
    reset_service_client()
    first = get_service_client()
    reset_service_client()
    second = get_service_client()
    assert first is not second
