# CarbonTally v1.0 — Production Hardening Plan

*Implementation decision document — prepared 4 August 2026; UK & Ireland launch scope; ADRs treated as frozen; no SQL, no migrations, no schema redesign.*

## 1. Executive Summary

This document is CarbonTally's official Production Hardening Plan. It triages the junior audit team's Production Readiness Report into the four client categories — **A** (must implement before launch), **B** (strongly recommended for v1.0), **C** (defer to v1.1), **D** (reject) — and converts the result into an executable checklist, a phased migration order, a testing strategy and a go/no-go verdict, superseding the audit's severity ratings wherever the two disagree.

The headline triage result is a recalibration, not a rubber stamp. The audit declared 26 "v1.0 launch blockers", fourteen of them Critical. The architect's register confirms 23 launch-gated A items once verification gates and deduplication are accounted for (§3) — roughly eleven to thirteen true defect classes — while deferring 29 recommendations to v1.1 and beyond (§5) and rejecting 20 outright with reasoning (§6). Roughly half of what the audit asked for will not be built before launch, and the launched half surrenders no defect touching customer money, credentials, tenant isolation or a reported carbon number.

Five launch-gating themes are restated here as decisions. First, the **Irish facility write-path**: `facilities.eircode` is added, `facilities.postcode` relaxed, and a presence CHECK guarantees one or the other — without this, an Irish customer cannot register the site whose emissions the product measures. Second, **jurisdiction IN-lists**: `country` constrained to ('GB','IE') and the six `currency` columns plus `system_settings.default_currency` to ('GBP','EUR'), because every jurisdiction rule, aggregation and Stripe reconciliation keys off them. Third, **factor provenance plus the minimal SEAI/EPA core load**: provenance columns and a uniqueness rule on `defra_conversion_factors`, then the current-year Irish grid, gas and common-fuels set — a DEFRA-factored Dublin site reports silently wrong Scope 2, and wrong numbers are worse than a missing feature. Fourth, **security-of-secrets and tenancy verification**: hashing of `consultant_profiles.api_key`, `password_reset_tokens.token` and `user_invitations.token`, the reset-token UNIQUE correction, the `users.password_hash` ownership decision, and evidence — not assumption — that the RLS matrix and nullable-`organization_id` remediation hold. Fifth, **the erasure procedure before the first DSAR**: an anonymise-in-place runbook tested on staging, because hard delete is structurally impossible against ~40 foreign keys and the statutory clock starts on day one.

Equally deliberate is what this plan does **not** do. Country-conditional regex CHECKs are rejected: presentation formats belong at the API layer, and the Eircode routing-key allowlist is a living registry that must not be frozen into a constraint (§6, D1). Monthly RANGE partitioning is rejected: low-seven-figure row counts after year one are trivially served by B-trees plus retention deletes (§6, D4). The audit hash-chain is rejected as security theatre whose verifier is its own writer; privilege revocation and PITR tell the honest storey (§6, D5). And the blanket "index every FK" programme is rejected at roughly 3× over-scope in favour of 15–18 targeted indexes (§6, D2/D19).

The effort shape is favourable: most A items are Small, Low-risk, additive changes — nullable columns, IN-list CHECKs, a data load, one configuration check — batched into five migrations plus two verification gates (§8). The verdict is a **conditional GO**: launch proceeds once every row of the §7 checklist is evidenced, with no partial credit (full reasoning in §10).

## 7. Final Production Hardening Checklist

This is the single authoritative launch gate: every row is Category A, drawn from the §3 register and ordered for execution. The ✔ column is initialled only when the named evidence exists; "code merged" is not evidence.

| ✔ | # | Item | Verification evidence required |
|---|---|---|---|
| ☐ | 1 | Inspect the Supabase migration files (action zero): reconcile the dump — which showed no indexes, FKs, CHECKs or RLS policies — against reality | Signed note restating which findings are real and which collapse to verification |
| ☐ | 2 | Fix the facilities blocker: nullable `facilities.eircode`, relaxed `facilities.postcode`, presence CHECK (postcode OR eircode) | Staging insert of an IE facility with Eircode and NULL postcode succeeds; insert with both NULL is rejected |
| ☐ | 3 | Constrain `organizations.country`, `facilities.country`, `suppliers.country`, `consultant_profiles.country` to IN ('GB','IE') | Constraint definitions present; out-of-list write rejected on staging |
| ☐ | 4 | Constrain the six `currency` columns and `system_settings.default_currency` to IN ('GBP','EUR') | As above; existing values audited to the list first |
| ☐ | 5 | Verify the full RLS policy matrix; enforce service-role discipline (no service key client-side; workers filter `organization_id` in code) | Executed penetration matrix (§9): zero cross-tenant rows for customer, consultant, staff and service roles; sign-off on service-key handling |
| ☐ | 6 | Backfill then NOT NULL `organization_id` on `conversations`, `messages`, `upload_batches`, `manual_review_queue`, `file_attachments`, `customer_verifications` | Zero-NULL counts; constraints present; pre-backfill snapshot retained |
| ☐ | 7 | Hash `consultant_profiles.api_key`, `password_reset_tokens.token`, `user_invitations.token` (SHA-256 + lookup prefix; rotation columns on the API key) | No plaintext credential recoverable from a staging dump; auth-flow regression passes |
| ☐ | 8 | Drop UNIQUE on `password_reset_tokens.user_id`; keep UNIQUE on `password_reset_tokens.token`; latest-valid-wins in app | Repeated resets for one user no longer error; only the latest token validates |
| ☐ | 9 | Decide `users.password_hash` ownership; if Supabase Auth is IdP, dead-column it and never write | Recorded decision; column confirmed unwritten by code inspection |
| ☐ | 10 | Verify every FK and ON DELETE action; RESTRICT on financial/audit tables where dangerous CASCADEs are found | FK/ON DELETE inventory; staging destructive-delete rehearsal matches it |
| ☐ | 11 | Seed cleanup: remove `.de`/`.fr`/`.fi`/`.ai` users; add IE org + IE facility fixtures (Eircode, EUR, IE factor) | Staging seed holds only GB/IE rows; the Irish end-to-end fixture passes |
| ☐ | 12 | Add `organizations.is_active` and `organizations.archived_at` | Suspend demonstrated on staging without deleting child rows |
| ☐ | 13 | Relax NOT NULL on `customer_documents.asset_id` | Supplier-invoice upload with no asset completes on staging |
| ☐ | 14 | Add `consultant_billing.currency` with default and backfill | All billing tables denominated; reconciliation report clean |
| ☐ | 15 | Add provenance columns to `defra_conversion_factors` (`unit`, `scope`, `factor_source`/`factor_set`, `country`); backfill 'DEFRA-DESNZ'; UNIQUE `(reporting_year, activity_type)` | Duplicate-insert rejected; every factor row states unit, scope, source |
| ☐ | 16 | Load the minimal current-year SEAI/EPA core set (grid electricity, gas, common fuels) | Dublin fixture's Scope 2 resolves to the Irish factor, not DEFRA |
| ☐ | 17 | Add `emissions_logs.unit` (FK to `units.code`) and `emissions_logs.scope` | kWh totals computable without the factor join; SECR fixture totals audit-clean |
| ☐ | 18 | Range CHECKs ≥ 0 on `emissions_logs.raw_quantity`, `.calculated_kg_co2e`, `defra_conversion_factors.co2e_multiplier`, `suppliers.annual_emissions_*` | Negative write rejected on each column |
| ☐ | 19 | Widen `file_attachments.file_size` (and peers) to int8 with size CHECKs | >2 GB synthetic upload path handled; constraints present |
| ☐ | 20 | Add `customer_documents.file_checksum` (SHA-256) for duplicate-upload detection | Identical re-upload detected deterministically |
| ☐ | 21 | Add the uniqueness set: `organization_members(organization_id, user_id)`, `consultant_clients(consultant_id, organization_id)`, `usage_tracking(organization_id, usage_month)`, `report_versions(report_id, version_number)`, `suppliers(organization_id, vat_number)`/`(organization_id, company_number)` partial WHERE NOT NULL | Dedupe sweep clean; each constraint rejects a scripted duplicate |
| ☐ | 22 | Block writes to `pending_invites`; `user_invitations` is canonical | Write to `pending_invites` fails; invite regression passes |
| ☐ | 23 | Anonymise-in-place erasure procedure (hash `users.email`, "Deleted User", keep UUID), tested on staging | Timed staging rehearsal against a production-like FK graph; residual-PII scan clean |
| ☐ | 24 | Residency verification: Supabase region UK-London or eu-west-1; `system_settings.backup_storage_location` matches | Configuration evidence archived in the compliance pack |

**B items scheduled for the v1.0.x hardening window** (recommended, none launch-gating):

| Item | Target release |
|---|---|
| Retention schedule + first pg_cron jobs (`processing_logs` 90d; login/email 12m; activity logs 12–24m; audit 24m); `retention_until` on the document class | v1.0.1 — first weeks post-launch |
| `customer_documents` soft-delete (`deleted_at` + RLS/query filters) | v1.0.1 |
| `pg_trgm` on `suppliers.name`/`.vat_number` and `organizations.name` + "did you mean?" UX | v1.0.1–v1.0.2 |
| App-layer validation pack (VAT + MOD97, CH/CRO numbers, GIR postcode, Eircode shape, libphonenumber/E.164) + EUR default when `country='IE'` | v1.0.1 |
| Audit privilege hardening (revoke UPDATE/DELETE on audit tables; drop `updated_at` from append-only logs) | v1.0.1 |
| `suppliers.sort_code` + last-4 bank masking in API responses | v1.0.2 |
| Labelled `organization_metadata.total_floor_area_sqm`/`.occupied_floor_area_sqm`; `facilities.meter_mpan_mprn`; `emissions_logs.facility_id` dual-write | v1.0.2 |
| Remaining B-class CHECKs (timezone IN-list, date pairs, percentage 0–100 after scale convention, counts ≥ 0) | v1.0.2 |
| PII inventory, DSAR export expiry, waitlist/beta purge at GA, support-log indexes | v1.0.1–v1.0.2 |

The checklist is the gate. There is no partial credit: twenty-three of twenty-four rows evidenced is a NO-GO, and the twenty-fourth row is precisely the one that fails publicly in the first month. The "verify" rows (1, 5, 10, 24) gate on evidence because a multi-tenant financial product cannot go live on unverified isolation, whatever the migration files turn out to contain.

## 8. Recommended Migration Order

Five phases, as the client framed them. Most A-class change is additive and Small; the phasing sequences verification before constraint, and constraint before data load — it is not managing heavy migration risk on a live-but-pre-revenue database.

### P1 — Critical production fixes

| Attribute | Detail |
|---|---|
| Objectives | Close the launch-blocking security, tenancy and Irish write-path defects (checklist rows 2–13): credential/token hashing, reset-token UNIQUE correction, `users.password_hash` decision, RLS verification, nullable-`organization_id` backfill + NOT NULL, tenant lifecycle columns, `asset_id` nullability, facilities Eircode fix, country/currency IN-lists, seed cleanup |
| Database impact | Medium (tenancy backfill + constraints); otherwise Small/additive |
| Application impact | Small: key/token issuance flows; insert paths must always set `organization_id`; suspend UI hook; upload paths |
| Migration risk | Low (security batch); Medium (tenancy batch — policy changes can lock out users if untested with non-privileged roles) |
| Estimated effort | Two migrations plus verification: (1) **P1 security migration** — hashing columns, reset-token UNIQUE drop, `suppliers.sort_code`, one deploy; (2) **P1 tenancy migration** — lifecycle columns, nullability, org backfill staged backfill → verify → constrain, one deploy |
| Testing requirements | RLS penetration matrix; auth-flow regression (reset, invite, API key); Irish fixture end-to-end; lockout test under non-privileged roles |
| Rollback strategy | Security migration rolls forward — hashing is one-way; re-issue keys/tokens rather than reverse. Tenancy migration: snapshot before backfill; dropping a NOT NULL is easy, un-backfilling is not |

### P2 — Data integrity improvements

| Attribute | Detail |
|---|---|
| Objectives | Land the integrity register (checklist rows 14–22): uniqueness set, targeted NOT NULL DEFAULTs, status CHECKs on queue/billing/role columns, money and emission range CHECKs, `file_size` int8 widening, `file_checksum`, soft-delete, factor provenance + UNIQUE, `pending_invites` write-block, audit privilege hardening; FK/ON DELETE remediation where P1 inspection proved danger |
| Database impact | Medium (constraints across many tables, one type widening) |
| Application impact | Small: invalid-state errors, duplicate 409s, ingest sets new columns; Medium for soft-delete (every document read path filters) |
| Migration risk | Low–Medium pre-revenue: dedupe before UNIQUEs, backfill before NOT NULLs, value-mapping before status CHECKs |
| Estimated effort | One **P2 integrity migration** after a staging data audit; CHECKs added NOT VALID-style then validated to avoid table locks; SEAI/EPA data load rides this phase as a data deploy |
| Testing requirements | Staging data audit (§9 gate 2) signed off first; constraint-rejection script per rule; soft-delete regression across every document read path |
| Rollback strategy | Easy — drop constraint / re-grant privilege; the soft-delete column drops safely only before the app depends on it |

### P3 — Performance improvements

| Attribute | Detail |
|---|---|
| Objectives | Build the targeted index baseline (~11 A-set plus ~7 B-set): tenant composites on `customer_documents(organization_id, created_at DESC)` and `emissions_logs(organization_id, start_date)`, `suppliers`/`facilities(organization_id)`, the `document_processing_queue(status, created_at)` queue-claim partial, `messages(conversation_id, created_at)`, the unread-notifications partial, support-log indexes, the `consultant_firm_members.client_access` GIN; plus `pg_trgm` indexes and interim presence-table UNIQUEs |
| Database impact | Medium (build I/O only; no schema shape change) |
| Application impact | None |
| Migration risk | Low — every index built CONCURRENTLY, each in its own transaction |
| Estimated effort | One **P3 index migration**: the full A+B set built CONCURRENTLY, one release; may land at any point in the programme |
| Testing requirements | Load smoke (§9 gate 7); before/after query plans on the document list, emissions aggregation and worker claim path |
| Rollback strategy | Trivial — drop each index CONCURRENTLY |

### P4 — Validation improvements

| Attribute | Detail |
|---|---|
| Objectives | Land the application-layer validation pack replacing the rejected regex CHECKs: VAT + MOD97, CH/CRO company-number rules, GIR-valid postcode, Eircode shape + routing-key allowlist, libphonenumber/E.164; normalisation at write; EUR default when `country='IE'`; write-path conventions (structured address columns canonical, blobs as display caches; API rule against nullable `asset_id`); trigram "did you mean?" UX |
| Database impact | None — this is the phase that keeps formats out of the database per the layering rule |
| Application impact | Medium: validator library integration on all write surfaces, onboarding defaults, supplier/org creation UX |
| Migration risk | Low; the principal risk is over-rejecting legitimate edge cases, mitigated by shadow-mode logging before enforcement |
| Estimated effort | One application sprint parallel to P2–P3; the trigram UX depends on the P3 indexes |
| Testing requirements | Validator unit suites per jurisdiction (GB/IE positive and negative cases); shadow-mode review; normalisation idempotence |
| Rollback strategy | Feature-flag enforcement per validator; revert to shadow mode without a database change |

### P5 — Compliance improvements

| Attribute | Detail |
|---|---|
| Objectives | Ship the compliance pack (checklist rows 23–24 plus B items): anonymise-in-place erasure procedure (launch-gated), residency verification, retention schedule + first pg_cron jobs, `retention_until` on the document class, PII inventory, DSAR export expiry, waitlist/beta purge at GA |
| Database impact | Small: one `retention_until` column, job schedule; the erasure artefact is a procedure, not schema |
| Application impact | Small: ingest sets `retention_until`; erasure is a manual runbook in v1.0 |
| Migration risk | Low for jobs (small batches, dry-run counts first); Medium for the erasure procedure — a destructive script rehearsed on staging against a production-like FK graph |
| Estimated effort | Documentation-led **P5 compliance pack**: two small migrations plus the runbook; design begins in P1 |
| Testing requirements | Erasure rehearsal with residual-PII scan (§9 gate 5); retention dry-runs; residency evidence archived |
| Rollback strategy | Jobs: drop the job. Erasure: not reversible by design — the staging rehearsal evidence *is* the mitigation |

**Sequencing rationale.** P1→P5 is not strictly linear. The P3 index batch is independent and can land whenever a release window allows — it blocks nothing and nothing blocks it. P5 design work (the retention schedule and the erasure runbook's FK-graph mapping) starts in P1 so documentation matures alongside the schema it describes. And although the erasure procedure lives administratively in P5, it is launch-gated with the P1 items: a DSAR can arrive on day one, and the one artefact this plan refuses to schedule after launch is the tested answer to that request.

## 9. Testing Strategy

The testing philosophy follows the triage: launch-gating defects are the ones that fail silently, so the programme exists to make silent failures loud before customers do. Seven pre-launch gates apply.

**Gate 1 — migration-file inspection (action zero).** Before any remediation is scored, reconcile the schema dump against the actual Supabase migration files: the dump showed no indexes, FKs, CHECKs or RLS policies, so if migrations contain them, several findings collapse to verification and the plan re-points at evidence.

**Gate 2 — staging data audit before constraints.** The P2 migration runs only after a staging audit: NULL backfills counted before NOT NULLs, duplicate sweeps clean before UNIQUEs, existing values mapped before status CHECKs. On a pre-revenue database the sweeps should be near-empty; the audit proves that rather than assumes it.

**Gate 3 — Irish end-to-end regression fixtures.** An IE organisation with an IE facility carrying an Eircode, EUR currency and an IE emission factor, exercised through onboarding, upload, mapping and reporting — the guard whose absence let the facilities blocker survive to audit, now running in every release candidate permanently.

**Gate 4 — RLS penetration matrix.** Scripted cross-tenant access attempts per role — customer, consultant, staff, service — against every tenant table class. One cross-tenant row from any role is a launch-stopping failure, not a bug ticket.

**Gate 5 — erasure runbook rehearsal.** The anonymise-in-place procedure executed on staging against a production-like FK graph, timed, with a residual-PII scan. The one-month statutory clock means the rehearsal, not the first live DSAR, is where the procedure earns trust.

**Gate 6 — rollback rehearsal for the two non-trivial rollbacks.** The nullable-org backfill (snapshot restore — un-backfilling is impossible) and the token-hashing roll-forward (re-issuance — hashing is one-way), each rehearsed once on staging before P1 ships.

**Gate 7 — load smoke on the indexed query paths.** Document list, emissions aggregation, worker claim path and notification badge at projected year-one volumes, with query-plan evidence the P3 indexes are used.

| Test | Phase | Pass criterion |
|---|---|---|
| Migration-file reconciliation | Pre-P1 | Signed note; findings re-scored against reality |
| Staging data audit | Pre-P2 | Zero unhandled NULLs/duplicates/unmapped values |
| Irish end-to-end fixture | P1, then every release | IE org/facility registers, uploads, reports with IE factor |
| RLS penetration matrix | P1 | Zero cross-tenant rows across all four roles |
| Erasure rehearsal | P5 (launch-gated) | Completes in time; residual-PII scan clean |
| Rollback rehearsals | Pre-P1 deploy | Snapshot restore and re-issuance demonstrated |
| Load smoke | P3 | New indexes used; p95 within target at year-one volume |

## 10. Go/No-Go Assessment

**Verdict: Conditional GO.** CarbonTally launches in the UK and Ireland once — and only once — every row of the §7 checklist carries its named evidence. The triage shrunk the audit's 26-item programme into five migrations and two verification gates; what remains is small, additive and mostly low-risk, and nothing in the B, C or D registers stands between the product and revenue. But the A register is not negotiable, and the reasoning is concrete rather than doctrinal.

Launch without the **write-path and jurisdiction class** (rows 2–4) and Irish customers cannot register the sites whose emissions the product measures — the loudest possible failure in a launch market, discovered in the first onboarding call. Launch without the **numbers class** (rows 14–18, 20) and the product ships silently wrong Scope 2 to Irish customers and unit-less quantities to everyone: nothing errors, the join succeeds, the arithmetic succeeds, and the filed report is wrong. Launch without the **tenancy and secrets class** (rows 5–9) and tenant isolation is unprovable — one forgotten `organization_id` or one escaped backup converts a marketing promise into a reportable ICO/DPC incident. Launch without the **compliance class** (rows 23–24) and the first DSAR triggers an untested destructive script against a live tenant under a one-month statutory clock. Every class fails invisibly at demo scale and publicly in production; that asymmetry is the entire case for the gate.

| Gate | Status today | Evidence required to clear |
|---|---|---|
| Irish write-path + jurisdiction IN-lists | Defects confirmed; fixes specified | Rows 2–4 evidenced on staging |
| Factor provenance + SEAI/EPA core load | Provenance columns and Irish data absent | Rows 15–16 evidenced; Dublin fixture resolves to IE factor |
| Tenancy isolation + secrets | Unverifiable from the dump; plaintext credentials present | Rows 1, 5–9 evidenced; penetration matrix clean |
| Uniqueness/integrity set | Unconstrained duplicates possible | Rows 13, 17–22 evidenced post data audit |
| Erasure + residency | Procedure unwritten; region unchecked | Rows 23–24 evidenced; rehearsal timed, scan clean |

One descope is acceptable. If the SEAI/EPA load slips beyond the launch window, the fallback is a **UK-only launch with IE signups gated at onboarding** — a product decision, executed at the registration flow, not in the schema. What is never acceptable is the third option: shipping Irish customers DEFRA factors and calling it Scope 2; a wrong answer is not a placeholder. The schema work is required under either outcome, so the fallback costs the programme nothing but honesty.

**The verdict: GO — conditional on every row of §7 being evidenced; the checklist is the launch.**
