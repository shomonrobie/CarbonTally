# CT-MP-SUB-004 — Production-Readiness Product Owner Decision Record (P-1 / P-2)

| Field | Value |
| --- | --- |
| **Document ID** | `CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01` |
| **Task ID** | `CT-MP-SUB-004-PROD-READINESS-PO-DECISIONS-01` |
| **Date** | **2026-10-05** |
| **Decision authority** | **Product Owner**, CarbonTally |
| **Recorded by** | Cline (implementation agent) — *recording, not authoring* |
| **Governing fact-finding** | `docs/architecture/CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01-report.md` |
| **Repository HEAD** | `375a48dc1b9e9cfd74090bbf747554ae997acb59` (branch `p8-release-reconciled`) |
| **Scope of this record** | Exactly two decisions: **P-1** (production performance SLO / **NV-9**) and **P-2** (Manual Processing proactive notifications / **NV-10**) |
| **Status** | **P-1 CLOSED — P-2 CLOSED** |
| **Type** | **Documentation / governance only.** No application code, schema, migration, RLS, database, Demo Lab fixture, credential or production change. No commit, no push, no deploy. |

---

## 1. Purpose and authority

This document is the **authoritative written record of the Product Owner's
decisions P-1 and P-2** for CT-MP-SUB-004, issued on **2026-10-05**.

The decisions were issued **explicitly by the Product Owner**. This record does
not create, extend, reinterpret or narrow them; it records them with their
rationale, their consequences, and their implications for independent
verification.

The decisions were prepared by the fact-finding task
`CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01`, which closed with
*"FACT-FINDING COMPLETE — READY FOR PO DECISIONS"* and posed exactly two
questions. Those questions are now answered.

Where this record and any other document appear to conflict, **this record and
the PO decisions it contains are authoritative**, and the conflicting document is
to be treated as stale (AGENTS.md §2 source-of-truth hierarchy: ratified PO
decisions outrank historical audit reports).

### 1.1 What these two items are (and are not)

**`NV-9` and `NV-10` are not product requirements.** They are entries **9** and
**10** of the *"Explicit list of anything NOT verified"* table in
`docs/architecture/CT-MP-SUB-004-independent-verification-report.md` §19 —
i.e. the independent verifier's own list of open verification gaps:

* `independent-verification-report.md:665` → `| NV-9 | Long-running/performance behaviour | Out of scope |`
* `independent-verification-report.md:666` → `| NV-10 | Email/notification side-effects | None expected from this surface |`

P-1 and P-2 therefore **close two verification gaps**. They do **not** authorise
two new features. This distinction is the whole substance of this record.

---

## 2. Decision summary

| # | Decision (topic) | **PO decision** | Governing evidence |
| --- | --- | --- | --- |
| **P-1** | Production performance SLO for Manual Processing coverage operations (NV-9) | **CLOSED — NO DEDICATED PRODUCTION PERFORMANCE SLO IS REQUIRED FOR THIS RELEASE** | Fact-finding §2 (no authoritative production SLO found; five artefacts record the absence) |
| **P-2** | Manual Processing proactive notifications on allocation / release (NV-10) | **CLOSED — PROACTIVE MANUAL PROCESSING NOTIFICATIONS ARE NOT REQUIRED FOR THIS RELEASE; ALLOCATION/RELEASE REMAIN AUDIT-ONLY** | Fact-finding §3–§4 (notification architecture exists; no MP producer; not required by D2) |

**Neither decision requires any code, schema, migration, RLS, fixture or
configuration change.** Both decisions describe the **already-implemented**
product state as the authorised state.

---

## 3. P-1 — Production Performance SLO

> ## **P-1 CLOSED**
> ## No dedicated production performance SLO is required for Manual Processing coverage operations for this release.

### 3.1 The decision

The Product Owner decides that **no production performance SLO is created for
the Manual Processing coverage operations in this release**, and that **no
production-scale performance claim may be made** for CT-MP-SUB-004.

### 3.2 Rationale (as established by the fact-finding report)

1. **No authoritative CarbonTally production SLO is currently ratified.** None
   exists anywhere in the repository, and its absence is explicitly recorded and
   PO-owned by five independent authoritative artefacts — including
   `CARBONTALLY_P8_I5_I8_PO_DECISION_AND_AUTHORIZATION_20260921.md:746`
   (*"SLOs NOT YET AUTHORIZED — PO/PRODUCT DECISION REQUIRED … No numerical SLO
   may be invented by Cline."*), the capability matrix gap **G-21** (*"No
   committed SLO"*, owner D-26 commercial / L8-A governance), and 8-X discovery
   **G10** (*"No availability/SLO definition — MISSING"*).
2. **The existing X7-D6 value (1,000 ms) is an observability threshold, not a
   production SLO.** It is the PO-supplied definition of *"slow"*, observed as
   **p95 over a rolling 60 minutes** (`backend/domain/api_metrics.py`:
   `SLOW_THRESHOLD_MS = 1000`, `WINDOW_SECONDS = 3600`). It carries no target,
   no budget, no per-endpoint bound and no consequence.
3. **The X1/X4 SLA values represent processing turnaround, not API performance
   SLO.** `queue_settings.sla_hours` (default 48) measures queue/workflow
   turnaround and is reported honestly as `not_configured` by default. It is a
   different dimension from request latency.
4. **The CT-MP-SUB-004 performance budgets are explicitly non-production
   engineering / Demo Lab budgets.** `tools/demo_lab/perf_mp_baseline.py`
   declares *local interactive budgets* (reads 500 ms p95, writes 750 ms p95)
   and states in its own docstring: *"NOT a production throughput/latency SLO.
   No production-scale SLO exists in the repository; if one is required it is a
   PO decision."*
5. **The Demo Lab cannot establish production p99, throughput, concurrency,
   capacity, topology or production-scale behaviour.** Twelve local iterations
   against a single-workstation stack cannot substantiate any production
   performance claim, and no load/capacity testing was performed or is proposed.
6. **Creating an MP-specific production SLO now would invent a platform policy
   that has not been ratified.** A production performance commitment is a
   commercial/operational policy that binds the whole platform, not one feature.
   Deciding it inside CT-MP-SUB-004 would pre-empt an unratified platform-level
   decision (capability matrix **G-21**, owner D-26 / L8-A).

### 3.3 What this decision does **not** do

* It does **not** repeal, replace or redefine the X7 observability threshold.
* It does **not** assert that CarbonTally needs no production SLO **ever**; it
  decides that no **MP-specific** SLO is required **for this release**.
* It does **not** authorise any new monitoring, metrics, alerting or SLO
  infrastructure.
* It does **not** change any existing performance threshold, budget or code.

### 3.4 Future platform-wide SLO policy

A platform-wide production performance SLO, if the PO later decides one is
required, is **outside this release**, is governed by the existing open item
**G-21 / D-26 (commercial) / L8-A (governance)**, and **does not block
CT-MP-SUB-004 acceptance**.

---

## 4. P-1 — authorised acceptance behaviour for NV-9

For CT-MP-SUB-004, the authoritative acceptance target for **NV-9** is now:

> **NV-9 — PO status: CLOSED**
>
> 1. The existing MP performance budgets
>    (`tools/demo_lab/perf_mp_baseline.py`, `BUDGETS`: reads 500 ms p95, writes
>    750 ms p95; `REQUIRED_INDEXES` = `uq_consultant_mp_allocations_active`,
>    `idx_consultant_mp_allocations_firm`, `idx_consultant_mp_allocations_org`)
>    **remain valid as engineering / verification budgets**.
> 2. Their **non-production disclaimer must remain explicit** in the tool and in
>    any report that cites the measurements.
> 3. The **required MP database indexes must remain present**.
> 4. Independent verification **may reproduce the local performance
>    measurements** (the recorded p50/p95 against the declared budgets).
> 5. **No production-scale capacity claim may be made** from Demo Lab
>    measurements.
> 6. **No production SLO compliance claim may be made.**
> 7. **No new production SLO or monitoring architecture is required** for
>    CT-MP-SUB-004.
> 8. Future platform-wide production SLO policy is **outside this release** and
>    **does not block** CT-MP-SUB-004 acceptance.

**Not authorised by P-1:** modifying the performance implementation; adding an
SLO; changing any existing performance threshold.

---

## 5. P-2 — Manual Processing proactive notifications

> ## **P-2 CLOSED**
> ## Manual Processing proactive notifications are NOT required for this release.
> ## Manual Processing allocation/release transitions remain audit-only.

### 5.1 The decision

The Product Owner decides that **Manual Processing allocation and release
transitions remain audit-only**, with **no proactive user-facing notification**,
for this release.

### 5.2 Rationale — CarbonTally already has an authoritative notification architecture

The fact-finding established that a complete, PO-ratified notification
subsystem already exists and is in use:

* **`public.notifications`** and **`public.notification_delivery`** tables
  (`supabase/migrations/00000000000000_init_schema.sql`) — the **D40**
  notification architecture;
* a **notification repository with idempotency** —
  `backend/data/notifications.py` (`create_idempotent`, `record_delivery`),
  backed by `notifications.event_key` + `uq_notifications_event_key`
  (`20260902050000_phase5_notification_event_key.sql`);
* **recipient resolution** (server-side only) — `support_staff_user_ids`,
  `internal_ops_user_ids`, `entity_participant_user_ids`, `email_for_user`;
* **delivery recording** — `notification_delivery` rows with status and error
  message;
* **existing email delivery / retry behaviour** —
  `backend/services/operational_alerting.py` (the **X2** operational alerting
  architecture: in-product + email, bounded retry, then `status='failed'`);
* the **D11 consultant-lifecycle notification decisions**
  (`backend/services/consultant_lifecycle.py`) with deterministic idempotent
  event keys and server-derived recipients.

### 5.3 Why that does **not** create an MP requirement

The same fact-finding established that the current Manual Processing
implementation:

* **emits Manual Processing audit events** — `manual_processing:allocation_created`
  and `manual_processing:allocation_released`
  (`backend/api/v3_manual_processing_coverage.py:350,408`;
  `backend/api/manual_processing_admin.py:761,804`);
* **does not emit notification events** — `grep 'notifications|create_idempotent|Notification'`
  over `manual_processing_admin.py`, `manual_processing_auth.py`,
  `data/manual_processing.py`, `domain/manual_processing.py` returns **no
  matches**;
* **has no notification producer** in the MP coverage implementation;
* **is not specified by the authoritative `CT-UX-MP-SUB-003` specification as
  requiring notifications** — that specification contains no notification, email
  or audit requirement.

Therefore:

> **The existence of a notification subsystem does not imply that every new
> Manual Processing transition must generate a notification.**

An agent must **not** invent such a requirement. The verifier's own note for
NV-10 recorded *"None expected from this surface."*

---

## 6. P-2 — authorised acceptance behaviour for NV-10

For CT-MP-SUB-004, the authoritative acceptance target for **NV-10** is now:

> **NV-10 — PO status: CLOSED**
>
> 1. **MP allocation remains audit-only.**
> 2. **MP release remains audit-only.**
> 3. **No default notification is required** when sponsored MP coverage is granted.
> 4. **No default notification is required** when sponsored MP coverage is withdrawn.
> 5. **No new MP notification event types** are authorised by this decision.
> 6. **No new recipient matrix** is authorised.
> 7. **No new notification preference system** is authorised.
> 8. **No new notification provider** is authorised.
> 9. **No new outbox/worker architecture** is authorised.
> 10. **Existing CarbonTally notification infrastructure remains unchanged.**
> 11. **Existing MP audit events remain the authoritative record** for these
>     transitions.
> 12. **The absence of MP notification rows for these transitions is acceptable
>     and expected.**

**Not authorised by P-2:** modifying notification code; adding notification
events, recipients, preferences, providers, outboxes or workers; or changing the
MP audit-event behaviour.

---

## 7. The four concepts that must stay distinct

The fact-finding warned explicitly against collapsing four different things.
This decision record preserves that separation, because the reason P-1 exists is
precisely that these concepts were being conflated.

| Concept | CarbonTally artefact | Is it a production SLO? | Status under P-1 |
| --- | --- | --- | --- |
| **Production SLO** | *(none exists — G-21 / D-26 / L8-A; P8 I5/I8 §746)* | — (absent by PO decision) | **Not created.** Platform-level, outside this release |
| **Observability threshold** | X7-D6 `SLOW_THRESHOLD_MS = 1000`, p95 over rolling 60 min (`backend/domain/api_metrics.py`) | **No** | **Unchanged.** Still an observability threshold only |
| **Processing-turnaround SLA** | X1/X4 `queue_settings.sla_hours` (default 48) | **No** — different dimension | **Unchanged.** Turnaround, not request latency |
| **Feature-local engineering / performance budget** | NV-9 `BUDGETS` (reads 500 ms, writes 750 ms p95) + `REQUIRED_INDEXES` in `tools/demo_lab/perf_mp_baseline.py` | **No** — explicitly non-production | **Retained as engineering/verification budgets only** |

None of the three existing mechanisms is promoted to, or renamed as, a
production SLO by this decision.

---

## 8. Authority and scope of this decision record

This document **records two PO decisions and nothing else.**

### 8.1 Explicitly NOT authorised by this task or this record

| Not authorised | Confirmed |
| --- | --- |
| Any **application implementation** (backend or frontend) | **NOT AUTHORISED** |
| Any **migration** (authoring, editing or applying) | **NOT AUTHORISED** |
| Any **production deployment** | **NOT AUTHORISED** |
| Creating a **production SLO** | **NOT CREATED** |
| Creating any **new notification behaviour** (event, recipient matrix, preference, provider, outbox, worker) | **NOT CREATED** |
| Any **schema, RLS, role or grant change** | **NOT AUTHORISED** |
| Any **Demo Lab fixture** change | **NOT AUTHORISED** |
| Any **test** change | **NOT AUTHORISED** |
| Any **performance-budget / threshold** change | **NOT AUTHORISED** |

Stated explicitly, in the required terms:

* **No application implementation is authorised by this task.**
* **No migration is authorised by this task.**
* **No production deployment is authorised by this task.**
* **No production SLO is created.**
* **No new notification behaviour is created.**

### 8.2 What this task actually did

**Documentation / governance only.** It created this decision record and its
companion report, and updated the *governance/acceptance-status references* of
the production-readiness report so that P-1/P-2 are no longer read as open
blockers. **No application behaviour, database, schema, migration, RLS, fixture,
test or production state was changed.**

---

## 9. Relationship to the existing production-readiness decisions

### 9.1 Previously closed decisions are **not** reopened

This record does **not** reopen or alter:

`F-1`, `F-2`, `F-3`, `F-5`, `F-6`, `F-8`, `F-10`, `NV-1`, `NV-2`, `NV-3`,
`NV-4`, `NV-7`, `NV-8`, `N-1`, `N-2`.

The decisions already made for `F-4`, `F-7`, `F-9`, `F-11`, `NV-5`, `NV-6`
remain part of the independent verification target established by
`CT-MP-SUB-004-PROD-READINESS-01` and are **unchanged**.

### 9.2 NV-7 is explicitly preserved

> **NV-7 remains: NOT REQUIRED — PO CLOSED**
>
> No pixel-perfect D2 comparison is required. **No visual pixel-comparison
> tooling is added.**

### 9.3 Relationship to the fact-finding and verification documents

| Document | Relationship |
| --- | --- |
| `CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01-report.md` | The **governing fact-finding**. Its findings are used, unchanged. Its closing status *"READY FOR PO DECISIONS"* is now **superseded** by this record for P-1/P-2. |
| `CT-MP-SUB-004-PROD-READINESS-01-report.md` | The implementation / self-verification report. Its **historical evidence is untouched**; only its governance/acceptance-status references are updated to point here. |
| `CT-MP-SUB-004-PO-decision-record.md` (`PD-1…PD-7`) | Unchanged and still authoritative for its own decisions. |
| `CT-MP-SUB-004-independent-verification-report.md` | Historical; **not amended**. Its §19 NV-9/NV-10 gaps are what P-1/P-2 close. |
| `CarbonTally_CT-UX-MP-SUB-003_Manual_Processing_ASCII_UIUX.md` (D2) | The authoritative UI/UX specification. Unchanged. It requires no MP notification. |

---

## 10. Instructions to the independent verifier (CoStrict / OHD)

The independent verifier must use **this document** as the **authoritative PO
decision source for P-1 and P-2**.

### 10.1 What the verifier must confirm for NV-9 (P-1 = no SLO required)

1. That **no production SLO was asserted, implied or fabricated** in the
   production-readiness report. In `tools/demo_lab/perf_mp_baseline.py` the
   docstring must **still** carry the *"NOT a production … SLO"* disclaimer.
2. That `tools/demo_lab/perf_mp_baseline.py` still runs green on a correctly
   restarted local stack, and that the recorded p50/p95 match the declared
   `BUDGETS` (`perf_mp_baseline.py:49–56`).
3. That the **required indexes** are still asserted and present:
   `uq_consultant_mp_allocations_active`, `idx_consultant_mp_allocations_firm`,
   `idx_consultant_mp_allocations_org`.
4. That local measurement remains **labelled non-production** wherever reported.
5. That the X7 observability threshold (`SLOW_THRESHOLD_MS`) was **not**
   redefined.

The verifier must **not** claim production SLO compliance, and must **not**
require any production SLO.

### 10.2 What the verifier must confirm for NV-10 (P-2 = audit-only)

1. `grep -rn 'notifications\|create_idempotent\|Notification' backend/api/manual_processing_admin.py backend/api/manual_processing_auth.py backend/data/manual_processing.py backend/domain/manual_processing.py`
   → **no matches** (audit-only preserved).
2. `pytest backend/tests/unit/api/test_ct_mp_sub_004_prod_readiness.py -k NV10`
   → **PASS**, still asserting: an audit action is written for
   allocate/release/admin-allocate **and** the notification row count is
   unchanged, and no response body claims a notification.
3. That a real `public.notifications` row is **not** created by an
   allocate/release against the live stack.
4. That **no new notification subsystem or provider** was introduced.

The verifier must **not** require implementation of proactive MP notifications.

### 10.3 Unchanged checks from the fact-finding report

The verifier should also re-run the CT-MP-SUB-004 targeted backend suite and the
frontend MP suite; re-confirm the **F-9 invariant** (0 duplicate active
`(firm, org)` pairs) and the fixture baseline (1 active allocation) on the live
local DB; and confirm the disclosed self-found regression in
`CT-MP-SUB-004-PROD-READINESS-01-report.md` §17
(`OrganizationsRepository.list_all` clobbered by the `get_many` edit, then
restored) is genuinely repaired — both `list_all` and `get_many` exist and are
correct in `backend/data/organizations.py`.

---

## 11. Final status

Both outstanding PO governance questions from
`CT-MP-SUB-004-PROD-READINESS-PO-FACTFIND-01` are now **closed**:

| # | Decision | Status |
| --- | --- | --- |
| **P-1** | Production performance SLO (NV-9) | **CLOSED — no dedicated production SLO required for this release** |
| **P-2** | Manual Processing proactive notifications (NV-10) | **CLOSED — not required; allocation/release remain audit-only** |

No application implementation, migration or deployment is authorised by this
record. No production SLO is created. No new notification behaviour is created.

> ## **P-1/P-2 PO DECISIONS CLOSED — READY FOR INDEPENDENT VERIFICATION**

This record does **not** grant production deployment authorization, production
migration authorization, or final CT-MP-SUB-004 acceptance. The next stage is
**independent verification by CoStrict/OHD**, which must use this document as the
authoritative PO decision source for P-1 and P-2.







