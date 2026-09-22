"""PO-authorized shared Source Evidence Viewer — backend surface tests.

Covers, in memory and with no database:

* the DM-6 authorization posture for the new resolution route (Owner/Admin FULL,
  Member/Viewer CONTROLLED, Consultant BOUNDED at the policy level, PE/internal
  staff denied, cross-organisation denied, re-authorization on every read);
* that the signed source-document URL cannot be obtained below FULL depth;
* bounded evidence-line resolution (valid / missing / foreign) with an allowlist
  and no raw row dump;
* authoritative source-location semantics (PDF page, CSV row, XLSX sheet+row,
  unavailable) and the rule that an evidence ordinal is never a physical row;
* the historical ``source_page`` correction (a page *count* is never presented as
  a verified location, on the line route and on the D33 evidence route).
"""
from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from auth import AuthUser
from tests.unit.api.fakes import (
    entity_operator_user,
    member_user,
    org_admin_user,
    org_owner_user,
    org_viewer_user,
    staff_user,
)

ORG = "org-a"
OTHER_ORG = "org-b"
LINE_ID = "line-a-3"
ITEM_ID = "item-a"
FILE_ID = "file-a"

#: A PDF-derived line: ordinal 3, authoritative page 2.
PDF_LINE = {
    "id": LINE_ID,
    "organization_id": ORG,
    "source_item_id": ITEM_ID,
    "source_file_id": FILE_ID,
    "line_number": 3,
    "source_page": 2,
    "row_reference": None,
    "raw_description": "Waste disposal 60 t",
    "raw_quantity": Decimal("60.0"),
    "raw_unit": "t",
    "payload_hash": "sha256-deadbeef",
    "extraction_method": "pdf_text",
    "materialisation_kind": "FORWARD",
    "created_at": "2026-05-08T00:00:00+00:00",
}

PDF_EXTRACTED = {
    "supplier": "Pure Energy PLC",
    "invoice_number": "INV-10482",
    "line_items": [
        {"activity": "Gas usage", "quantity": 5362.2, "unit": "kwh", "page": 1,
         "source_line": "Gas usage 5,362.2000 kWh"},
        {"activity": "Diesel supply", "quantity": 4434.4, "unit": "l", "page": 2,
         "source_line": "Diesel supply 4,434.4000 L"},
        {"activity": "Waste disposal", "quantity": 60.0, "unit": "t", "page": 2,
         "source_line": "Waste disposal 60 t"},
    ],
}


def _install(world, *, org_id: str = ORG, extracted: dict | None = None,
             line: dict | None = None) -> dict:
    """Wire the in-memory line → item → document chain; returns the seeded line."""
    seeded = dict(line or PDF_LINE)
    seeded["organization_id"] = seeded.get("organization_id", org_id)
    world.evidence_line_items.seed(seeded)

    payload = extracted if extracted is not None else PDF_EXTRACTED

    async def items_get(item_id: str):
        return SimpleNamespace(
            id=item_id,
            file_name="INV-10482.pdf",
            file_url="uploads/org-a/2026/05/inv-10482.pdf",
            file_id=FILE_ID,
            page_count=8,
            document_type="utility",
            status="approved",
            extracted_data=payload,
            mapped_data={"activity_type": "Diesel"},
            calculated_emissions_kg_co2e=Decimal("150.4"),
        )

    async def files_get(file_id: str):
        return SimpleNamespace(
            id=file_id,
            organization_id=org_id,
            name="INV-10482.pdf",
            path="uploads/org-a/2026/05/inv-10482.pdf",
            file_type="PDF",
            size_bytes=2048,
            uploaded_by="u-a",
            uploaded_at=None,
            metadata={"data_type": "utility"},
        )

    world.manual_extraction.get_item = items_get
    world.files.get = files_get
    world.files.get_by_path = files_get
    return seeded


def _seed_calculation(world, *, line_id: str = LINE_ID, org_id: str = ORG) -> None:
    world.logs.seed_line_snapshots(
        [
            {
                "id": "snap-a",
                "organization_id": org_id,
                "source_item_id": ITEM_ID,
                "source_line_item_id": line_id,
                "activity": "Waste disposal",
                "activity_type": "Waste disposal",
                "quantity": Decimal("60.0"),
                "quantity_unit": "t",
                "co2e_kg": Decimal("150.4"),
                "scope": "Scope 3",
                "date": "2026-05-08",
                "reporting_year": 2026,
                "methodology": "direct_multiply",
                "algorithm_version": "1.0",
                "content_hash": "hash-a",
                "calculated_at": "2026-05-08T10:00:00+00:00",
            }
        ]
    )


def _signed(monkeypatch, value: str = "https://signed/x") -> None:
    monkeypatch.setattr("services.storage.storage_signed_url", lambda *a, **k: value)


def _url(line_id: str = LINE_ID) -> str:
    return f"/api/v3/evidence/line-items/{line_id}"


# ---------------------------------------------------------------------------
# Authorization — DM-6 posture preserved, never broadened
# ---------------------------------------------------------------------------


def test_owner_gets_full_depth_including_the_signed_document(
    client, world, user_provider, monkeypatch
):
    _install(world)
    _signed(monkeypatch)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    resp = client.get(_url())

    assert resp.status_code == 200
    body = resp.json()
    assert body["access"]["drill_down_depth"] == "FULL"
    assert body["access"]["document_references_available"] is True
    assert body["document"]["signed_url"] == "https://signed/x"
    assert body["document"]["path"] == "uploads/org-a/2026/05/inv-10482.pdf"
    assert body["location"]["page"] == 2
    assert body["location"]["page_state"] == "verified"


def test_admin_gets_full_depth(client, world, user_provider, monkeypatch):
    _install(world)
    _signed(monkeypatch)
    user_provider.set_user(org_admin_user(ORG, "u-admin", "admin@example.test"))

    resp = client.get(_url())

    assert resp.status_code == 200
    body = resp.json()
    assert body["access"]["drill_down_depth"] == "FULL"
    assert body["document"]["signed_url"] == "https://signed/x"


def test_member_is_controlled_and_never_receives_a_signed_url(
    client, world, user_provider, monkeypatch
):
    _install(world)
    _signed(monkeypatch)
    user_provider.set_user(member_user(ORG, "u-member", "member@example.test"))

    resp = client.get(_url())

    assert resp.status_code == 200
    body = resp.json()
    assert body["access"]["drill_down_depth"] == "CONTROLLED"
    assert body["access"]["document_references_available"] is False
    # The signed URL EXISTS for a FULL caller (asserted elsewhere) but must not be
    # obtainable here — the storage pointer never bypasses authorization.
    assert body["document"]["signed_url"] == ""
    assert "path" not in body["document"]
    assert "metadata" not in body["document"]
    # A page/sheet/row is a document reference: withheld, not nulled, and explained.
    assert body["location"]["state"] == "restricted"
    assert "page" not in body["location"]


def test_viewer_is_controlled(client, world, user_provider, monkeypatch):
    _install(world)
    _signed(monkeypatch)
    user_provider.set_user(org_viewer_user(ORG, "u-viewer", "viewer@example.test"))

    resp = client.get(_url())

    assert resp.status_code == 200
    body = resp.json()
    assert body["access"]["drill_down_depth"] == "CONTROLLED"
    assert body["document"]["signed_url"] == ""
    assert body["location"]["state"] == "restricted"


def test_processing_entity_staff_are_denied(client, world, user_provider):
    _install(world)
    user_provider.set_user(entity_operator_user("entity-a"))

    assert client.get(_url()).status_code == 403


def test_internal_staff_are_denied(client, world, user_provider):
    _install(world)
    user_provider.set_user(staff_user("u-staff", email="staff@example.test"))

    assert client.get(_url()).status_code == 403


def test_unrecognised_organisation_role_is_denied_by_dm6(client, world, user_provider):
    _install(world)
    user_provider.set_user(
        AuthUser(
            user_id="u-other",
            email="other@example.test",
            role="org_auditor",
            role_name="org_auditor",
            organization_id=ORG,
            is_org_member=True,
        )
    )

    resp = client.get(_url())

    assert resp.status_code == 403
    assert "DM-6" in resp.text


def test_cross_organization_line_is_denied(client, world, user_provider, monkeypatch):
    _install(world)
    _signed(monkeypatch)
    # A Member (allowed depth) of a DIFFERENT organisation must not read this line.
    user_provider.set_user(member_user(OTHER_ORG, "u-b", "b@example.test"))

    assert client.get(_url()).status_code == 403


def test_authorization_is_reapplied_on_every_read(client, world, user_provider, monkeypatch):
    _install(world)
    _signed(monkeypatch)

    user_provider.set_user(member_user(ORG, "u-member", "member@example.test"))
    member_body = client.get(_url()).json()

    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))
    owner_body = client.get(_url()).json()

    # No decision was cached from the first read: the same locator yields the
    # second caller's own depth.
    assert member_body["document"]["signed_url"] == ""
    assert owner_body["document"]["signed_url"] == "https://signed/x"
    assert member_body["access"]["drill_down_depth"] == "CONTROLLED"
    assert owner_body["access"]["drill_down_depth"] == "FULL"


def test_consultant_depth_is_bounded_at_the_policy_level(client, world, user_provider):
    """DM-6 BOUNDED is preserved (and is exercised at the policy level).

    A consultant is not an organisation member, so the customer evidence surfaces
    refuse them at the existing dependency (no I2 change is made here). The
    ratified BOUNDED projection itself is asserted directly against the single
    shared matrix.
    """
    from domain.disclosure_exposure import exposure_for_role, project_lines

    rule = exposure_for_role("consultant")
    assert rule.depth == "BOUNDED"
    assert rule.allow_lines is True
    assert rule.allow_amounts is False
    assert rule.allow_document_refs is False

    projected = project_lines([PDF_LINE], rule)[0]
    assert projected["id"] == LINE_ID
    assert projected["line_number"] == 3
    assert "raw_quantity" not in projected      # amounts withheld
    assert "source_page" not in projected       # document reference withheld
    assert "raw_description" not in projected   # free text withheld

    _install(world)
    user_provider.set_user(
        AuthUser(
            user_id="u-consultant",
            email="consultant@example.test",
            role="consultant",
            role_name="consultant",
            organization_id=None,
            is_org_member=False,
        )
    )
    assert client.get(_url()).status_code == 403


# ---------------------------------------------------------------------------
# Evidence resolution — bounded, allowlisted, non-disclosing
# ---------------------------------------------------------------------------


def test_valid_line_resolves_with_allowlisted_provenance(
    client, world, user_provider, monkeypatch
):
    _install(world)
    _signed(monkeypatch)
    _seed_calculation(world)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    body = client.get(_url()).json()

    assert body["evidence_line_item_id"] == LINE_ID
    assert body["source_item_id"] == ITEM_ID
    assert body["materialisation_kind"] == "FORWARD"
    assert body["line"]["id"] == LINE_ID
    assert body["line"]["line_number"] == 3
    assert body["line"]["raw_description"] == "Waste disposal 60 t"
    assert body["document"]["name"] == "INV-10482.pdf"
    assert body["document_available"] is True
    # Bounded calculation context for the same line.
    assert [c["id"] for c in body["calculations"]] == ["snap-a"]
    assert body["calculations"][0]["co2e_kg"] == "150.4"


def test_response_exposes_no_arbitrary_columns(client, world, user_provider, monkeypatch):
    _install(world)
    _signed(monkeypatch)
    user_provider.set_user(member_user(ORG, "u-member", "member@example.test"))

    body = client.get(_url()).json()

    assert set(body) == {
        "evidence_line_item_id",
        "source_item_id",
        "materialisation_kind",
        "line",
        "location",
        "document",
        "document_available",
        "calculations",
        "access",
    }
    # CONTROLLED is the existing DM-6 allowlist: structural keys + amounts only,
    # with the withheld keys reported (never silently dropped).
    assert set(body["line"]) == {"id", "line_number", "raw_quantity", "raw_unit", "redacted_fields"}
    assert "source_page" in body["line"]["redacted_fields"]
    assert "payload_hash" in body["line"]["redacted_fields"]


def test_missing_line_is_404(client, world, user_provider):
    _install(world)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    assert client.get(_url("line-does-not-exist")).status_code == 404


def test_line_read_is_audited_without_recording_urls(
    client, world, user_provider, monkeypatch
):
    _install(world)
    _signed(monkeypatch)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    client.get(_url())

    entries = [e for e in world.audit._entries if e.action == "evidence.line_access"]
    assert len(entries) == 1
    assert entries[0].entity_id == LINE_ID
    assert entries[0].changed_fields["source_file_id"] == FILE_ID
    text = repr(entries[0].changed_fields).lower()
    assert "signed" not in text and "token" not in text


# ---------------------------------------------------------------------------
# Source-location semantics (authoritative only; never fabricated)
# ---------------------------------------------------------------------------


def test_pdf_line_location_is_the_verified_page(client, world, user_provider, monkeypatch):
    _install(world)
    _signed(monkeypatch)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    location = client.get(_url()).json()["location"]

    assert location["kind"] == "page"
    assert location["page"] == 2
    assert location["page_state"] == "verified"
    assert "page 2" in location["display"]


def test_csv_line_location_prefers_the_producer_row_over_the_ordinal(
    client, world, user_provider, monkeypatch
):
    line = {**PDF_LINE, "source_page": None, "line_number": 3, "materialisation_kind": "FORWARD"}
    extracted = {
        "source_headers": ["Description", "Qty", "Unit"],
        "line_items": [
            {"activity": "Gas usage", "quantity": 1, "unit": "kwh", "source_row": 2},
            {"activity": "Diesel", "quantity": 2, "unit": "l", "source_row": 3},
            {"activity": "Waste disposal", "quantity": 60, "unit": "t", "source_row": 5},
        ],
    }
    _install(world, line=line, extracted=extracted)
    _signed(monkeypatch)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    location = client.get(_url()).json()["location"]

    assert location["kind"] == "row"
    # The producer's own row is authoritative; the evidence ordinal is NOT it.
    assert location["row"] == 5
    assert location["line_number"] == 3
    assert location["row"] != location["line_number"]
    assert "not a physical" in (location["ordinal_note"] or "")


def test_xlsx_line_location_reports_sheet_and_row(client, world, user_provider, monkeypatch):
    line = {**PDF_LINE, "source_page": None, "line_number": 2}
    extracted = {
        "source_sheet": "Activity Data",
        "sheet_names": ["Cover", "Activity Data"],
        "source_headers": ["Description", "Qty", "Unit"],
        "line_items": [
            {"activity": "Gas usage", "quantity": 1, "unit": "kwh", "source_row": 4},
            {"activity": "Diesel", "quantity": 2, "unit": "l", "source_row": 7},
        ],
    }
    _install(world, line=line, extracted=extracted)
    _signed(monkeypatch)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    location = client.get(_url()).json()["location"]

    assert location["kind"] == "sheet_row"
    assert location["sheet"] == "Activity Data"
    assert location["row"] == 7


def test_location_is_unavailable_when_nothing_authoritative_exists(
    client, world, user_provider, monkeypatch
):
    line = {**PDF_LINE, "source_page": None, "line_number": 3}
    extracted = {"line_items": [{}, {}, {"activity": "Waste disposal", "quantity": 60}]}
    _install(world, line=line, extracted=extracted)
    _signed(monkeypatch)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    location = client.get(_url()).json()["location"]

    assert location["kind"] == "unavailable"
    assert location["page"] is None
    assert location["row"] is None
    assert "not available" in location["display"]


def test_ordinal_is_never_presented_as_a_physical_row(
    client, world, user_provider, monkeypatch
):
    """An evidence ordinal alone never becomes ``row`` or ``page``."""
    line = {**PDF_LINE, "source_page": None, "line_number": 4}
    _install(world, line=line, extracted={"line_items": [{}, {}, {}, {}]})
    _signed(monkeypatch)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    location = client.get(_url()).json()["location"]

    assert location["row"] is None and location["page"] is None
    assert location["line_number"] == 4
    assert "Line 4" in (location["ordinal_note"] or "")


# ---------------------------------------------------------------------------
# Historical source_page — a page COUNT is never an exact location
# ---------------------------------------------------------------------------


def _install_emission_chain(
    world, *, snapshot_page=8, with_line=False, line_page=None, org_id: str = ORG
) -> None:
    async def logs_get(log_id: str):
        return SimpleNamespace(
            id="log-a",
            organization_id=org_id,
            snapshot_id="snap-a",
            date="2026-05-08",
            quantity="60",
            unit="t",
            calculated_kg_co2e="150.40",
            scope="Scope 3",
            asset_id=None,
            created_at=None,
        )

    async def logs_get_snapshot(snapshot_id: str):
        return {
            "id": "snap-a",
            "organization_id": org_id,
            "activity": "Waste disposal",
            "activity_type": "Waste disposal",
            "quantity": "60",
            "quantity_unit": "t",
            "co2e_multiplier": "2.5067",
            "co2e_kg": "150.40",
            "scope": "Scope 3",
            "date": "2026-05-08",
            "reporting_year": 2026,
            "factor_source": "DEFRA-DESNZ",
            "factor_set": "2025",
            "methodology": "direct_multiply",
            "algorithm_version": "1.0",
            "content_hash": "hash-a",
            "calculated_at": "2026-05-08T10:00:00+00:00",
            "calculated_by": "u-owner",
            "request_id": "req-a",
            "factor_id": "f1",
            "customer_factor_id": None,
            "source_item_id": ITEM_ID,
            "source_file": "INV-10482.pdf",
            # Historical rows were written from the document page COUNT.
            "source_page": snapshot_page,
            "source_line_item_id": LINE_ID if with_line else None,
        }

    async def items_get(item_id: str):
        return SimpleNamespace(
            id=item_id,
            file_name="INV-10482.pdf",
            file_url="uploads/org-a/2026/05/inv-10482.pdf",
            file_id=FILE_ID,
            page_count=8,
            document_type="utility",
            status="approved",
            extracted_data=PDF_EXTRACTED,
            mapped_data={"activity_type": "Waste disposal"},
            mapped_facility_id=None,
            mapped_asset_id=None,
            mapped_supplier_id=None,
            extracted_by="u-a",
            extracted_at=None,
            calculated_emissions_kg_co2e=Decimal("150.40"),
        )

    async def files_get(file_id: str):
        return SimpleNamespace(
            id=file_id,
            organization_id=org_id,
            name="INV-10482.pdf",
            path="uploads/org-a/2026/05/inv-10482.pdf",
            file_type="PDF",
            size_bytes=2048,
            uploaded_by="u-a",
            uploaded_at=None,
            metadata={"data_type": "utility"},
        )

    async def factors_get(factor_id: str):
        return SimpleNamespace(
            id="f1",
            reporting_year=2026,
            activity_type="Waste disposal",
            co2e_multiplier="2.5067",
            unit="t",
            scope="Scope 3",
            factor_source="DEFRA-DESNZ",
            factor_set="DEFRA-2025",
            country="GB",
        )

    world.logs.get = logs_get
    world.logs.get_snapshot = logs_get_snapshot
    world.manual_extraction.get_item = items_get
    world.files.get = files_get
    world.files.get_by_path = files_get
    world.factors.get = factors_get

    if with_line:
        world.evidence_line_items.seed(
            {**PDF_LINE, "organization_id": org_id, "source_page": line_page}
        )


def _emission_url() -> str:
    return "/api/v3/emissions/log-a/evidence"


def test_historical_page_count_is_never_presented_as_a_verified_location(
    client, world, user_provider, monkeypatch
):
    _install_emission_chain(world, snapshot_page=8, with_line=False)
    _signed(monkeypatch)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    body = client.get(_emission_url()).json()

    assert body["evidence"]["source_page"] is None            # never the count
    assert body["evidence"]["source_page_state"] == "unverified"
    record = body["evidence_record"]
    assert record["technical_details"]["source_page"] is None
    assert record["technical_details"]["source_page_reported"] == 8  # kept, not shown
    assert record["source_location"]["page"] is None
    assert record["completeness"] == "PARTIAL"


def test_authoritative_line_page_is_used_and_verified(
    client, world, user_provider, monkeypatch
):
    _install_emission_chain(world, snapshot_page=8, with_line=True, line_page=2)
    _signed(monkeypatch)
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))

    body = client.get(_emission_url()).json()

    assert body["evidence"]["source_page"] == 2               # the line's own page
    assert body["evidence"]["source_page_state"] == "verified"
    assert body["evidence"]["source_line_item_id"] == LINE_ID  # the viewer handoff
    assert body["evidence_record"]["completeness"] == "COMPLETE"


def test_member_cannot_obtain_the_signed_document_url_from_the_evidence_route(
    client, world, user_provider, monkeypatch
):
    """The corrected D33 inconsistency: no storage pointer below FULL depth."""
    _install_emission_chain(world, snapshot_page=2, with_line=True, line_page=2)
    _signed(monkeypatch)

    user_provider.set_user(member_user(ORG, "u-member", "member@example.test"))
    member_body = client.get(_emission_url()).json()
    assert member_body["source_document"]["signed_url"] == ""
    assert member_body["evidence"]["signed_url"] == ""
    assert member_body["source_document"]["path"] is None
    assert member_body["evidence"]["drill_down_depth"] == "CONTROLLED"

    # A FULL caller (Owner) may still open the document.
    user_provider.set_user(org_owner_user(ORG, "u-owner", "owner@example.test"))
    owner_body = client.get(_emission_url()).json()
    assert owner_body["source_document"]["signed_url"] == "https://signed/x"
    assert owner_body["evidence"]["drill_down_depth"] == "FULL"
