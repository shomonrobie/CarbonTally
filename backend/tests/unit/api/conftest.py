"""Phase 10 API contract-test fixtures (in-memory, no database access).

Every fixture is wired over the in-memory fakes through FastAPI dependency
overrides. The production composition root (``api.dependencies``) is reused —
only the leaf dependencies (auth user, repositories, audit logger, event bus,
search index) are replaced. The development database is never opened: the
DEFRA/SEAI baseline (7,029 / 20 / 7,049) is untouched by these tests.
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


class UserProvider:
    """Mutable ``get_current_user`` override for tests."""

    def __init__(self) -> None:
        self.current = admin_user()
        self.unauthenticated = False

    async def __call__(self):
        if self.unauthenticated:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
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
    app = create_app()

    index = FactorSearchIndex()
    index.load(list(world.factors._factors.values()))

    app.dependency_overrides[get_current_user] = user_provider
    app.dependency_overrides[get_repositories] = lambda: world.bundle()
    app.dependency_overrides[get_audit_logger] = lambda: AuditLogger(world.audit)
    app.dependency_overrides[get_event_bus] = lambda: EventBus()
    app.dependency_overrides[get_factor_search_index] = lambda: index
    return app


@pytest.fixture
def client(app):
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
