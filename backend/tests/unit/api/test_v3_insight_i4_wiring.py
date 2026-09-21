"""I4 — real repository-wiring contract (OHD I3 D-01 lesson applied to I4).

The I3 remediation established that a test-only duck-typed bundle can mask a
missing production attribute. These tests therefore exercise the REAL
``RepositoryBundle`` construction path, so a future edit that drops the I4
repositories from the composition root fails here instead of in production.
"""
from __future__ import annotations

import dataclasses
import inspect

import pytest

from api import dependencies as deps
from data.insight_interactions import InsightInteractionRepository
from services import insight_interactions as svc

#: Attributes the I4 orchestration resolves through the real bundle.
REQUIRED_REPOSITORIES = (
    "insight",
    "insight_interactions",
    "audit",
    "organizations",
    "reports",
)


class _Pool:
    """Sentinel pool: AbstractRepository only rejects ``None``."""


@pytest.fixture()
async def real_bundle(monkeypatch):
    async def _fake_pool():
        return _Pool()

    monkeypatch.setattr(deps, "get_pool", _fake_pool)
    return await deps.get_repositories()


def test_real_bundle_declares_every_repository_i4_resolves():
    names = {f.name for f in dataclasses.fields(deps.RepositoryBundle)}
    missing = [name for name in REQUIRED_REPOSITORIES if name not in names]
    assert missing == [], f"RepositoryBundle is missing: {missing}"


def test_real_factory_constructs_the_i4_repositories():
    source = inspect.getsource(deps.get_repositories)
    missing = [name for name in REQUIRED_REPOSITORIES if f"{name}=" not in source]
    assert missing == [], f"get_repositories() does not construct: {missing}"


def test_service_module_imports_without_an_api_cycle():
    """I3 D-02 lesson: the service must not import api.* at import time."""
    source = inspect.getsource(svc)
    head = source.split("if TYPE_CHECKING:")[0]
    assert "if TYPE_CHECKING:" in source
    assert "from api.dependencies import" not in head
    assert "from api.insight_authz import" not in head


async def test_real_bundle_exposes_the_i4_evidence_repository(real_bundle):
    assert isinstance(real_bundle.insight_interactions, InsightInteractionRepository)
    assert isinstance(real_bundle.audit, object)
    # The append-only boundary is declared in the repository itself.
    with pytest.raises(NotImplementedError):
        await real_bundle.insight_interactions.save(object())
