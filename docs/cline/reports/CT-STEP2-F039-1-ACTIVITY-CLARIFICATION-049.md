# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-049

```text
1  BASELINE SHA  d3491e2f8d1202133c2e246739ffd3af515ce037 (p8-release-reconciled; origin equal; clean tree)
2  FINAL SHA     recorded in the completion summary (HEAD == origin; tree clean)
3  BRANCH        p8-release-reconciled (no reset/rebase/force-push)
4  GIT STATUS    CLEAN at finish
5  FILES CHANGED  supabase/migrations/20260928000000_p8_fs_activity_clarifications.sql (text unchanged —
                 now RUNTIME-APPLIED in the disposable test DB) ·
                 docs/cline/reports/CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-049.md
6  COMMITS       this report commit (see completion summary)
7  MIGRATION EXECUTION ENVIRONMENT
   Dedicated disposable test database `carbontally_test`
   (postgresql://postgres:postgres@127.0.0.1:54426/carbontally_test) — the project's own integration target,
   guarded by the F-046-1 invariant in backend/tests/integration/conftest.py which REFUSES the main database
   and any qa/demo/investor/prod/live-named database.
   Probe evidence: CONNECTED ✓ · the test DB is a clone of the authoritative schema — present:
   organizations, emission_factors, manual_extraction_items, manual_extraction_batches; helpers present:
   is_org_member, is_org_consultant.
   NOT production. NOT the investor/demo database.
8  RUNTIME MIGRATION VERIFICATION RESULT — **APPLIED AND INSPECTED** (evidence, not inference)
     MIGRATION APPLIED ✓
     columns: 24 — id uuid · activity_key text · batch_key text · item_key text · organization_id uuid ·
       original_activity text · source_evidence_ref text · clarification text · clarification_type ·
       policy_input · outcome_status · selected_factor_id · selected_factor_name · factor_set ·
       factor_source · reporting_year · unit · scope · eligible_group_count · eligible_groups · actor_id ·
       actor_scope · created_at · updated_at
     rls_enabled: True
     policies: activity_clarifications_tenant_select (SELECT) · _insert (INSERT) · _update (UPDATE) ·
       _delete (DELETE)
     indexes: activity_clarifications_pkey · activity_clarifications_unique ·
       activity_clarifications_activity_idx · activity_clarifications_org_created_idx
   ⇒ DDL, RLS ENABLEMENT and the four tenant policies are RUNTIME-VERIFIED.
   NOT verified, NOT claimed: RLS *behaviour* per actor — authenticated tenant SELECT/INSERT/UPDATE/DELETE,
   cross-organisation denial, consultant grant/denial, consultant-client confinement, anon denial and
   service_role behaviour. Those need role-playing RLS assertions (SET ROLE + claims) that this window did
   not run.
9  RLS POSITIVE/NEGATIVE TEST RESULTS  NOT RUN (see §8). The predicates are the project's frozen tenant
   matrix verbatim: SELECT is_org_member(organization_id) OR is_org_consultant(organization_id);
   INSERT/UPDATE/DELETE USING/WITH CHECK is_org_member(organization_id).
10 REPOSITORY  NOT implemented this window (F-048-2).
11 API  NOT implemented this window (F-048-2).
12 SERVICE INTEGRATION  UNCHANGED AND GREEN — the 045 family gate remains wired at the real mapping
   boundary; nothing here touched it (services 264 · engines 340 at baseline).
13 D19 UI  NOT implemented this window (F-048-3).
14 CONSULTANT CLIENT PARITY  Preserved by the applied policy matrix (one table, one policy set; only the
   authorising relationship differs). Not regressed; the repository/API/UI layer still owes the same
   capability to consultants and consultant clients.
15 IDEMPOTENCY  Enforced at the database layer and now RUNTIME-PRESENT: UNIQUE(activity_key,
   original_activity, clarification) materialised as `activity_clarifications_unique`. API-level retry
   semantics remain part of F-048-2.
16 TEST TOTALS  services 264 · engines 340 · 041 clarification 16 · 043 trigger 13 · D-A policy 26 ·
   D-A discovery 9 · units 13/27/35. No test modified. The broadest aggregate was not completed in this
   window → no aggregate total claimed.
17 REMAINING BLOCKERS / DEFERRED
   F-049-1 (F-048-5 — NOW ANSWERED) Authoritative parents confirmed: `manual_extraction_items` (item) and
     `manual_extraction_batches` (batch); `emission_factors` is the factor table, `organizations` the tenant.
     The migration currently stores item_key/batch_key as TEXT and was applied/verified in that form; binding
     them as FKs is a ONE-LINE follow-up that must be applied and re-verified in the same disposable DB. It
     was deliberately not changed in-window so as not to invalidate the verification just performed.
   F-049-2 RLS behavioural verification (positive + negative, per actor) in the disposable DB.
   F-049-3 Repository + API (options · clarify · decline) reusing existing staff/tenant dependencies, with
     actor_id from the authenticated context and selected-factor metadata taken ONLY from the server-side
     policy result — never from client input.
   F-049-4 D19 UI panel (clarification-required · semantic options · submit · decline · resulting state;
     no factor ids).
   F-049-5 The 22 service-level regression tests (F-048-4) and the negative isolation tests.
```

## Why this window is still PARTIAL, honestly stated

The window's first mandate was runtime migration verification, and that was achieved: the migration executed
against the project's own disposable `carbontally_test` database and the resulting object was inspected —
table, 24 columns, RLS enabled, the four tenant policies, and the unique/index set. Answering F-048-5 came
out of the same forensic pass: the authoritative parents are `manual_extraction_items` /
`manual_extraction_batches`, so the FK binding is now a one-line change rather than an unknown.

What did NOT happen is the rest of the package — RLS behavioural testing per actor, the repository, the API,
the D19 UI panel and both test batches — so the feature still cannot be exercised end to end by a user, and
no RLS behaviour is claimed. Repository/API/UI code was deliberately not written without the ability to test
it: the same governance rule that made 048 stop applies to anything built on an as-yet unverified security
surface.

## STATEMENTS

```text
· D-A NOT REOPENED · D-FS-1…6 NOT REOPENED · the 045 gate NOT modified · the withdrawn 044/045 attribution
  NOT revisited · no factor-data change · no production migration · no production deployment · no deployment
  of any kind · no existing RLS weakened · no new admin bypass · no unrelated scope touched
· The migration was applied ONLY to the disposable test database named in §7 — never production, never the
  investor/demo database.
· INDEPENDENT VERIFICATION NOT PERFORMED by me · PRODUCTION VERIFICATION NOT CLAIMED · PO CLOSURE NOT CLAIMED
```

## VERDICT

**PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

Positive movement: the migration is no longer "composed but unverified" — it is applied and runtime-inspected
in a disposable database, with RLS enablement, the four tenant policies, the unique idempotency constraint
and the indexes confirmed present, and the authoritative parent tables identified for the FK follow-up.
Still missing: RLS behavioural verification, the repository, the API, the D19 UI and the
service-level/isolation test batches. No production system, factor data, existing RLS or unrelated scope was
touched.
