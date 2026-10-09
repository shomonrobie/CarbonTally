# CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01 — Report

| Field | Value |
| --- | --- |
| **Task ID** | `CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01` |
| **Date** | **2026-10-05** |
| **Author** | Cline (implementation agent) |
| **Type** | **Documentation / governance only.** No application code, schema, migration, RLS, database, fixture, credential, test or production change. No commit, no push, no deploy. |
| **Repository HEAD** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (branch `p8-release-reconciled`) — unchanged by this task |
| **Governing fact-finding** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01-report.md` |
| **Decision record produced** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` |
| **Status** | **COMPLETE** |
| **Final status** | **P-1/P-2 PO DECISIONS CLOSED — CT-MP-SUB-004 READY FOR INDEPENDENT VERIFICATION** |
| **Governance follow-up (2026-10-05)** | **P-2 scope clarification OPEN — PO DECISION REQUIRED.** P-2 remains **CLOSED** for Manual Processing **coverage allocation/release** (audit-only). Whether a **document batch entering Manual Processing** must notify an actor is **not** closed by P-2. Source: `docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md` (§7.3 question; §8.2 proposed minimum amendment — **proposed, NOT applied**); see **§H** below. The decision record itself is **unmodified**. |

---

## A. Task status

**COMPLETE.**

The task recorded the two Product Owner decisions (P-1, P-2), created the formal
PO decision record, updated the governance/acceptance-status references of the
production-readiness report so P-1/P-2 are no longer read as open blockers, and
verified the working-tree impact. Nothing was implemented, fixed, refactored,
deployed, committed or pushed.

---

## B. Files created / modified

| Action | Exact path | Nature of the change |
| --- | --- | --- |
| **CREATED** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` | **New** formal PO decision record (P-1 CLOSED, P-2 CLOSED; §§1–11) |
| **CREATED** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01-report.md` | **New** task report (this file, §§A–G) |
| **MODIFIED** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-01-report.md` | **Governance/acceptance-status references only**: header *Status* field, inline P-1/P-2 pointers in §11/§12/§13/§19/§20, and a new appended §21 *Governance status update*. **No historical evidence, test result or implementation claim was altered.** |
| **MODIFIED** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01-report.md` | **Single governance-status pointer line** in the header block only, marking P-1/P-2 as closed by the decision record. **No finding, section or evidence was altered.** |

No other file was created, modified or deleted.

---

## C. Decisions recorded

| # | Decision | PO status |
| --- | --- | --- |
| **P-1** | Production performance SLO for Manual Processing coverage operations (NV-9) | **CLOSED** — *no dedicated production SLO is required for this release; no production-scale performance or SLO-compliance claim may be made.* |
| **P-2** | Manual Processing proactive notifications (NV-10) | **CLOSED** — *proactive MP notifications are not required; allocation/release remain audit-only.* |

Both decisions are recorded, with their rationale and acceptance implications, in
`docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` (§3–§6).

**Rationale carried forward, without alteration, from the fact-finding:**

* **P-1** — no authoritative production SLO is ratified anywhere in the
  repository (its absence is itself PO-owned and recorded by five authoritative
  artefacts, incl. `CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md:746`,
  capability-matrix gap **G-21**, 8-X **G10**); **X7-D6 = 1,000 ms** is an
  observability threshold (p95 over a rolling 60 min), not a production SLO;
  **X1/X4** `queue_settings.sla_hours` is processing-turnaround, not API latency;
  the CT-MP-SUB-004 budgets are explicitly **non-production** Demo-Lab
  engineering budgets; the Demo Lab cannot establish production p99, throughput,
  concurrency, capacity or topology; creating an MP-specific SLO now would
  invent an unratified platform policy.
* **P-2** — CarbonTally already has a ratified notification architecture
  (`public.notifications` / `public.notification_delivery`, the idempotent
  notification repository, server-side recipient resolution, delivery recording,
  email delivery/retry, **D40**, **D11**, **X2**); the Manual Processing
  implementation **emits audit events only**, has **no notification producer**,
  and is **not specified by `CT-UX-MP-SUB-003` as requiring notifications**.
  The existence of the subsystem does not imply a requirement on MP transitions.

---

## D. Acceptance target changes

The **authoritative acceptance target** for CT-MP-SUB-004 is now the one
recorded in
`CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` §4 (NV-9) and §6 (NV-10).
Precisely how the two previously-unresolved entries are now interpreted:

### D.1 NV-9 — performance (was *"PO DECISION REQUIRED"*)

| Before | After (P-1 CLOSED) |
| --- | --- |
| Open PO question: is a production performance SLO required? | **Answered: no dedicated production SLO for this release.** |
| Ambiguous whether the local budgets were contractual | Local budgets remain **engineering / verification budgets only**; the **non-production disclaimer must remain explicit**. |
| No defined verification scope | Verification **limited to**: reproducible local MP performance budgets; the **required indexes remain present**; absence of obvious query/performance regression; preservation of the non-production disclaimer. |
| — | Verification **must not claim production SLO compliance**, must not claim production-scale capacity, and must not require any new SLO/monitoring architecture. |

The verifier re-runs/reproduces the local measurements only; it does **not**
certify a production SLO (none exists).

### D.2 NV-10 — notifications (was *"PO DECISION REQUIRED"*)

| Before | After (P-2 CLOSED) |
| --- | --- |
| Open PO question: must coverage grant/withdrawal notify anyone? | **Answered: no.** Allocation and release remain **audit-only**. |
| Ambiguous whether a missing notification was a defect | Explicitly **not a defect**; the absence of MP notification rows is **acceptable and expected**. |
| No defined verification scope | Verification **limited to**: confirmation that MP transitions remain **audit-only**; confirmation that **no unauthorised notification side effect** occurs; confirmation that the **existing notification architecture remains intact**; confirmation that **no new notification subsystem/provider** was introduced. |
| — | The acceptance target **must not require implementation** of proactive MP notifications. |

**Scope note (Notification fact-finding 02, 2026-10-05 — full detail in §H).**
§D.2 above closes **only** the *MP coverage allocation/release* question. It does
**not** close the separate question of whether **a document batch entering Manual
Processing** must notify an actor, and it must not be read as either requiring or
prohibiting such a notification. The decision record is **unamended** and the
clarification remains **OPEN — PO DECISION REQUIRED**.

### D.3 Unchanged acceptance items

`F-4`, `F-7`, `F-9`, `F-11`, `NV-5`, `NV-6` remain the independent verification
target established by `CT-MP-SUB-004-PROD-READINESS-01` — **unchanged**.
Previously closed decisions (`F-1`, `F-2`, `F-3`, `F-5`, `F-6`, `F-8`, `F-10`,
`NV-1`…`NV-4`, `NV-7`, `NV-8`, `N-1`, `N-2`) are **not reopened**.
**NV-7 remains NOT REQUIRED — PO CLOSED**, with no pixel-comparison tooling added.

---

## E. Implementation safety

**No application behaviour was changed.**

| Check | Result |
| --- | --- |
| Backend application code changed | **NO** |
| Frontend code changed | **NO** |
| Notification code changed | **NO** |
| Performance code / budgets / thresholds changed | **NO** |
| Tests changed or added | **NO** |
| Migrations created | **NO** |
| Schema / RLS / roles / grants changed | **NO** |
| Database data changed | **NO** |
| Demo Lab fixtures changed | **NO** |
| Notification events / providers / outbox / workers added | **NO** |
| Performance monitoring / SLO infrastructure added | **NO** |
| Anything "cleaned up" or refactored | **NO** |

The **only** files touched are Markdown documents under `docs/architecture/`
(listed in §B). Verified by inspecting the working tree after the edits.

---

## F. Production safety

Confirmed: this task performed

* **no production database access;**
* **no production credentials use;**
* **no production migration** (authored or applied);
* **no production deployment;**
* **no Supabase production link;**
* **no `git commit`;**
* **no `git push`.**

The repository HEAD is unchanged at
`375a48dc1b9e9cfd74090bbf747554ae997acb59`, and the reflog is untouched. The
working tree impact is limited to **four Markdown documents**, all currently
`??` (untracked): the two new records created by this task, plus the two
pre-existing-but-untracked CT-MP-SUB-004 reports
(`CT-MP-SUB-004-PROD-READINESS-01-report.md`,
`CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01-report.md`) that were edited **in
place** with governance-status references only.

Evidence (read-only, after the edits):

* `find` for files modified in the task window → **only** the four `.md` files
  above; no `.py`, `.js`, `.jsx`, `.sql`, JSON or config file.
* `git diff --name-only | wc -l` → **39** tracked modifications, i.e. the
  **pre-existing** CT-MP-SUB-004 / FINAL-03 worktree changes, **unchanged**;
  none under `supabase/` or of type `*.sql`.
* The two untracked MP migrations present in the tree are dated **2026-10-04**
  (authored by the earlier CT-MP-SUB-003/004 workstream) — **not** created or
  modified by this task.
* `git diff --cached --name-only | wc -l` → **0** (nothing staged).
* `git reflog -3` → HEAD@{0} is still *"FINAL-03: freeze production cutover
  release"*; **no commit, amend, reset or clean** occurred.

---

## G. Final status

The task is complete: P-1 and P-2 are recorded as **CLOSED** in the authoritative
PO decision record
`docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md`, and the
acceptance target for NV-9/NV-10 now reflects those decisions (§D).

This report does **not** claim independent verification has passed, does **not**
claim CT-MP-SUB-004 is finally accepted, and does **not** grant production
deployment or migration authorization. The next stage is independent
verification by CoStrict/OHD using the decision record above as the
authoritative PO decision source for P-1 and P-2.

> # P-1/P-2 PO DECISIONS CLOSED — CT-MP-SUB-004 READY FOR INDEPENDENT VERIFICATION

---

## H. Governance status update — P-2 scope clarification (Notification fact-finding 02, 2026-10-05)

**Appended governance metadata.** It does **not** amend §A–§G above, any historical
evidence, or any PO decision. Nothing in
`CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01.md` was changed.

**Source (read-only):**
`docs/architecture/CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02-report.md`
— task `CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-FACTFIND-02`, status
*NOTIFICATION FACT-FINDING COMPLETE — READY FOR PO CLARIFICATION*.

**Finding.** P-2 is *evidenced* over the Manual Processing **coverage
allocation/release** surface (the `manual_processing_admin.py` /
`manual_processing_auth.py` / `data/manual_processing.py` / `domain/manual_processing.py`
`grep` set), but three of its sentences are drafted at the level of *"Manual
Processing" as a whole* (decision record lines `:162`, `:232`, `:279`, `:291`), so a
reader or verifier could legitimately read P-2 as also closing the separate
question of a **document batch entering Manual Processing**. That event is created
by `services/manual_processing_routing.py` (D38 `work_item_assignments` ledger +
`manual_processing:auto_routed` audit) with **no notification producer**, and the
files that implement it are **not** in the P-2 evidence set.

**Where P-2 stands now:**

| Question | Status |
| --- | --- |
| Proactive notification for MP **coverage allocation / release** (NV-10) | **CLOSED — not required; audit-only.** Unchanged by this update. |
| Notification when a **document batch/item enters Manual Processing** | **OPEN — PO DECISION REQUIRED.** P-2 neither requires nor prohibits it. |

**Proposed minimum amendment — PROPOSED, NOT APPLIED.** A new §5.1a scope-limit
paragraph plus one clarifying clause in §6 item 5 of the decision record (exact
wording in `…NOTIFICATION-FACTFIND-02-report.md` §8.2). Until the PO applies it,
the decision record stands **exactly as written**.

**Effect on this report's earlier statements:** the §C/§D statements that P-2 is
CLOSED remain correct **for the coverage surface only**. §D.2 is subject to the
scope note above. §D.3 (`F-4`, `F-7`, `F-9`, `F-11`, `NV-5`, `NV-6`) is unchanged.

**Effect on the next stage:** independent verification proceeds on the existing
target. If the PO applies the §5.1a scope limit, verification extends per
`…NOTIFICATION-FACTFIND-02-report.md` §9.2.

**Safety:** this update is documentation only — no code, test, database,
migration, schema, RLS, notification, Realtime or fixture change; no commit; no push.
