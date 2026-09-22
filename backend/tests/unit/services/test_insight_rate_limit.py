"""Phase 8 — Insight execution rate limiting and the analytics answer states.

Authorization: PO Insight Discovery-Aggregation-Provenance-RateLimiting package
(2026-09-22). Covers the ratified defaults, both scopes, burst/concurrency
semantics, ``429`` + ``Retry-After``, the anti-bypass guarantee across *both*
customer-facing execution routes, and the truthful use of the existing I4
``rate_limited`` / ``multiple_matches`` / ``zero`` answer states.
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from starlette.testclient import TestClient

from api import v3_insight_tools
from api.dependencies import get_repositories
from auth import AuthUser, get_current_user
from services import insight_interactions as svc
from services import insight_rate_limit as limiter
from tests.unit.api.insight_analytics_fakes import (
    AuditSinkFake,
    InsightConversationFake,
    InsightInteractionFake,
    InsightLogsFake,
    snapshot_row,
)
from tests.unit.api.insight_limit_fakes import InsightLimitsFake

ORG_A = "11111111-1111-4111-8111-111111111111"
ALICE = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa"
BOB = "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb"
CONV = "cccccccc-1111-4111-8111-111111111111"


class _Orgs:
    async def get_by_id(self, organization_id):
        from types import SimpleNamespace

        return SimpleNamespace(id=organization_id, is_active=True)


class _NoneRepo:
    async def get_by_user(self, user_id):
        return None

    async def get_active_memberships_by_user(self, user_id):
        return []


def _auth_user(user_id=ALICE, organization_id=ORG_A):
    return AuthUser(
        user_id=user_id,
        email="alice@example.test",
        role="org_owner",
        role_name="org_owner",
        organization_id=organization_id,
        is_org_member=True,
    )


@pytest.fixture(autouse=True)
def _clear_limit_env(monkeypatch):
    for name in (
        limiter.ENV_ENABLED,
        limiter.ENV_USER_PER_MINUTE,
        limiter.ENV_USER_BURST,
        limiter.ENV_USER_MAX_CONCURRENT,
        limiter.ENV_ORG_PER_MINUTE,
        limiter.ENV_ORG_BURST,
        limiter.ENV_ORG_MAX_CONCURRENT,
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture()
def world():
    limits = InsightLimitsFake()
    logs = InsightLogsFake()
    return SimpleNamespace(limits=limits, logs=logs)


@pytest.fixture()
def repos(world):
    from types import SimpleNamespace

    return SimpleNamespace(
        organizations=_Orgs(),
        staff=_NoneRepo(),
        consultants=_NoneRepo(),
        logs=world.logs,
        insight=InsightConversationFake(CONV, ORG_A, ALICE),
        insight_interactions=InsightInteractionFake(),
        audit=AuditSinkFake(),
        insight_limits=world.limits,
    )


# --------------------------------------------------------------------------
# Configuration: ratified defaults, bounded operator overrides
# --------------------------------------------------------------------------
def test_ratified_defaults_are_the_published_technical_limits():
    user, org = limiter.configured_policies()
    assert (user.requests_per_minute, user.burst, user.max_concurrent) == (20, 5, 2)
    assert (org.requests_per_minute, org.burst, org.max_concurrent) == (100, 20, 10)
    assert user.capacity == 25 and org.capacity == 120
    assert user.refill_per_second == pytest.approx(1 / 3)


def test_operator_overrides_are_honoured_within_the_safety_ceiling(monkeypatch):
    monkeypatch.setenv(limiter.ENV_USER_PER_MINUTE, "30")
    monkeypatch.setenv(limiter.ENV_USER_MAX_CONCURRENT, "3")
    user, _org = limiter.configured_policies()
    assert user.requests_per_minute == 30
    assert user.max_concurrent == 3


@pytest.mark.parametrize("value", ["nonsense", "0", "999999"])
def test_an_invalid_or_unbounded_override_falls_back_to_the_default(monkeypatch, value):
    monkeypatch.setenv(limiter.ENV_USER_PER_MINUTE, value)
    user, _org = limiter.configured_policies()
    assert user.requests_per_minute == 20


def test_rate_limiting_can_only_be_disabled_explicitly_server_side(monkeypatch):
    assert limiter.rate_limiting_enabled() is True
    monkeypatch.setenv(limiter.ENV_ENABLED, "false")
    assert limiter.rate_limiting_enabled() is False


# --------------------------------------------------------------------------
# Bucket behaviour (per user, per organisation)
# --------------------------------------------------------------------------
async def test_the_user_bucket_admits_the_allowance_then_refuses(repos, world):
    user, _org = limiter.configured_policies()
    for _ in range(user.capacity):
        decision = await limiter.check_request_rates(
            repos=repos, user_id=ALICE, organization_id=ORG_A
        )
        assert decision.allowed is True
    denied = await limiter.check_request_rates(
        repos=repos, user_id=ALICE, organization_id=ORG_A
    )
    assert denied.allowed is False
    assert denied.scope == "user"
    assert denied.remaining == 0
    assert denied.retry_after_seconds >= 1
    assert world.limits.denials[("user", ALICE)] == 1


async def test_a_user_denial_does_not_consume_the_organisation_token(repos, world):
    world.limits.drain("user", ALICE)
    denied = await limiter.check_request_rates(
        repos=repos, user_id=ALICE, organization_id=ORG_A
    )
    assert denied.allowed is False
    # The organisation bucket was never touched.
    assert ("org", ORG_A) not in world.limits.consumed


async def test_the_organisation_bucket_bounds_many_users(repos, world):
    world.limits.drain("org", ORG_A)
    denied = await limiter.check_request_rates(
        repos=repos, user_id=BOB, organization_id=ORG_A
    )
    assert denied.allowed is False
    assert denied.scope == "org"
    # The user token was consumed before the organisation check refused.
    assert ("user", BOB) in world.limits.consumed


async def test_rate_limiting_can_be_disabled_server_side(repos, monkeypatch):
    monkeypatch.setenv(limiter.ENV_ENABLED, "false")
    decision = await limiter.check_request_rates(
        repos=repos, user_id=ALICE, organization_id=ORG_A
    )
    assert decision.allowed is True and decision.enforced is False
    assert limiter.rate_limit_headers(decision) == {}


# --------------------------------------------------------------------------
# Concurrency leases
# --------------------------------------------------------------------------
async def test_concurrency_is_bounded_per_user_and_released(repos):
    user, _org = limiter.configured_policies()
    first = await limiter.acquire_execution_leases(
        repos=repos, user_id=ALICE, organization_id=ORG_A
    )
    second = await limiter.acquire_execution_leases(
        repos=repos, user_id=ALICE, organization_id=ORG_A
    )
    assert first.acquired and second.acquired
    denied = await limiter.acquire_execution_leases(
        repos=repos, user_id=ALICE, organization_id=ORG_A
    )
    assert denied.acquired is False
    assert denied.scope == "user"
    assert denied.max_concurrent == user.max_concurrent
    assert denied.retry_after_seconds == limiter.LEASE_SECONDS
    await limiter.release_execution_leases(repos=repos, lease=first)
    recovered = await limiter.acquire_execution_leases(
        repos=repos, user_id=ALICE, organization_id=ORG_A
    )
    assert recovered.acquired is True


async def test_a_partial_acquisition_is_released_when_the_organisation_is_full(repos, world):
    _user, org = limiter.configured_policies()
    world.limits.seed_lease("org", ORG_A, org.max_concurrent)
    denied = await limiter.acquire_execution_leases(
        repos=repos, user_id=ALICE, organization_id=ORG_A
    )
    assert denied.acquired is False
    assert denied.scope == "org"
    # The user slot taken first was given back rather than leaked.
    assert world.limits.leases[("user", ALICE)]["in_flight"] == 0


async def test_a_stale_lease_is_recovered(repos, world):
    world.limits.seed_lease("user", ALICE, 99)
    world.limits.expire_lease("user", ALICE)
    lease = await limiter.acquire_execution_leases(
        repos=repos, user_id=ALICE, organization_id=ORG_A
    )
    assert lease.acquired is True


async def test_releasing_an_empty_lease_is_safe(repos):
    await limiter.release_execution_leases(repos=repos, lease=None)
    await limiter.release_execution_leases(
        repos=repos, lease=limiter.ExecutionLease(acquired=True, keys=())
    )


# --------------------------------------------------------------------------
# Headers
# --------------------------------------------------------------------------
def test_refusal_headers_are_bounded_and_truthful():
    headers = limiter.refusal_headers(7)
    assert headers["Retry-After"] == "7"
    assert headers["X-RateLimit-Remaining"] == "0"
    assert limiter.refusal_headers(99999)["Retry-After"] == str(limiter.MAX_RETRY_AFTER_SECONDS)
    assert limiter.refusal_headers(0)["Retry-After"] == "1"


def test_rate_limited_error_is_a_429_with_a_retry_after():
    error = limiter.rate_limited_error(
        limiter.RateLimitDecision(allowed=False, scope="user", retry_after_seconds=3)
    )
    assert error.status_code == 429
    assert error.headers["Retry-After"] == "3"


# --------------------------------------------------------------------------
# Anti-bypass: both customer-facing execution routes carry the same limit
# --------------------------------------------------------------------------
def _tools_client(world):
    from types import SimpleNamespace

    app = FastAPI()
    app.include_router(v3_insight_tools.router)
    app.dependency_overrides[get_current_user] = lambda: _auth_user()
    app.dependency_overrides[get_repositories] = lambda: SimpleNamespace(
        organizations=_Orgs(),
        staff=_NoneRepo(),
        consultants=_NoneRepo(),
        logs=world.logs,
        insight=None,
        insight_limits=world.limits,
    )
    return TestClient(app)


def test_the_tools_route_is_rate_limited_too(world):
    client = _tools_client(world)
    world.limits.drain("user", ALICE)
    response = client.post(
        "/api/v3/insight/tools/invoke",
        json={
            "organization_id": ORG_A,
            "tool": "calculation_snapshot_lookup",
            "input": {"snapshot_id": "s1"},
        },
    )
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) >= 1


def test_the_tools_route_refuses_when_the_concurrency_ceiling_is_held(world):
    client = _tools_client(world)
    world.limits.seed_lease("user", ALICE, 99)
    response = client.post(
        "/api/v3/insight/tools/invoke",
        json={
            "organization_id": ORG_A,
            "tool": "calculation_snapshot_lookup",
            "input": {"snapshot_id": "s1"},
        },
    )
    assert response.status_code == 429
    assert response.headers["Retry-After"] == str(limiter.LEASE_SECONDS)


def test_a_successful_tool_call_releases_its_lease(world):
    client = _tools_client(world)
    response = client.post(
        "/api/v3/insight/tools/invoke",
        json={
            "organization_id": ORG_A,
            "tool": "insight_discovery",
            "input": {"reporting_year": "2024"},
        },
    )
    assert response.status_code == 200
    assert world.limits.leases[("user", ALICE)]["in_flight"] == 0
    assert world.limits.leases[("org", ORG_A)]["in_flight"] == 0


# --------------------------------------------------------------------------
# Interaction path: analytics answer states and the rate-limited record
# --------------------------------------------------------------------------
async def _run(repos, question, **kwargs):
    return await svc.run_interaction(
        current_user=_auth_user(),
        repos=repos,
        organization_id=ORG_A,
        conversation_id=CONV,
        question=question,
        narration=svc.NARRATION_NONE,
        **kwargs,
    )


async def test_a_planned_discovery_question_runs_the_analytics_tool(repos, world):
    world.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A))
    outcome = await _run(repos, "which calculation was 20000 kg co2e on 2024-02-02?")
    assert outcome.intent == "insight_discovery"
    assert outcome.answer_status == "success"
    assert repos.insight_interactions.tool_calls[0]["tool_name"] == "insight_discovery"
    assert repos.insight_interactions.tool_calls[0]["arguments"]["co2e_kg"] == "20000"


async def test_several_matches_become_the_multiple_matches_answer_state(repos, world):
    for index in range(3):
        world.logs.snapshots.append(snapshot_row(f"s{index}", organization_id=ORG_A))
    outcome = await _run(repos, "which calculation was 20000 kg co2e on 2024-02-02?")
    assert outcome.answer_status == "multiple_matches"
    assert outcome.lifecycle == "completed"
    call = repos.insight_interactions.tool_calls[0]
    # The evidence records the truth: the tool succeeded and reported ambiguity.
    assert call["tool_status"] == "success"
    assert call["result_metadata"]["reason"] == "multiple_matches"
    assert call["result_metadata"]["match_count"] == 3
    assert outcome.narration_state == "skipped"
    assert outcome.narration_text is None
    assert any(r["kind"] == "calculation_snapshot" for r in outcome.references)


async def test_zero_matches_is_no_data_and_a_zero_total_is_zero(repos, world):
    none = await _run(repos, "which calculation was 20000 kg co2e on 2024-02-02?")
    assert none.answer_status == "no_data"
    world.logs.groups = [{"group_key": "Scope 1", "row_count": 1, "co2e_kg": Decimal("0")}]
    world.logs.totals = {"rows": 1, "co2e": Decimal("0")}
    zero = await _run(repos, "emissions by scope in 2024")
    assert zero.answer_status == "zero"
    assert zero.intent == "insight_aggregation"


async def test_an_approximate_amount_without_tolerance_asks_for_clarification(repos):
    outcome = await _run(repos, "approximately 20000 kg co2e in 2024")
    assert outcome.answer_status == "needs_clarification"
    assert outcome.intent == "clarification:amount_tolerance_required"
    assert repos.insight_interactions.tool_calls == []


async def test_an_invalid_scope_is_invalid_input_not_a_guess(repos):
    outcome = await _run(repos, "scope 9 emissions in 2024")
    assert outcome.answer_status == "invalid_input"
    assert outcome.intent == "invalid:invalid_scope"


async def test_a_rate_limited_request_answers_429_before_any_layer2_record(repos, world):
    world.limits.drain("user", ALICE)
    with pytest.raises(HTTPException) as raised:
        await _run(repos, "which calculation was 20000 kg co2e on 2024-02-02?")
    assert raised.value.status_code == 429
    assert "Retry-After" in raised.value.headers
    # No interaction, no message, no tool call: a refusal costs almost nothing.
    assert repos.insight_interactions.rows == {}
    assert repos.insight.messages == []


async def test_a_concurrency_refusal_is_recorded_as_rate_limited(repos, world):
    world.logs.snapshots.append(snapshot_row("s1", organization_id=ORG_A))
    world.limits.seed_lease("user", ALICE, 99)
    with pytest.raises(HTTPException) as raised:
        await _run(repos, "which calculation was 20000 kg co2e on 2024-02-02?")
    assert raised.value.status_code == 429
    row = next(iter(repos.insight_interactions.rows.values()))
    assert row["answer_status"] == "rate_limited"
    assert row["lifecycle"] == "failed"
    assert row["error_class"] == "concurrency_limit"
    assert repos.audit.entries, "the refusal is audited"
    assert repos.insight_interactions.tool_calls == []


async def test_narration_is_never_attempted_for_an_ambiguous_result(repos, world):
    for index in range(2):
        world.logs.snapshots.append(snapshot_row(f"s{index}", organization_id=ORG_A))

    class _Client:
        def __init__(self):
            self.prompts = []

        async def complete(self, prompt, *, system=None, temperature=0.0, max_tokens=512):
            self.prompts.append(prompt)
            return "should not run"

    client = _Client()
    outcome = await svc.run_interaction(
        current_user=_auth_user(),
        repos=repos,
        organization_id=ORG_A,
        conversation_id=CONV,
        question="which calculation was 20000 kg co2e on 2024-02-02?",
        narration=svc.NARRATION_OPTIONAL,
        llm_client=client,
    )
    assert outcome.answer_status == "multiple_matches"
    assert client.prompts == []
