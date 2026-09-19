"""F-048-2/052 — activity-clarification API: authorization + anti-bypass.

The app under test is the REAL router over the REAL authorization code path
(``ensure_processing_org_access``) and the REAL clarification engine. Only the
transport dependencies FastAPI requires are substituted, through the project's
standard ``dependency_overrides`` mechanism:

* ``get_current_user`` → an authenticated ``AuthUser``, or the real 401 shape for
  an unauthenticated request (the endpoints declare ``Depends(get_current_user)``,
  so an anonymous request cannot reach the handler);
* ``get_repositories`` → a bundle whose ``clarifications`` member is the REAL
  repository over a capturing fake pool, so persistence (and the exact SQL
  parameters reaching the database) is genuinely exercised;
* ``get_matching_engine`` → a stub engine returning the scenario's candidates.

**No authorization function is mocked** — ``ensure_processing_org_access`` runs for
real, which is what makes the cross-tenant and unauthenticated cases meaningful.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from decimal import Decimal

from api.dependencies import get_matching_engine, get_repositories
from api.v3_activity_clarifications import router
from auth import AuthUser, get_current_user
from data.activity_clarifications import ActivityClarificationsRepository
from domain.factor import EmissionFactor

ORG_A = "aaaaaaaa-1111-4111-8111-aaaaaaaaaaaa"
ORG_B = "bbbbbbbb-2222-4222-8222-bbbbbbbbbbbb"
USER = "cccccccc-3333-4333-8333-cccccccccccc"


class _FakeConn:
    def __init__(self, rows=None):
        self.rows = list(rows or [])
        self.queries: list[str] = []
        self.params: list[tuple] = []
        #: asyncpg parity for the versioned-write contract (F-039-1 remediation):
        #: the transition resolves the current row under a lock and runs the retire
        #: and the insert in ONE transaction on ONE acquired connection.
        self.acquires = 0
        self.transactions = 0
        self.in_transaction = False

    async def fetchrow(self, query, *args):
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        if "AND is_current" in query:
            # Effective/current-row lookup (the write path locks it with FOR UPDATE):
            # only a scripted CURRENT row is returned, and a non-current scripted row
            # is left for the INSERT that follows.
            if self.rows and isinstance(self.rows[0], dict) and self.rows[0].get("is_current"):
                return self.rows.pop(0)
            return None
        return self.rows.pop(0) if self.rows else None

    async def fetch(self, query, *args):
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        row = self.rows.pop(0) if self.rows else None
        return [] if row is None else list(row)

    async def execute(self, query, *args):
        self.queries.append(" ".join(query.split()))
        self.params.append(args)
        return "OK"

    def transaction(self):
        return _FakeTransaction(self)


class _FakeTransaction:
    """Minimal asyncpg-style transaction context manager."""

    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        self._conn.transactions += 1
        self._conn.in_transaction = True
        return self

    async def __aexit__(self, *exc):
        self._conn.in_transaction = False
        return False


class _Acquire:
    def __init__(self, conn):
        self._conn = conn

    async def __aenter__(self):
        self._conn.acquires += 1
        return self._conn

    async def __aexit__(self, *exc):
        return False


class _Pool:
    def __init__(self, conn):
        self._conn = conn

    def acquire(self):
        return _Acquire(self._conn)


class _Engine:
    """Stub matching engine — returns the scenario's candidates."""

    def __init__(self, candidates=()):
        self._candidates = list(candidates)

    def clarification_candidates(self, request):
        return list(self._candidates)


def _client(*, user=None, candidates=None, rows=(), memberships=(), firm=None, client_grant=None, grant_org=ORG_A):
    conn = _FakeConn(rows)
    engine = _Engine(_waste_candidates() if candidates is None else candidates)
    bundle = SimpleNamespace(
        clarifications=ActivityClarificationsRepository(_Pool(conn)),  # type: ignore[arg-type]
        consultants=_Consultants(
            memberships=memberships, profile=firm, client=client_grant, grant_org=grant_org
        ),
    )
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_repositories] = lambda: bundle
    app.dependency_overrides[get_matching_engine] = lambda: engine
    if user is None:

        def _unauthenticated():
            raise HTTPException(status_code=401, detail="Not authenticated")

        app.dependency_overrides[get_current_user] = _unauthenticated
    else:
        app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(app), conn


class _Consultants:
    """Faithful double for the three methods the consultant gate actually calls.

    ``ensure_consultant_org_access`` resolves: active firm memberships →
    the firm's profile (must exist and be active) → an ACTIVE
    ``consultant_clients`` grant for the organisation (D15). Only the data is
    faked here; the authorization logic under test is the real implementation.
    """

    def __init__(self, *, memberships=(), profile=None, client=None, grant_org=ORG_A):
        self._memberships = list(memberships)
        self._profile = profile
        self._client = client
        self._grant_org = grant_org

    async def get_active_memberships_by_user(self, user_id):
        return list(self._memberships)

    async def get_profile_by_id(self, firm_id):
        return self._profile

    async def get_client_by_org(self, firm_id, organization_id):
        # The grant covers exactly one organisation: the fake mirrors the real
        # ``consultant_clients`` lookup (an unauthorised org resolves to None).
        if self._client is not None and organization_id != self._grant_org:
            return None
        return self._client


def _member(org: str = ORG_A) -> AuthUser:
    return AuthUser(
        user_id=USER,
        email="member@example.com",
        role="member",
        organization_id=org,
        is_org_member=True,
    )


def _declined_row(**over):
    row = {
        "activity_key": "k1",
        "original_activity": "Waste",
        "clarification": "i_dont_know",
        "clarification_type": "declined",
        "policy_input": "Waste",
        "outcome_status": "unresolved_declined",
        "selected_factor_id": None,
        "selected_factor_name": None,
        "factor_set": None,
        "factor_source": None,
        "reporting_year": None,
        "unit": None,
        "scope": None,
        "eligible_group_count": 0,
        "actor_id": USER,
        "actor_scope": "organization_member",
        "created_at": "2026-09-18T00:00:00+00:00",
    }
    row.update(over)
    return row


# ---------------------------------------------------------------------------
# Real engine fixtures (same conventions as 041/039 — no invented vocabulary)
# ---------------------------------------------------------------------------


def _f(name: str, *, unit: str = "tonnes", scope: str = "Scope 3", value: str = "1.26338",
       fid: str = "f-1") -> EmissionFactor:
    text = f"{name} [{unit}]" if "[" not in name else name
    return EmissionFactor(
        id=fid, reporting_year=2025, activity_type=text, co2e_multiplier=Decimal(value),
        unit=unit, scope=scope, factor_source="DEFRA-DESNZ", factor_set="DEFRA-2025",
        country="GB", provider_key="DEFRA-DESNZ",
        natural_key=("2025", text, "GB", unit, scope),
    )


def _waste_candidates() -> list:
    """The 041 fixture set: three treatment routes plus a waste-oils combustion family."""
    return [
        _f("Waste disposal > Construction > Aggregates - Landfill (kg CO2e)", fid="lf"),
        _f("Waste disposal > Construction > Aggregates - Open-loop (kg CO2e)",
           value="1.00835", fid="ol"),
        _f("Waste disposal > Construction > Aggregates - Incineration with Energy Recovery "
           "(kg CO2e)", value="0.02106", fid="inc"),
        _f("Fuels > Liquid fuels > Waste oils (kg CO2e)", scope="Scope 1",
           value="3219.37916", fid="oils"),
    ]


def _diesel_candidates() -> list:
    """The 039 fixture naming for the mineral-vs-blend diesel ambiguity."""
    return [
        _f("Fuels > Liquid fuels > Diesel (100% mineral diesel) (kg CO2e)", unit="litres",
           fid="min", scope="Scope 1"),
        _f("Fuels > Liquid fuels > Diesel (average biofuel blend) (kg CO2e)", unit="litres",
           fid="blend", scope="Scope 1"),
    ]


def _consultant() -> AuthUser:
    return AuthUser(user_id=USER, email="consultant@example.com", role="consultant")


def _consultant_grants(grant_status: str = "active") -> dict:
    """Active firm membership + firm profile + the client grant for ORG_A."""
    return dict(
        memberships=[SimpleNamespace(firm_id="firm-1", joined_at=None, invited_at=None)],
        firm=SimpleNamespace(id="firm-1", is_active=True),
        client_grant=SimpleNamespace(status=grant_status),
    )


def _insert_params(conn):
    """The parameter tuple the repository sent for the clarification INSERT."""
    index = next(
        i for i, q in enumerate(conn.queries) if q.startswith("INSERT INTO public.activity_clarifications")
    )
    return conn.params[index]


def _selected_row(**over):
    row = {
        "activity_key": "k1",
        "original_activity": "Waste",
        "clarification": "Landfill",
        "clarification_type": "semantic_activity",
        "policy_input": "Waste Landfill",
        "outcome_status": "selected",
        "selected_factor_id": "lf",
        "selected_factor_name": "Waste disposal > Construction > Aggregates - Landfill (kg CO2e) [tonnes]",
        "factor_set": "DEFRA-2025",
        "factor_source": "DEFRA-DESNZ",
        "reporting_year": 2025,
        "unit": "tonnes",
        "scope": "Scope 3",
        "eligible_group_count": 1,
        "actor_id": USER,
        "actor_scope": "organization_member",
        "created_at": "2026-09-18T00:00:00+00:00",
    }
    row.update(over)
    return row


DECLINE = "/api/v3/activity-clarifications/decline"
CLARIFY = "/api/v3/activity-clarifications/clarifications"
OPTIONS = "/api/v3/activity-clarifications/options"


# ---------------------------------------------------------------------------
# Consultant authorization over HTTP (Part A) — the REAL gate chain
# ---------------------------------------------------------------------------
# ensure_processing_org_access → ensure_consultant_org_access → active firm
# membership → active firm profile → ACTIVE consultant_clients grant (D15).
# Only the *data* those calls read is faked; the logic is the implementation.


def test_authorized_consultant_can_act_on_its_client_organization() -> None:
    client, conn = _client(
        user=_consultant(),
        rows=[_declined_row(actor_scope="consultant")],
        **_consultant_grants(),
    )
    response = client.post(DECLINE, json={"organization_id": ORG_A, "activity": "Waste"})
    assert response.status_code == 201
    assert response.json()["actor_scope"] == "consultant"
    assert _insert_params(conn)[3] == ORG_A


def test_consultant_cannot_forge_an_organization_it_has_no_grant_for() -> None:
    """The grant covers ORG_A; a body naming ORG_B must be refused."""
    client, conn = _client(user=_consultant(), rows=[_declined_row()], **_consultant_grants())
    assert client.post(
        DECLINE, json={"organization_id": ORG_B, "activity": "Waste"}
    ).status_code == 403
    assert client.get(
        OPTIONS, params={"organization_id": ORG_B, "activity": "Waste"}
    ).status_code == 403
    assert conn.params == []


def test_consultant_with_an_ended_grant_is_denied() -> None:
    client, conn = _client(
        user=_consultant(), rows=[_declined_row()], **_consultant_grants(grant_status="ended")
    )
    assert client.post(
        DECLINE, json={"organization_id": ORG_A, "activity": "Waste"}
    ).status_code == 403
    assert conn.params == []


def test_consultant_without_firm_membership_is_denied() -> None:
    client, conn = _client(user=_consultant(), rows=[_declined_row()])
    assert client.post(
        DECLINE, json={"organization_id": ORG_A, "activity": "Waste"}
    ).status_code == 403
    assert conn.params == []


def test_consultant_cannot_impersonate_another_actor() -> None:
    client, conn = _client(user=_consultant(), rows=[_declined_row()], **_consultant_grants())
    response = client.post(
        DECLINE,
        json={
            "organization_id": ORG_A,
            "activity": "Waste",
            "actor_id": "99999999-9999-4999-8999-999999999999",
        },
    )
    assert response.status_code == 422  # rejected, not silently ignored
    assert conn.params == []


def test_consultant_client_operates_only_within_its_own_organization() -> None:
    """A consultant's client is an ordinary organisation member (same boundary)."""
    client, _conn = _client(
        user=_member(ORG_A), rows=[_declined_row(actor_scope="organization_member")]
    )
    assert client.post(
        DECLINE, json={"organization_id": ORG_A, "activity": "Waste"}
    ).status_code == 201
    client_b, conn_b = _client(user=_member(ORG_A), rows=[_declined_row()])
    assert client_b.post(
        DECLINE, json={"organization_id": ORG_B, "activity": "Waste"}
    ).status_code == 403
    assert conn_b.params == []


def test_internal_staff_allowed_and_entity_staff_denied() -> None:
    """Consistent with the existing convention (internal scope pass, PE denied)."""
    internal = AuthUser(
        user_id=USER, email="ops@carbontally.co.uk", role="staff", is_staff=True
    )
    client, _conn = _client(user=internal, rows=[_declined_row(actor_scope="internal_staff")])
    response = client.post(DECLINE, json={"organization_id": ORG_A, "activity": "Waste"})
    assert response.status_code == 201
    assert response.json()["actor_scope"] == "internal_staff"

    entity = AuthUser(
        user_id=USER, email="pe@example.com", role="pe_staff", is_staff=True, entity_id="pe-1"
    )
    client_b, conn_b = _client(user=entity, rows=[_declined_row()])
    assert client_b.post(
        DECLINE, json={"organization_id": ORG_A, "activity": "Waste"}
    ).status_code == 403
    assert conn_b.params == []


# ---------------------------------------------------------------------------
# Positive semantic flow over HTTP (Part B) — the real engine and policy
# ---------------------------------------------------------------------------


def test_bare_waste_requires_clarification_and_offers_semantic_options_only() -> None:
    client, _conn = _client(user=_member(), candidates=_waste_candidates())
    response = client.get(
        OPTIONS, params={"organization_id": ORG_A, "activity": "Waste", "unit": "tonnes"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["clarification_required"] is True
    assert body["options"], "the engine's eligible semantic groups must be offered"
    assert all(o["id"] and o["semantic_term"] for o in body["options"])
    assert not any(o["id"] in {"lf", "ol", "inc", "oils"} for o in body["options"])


def test_waste_plus_landfill_reruns_the_policy_and_stores_server_factor_metadata() -> None:
    client, conn = _client(
        user=_member(), candidates=_waste_candidates(), rows=[_selected_row()]
    )
    response = client.post(
        CLARIFY,
        json={
            "organization_id": ORG_A,
            "activity": "Waste",
            "clarification": "Landfill",
            "activity_key": "k1",
        },
    )
    assert response.status_code == 201, response.text
    params = _insert_params(conn)
    # INSERT params: [3] organization_id · [4] original_activity · [6] clarification
    # [8] policy_input · [9] outcome_status · [10] selected_factor_id ·
    # [12] factor_set · [14] reporting_year · [15] unit · [16] scope
    assert params[4] == "Waste"  # original extracted evidence preserved
    assert params[6] == "Landfill"  # the user's statement, kept separate
    assert params[8] == "Waste Landfill"  # the policy input it produced
    assert params[9] == "selected"  # the policy's own outcome
    assert params[10] == "lf"  # the factor the POLICY selected
    assert params[12] == "DEFRA-2025" and params[14] == 2025
    # [15] is the RECORDED unit — the selected factor's own (the policy INPUT was None,
    # because F4 forbids taking unit/scope from the request body).
    assert params[15] == "tonnes"
    body = response.json()
    assert body["outcome_status"] == "selected" and body["resolved"] is True
    assert body["original_activity"] == "Waste" and body["clarification"] == "Landfill"
    assert body["selected_factor_id"] == "lf"


def test_waste_plus_waste_oils_selects_the_oils_family() -> None:
    client, conn = _client(
        user=_member(),
        candidates=_waste_candidates(),
        rows=[
            _selected_row(
                clarification="Waste oils",
                policy_input="Waste Waste oils",
                selected_factor_id="oils",
                scope="Scope 1",
            )
        ],
    )
    response = client.post(
        CLARIFY,
        json={
            "organization_id": ORG_A,
            "activity": "Waste",
            "clarification": "Waste oils",
        },
    )
    assert response.status_code == 201, response.text
    params = _insert_params(conn)
    assert params[6] == "Waste oils"
    assert params[10] == "oils" and params[16] == "Scope 1"  # the factor's own scope
    assert response.json()["selected_factor_id"] == "oils"


def test_diesel_variants_resolve_from_the_options_the_engine_offers() -> None:
    for needle, expected in (("mineral", "min"), ("blend", "blend")):
        client, conn = _client(
            user=_member(),
            candidates=_diesel_candidates(),
            rows=[_selected_row(selected_factor_id=expected, unit="litres", scope="Scope 1")],
        )
        offered = client.get(
            OPTIONS, params={"organization_id": ORG_A, "activity": "Diesel", "unit": "litres"}
        ).json()
        choice = next(
            o["semantic_term"]
            for o in offered["options"]
            if needle in (o["id"] + o["label"] + o["semantic_term"]).lower()
        )
        response = client.post(
            CLARIFY,
            json={
                "organization_id": ORG_A,
                "activity": "Diesel",
                "clarification": choice,
            },
        )
        assert response.status_code == 201, (choice, response.text)
        assert _insert_params(conn)[10] == expected


# ---------------------------------------------------------------------------
# Conflict + idempotency at the API seam (Parts D, E)
# ---------------------------------------------------------------------------


def test_identical_successful_clarification_retried_returns_the_stored_row() -> None:
    stored = _selected_row()
    client, conn = _client(
        user=_member(), candidates=_waste_candidates(), rows=[None, stored]
    )
    response = client.post(
        CLARIFY,
        json={
            "organization_id": ORG_A,
            "activity": "Waste",
            "clarification": "Landfill",
            "activity_key": "k1",
        },
    )
    assert response.status_code == 201
    assert response.json()["selected_factor_id"] == "lf"
    # the effective lookup runs first; the replay-guarded INSERT is the second statement
    assert (
        "ON CONFLICT ON CONSTRAINT activity_clarifications_replay_unique DO NOTHING"
        in conn.queries[1]
    )


def test_conflicting_clarification_is_distinct_and_never_overwrites() -> None:
    """Follows the existing architecture rather than inventing a rule.

    The adjudication identity is ``UNIQUE(activity_key, original_activity,
    clarification)``, so a *different* clarification for the same activity is a
    separate adjudication; the first is left untouched. Nothing here issues an
    UPDATE — the repository has no overwrite path (asserted below).
    """
    client, conn = _client(
        user=_member(),
        candidates=_waste_candidates(),
        rows=[
            _selected_row(),
            _selected_row(
                clarification="Waste oils",
                policy_input="Waste Waste oils",
                selected_factor_id="oils",
            ),
        ],
    )
    payload = {
        "organization_id": ORG_A,
        "activity": "Waste",
        "activity_key": "k1",
    }
    first = client.post(CLARIFY, json={**payload, "clarification": "Landfill"})
    second = client.post(CLARIFY, json={**payload, "clarification": "Waste oils"})
    assert first.status_code == second.status_code == 201
    assert first.json()["selected_factor_id"] == "lf"
    assert second.json()["selected_factor_id"] == "oils"
    assert not any(q.upper().startswith("UPDATE") for q in conn.queries)


# ---------------------------------------------------------------------------
# F3 decline gate + F4 evidence integrity
# ---------------------------------------------------------------------------


def test_decline_is_refused_when_the_activity_is_deterministic() -> None:
    """F3: a deterministic activity must not manufacture an unresolved_declined row."""
    client, conn = _client(user=_member(), rows=[_declined_row()])
    response = client.post(
        DECLINE, json={"organization_id": ORG_A, "activity": "Waste oils"}
    )
    assert response.status_code == 409
    assert conn.params == []  # no database write on a rejected decline


def test_forged_unit_or_scope_in_the_body_is_rejected() -> None:
    """F4: unit/scope are not client-authoritative, so submitting them is a 422."""
    client, conn = _client(user=_member(), rows=[_selected_row()])
    for extra in ({"unit": "litres"}, {"scope": "Scope 1"}):
        body = {
            "organization_id": ORG_A,
            "activity": "Waste",
            "clarification": "Landfill",
            **extra,
        }
        assert client.post(CLARIFY, json=body).status_code == 422
    assert conn.params == []


def test_authoritative_evidence_is_derived_from_the_persisted_item() -> None:
    """F2/F4: with a persisted item the server derives provenance and unit/scope."""
    item = "44444444-4444-4444-8444-444444444444"
    client, conn = _client(
        user=_member(),
        rows=[
            {
                "item_key": item,
                "batch_key": None,
                "organization_id": ORG_A,
                "source_file_id": "55555555-5555-4555-8555-555555555555",
                "extracted_data": {
                    "line_items": [{"activity": "Waste", "unit": "tonnes", "scope": "Scope 3"}]
                },
            },
            _selected_row(),
        ],
    )
    response = client.post(
        CLARIFY,
        json={
            "organization_id": ORG_A,
            "activity": "Waste",
            "clarification": "Landfill",
            "item_id": item,
        },
    )
    assert response.status_code == 201, response.text
    params = _insert_params(conn)
    assert params[2] == item  # item_key derived server-side
    assert params[5] == "55555555-5555-4555-8555-555555555555"  # source_evidence_ref
    assert params[15] == "tonnes" and params[16] == "Scope 3"  # authoritative evidence
    assert params[25] == item  # bounded context key = the persisted item
    assert isinstance(params[26], str) and len(params[26]) == 64  # D-039-1-I signature


def test_an_item_from_another_organisation_is_refused() -> None:
    """F2: provenance fields cannot be used to cross a tenant boundary."""
    item = "66666666-6666-4666-8666-666666666666"
    client, conn = _client(
        user=_member(ORG_A),
        rows=[{"item_key": item, "organization_id": ORG_B, "extracted_data": None}],
    )
    response = client.post(
        CLARIFY,
        json={
            "organization_id": ORG_A,
            "activity": "Waste",
            "clarification": "Landfill",
            "item_id": item,
        },
    )
    assert response.status_code == 403
    # only the context LOOKUP ran — no adjudication was written
    assert not any(q.startswith("INSERT") for q in conn.queries)


# ---------------------------------------------------------------------------
# Authentication / authorization (Parts D, I.1–I.7)
# ---------------------------------------------------------------------------


def test_unauthenticated_requests_are_denied() -> None:
    client, conn = _client(user=None)
    assert client.get(
        "/api/v3/activity-clarifications/options",
        params={"organization_id": ORG_A, "activity": "Waste"},
    ).status_code == 401
    assert client.post(
        "/api/v3/activity-clarifications/clarifications",
        json={"organization_id": ORG_A, "activity": "Waste", "clarification": "Landfill"},
    ).status_code == 401
    assert client.post(
        "/api/v3/activity-clarifications/decline",
        json={"organization_id": ORG_A, "activity": "Waste"},
    ).status_code == 401
    assert conn.params == []  # nothing reached persistence


def test_member_cannot_reach_another_organisation() -> None:
    client, conn = _client(user=_member(ORG_A))
    assert client.get(
        "/api/v3/activity-clarifications/options",
        params={"organization_id": ORG_B, "activity": "Waste"},
    ).status_code == 403
    assert client.post(
        "/api/v3/activity-clarifications/clarifications",
        json={"organization_id": ORG_B, "activity": "Waste", "clarification": "Landfill"},
    ).status_code == 403
    assert client.post(
        "/api/v3/activity-clarifications/decline",
        json={"organization_id": ORG_B, "activity": "Waste"},
    ).status_code == 403
    assert conn.params == []


# ---------------------------------------------------------------------------
# Anti-bypass: the body cannot carry authority (Parts C, I.8–I.14)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    [
        ("selected_factor_id", "11111111-2222-4333-8444-555555555555"),
        ("selected_factor_name", "Landfill of waste"),
        ("factor_set", "DEFRA 2024"),
        ("factor_source", "customer"),
        ("outcome_status", "selected"),
        ("actor_id", "99999999-9999-4999-8999-999999999999"),
    ],
)
def test_submitted_factor_metadata_is_rejected(field: str, value) -> None:
    """The *answer* cannot be supplied by the client.

    ``unit`` / ``scope`` / ``country`` / ``reporting_year`` are deliberately NOT in
    this list: they are policy INPUTS (scoping evidence for candidate lookup), which
    is why they are accepted — but the values *recorded* as the adjudication's factor
    metadata are always the server-selected factor's own, never the request's.
    """
    client, conn = _client(user=_member(), rows=[_declined_row()])
    body = {"organization_id": ORG_A, "activity": "Waste", "clarification": "Landfill"}
    body[field] = value
    assert client.post(
        "/api/v3/activity-clarifications/clarifications", json=body
    ).status_code == 422
    assert conn.params == []


def test_decline_cannot_be_told_it_succeeded_and_rejects_extras() -> None:
    client, conn = _client(user=_member(), rows=[_declined_row()])
    for extra in (
        {"outcome_status": "selected"},
        {"unit": "kg"},
        {"selected_factor_id": None},
    ):
        body = {"organization_id": ORG_A, "activity": "Waste", **extra}
        assert client.post(
            "/api/v3/activity-clarifications/decline", json=body
        ).status_code == 422
    assert conn.params == []


# ---------------------------------------------------------------------------
# Decline semantics + provenance (Parts G, H, I.18–I.20)
# ---------------------------------------------------------------------------


def test_decline_persists_unresolved_declined_without_a_factor() -> None:
    client, conn = _client(user=_member(), rows=[_declined_row()])
    response = client.post(
        "/api/v3/activity-clarifications/decline",
        json={"organization_id": ORG_A, "activity": "Waste", "activity_key": "k1"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["outcome_status"] == "unresolved_declined"
    assert body["selected_factor_id"] is None
    assert body["resolved"] is False
    assert body["actor_id"] == USER  # server-derived, never client-supplied
    assert body["actor_scope"] == "organization_member"
    assert body["clarification_type"] == "declined"

    params = _insert_params(conn)
    assert params[3] == ORG_A  # organisation from the authorised context
    assert params[4] == "Waste"  # original extracted evidence preserved
    assert params[6] == "i_dont_know"  # the user's statement, kept separate


def test_decline_retry_returns_the_stored_adjudication() -> None:
    client, conn = _client(user=_member(), rows=[None, _declined_row()])
    response = client.post(
        "/api/v3/activity-clarifications/decline",
        json={"organization_id": ORG_A, "activity": "Waste", "activity_key": "k1"},
    )
    assert response.status_code == 201
    assert response.json()["outcome_status"] == "unresolved_declined"
    # the replay guard is now the context-bounded effective lookup, then the
    # replay-protected INSERT
    assert "AND is_current" in conn.queries[0]
    assert (
        "ON CONFLICT ON CONSTRAINT activity_clarifications_replay_unique DO NOTHING"
        in conn.queries[1]
    )
    assert "INSERT INTO public.activity_clarifications" in conn.queries[1]


def test_decline_repeated_returns_the_same_state() -> None:
    client, _conn = _client(
        user=_member(), rows=[_declined_row(), _declined_row(), _declined_row()]
    )
    payload = {"organization_id": ORG_A, "activity": "Waste", "activity_key": "k1"}
    first = client.post("/api/v3/activity-clarifications/decline", json=payload)
    second = client.post("/api/v3/activity-clarifications/decline", json=payload)
    assert first.status_code == second.status_code == 201
    assert first.json() == second.json()


# ---------------------------------------------------------------------------
# Options / not-required behaviour (Part E)
# ---------------------------------------------------------------------------


def test_options_reports_state_without_offering_factor_ids() -> None:
    client, _conn = _client(user=_member(), candidates=[])
    response = client.get(
        "/api/v3/activity-clarifications/options",
        params={"organization_id": ORG_A, "activity": "Waste"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["verdict"]
    assert body["clarification_required"] is False  # no eligible candidates → no prompt
    assert body["options"] == []  # options are never invented
    assert "selected_factor_id" not in body


def test_clarification_is_not_adjudicated_when_the_engine_does_not_ask() -> None:
    client, conn = _client(user=_member(), candidates=[])
    response = client.post(
        "/api/v3/activity-clarifications/clarifications",
        json={"organization_id": ORG_A, "activity": "Waste", "clarification": "Landfill"},
    )
    assert response.status_code == 409
    assert conn.params == []  # nothing persisted, nothing guessed


# ---------------------------------------------------------------------------
# F-039-1 (063) B/C — the adjudication reads (current + immutable history)
# ---------------------------------------------------------------------------
# Same construction as above: the REAL router, the REAL authorization gate chain
# (`ensure_processing_org_access` → `ensure_consultant_org_access`) and the REAL
# clarifications repository over a capturing fake connection. Only transport
# dependencies and the scripted database are substituted.

_ITEM = "22222222-2222-4222-8222-222222222222"
_ADJ = "55555555-5555-4555-8555-555555555555"
EFFECTIVE = "/api/v3/activity-clarifications/effective"
HISTORY = "/api/v3/activity-clarifications/history"


def _item_row(*, organization_id: str = ORG_A, activity: str = "Waste") -> dict:
    """The persisted extraction item the read context must be resolved from."""
    return {
        "item_key": _ITEM,
        "batch_key": "33333333-3333-4333-8333-333333333333",
        "source_file_id": "44444444-4444-4444-8444-444444444444",
        "source_file_name": "waste.csv",
        "organization_id": organization_id,
        "extracted_data": {
            "line_items": [{"activity": activity, "unit": "tonnes", "scope": "Scope 3"}]
        },
    }


def _read_row(
    *,
    version: int = 1,
    is_current: bool = True,
    clarification: str = "Landfill",
    organization_id: str = ORG_A,
    activity: str = "Waste",
) -> dict:
    """One persisted adjudication row, as the reads must project it."""
    return {
        "id": f"row-v{version}",
        "adjudication_id": _ADJ,
        "organization_id": organization_id,
        "activity_key": _ITEM,
        "original_activity": activity,
        "effective_context_key": _ITEM,
        "clarification": clarification,
        "clarification_type": "semantic_activity",
        "policy_input": f"{activity} {clarification}",
        "outcome_status": "selected",
        "selected_factor_id": "lf",
        "selected_factor_name": "Waste disposal > Construction > Aggregates - Landfill",
        "factor_set": "DEFRA-2025",
        "factor_source": "DEFRA-DESNZ",
        "reporting_year": 2025,
        "unit": "tonnes",
        "scope": "Scope 3",
        "version": version,
        "is_current": is_current,
        "supersedes_id": None if version == 1 else "row-v1",
        "actor_id": USER,
        "actor_scope": "organization_member",
        "evidence_signature": "signature-v1",
        "re_evaluation_required": False,
        "created_at": "2026-09-18T00:00:00+00:00",
    }


def _params(**over) -> dict:
    base = {"organization_id": ORG_A, "item_id": _ITEM, "activity": "Waste"}
    base.update(over)
    return base


def _adjudication_queries(conn) -> list[str]:
    """Every statement that touched the adjudication table (never a global read)."""
    return [q for q in conn.queries if "public.activity_clarifications" in q]



# -- Part B: the current/effective adjudication read -------------------------


def test_effective_read_returns_the_current_adjudication_for_its_own_org() -> None:
    client, conn = _client(user=_member(), rows=[_item_row(), _read_row()])
    response = client.get(EFFECTIVE, params=_params())
    assert response.status_code == 200
    body = response.json()
    assert body["found"] is True
    assert body["adjudication"]["clarification"] == "Landfill"
    assert body["adjudication"]["version"] == 1
    assert body["adjudication"]["is_current"] is True
    assert body["adjudication"]["selected_factor_id"] == "lf"
    # the bounded context, not the activity text alone
    effective = [q for q in conn.queries if "AND is_current" in q]
    assert len(effective) == 1
    for clause in ("organization_id = $1", "effective_context_key = $2",
                   "activity_key = $3", "original_activity = $4"):
        assert clause in effective[0]
    assert conn.params[1] == (ORG_A, _ITEM, _ITEM, "Waste")


def test_effective_read_is_denied_for_another_organization() -> None:
    client, conn = _client(user=_member(), rows=[_item_row(), _read_row()])
    response = client.get(EFFECTIVE, params=_params(organization_id=ORG_B))
    assert response.status_code == 403
    assert conn.params == []  # refused before any read


def test_effective_read_is_denied_when_the_item_belongs_to_another_org() -> None:
    """Authorized for ORG_A, but the item resolves to ORG_B → the boundary holds."""
    client, conn = _client(user=_member(), rows=[_item_row(organization_id=ORG_B)])
    response = client.get(EFFECTIVE, params=_params())
    assert response.status_code == 403
    assert "another organisation" in response.json()["detail"]
    assert _adjudication_queries(conn) == []  # no adjudication was read


def test_effective_read_allows_an_authorized_consultant_client() -> None:
    client, conn = _client(
        user=_consultant(), rows=[_item_row(), _read_row()], **_consultant_grants()
    )
    response = client.get(EFFECTIVE, params=_params())
    assert response.status_code == 200
    assert response.json()["found"] is True
    assert conn.params[1][0] == ORG_A


def test_effective_read_denies_an_unauthorized_consultant_client() -> None:
    # active membership + firm profile, but the grant covers only ORG_A
    client, conn = _client(user=_consultant(), rows=[_item_row(), _read_row()],
                           **_consultant_grants())
    assert client.get(EFFECTIVE, params=_params(organization_id=ORG_B)).status_code == 403
    # an ended grant is no grant at all
    ended, ended_conn = _client(user=_consultant(), rows=[_item_row(), _read_row()],
                               **_consultant_grants(grant_status="ended"))
    assert ended.get(EFFECTIVE, params=_params()).status_code == 403
    # a consultant with no firm membership at all
    none, _c = _client(user=_consultant(), rows=[_item_row(), _read_row()])
    assert none.get(EFFECTIVE, params=_params()).status_code == 403
    assert conn.params == [] and ended_conn.params == []


def test_effective_read_is_denied_when_unauthenticated() -> None:
    client, conn = _client(rows=[_item_row(), _read_row()])
    response = client.get(EFFECTIVE, params=_params())
    assert response.status_code == 401
    assert conn.params == []


def test_effective_read_reports_an_unknown_context_as_not_found() -> None:
    client, conn = _client(user=_member(), rows=[None])
    response = client.get(EFFECTIVE, params=_params())
    assert response.status_code == 404
    assert "item not found" in response.json()["detail"]
    assert _adjudication_queries(conn) == []


def test_effective_read_reports_no_current_adjudication_as_an_empty_answer() -> None:
    client, conn = _client(user=_member(), rows=[_item_row()])
    response = client.get(EFFECTIVE, params=_params())
    assert response.status_code == 200
    assert response.json() == {"found": False, "adjudication": None}
    assert any("AND is_current" in q for q in conn.queries)


def test_effective_read_requires_the_item_bounded_context() -> None:
    """No item → no context: the read cannot be widened to a global lookup."""
    client, conn = _client(user=_member(), rows=[_item_row(), _read_row()])
    response = client.get(EFFECTIVE, params={"organization_id": ORG_A, "activity": "Waste"})
    assert response.status_code == 422
    assert conn.params == []



# -- Part C: the immutable history read --------------------------------------


def _history_params(**over) -> dict:
    return _params(adjudication_id=_ADJ, **over)


def test_history_read_returns_a_single_version() -> None:
    client, conn = _client(user=_member(), rows=[_item_row(), _read_row(), [_read_row()]])
    response = client.get(HISTORY, params=_history_params())
    assert response.status_code == 200
    body = response.json()
    assert body["adjudication_id"] == _ADJ
    assert body["count"] == 1
    assert body["current_version"] == 1
    assert [v["version"] for v in body["versions"]] == [1]
    assert body["versions"][0]["is_current"] is True
    assert "ORDER BY version ASC" in conn.queries[-1]


def test_history_read_returns_every_version_in_deterministic_order() -> None:
    v1 = _read_row(version=1, is_current=False, clarification="Incineration")
    v2 = _read_row(version=2, is_current=True, clarification="Landfill")
    client, conn = _client(user=_member(), rows=[_item_row(), _read_row(), [v1, v2]])
    response = client.get(HISTORY, params=_history_params())
    assert response.status_code == 200
    body = response.json()
    assert body["count"] == 2
    assert [v["version"] for v in body["versions"]] == [1, 2]  # oldest → newest
    # v2 is the current one; v1 stays historical
    assert body["current_version"] == 2
    assert body["versions"][0]["is_current"] is False
    assert body["versions"][1]["is_current"] is True
    assert body["versions"][1]["clarification"] == "Landfill"
    # the deterministic order and the tenant scope come from the repository's SQL
    history_sql = conn.queries[-1]
    assert "ORDER BY version ASC" in history_sql
    assert "organization_id = $1" in history_sql
    assert conn.params[-1] == (ORG_A, _ADJ)


def test_history_read_never_mutates_the_stored_versions() -> None:
    v1 = _read_row(version=1, is_current=False, clarification="Incineration")
    v2 = _read_row(version=2, is_current=True, clarification="Landfill")
    snapshot = (dict(v1), dict(v2))
    client, _conn = _client(user=_member(), rows=[_item_row(), _read_row(), [v1, v2]])
    body = client.get(HISTORY, params=_history_params()).json()
    assert (v1, v2) == snapshot  # the read is a projection, not an edit
    # v1's own fields are echoed exactly as stored
    assert body["versions"][0]["clarification"] == "Incineration"
    assert body["versions"][0]["outcome_status"] == "selected"
    assert body["versions"][0]["selected_factor_id"] == "lf"



def test_history_read_is_denied_for_another_organization() -> None:
    client, conn = _client(user=_member(), rows=[_item_row(), _read_row(), [_read_row()]])
    response = client.get(HISTORY, params=_history_params(organization_id=ORG_B))
    assert response.status_code == 403
    assert conn.params == []


def test_history_read_allows_an_authorized_consultant_client() -> None:
    client, conn = _client(
        user=_consultant(), rows=[_item_row(), _read_row(), [_read_row()]],
        **_consultant_grants(),
    )
    response = client.get(HISTORY, params=_history_params())
    assert response.status_code == 200
    assert response.json()["count"] == 1
    assert conn.params[-1] == (ORG_A, _ADJ)


def test_history_read_denies_an_unauthorized_consultant_client() -> None:
    client, conn = _client(user=_consultant(), rows=[_item_row(), _read_row(), [_read_row()]])
    assert client.get(HISTORY, params=_history_params()).status_code == 403
    ended, ended_conn = _client(
        user=_consultant(), rows=[_item_row(), _read_row(), [_read_row()]],
        **_consultant_grants(grant_status="ended"),
    )
    assert ended.get(HISTORY, params=_history_params()).status_code == 403
    # an ended/no grant must not be usable against the other organisation either
    assert client.get(
        HISTORY, params=_history_params(organization_id=ORG_B)
    ).status_code == 403
    assert conn.params == [] and ended_conn.params == []


def test_history_read_is_denied_when_unauthenticated() -> None:
    client, conn = _client(rows=[_item_row(), _read_row(), [_read_row()]])
    response = client.get(HISTORY, params=_history_params())
    assert response.status_code == 401
    assert conn.params == []


def test_history_read_refuses_an_adjudication_outside_the_bounded_context() -> None:
    """A well-formed id from ANOTHER context is refused: never a global history read."""
    other = _read_row()
    other["activity_key"] = "other-item"
    other["effective_context_key"] = "other-item"
    client, conn = _client(user=_member(), rows=[_item_row(), other, [_read_row()]])
    response = client.get(HISTORY, params=_history_params())
    assert response.status_code == 404
    assert "this extraction context" in response.json()["detail"]
    assert not any("ORDER BY version" in q for q in conn.queries)  # history never read


def test_history_read_refuses_an_adjudication_for_a_different_activity() -> None:
    other = _read_row(activity="Waste disposal")
    client, conn = _client(user=_member(), rows=[_item_row(), other, [_read_row()]])
    assert client.get(HISTORY, params=_history_params()).status_code == 404
    assert not any("ORDER BY version" in q for q in conn.queries)


def test_history_read_reports_an_unknown_adjudication_or_item_as_not_found() -> None:
    unknown, _conn = _client(user=_member(), rows=[_item_row(), None, [_read_row()]])
    assert unknown.get(HISTORY, params=_history_params()).status_code == 404
    unknown_item, _conn2 = _client(user=_member(), rows=[None])
    response = unknown_item.get(HISTORY, params=_history_params())
    assert response.status_code == 404
    assert "item not found" in response.json()["detail"]


def test_both_reads_are_tenant_scoped_without_a_global_lookup() -> None:
    effective, effective_conn = _client(user=_member(), rows=[_item_row(), _read_row()])
    assert effective.get(EFFECTIVE, params=_params()).status_code == 200
    history, history_conn = _client(
        user=_member(), rows=[_item_row(), _read_row(), [_read_row()]]
    )
    assert history.get(HISTORY, params=_history_params()).status_code == 200
    for conn in (effective_conn, history_conn):
        queries = _adjudication_queries(conn)
        assert queries, "the adjudication table must have been read"
        for query in queries:
            assert "organization_id = $1" in query   # one tenant, always
            assert "WHERE" in query.upper()



# ---------------------------------------------------------------------------
# F-039-1 remediation (065) — malformed identifiers are input errors, not 500s
# ---------------------------------------------------------------------------
# The schema stores these identifiers in uuid columns, so a non-uuid value used to reach
# asyncpg and raise DataError, which the endpoints do not translate: the caller saw a 500
# for a plain input error. The boundary now rejects the shape with the project's normal
# 422 validation response and no statement is executed.


def test_write_endpoints_reject_malformed_identifiers_with_422() -> None:
    for endpoint in (CLARIFY, DECLINE):
        body = {"organization_id": "not-a-uuid", "activity": "Waste"}
        if endpoint == CLARIFY:
            body["clarification"] = "Landfill"
        client, conn = _client(user=_member(), candidates=[])
        response = client.post(endpoint, json=body)
        assert response.status_code == 422, f"{endpoint}: {response.status_code}"
        assert conn.params == []  # rejected before any statement

        body = {"organization_id": ORG_A, "activity": "Waste", "item_id": "12345"}
        if endpoint == CLARIFY:
            body["clarification"] = "Landfill"
        client, conn = _client(user=_member(), candidates=[])
        response = client.post(endpoint, json=body)
        assert response.status_code == 422, f"{endpoint}: {response.status_code}"
        assert conn.params == []


def test_read_endpoints_reject_malformed_identifiers_with_422() -> None:
    for path, extra in ((EFFECTIVE, {}), (HISTORY, {"adjudication_id": _ADJ})):
        client, conn = _client(user=_member(), rows=[_item_row()])
        response = client.get(path, params={**_params(), **extra, "organization_id": "nope"})
        assert response.status_code == 422, f"{path}: {response.status_code}"
        assert conn.params == []

        client, conn = _client(user=_member(), rows=[_item_row()])
        response = client.get(path, params={**_params(), **extra, "item_id": "nope"})
        assert response.status_code == 422, f"{path}: {response.status_code}"
        assert conn.params == []

    client, conn = _client(user=_member(), rows=[_item_row(), _read_row()])
    response = client.get(HISTORY, params={**_params(), "adjudication_id": "nope"})
    assert response.status_code == 422
    assert conn.params == []


def test_well_formed_identifiers_are_passed_through_unchanged() -> None:
    """The boundary check must not alter a valid identifier (context keys stay textual)."""
    client, conn = _client(user=_member(), rows=[_item_row(), _read_row()])
    response = client.get(EFFECTIVE, params=_params())
    assert response.status_code == 200 and response.json()["found"] is True
    assert conn.params[1] == (ORG_A, _ITEM, _ITEM, "Waste")

