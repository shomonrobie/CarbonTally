"""P6-2F E2E fixtures — the real FastAPI app over the in-memory world.

Reuses the production composition root (``api.router.create_app``) and overrides
only the leaf dependencies (auth user, repositories, audit logger, event bus,
search index). No database is opened; no production data is touched. Each test
gets a fresh ``InMemoryWorld`` so the state is fully resettable.
"""
from __future__ import annotations

import pytest
from fastapi import HTTPException, status
from starlette.testclient import TestClient

from api.dependencies import (
    get_audit_logger,
    get_current_user,
    get_event_bus,
    get_factor_search_index,
    get_repositories,
)
from api.router import create_app
from infra.audit_logger import AuditLogger
from infra.event_bus import EventBus
from infra.search_index import FactorSearchIndex

from tests.unit.api.fakes import InMemoryWorld, admin_user
from tests.e2e import fixtures as fx


class UserProvider:
    """Mutable ``get_current_user`` override (real dependency override)."""

    def __init__(self) -> None:
        self.current = admin_user()
        self.unauthenticated = False

    async def __call__(self):
        if self.unauthenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated"
            )
        return self.current

    def set_user(self, user) -> None:
        self.current = user
        self.unauthenticated = False

    def set_unauthenticated(self) -> None:
        self.unauthenticated = True


@pytest.fixture
def world() -> InMemoryWorld:
    return InMemoryWorld()


@pytest.fixture
def user_provider() -> UserProvider:
    return UserProvider()


@pytest.fixture
def app(world: InMemoryWorld, user_provider: UserProvider):
    application = create_app()
    index = FactorSearchIndex()
    index.load(list(world.factors._factors.values()))
    application.dependency_overrides[get_current_user] = user_provider
    application.dependency_overrides[get_repositories] = lambda: world.bundle()
    application.dependency_overrides[get_audit_logger] = lambda: AuditLogger(world.audit)
    application.dependency_overrides[get_event_bus] = lambda: EventBus()
    application.dependency_overrides[get_factor_search_index] = lambda: index
    return application


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client


@pytest.fixture
def scenario(world: InMemoryWorld) -> InMemoryWorld:
    """The standard two-org / two-firm synthetic E2E scenario."""
    fx.seed_standard_scenario(world)
    return world
