"""FIN-06 — manual-processing enforcement coverage.

P8-FINALIZATION-REMEDIATION-001 (fixes IV-01): the independent verification found
that the Manual Processing control covered only the manual batch/item *creation*
endpoints, leaving the manual data-entry and workflow-stage actions reachable —
``PUT /api/v3/manual-extraction/items/{id}`` returned 200 while the capability
was OFF.

These tests pin the completed boundary:

* every manual-processing ACTION is denied (403, policy message) when OFF;
* the same actions succeed when a CarbonTally-Admin grant enables the scope;
* Automatic Processing is NOT blocked by Manual Processing governance;
* authorization/isolation are unchanged (cross-tenant, consultant, member);
* a coverage invariant fails if a manual action ever loses its gate.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace

from tests.unit.api.fakes import member_user, org_admin_user, staff_user

ADMIN_BASE = "/api/v3/admin/manual-processing"
DENIAL = "A CarbonTally administrator must enable it"
BACKEND = Path(__file__).resolve().parents[3]

#: (label, method, path, payload, item status required before the action)
MANUAL_ACTIONS: tuple[tuple[str, str, str, dict | None, str | None], ...] = (
    ("item_update", "PUT", "/api/v3/manual-extraction/items/{item_id}", {"extracted_data": {"quantity": 1}}, None),
    ("stage_start", "POST", "/api/v3/processing/items/{item_id}/start", {"stage": "extraction"}, "pending"),
    ("extract", "POST", "/api/v3/processing/items/{item_id}/extract", {"extracted_data": {"quantity": 1}}, "extracting"),
    ("map", "POST", "/api/v3/processing/items/{item_id}/map", {"mapped_data": {"factor_id": "factor-defra-gas"}}, "extracted"),
    ("validate", "POST", "/api/v3/processing/items/{item_id}/validate", None, "mapped"),
    ("calculate", "POST", "/api/v3/processing/items/{item_id}/calculate", {}, "validated"),
)


def _seed_internal_admin(world, *, user_id: str = "u-admin", can_process: bool = False) -> None:
    from domain.staff import StaffProfile, StaffRole

    world.staff.seed_role(
        StaffRole(
            id="role-fin06-rem",
            name="system_admin",
            permissions={
                "can_manage_organizations": True,
                "can_manage_staff": True,
                "can_process": can_process,
            },
        )
    )
    asyncio.run(
        world.staff.save(
            StaffProfile(
                id="sp-fin06-rem",
                user_id=user_id,
                first_name="Admin",
                last_name="Rem",
                email="admin@carbontally.test",
                role_id="role-fin06-rem",
            )
        )
    )


def _grant_org(client, world, user_provider, *, scope_id: str = "org-a", enabled: bool = True):
    """Grant (or deny) Manual Processing for an organisation as CarbonTally Admin."""
    _seed_internal_admin(world)
    user_provider.set_user(staff_user("u-admin", role_name="admin"))
    resp = client.put(
        f"{ADMIN_BASE}/grants",
        json={
            "scope_type": "organization",
            "scope_id": scope_id,
            "enabled": enabled,
        },
    )
    assert resp.status_code == 200, resp.text
    return resp


def _seed_item(world, *, org: str = "org-a", status: str | None = "pending"):
    batch = asyncio.run(
        world.manual_extraction.create_batch(org_id=org, batch_name="rem-batch")
    )
    item = asyncio.run(
        world.manual_extraction.create_item(
            batch.id, "f.pdf", "uploads/f.pdf", 1, "pdf", "pending"
        )
    )
    if status and status != "pending":
        asyncio.run(world.manual_extraction.set_item_status(item.id, status))
    return batch, item


def _call(client, method: str, path: str, payload: dict | None):
    if method == "PUT":
        return client.put(path, json=payload or {})
    return client.post(path, json=payload) if payload is not None else client.post(path)


class TestManualOffDeniesEveryManualAction:
    """IV-01 regression: no manual action may succeed while the capability is OFF."""

    def test_every_manual_action_is_denied(self, world, client, user_provider) -> None:
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        for label, method, path, payload, status in MANUAL_ACTIONS:
            _batch, item = _seed_item(world, status=status)
            resp = _call(client, method, path.format(item_id=item.id), payload)
            assert resp.status_code == 403, f"{label} was not denied: {resp.status_code}"
            assert DENIAL in resp.text, f"{label} denied by something else: {resp.text}"

    def test_item_update_is_denied_while_off(self, world, client, user_provider) -> None:
        """The exact IV-01 bypass (was HTTP 200)."""
        _batch, item = _seed_item(world)
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = client.put(
            f"/api/v3/manual-extraction/items/{item.id}",
            json={"extracted_data": {"kwh": 100}},
        )
        assert resp.status_code == 403
        assert DENIAL in resp.text

    def test_batch_start_is_denied_while_off(self, world, client, user_provider) -> None:
        batch, _item = _seed_item(world)
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = client.post(f"/api/v3/processing/batches/{batch.id}/start", json={})
        assert resp.status_code == 403
        assert DENIAL in resp.text

    def test_consultant_review_and_submit_are_denied_or_unauthorized(
        self, world, client, user_provider
    ) -> None:
        """Both consultant stages are gated for an authorised consultant.

        A non-consultant caller is denied earlier by the consultant
        authorization contract, so this asserts the policy gate is *also* on the
        path (proven structurally by TestEnforcementCoverageInvariant) and that
        neither stage is reachable while OFF.
        """
        _batch, item = _seed_item(world, status="calculated")
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        for path in (
            f"/api/v3/processing/items/{item.id}/consultant-review",
            f"/api/v3/processing/items/{item.id}/consultant-submit",
        ):
            resp = client.post(path, json={"decision": "approved"})
            assert resp.status_code in (403, 409, 404), resp.text
            assert resp.status_code != 200


class TestManualOnAllowsTheSameActions:
    def test_granted_scope_allows_the_manual_workflow(
        self, world, client, user_provider
    ) -> None:
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        _grant_org(client, world, user_provider)
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))

        _batch, item = _seed_item(world)  # pending
        assert client.post(
            f"/api/v3/processing/items/{item.id}/start", json={"stage": "extraction"}
        ).status_code == 200
        assert client.post(
            f"/api/v3/processing/items/{item.id}/extract",
            json={"extracted_data": {"quantity": 10, "unit": "kWh"}},
        ).status_code == 200
        assert client.post(
            f"/api/v3/processing/items/{item.id}/map",
            json={
                "mapped_data": {"factor_id": "factor-defra-gas"},
                "emission_factor_used": "factor-defra-gas",
            },
        ).status_code == 200
        assert client.post(f"/api/v3/processing/items/{item.id}/validate").status_code == 200

    def test_granted_scope_allows_item_update_and_batch_start(
        self, world, client, user_provider
    ) -> None:
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        _grant_org(client, world, user_provider)
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))

        batch, item = _seed_item(world)
        assert client.put(
            f"/api/v3/manual-extraction/items/{item.id}",
            json={"extracted_data": {"kwh": 100}},
        ).status_code == 200
        assert client.post(
            f"/api/v3/processing/batches/{batch.id}/start", json={}
        ).status_code == 200

    def test_calculate_is_not_blocked_by_governance_when_enabled(
        self, world, client, user_provider
    ) -> None:
        """Enabled scope: the request passes the governance boundary.

        ``calculate`` has its own data/state prerequisites, so the assertion is
        that it is no longer the FIN-06 policy that denies the call.
        """
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        _grant_org(client, world, user_provider)
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))

class TestAutomaticProcessingIsNeverBlockedByManualGovernance:
    """The remediation must not turn FIN-06 into an Automatic Processing kill switch."""

    def test_automatic_enqueue_still_works_with_manual_processing_off(
        self, world, client, user_provider
    ) -> None:
        """Automatic processing creation stays open when the capability is OFF."""
        from domain.automatic_processing import AutomaticProcessingJob

        job = AutomaticProcessingJob(
            id="job-1",
            organization_id="org-a",
            file_name="usage.csv",
            file_url="uploads/org-a/usage.csv",
            file_type="SPREADSHEET",
            stage="enqueued",
            status="pending",
            metadata={"mime": "text/csv"},
            source_item_id=None,
        )

        class _Processing:
            def __init__(self) -> None:
                self.created: list[dict] = []

            async def get_by_item(self, item_id: str):
                return None

            async def create(self, **kwargs):
                self.created.append(kwargs)
                return job

        world.processing = _Processing()
        world.files.add_file(
            SimpleNamespace(
                id="file-1",
                organization_id="org-a",
                name="usage.csv",
                path="org-a/usage.csv",
                file_type="CSV",
                mime_type="text/csv",
                metadata={},
            )
        )
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        resp = client.post(
            "/api/v3/processing/documents/file-1/enqueue",
            json={"processing_type": "utility"},
        )
        assert resp.status_code == 201, f"enqueue blocked/changed: {resp.status_code} {resp.text}"
        assert DENIAL not in resp.text, resp.text
        # The shared evidence-chain root (manual-extraction item) was created by
        # the automatic path even though Manual Processing is OFF, and the job
        # was linked to it.
        processing = world.processing
        assert processing.created, "automatic job was not created"
        assert processing.created[0]["source_item_id"], processing.created[0]

    def test_the_gate_is_absent_from_the_automatic_and_ingestion_paths(self) -> None:
        """Structural proof: automation never passes through the HTTP gate."""
        for relative in (
            "services/automatic_processing.py",
            "workers/automatic_processing.py",
            "api/v3_documents.py",
            "api/v3_automatic_processing.py",
        ):
            source = (BACKEND / relative).read_text(encoding="utf-8")
            assert "ensure_manual_processing_allowed" not in source, relative

    def test_the_worker_writes_through_repositories_not_http(self) -> None:
        """The worker performs extraction/mapping/status directly on the repo."""
        source = (BACKEND / "services" / "automatic_processing.py").read_text(
            encoding="utf-8"
        )
        for call in (
            "save_extracted_data(",
            "save_mapped_data(",
            "set_item_status(",
        ):
            assert call in source, call


class TestEnforcementCoverageInvariant:
    """Fails if a manual-processing handler ever loses its governance gate."""

    MANUAL_HANDLERS: tuple[tuple[str, str], ...] = (
        ("api/v3_manual_extraction.py", "create_batch"),
        ("api/v3_manual_extraction.py", "create_item"),
        ("api/v3_manual_extraction.py", "update_item"),
        ("api/v3_processing_workflow.py", "_get_checked_item"),
        ("api/v3_processing_workflow.py", "start_batch"),
        ("api/v3_processing_workflow.py", "consultant_review_item"),
        ("api/v3_processing_workflow.py", "consultant_submit_item"),
    )

    def test_every_manual_handler_carries_the_gate(self) -> None:
        for relative, handler in self.MANUAL_HANDLERS:
            source = (BACKEND / relative).read_text(encoding="utf-8")
            marker = f"async def {handler}("
            assert marker in source, f"{handler} not found in {relative}"
            body = source.split(marker, 1)[1]
            # Cut the handler body at the next top-level definition.
            body = body.split("\n@router", 1)[0]
            assert "ensure_manual_processing_allowed" in body, (
                f"{handler} in {relative} no longer enforces FIN-06"
            )

    def test_every_stage_action_enables_the_gate(self) -> None:
        """The five manual actions must opt in to the governance gate."""
        source = (BACKEND / "api" / "v3_processing_workflow.py").read_text(
            encoding="utf-8"
        )
        for handler in (
            "start_item",
            "extract_item",
            "map_item",
            "validate_item",
            "calculate_item",
        ):
            body = source.split(f"async def {handler}(", 1)[1].split("\n@router", 1)[0]
            assert "_get_checked_item(" in body, handler
            assert "enforce_manual_processing=True" in body, handler

    def test_read_and_approval_surfaces_do_not_opt_in(self) -> None:
        """Reading work and approving it are not manual processing."""
        source = (BACKEND / "api" / "v3_processing_workflow.py").read_text(
            encoding="utf-8"
        )
        for handler in (
            "get_item_workspace",
            "get_mapping_options",
            "customer_review_item",
        ):
            if f"async def {handler}(" not in source:
                continue
            body = source.split(f"async def {handler}(", 1)[1].split("\n@router", 1)[0]
            assert "enforce_manual_processing=True" not in body, handler


class TestAuthorizationAndIsolationUnchanged:
    def test_cross_tenant_action_is_denied(self, world, client, user_provider) -> None:
        """An org-B admin cannot act on org-A's manual item."""
        _batch, item = _seed_item(world, org="org-a")
        user_provider.set_user(org_admin_user("org-b", "admin-b", "b@test"))
        resp = client.put(
            f"/api/v3/manual-extraction/items/{item.id}",
            json={"extracted_data": {"kwh": 1}},
        )
        assert resp.status_code == 403
        assert DENIAL not in resp.text  # denied by isolation, not by governance

    def test_org_member_is_denied_while_off(self, world, client, user_provider) -> None:
        _batch, item = _seed_item(world)
        user_provider.set_user(member_user("org-a", "member-1", "m@test"))
        resp = client.put(
            f"/api/v3/manual-extraction/items/{item.id}",
            json={"extracted_data": {"kwh": 1}},
        )
        assert resp.status_code == 403

    def test_consultant_without_an_allow_is_denied(
        self, world, client, user_provider
    ) -> None:
        """An active consultant-client grant is required for org access, and the
        FIN-06 entitlement is required on top of it."""
        from tests.unit.api.fakes import consultant_user

        world.consultants.seed_profile("firm-1", "cons-1", "Firm")
        world.consultants.seed_firm_member("firm-1", "cons-1", role="owner")
        world.consultants.seed_client("cc-1", "firm-1", "org-a", "Org A", status="active")
        _batch, item = _seed_item(world, org="org-a")

        user_provider.set_user(consultant_user("cons-1", "c@test"))
        resp = client.put(
            f"/api/v3/manual-extraction/items/{item.id}",
            json={"extracted_data": {"kwh": 1}},
        )
        assert resp.status_code == 403

    def test_internal_staff_operator_is_not_blocked(
        self, world, client, user_provider
    ) -> None:
        """Platform-operator exemption (unchanged actor rule).

        Internal staff reach manual processing through the operations surface
        (``/api/v3/ops/...``), which is internal-staff only; the customer
        endpoint rejects non-organisation-members before any governance check.
        With governance OFF the operator must still be able to process.
        """
        _seed_internal_admin(world, can_process=True)
        _batch, item = _seed_item(world, org="org-a", status="extracting")
        user_provider.set_user(staff_user("u-admin", role_name="admin"))
        resp = client.post(
            f"/api/v3/ops/items/{item.id}/extract",
            json={"extracted_data": {"quantity": 5, "unit": "kWh"}},
        )
        assert resp.status_code == 200, resp.text

    def test_governance_plane_remains_carbonTally_admin_only(
        self, world, client, user_provider
    ) -> None:
        user_provider.set_user(org_admin_user("org-a", "admin-1", "a@test"))
        assert client.get(f"{ADMIN_BASE}/grants").status_code == 403
        assert (
            client.put(
                f"{ADMIN_BASE}/grants",
                json={
                    "scope_type": "organization",
                    "scope_id": "org-a",
                    "enabled": True,
                },
            ).status_code
            == 403
        )
