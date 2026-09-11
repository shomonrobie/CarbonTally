# CarbonTally V3 — Investor Demo Data Report

LOCAL synthetic demonstration environment. No production data touched.

## 1. Dataset specification

A repeatable, deterministic synthetic ecosystem for the LOCAL CarbonTally V3
stack (`supabase=127.0.0.1:54425`, `api=127.0.0.1:8050`). All identities use the
`@demo.carbontally.local` development domain and a single shared local-only
password (stored in the existing gitignored `.local-demo-credentials.md` /
`DEMO_PASSWORD` env — never committed).

## 2. Generation parameters (this run)

```
python -m tools.seed_investor_demo --reset-demo
# default scale: --organisations 50 --consultants 50 --clients-min 5
#   --clients-max 30 --documents-per-org 4 --pipeline-docs 60 --pes 3 --seed 2026
```

The same command is fully idempotent (deterministic UUIDs + ignore-duplicates)
and can be scaled upward by changing the parameters.

## 3–4. Organisations and consultants created

- **Direct customer organisations: 50** (diverse sectors: manufacturing,
  offices, logistics, retail, hospitality, distribution, technology,
  professional services, construction, mixed operations; GB/IE addresses,
  registration numbers, metadata, reporting config).
- **Consultant firms: 50** (with `consultant_profiles`, firm members, partner
  status, industries served).
- **Client organisations: 916** across the consultant portfolios
  (`consultant_clients`), within the configured 5–30 range per consultant.

## 5. Users by role

- **Customer Owner/Admin/Member/Viewer: 200** (4 per direct org) +
  client owners (one per client org) → **users total: 1323**;
  **organization_members: 1125** (all roles valid — verification shows 0
  invalid role rows).
- **Consultant users: 50** (+ client-owner users).
- **Processing Entity users: PE Manager + PE Staff per entity** (entity-scoped
  `staff_profiles.entity_id`).

## 6–8. Processing entities, CarbonTally staff

- **Processing entities: 3** (Alpha/Beta/Gamma), each with a PE Manager
  (reviewer role) and PE Staff (operator role) — **10 entity-scoped staff
  profiles**.
- **CarbonTally internal staff: 12 profiles** — Operator, Reviewer, QC
  specialist, Staff Admin, System Admin (real `staff_roles` with
  `can_process`/`can_review`/`can_manage_staff`/`can_view_all` permissions).

## 9. Master data counts

| Master data | Count |
|---|---|
| Facilities | 156 |
| Assets | 310 |
| Suppliers | 156 |
| Customer factors | 245 (mix of `active` (approved), `draft` (pending), `inactive` (rejected)) |

Locations follow N2 (facilities-based representation; no duplicate table).
**Vehicles:** BLOCKED — the approved `v3m7_vehicles` migration is not applied
to the current local stack (table absent), reported as an implementation
dependency (deployment item, not a schema change).

## 10. Documents

- **219 organisation_files** — real PDFs uploaded to the private Supabase
  Storage `documents` bucket (viewable via signed URLs), linked to their
  organisations; each also enqueued as a `manual_extraction_items` row.
- Types: Electricity (kWh), Natural gas (kWh Net CV), Diesel (litres),
  Freight (tonne.km), Waste (tonnes), Purchased goods (spend).
- 55 extraction batches (incl. an "Uploads" batch per direct org).

## 11. Processing-state distribution

From `manual_extraction_items` (219):

| Status | Count |
|---|---|
| pending | 150 |
| extracted | 25 |
| mapped | 12 |
| validated | 6 |
| calculated | 14 |
| approved | 8 |
| rejected | 3 |
| qc_approved | 1 |

Includes correction/rework paths via the real rework loop (rejections route
back to mapping).


## 12. Calculations

- **26 `calculation_snapshots` + 26 `emissions_logs`** produced by the REAL
  engine (`quantity × co2e_multiplier` from the mapped emission factor; the
  client never supplies the result).
- Scope split: **Scope 1 ×15, Scope 2 ×9, Scope 3 ×2**.
- **Total: 82,560.8 kg CO₂e** across the processed portfolio (sum of the
  real snapshot values).

## 13. Evidence

Each calculated item carries the D33 chain: source file → extracted data →
mapped factor (`emission_factor_used`) → validation → calculation snapshot
(with `source_item_id` link) → `emissions_logs` row. No fabricated
certification/assurance status.

## 14. Reports

- **7 annual reports generated (HTTP 201) through the REAL report engine** for
  organisations with approved items; 10 `report_generation_queue` rows and 13
  `report_versions` snapshots persisted. Totals derive from actual calculated
  records.

## 15. Customer review / approval

Real `customer-review` calls (owner/admin gate) produced **8 approved** and
**3 rejected** items (with rejection reasons routed back to the rework loop).

## 16–17. Consultant and PE demo data

- Consultants: client portfolios (916 clients), consultant↔client messages,
  support conversations; active-client isolation follows the existing grants.
- PEs: assigned extraction work via the entity workspace surface.
  **PE-internal chat is NOT seeded** — the approved architecture denies
  entity-staff messaging (org-scoped conversations only); documented as an
  implementation dependency per N1.

## 18. CarbonTally staff

Operator/reviewer/QC queues are populated by the 150 pending + intermediate
items; staff-admin has issues (48), audit/messaging contexts; system-admin has
PE/commercial context rows.

## 19. Messaging (N1)

37 conversations / 54 messages / 60 participants:
customer-internal (Owner↔Admin), consultant↔client, CarbonTally support↔
customer and support↔consultant. **No Customer↔PE threads** (enforced).

## 20–21. Issues and commercial

- **48 issues** (open/in_progress/resolved/closed/escalated, all severities).
- Billing/commercial: orgs carry `subscription_status`/`tier`; no fake payment
  transactions; no real provider connected.

## 22. Search

219 documents, 219 processing items, 156 facilities, 310 assets, 156
suppliers, 10 reports and 48 issues across orgs give organisation-scoped search
real material; org isolation is enforced by the API/RLS.

## 23. Dashboard quality

Dashboards derive metrics from actual seeded records (document counts,
emissions totals above, pending queues, approved items, reports). No fabricated

## 25. Demo credentials handling

Passwords live in the gitignored `.local-demo-credentials.md` (or `DEMO_PASSWORD`
env); the generated `demo_manifest.json` (gitignored) lists personas, emails and
landing routes — **no secrets in committed files**.

## 26. Idempotency / reset

Deterministic UUIDs + `Prefer: resolution=ignore-duplicates` make re-runs
idempotent. `--reset-demo` deletes ONLY demo-namespaced rows (children first),
including matching `auth.users` via the GoTrue admin API.

## 27. Performance

Full run: reset ~81 s, seed ~3–4 min (auth-user creation is the bottleneck;
threaded + batched). Document uploads batched; PostgREST bulk inserts used.
Dashboard queries remain unchanged.

## 28–30. Validation / browser / safety

- Counts verified via PostgREST `count=exact` (table above); 0 invalid
  member roles; staff internal=12 / entity=10.
- **Browser verification (real login):** owner.demo0001 → `/home`,
  consultant.demo0001 → `/consultant`, operator.demo → `/ops`.
- RLS behavior suite: 27/27 PASS (pre-existing).
- Environment safety: seeder refuses non-local targets (local-only gate).

## 31. Remaining blockers / dependencies

- Vehicles master data requires applying `20260825000000_v3m7_vehicles.sql`
  to the local stack (deployment item).
- PE-internal chat is out of scope for the current architecture (N1).
- The DEMO manifest is gitignored; re-run the seeder after a local stack reset.

analytics values.

## 24. Tooling

Repeatable command: `python -m tools.seed_investor_demo` with
`--organisations/--consultants/--clients-min/--clients-max/--documents-per-org/
--pipeline-docs/--pes/--seed/--dry-run/--reset-demo/--only`. Modules under
`tools/seed_investor_demo/`.
