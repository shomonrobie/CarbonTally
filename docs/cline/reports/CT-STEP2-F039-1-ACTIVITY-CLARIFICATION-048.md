# CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-048

```text
1  BASELINE SHA  c721569e2ee4f5666bc0eb688909baa6df1adee4 (p8-release-reconciled; origin equal; clean tree)
2  FINAL SHA     recorded in the completion summary (commit + push; HEAD == origin; tree clean)
3  BRANCH        p8-release-reconciled (no reset/rebase/force-push)
4  GIT STATUS    CLEAN at finish; changed files in §25
```

## 5–6. AUTHORIZATION ARCHITECTURE DISCOVERED (PHASE A) — ACTOR → RELATIONSHIP → SCOPE → HELPER → ENFORCEMENT

```text
TENANT TABLES (verified in the migrations): public.organizations · organization_members ·
consultant_clients · consultant_firm_members · consultant_profiles

RLS HELPERS (all SECURITY DEFINER — REUSED, never re-implemented):
  public.is_org_member(p_org uuid)        customer users: membership of the organisation
  public.is_org_active / is_org_admin_or_owner(p_org uuid)
  public.is_org_consultant(p_org uuid)    AUTHORISED CONSULTANT access to a client organisation
  public.is_consultant_firm_member/manager/team_admin/revoker(p_firm uuid)
  public.is_entity_member / is_active_pe_member(p_entity uuid)   Processing Entity scope
  public.is_ops_messaging_staff()                                internal staff

FROZEN TENANT-TABLE POLICY MATRIX (20260803000000_rc2_rls.sql §3, generated there by a loop over
organisation-gated tables; reproduced by hand for each new table in 20260807070000_add_new_table_rls.sql):
  SELECT : is_org_member(organization_id) OR is_org_consultant(organization_id)
  INSERT : WITH CHECK (is_org_member(organization_id))
  UPDATE : USING + WITH CHECK (is_org_member(organization_id))
  DELETE : USING (is_org_member(organization_id))

ACTOR PATHS
  Customer user     → organization_members row → organization_id → is_org_member     → RLS
  Consultant        → consultant_clients grant → client org id   → is_org_consultant → RLS
  Consultant client → member of its OWN org    → organization_id → is_org_member     → RLS
  Internal staff    → API staff dependencies (require_staff / operations_auth / consultant_auth / pe_auth)
                      with service_role for backend writes
  Database layer    → explicit table privileges on this stack: service_role ALL; authenticated DML only
                      with TRUNCATE/TRIGGER/REFERENCES/MAINTAIN REVOKEd; anon nothing. RLS is the
                      authoritative boundary for authenticated access.
```

## 7–12. RLS HELPERS REUSED · POLICIES · SCHEMA · MIGRATION

```text
7  HELPERS REUSED: is_org_member(uuid) and is_org_consultant(uuid). No new helper or predicate vocabulary.
8  POLICIES CREATED (the four frozen tenant policies, matrix verbatim):
     activity_clarifications_tenant_select / _insert / _update / _delete
   ⇒ an organisation reaches only its own rows; a consultant only the client organisations
     is_org_consultant already authorises; a consultant client (member of its own organisation) only that
     organisation; unrelated authenticated actors and anon reach nothing; no service-role bypass is
     introduced and no existing RLS was weakened.
9  SCHEMA — CREATE TABLE IF NOT EXISTS public.activity_clarifications: id · activity_key · batch_key ·
   item_key · organization_id FK→organizations ON DELETE CASCADE · original_activity ·
   source_evidence_ref · clarification · clarification_type · policy_input · outcome_status ·
   selected_factor_id FK→emission_factors ON DELETE SET NULL · selected_factor_name · factor_set ·
   factor_source · reporting_year · unit · scope · eligible_group_count · eligible_groups jsonb ·
   actor_id · actor_scope · created_at · updated_at, plus
     UNIQUE (activity_key, original_activity, clarification)   ← idempotency constraint
     INDEX (organization_id, created_at DESC) · INDEX (activity_key)
   Original source evidence (original_activity / source_evidence_ref) is a separate column family from the
   user adjudication (clarification / clarification_type); extracted_data is never overwritten and no
   factor-library data is duplicated (only the selected factor id + provenance metadata).
10 MIGRATION: supabase/migrations/20260928000000_p8_activity_clarifications.sql — ordering follows the
   existing timestamp convention; idempotent (ENABLE RLS, GRANT re-application, DROP POLICY IF EXISTS).
   DELIBERATE DOCUMENTED LIMITATION: batch_key/item_key are text, not FKs, because the batch/item table
   names were not confirmed in this window — a one-line follow-up once confirmed.
11 MIGRATION EXECUTION ENVIRONMENT: NONE — not applied locally, in test, or in production; no disposable
   database was used and none is claimed.
12 MIGRATION VERIFICATION: **STATIC ONLY** — composed from the traced conventions and read back. It has
   NOT been executed, so table creation, constraints, indexes, RLS enablement and policy behaviour are
   UNVERIFIED. No RLS behaviour is claimed anywhere in this report.
```

## 13–23. REPOSITORY · API · SERVICE INTEGRATION · SAFETY · PROVENANCE · IDEMPOTENCY · UI · PARITY

```text
13 REPOSITORY   NOT implemented this window.
14 API          NOT implemented this window.
15 SERVICE INTEGRATION  UNCHANGED AND GREEN — the 045 family gate remains wired at the real mapping
   boundary (services 264 · engines 340 at this baseline); nothing in this window touched it.
16 LEGACY BYPASS  Still eliminated for the mapped path.
17 CALCULATION SAFETY  Unchanged — clarification-required rows remain unresolved with no factor id.
18 PROVENANCE   The new column family ENCODES the required separation (source evidence vs user adjudication
   vs policy input/outcome vs actor attribution), but nothing writes to it yet; at runtime provenance still
   lives in the job's unresolved mapping entry (046).
19 IDEMPOTENCY  Designed and enforced at the DATABASE layer by the UNIQUE constraint (one authoritative
   record per parent + original evidence + clarification). API-level retry/duplicate behaviour is part of
   the remaining work.
20 D19 UI       NOT implemented this window.
21 CONSULTANT CLIENT PARITY  Preserved by the policy matrix — the same table and the same four policies
   serve organisations and consultant clients; only the authorising relationship differs. Not regressed.
22 POSITIVE AUTHORIZATION TESTS  NOT added.
23 NEGATIVE ISOLATION TESTS  NOT added. The required negatives (org A→B read/write · consultant→
   unauthorised client read/write · client→other client · unrelated actor · unauthenticated) can only be
   meaningfully asserted once the migration is applied in a disposable environment.
```

## 24–33. TESTS, REGRESSIONS, DATA, DEPLOYMENT, REMAINING WORK

```text
24 SERVICE REGRESSION TESTS (F-047-2)  NOT added this window.
25 FILES CHANGED  supabase/migrations/20260928000000_p8_activity_clarifications.sql (NEW) ·
   docs/cline/reports/CT-STEP2-F039-1-ACTIVITY-CLARIFICATION-048.md
26 D-A REGRESSION   PASS (untouched)      27 D-FS REGRESSION  PASS (policy module unchanged)
28 039/040/041/043/045 REGRESSION  PASS — 041 clarification 16 · 043 trigger 13, unchanged and green
29 BROAD TEST TOTALS  services 264 · engines 340 · 041 16 · 043 13 · D-A 26 · D-A discovery 9 ·
   units 13/27/35 (confirmed at this baseline). The broadest aggregate was not completed this window, so
   no aggregate total is claimed.
30 FACTOR DATA CHANGES  NONE.   31 PRODUCTION MIGRATION  NONE.   32 DEPLOYMENT  NONE (P1 remains SHADOW).
33 REMAINING LIMITATIONS
   F-048-1 Apply and verify the migration in a DISPOSABLE database (table, indexes, constraints, RLS
     enablement, positive + negative policy behaviour). Nothing about the SQL is verified yet.
   F-048-2 Repository + API (options · clarify · decline) with server-side authorization reusing
     require_staff / operations_auth / consultant_auth / RLS, never trusting client-supplied factor
     metadata and recomputing the policy outcome server-side.
   F-048-3 D19 UI panel (clarification-required, semantic options, submit, decline, resulting state) with
     no factor ids exposed.
   F-048-4 F-047-2 service-level regression tests (22 items) + the negative isolation tests at both the
     application and database layers.
   F-048-5 Confirm the batch/item table names and bind batch_key/item_key as FKs.
```

## STATEMENTS

```text
· D-A NOT REOPENED · D-FS-1…6 NOT REOPENED · the 045 gate NOT modified · the withdrawn 044/045 attribution
  NOT revisited · no factor-data change · no production migration · no deployment · no existing RLS
  weakened · no new admin bypass
· INDEPENDENT VERIFICATION NOT PERFORMED by me · PRODUCTION VERIFICATION NOT CLAIMED · PO CLOSURE NOT CLAIMED
```

## FINAL VERDICT

**PARTIALLY IMPLEMENTED — SPECIFIC FOLLOW-UP REQUIRED**

The forensic gate this window required is complete and is the substantive result: the existing
authorization architecture is documented — membership, consultant, consultant-client, PE and internal staff
relationships; the SECURITY DEFINER helpers; and the frozen tenant-policy matrix — and it is demonstrably
sufficient to express the clarification capability without inventing anything, so the architecture is not
the blocker. On that basis the first-class migration was composed strictly on those conventions (tenant
policies reusing is_org_member/is_org_consultant, deny-by-default RLS, explicit grants and REVOKEs, a UNIQUE
idempotency constraint, and a column family separating source evidence from user adjudication).

It has not been executed anywhere, so none of its runtime behaviour is verified; and the repository, API,
D19 UI, service-level regression tests and negative isolation tests remain outstanding. The service half of
F-039-1 remains green and untouched.
