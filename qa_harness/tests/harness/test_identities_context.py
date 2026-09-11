"""Deterministic demo runtime context self-tests (offline, no live stack)."""

from __future__ import annotations

import uuid

from qa_harness.identities import context
from qa_harness.identities.loader import generate_full_population
from qa_harness.identities.resolver import IdentityResolver


def _det(seed_key: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"carbontally-demo:{seed_key}"))


def test_demo_uuid_scheme_matches_seeder() -> None:
    assert context.demo_uuid("org:1") == _det("org:1")
    assert context.organization_id(1) == _det("org:1")
    assert context.organization_id(50) == _det("org:50")
    assert context.client_organization_id(1, 1) == _det("client_org:1:1")
    assert context.entity_id(2) == _det("entity:2")
    assert context.staff_user_id("pe-manager-1") == _det("staff_user:pe-manager-1")


def test_demo_uuid_scheme_matches_live_orgs() -> None:
    # Live-verified mapping (read-only psql, 2026-08-24):
    #   org:1 -> bc197ccf Quayside Energy (owner.demo0001)
    #   org:2 -> e5218a70 Granite Distribution (owner.demo0002)
    assert context.organization_id(1) == "bc197ccf-cd12-56dd-8773-3c4d7a16c69e"
    assert context.organization_id(2) == "e5218a70-c235-5b73-a5a3-da029c995462"


def test_resolve_context_personas() -> None:
    owner = context.resolve_context("owner", org_index=3)
    assert owner["organization_id"] == context.organization_id(3)
    assert owner["member_role"] == "owner"
    pe = context.resolve_context("pe_manager", entity_index=1)
    assert pe["processing_entity_id"] == context.entity_id(1)
    assert pe["is_pe"] and pe["is_staff"]
    staff = context.resolve_context("system-admin")
    assert staff["staff_role"] == "system_admin"
    assert context.resolve_context("legacy") == {}


def test_resolver_enriches_organization_id() -> None:
    population = {i.email: i for i in generate_full_population()}
    resolver = IdentityResolver(population=population)
    owner = resolver.resolve("owner.demo0001@demo.carbontally.local")
    assert owner.organization_id == context.organization_id(1)
    assert owner.member_role == "owner"
    client = resolver.resolve("client.owner.demo0001.1@demo.carbontally.local")
    assert client.organization_id == context.client_organization_id(1, 1)
    pe = resolver.resolve("pe-manager-1.demo@demo.carbontally.local")
    assert pe.processing_entity_id == context.entity_id(1)
    consultant = resolver.resolve("consultant.demo0001@demo.carbontally.local")
    assert consultant.organization_id in (None, "")


def test_resolver_population_covers_all_org_indices() -> None:
    population = {i.email: i for i in generate_full_population()}
    resolver = IdentityResolver(population=population)
    # Direct orgs 1..50 must all resolve with a deterministic org id.
    for index in (1, 2, 25, 50):
        email = f"owner.demo{index:04d}@demo.carbontally.local"
        assert resolver.resolve(email).organization_id == context.organization_id(index)
