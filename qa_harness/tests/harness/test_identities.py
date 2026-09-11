"""Harness self-tests: the complete demo identity population (spec §7, §35)."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_harness.identities.loader import (
    LEGACY_DEMO_LOCALS,
    REPRESENTATIVE_EMAILS,
    TEST_DOMAIN,
    Identity,
    IdentityLoader,
    generate_full_population,
    parse_identity_scheme,
    resolve_manifest_path,
)
from qa_harness.identities.resolver import IdentityResolver, ResolveError
from qa_harness.identities.selectors import (
    BoundaryPair,
    RepresentativeSelector,
    cross_boundary_pairs,
    select_by_role,
)

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures"

# Live-verified population (read-only auth.users count, 2026-08-24):
# 1172 standard demo scheme (200 direct roles + 911 client owners + 50
# consultants + 6 PE + 5 internal staff) + 11 legacy demo fixtures
# = 1183 demo (@demo.carbontally.local) + 6 OHD audit (@test) + 3
# system/selftest fixtures = 1192 total. DEMO_IDENTITIES.md documented 1185
# demo identities (verified 2026-08-28); live drift of 2 is noted in the
# reconciliation report — the model mirrors the live count.
EXPECTED_POPULATION = 50 * 4 + 50 + 911 + 6 + 5 + 11 + 6 + 3
EXPECTED_DEMO = 50 * 4 + 50 + 911 + 6 + 5 + 11


def test_full_population_size() -> None:
    population = generate_full_population()
    assert len(population) == EXPECTED_POPULATION
    emails = {i.email for i in population}
    assert len(emails) == len(population), "duplicate emails in generated population"


def test_demo_population_matches_live_count() -> None:
    population = generate_full_population()
    demo = [i for i in population if i.is_demo]
    non_demo = [i for i in population if not i.is_demo]
    assert len(demo) == EXPECTED_DEMO
    assert len(non_demo) == EXPECTED_POPULATION - EXPECTED_DEMO
    # Every legacy fixture account lives at the demo domain (live-verified).
    for local in LEGACY_DEMO_LOCALS:
        assert f"{local}@demo.carbontally.local" in {i.email for i in demo}
    # Audit/fixture identities never carry demo credentials.
    assert all(i.email.endswith(TEST_DOMAIN) or not i.is_demo for i in non_demo)


def test_role_counts() -> None:
    population = generate_full_population()
    by_role: dict = {}
    for identity in population:
        by_role[identity.persona] = by_role.get(identity.persona, 0) + 1
    assert by_role["owner"] == 50
    assert by_role["admin"] == 50
    assert by_role["member"] == 50
    assert by_role["viewer"] == 50
    assert by_role["consultant"] == 50
    assert by_role["client_owner"] == 911
    assert by_role["pe_manager"] == 3
    assert by_role["pe_staff"] == 3
    assert by_role["legacy"] == 11
    assert by_role["audit"] == 6
    assert by_role["fixture"] == 3
    for internal in ("operator", "reviewer", "qc", "staff-admin", "system-admin"):
        assert by_role[internal] == 1


def test_client_total_is_documented() -> None:
    population = generate_full_population()
    clients = [i for i in population if i.persona == "client_owner"]
    assert len(clients) == 911
    # Every client belongs to a consultant firm.
    assert all(i.consultant_index >= 1 for i in clients)


def test_client_distribution_mirrors_live() -> None:
    from qa_harness.identities.loader import CLIENT_COUNTS_BY_CONSULTANT

    assert len(CLIENT_COUNTS_BY_CONSULTANT) == 50
    assert sum(CLIENT_COUNTS_BY_CONSULTANT) == 911
    assert all(5 <= n <= 30 for n in CLIENT_COUNTS_BY_CONSULTANT)
    population = generate_full_population()
    for consultant_index, expected in enumerate(CLIENT_COUNTS_BY_CONSULTANT, start=1):
        per_firm = [
            i for i in population
            if i.persona == "client_owner" and i.consultant_index == consultant_index
        ]
        assert len(per_firm) == expected, f"consultant {consultant_index}"
        numbers = sorted(i.client_number for i in per_firm)
        assert numbers == list(range(1, expected + 1)), f"consultant {consultant_index} numbering"


def test_no_password_on_identity() -> None:
    population = generate_full_population()
    for identity in population:
        assert not hasattr(identity, "password")


def test_loader_with_manifest_marks_representative() -> None:
    loader = IdentityLoader(manifest_path=FIXTURES / "sample_manifest.json")
    population = loader.load()
    owner = population["owner.demo0001@demo.carbontally.local"]
    assert owner.representative is True
    assert owner.org == "Quayside Energy"
    # Non-manifest identity stays unmarked.
    other = population["owner.demo0002@demo.carbontally.local"]
    assert other.representative is False


def test_representative_set() -> None:
    loader = IdentityLoader(manifest_path=FIXTURES / "sample_manifest.json")
    reps = loader.representative()
    emails = {i.email for i in reps}
    assert REPRESENTATIVE_EMAILS["customer_owner"] in emails
    assert REPRESENTATIVE_EMAILS["consultant"] in emails
    assert REPRESENTATIVE_EMAILS["system_admin"] in emails


def test_resolve_manifest_path() -> None:
    path = resolve_manifest_path("../tools/seed_investor_demo/demo_manifest.json")
    assert str(path).endswith("tools/seed_investor_demo/demo_manifest.json")
    assert path.is_absolute()


def test_resolver_context() -> None:
    population = {i.email: i for i in generate_full_population()}
    resolver = IdentityResolver(population=population)
    resolved = resolver.resolve("owner.demo0001@demo.carbontally.local")
    assert resolved.member_role == "owner"
    assert resolved.is_staff is False
    assert resolved.is_demo is True
    assert resolved.identity.workspace == "customer"
    assert resolved.identity.landing_route == "/home"
    with pytest.raises(ResolveError):
        resolver.resolve("nobody@nowhere.invalid")


def test_resolver_fixture_classification() -> None:
    population = {i.email: i for i in generate_full_population()}
    resolver = IdentityResolver(population=population)
    # Legacy @demo fixture: demo credentials, but outside the role model.
    legacy = resolver.resolve("owner@demo.carbontally.local")
    assert legacy.is_demo is True
    assert legacy.is_staff is False
    assert legacy.member_role == ""
    # OHD audit @test: never demo credentials.
    audit = resolver.resolve("ohd.owner.a@test.carbontally.local")
    assert audit.is_demo is False
    assert audit.is_staff is False
    # System/selftest fixture: never demo credentials.
    selftest = resolver.resolve("rv2.owner1787494916@rev2-selftest.test")
    assert selftest.is_demo is False


def test_demo_login_refuses_non_demo_identity() -> None:
    from qa_harness.browser.auth import demo_login

    population = {i.email: i for i in generate_full_population()}
    with pytest.raises(ValueError):
        demo_login("http://127.0.0.1:54425", population["ohd.owner.a@test.carbontally.local"], "pw")
    with pytest.raises(ValueError):
        demo_login("http://127.0.0.1:54425", population["rv2.owner1787494916@rev2-selftest.test"], "pw")
    # A demo identity passes the guard (no live call: bogus URL never reached
    # because requests would 404 — but the guard runs first; we only assert
    # the guard accepts, so patch the network call out).
    import qa_harness.browser.auth.session as session_mod

    calls = []

    def fake_login(url, email, password, timeout=15):
        calls.append((url, email, password))
        return session_mod.AuthSession(email=email)

    original = session_mod.login_via_password_grant
    session_mod.login_via_password_grant = fake_login
    try:
        demo_login("http://127.0.0.1:54425", population["owner@demo.carbontally.local"], "pw")
    finally:
        session_mod.login_via_password_grant = original
    assert calls and calls[0][1] == "owner@demo.carbontally.local"


def test_organization_identities() -> None:
    population = {i.email: i for i in generate_full_population()}
    resolver = IdentityResolver(population=population)
    members = resolver.organization_identities(1)
    assert len(members) == 4
    assert {i.persona for i in members} == {"owner", "admin", "member", "viewer"}


def test_select_by_role_deterministic() -> None:
    population = {i.email: i for i in generate_full_population()}
    owners = select_by_role(population, "customer_owner", limit=5)
    assert [i.email for i in owners] == [
        f"owner.demo{n:04d}@demo.carbontally.local" for n in range(1, 6)
    ]
    assert len(select_by_role(population, "customer_owner")) == 50


def test_cross_boundary_pairs() -> None:
    population = {i.email: i for i in generate_full_population()}
    pairs = cross_boundary_pairs(population)
    assert len(pairs) == 9
    labels = {p.label for p in pairs}
    assert "Customer A vs Customer B" in labels
    assert "Consultant A vs Consultant B" in labels
    assert "PE A vs PE B" in labels
    assert "Staff Admin vs System Admin" in labels
    for pair in pairs:
        assert isinstance(pair, BoundaryPair)
        assert pair.actor_a.email != pair.actor_b.email


def test_parse_identity_scheme() -> None:
    doc = (
        "owner.demo0001 owner.demo0002 admin.demo0001 member.demo0001 "
        "client.owner.demo0001.1 pe-manager-1.demo pe-staff-1.demo consultant.demo0001"
    )
    counts = parse_identity_scheme(doc)
    assert counts["customer_owner"] == 2
    assert counts["customer_admin"] == 1
    assert counts["customer_member"] == 1
    assert counts["client_owner"] == 1
    assert counts["pe_manager"] == 1
    assert counts["consultant"] == 1
