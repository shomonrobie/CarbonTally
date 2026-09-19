# CT-STEP2-CARBONTALLY-REMAINING-ENGINEERING-HARDENING-070 — final consolidated report

```text
BRANCH          p8-release-reconciled
STARTING HEAD   38224d90ae1bf715b5239962a669fadaae9410b4   (F-039-1 closed, OHD-verified 069)
WORKSTREAMS     A F-064-1 · B F-064-2 · C effective adjudication · D Render OOM
                E entity routing · F backup/recovery · G regression · H this report
PRODUCTION      not deployed · not modified · no production data touched · no PO closure
SELF-VERIFIED   yes (implementation evidence only — NOT independent verification)
```

## 1. Starting repository state

```text
branch            p8-release-reconciled
HEAD              38224d9  (== origin at the start of the campaign)
tree              clean
migrations        75 files in supabase/migrations/
F-039-1           CLOSED: one adjudication lineage per bounded context (D-F039-1-J)
                  after independent verification 069; not regressed anywhere below
```

## 2. What the previous 070 attempt had already completed

Five workstreams were **implemented, tested and committed** before the attempt stopped:

```text
704a9b8  A  fix(p8/fs): F-064-1 — /history resolves the adjudication LINEAGE identity
fc0a885  B  fix(p8/fs): F-064-2 — a consumption failure is no longer indistinguishable
              from "no adjudication"
967ad0e  C  test(p8/fs): workstream C — effective-adjudication determinism verified;
              no code change required
653d5a3  D  fix(p8/fs): F-070-D — bounded OCR: one page at a time, no wasted render
437a6cf  E  fix(p8/fs): workstream E — entity routing: split the internal-staff and PE
              domains
```

## 3. What remained when this continuation started

```text
F  PARTIALLY IMPLEMENTED — tools/backup_recovery_drill.py existed (untracked) and had been
   executed successfully once; the manifest fields it printed were wrong (it read top-level
   `tables`/`total_rows` instead of the artifact's `counts`/`inventory`), the safety guard had
   no test, no documentation existed, the kept drill target database was still on the cluster,
   and nothing was committed.
G  NOT STARTED — no consolidated regression had been run for the campaign.
H  NOT STARTED — no final report existed (the previous response stopped mid-sentence).
   Also: all five workstream commits were UNPUSHED (origin was still 38224d9).
```

Continuation work (this session): finished F, ran G, wrote H, pushed everything.

## 4. A — F-064-1 `/history` contract

```text
STATUS  IMPLEMENTED — SELF-VERIFIED (commit 704a9b8)
```

Root cause (as independently found): the route resolved its `adjudication_id` parameter with
`repos.clarifications.get()`, which binds to the row `id` column, while the 055 schema makes
`id` and `adjudication_id` different values — so the value `/effective` publishes as
`adjudication.adjudication_id` returned 404 while a version row id returned 200.

Correction: the documented form is resolved first **as the lineage identity** in one
tenant-scoped history read; a version row identity is still accepted and mapped to its lineage
(existing callers keep working); either way the identifier is resolved inside the authorised
tenant AND the asserted bounded context, and the response always reports the canonical lineage
identity. No new identifier semantic was invented; authorization, tenant isolation, RLS and
consultant/client isolation are untouched.

Verification (re-executed in this session):

```text
unit     tests/unit/api/test_v3_activity_clarifications_api.py            59 passed
         (lineage-addressed contract; row-id compatibility; foreign-context refusal through
          BOTH forms; other-tenant refusal through both forms; unknown→404; malformed→422)
real DB  tests/integration/test_f039_1_adjudication_lifecycle_runtime.py   9 passed
         (4 versions addressed by the /effective-published lineage id; the SAME id still
          resolves after a further modification; row-id compatibility; unknown→404;
          malformed→422; other organisation 403; another tenant's member 404 on this lineage;
          ACTIVE consultant 200; ENDED grant 403; consultant granted only another client 403;
          unauthenticated 401)
```

## 5. B — F-064-2 consumption error semantics

```text
STATUS  IMPLEMENTED — SELF-VERIFIED (commit fc0a885)
```

The F1 consumption helper caught every exception, logged it and returned `None`, collapsing
"no adjudication applies" into "the consumption path is broken". It now returns an explicit
outcome (`_AdjudicationConsumption(result, failed, reason)`): a legitimate no-result keeps the
existing clarification diversion unchanged, a successful adjudication is consumed unchanged,
and a lookup/consumption **failure** is recorded in the job's persisted blocked reason
("adjudication consumption failed for '<activity>'; falling back to clarification") — no factor
is ever invented, exception text is not exposed (the traceback stays in the log), and no new
exception framework or external contract was introduced.

```text
unit  tests/unit/services/test_automatic_processing.py   42 passed
      (injected repository failure → blocked, nothing mapped, failure named and NOT reported
       as "clarification required", no internals in job state; a failing resolve_evidence
       never runs the clarified re-match; a legitimate no-adjudication job is unchanged; a
       successful consumption is unchanged)
```

## 6. C — effective adjudication deterministic selection

```text
STATUS  VERIFIED — NO CODE CHANGE REQUIRED (commit 967ad0e, tests only)
```

The effective read carries no `ORDER BY`/`LIMIT` **by design**, and ordering is explicitly NOT
a substitute for the invariant: the query's predicate set (`organization_id`,
`effective_context_key`, `activity_key`, `original_activity`, `is_current`) is exactly the
column list of the D-F039-1-J partial UNIQUE index, so the database cannot return two current
rows for one bounded context. Every other single-row read is backed by a unique key
(`activity_clarifications_pkey`, `…_replay_unique`, `…_current_unique`), and the two genuinely
multi-row reads already order explicitly (`history()` by version, `list_for_organization()` by
`created_at DESC LIMIT n`).

Evidence (tests only — no production behaviour changed):

```text
unit      tests/unit/data/test_activity_clarifications_repository.py       20 passed
          (single bounded statement, no ORDER BY/LIMIT; a drift guard asserts the shipped
           migration really declares the partial UNIQUE index on exactly those four columns;
           repeated reads return the same current row)
real DB   tests/integration/test_f039_1_adjudication_lifecycle_runtime.py
          (four UNIQUE indexes inspected with indisunique + exact definitions; a 3-version
           lineage; 25 consecutive effective reads return the same row/version; the
           consumption read agrees; the database reports exactly one current row)
```



## 7. D — Render OOM / memory remediation

```text
STATUS  IMPLEMENTED — SELF-VERIFIED (commit 653d5a3)
```

Reproduced locally and located exactly: `convert_from_bytes(pdf_bytes, dpi=300)` with no page
bounds makes pdf2image read poppler's entire multi-page stdout stream and parse every page
before returning. Measured peak RSS, fresh process per document:

```text
document         BEFORE                                  AFTER
1-page scan      +51 MiB (render)                        +51 MiB
6-page scan      +400 MiB  →  573 MiB peak               +1.6 MiB → 174 MiB peak
24-page scan     +1349 MiB → 1921 MiB peak               +3.4 MiB → 178 MiB peak
Tesseract absent renders everything, OCR fails, the whole allocation is discarded and every
                 retry repeats it                       → renders NOTHING (flat ~122 MiB,
                                                          0 MiB delta)
```

A **six-page** scanned PDF therefore crosses the 512 MiB container limit, and on the
production host all of it was wasted because the Tesseract binary was missing — exactly the
reported incident (first OOM 2026-09-17, last observed 2026-09-19, correlated with PDF OCR).

Remediation: one page rendered, OCR'd and released per call (same 300 DPI; identical OCR text
— 39/234/951 chars on the same documents); a cached one-off Tesseract probe that removes the
wasted render entirely when OCR is unavailable; an explicit configurable page budget
(`OCR_MAX_PAGES`, default 100); partial text preserved when a later page fails; `print` →
project logger; and the no-poppler pypdfium2/ONNX fallback (the path taken on hosts without
Tesseract) converted from a materialised list to a lazy generator rendering one page at a time.
OCR functionality was NOT removed and non-OCR PDF processing is unchanged.

```text
unit          tests/unit/engines/test_pdf_engine.py                  14 passed
integration   tests/integration/test_pdf_ocr_memory_runtime.py       10 passed
              (small / multi-page / 24-page / OCR-required / missing binary / failing
               recogniser / 10 repeated requests / 4 concurrent requests / fallback laziness
               and memory bound; the same suite FAILS 4/10 against the pre-fix code:
               "24-page OCR added 1330.1 MiB of peak RSS")
related       extraction/OCR unit+integration suites                90 passed
```

Limitations: no Tesseract binary exists in this environment (the recogniser is stubbed where a
working OCR host must be simulated; the render — the memory-critical part — runs for real), so
OCR *accuracy* is not verifiable here; `rapidocr_onnxruntime` is absent, so the ONNX

## 8. E — entity routing

```text
STATUS  IMPLEMENTED — SELF-VERIFIED for E-1/E-2 (commit 437a6cf)
        VERIFIED — NO CODE CHANGE REQUIRED for E-3/E-4
```

```text
E-1  real defect (frontend)   `/ops` and `/pe` both used the SAME `requireStaff` guard, and
                              `useActorRoles` collapsed actor_type 'staff' and 'entity_staff'
                              into one flag — while the server separates them:
                                /api/v3/me/context → 'staff' → /ops ; 'entity_staff' → /pe
                                api/pe_auth.py         → internal staff DENIED on /api/v3/pe/*
                                api/operations_auth.py → entity staff denied on ops surfaces
                              So each domain could open the other's shell, where every API
                              call answered 403 — the misroute the component's own header
                              calls a defect. Fix: `requireInternalStaff` /
                              `requireEntityStaff` guards (the union guard retained for a
                              genuine union), /ops and /pe wired to their own domain, and a
                              redirecting guard now returns the caller to the workspace the
                              SERVER assigns (the context destination) rather than the public
                              landing page.
E-2  real defect (evidence)   `_first_get_route` scanned `app.routes` for an `APIRoute`, but
                              the installed FastAPI stores included routers as lazy
                              `_IncludedRouter` wrappers, so TWO pre-existing boundary tests
                              failed VACUOUSLY ("expected a GET commercial (staff) route")
                              instead of proving anything. It now reads the app's own OpenAPI
                              document; both tests run for real and pass (consultant → 403 on
                              the commercial and PE surfaces).
E-3  verified, no change      `/admin` is a live, preserved surface served by the SEPARATE
                              legacy admin application through the root `vercel.json`
                              rewrites (`/admin`, `/admin/*` → `/admin/index.html`). No actor
                              destination in `/api/v3/me/context` is `/admin`; the V3 internal
                              control plane is `/ops` and customer organisation administration
                              is `/organization`. Adding a V3 `/admin` route would be a PO
                              decision, not a defect fix — not taken.
E-4  verified                 the API-level domain boundary is implemented (pe_auth /
                              operations_auth) and is now explicitly covered end to end.
```

```text
frontend  src/__tests__/entity-routing-guards.test.jsx  12 new (+6 existing) = 18 passed
          (PE staff admitted to /pe; internal staff redirected /pe → /ops; internal staff
           admitted to /ops; PE staff redirected /ops → /pe; customer → /home; consultant →
           /consultant; explicit fallback honoured; onboarding preserved; plus source-level
           guards that every /pe route requires entity staff, every /ops route requires
           internal staff, every /consultant route requires a consultant, and no route uses
           the coarse union guard)
          full frontend suite: 318 tests passed. The only failing SUITE is the CRA default
          src/App.test.js, which fails to LOAD ("Cannot find module 'react-router/dom'" inside
          node_modules) and fails IDENTICALLY with this change stashed — pre-existing,
          unrelated, not reclassified.
backend   tests/unit/api/test_p6_1b_membership_workspace_authorization.py 32 passed
          (the two repaired boundary tests plus 10 new cross-surface tests: internal staff
           denied on /api/v3/pe/me; entity staff reach their own /api/v3/pe/me with an
           entity-scoped role; entity staff denied on commercial and on the internal QC queue;
           a SUSPENDED entity has no PE workspace; a PE identity cannot name another entity;
           customer/consultant/unauthenticated refused on /pe (403/403/401); and a PE work
           read never returns another entity's work)
```


## 9. F — backup / recovery

```text
STATUS  database recovery VERIFIED locally · the shipped export artifact VERIFIED as an
        artifact (commit dc154e0, tool + tests + documentation)
        BLOCKED — ENVIRONMENT/ACCESS REQUIRED for the production half (see §17)
```

The project's own operations reference recorded "PROVEN RESTORE DRILL — NOT PERFORMED" and
"restore NOT implemented", so recoverability was unproven. A drill was created, run end to end
(exit 0) and documented; it touches DISPOSABLE databases only.

PHASE 1 — the project's OWN capability (`backend/backup`, the real `BackupService` run):

```text
artifact            155,456 bytes · ciphertext-only · AES-256-GCM · key-v1
members             140 (manifest + catalog + ddl + 135 per-table .copy)
checksums           138 verified after decryption
manifest counts     135 tables · 752 rows · 218 policies · 89 triggers · 55 functions
ddl capability      CREATE TABLE ✓ PK ✓ FK ✓ INDEX ✓ UNIQUE ✓ POLICY ✓
                    ENABLE ROW LEVEL SECURITY ✗   ← measured, not assumed
restore (D4)        NOT IMPLEMENTED (stated in backup/__init__.py)
```

PHASE 2 — actual recovery with the platform's native tooling (`pg_dump -Fc` → `pg_restore`
into a FRESH disposable database):

```text
pg_restore rc 0 · 0 errors · 0 missing tables of 135 · 0 row-count mismatches
index delta 0 (331) · constraint delta 0 (507) · policy delta 0 (218)
RLS-enabled tables 135 → 135 · storage.buckets 1 → 1 (bucket configuration restored)
```

PHASE 3 — state compatibility: 75 migrations, 74 applied, 1 already present, **0 failed**.
PHASE 4 — application compatibility: the real lifecycle suite returns **0** against the
reconstruction.

```text
new  tools/backup_recovery_drill.py                        (4-phase drill + disposal guard)
new  docs/operations/CARBONTALLY_BACKUP_RECOVERY_DRILL.md   (performed evidence + gaps)
new  backend/tests/unit/tools/test_backup_recovery_drill_guard.py        9 passed
```

Gaps recorded in the documentation (not hidden): no D4 restore; the artifact's DDL does not
enable RLS; storage OBJECTS are covered by no mechanism found in the repository (only bucket
configuration is reproducible); RPO/RTO and scheduling are undefined; Supabase production
backup/PITR configuration is not verifiable from this environment (§17). No
disaster-recovery readiness claim is made.

## 10. Tests per workstream (all re-executed in this session)

```text
A  unit  api vouchers clarified reads/writes        tests/unit/api/test_v3_activity_clarifications_api.py   59
   integ lifecycle (real schema)                    tests/integration/…lifecycle_runtime.py                9
B  unit  consumption semantics                      tests/unit/services/test_automatic_processing.py       42
C  unit  repository determinism + drift guard       tests/unit/data/test_activity_clarifications_repository.py 20
   integ (shared with A, includes the determinism case)
D  unit  OCR bounds/fail-safe                       tests/unit/engines/test_pdf_engine.py                  14
   integ OCR memory/behaviour (real poppler)        tests/integration/test_pdf_ocr_memory_runtime.py       10
   related extraction/OCR suites                                                               90
E  frontend guards (incl. routing-table checks)     src/__tests__/entity-routing-guards.test.jsx           12
   frontend full suite (318 passed; 1 pre-existing suite-load failure)                        318
   backend cross-surface authorization               tests/unit/api/test_p6_1b_…authorization.py            32
F  drill disposal guard                             tests/unit/tools/test_backup_recovery_drill_guard.py    9
   drill execution (exit 0)                         tools/backup_recovery_drill.py (4 phases, see §9)
```

## 11. Consolidated regression (G)

```text
focused (A–F suites above, one run)                 176 passed · exit 0
integration (real PostgreSQL, fully-migrated DB)     28 passed · exit 0
   lifecycle 9 + concurrency 9 + OCR-memory 10
RLS / tenancy harness (F-063-1, real PostgreSQL)    28/28 PASS · RESIDUE_FREE (exit 0)
frontend suite (jest)                              318 passed · 1 pre-existing suite-load failure
BROAD REGRESSION — tests/unit, pytest 9.1.1 / Python 3.14.4
  baseline of record (067, HEAD 38224d9)           6 failed · 2734 passed · 2 skipped · 2742 collected
  this campaign (HEAD dc154e0)                     4 failed · 2766 passed · 1 skipped · 2770 collected
  failure-set delta                                EXACTLY 2 REMOVED · 0 ADDED
    removed: tests/unit/api/test_p6_1b_…::test_consultant_cannot_reach_operations_surface
             tests/unit/api/test_p6_1b_…::test_consultant_cannot_reach_pe_surface
             (repaired by workstream E: their assertions now run against real routes)
  remaining pre-existing failures (unchanged, not reclassified):
    tests/unit/api/test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained
    tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered
    tests/unit/api/test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered
    tests/unit/data/test_d17_provider_ownership_migration_revision.py::
        TestRevisionScope::test_migration_ordering_is_unchanged   (hard-coded count pin)
  movement explained: +32 passed = the campaign's new tests (E 10 backend + F 9 + A 4 + B 4 +
    D 8 … — surface moved between files, see §10); -1 skipped = the sandbox `.git`-dependent
    skip recorded in 067 (a real checkout has git history).
```


## 12. Security / RLS / authorization impact

```text
RLS                       unchanged in behaviour: the F-063-1 harness is 28/28 with zero
                          residue on a fully-migrated disposable database. The only schema
                          addition in this campaign was the F-039-1-J uniqueness index
                          (067 window), which adds no policy, grant or privilege.
tenant isolation          unchanged; F-064-1's correction resolves the identifier inside the
                          authorised tenant AND the bounded context for BOTH addressing forms,
                          and refuses other tenants through both (tested).
consultant/client         unchanged (ACTIVE grant 200; ENDED grant 403; a consultant granted
                          only another client 403; another tenant's member 404 on this lineage).
PE / internal separation  STRENGTHENED in the UI (E-1) to match the server: the PE domain and
                          the internal-staff domain no longer admit each other's workspace;
                          10 new cross-surface API assertions (403/403/401 and cross-entity
                          invisibility) make the boundary evidence explicit.
authorization code        not weakened anywhere: no guard removed, no check relaxed, no RLS
                          bypass introduced, no service-role escape added.
```

## 13. Database / migration impact

```text
new migrations            0 in this campaign (the F-039-1-J index migration belongs to the
                          067 window and is already merged)
migration set             75 files; reproducible on a disposable database: 67 applied on a
                          template copy + 1 environment-privilege failure
                          (`20260823000000_… permission denied for table buckets`, a local
                          cluster storage-schema ownership artefact, not an app-schema gap)
data changes              none anywhere outside disposable test/clone databases
production                not contacted, not modified, no restore performed over it
```

## 14. Memory / performance observations

```text
OCR peak RSS (the campaign's only memory work):
  1 page   +51 MiB → unchanged (one page is the floor)
  6 pages  +400 MiB → +1.6 MiB          (573 MiB peak → 174 MiB peak)
  24 pages +1349 MiB → +3.4 MiB         (1921 MiB peak → 178 MiB peak)
  Tesseract absent: full render + discard → NOTHING rendered (flat ~122 MiB)
  10 sequential requests and 4 concurrent requests: bounded (no accumulation)
runtime cost: one extra page-count read per OCR pass (negligible) and one poppler invocation
  per page instead of one for the whole document (slightly more process starts, far less
  memory); the Tesseract probe is cached for the process lifetime.
```

## 15. Files changed (this campaign, by workstream)

```text
A  backend/api/v3_activity_clarifications.py
   backend/tests/unit/api/test_v3_activity_clarifications_api.py
   backend/tests/integration/test_f039_1_adjudication_lifecycle_runtime.py
B  backend/services/automatic_processing.py
   backend/tests/unit/services/test_automatic_processing.py
C  backend/tests/unit/data/test_activity_clarifications_repository.py
   backend/tests/integration/test_f039_1_adjudication_lifecycle_runtime.py  (shared)
D  backend/pdf_engine.py · backend/services/automatic_extraction.py
   backend/tests/unit/engines/test_pdf_engine.py
   backend/tests/integration/test_pdf_ocr_memory_runtime.py                 (new)
E  frontend/src/v3/components/RoleRoute.jsx · frontend/src/App.js
   frontend/src/__tests__/entity-routing-guards.test.jsx                   (new)
   backend/tests/unit/api/test_p6_1b_membership_workspace_authorization.py
F  tools/backup_recovery_drill.py                                          (new)
   docs/operations/CARBONTALLY_BACKUP_RECOVERY_DRILL.md                    (new)
   backend/tests/unit/tools/test_backup_recovery_drill_guard.py            (new)
   backend/tests/unit/tools/__init__.py                                    (new)
H  docs/cline/reports/CT-STEP2-REMAINING-ENGINEERING-HARDENING-070.md      (this report)
```

## 16. Git commits

```text
704a9b8  A  fix(p8/fs): F-064-1 — /history resolves the adjudication LINEAGE identity
fc0a885  B  fix(p8/fs): F-064-2 — a consumption failure is no longer indistinguishable from
              "no adjudication"
967ad0e  C  test(p8/fs): workstream C — effective-adjudication determinism verified; no code
              change required
653d5a3  D  fix(p8/fs): F-070-D — bounded OCR: one page at a time, no wasted render (Render OOM)
437a6cf  E  fix(p8/fs): workstream E — entity routing: split the internal-staff and PE domains
dc154e0  F  test(p8/fs): workstream F — backup/recovery: a PERFORMED recovery drill +
              documented gaps
<pending>   H  docs: final consolidated report (this file)
```


## 17. Remaining blockers

```text
BLOCKED — ENVIRONMENT/ACCESS REQUIRED  (backup/recovery, production half only)
  a. Supabase production backup/PITR configuration: enabled tier, retention window, PITR
     window and the last successful backup timestamp (dashboard / Management API).
  b. A restore rehearsal in a NON-production Supabase project from a real production backup,
     verified like §9 phase 2 (row counts + schema + RLS).
  c. The storage-object backup/versioning policy for the documents bucket plus one sampled
     object restored and byte-compared.
  d. An agreed RPO/RTO and the schedule that delivers it (an operational decision).
  e. A named operator and a rehearsed procedure covering (a)–(d).
  The local drill cannot substitute for any of these, and no claim is made about production.
```

## 18. Remaining non-blocking findings (recorded, not fixed)

```text
1. F-064-2's sibling: the mapping stage still embeds a raw exception string in a persisted
   reason ("line N: matching failed (<exc>)"). It is explicit (never masquerades as
   "no adjudication"), so it was left alone — worth a separate later change.
2. The backup artifact's DDL does not enable RLS, and restore (D4) is unimplemented; a restore
   implementation would have to install policies/triggers/functions from catalog.json.
3. Storage-object backup is unimplemented at the product level (see §9/§17).
4. `src/App.test.js` (CRA default) cannot load in this environment: `Cannot find module
   'react-router/dom'` inside node_modules — pre-existing, proven unrelated (identical with
   the change stashed); the codebase convention is to stub router primitives in tests.
5. The D17 migration-count pin (hard-coded 71) still fails and now reports 75 — the same
   pre-existing failure class, the count moved by migrations that predate this campaign.
6. The disposable `carbontally_test` template is stale relative to the migration set (it lacked
   e.g. 20260906100000 consultant permissions); rebuilding it from migrations would remove a
   class of confusing fixture errors.
```

## 19./20. Final repository HEAD and push status

```text
branch            p8-release-reconciled
HEAD / origin     recorded in the git-state block appended below
push status       recorded in the git-state block appended below
git status        clean (apart from the report commit itself)
secrets           none introduced: no key, token, JWT, signed URL or credential in any diff;
                  the backup drill generates a throwaway encryption key at runtime only
```

## FINAL CAMPAIGN STATUS

```text
READY FOR INDEPENDENT VERIFICATION

A  IMPLEMENTED — SELF-VERIFIED
B  IMPLEMENTED — SELF-VERIFIED
C  VERIFIED — NO CODE CHANGE REQUIRED
D  IMPLEMENTED — SELF-VERIFIED
E  IMPLEMENTED — SELF-VERIFIED (E-1/E-2) · VERIFIED — NO CODE CHANGE REQUIRED (E-3/E-4)
F  database recovery VERIFIED and the export artifact VERIFIED locally; the production half is
   BLOCKED — ENVIRONMENT/ACCESS REQUIRED (§17) — an outcome the workstream's own scope
   explicitly allows, reported rather than fabricated
G  regression complete: 2 pre-existing failures repaired, 0 added
H  this report
```

Not independently verified · nothing PO-closed · nothing deployed.

recogniser itself was not exercised (its renderer was). No production memory claim is made.
