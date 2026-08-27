---
Document Type: Implementation Report
Project: CarbonTally
Architecture: CarbonTally V3 backend consolidation
Version: 1.0
Status: IMPLEMENTED (code + wiring + tests); RUNTIME VERIFICATION PENDING (shell unavailable)
Created: 2026-08-15
Author: Cline
Aligned With: CARBONTALLY_V3_BACKEND_CONSOLIDATION_PLAN.md, CARBONTALLY_V3_LEGACY_CONFORMITY_PLAN.md
---

# CarbonTally V3 — New Capabilities Report

## 1. Executive Summary

Six new V3 capabilities were implemented on the existing V3 layered architecture:
**consultants, multi-client grants, processing companies, manual extraction, QC,
and suppliers**. The implementation reuses the established v2.1 conventions
(`AbstractRepository`, `RepositoryBundle`, thin routers, `auth.py` guards) and
targets the existing RC2 tables — **no database / schema / RLS / migration was
modified**. All surfaces are mounted on the single V3 router (served by both
`main.py` and `main_v2.py`).

## 2. Capability → implementation map

| Capability | Domain model | Repository | API router | Endpoints |
|---|---|---|---|---|
| consultants | `ConsultantProfile` | `ConsultantsRepository` | `api/v3_consultants.py` | `/api/v3/consultants/me`, `/me/team`, `/me/tasks`, `/tasks/{id}/status` |
| multi-client | `ConsultantClient`, `ConsultantFirmMember` | `ConsultantsRepository` | same | `/api/v3/consultants/me/clients` (list/add) |
| processing companies | `ProcessingEntity` (existing) | `ProcessingEntitiesRepository` (existing) | `api/v3_processing.py` | `/api/v3/processing-entities` (list/create/get/update) |
| manual extraction | `ManualExtractionBatch`, `ManualExtractionItem` | `ManualExtractionRepository` | `api/v3_manual_extraction.py` | `/api/v3/manual-extraction/batches`, `/items` |
| QC | `ManualExtractionItem` (qc fields) | `ManualExtractionRepository` | `api/v3_qc.py` | `/api/v3/qc/queue`, `/items/{id}/review`, `/stats` |
| suppliers | `Supplier` | `SuppliersRepository` | `api/v3_suppliers.py` | `/api/v3/suppliers` (CRUD) |

## 3. What was built

**Domain models** — `domain/partners.py` (immutable dataclasses):
`ConsultantProfile`, `ConsultantFirmMember`, `ConsultantClient`, `ConsultantTask`,
`ManualExtractionBatch`, `ManualExtractionItem`, `Supplier`. Processing companies
reuse the existing `domain/entity.py::ProcessingEntity`.

**Repositories** (`data/`, asyncpg over the service-role pool):
- `consultants.py` — profiles, firm members, client grants, tasks.
- `manual_extraction.py` — batches, items, item update, and the QC surface
  (list pending, QC review writes `qc_by/qc_at/qc_notes/quality_score/status`).
- `suppliers.py` — organisation-scoped supplier CRUD (soft delete).
- Processing entities reuse the existing `data/processing_entities.py`.

**API routers** (`api/`, thin, inline typed contracts):
- `v3_consultants.py` — `/api/v3/consultants/*` (`require_auth`).
- `v3_processing.py` — `/api/v3/processing-entities/*` (`require_admin`).
- `v3_manual_extraction.py` — `/api/v3/manual-extraction/*` (org-scoped).
- `v3_qc.py` — `/api/v3/qc/*` (`require_admin`).
- `v3_suppliers.py` — `/api/v3/suppliers/*` (org-scoped).

**Wiring**: `data/__init__.py` (3 new repo exports), `api/dependencies.py`
(`RepositoryBundle` += consultants, manual_extraction, suppliers), `api/router.py`
(5 new routers included). Processing entities were already wired (`entities`).

**Tests**: `tests/unit/api/test_v3_new_capabilities.py` asserts the new routes
are registered on the V3 router.

## 4. Files created / changed

Created: `domain/partners.py`, `data/consultants.py`, `data/manual_extraction.py`,
`data/suppliers.py`, `api/v3_consultants.py`, `api/v3_processing.py`,
`api/v3_manual_extraction.py`, `api/v3_qc.py`, `api/v3_suppliers.py`,
`tests/unit/api/test_v3_new_capabilities.py`, and this report.

Changed: `data/__init__.py`, `api/dependencies.py`, `api/router.py`.

## 5. Design decisions

1. No schema changes: consultant, manual-extraction and supplier tables already
   exist; `manual_extraction_items` already carries the QC columns, so the QC
   surface needed no new table.
2. Processing companies reuse the existing `ProcessingEntity` domain model and
   `ProcessingEntitiesRepository` (ADR-V3-001) with lifecycle validation against
   `ENTITY_STATUSES`.
3. Consultant auth currently uses `require_auth`; a dedicated consultant RBAC
   guard and RLS-enforced client-scoped data access are production-phase
   follow-ons (documented).
4. QC writes to `manual_extraction_items` (`qc_by/qc_at/qc_notes/quality_score`,
   status `qc_approved`/`qc_rejected`); a future dedicated `qc_reviews` table is
   optional and not required for this surface.
5. Suppliers are org-scoped and soft-deleted (`is_active = FALSE`).
6. All new surfaces are mounted on the single V3 router (one OpenAPI contract).

## 6. Verification status

**Executed (static):** every new/modified file was created and re-read for
syntax and internal consistency (domain models match the RC2 tables verified
from `CarbonTally_DB_Schema_V3M2.sql`; repositories implement
`AbstractRepository`; routers use `auth.py` guards; wiring in
`data/__init__.py`, `api/dependencies.py` and `api/router.py` is complete).

**Not executed (environmental):** `pytest` / `uvicorn` / live-DB checks could
not run in this session because the shell tool is wedged on a hung `docker exec`
from a previous session. This is an environment limitation, not a code defect.

## 7. Commands to run

```bash
cd backend
python -m pip install -r requirements.txt
python -m py_compile api/v3_consultants.py api/v3_processing.py \
    api/v3_manual_extraction.py api/v3_qc.py api/v3_suppliers.py \
    data/consultants.py data/manual_extraction.py data/suppliers.py domain/partners.py
python -m pytest tests/unit/api/test_v3_new_capabilities.py -q
python -m pytest tests/unit/api/test_v3_routes_exposed.py -q
python -m pytest tests/unit/api/test_composition_root.py -q
python -m pytest tests/unit -q
uvicorn main:app --host 0.0.0.0 --port 8000   # then curl /openapi.json
```

## 8. Limitations & next steps

- Runtime/DB verification pending (see §6); repositories assume the RC2 column
  shapes verified from the schema.
- Consultant multi-client data access is grant-management only at this stage:
  reading a client organisation's documents/emissions as a consultant requires
  either RLS enforcement (`is_org_consultant`) or explicit user-scoped
  authorization — a production-phase item.
- Consultant RBAC guard (`require_consultant`) and firm-invite/notification flow
  are follow-ons.
- Manual extraction is not yet wired into the upload→extraction→review pipeline
  or the processing-company assignment flow; QC is item-level.
- A dedicated `qc_reviews` table and extraction span/coordinate model (split-screen
  Phase 2) are future additive migrations.

## 9. Risks

1. Untested SQL against live tables — mitigated by integration tests before use.
2. Consultant endpoints authenticate any authenticated user with a consultant
   profile; org-level and consultant-level authorization hardening is required
   before production.
3. `consultant_tasks` metadata JSONB round-trip is best-effort.
4. QC status vocabulary (`qc_approved`/`qc_rejected`) is stored on
   `manual_extraction_items.status`; confirm downstream consumers accept it.

