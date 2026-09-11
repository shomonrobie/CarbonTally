# CarbonTally — Production Backup, Restore & Disaster Recovery Roadmap V1.0

**Prompt Ref:** `CT-PROD-BACKUP-DR-ROADMAP-DOC-20260911-001`
**Response Ref:** `CT-PROD-BACKUP-DR-ROADMAP-DOC-20260911-001-R1`
**Datetime:** 2026-09-11
**Document type:** Future-work roadmap / durable planning record. **Not an authorization.**
**Status:** **`PARKED — FUTURE PRODUCTION HARDENING`**

> This document records what remains to be built so that it is not forgotten while the main CarbonTally
> roadmap continues through Phase 6, Phase 7 and Phase 8. It authorizes **no** work, **no** production
> contact, **no** migration and **no** restore. Nothing in it may be read as approval to begin.

---

## 0. Status at a glance

| Item | Status |
|---|---|
| Production Backup **Phase 1** (encrypted logical export foundation) | **COMPLETE** within its authorized scope |
| Production Backup **Phase 1.1** (F1–F12 remediation) | **COMPLETE**; independently verified |
| **P1.1 N1** (`backup_id=""` fail-closed) | **REMEDIATED and INDEPENDENTLY VERIFIED — CLOSED** |
| Backup/DR programme | **PARKED — FUTURE PRODUCTION HARDENING** |
| **`DR-20`** | **NOT SATISFIED** |
| Restore implementation | **NOT IMPLEMENTED** |
| Proven restore drill | **NOT PERFORMED** |
| Scheduled backups | **NOT IMPLEMENTED** |
| Supabase Storage-object backup | **NOT IMPLEMENTED** |
| Migrations 22 → 53 | **NOT AUTHORIZED** |
| Production backup authorized | **NO** |
| Production restore authorized | **NO** |

**Position statement.** The existing backup foundation provides an **encrypted, checksummed logical
database backup capability** suitable for continued future development. It is a *capability*, not a
*recovery guarantee*: an archive that has never been restored proves nothing.

---

## 1. Purpose, authority and use

**Purpose.** Establish one durable record of the future CarbonTally Production Backup, Restore &
Disaster Recovery work, including its boundaries, its proposed staging, its open decisions, and the
principles that must govern its eventual architecture.

**Authority consulted (read, unmodified).**

| Document | Used for |
|---|---|
| `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | Platform architecture of record (Supabase/Postgres/Auth/Storage/Realtime topology). |
| `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | Phase 6 / 7 / 8 definitions, dependencies (§12), current position (§13). |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_ARCHITECTURE_20260911.md` | Design of record: feasibility, restore strategy (§13), storage-object separation (§14), retention (§16), `DR-20` prerequisite (§20), proposed phases (§22), first-customer impact (§23A). |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_IMPLEMENTATION_PHASE1_20260911.md` | What Phase 1/1.1 actually implemented; remaining prerequisites (§9); unimplemented list (§10); `DR-20` status (§11). |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_PHASE1_1_INDEPENDENT_VERIFICATION_20260911.md` | Independent verdict `P1.1 VERIFIED — PASS WITH NON-BLOCKING FINDINGS`; §8 `DR-20 — NOT SATISFIED`. |
| `docs/architecture/CARBONTALLY_PRODUCTION_BACKUP_P1_1_N1_INDEPENDENT_VERIFICATION_20260911.md` | Independent verdict `N1 VERIFIED — PASS`. |
| `docs/architecture/CARBONTALLY_PRODUCTION_MIGRATION_SAFETY_PLAN_20260911.md` | `DR-20` as a P0 hard gate on migrations 22 → 53. |
| `docs/cline/prompt-history/CT-PROD-BACKUP-*.md` (8 records) | Prompt/response provenance for architecture, decisions, Phase 1, Phase 1.1, N1. |

**What this document does.** It records status, boundaries, future work, and principles.

**What this document does not do.** It does not authorize implementation, does not define the final
architecture, does not schedule work, does not change any Product Owner decision, does not modify any of
the documents above, and does not mark `DR-20` complete.

---

## 2. What exists today (implemented and verified)

| Capability | State | Evidence |
|---|---|---|
| Pure-Python logical export (`asyncpg`, no `pg_dump`, no Docker, no subprocess) | Implemented | Phase 1 report; decision **D1** |
| Catalog capture: tables, columns, identity/generated columns, collations, constraints, indexes, sequences + ownership, functions, triggers, RLS policies, extensions, comments, partition parents/leaves | Implemented (F1, F3–F9) | Phase 1.1 implementation + verification |
| Credential-bearing schema deny-list, fail-closed at two layers | Implemented (F2) | Phase 1.1 |
| `backup_id` allow-list validation, fail-closed for every supplied value | Implemented (F10, N1) | N1 remediation + `N1 VERIFIED — PASS` |
| Application-level AES-256-GCM encryption; only ciphertext reaches the storage boundary | Implemented | Decision **D3**; ciphertext-only boundary tests |
| Checksums independent of provider semantics (`content_sha256` vs `provider_checksum`), read-back verification, discard-on-mismatch | Implemented (F11) | Phase 1.1 |
| Artifact manifest, deterministic archive, staging hygiene (`0700` staging, cleanup on every path) | Implemented | Phase 1/1.1 suites |
| Snapshot discipline (`REPEATABLE READ` + `READ ONLY`) | Implemented | Phase 1/1.1 suites |
| Storage provider interface (local + in-memory implementations) | Implemented | Decision **D2** — production provisioning untouched |
| Test baseline (current, independently reproduced at N1 verification) | `tests/unit/backup` **109 passed**; `tests/integration/backup` **9 passed** | N1 independent verification; full `tests/unit` **1,763 passed** per the N1 implementation report |

**Interpretation.** CarbonTally can currently *produce* a durable, encrypted, checksummed export of its
database schema and data into an off-site-capable artifact. It cannot yet *recover from* one, and it does
not yet cover uploaded documents. Those are the two facts that keep `DR-20` unsatisfied.

---

## 3. What is explicitly NOT implemented

| Not implemented | Consequence today |
|---|---|
| Restore engine (any form) | No recovery path exists from an archive. |
| Disposable/recovery environment provisioning | Nowhere safe to prove a restore. |
| Automated restore verification | Nothing detects an unrestorable archive. |
| Formal DR restore drill | **`DR-20` cannot be satisfied.** |
| Backup scheduling | Backups are not automatic; none recur. |
| Backup failure detection / alerting | A silent backup failure would be invisible. |
| Retry / idempotency at the job-orchestration layer | Single-shot runs only; no stale-lock recovery, no dead-letter handling. |
| Off-site destination provisioning | No private bucket, lifecycle rule, or write-scoped credential exists. |
| Backup lifecycle management (expiry, deletion authorization) | Retention exists as a concept, not as enforcement. |
| Supabase Storage-object backup/recovery | Uploaded PDFs/CSV/XLSX/images are **not** protected by the database artifact. |
| Application-level recovery validation | No post-restore proof that the application starts and its critical workflows function. |
| Monitoring / alerting for backup and recovery posture | No visibility of backup age, last success, or recovery readiness. |
| Recovery runbooks | No written procedure a human could follow under pressure. |
| Measured RPO / RTO | Recovery expectations are undefined. |
| Security review of the recovery path | Restore is the highest-risk capability and is unreviewed — because it does not exist. |
| Production recovery procedures | No authorized procedure for restoring production. |
| `ct_backup` least-privilege role | The exporter supports injection; the role was never created in any environment. |
| Reserved for later scope | `DR-16` (anonymous `emission_factors` readability) and `DR-19` (D6 same-month uniqueness) — related but **separate**, neither fixed nor absorbed into this programme. |

---

## 4. Roadmap boundary (binding for the current roadmap period)

```text
Backup / DR work is PARKED.
```

| Boundary statement | Status |
|---|---|
| Backup/DR work is currently parked | **TRUE** |
| It does **not** block Phase 6 completion | **TRUE** — Phase 6 gates run **P6-2C → P6-2D → P6-2E → P6-2F** with no backup/DR dependency |
| It does **not** block Phase 7 | **TRUE** — Phase 7 (Auditor/Assurance) depends on Phase 6, not on DR |
| It does **not** block Phase 8 | **TRUE** — Phase 8 (Advanced Analytics) depends on the Phase 6→7 sequence, not on DR |
| No production restore is currently authorized | **TRUE** |
| No production backup is currently authorized | **TRUE** |
| Migrations 22 → 53 remain **NOT AUTHORIZED** | **TRUE** |
| Future backup/DR work requires **separate authorization** | **TRUE** |

**Consequences to respect while parked.**

* The parked programme must not be used as an argument to reorder, delay or expand Phase 6/7/8 gates.
* Conversely, Phase 6/7/8 work must not silently absorb backup/DR scope (for example, no "convenient"
  restore endpoint, no backup UI, no scheduling, no Storage-copy job added as a side effect of a Phase-6
  change).
* The two P0/P1 classifications recorded in the backup architecture (§23A) remain outstanding: a
  **pre-migration backup + proven restore drill** is a P0 gate *on the migration operation*, and
  **Phase 1–2 plus one Phase 3 drill** was recommended before the first customer. Those are criteria on
  *other* operations (migration, first customer), not authorization to start now.
* Because the programme is parked, the classification above is a **planning constraint**, and any movement
  on it requires explicit, separate Product Owner authorization.

---

## 5. `DR-20` — definition preserved, NOT satisfied

> **DR-20** is not satisfied until CarbonTally has a **proven restore into a disposable environment** and
> the required recovery evidence is recorded.

Preserved from the migration safety plan and the backup architecture (§20), which state the exact
prerequisite before migrations 22 → 53 may be authorized:

> A **verified, restorable backup of the pre-migration production database** must exist **off-site**, with
> (a) a completed logical dump of the `public` schema + data (+ role definitions); (b) a recorded
> **SHA-256 checksum** and manifest; (c) **encryption at rest** with the key held outside the artifact;
> and (d) **a proven restore** of that archive into a **disposable project** — recovering schema, data and
> RLS — **before** any migration touches production.

**Current `DR-20` state:**

| Element | State |
|---|---|
| (a) logical dump capability of schema + data | **AVAILABLE** (Phase 1/1.1) — not yet exercised against production |
| (b) checksum + manifest | **AVAILABLE** (Phase 1/1.1) |
| (c) encryption at rest, key held outside the artifact | **IMPLEMENTED**; production key custody/escrow **NOT DONE** |
| (d) proven restore into a disposable environment | **NOT DONE** |
| Off-site production destination | **NOT PROVISIONED** |

> ### **`DR-20 — NOT SATISFIED`**

`DR-20` must **not** be marked complete in any document, issue tracker or acceptance record until (d) has
been performed and evidenced. A dump that has never been restored cannot satisfy it — the restore drill
*is* the evidence.

---

## 6. Future work register (roadmap level — nothing here is implemented)

Each item records *what*, *why it matters*, and *what it depends on*. Sequencing is proposed in §11; the
items are not authorization to build.

| # | Work item | What it means | Depends on |
|---|---|---|---|
| 1 | **Restore engine** | Code that decrypts an artifact and restores schema, data, sequences, constraints, RLS policies and role definitions into a **new** database/project in a defined order, with verification hooks. Must be a **separate, strongly authorized, high-risk capability** (decision D4) — never casual, never a one-click production action. | B1 reassessment; key custody; least-privilege restore credential |
| 2 | **Disposable restore environment** | Provisioning of a throwaway Supabase project/database used as the restore target, so recovery is proven **without** ever touching production. | restore engine; provisioning authorization |
| 3 | **Automated restore verification** | Post-restore checks: object/row counts against an oracle, schema fingerprint, RLS policy presence, sequence ownership, constraint validity, application start-up, and at least one critical business workflow (auth, provisioning, one processing path). | disposable environment; restore engine |
| 4 | **Formal DR restore drill** | A recorded, evidence-bearing exercise that satisfies `DR-20`: artifact → decrypt → restore → verify → evidence (git SHA, artifact checksum/manifest, target, timings, RPO/RTO achieved). | 1, 2, 3 |
| 5 | **Scheduled backups** | Recurring automatic execution (frequency is a PO decision; the architecture's initial proposal is daily + weekly classes). Backups that never run are not backups. | B1 reassessment; destination provisioning; job orchestration |
| 6 | **Backup failure detection** | Detection that a scheduled run did not happen, failed, was truncated, or produced a suspiciously small artifact — plus a visible "last successful backup" age. | 5; audit trail; monitoring |
| 7 | **Retry and idempotency** | Bounded retries, attempt counting, deterministic job/request identifiers, duplicate prevention so a retry cannot publish a second artifact for the same logical run, and stale-lock recovery. | job model (`backup_jobs` exists in design) |
| 8 | **Off-site artifact retention** | A private, independent destination with lifecycle expiry, write-scoped credentials, separated from the production host — an on-host or unencrypted copy is not credible. | B1 reassessment; provisioning authorization (OID-3) |
| 9 | **Backup lifecycle management** | Expiry enforcement, verified deletion (object **and** job reference), deletion authorization (`can_manage_backups`), an audit entry per mutation, and no silent destruction of required auditability (aligns with N3). | 5, 8; PO decision on retention durations |
| 10 | **Backup integrity verification** | Periodic independent verification that stored artifacts still decrypt and their checksums still match, including a decrypt/restore rehearsal — bit-rot and key loss are silent. | 1, 2, 3, 8; key custody/escrow |
| 11 | **Supabase Storage-object backup/recovery** | Separate, paired export/copy of uploaded objects (see §8), tracked by a common *backup-set id* with the database artifact so a restore can select a mutually consistent pair. | B1 reassessment; destination; service-role boundary review |
| 12 | **Application-level recovery validation** | Proof that restored data actually supports the application: schema expectations, migration state, RLS behaviour and one end-to-end business outcome — not merely "the SQL ran". | 1, 2, 3 |
| 13 | **Monitoring and alerting** | Observable backup/recovery posture: last success, age, duration, size, failure reason, retry count, drill recency; alerts for stale/failed backups and failed drills. | 5, 6, 10 |
| 14 | **Recovery runbooks** | Written, human-followable procedures: assess the incident, select the correct artifact, restore to a disposable environment, verify, and the separate exceptional production path — plus a sealed configuration/secrets inventory with **names and locations only**. | 1, 2, 4 |
| 15 | **RPO measurement** | Definition **and measurement** of the recovery-point objective actually achieved by the chosen mechanism (§7). Unmeasured RPO is a claim, not a property. | 4, 5; PO decision on target |
| 16 | **RTO measurement** | Definition **and measurement** of end-to-end restore duration, including detection, decision and verification time — against the vendor's warning that a project is inaccessible during a managed restore. | 4, 5; PO decision on target |
| 17 | **Security review** | Independent review of the recovery path: restore authorization, credential scope, key custody and rotation, deny-by-default boundaries, least privilege, audit completeness and negative isolation tests (the P6-2F isolation matrix is a candidate post-restore security test). | 1, 2, 8, 14 |
| 18 | **Production recovery procedures** | The exceptional, two-person-approval procedure for restoring **production**, with a readiness snapshot immediately beforehand, an explicit downtime window and an acceptance record. Must stay separately authorized and never casually automated. | 4, 12, 14, 17 |
| 19 | **Disaster-recovery acceptance gate** | A final evidenced acceptance that the programme is complete: objectives met or explicitly waived, drills passed, monitoring live, runbooks exercised, security review closed. | all of the above |

### 6.1 Cross-cutting requirements for every item

* **No weakening of security.** Multi-tenant isolation, RLS, authorization and the storage boundary must
  not be relaxed to make backup or restore convenient. Any elevated access must stay explicit, documented
  and minimal.
* **Real evidence over claims.** Each item must produce durable evidence (artifact references, checksums,
  test output, drill records) rather than a status assertion.
* **Honest state.** Implementation, testing, verification and acceptance are distinct; a document must
  never present one as another.
* **No invented policy.** Retention durations, RPO/RTO targets, restore authorization and recovery
  boundaries are **Product Owner decisions**.

---

## 7. RPO / RTO principle

**CarbonTally does not promise, and must never claim, "zero data loss".** Recovery expectations must be
*defined, measurable and measured* for the mechanism actually chosen.

**Parameters that future implementation must define and measure:**

| Parameter | Meaning | Must be recorded as |
|---|---|---|
| **RPO** (recovery point objective) | How much committed data may be lost, expressed as a time bound | a target **and** a measured value |
| **RTO** (recovery time objective) | How long recovery may take | a target **and** a measured value |
| **Backup frequency** | How often an artifact is produced | a PO-approved schedule |
| **Retention** | How long artifacts are kept, per class | a PO-approved policy |
| **Detection time** | How long until a failure/incident is noticed | measured, with alerting evidence |
| **Restore time** | End-to-end restore + verification duration | measured during a drill |

**Mechanisms must be distinguished — they are not equivalent:**

| Mechanism | What it protects | Data-loss characteristic |
|---|---|---|
| **Periodic logical backup** (what exists today, when run) | Schema + data as of the artifact | everything written since the artifact is lost |
| **Near-real-time backup** (continuous replication/streaming) | A continuously advanced copy | small but non-zero loss window |
| **Point-in-time recovery (PITR)** | Arbitrary point within a retention window | near-zero for the window; plan-dependent and downtime-bearing to restore |
| **Zero / near-zero RPO** | Requires continuous replication *and* proven failover | only claimable when measured and drilled |

**Architecture reassessment trigger.** The eventual production architecture **must be reassessed once the
production Supabase subscription/feature set is selected** — the recovery properties available depend on
the plan, and Supabase Free provides **no managed backups and no PITR**.

**Current subscription position.** CarbonTally **remains on Supabase Free** until the Product Owner
chooses otherwise. On Free, the vendor's own recommendation is the CLI `db dump` + maintained off-site
backups — which is the shape the existing foundation already implements.

---

## 8. Supabase Storage warning (database backups are not file backups)

> **PostgreSQL/database backups do not by themselves constitute a backup of CarbonTally's uploaded Storage
> objects.**

Vendor documentation is explicit: a database backup includes **only metadata** about Storage objects
("the database only includes metadata about these objects"), and restoring an old backup **does not
restore objects deleted after that backup**. A database-only restore therefore yields document records
pointing at **missing files**.

Future DR work must therefore **separately** address application-managed Storage objects, including at
minimum:

* **PDFs** — supplier/customer source documents;
* **CSV / XLS / XLSX** — activity and emissions data uploads;
* **images** — scanned documents / OCR inputs;
* **other application-managed Storage objects** — anything else CarbonTally writes to buckets.

Additional recorded constraints:

* Database artifact and object artifact must be **paired** by a common backup-set id, because a restore
  needs **both** to be mutually consistent.
* Object copies should be a **separate job** from the database job (they are much larger and slower), but
  **sequenced** with it.
* The `documents` bucket did not exist in production at the time of the architecture assessment and there
  were no customer documents, so object backup was not blocking *then* — it becomes **P1 the moment the
  first real document is uploaded**.
* Storage access must respect the same security model as database records; authorization must occur
  **before** any signed URL or object read, and signed URLs must never be logged or recorded.

---

## 9. Future paid-Supabase decision (recorded principle, not a decision made)

> **When CarbonTally approaches real-customer production readiness and a paid Supabase plan is selected,
> reassess the DR architecture before implementing the remaining backup work.**

* If Supabase provides an **adequate managed database backup / PITR capability**, **do not unnecessarily
  duplicate** that capability with custom PostgreSQL backup infrastructure. Buying a property and then
  rebuilding it by hand is not diligence — it is duplicated risk and duplicated cost.
* Supabase Free currently provides **no managed backups and no PITR**, which is precisely why the existing
  CarbonTally-managed logical-export capability exists. If that changes with a paid plan, the assessment
  must be repeated rather than assumed.
* **CarbonTally-specific DR responsibilities may still include:** Storage-object recovery, application
  recovery, restore validation, RPO/RTO measurement, monitoring, alerting, recovery runbooks and DR
  drills — none of which a managed database backup provides.
* **Do not assume the final architecture now.** Stage **B1** exists precisely to re-open this question
  with facts instead of predictions.

---

## 10. Future implementation ownership

* Future backup/DR engineering **may be delegated to OpenHands (OHD)** as a **separate parallel
  workstream**, while **Cline** continues the main CarbonTally roadmap (Phase 6 → 7 → 8).
* The rationale is independence and parallelism: backup/DR is a self-contained programme whose
  verification benefits from an agent other than the one that implements it.
* Normal discipline still applies to whichever agent performs the work: inspect before changing, smallest
  correct change, tests before claims, evidence over assertions, and independent verification of any
  security-relevant capability (restore is security-relevant).
* **This is a future plan, not an authorization to begin that work now.** No ownership change alters any
  boundary recorded in §4.

---

## 11. Proposed future staged structure (proposal only — NOT authorized)

The structure below is the *proposed* shape of the programme. It supersedes nothing and authorizes
nothing. It expresses the work in §6 in dependency order.

```text
B1  Architecture reassessment
B2  Restore engine
B3  Disposable restore verification
B4  DR restore drill
B5  Scheduled backup orchestration
B6  Off-site lifecycle
B7  Storage-object recovery
B8  Monitoring and alerting
B9  Recovery runbooks
B10 RPO/RTO validation
B11 Security review
B12 Final DR acceptance
```

**Universal stage discipline — every stage must:**

```text
implement
   → test
   → verify
   → document
   → accept
   → continue
```

**A failed stage stops progression until it is resolved.** No stage may be "passed" by assertion, by a
spinner, or by a document claiming success; each stage must produce its own evidence, and stages that
touch security or recovery must be **independently** verified.

| Stage | Name | Objective | Exit evidence (proposed) |
|---|---|---|---|
| **B1** | Architecture reassessment | Re-open the DR design against the **selected production subscription/feature set**: decide what Supabase provides vs what CarbonTally must own; confirm or revise retention classes and mechanism (periodic logical / near-real-time / PITR); identify the PO decisions required. | A ratified reassessment record; explicit PO decisions; **no code**. |
| **B2** | Restore engine | Implement decrypt → restore schema/data/sequences/constraints/RLS/roles into a **new** target, with verification hooks and **no production path**. | Implementation report; tests incl. negative cases; no production target. |
| **B3** | Disposable restore verification | Provision a throwaway environment and prove a restore end-to-end: counts vs oracle, schema fingerprint, RLS presence, app start-up, one critical workflow. | Restore verification evidence bundle; disposable environment torn down; **0 leftovers**. |
| **B4** | DR restore drill | Perform the formal, recorded drill: artifact → decrypt → restore → verify → evidence, with timings; **satisfies `DR-20`**. | Drill record (git SHA, checksum/manifest, target, timings, RPO/RTO achieved); `DR-20` evidence. |
| **B5** | Scheduled backup orchestration | Recurring runs with failure detection, retry, idempotency, duplicate prevention, stale-lock recovery and observable state. | Orchestration tests; schedule evidence; failure-path evidence. |
| **B6** | Off-site lifecycle | Provisioned private destination, write-scoped credentials, expiry enforcement, verified deletion, deletion authorization, audit entries. | Provisioning record; lifecycle tests; audit evidence. |
| **B7** | Storage-object recovery | Separate, sequenced object backup paired to the DB artifact by backup-set id; recovery rehearsed; bucket boundary respected. | Object recovery evidence; pairing evidence; security-negative tests. |
| **B8** | Monitoring and alerting | Backup age/success/failure, retry counts, drill recency; alerting wired to an operational owner. | Alert definitions + observed firing; dashboard evidence. |
| **B9** | Recovery runbooks | Written procedures (disposable, and separately the exceptional production path), plus a sealed configuration/secrets inventory (names/locations only) and key escrow/rotation. | Reviewed runbooks; walkthrough evidence; inventory **without** secrets. |
| **B10** | RPO/RTO validation | Measure achieved RPO and RTO against targets; record any shortfall honestly; obtain PO sign-off or explicit waiver. | Measurements; PO acceptance or documented waiver. |
| **B11** | Security review | Independent review of the recovery path: authorization, credential scope, key custody, least privilege, audit completeness, negative isolation tests. | Independent findings; remediation evidence; closure statement. |
| **B12** | Final DR acceptance | Programme acceptance: objectives met or waived, drills passed, monitoring live, runbooks exercised, review closed. | Acceptance record with verdict and explicit residual limitations. |

**Relationship to the earlier "Backup Phase 1–4" proposal.** The backup architecture (§22) proposed
`Backup Phase 1` (job + secure artifact), `Phase 2` (admin UI/history/notifications), `Phase 3`
(restore-to-disposable verification) and `Phase 4` (scheduling/retention). **Phase 1 and Phase 1.1 are
done.** The B-stages above are a **finer-grained restatement** of the remaining work: they do not
contradict that proposal, and the admin-UI/history/notifications portion of `Backup Phase 2` is **not
lost** — it belongs with the operational surface of **B6/B8** and any future authorized admin work, and
must not be reintroduced under a Phase-6 label.

---

## 12. Security and authorization requirements for future work

Recorded so that no future stage solves a recovery problem by weakening the platform:

* **Restore is a distinct, higher-risk capability.** It replaces live data, is downtime-bearing, and — on
  a managed platform — may make the project inaccessible during the operation. It therefore requires
  **stronger authorization than backup**, a written checklist, two-person approval, and a readiness
  snapshot immediately beforehand. It must never be reachable as a casual or one-click action.
* **Disposable target first, always.** Production restore is the *last*, exceptional step; the default and
  demonstrated path is restore into a new disposable environment.
* **No RLS bypass, no tenant-isolation weakening, no storage-boundary relaxation** to make backup or
  restore convenient. Where elevated access is genuinely required, it must remain **explicit, minimal and
  documented**, with application-level authorization still enforced.
* **Least privilege.** A dedicated restricted backup/restore credential (the proposed `ct_backup` role:
  `BYPASSRLS` with SELECT-only grants and `default_transaction_read_only = on`, or the documented
  per-table `FOR SELECT USING (true)` fallback if `BYPASSRLS` cannot be granted) is a **production SQL
  action requiring separate authorization** and has **not** been created anywhere.
* **Key custody.** Backup encryption keys must live in a key store **separate from the artifacts**, with
  documented rotation and escrow. A manual restore does **not** automatically carry a platform-managed
  encryption root key — handle it explicitly.
* **Secrets never enter artifacts or logs.** No service keys, JWT secrets, database passwords, API keys,
  signing keys or signed URLs in the dump, the manifest, the audit record or any log.
* **Auditability.** Every backup, restore, expiry, deletion and drill action must produce an append-only
  audit record that itself contains no credentials or artifact contents.

---

## 13. Product Owner decisions required before future implementation

These are **policy** choices and must not be invented by an implementing agent:

| # | Decision needed | Affects |
|---|---|---|
| 1 | Target **RPO** and **RTO** (and any tiering by data class) | B5, B10 |
| 2 | **Backup frequency** and **retention** classes (duration, expiry behaviour) | B5, B6 |
| 3 | **Restore authorization** — who may approve a restore, and whether two-person approval is mandatory | B2, B11, B12 |
| 4 | Whether to purchase a **paid Supabase plan / PITR**, and when | B1, B5, B6 |
| 5 | Who owns **recovery operations** (role, escalation path, on-call expectation) | B8, B9 |
| 6 | **Deletion authorization** for backups (`can_manage_backups` holder) and the confirmation standard | B6 |
| 7 | Whether **Storage-object recovery** becomes P1 immediately once the first real document is uploaded | B7 |
| 8 | Any **regulatory/privacy** constraint on retention (a backup containing personal data is itself personal data) | B1, B6 |

---

## 14. Explicitly out of scope / not authorized (unchanged)

Restore implementation · restore drill · production restore · production backup · production database
contact · Supabase migration · migrations 22 → 53 · provisioning (`ct_backup` role, off-site bucket,
key store) · backup scheduling · admin backup UI · backup deletion/retention automation · Supabase
Storage-object backup · `DR-16` · `DR-19` · P6-2F remediation · Phase 6 remainder work under this
programme · Phase 7 · Phase 8 · `/demo` · `/investors` · deployment · push · commit.

---

## 15. Change control

* This document is a **planning record**, not an authorization. It grants no capability and changes no
  Product Owner decision.
* It must be **superseded only by an explicit Product Owner decision** — either a new version of this
  roadmap, or a bounded authorization prompt for a specific stage.
* Progress against it must be recorded honestly: a stage is complete only when its exit evidence exists.
  Status labels used here mean what they say — **PARKED**, **NOT IMPLEMENTED**, **NOT SATISFIED**,
  **NOT AUTHORIZED**.
* No stage may be started, and no boundary in §4 relaxed, on the basis of this document alone.

---

## 16. Mandatory no-change confirmation

This operation was **documentation-only**:

| Item | Status |
|---|---|
| Implementation code changed | **NO** |
| Tests changed | **NO** |
| Database schema changed | **NO** |
| Migration created | **NO** |
| Production contacted | **NO** |
| Production backup created | **NO** |
| Restore implemented | **NO** |
| Deployment / push / commit | **NO** |
| Authoritative documents altered | **NO** |

---

## 17. Final verdict

> ### **`PARKED — FUTURE PRODUCTION HARDENING`**

> **`DR-20 — NOT SATISFIED`**

> **`MIGRATIONS 22 → 53 — NOT AUTHORIZED`**

**Production Backup P1.1 N1 is independently verified and closed. The backup foundation (Phase 1 + 1.1)
provides an encrypted, checksummed logical database backup capability. Restore, restore drills, scheduling,
Storage-object recovery, monitoring, runbooks and RPO/RTO measurement remain future work. DR-20 remains NOT
SATISFIED. Migrations 22→53 remain NOT AUTHORIZED.**
