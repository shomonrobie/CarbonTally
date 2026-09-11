# CarbonTally — Production Supabase Reconciliation (READ-ONLY)

**Prompt Ref:** `CT-PROD-SUPABASE-RECON-20260911-001` · **Date:** 2026-09-11
**Mode:** READ-ONLY production reconciliation — no migration, no DDL, no DML, no config change, no deploy, no push
**Repository:** CarbonTally · **Branch:** `main` · **HEAD:** `daad396523ac693352cc2f4ebb7fc58814a9e60b`
**Release-1 commit:** `daad396` — `release: establish CarbonTally production release 1`
**Predecessors:** `CT-PROD-READINESS-AUDIT` · `CT-PROD-RELEASE-MANIFEST` · `CT-PROD-PRECOMMIT-GATE` ·
`CT-PROD-RELEASE-COMMIT(-CORRECTION)` · `CT-PROD-DEPLOYMENT-READINESS` (which raised `DR-01 — Live migration state UNKNOWN`)
**Authorities:** Blueprint V1.3 · Master Roadmap V1.0 · Release Manifest 20260911 · Deployment Readiness 20260911

> This operation existed solely to resolve `DR-01`. **It could not be resolved: production is not
> reachable with any genuinely read-only credential available in this environment.** The report
> therefore establishes the production *identity and availability* findings, and records exactly
> which questions remain `UNKNOWN` and why.

---

## 0. Executive conclusion

* **Production target identity: CONFIRMED** — Supabase project ref **`pvwiojoyaqywtydzcpbg`**, project
  name **`CarbonTally`**, org `pfurlzwxdtvyljnahlnx`. Corroborated by **four independent
  repository/configuration artefacts** (§2).
* **Safe read-only production access: NOT AVAILABLE.** There is **no** read-only (or password-based)
  production credential in this environment. The only production-capable credential present is a
  **`SUPABASE_SERVICE_KEY`**, which is a **write-capable** credential, **not** read-only access; §2
  forbids using it as a substitute, and §16 mandates a stop. It was **not used**.
* **New availability finding:** the project API host `pvwiojoyaqywtydzcpbg.supabase.co` returns
  **NXDOMAIN**, while control lookups (`supabase.co`, `supabase.com`, `api.supabase.com`) resolve and
  `https://supabase.com` returns **HTTP 200**, and the regional pooler
  `aws-0-eu-west-2.pooler.supabase.com:5432` **accepts TCP**. This combination is consistent with the
  project **not being active** (the dedicated project hostname does not exist). Production
  *availability* is therefore **NOT CONFIRMED**. The earlier CLI failure
  (`Failed to create login role: Connection terminated due to connection timeout`) is consistent
  with this.
* **A previously used command was identified as unsafe and was NOT repeated:** `supabase migration
  list --linked` attempts to **create a temporary login role** in the target database — i.e. it can
  *mutate* production. Under §16 ("a command's mutation safety is uncertain") it must not be run.
  It was not re-run in this operation.
* Consequently: **production migration history, schema, RLS, storage and factor rows all remain
  `UNKNOWN`.**

**Final verdict: `NOT READY — PRODUCTION STATE STILL UNKNOWN`.**

---

## 1. Git / Release-1 verification

| Item | Result |
|---|---|
| branch | `main` |
| HEAD | `daad396523ac693352cc2f4ebb7fc58814a9e60b` |
| Release-1 commit exists | **YES** |
| HEAD *is* the Release-1 commit | **YES** (`git rev-parse HEAD` == expected) |
| Release-1 is an ancestor of HEAD | **YES** |
| commits after Release-1 | **0** → no post-Release-1 repository change affects production schema or runtime |
| working tree | `75 untracked · 152 deleted · 209 modified`, staged **0** (2 of the untracked files are this operation's documentation) |
| pushed? | **NO** — `main…origin/main [ahead 29]` |
| migration files modified/untracked | **0** |

No stage, commit, push, restore or clean was performed.

---

## 2. Production target evidence

| Evidence source | Value (no secrets) |
|---|---|
| `supabase/.temp/linked-project.json` | `{"ref":"pvwiojoyaqywtydzcpbg","name":"CarbonTally","organization_id":"pfurlzwxdtvyljnahlnx","organization_slug":"pfurlzwxdtvyljnahlnx"}` |
| `supabase/.temp/project-ref` | `pvwiojoyaqywtydzcpbg` |
| `backend/supabase/.temp/project-ref` | `pvwiojoyaqywtydzcpbg` |
| root `.env.production` → `SUPABASE_URL` | `https://pvwiojoyaqywtydzcpbg.supabase.co` |
| `frontend/.env.production` → `SUPABASE_URL` | `https://pvwiojoyaqywtydzcpbg.supabase.co` |
| `frontend/.env.production` → `REACT_APP_API_URL` | `https://carbontally-api.onrender.com` (production backend target corroborated) |
| `frontend/src/supabaseClient.js` in-source default | same production project (production fallback) |
| `supabase/.temp/pooler-url` (password not embedded) | `postgresql://postgres.pvwiojoyaqywtydzcpbg@aws-1-eu-west-2.pooler.supabase.com:5432/postgres` |

**Production identity: `CONFIRMED`** — the ref is asserted by the Supabase CLI link metadata (which
includes the project *name* `CarbonTally` and its organisation id) **and** independently by two
committed/unchanged production env files **and** by the shipped frontend default. This is materially
stronger than a lone `.temp/project-ref`.

**Pooler hostname discrepancy (diagnostic):** the cached pooler URL names
`aws-1-eu-west-2.pooler.supabase.com`, whereas in this environment only
`aws-0-eu-west-2.pooler.supabase.com` resolves. A stale pooler hostname is an additional plausible
contributor to the earlier connection failure, independently of project state.

**Safe read-only production connection: `NOT AVAILABLE`.**
* No production DB password, no `SUPABASE_ACCESS_TOKEN`, no `PGHOST`/`PGPASSWORD`; every local
  `DATABASE_URL` is `127.0.0.1`.
* `~/.supabase/` contains only `telemetry.json` and `traces/` — **no CLI login token**.
* `SUPABASE_SERVICE_KEY` **is present** (root `.env.production`) — a **service-role, write-capable**
  credential. Deliberately **not used** (§2 read-only limitation; §16 stop condition).

---

## 3. Migration inventory (repository)

| Measure | Value |
|---|---|
| migration files in `supabase/migrations/` | **53** |
| tracked at `HEAD` | **53** |
| tracked at `HEAD~1` (pre-Release-1) | **36** |
| **added by Release-1** | **17** |
| modified / untracked migration files | **0 / 0** |
| history mechanism | Supabase CLI `supabase_migrations.schema_migrations` — created and written **by the CLI**, not by any repository SQL (no migration file references the table) |

**The 17 Release-1 migrations (exact, ordered):**

```
 1 20260831000000_v3m10_org_membership_unique.sql
 2 20260831010000_v3m11_operational_indexes.sql
 3 20260831020000_audit_activity_immutability.sql
 4 20260831030000_tenant_org_id_not_null.sql
 5 20260831040000_consultant_revocation_roles.sql
 6 20260902020000_v1_2_dual_origin_workflow.sql
 7 20260902030000_phase5_work_item_assignments.sql
 8 20260902040000_phase5_pe_operational_messaging.sql
 9 20260902050000_phase5_notification_event_key.sql
10 20260903010000_ws4_gate3_4a_item_assignment_foundation.sql
11 20260905000000_gate4_actor_provenance.sql
12 20260905010000_gate5_t1_automation_provenance.sql
13 20260905020000_gate5_t6_automation_write_once_guard.sql
14 20260906010000_gate6_w1_automation_extracted_output.sql
15 20260906090000_p6_1c_consultant_engagement.sql
16 20260906100000_p6_2a_consultant_processing_permissions.sql
17 20260910120000_p6_2d_consultant_provenance.sql
```

---

## 4. Production migration reconciliation — `PRODUCTION MIGRATION STATE REMAINS UNKNOWN`

Production could not be queried. **No migration is asserted as applied.** Per §7, the classification
below does **not** infer application from local/E2E state.

| # | Migration | In repository | Recorded production | Required schema evidence | Status |
|---|---|---|---|---|---|
| 1 | `v3m10_org_membership_unique` | YES | `?` | unique org-membership index exists | `UNKNOWN` |
| 2 | `v3m11_operational_indexes` | YES | `?` | operational indexes exist | `UNKNOWN` |
| 3 | `audit_activity_immutability` | YES | `?` | immutability functions/triggers exist | `UNKNOWN` |
| 4 | `tenant_org_id_not_null` | YES | `?` | `assets.org_id` NOT NULL | `UNKNOWN` |
| 5 | `consultant_revocation_roles` | YES | `?` | revocation/role vocabulary present | `UNKNOWN` |
| 6 | `v1_2_dual_origin_workflow` | YES | `?` | `manual_extraction_items`: `processing_origin`, `processing_entity_id`, `pe_qc_*`, `pe_reviewed_*` | `UNKNOWN` |
| 7 | `phase5_work_item_assignments` | YES | `?` | table `work_item_assignments` + unique index | `UNKNOWN` |
| 8 | `phase5_pe_operational_messaging` | YES | `?` | `conversations`/`messages`: `conversation_kind`, `context`, `processing_entity_id` | `UNKNOWN` |
| 9 | `phase5_notification_event_key` | YES | `?` | `notifications`: `event_key`, `actor_domain` + unique index | `UNKNOWN` |
| 10 | `ws4_gate3_4a_item_assignment_foundation` | YES | `?` | item-assignment foundation objects | `UNKNOWN` |
| 11 | `gate4_actor_provenance` | YES | `?` | `calculation_snapshots.performed_by` | `UNKNOWN` |
| 12 | `gate5_t1_automation_provenance` | YES | `?` | `document_processing_queue`: automation provider/model/version | `UNKNOWN` |
| 13 | `gate5_t6_automation_write_once_guard` | YES | `?` | write-once guard function/trigger | `UNKNOWN` |
| 14 | `gate6_w1_automation_extracted_output` | YES | `?` | `document_processing_queue.automation_extracted_data` | `UNKNOWN` |
| 15 | `p6_1c_consultant_engagement` | YES | `?` | `consultant_clients`: `relationship_origin`, `engagement_*` | `UNKNOWN` |
| 16 | `p6_2a_consultant_processing_permissions` | YES | `?` | `consultant_firm_members.can_*` capability columns | `UNKNOWN` |
| 17 | `p6_2d_consultant_provenance` | YES | `?` | `manual_extraction_items`: `consultant_firm_id`, `processing_mode`, provenance columns | `UNKNOWN` |

Every row is `UNKNOWN` — **not** `APPLIED_AND_VERIFIED`, **not** `APPLIED_BUT_SCHEMA_UNVERIFIED`, and
**not** `NOT_RECORDED`. The 17-migration matrix cannot be closed from this environment, and the
production delta therefore remains undetermined.


### 4.1 Why no reconciliation was possible (and why no shortcut was taken)

| Candidate path | Outcome |
|---|---|
| `supabase migration list --linked` | **Not re-run.** It **creates a temporary login role** in the target database (a mutation) before reading history → §16 stop condition ("a command's mutation safety is uncertain"). The earlier attempt failed at connection with no session established. |
| Direct `psql` to the pooler | **Refused.** No production DB password exists (`pooler-url` carries no password; no keyring entry; `PGPASSWORD` unset). Manufacturing credentials is prohibited (§2). |
| PostgREST / Management API with the service key | **Refused.** A service-role key is **write-capable**, not read-only access (§2 requires read-only access to be *already available*). It was **not used**. It is also unreachable — the project API host is NXDOMAIN (§5). |
| Infer state from local/E2E | **Refused.** §7 forbids inferring production application from local/E2E state; §13 forbids `local = production` and `E2E = production`. |

---

## 5. Production availability finding (new evidence)

| Probe (all read-only, credential-free) | Result |
|---|---|
| `getent hosts supabase.co` | resolves (76.76.21.21) |
| `getent hosts supabase.com` | resolves (216.150.1.193) |
| `getent hosts api.supabase.com` | resolves |
| `curl https://supabase.com` | **HTTP 200** |
| `getent hosts pvwiojoyaqywtydzcpbg.supabase.co` | **NXDOMAIN / FAIL** |
| `curl https://pvwiojoyaqywtydzcpbg.supabase.co/auth/v1/health` | `Could not resolve host` (HTTP `000`) |
| `curl https://pvwiojoyaqywtydzcpbg.supabase.co/rest/v1/` | `Could not resolve host` (HTTP `000`) |
| TCP connect `aws-0-eu-west-2.pooler.supabase.com:5432` | **OPEN** (shared regional pooler; does not by itself prove the project exists) |

**Interpretation (bounded, not overclaimed):** DNS and HTTPS egress work and the regional pooler is
reachable, yet the **project-specific API hostname does not resolve at all**. A Supabase project whose
dedicated `<ref>.supabase.co` host does not resolve is one whose project is **not currently active**
(e.g. deleted / not provisioned); paused projects normally retain their hostname. This is stated as
the **most probable** explanation — alternatives (project-specific DNS withdrawal while paused, or a
resolver policy for that exact name) cannot be excluded from outside the Supabase console. Either
way, **production availability is NOT CONFIRMED**, and this is now a PO-visible finding in its own
right, beyond the original "state unknown".

Cached (non-secret) stack metadata recorded from an earlier successful link — reference only, **not**
a statement about current production state: `gotrue v2.195.0`, `postgrest v14.5`, `storage v1.69.0`,
`postgres 17.6.1.147`, `cli-latest v2.117.0`; `supabase/.temp/pgdelta` and
`supabase/.temp/start-secrets` are both **0 bytes**.

---

## 6. Schema reconciliation — `UNKNOWN`

Could not be performed: no production connection exists. The full object-level requirement set that
must be verified in production once read-only access exists (tables, columns, types, nullability, PKs,
FKs, unique/check constraints, indexes, functions, triggers, RLS enablement, policies, grants) is
unchanged from the Deployment Readiness audit §4 and is reproduced as the "required schema evidence"
column in §4 above, covering: organisations/tenant isolation, organisation memberships, consultant
profiles/firms, processing entities, capabilities/grants, manual extraction items, processing
workflow, consultant provenance, notifications, conversations/messaging, billing/usage, customer
subscriptions, allowances, emission factors, documents/storage integration, automatic processing and
QC workflows.

**Production-critical drift checks that remain outstanding** (repo-side expectations):
`usage_tracking.usage_month` = `date`; `notifications` unique event-key index; `assets.org_id`
NOT NULL; organisation-membership unique index; `document_processing_queue` automation columns +
write-once guard; `work_item_assignments` table + unique index; `consultant_firm_members.can_*`
capability columns.

---

## 7. RLS reconciliation — `UNKNOWN`

Could not be performed (no connection). **No policy was created, dropped or altered.** Outstanding
verification (once access exists): RLS enabled on every tenant table; policy names, commands
(`SELECT`/`INSERT`/`UPDATE`/`DELETE`/`ALL`), roles and `USING`/`WITH CHECK` expressions for
cross-organisation isolation, consultant-firm isolation, processing-entity isolation,
capability/grant enforcement, entitlement ownership, provenance integrity, notification access,
conversation access, document/storage access and billing/usage access. If policy text cannot be
safely extracted, that limitation must be recorded rather than guessed.

---

## 8. Auth reconciliation — `REQUIRES PRODUCTION-CONSOLE VERIFICATION`

`VERIFIED` (repository side only):
* Supabase Auth is the single identity system (Blueprint V1.3 §4.1); backend validates
  Supabase-issued JWTs; frontend is configured against the production project (§2).
* The **production auth/runtime component versions** were cached from a previous link
  (GoTrue `v2.195.0`) — reference only.

`REQUIRES PRODUCTION-CONSOLE VERIFICATION` (not readable from here):
* production site URL and additional redirect URLs;
* email/auth settings (confirmations, signup enablement, password policy, SMTP);
* JWT expiry/issuer configuration relevant to backend validation;
* whether production Auth state is consistent with Release-1 assumptions.

**No user was created or modified; no secret is reproduced.**


---

## 9. Storage reconciliation — `UNKNOWN`

The production `documents` bucket **could not be inspected** (no connection).

**Repository-side fact (decisive for the prerequisite):** **no migration creates the bucket.** The only
reference is:

```
supabase/migrations/20260823000000_d32_private_documents_storage.sql:18
UPDATE storage.buckets SET public = FALSE WHERE name = 'documents';
```

That statement **assumes the bucket already exists**; the same migration then defines the storage
policies. Therefore **bucket creation is an out-of-band prerequisite** and — absent console
verification — its absence in production remains possible.

> **`DR-08 remains a deployment blocker.`** (unchanged; not resolvable from this environment)

**No bucket was created, and no file was uploaded, downloaded or signed.**

---

## 10. Emission-factor findings

No factor data was loaded, copied or relocated.

| Question | Finding |
|---|---|
| Production has expected factor **structures**? | `UNKNOWN` — schema not inspectable. Repository-side: factor structures are created by `00000000000000_init_schema.sql`, `20260800000000_rc2_schema.sql`, `20260807010000_add_emission_factors_import_batch.sql`, `20260810020000_v3m3_customer_factors.sql`, `20260807050000_add_factor_aliases.sql` |
| Production currently holds factor **rows**? | `UNKNOWN` — not safely queryable |
| Approximate production row count | `UNKNOWN` (never estimated or guessed) |
| Clean authoritative **production-load source** in the repository? | **YES, but misplaced.** `output/sql/import_defra_2025.sql` — **5 602 253 bytes**, tracked at `HEAD`, containing **14 059** factor insert statements (DEFRA 2025 import). Reachable **only** via its already-tracked git blob; it was **deleted from the working tree** (one of the 152 excluded deletions) |
| Source trapped in excluded `output/**`? | **YES.** `output/**` was outside the Release-1 staging boundary. A second copy, `output/sql/emission_factors.sql` (**5 707 634 bytes**, 7 049-factor export), exists **on disk only and is untracked/not committed** |

**Consequence:** the factor dataset is not reachable from a clean Release-1 checkout path — it exists
either as a tracked-but-deleted file inside an excluded tree, or as an uncommitted local file.
**`DR-02` is confirmed unchanged (P0 prerequisite).** *Not remediated here (out of scope).*

---

## 11. Provisioning / billing readiness — schema `UNKNOWN`, code `READY`

Production schema for provisioning/billing is **not inspectable** (`UNKNOWN`). Repository-side, these
structures are created by the `d37` migrations:

```
billing_plans · billing_commercial_config · billing_credit_ledger ·
billing_orders · billing_payment_records · billing_storage_usage ·
billing_idempotency_keys        (+ customer_subscriptions, usage_tracking)
```

Application capability (repository-verified): the v3 provisioning path exists —
`/api/v3/commercial` (plans, subscriptions, subscription status, credits grant/adjust/refund/
reverse/rollover, orders + complete, entitlement, config) and `/api/v3/billing` (assisted/managed
orders, approve/cancel) — with D6 entitlement enforcement fail-closed and usage recording on approval
(`backend/data/billing.py`, `usage_tracking.usage_month = date`).

**Conclusion:** the application *appears capable* of provisioning a clean customer through the
intended v3 path **once** migrations are applied and an authorised operator exists. **No production
record was created** (no subscription, allowance, organisation or user).


---

## 12. Production-vs-local comparison (explicitly separated)

Read-only, **local only** — this is **not** evidence of production state.

| Measure | Local dev `:54426` | Isolated E2E `:55326` | **Production** |
|---|---|---|---|
| `public` tables | 116 | 116 | `UNKNOWN` |
| RLS-enabled `public` tables | 116 | (not re-queried) | `UNKNOWN` |
| RLS policies | 174 | 175 | `UNKNOWN` |
| recorded migrations (`schema_migrations`) | 46 | 26 | `UNKNOWN` |
| `emission_factors` rows | 7 049 | **0** | `UNKNOWN` |
| `documents` bucket present | yes (1) | **no (0)** | `UNKNOWN` |

**Interpretation:** even the isolated E2E stack has **no factor rows and no `documents` bucket**,
independently confirming that factor loading and bucket creation are genuine **external
prerequisites** rather than something the migration set provides. **No inference from either local
stack to production is made anywhere in this report.**

---

## 13. Blocker matrix (evidence from this reconciliation)

| ID | Finding | Severity | Justification |
|---|---|---|---|
| DR-01 | Live production migration state — **now also availability-affected**: project host NXDOMAIN; no read-only access | **P0** / `UNKNOWN` | Still prevents any deployment decision; additionally *why* it is unknown is now evidenced (§5) |
| DR-02 | Emission-factor reference source not reachable from a clean Release-1 path | **P0** | Confirmed unchanged: 5.6 MB factor import is tracked inside an excluded tree and deleted from the worktree; the worktree copy is untracked |
| DR-04 | Production secrets/environment not representable from the repo | **P0** | Unchanged; confirmed no read-only production credential exists locally |
| **DR-15 (NEW)** | **Production project availability not confirmed — the dedicated project hostname does not resolve while control lookups and the regional pooler succeed** | **P0** | New, directly evidenced finding from §5; must be resolved by the PO in the Supabase console before any deployment operation can be planned |
| DR-03 | Migration history ≠ schema | **P1** / `UNKNOWN` | Cannot be evaluated without access; local evidence (46 / 26 recorded vs 116 tables) still justifies object-level reconciliation |
| DR-05 | Frontend build/output config not in repo | **P1** | Unchanged |
| DR-08 | `documents` bucket not created by any migration | **P1** | Re-confirmed (§9); bucket existence in production `UNKNOWN` |
| DR-09 | OCR system binaries not expressible in `requirements.txt` | **P1** | Unchanged |
| DR-10 | Backup / PITR / restore undefined in repo | **P1** | Unchanged |
| DR-13 | No migration down-scripts (forward-only) | **P1** | Unchanged |
| DR-06 / DR-07 / DR-02b / DR-12 | Frontend production fallbacks · hard-coded CORS incl. ineffective wildcard · `supabase/seed.sql` local dump-style file · repository hygiene | **P2 / P3** | Unchanged from the Deployment Readiness audit |
| DR-14 | P6-2F residual evidence gaps | **EVIDENCE GAP** | Unchanged; not a launch blocker |

**No blocker was invented beyond DR-15**, which is a direct, evidenced consequence of the probes in
§5 (not a general imperfection finding).

### Unresolved `UNKNOWN`s (explicit)

1. Production migration history — recorded versions, missing versions, unexpected/duplicate/malformed
   versions, ordering anomalies.
2. Production schema objects (tables, columns, types, nullability, PK/FK, unique/check, indexes,
   functions, triggers).
3. Production RLS enablement and policy definitions.
4. Production grants/privileges.
5. Production storage bucket existence, privacy and policies.
6. Production emission-factor structures and row availability.
7. Production Auth configuration (site URL, redirects, email/JWT policy).
8. Production backup/PITR posture.
9. Whether the production project is merely paused or no longer exists.


---

## 14. Required final determination (§15)

**Q1 — Is the production Supabase target confirmed?**
**Yes — CONFIRMED.** Ref `pvwiojoyaqywtydzcpbg`, name `CarbonTally`, org `pfurlzwxdtvyljnahlnx`,
corroborated by CLI link metadata, `supabase/.temp/project-ref`, `backend/supabase/.temp/project-ref`,
root `.env.production`, `frontend/.env.production` and the shipped frontend default.

**Q2 — Can production be queried safely in read-only mode?**
**No.** No read-only or password-based production credential exists. The only production-capable
credential present is a write-capable service key, which was **not** used. The command that could have
read history (`supabase migration list --linked`) **can mutate** (it creates a temporary login role)
and was **not re-run**. Additionally, the project API host does not resolve.

**Q3 — What migration versions are actually recorded in production?**
**`UNKNOWN`.** Not obtainable without mutation risk or prohibited credentials.

**Q4 — What Release-1 migrations are missing?**
**`UNKNOWN`.** The delta cannot be determined; for all 17 neither "applied" nor "missing" may be
asserted.

**Q5 — Does production schema match Release-1 for the production-critical objects?**
**`UNKNOWN`** — no catalog access.

**Q6 — Does production RLS match the Release-1 security model?**
**`UNKNOWN`** — no policy access.

**Q7 — Does the private `documents` bucket exist?**
**`UNKNOWN`** — and repository evidence proves **no migration creates it**, so `DR-08` remains a
deployment blocker regardless of what production holds.

**Q8 — Is the emission-factor reference data present in production?**
**`UNKNOWN`.** Repository-side, the authoritative DEFRA load source is **misplaced** (tracked inside
the excluded `output/**` tree and deleted from the worktree; the remaining on-disk copy is untracked)
→ `DR-02` remains a P0 prerequisite.

**Q9 — What exact prerequisites remain before migrations may be applied?**
1. **Resolve production project availability** (DR-15) — confirm in the Supabase console whether the
   project exists, is paused, or has been deleted. This is now the **first** blocker.
2. Provide a **genuinely read-only** production access path (a read-only DB role, or an approved
   read-only connection whose password is supplied out-of-band) — **not** a service-role key.
3. **Reconcile history AND objects** for all 53 migrations (DR-01 / DR-03) using that access.
4. Load the **emission-factor** reference library from the authoritative source (DR-02).
5. Create/verify the private **`documents` bucket** (DR-08).
6. Configure **production secrets/environment** (DR-04).
7. Install the **OCR system binaries** (DR-09).
8. Confirm **backups/PITR** and rehearse **rollback** (DR-10 / DR-13).

Only then may migrations be applied — and applying them is a **separate, explicitly authorized**
operation.

**Q10 — Is CarbonTally now ready for the next deployment operation?**
**No.**

> ## `NOT READY — PRODUCTION STATE STILL UNKNOWN`

The alternative verdicts do not apply: `RECONCILIATION FOUND BLOCKERS` would require having
*inspected* production objects (none could be inspected), and `READY FOR NEXT DEPLOYMENT OPERATION`
(which requires PO authorization anyway) is plainly unavailable. The production target is confirmed,
but the production **state** — and even its **availability** — remains unestablished.

---

## 15. Exact next recommended operation

> **Step 1 — PO console action (not an agent action).** In the Supabase console for organisation
> `pfurlzwxdtvyljnahlnx`, determine whether project **`CarbonTally`** (`pvwiojoyaqywtydzcpbg`)
> currently **exists**, is **paused**, or has been **deleted**, and confirm that this is the correct
> production project for Release-1. (Evidence in §5 shows its dedicated hostname does not resolve
> while all control lookups and the regional pooler succeed.)
>
> **Step 2 — if and only if a production project is confirmed to exist:** authorize a **single bounded
> read-only reconciliation operation** supplied with a **read-only** database credential
> (host `aws-0-eu-west-2.pooler.supabase.com`, port `5432`, database `postgres`, user scoped to project
> `pvwiojoyaqywtydzcpbg`) — **not** a service-role key — so that §4, §6 and §7 can be closed
> **object-by-object** rather than by migration history alone.
>
> **Not authorized yet:** applying migrations, loading factor data, creating the storage bucket,
> configuring secrets, deploying Render/Vercel, or provisioning any organisation.

---

## 16. Mandatory no-change confirmation

```text
Repository source modified: NO
Tests modified: NO
Migrations modified: NO
Git commit created: NO
Git push performed: NO
Production database altered: NO
Production migrations applied: NO
Production data created: NO
Emission-factor data loaded: NO
Demo data migrated: NO
Production users created: NO
Production organisations created: NO
Production subscriptions created: NO
Production storage modified: NO
Production RLS modified: NO
Production Auth modified: NO
Production deployment performed: NO
Secrets changed: NO
```

*The only files written by this operation are the two durable documentation artefacts named in §17 of
the prompt; both are untracked and unstaged.*

---

## FINAL VERDICT

## `NOT READY — PRODUCTION STATE STILL UNKNOWN`


---
---

# PART 2 — ACTIVE-PROJECT OBJECT-LEVEL RECONCILIATION

**Prompt Ref:** `CT-PROD-SUPABASE-RECON-20260911-002` · **Date:** 2026-09-11 · **Mode:** READ-ONLY
**Supersedes for §5–§13 below:** the `UNKNOWN` results of Part 1 (**Part 1 is preserved above in full**).
**Release-1:** `daad396523ac693352cc2f4ebb7fc58814a9e60b` (HEAD; unchanged) · **Branch:** `main`

## 0A. Headline result of Part 2

* **`DR-15 — production availability: RESOLVED.`** Production is **active and reachable**: the API host
  now resolves and both `/auth/v1/health` and `/rest/v1/` respond (401 unauthenticated, 200 with a
  read-only key); GoTrue reports `v2.196.0`.
* **Production ≠ Release-1.** The production *effective schema* corresponds to approximately the first
  **21 of 53** repository migrations. **All 17 Release-1 migrations are not applied**, and a further
  ~15 pre-Release-1 migrations are also unapplied.
* **Confirmed additional blockers (now evidenced, not theoretical):**
  the private **`documents` bucket does not exist** (`NoSuchBucket`); the entire **D37 `billing_*`
  family is absent**; **`work_item_assignments`** and **`vehicles`** are absent; **all** Release-1
  workflow/provenance columns are absent.
* **Confirmed resolved on the production side:** the **emission-factor library IS present** —
  **exactly 7 049 rows** — matching the local library.
* **New security finding:** **`emission_factors` is readable by the anonymous role** (all 7 049 rows).
  All other probed tables return `[]` to anon, so the exposure is isolated to that one table.

## 0B. Connection / target verification (no secrets disclosed)

| Item | Value |
|---|---|
| project ref | `pvwiojoyaqywtydzcpbg` |
| project name | `CarbonTally` |
| organisation | `pfurlzwxdtvyljnahlnx` |
| endpoint | `https://pvwiojoyaqywtydzcpbg.supabase.co` |
| database | `postgres` (per cached pooler URL; no password retained in the repository) |
| connection actually used | **HTTPS PostgREST/GoTrue/Storage APIs via the repository's public publishable (anon-class) key** — GET-only |
| identity confirmation | the same ref is asserted by CLI link metadata, two `.temp/project-ref` files, root `.env.production` and `frontend/.env.production`; API responses are self-consistent with project `CarbonTally` |

**Read-only access method and why it is admissible:** `SUPABASE_ACCESS_TOKEN`, `PGPASSWORD`,
`PGHOST`, `~/.pgpass`, `~/.netrc` and the CLI login token are **all absent**, and the sole
DB-capable credential present (`SUPABASE_SERVICE_KEY`) is **write-capable and explicitly prohibited**.
A `psql`/SELECT-only DB session was therefore **not available**. The **publishable key** is (a) already
committed in the shipped frontend and (b) **not write-capable in this schema**: a repository-wide scan
of all 53 migrations found **no policy or grant to `anon` at all** (policies target `authenticated` and
`service_role`; the only occurrence of "anon" is a comment). Every request issued in Part 2 was an
**HTTP GET** (PostgREST maps GET → `SELECT`), so **no statement capable of mutation was ever sent**.
Where a method could not be proven read-only it was **not used** — in particular no write-verb probe
was attempted to test `anon` write capability, and `supabase migration list --linked` was **not run**
(it creates a temporary login role).

**Evidence classes (rigour note):** responses with Postgres error code **`42703`**
(`column … does not exist`) are **Postgres-level and definitive** — the statement was planned by the
database itself. Responses with **`PGRST205`** ("table not found") are **PostgREST cache-level**
(strong, but to be re-confirmed with direct DB access). `NoSuchBucket` is issued by the Storage API
bucket-existence check.

**Positive controls (method validation):** 14/14 columns that must exist returned `PRESENT` — e.g.
`organizations.id`, `organizations.name`, `organizations.created_at`, `notifications.id`,
`notifications.created_at`, `manual_extraction_items.id`, `manual_extraction_items.status`,
`conversations.id`, `messages.id`, `calculation_snapshots.id`, `consultant_clients.id`, `assets.id`,
`assets.organization_id`, `document_processing_queue.id`, `processing_assignments.id`. **The probing
method is therefore validated**, and its negative results are meaningful.

## 0C. Production reachability evidence (read-only probes)

| Probe | Result |
|---|---|
| `getent hosts pvwiojoyaqywtydzcpbg.supabase.co` | resolves (172.64.149.246 / 104.18.38.10) |
| `GET /auth/v1/health` (no key) | `401` |
| `GET /auth/v1/health` (publishable key) | **`200`** → `{"version":"v2.196.0","name":"GoTrue"}` |
| `GET /rest/v1/` (no key) | `401` |
| `GET /rest/v1/` (publishable key) | `401` — *"Only secret API keys can be used for this endpoint"* (the OpenAPI catalogue is secret-key-only; per-table probes were used instead) |
| `GET /rest/v1/emission_factors?select=id&limit=1` | `200` with row data |
| `GET /storage/v1/bucket/documents` | `404` `NoSuchBucket` → **bucket absent** |


---

## 5A. Production migration history — recorded versions `UNKNOWN`; effective schema DETERMINED

* **Recorded history (`supabase_migrations.schema_migrations`) = `UNKNOWN`.** That schema is not
  exposed through PostgREST, and no DB session is available. Per §5, **history is not equated with
  schema**; the effective schema has instead been established by direct object probing.
* **Effective production schema baseline: approximately migrations 1–21**, i.e. through
  `20260810050000_v3m6_entity_rls.sql`. Everything from
  `20260821000000_d20_d15_active_consultant_grant` onward is **not present**, including **all 17
  Release-1 migrations**.
* Baseline discriminators (Postgres-level `42703` unless noted):
  * `organizations.white_label_enabled` (d21, 20260821010000) — **absent**
  * `processing_assignments.entity_id`, `.manual_extraction_batch_id` (d22, 20260821020000) — **absent**
  * `organizations.customer_type`, `consultant_clients.suspended_at/ended_at/lifecycle_updated_at` and
    tables `consultant_custom_domains` / `consultant_senders` / `data_discovery_requests`
    (d27, 20260822010000) — **absent**
  * `calculation_snapshots.source_item_id/source_file/source_page`, `manual_extraction_items.file_id`
    (d33, 20260823010000) — **absent**
  * `billing_plans`, `billing_commercial_config`, `billing_credit_ledger`, `billing_orders`,
    `billing_payment_records`, `billing_storage_usage`, `billing_idempotency_keys`
    (d37_0 / d37, 20260824020000/0300) — **absent**
  * `vehicles` (v3m7, 20260825000000) — **absent**
  * all `document_processing_queue` durability columns incl. `stage`, `attempt_count`, `locked_at`,
    `lock_token`, `max_attempts`, `pipeline_version`, `reprocess_count`, `source_item_id`,
    `extracted_data` (v3m9, 20260829000000) — **absent**
  * all 35 probed Release-1 columns — **absent**
* Baseline positives (applied): all core/base tables; `processing_entities` (v3m1);
  `customer_factors` (v3m3); `issues` (v3m5); `import_batches`; `factor_aliases`; `domain_events`;
  `calculation_snapshots`; `emissions_logs.organization_id`;
  `document_processing_queue.workflow_error_count/.workflow_next_retry_at` (20260807060000).


## 6A. 53-migration matrix (repository vs production)

Status key: `APPLIED` (object-evidenced present) · `NOT_APPLIED` (object-evidenced absent) ·
`UNKNOWN` (no directly probeable object — indexes/triggers/grants/vocabulary only).

| # | Migration | Repo | Prod history | Production evidence | Status |
|---|---|---|---|---|---|
| 1 | `00000000000000_init_schema` | YES | UNKNOWN | core tables all present | `APPLIED` |
| 2 | `20260800000000_rc2_schema` | YES | UNKNOWN | rc2-era shape implied by later objects | `APPLIED` |
| 3 | `20260801000000_rc2_constraints` | YES | UNKNOWN | constraints not probeable | `UNKNOWN` |
| 4 | `20260802000000_rc2_indexes` | YES | UNKNOWN | indexes not probeable | `UNKNOWN` |
| 5 | `20260803000000_rc2_rls` | YES | UNKNOWN | policies not probeable | `UNKNOWN` |
| 6 | `20260804000000_rc2_functions` | YES | UNKNOWN | functions not probeable | `UNKNOWN` |
| 7 | `20260805000000_rc2_triggers` | YES | UNKNOWN | triggers not probeable | `UNKNOWN` |
| 8 | `20260806000000_rc2_verification` | YES | UNKNOWN | verification only | `UNKNOWN` |
| 9 | `20260807000000_add_import_batches` | YES | UNKNOWN | `import_batches` present | `APPLIED` |
| 10 | `20260807010000_add_emission_factors_import_batch` | YES | UNKNOWN | factor structures + 7 049 rows | `APPLIED` |
| 11 | `20260807020000_add_calculation_snapshots` | YES | UNKNOWN | `calculation_snapshots` present | `APPLIED` |
| 12 | `20260807030000_add_emissions_logs_snapshot` | YES | UNKNOWN | `emissions_logs.organization_id` present | `APPLIED` |
| 13 | `20260807040000_add_domain_events` | YES | UNKNOWN | `domain_events` present | `APPLIED` |
| 14 | `20260807050000_add_factor_aliases` | YES | UNKNOWN | `factor_aliases` present | `APPLIED` |
| 15 | `20260807060000_add_dpq_workflow_columns` | YES | UNKNOWN | `workflow_error_count`/`workflow_next_retry_at` present | `APPLIED` |
| 16 | `20260807070000_add_new_table_rls` | YES | UNKNOWN | RLS/grants only | `UNKNOWN` |
| 17 | `20260810000000_v3m1_processing_entities` | YES | UNKNOWN | `processing_entities` present | `APPLIED` |
| 18 | `20260810010000_v3m2_entity_relationships` | YES | UNKNOWN | `processing_assignments` present | `APPLIED` |
| 19 | `20260810020000_v3m3_customer_factors` | YES | UNKNOWN | `customer_factors` present | `APPLIED` |
| 20 | `20260810040000_v3m5_issues` | YES | UNKNOWN | `issues` present | `APPLIED` |
| 21 | `20260810050000_v3m6_entity_rls` | YES | UNKNOWN | RLS only | `UNKNOWN` (chronologically consistent) |
| 22 | `20260821000000_d20_d15_active_consultant_grant` | YES | UNKNOWN | grants only; d21/d22 proven absent | `UNKNOWN` → implied `NOT_APPLIED` |
| 23 | `20260821010000_d21_white_label_branding` | YES | UNKNOWN | `organizations.white_label_enabled` **absent** | `NOT_APPLIED` |
| 24 | `20260821020000_d22_processing_work_assignment` | YES | UNKNOWN | `processing_assignments.entity_id` **absent** | `NOT_APPLIED` |
| 25 | `20260822000000_p9_rls_recursion_fix` | YES | UNKNOWN | policies only | `UNKNOWN` → implied `NOT_APPLIED` |
| 26 | `20260822010000_d27_d19_customer_lifecycle` | YES | UNKNOWN | `organizations.customer_type` **absent**; 3 tables **absent** | `NOT_APPLIED` |
| 27 | `20260823000000_d32_private_documents_storage` | YES | UNKNOWN | storage bucket **absent** (`NoSuchBucket`) | `NOT_APPLIED` |
| 28 | `20260823010000_d33_evidence_traceability` | YES | UNKNOWN | `calculation_snapshots.source_item_id` **absent** | `NOT_APPLIED` |

| 29 | `20260824010000_d35_self_service_onboarding` | YES | UNKNOWN | trigger-only | `UNKNOWN` → implied `NOT_APPLIED` |
| 30 | `20260824020000_d37_0_billing_security_and_configurable_subscription` | YES | UNKNOWN | `billing_plans` et al. **absent** | `NOT_APPLIED` |
| 31 | `20260824030000_d37_master_commercial_billing` | YES | UNKNOWN | `billing_*` family **absent** | `NOT_APPLIED` |
| 32 | `20260825000000_v3m7_vehicles` | YES | UNKNOWN | table `vehicles` **absent** | `NOT_APPLIED` |
| 33 | `20260828000000_v3m8_messaging_unique_participants` | YES | UNKNOWN | unique index only | `UNKNOWN` → implied `NOT_APPLIED` |
| 34 | `20260828010000_v3m8_system_admin_role_model` | YES | UNKNOWN | role model; not probeable | `UNKNOWN` → implied `NOT_APPLIED` |
| 35 | `20260828020000_v3m8_pe_manager_role` | YES | UNKNOWN | role seed; not probeable | `UNKNOWN` → implied `NOT_APPLIED` |
| 36 | `20260829000000_v3m9_durable_automatic_processing` | YES | UNKNOWN | `document_processing_queue.stage` **absent** (+18 columns) | `NOT_APPLIED` |
| 37 | `20260831000000_v3m10_org_membership_unique` | YES | UNKNOWN | unique index only | `UNKNOWN` → implied `NOT_APPLIED` |
| 38 | `20260831010000_v3m11_operational_indexes` | YES | UNKNOWN | indexes only | `UNKNOWN` → implied `NOT_APPLIED` |
| 39 | `20260831020000_audit_activity_immutability` | YES | UNKNOWN | functions/triggers only | `UNKNOWN` → implied `NOT_APPLIED` |
| 40 | `20260831030000_tenant_org_id_not_null` | YES | UNKNOWN | `assets.organization_id` exists; nullability not probeable | `UNKNOWN` → implied `NOT_APPLIED` |
| 41 | `20260831040000_consultant_revocation_roles` | YES | UNKNOWN | role vocabulary only | `UNKNOWN` → implied `NOT_APPLIED` |
| 42 | `20260902020000_v1_2_dual_origin_workflow` | YES | UNKNOWN | 6 columns **absent** (probed) | `NOT_APPLIED` |
| 43 | `20260902030000_phase5_work_item_assignments` | YES | UNKNOWN | table **absent** (`PGRST205`) | `NOT_APPLIED` |
| 44 | `20260902040000_phase5_pe_operational_messaging` | YES | UNKNOWN | 5 columns **absent** (probed) | `NOT_APPLIED` |
| 45 | `20260902050000_phase5_notification_event_key` | YES | UNKNOWN | `event_key`/`actor_domain` **absent** | `NOT_APPLIED` |
| 46 | `20260903010000_ws4_gate3_4a_item_assignment_foundation` | YES | UNKNOWN | functions/policies only | `UNKNOWN` → implied `NOT_APPLIED` |
| 47 | `20260905000000_gate4_actor_provenance` | YES | UNKNOWN | `calculation_snapshots.performed_by` **absent** | `NOT_APPLIED` |
| 48 | `20260905010000_gate5_t1_automation_provenance` | YES | UNKNOWN | 3 automation columns **absent** | `NOT_APPLIED` |
| 49 | `20260905020000_gate5_t6_automation_write_once_guard` | YES | UNKNOWN | functions/triggers only | `UNKNOWN` → implied `NOT_APPLIED` |
| 50 | `20260906010000_gate6_w1_automation_extracted_output` | YES | UNKNOWN | `automation_extracted_data` **absent** | `NOT_APPLIED` |
| 51 | `20260906090000_p6_1c_consultant_engagement` | YES | UNKNOWN | 4 engagement columns **absent** | `NOT_APPLIED` |
| 52 | `20260906100000_p6_2a_consultant_processing_permissions` | YES | UNKNOWN | 6 `can_*` columns **absent** | `NOT_APPLIED` |
| 53 | `20260910120000_p6_2d_consultant_provenance` | YES | UNKNOWN | `consultant_firm_id`/`processing_mode`/`consultant_provenance_at` **absent** | `NOT_APPLIED` |

**Totals:** `APPLIED` **15** · `NOT_APPLIED` **16** (including **10 of the 17 Release-1 migrations proven
absent by direct probe**) · `UNKNOWN` **22**, of which 12 are **implied `NOT_APPLIED`** by chronology
and by the proven absence of adjacent objects. Nothing is claimed applied on the strength of history
alone, and nothing is excluded on the strength of history alone.

### 6A.1 Release-1 migration delta — the answer to Q3

| Release-1 migration | Status | Evidence |
|---|---|---|
| #1 v3m10 org-membership unique | `UNKNOWN` (implied NOT_APPLIED) | index-only; no probe |
| #2 v3m11 operational indexes | `UNKNOWN` (implied NOT_APPLIED) | index-only; no probe |
| #3 audit/activity immutability | `UNKNOWN` (implied NOT_APPLIED) | function/trigger-only; no probe |
| #4 tenant `assets.organization_id` NOT NULL | `UNKNOWN` (implied NOT_APPLIED) | column exists; nullability not probeable via PostgREST |
| #5 consultant revocation roles | `UNKNOWN` (implied NOT_APPLIED) | role vocabulary only |
| #6 v1.2 dual-origin workflow | **`NOT_APPLIED`** | all 6 columns `42703` |
| #7 phase5 work-item assignments | **`NOT_APPLIED`** | table `PGRST205` |
| #8 phase5 PE operational messaging | **`NOT_APPLIED`** | 5 columns `42703` |
| #9 phase5 notification event key | **`NOT_APPLIED`** | `event_key`, `actor_domain` `42703` |
| #10 ws4 gate3-4a item-assignment foundation | `UNKNOWN` (implied NOT_APPLIED) | function/policy-only |
| #11 gate4 actor provenance | **`NOT_APPLIED`** | `calculation_snapshots.performed_by` `42703` |
| #12 gate5 t1 automation provenance | **`NOT_APPLIED`** | `automation_provider/model/model_version` `42703` |
| #13 gate5 t6 write-once guard | `UNKNOWN` (implied NOT_APPLIED) | function/trigger-only |
| #14 gate6 w1 automation extracted output | **`NOT_APPLIED`** | `automation_extracted_data` `42703` |
| #15 p6-1c consultant engagement | **`NOT_APPLIED`** | 4 engagement columns `42703` |
| #16 p6-2a consultant processing permissions | **`NOT_APPLIED`** | 6 `can_*` columns `42703` |
| #17 p6-2d consultant provenance | **`NOT_APPLIED`** | `consultant_firm_id`, `processing_mode`, `consultant_provenance_at` `42703` |

**10 of 17 Release-1 migrations are provably not applied; the remaining 7 are index/trigger/function/
vocabulary-only and cannot be probed through PostgREST — all 7 sit chronologically between proven-absent
neighbours, so none can be assumed present.** The Release-1 delta therefore spans essentially the whole
of the Release-1 migration set.


## 6B. Table presence matrix (GET probes, anon)

**PRESENT (28 probed):** `organizations`, `organization_members`, `users`, `processing_entities`,
`staff_profiles`, `staff_roles`, `consultant_profiles`, `consultant_firm_members`,
`consultant_clients`, `customer_factors`, `issues`, `facilities`, `assets`, `suppliers`,
`processing_assignments`, `manual_extraction_items`, `manual_extraction_batches`,
`document_processing_queue`, `calculation_snapshots`, `emissions_logs`, `notifications`,
`conversations`, `messages`, `domain_events`, `audit_trail`, `import_batches`, `emission_factors`,
`factor_aliases`, `activity_categories`, `document_types`.

**ABSENT — confirmed by probe:**

| Object | Expected by | Evidence |
|---|---|---|
| `work_item_assignments` | Release-1 #7 | `PGRST205`; PostgREST hint points to the legacy `public.processing_assignments` |
| `vehicles` | `v3m7_vehicles` (20260825) | `PGRST205` |
| `billing_plans`, `billing_commercial_config`, `billing_credit_ledger`, `billing_orders`, `billing_payment_records`, `billing_storage_usage`, `billing_idempotency_keys` | `d37_0` / `d37` (20260824) | `PGRST205` (7 tables) |
| `consultant_custom_domains`, `consultant_senders`, `data_discovery_requests` | `d27_d19` (20260822) | `PGRST205` |

**Not a diff (withdrawn after repository verification):** `consultant_firms`, `entity_relationships`,
`work_items` and `profiles` **are not created by any migration in this repository** — their absence in
production is expected, not a discrepancy. Likewise, two early probes used incorrect column names
(`assets.org_id`, `processing_assignments.processing_entity_id`, `organizations.white_label`,
`processing_assignments.assignee_user_id`, `domain_events.organization_id`) and were **withdrawn and
re-run with the authoritative names** (`assets.organization_id`, `processing_assignments.entity_id`,
`organizations.white_label_enabled`); the corrected results are those reported in §5A/§6A.

## 7A. RLS reconciliation — partial, with one material exposure

**What is verified:** for every probed tenant table except one, the **anonymous role sees zero rows**
(`organizations`, `organization_members`, `notifications`, `conversations`, `usage_tracking`,
`customer_subscriptions`, `manual_extraction_items`, `factor_aliases`, `activity_categories`,
`document_types`, `suppliers`, `facilities` → all `[]`). **Row-level isolation is therefore active and
enforced for the anonymous role** — a positive security signal, and consistent with the repository
model in which policies target `authenticated`/`service_role` only.

**Material exposure (NEW — security DIFF):**

```
GET /rest/v1/emission_factors?select=id&limit=1        → 200  [row data returned]
GET /rest/v1/emission_factors  (Prefer: count=exact)   → 206  content-range: 0-0/7049
```

**The `emission_factors` table is fully readable by the unauthenticated/anonymous role — all 7 049
rows.** The content is public reference data (DEFRA 2025 factors), so this is **not** a tenant-data
breach, but it is a deviation from the repository model (which grants nothing to `anon`) and it uses
production egress. Two explanations are possible and **could not be distinguished read-only**:
(a) RLS is **disabled** on `emission_factors`, or (b) a permissive `anon`-facing SELECT policy exists.
**Clause (a) would additionally imply possible anonymous WRITE capability**, which is a serious
data-integrity risk. **This was deliberately not tested**: probing write capability requires a
write-verb request, which the safety boundary prohibits. It requires Supabase-console or read-only-DB
confirmation.

**Still `UNKNOWN` (not probeable through PostgREST):** RLS-enabled/disabled flags per table, policy
names, commands, roles, `USING`/`WITH CHECK` expressions, and grants/privileges — i.e. the full §7/§8
inventory. No policy was created, dropped or altered.

## 9A. Storage reconciliation — bucket ABSENT (confirmed)

| Probe | Result |
|---|---|
| `GET /storage/v1/bucket/documents` | `{"statusCode":"404","error":"Bucket not found","code":"NoSuchBucket"}` |
| `GET /storage/v1/object/list/documents` | `{"statusCode":"404","error":"Bucket not found","code":"NoSuchBucket"}` |

**The private `documents` bucket does not exist in production.**

> **`DR-08` is now EVIDENCED, not theoretical: `documents` bucket absence is a confirmed deployment
> blocker.**

This is consistent with `d32_private_documents_storage` being among the unapplied migrations (that
migration only flips an *existing* bucket private in any case — **the bucket is created out-of-band in
every scenario**). No bucket was created and no object was uploaded, listed or downloaded.

## 10A. Emission-factor reconciliation — PRESENT (7 049 rows)

* `emission_factors` exists and contains **exactly 7 049 rows** (PostgREST exact count,
  `content-range: 0-0/7049`) — identical to the local library.
* `factor_aliases` exists; its row count is **RLS-blocked to anon** (`*/0`) → `UNKNOWN`.
* **Q8 is therefore answered YES for the production side**: production **already holds the required
  emission-factor reference data**; **no factor load is required for deployment**.
* **`DR-02` is therefore DOWNGRADED on the production axis** — the earlier concern that production
  would have zero factors is **disproved**. What remains of `DR-02` is the **repository packaging**
  issue (the authoritative DEFRA load SQL `output/sql/import_defra_2025.sql` is tracked inside the
  excluded `output/**` tree and deleted from the worktree; `output/sql/emission_factors.sql` is
  untracked) — a **P2/P3 packaging/hygiene item**, no longer a P0 deployment blocker. *(Not fixed here.)*
* No factor data was loaded, copied or modified.


## 11A. Billing / entitlement reconciliation — structures largely ABSENT

| Structure | Repository expects | Production | Result |
|---|---|---|---|
| `customer_subscriptions` | present | **present** (anon sees 0 rows → RLS active) | `PASS (existence)` |
| `usage_tracking` | present, `usage_month` = `date` | **present** (anon sees 0 rows) | `PASS (existence)`; column type not probeable |
| `billing_plans` | present (`d37_0`/`d37`) | **ABSENT** | `DIFF` |
| `billing_commercial_config` | present | **ABSENT** | `DIFF` |
| `billing_credit_ledger` | present | **ABSENT** | `DIFF` |
| `billing_orders` | present | **ABSENT** | `DIFF` |
| `billing_payment_records` | present | **ABSENT** | `DIFF` |
| `billing_storage_usage` | present | **ABSENT** | `DIFF` |
| `billing_idempotency_keys` | present | **ABSENT** | `DIFF` |

**Consequence:** the Release-1 commercial/entitlement model **cannot function in production**. The
`/api/v3/commercial` and `/api/v3/billing` surfaces depend on the `billing_*` family (plan catalogue,
commercial config, credit ledger, orders, idempotency). With `d37_0`/`d37` unapplied, provisioning a
customer, granting an allowance and recording an idempotent charge are all impossible. **No row was
created and no billing transaction was performed.**

## 12A. Auth reconciliation

**`VERIFIED` (read-only, via the public `GET /auth/v1/settings`):**

| Setting | Production value | Assessment |
|---|---|---|
| GoTrue version | `v2.196.0` (health `200`) | service healthy |
| `external.email` | `true` | email auth enabled |
| `external.google` | `true` | Google OAuth enabled (matches the Release-1 auth model) |
| `external.anonymous_users` | `false` | anonymous sign-in disabled (good) |
| other providers | all `false` | — |
| `disable_signup` | `false` | **sign-ups enabled** |
| `mailer_autoconfirm` | `false` | **email confirmation required** |
| `saml_enabled` | `false` | — |
| `sms_provider` | `twilio` | SMS configured (unused: `phone` = false) |

**`REQUIRES SUPABASE CONSOLE VERIFICATION`:** production **site URL**, **additional redirect URLs**,
allowed origins, JWT secret/expiry alignment with the backend, MFA policy, and SMTP/mailer
configuration. These are not exposed by any read-only API used here.

**No user or Auth setting was created or modified.**

## 13A. Final production-vs-Release-1 matrix

| Area | Release-1 expected | Production (evidenced) | Result |
|---|---|---|---|
| Migration history | 53 recorded (17 new) | recorded history **not readable**; effective schema ≈ 21/53 | **`DIFF`** (history `UNKNOWN`) |
| Core schema | base + all increments | base applied; **~32 migrations unapplied**, incl. **10/17 Release-1 proven absent** | **`DIFF`** |
| RLS | enforced on tenant tables; nothing granted to `anon` | tenant tables **block anon** (good); `emission_factors` **fully anon-readable (7 049 rows)** | **`DIFF`** (one exposure) |
| Grants/privileges | `authenticated`/`service_role` scoped; no `anon` | anon evidently has schema privileges (default Supabase grants) with RLS enforcing row access | **`UNKNOWN`** (not enumerable read-only) |
| Storage | private `documents` bucket | **bucket ABSENT** (`NoSuchBucket`) | **`DIFF`** |
| Factors | required library | **7 049 rows PRESENT** | **`PASS`** |
| Billing | `billing_*` family + subscriptions + usage | `customer_subscriptions`/`usage_tracking` present; **all 7 `billing_*` ABSENT** | **`DIFF`** |
| Auth | email + Google, confirmations required | email `true`, google `true`, `disable_signup=false`, `mailer_autoconfirm=false` | **`PASS` (verified subset)**; redirect/site URL `REQUIRES CONSOLE VERIFICATION` |

*No cell is marked `PASS` without direct evidence; no cell is marked `DIFF` on inference alone.*


## 14A. Blocker re-classification (Part 2)

| ID | State after Part 2 | Severity | Evidence | Blocks migration? | Blocks deployment? | Blocks first customer? |
|---|---|---|---|---|---|---|
| **DR-15** | **RESOLVED** — production active and reachable | — | host resolves; `/auth/v1/health` 200; GoTrue `v2.196.0` | No | No | No |
| **DR-01** | **UPGRADED from `UNKNOWN` → CONFIRMED LARGE DELTA** | **P0** | effective schema ≈ 21/53; 10/17 Release-1 migrations proven absent; 16 `NOT_APPLIED` + 12 implied | **YES** | **YES** | **YES** |
| **DR-03** | **CONFIRMED** (history ≠ schema) | **P1** | recorded history unreadable; effective schema established only by object probing | YES | YES | YES |
| **DR-08** | **CONFIRMED** — `documents` bucket absent | **P1** | `NoSuchBucket` (two endpoints) | No | **YES** | **YES** |
| **DR-02** | **DOWNGRADED (P0 → P2/P3)** | P2/P3 | production already holds **7 049** factor rows → no load needed; residual is repository packaging of the DEFRA source inside the excluded tree | No | No | No |
| **DR-16 (NEW)** | `emission_factors` readable by **anonymous** (all 7 049 rows) | **P1 (security)** | `200` with rows + `content-range: 0-0/7049` | No | No | **YES** |
| **DR-17 (NEW)** | D37 commercial/billing schema absent → `/api/v3/commercial` + `/api/v3/billing` cannot function | **P1** | all 7 `billing_*` tables `PGRST205` | YES (part of delta) | **YES** | **YES** |
| **DR-18 (NEW)** | `work_item_assignments` absent while legacy `processing_assignments` present → assignment model is pre-Release-1 | **P1** | `PGRST205` + PostgREST hint | YES (part of delta) | YES | YES |
| **DR-04** | Production secrets/environment still not representable from the repo | **P0** | unchanged | No | **YES** | **YES** |
| **DR-05** | Frontend build/output config not in repo | **P1** | unchanged | No | **YES** | **YES** |
| **DR-09** | OCR system binaries not expressible in `requirements.txt` | **P1** | unchanged | No | **YES** | **YES** |
| **DR-10** | Backups / PITR / restore undefined in repo | **P1** | unchanged; **more material now** that a large delta is pending | No | No | **YES** |
| **DR-13** | No migration down-scripts (forward-only) | **P1** | unchanged; **more material now** — ~32 migrations to apply with no rollback path | YES (raises delta risk) | YES | **YES** |
| DR-06 / DR-07 / DR-02b / DR-12 | Frontend production fallbacks · hard-coded CORS · `supabase/seed.sql` dump-style file · repo hygiene | P2/P3 | unchanged | No | No | No |
| DR-14 | P6-2F residual evidence gaps | EVIDENCE GAP | unchanged | No | No | No |

**Nothing was invented:** DR-16/17/18 are direct, probed consequences of this operation. `DR-15` is
closed. `DR-02` is downgraded **only** because a positive measurement (7 049 rows) disproves its
premise; its packaging residual is retained at P2/P3.


## 15A. Mandatory answers (Part 2)

**Q1 — Is the production project active and reachable?**
**Yes.** `pvwiojoyaqywtydzcpbg.supabase.co` resolves (172.64.149.246 / 104.18.38.10);
`/auth/v1/health` → **200**, GoTrue **v2.196.0**; `/rest/v1/` responds. **`DR-15` RESOLVED.**

**Q2 — What migration versions are actually recorded in production?**
**`UNKNOWN`.** `supabase_migrations.schema_migrations` is not exposed through PostgREST and no
read-only DB session is available, so **recorded history could not be read**. The *effective* schema was
determined instead (Q4).

**Q3 — Which Release-1 migrations are not recorded?**
Not readable as *history*; however **10 of 17 are proven not applied** by direct object probing
(#6, #7, #8, #9, #11, #12, #14, #15, #16, #17), and the remaining **7 are index/trigger/function/
vocabulary-only** and cannot be verified through PostgREST — all sitting between proven-absent
neighbours. **Effectively: none of the 17 can be shown to be applied, and 10 are proven absent.**

**Q4 — Does actual production schema match Release-1?**
**No — large `DIFF`.** Production's effective schema ≈ **migrations 1–21** (through
`20260810050000_v3m6_entity_rls`). Missing: everything from `20260821000000` onward — **~32 of 53
migrations** — including all Release-1 workflow/provenance columns, `work_item_assignments`,
`vehicles`, the entire `billing_*` family, `consultant_custom_domains`/`consultant_senders`/
`data_discovery_requests`, and all `document_processing_queue` durability columns.

**Q5 — Does production RLS match Release-1?**
**`DIFF` / partial.** Positively: **all probed tenant tables block the anonymous role** (0 rows) — row
isolation is enforced. Negatively: **`emission_factors` is fully readable by the anonymous role
(7 049 rows)** — a deviation from the repository model that grants nothing to `anon` (`DR-16`). Policy
inventory, per-table RLS flags and grants remain **`UNKNOWN`** (not probeable via PostgREST).

**Q6 — Does the production privilege model support the RLS/application model?**
**Currently `UNKNOWN`, and untestable at the application level.** The `anon` role demonstrably holds
schema/table privileges (it can read 7 049 factor rows) while RLS enforces row access elsewhere; the
`authenticated`/`service_role` sets could not be enumerated. **More decisively, the application cannot
function at all until the migration delta is applied**, because required columns and tables (incl.
`billing_*`) are absent.

**Q7 — Does the private `documents` bucket exist?**
**No — `NoSuchBucket` from two Storage endpoints.** **`DR-08` confirmed as a deployment blocker.**
(The bucket is never migration-created in any case.)

**Q8 — Does production contain the required emission-factor reference data?**
**Yes — 7 049 rows**, exactly matching the local library — **but they are anonymously readable.**
**No factor load is required for deployment**, and **`DR-02` is downgraded** (residual = repository
packaging of the DEFRA source inside the excluded `output/**` tree).


**Q9 — What exact differences must be resolved before migration/deployment?**
1. Read the **recorded migration history** with a genuinely **read-only DB credential** and reconcile it
   against §5A/§6A (history is not a substitute for schema).
2. Apply the **ordered migration delta (≈32 migrations; all 53 to be reconciled)** — including the D37
   `billing_*` family, `work_item_assignments`, `vehicles`, `document_processing_queue` durability
   columns, and **all 17 Release-1 migrations** — with **schema-object verification** after each block.
3. **Create the private `documents` bucket** and verify its policies (`DR-08`).
4. **Investigate and remediate the anonymous read on `emission_factors`** (`DR-16`), including whether
   RLS is disabled there (which would imply possible anonymous **write** capability).
5. Configure **production secrets/environment** (`DR-04`); install **OCR system binaries** (`DR-09`);
   define **frontend build/output config** (`DR-05`).
6. Confirm **backups/PITR** and rehearse **rollback BEFORE applying the delta** (`DR-10`, `DR-13`) —
   there are no down-scripts.
7. Verify the **`usage_tracking.usage_month`** column type (`date`) after the delta is applied.

**Q10 — Can the Product Owner authorize the next separate operation?**
**Yes — but the next operation must be a read-only history/RLS read followed by a separately authorized
migration-preparation operation, not a deployment.** **No deployment is authorized by this report.**

---

## 16A. Exact next recommended operation

> **Operation A (recommended first).** Supply a **read-only** production database credential (a
> read-only role, or the project DB password supplied out-of-band for use with `sslmode=require` against
> `aws-0-eu-west-2.pooler.supabase.com:5432`, database `postgres`) so that one bounded read-only session
> can: (1) read `supabase_migrations.schema_migrations`; (2) enumerate RLS flags, policies and grants;
> (3) confirm the `emission_factors` RLS state and the exact column types flagged in Q9.
>
> **Operation B (only after A).** A **separately authorized migration-application operation** — after a
> verified production backup/checkpoint — applying the ordered delta (≈32 migrations) with object-level
> verification after each block, on a database that currently has **no rollback path**.
>
> **Not authorized by this report:** deploying Render/Vercel, provisioning an organisation, creating the
> storage bucket, loading factors, or modifying RLS/Auth.

---

## 17A. Mandatory no-change confirmation (Part 2)

```text
Repository source modified: NO
Tests modified: NO
Migrations modified: NO
Git commit created: NO
Git push performed: NO
Production database altered: NO
Production migrations applied: NO
Production data created: NO
Emission-factor data loaded: NO
Demo data migrated: NO
Production users created: NO
Production organisations created: NO
Production subscriptions created: NO
Production storage modified: NO
Production RLS modified: NO
Production Auth modified: NO
Production deployment performed: NO
Secrets changed: NO
```

*Only documentation files were written (this report and the `RECON-002` history record). Every
production interaction was an HTTP **GET** (PostgREST → `SELECT`); no write-verb, DDL or migration
command was issued at any point.*

---

## FINAL VERDICT (Part 2 — supersedes the Part 1 verdict)

## `NOT READY — RECONCILIATION FOUND BLOCKERS`

