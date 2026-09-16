# CT-P8-B4-IMPLEMENTATION-20260913-035

**Task ID:** `CT-P8-B4-IMPLEMENTATION-20260913-035` (increment 1 — the ratified narrative/finalisation spine)
**Title:** Phase 8 Batch B4 — narrative overlay schema + narrative/finalisation domain model
**Date:** 2026-09-13
**Authorization:** PO blanket authorization `…050`; contract `CARBONTALLY_PHASE8_B4_IMPLEMENTATION_CONTRACT_20260913.md` §§7–8 (policy **ratified** by `A1`, `A3`, `P3`, `DM-5`, `DM-6`, `D15`)
**Environment:** `carbontally_qa_phase8` (non-production)

---

## 1. Scope delivered (increment 1)

| Deliverable | State |
|---|---|
| **A** `disclosure_narrative_entries` — requirement-bound narrative store (migration `20260918000000_p8_b4_narrative_overlay.sql`) | **IMPLEMENTED + APPLIED** |
| **B** narrative domain layer (`backend/domain/disclosure_narrative.py`) | **IMPLEMENTED + TESTED** |
| **C** the `DM-5` **finalisation gate** (pure evaluation) | **IMPLEMENTED + TESTED** |
| D drill-down exposure rule, E approval workflow, F frozen artefact, G retention, I RLS on remaining objects, J service/API plumbing | **PENDING** (E/F/G await `B4-D1…B4-D8`; D is a rule over the B3 read model + API exposure) |

## 2. What the schema enforces (ratified policy, no new decision)

* `requirement_version_id` **NOT NULL** and part of `UNIQUE (report_version_id, requirement_version_id, narrative_kind)` → **`A1`: narrative is requirement-bound; a report-wide narrative path does not exist.**
* `narrative_kind` closed vocabulary (3 values) → no generic rules engine (D4).
* `body` — **plain text, non-empty only**: **no character cap** (`A3`).
* `state` ∈ {`DRAFT`, `SUPERSEDED`} → authoring lifecycle only.
* No column, FK or trigger can reach `calculation_snapshots`, `emissions_logs`, `emission_factors`, `customer_factors` → **`P3` structurally honoured**.
* RLS enabled; `anon` revoked; **member read / Owner-Admin write** (`p8_disclosure_is_org_admin`); no PE policy; no `FORCE RLS`; no trigger; no retention artefact.

## 3. What the domain layer enforces (pure, test-locked)

* binding required (`A1`); plain-text-only, non-empty, **no length limit** (`A3`);
* authorship restricted to **Owner/Admin** (`A1`/`P3`);
* authoring **refused on `APPROVED`/`FINAL`** versions (`D15`);
* the **`DM-5` gate**: unresolved `REQUIRED` **blocks**; unresolved `CUSTOMER_INPUT_REQUIRED` **blocks**; applicable required `NOT_SUPPORTED` is **surfaced** (never blocking-hidden, never presented as satisfied); `NOT_APPLICABLE`/`UNDETERMINED` are informational;
* `assert_states_are_not_collapsed()` guards the DM-5 distinction (a forged collapse raises).

## 4. Verification (executed)

| Check | Command | Result |
|---|---|---|
| Migration apply | `psql -f …20260918000000…` | **rc=0** |
| Migration re-apply (idempotency) | same file again | **rc=0** |
| RLS + policies | live introspection | `rls=true`, **2 policies**, **5 indexes** |
| Blank body rejected (`A3` non-empty) | direct insert of `'   '` | **rejected** by `…_body_check` |
| No length cap (`A3`) | pure test with a 20,000-char body | **accepted** |
| B4 domain unit suite | `pytest tests/unit/domain/test_disclosure_narrative.py -q` | **14/14 PASS (EXIT=0)** |

**DM-5 behaviour proven:** all-resolved can finalise; unresolved `REQUIRED` blocks; `CUSTOMER_INPUT_REQUIRED` blocks and is reported separately; `NOT_SUPPORTED` **surfaces without blocking and is never listed as informational/satisfied**; `NOT_APPLICABLE`/`UNDETERMINED` do not block.

## 5. Defects

None found in this increment (no failure required a fix).

## 6. Repository state

| Item | Value |
|---|---|
| Branch / HEAD | `main` / `37b19d13723b0b1eabceeade86ce1615a98ab400` (unchanged) |
| Commits | none |
| Staged | 0 |
| New artefacts | the migration, the domain module, the unit suite, the contract, the `…034` report, this report |
| Applied to | `carbontally_qa_phase8` only (non-production) |

## 7. Verdict

### `B4 INCREMENT 1 COMPLETE — RATIFIED NARRATIVE/FINALISATION SPINE IMPLEMENTED AND VERIFIED; APPROVAL, FROZEN ARTEFACT AND RETENTION AWAIT PO DECISIONS`

---

# Increment 2 — `B4-D1` approval/finalisation transition (PO decision AMENDMENT 1)

## 8. Recorded decision (verbatim, no reinterpretation)

> **PO DECISION B4-D1 — Yes. Approve Option A.** Customer **Owner and Admin** may approve/finalise a customer report version. **Consultants and CarbonTally internal staff may never approve or finalise** a customer report version.

Recorded as contract **§23 Amendment 1**. Not reinterpreted as authority for consultants or internal staff.

## 9. Delivered

| Artefact | Lines | Purpose |
|---|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_B4_IMPLEMENTATION_CONTRACT_20260913.md` §23 | +30 | `B4-D1` recorded; `B4-D1` → DECIDED; authority scope stated |
| `backend/services/disclosure_finalisation.py` | 200 | `assess` (DM-5 preview), `approve`, `finalise`; B4-D1 role re-check; terminal-state refusal; atomic state guard |
| `backend/api/v3_disclosure.py` | +95 | `GET /reports/{report_id}/finalisation-check`, `POST …/approve`, `POST …/finalise` |
| `backend/tests/unit/api/test_v3_disclosure_finalisation_api.py` | 302 | 19 in-memory API tests (ALLOW/DENY/gate/conflict/invalid-transition) |
| `backend/tests/integration/test_disclosure_b4_finalisation_runtime.py` | 228 | 10 runtime tests on the QA database |

## 10. Enforcement (server-side — the UI is not a boundary)

1. **Authorization.** `_authorize_write` denies Processing-Entity staff and CarbonTally internal staff, then requires the organisation role ∈ {owner, admin}. Consultants (non-members) and members/viewers are denied. The service **re-checks** the role (`assert_author_role`) as defence in depth, so a future caller cannot bypass the API check.
2. **Lifecycle/immutability.** Every transition goes through the ratified S3 rule table (`resolve_transition`); invalid transitions raise; a **terminal** version is refused (`create a new version instead`); the DB `UPDATE … WHERE status = <expected>` makes a concurrent/stale caller return a conflict instead of clobbering state.
3. **DM-5 gate.** Finalisation evaluates the disclosure values first: unresolved `REQUIRED` and `CUSTOMER_INPUT_REQUIRED` **block**; required `NOT_SUPPORTED` **proceeds but is surfaced** in the response; the two conditions are never collapsed (guarded).

## 11. Verification (executed)

| Check | Result |
|---|---|
| Unit: B4 API suite | **19/19 PASS** |
| Unit: B3 API + B4/B3 domain suites (combined run) | **71/71 PASS (EXIT=0)** |
| Runtime: B4 finalisation suite (`carbontally_qa_phase8`) | **10/10 PASS (EXIT=0)** |
| Runtime proof of the gate | `assess` → `can_finalise=False`; `finalise` raised `FinalisationBlocked` and DB status stayed `APPROVED`; after resolving the required items, `finalise` → `FINAL`, and the `NOT_SUPPORTED` limitation was still reported |
| Runtime proof of B4-D1 | six role variants (`member`, `viewer`, `consultant`, `pe_staff`, `staff`, `None`) all refused by the service; DB status unchanged (`REVIEWED`) |
| RLS/privilege | `anon` has **no** SELECT on `disclosure_narrative_entries`; `relrowsecurity = true` |

## 12. Defects found and fixed during this increment

1. **Self-inflicted, caught by the tests (before any completion claim):** the first draft used the *narrative-authoring* guard (`assert_can_author`, which refuses `APPROVED`) as the finalisation precondition, so every legitimate finalisation was refused. Replaced with the lifecycle **terminal-state** rule (`is_terminal`); the narrative-authoring rule remains where it belongs (narrative writes).
2. **Test-fake fidelity:** the fake version row had to be a mapping (the repository materialises rows via `dict(row)`), and the admin fixture must be the existing `org_admin_user` factory (an ad-hoc user lacked `organization_id`/`is_org_member` and was — correctly — denied). Neither was an application defect.

## 13. Verdict

### `B4-D1 IMPLEMENTED, ENFORCED SERVER-SIDE, TESTED (ALLOW + DENY) AND RUNTIME-VERIFIED`

Still open: `B4-D2…D12` (next question raised: **`B4-D10`** S4/S5/S6/S7 allocation), including the frozen-artefact and retention deliverables.

## 14. Regression outcome (post-`B4-D1`)

| Suite | Result |
|---|---|
| `tests/unit/api` (whole suite) | **EXIT=0** (no failures) |
| `tests/unit/domain` (whole suite) | **EXIT=0** (no failures) |
| B1 boundary guard `test_b2_b3_b4_boundary_untouched` (amended, see below) | **PASS** |
| `tests/integration/test_disclosure_b4_finalisation_runtime.py` | **10/10 PASS** |
| B1 boundary + B4 runtime together | **11/11 PASS** |

### 14.1 One real regression, fixed by the established precedent (not by weakening)

Adding B4's `disclosure_narrative_entries` tripped the B1 namespace guard
`test_b2_b3_b4_boundary_untouched`, which asserts the **exact** set of
`disclosure%` tables. This is the *same* event that occurred when B3 added its
three intensity tables, and it was handled by the identical, already-documented
precedent (B2 contract §20.6 / F-B2-13 — **amended, never deleted**):

1. the permitted namespace now includes **exactly** the one B4 table
   (`disclosure_narrative_entries`) alongside the 11 B1 and 3 B3 tables;
2. the former blanket “no narrative/commentary table may exist” assertion — which
   cannot survive B4's authorised narrative store — was **re-scoped, not deleted**,
   into the two properties that still matter:
   * narrative storage exists in **exactly** the one ratified B4 table, and
   * **B1's own 11 tables carry no narrative/commentary column** (B1's namespace
     is not where B4 stores prose);
3. B1's other guards (no `line_number` capability, exact intensity-table set)
   are unchanged.

No security guard was weakened, and the B4 presence/intent tests live in the B4
runtime suite.

---

## 16. Next open decision raised

**`B4-D10` — S4/S5/S6/S7 batch allocation** (does B4 absorb S4 narrative + S5 frozen
artefact, and where do S6 frontend lifecycle UI and S7 regression/security tests live?).
Raised to the PO in the compact format; `B4-D2…D9`/`B4-D11`/`B4-D12` follow as they block.

---

# Increment 3 — `B4-D10` recorded + narrative API + `DM-6` exposure rule

## 17. Decision recorded

> **PO DECISION B4-D10 — Yes, Option A.** B4 absorbs **S4 (narrative)** and **S5 (frozen artefact)**; **S7 (regression/security verification) stays inside B4 and is included in gate V4**; B4 does **not** absorb **S6 (frontend lifecycle UI)**. S6 remains a separate Phase 8 / Phase 8-X backlog item built against the ratified B4 lifecycle APIs once the frozen-artefact model is settled.

Recorded as contract **§24 Amendment 2**, including the explicit statement that this is **not** a deferral of security/regression testing.

## 18. Delivered in this increment

| Artefact | Lines | Purpose |
|---|---|---|
| `backend/domain/disclosure_exposure.py` | 200 | The ratified **`DM-6`** drill-down matrix + fail-closed line projection |
| `backend/data/disclosure_narrative.py` | 120 | `disclosure_narrative_entries` repository (requirement-bound upsert) |
| `backend/services/disclosure_narrative.py` | 110 | Authoring rules `A1`/`A3`/`P3`/`D15` + binding verification |
| `backend/api/v3_disclosure.py` | +120 | `GET …/disclosure/narrative`, `PUT …/disclosure/narrative/{requirement_version_id}`; `DM-6` applied to the drill-down route |
| `backend/tests/unit/domain/test_disclosure_exposure.py` | 110 | `DM-6` matrix + redaction (pure) |
| `backend/tests/unit/api/test_v3_disclosure_narrative_api.py` | 298 | 20 in-memory tests (narrative ALLOW/DENY + drill-down per depth) |
| `backend/tests/integration/test_disclosure_b4_finalisation_runtime.py` | +75 | Runtime narrative proof (binding, replacement, refusal) |

## 19. What is now enforced

* **`DM-6` depth is a single tested matrix:** Owner/Admin `FULL`; Viewer and Member `CONTROLLED` (measurements visible, document/storage references removed); Consultant `BOUNDED` (structural fields only); Processing Entity, CarbonTally internal staff, unrecognised roles and cross-tenant `DENIED` (403, never a partial answer).
* **Redaction is fail-closed:** below `FULL` only allowlisted key families are returned, so a new upstream column is never exposed by default; removed fields are reported in `redacted_fields` so the UI can explain itself.
* **Narrative is requirement-bound and Owner/Admin-authored:** the binding requirement must belong to this report version's requirement set, the body must be non-empty plain text with **no length cap** (`A3`), a repeated write replaces the single entry for that binding, and an `APPROVED`/`FINAL` version refuses authoring (`D15`).

## 20. Verification (executed)

| Check | Result |
|---|---|
| Unit: `DM-6` matrix suite | **PASS (all cases)** |
| Unit: narrative API + finalisation API + B3 API + narrative domain | **87/87 PASS** |
| Runtime: B4 suite (`carbontally_qa_phase8`) incl. the new narrative test | **11/11 PASS** |
| Compile | all four new/changed modules compile |

## 21. Defects found and corrected (both caught by the new tests)

1. **My docstring over-claimed redaction.** The first implementation was a *denylist* (unknown columns passed through below `FULL`) while the module claimed nothing was exposed by default. Corrected to a **fail-closed allowlist**, so the claim and the behaviour now agree — verified by a test that inserts an unrecognised `future_sensitive_column`.
2. **Consultant drill-down expectation was wrong, and the code was right.** A non-member consultant is stopped by the **B3 organisation-member gate** *before* any `DM-6` decision. The `DM-6` `BOUNDED` projection is enforced and tested at the domain layer; the HTTP test now documents the unchanged B3 boundary and asserts the denial leaks no field names. B4 does **not** widen that boundary — consultant reach into client data is the consultant operating model (AGENTS.md §10–§11), not membership here. **Recorded as an observation for the playbook, not as a defect.**

## 22. Verdict

### `B4 INCREMENTS 1–3 COMPLETE AND VERIFIED; S4 (NARRATIVE) AND DM-6 DONE — S5 (FROZEN ARTEFACT) IS NOW IN SCOPE AND BLOCKED ONLY BY THE ARTEFACT-MODEL DECISIONS (B4-D5…D7/D8)`

---

# Increment 4 — `B4-D5`/`B4-D6`/`B4-D7` recorded + S5 frozen artefact implemented

## 23. Decision recorded

Contract **§25 Amendment 3**, verbatim: the frozen artefact is **mandatory** at finalisation; finalisation **fails** if the immutable PDF cannot be produced and stored; **private** Supabase Storage bucket `report-artifacts`; key `{organization_id}/{report_id}/{version_id}.pdf`; **short-lived signed URLs** only, after authorization; **append-only** `report_version_artifacts` with **exactly one** record per finalised version; **SHA-256**; key and hash **immutable**; immutability via the append-only record + the version's `FINAL` state; corrections create a **new version**; live-render retained for **DRAFT only**; **no** SHA-512, MD5 fallback, optional artefact, external storage or FINAL-without-artefact path.

## 24. Delivered

| Artefact | Lines | Purpose |
|---|---|---|
| `supabase/migrations/20260919000000_p8_b4_frozen_artefact.sql` | 120 | `report_version_artifacts` — the mandate expressed structurally |
| `backend/domain/report_artefact.py` | 135 | derived key, SHA-256, single bucket/content type, no-rewrite rule |
| `backend/data/report_artefacts.py` | 102 | append-only persistence (`delete()` **raises** by design) |
| `backend/services/report_artefact_storage.py` | 118 | private-bucket adapter + in-memory double for tests |
| `backend/services/disclosure_finalisation.py` | 336 | freeze **before** transition; `ArtefactRequired`; status/signed-URL methods |
| `backend/api/v3_disclosure.py` | 682 | producer + storage dependency; finalise wiring; artefact metadata + signed-URL routes |
| `backend/tests/unit/domain/test_report_artefact.py` | 129 | 24 pure tests |
| `backend/tests/unit/api/test_v3_disclosure_finalisation_api.py` | 516 | 31 tests incl. the mandate cases |
| `backend/tests/integration/test_disclosure_b4_finalisation_runtime.py` | 425 | 15 runtime tests incl. S5 |

### 24.1 How the mandate is made structural (not conventional)

* **Bucket:** `CHECK (storage_bucket = 'report-artifacts')` — no other bucket is representable.
* **Key:** `CHECK (object_key = organization_id::text || '/' || report_id::text || || report_version_id::text || '.pdf')` — the mandated layout is **derived**, so it cannot drift from the row. The Python layer derives it too (never accepts it).
* **One record:** `UNIQUE (report_version_id)`.
* **Hash:** `CHECK (content_sha256 ~ '^[0-9a-f]{64}$')` — SHA-256 only.
* **Append-only:** `GRANT SELECT, INSERT` only, **no UPDATE/DELETE grant and no such policy**; the repository has no update path and its `delete()` raises.
* **No-FINAL-without-artefact:** the service returns an artefact first and only then transitions; `pdf_producer is None` raises before anything else.

## 25. Verification (executed)

| Check | Result |
|---|---|
| Migration apply ×2 on `carbontally_qa_phase8` | **rc=0, rc=0** (idempotent) |
| Live introspection | table present · `rls=true` · **2 policies** · 4 indexes · 10 constraints · `anon SELECT=false` · `authenticated UPDATE=false` · `INSERT=true` · `DELETE=false` |
| Unit: artefact domain + finalisation API | **52/52 PASS** |
| Runtime: B4 suite (real DB) | **15/15 PASS** |
| Mandate proof (runtime) | without a producer: `ArtefactRequired`, version stayed `APPROVED`, **zero** artefact rows |
| Integrity proof (runtime) | row key = derived layout, bucket = `report-artifacts`, `content_sha256` = `sha256(payload)`, `byte_size` = payload length, object present exactly once; a changed render is **refused** |
| Draft safety | signed URL for a version with no artefact → refused (`A15` live-render path stays for drafts) |
| Append-only proof | `authenticated` lacks `UPDATE`/`DELETE`; `anon` lacks `SELECT` |

## 26. Defects found and corrected in this increment

1. **Migration SQL:** a single-quoted bucket name inside a single-quoted `COMMENT` broke parsing — rewritten with dollar-quoting (`$cmt$ … $cmt$`).
2. **Two of my own new tests were wrong, not the code:** a producer stub returned a *coroutine* instead of a *callable* (so the API correctly reported 503 rather than the intended 409), and a parametrized denial test passed `json=` to `GET`. Both fixed; the assertions now match the real contract.
3. **One legitimate behaviour change surfaced by an existing test:** `test_owner_can_finalise_once_required_is_resolved` failed because finalisation now requires the artefact — exactly what `B4-D5` mandates. Amended (never deleted, B2 §20.6 precedent) with a docstring stating the change and pointing at the dedicated mandate test that proves the refusal.

## 27. Verdict

### `B4-D5/D6/D7 (S5) IMPLEMENTED, STRUCTURALLY ENFORCED, TESTED AND RUNTIME-VERIFIED — NO FINAL WITHOUT A FROZEN ARTEFACT`

---

# Increment 5 — `B4-D8` recorded; `B4-D2`/`B4-D3`/`B4-D11`/`B4-D12` dispositioned and implemented

## 28. Decision recorded

Contract **§26 Amendment 4** (`B4-D8`, **retain indefinitely**): no deletion path, no invented duration, retention stays configurable/server-side in the N3 control plane later, future retention must never weaken auditability/evidence/traceability or `FINAL` immutability, **no** scheduled deletion job or expiry, and the append-only model from `B4-D5/D6/D7` is untouched.

Contract **§27 Amendment 5** records the dispositions below (also stating the one genuine open item).

## 29. What was implemented for the dispositioned items

| ID | Outcome | Implementation |
|---|---|---|
| `B4-D2` | **Settled by the ratified spine** (D15/DM-7/S3/B4-D5…D7) — no new policy | proven by tests: a corrected report creates version 2 while version 1's frozen artefact stays byte-identical and version 2 starts with no artefact; a changed render is refused |
| `B4-D3` | **Satisfied by S3** | DRAFT → approve is refused (409, no transition attempted) |
| `B4-D11` | **Applied per the recommendation** | reuse of the existing append-only `audit_trail` (**no new audit table**): `frozen_artefact.created` + `frozen_artefact.signed_url_issued`, payload = object key/hash/TTL and **never** the signed URL; `artefact_status` now reports `data_as_of` + `stale` with an explicit “never auto-invalidated” statement |
| `B4-D12` | **Out of scope for B4 — deliberately no code** | commercial gating is a commercial-policy decision; `usage_tracking.reports_generated` remains untouched (E31) |

## 30. Verification (executed)

| Check | Result |
|---|---|
| Unit: artefact domain + finalisation API | **52/52 PASS** |
| Runtime: B4 suite (real DB) | **18/18 PASS** |
| Audit proof | the `signed_url_issued` entry exists in `audit_trail` and **does not contain the signed URL** |
| Staleness proof | `stale=False` at freeze · after a value changes ⇒ `stale=True` while the version remains `FINAL` (never auto-invalidated) |
| New-version proof | version 1's artefact row (id, key, hash, produced_at) is unchanged after version 2 is created; version 2 has no artefact |
| Compile | service + API modules compile |

## 31. Verdict

### `B4-D8 CLOSED (RETAIN INDEFINITELY) · B4-D2/B4-D3/B4-D11/B4-D12 DISPOSITIONED — ONLY B4-D4/B4-D9 (COMMENTS VISIBILITY) REMAINS AS A GENUINE PO DECISION`

S7 security/regression verification continues (see §32 on consolidation); S6 stays outside B4; gate V4 closure and playbook reconciliation follow once `B4-D4`/`B4-D9` is answered.

## 32. S7 — consolidated B4 security/regression verification

S7 stays **inside** B4 (per `B4-D10`) and gate V4 cannot pass without it. The B4 surfaces and their proven boundaries:

| Surface | ALLOW | DENY (proven) |
|---|---|---|
| `GET …/disclosure` | org member | Processing-Entity staff · CarbonTally internal staff (403) |
| `GET …/disclosure/{value_id}/lines` (`DM-6`) | Owner/Admin = `FULL`; Member/Viewer = `CONTROLLED` (measurements only, no document/storage refs); Consultant = `BOUNDED` (structural only) | PE · internal staff · unknown role · cross-tenant (403, and no field names leaked) |
| `GET/PUT …/disclosure/narrative` | member read; **Owner/Admin** authoring | Member/Viewer/Consultant/PE/staff authoring (403, no write attempted); authoring on `APPROVED`/`FINAL` (409); requirement not in this report (409, `A1`); empty body / unknown kind (409) |
| `POST …/approve`, `POST …/finalise` | **Owner and Admin** (`B4-D1`) | Consultant · PE staff · CarbonTally internal staff · Member/Viewer (403, no transition attempted); invalid transition (409); concurrent state change (409); `DM-5` blocked (409) |
| `POST …/finalise` artefact mandate | freeze → store → record → `FINAL` | renderer failure · storage failure · missing producer (**503**, version stays `APPROVED`); existing artefact with a different hash (409, never rewritten) |
| `GET …/frozen-artefact`, `POST …/frozen-artefact/signed-url` | org member (metadata / short-lived URL) | PE staff · internal staff (403); no frozen artefact (404 — drafts use the live-render route, `A15`) |
| `report_version_artifacts` (RLS/privileges) | member `SELECT`; Owner/Admin `INSERT` | `anon` `SELECT`; `authenticated` `UPDATE`; `authenticated` `DELETE` (all false) · no UPDATE/DELETE policy exists |
| Audit | append-only `audit_trail` entries for artefact creation and download issuance | the signed URL is **never** written to the audit trail or logs |

Every DENY row above is asserted by an executed test (unit or runtime) — none is asserted only by inspection.
