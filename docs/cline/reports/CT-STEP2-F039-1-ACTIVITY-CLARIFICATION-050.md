# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-050

```text
1  BASELINE SHA  89211d40accba8b552d3c3457e88055abcb16a4e
2  FINAL SHA     recorded in the completion summary (HEAD == origin verified after push)
3  BRANCH        p8-release-reconciled (no reset / rebase / force-push / history rewrite)
4  HEAD==origin  verified after push (see summary)
5  GIT STATUS    clean at finish
6  FILES CHANGED
     supabase/migrations/20260929000000_p8_fs_activity_clarifications_fks.sql   (new)
     backend/tests/integration/verify_activity_clarifications_rls.py            (new)
     docs/cline/reports/CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-050.md           (new)
7  COMMITS       the report commit (see summary)
8  MIGRATION EXECUTION ENVIRONMENT — dedicated disposable `carbontally_test`
     (postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test), reached over loopback as
     superuser `postgres`. The project's own integration target (guarded by the F-046-1 invariant).
     NEVER production; NEVER the investor/demo database; nothing deployed.
```

## PART A — FOREIGN KEYS (F-049-1) — DONE AND RUNTIME-VERIFIED

**Discovery (not guessed).** `manual_extraction_items.id` = uuid PK, `manual_extraction_batches.id`
= uuid PK, `manual_extraction_batches.organization_id` = uuid; `manual_extraction_items` has **no**
`organization_id` (tenant is reached via `batch_id → manual_extraction_batches.organization_id`).
The clarification columns were `text`, so a foreign key was **structurally impossible** without a type
change — the "one-line FK follow-up" promised in 049 was therefore not sufficient. The blocker was
identified and fixed properly rather than forced.

**Follow-up migration** `20260929000000_p8_fs_activity_clarifications_fks.sql`:
* narrows `item_key` / `batch_key` text → uuid, guarded by an `information_schema` check (idempotent),
  and safe because the table was empty (0 rows) when it ran, so no value can fail the cast;
* adds `activity_clarifications_item_key_fkey → manual_extraction_items(id)` and
  `activity_clarifications_batch_key_fkey → manual_extraction_batches(id)`, both **`ON DELETE SET NULL`**,
  following the established convention (`calculation_snapshots.source_item_id`,
  `evidence_line_items.source_file_id`; `ON DELETE CASCADE` is reserved for `organization_id`):
  an adjudication *about* an item must survive the item's deletion, so the link is severed, not cascaded;
* adds the two parent indexes (`activity_clarifications_item_idx`, `activity_clarifications_batch_idx`).

**Runtime result (executed, then inspected):**
```text
FK MIGRATION APPLIED ✓ · RE-APPLIED cleanly (idempotent) ✓
FKs  : activity_clarifications_item_key_fkey  -> manual_extraction_items   (SET NULL)
       activity_clarifications_batch_key_fkey -> manual_extraction_batches (SET NULL)
       activity_clarifications_organization_id_fkey -> organizations (CASCADE, pre-existing)
key types: item_key uuid · batch_key uuid
invalid batch_key      -> PASS (foreign key violation)
invalid item_key       -> PASS (foreign key violation)
non-uuid text item_key -> PASS (InvalidTextRepresentationError — type now enforced)
cleanup: 0 rows left
```
**Honest limitation:** no `manual_extraction_batches` / `manual_extraction_items` rows exist in the
disposable database, so the *positive* reference exercised was a legally-NULL parent (FK-permitted).
A **non-null positive parent reference was NOT exercised** and is not claimed.

## PART B — RLS BEHAVIOURAL VERIFICATION — DONE, 27/27 PASS

Exercised against the **real PostgreSQL RLS engine** by role-playing actual identities
(`SET LOCAL ROLE authenticated|anon|service_role` + `set_config('request.jwt.claim.sub', …)`, matching
`auth.uid()`'s definition), never by calling the helpers directly. Isolated QA fixtures (labelled
`QA` / `qa:`) were created and **only those** deleted afterwards — cleanup verified: 0 clarification
rows and 0 QA users left; no truncate, reset or modification of existing data.

```text
member (org A)      own SELECT allow · INSERT allow · UPDATE allow · DELETE allow      PASS x4
member A -> B       SELECT 0 rows · INSERT RLS violation · UPDATE 0 · DELETE 0         PASS x4
                    org B row verified unmodified afterwards                           PASS
authorised consultant (granted client org A)
                    SELECT allow · INSERT denied · UPDATE denied · DELETE denied      PASS x4
unauthorised consultant (org B)
                    SELECT 0 rows · INSERT denied                                      PASS x2
consultant CLIENT (member of org B — the exact population a consultant client is)
                    own org SELECT allow · INSERT allow                                PASS x2
                    other org SELECT 0 · INSERT denied · UPDATE 0 · DELETE 0           PASS x4
anon                SELECT/INSERT/UPDATE/DELETE all permission-denied                  PASS x4
service_role        SELECT executes · INSERT succeeds (BYPASSRLS convention)            PASS x2
TOTAL 27/27 PASS
```
Verifier notes (no inflation): the `service_role` SELECT check asserts the statement executes and
returns a count (observed 0 on the re-run, the seed row having been deleted by an earlier scenario) —
it establishes *access*, not a specific row count. RLS **behaviour is now established**; this
supersedes 049, which could only assert enablement.

**Reproducible artefact:** `backend/tests/integration/verify_activity_clarifications_rls.py`
(not `test_`-prefixed, so pytest does not collect it). Re-run:

## PARTS C–G — REPOSITORY · API · ANTI-BYPASS · SEMANTICS · IDEMPOTENCY · 22 SERVICE REGRESSIONS

**NOT implemented in this window.** Per the stated priority order, Parts A and B were the bounded
portion: the security surface had to be behaviourally established *before* anything was built on it.
Parts C (repository), D (API), E (anti-bypass/semantic tests), F (idempotency tests beyond the
existing DB constraint) and G (the 22 service regressions) remain open, and **Part I is therefore
correctly skipped — D19 UI was NOT implemented**, its prerequisites not being met.

## TEST TOTALS (exact, only what actually ran)

No application (Python) code changed in this window — only one SQL migration and one standalone
verification script — so the regression suites were **not re-run**; prior recorded totals (services
264 · engines 340 · 041 16 · 043 13, etc.) are **carried forward, not re-measured**.
```text
RLS behavioural matrix (Part B)   27 passed · 0 failed · 0 skipped · 0 errors
FK migration runtime checks        5 passed · 0 failed
F-046-1 target guard               1 passed (correctly refused a forbidden target)
```

## STATUS, BLOCKERS, VERDICT

* **D19 UI:** NOT implemented (prerequisites unmet — correct per Part I).
* **Production / deployment:** production database NOT touched · nothing applied to production ·
  NOTHING DEPLOYED · no unrelated scope touched · no existing RLS weakened · no admin bypass added.
* **Remaining blockers:** F-049-3 repository · F-049-4 API · F-049-5 the 22 service regressions ·
  F-049-6 anti-bypass/semantic tests · F-049-7 non-null positive FK reference exercise.
* No independent verification performed; no PO closure claimed.

**VERDICT: PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

Gained this window: the parent relationships are now real, type-correct, idempotent foreign keys
(runtime-verified), and the tenant security model is **behaviourally proven** — 27/27 scenarios across
five actor types, including cross-organisation denial, consultant authorisation *and* denial,
consultant-client confinement and anon denial, against the real RLS engine, with a committed
reproducible harness. Not gained: repository, API, anti-bypass tests, the 22 service regressions, D19 UI.

```text
INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test \
  python backend/tests/integration/verify_activity_clarifications_rls.py
→ === RLS MATRIX: 27/27 PASS === (exit 0)
guard: pointed at ...:54322/postgres → "F-046-1: refusing non-disposable target 'postgres'"  ✓
```
