# CT-PROD-SUPABASE-RECON-20260911-002

**Prompt Ref:** `CT-PROD-SUPABASE-RECON-20260911-002`
**Datetime:** 2026-09-11
**Response Ref:** `CT-PROD-SUPABASE-RECON-20260911-002-R1`
**Mode:** READ-ONLY production object-level reconciliation (active project)
**Repository:** CarbonTally · branch `main` · HEAD `daad396523ac693352cc2f4ebb7fc58814a9e60b`
**Primary artifact (updated):** `docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` → **PART 2**
**Final verdict:** `NOT READY — RECONCILIATION FOUND BLOCKERS`

---

## 1. Prompt (faithful summary of the full PO prompt)

The PO confirmed via the Supabase console that production (`CarbonTally` / `pvwiojoyaqywtydzcpbg` /
org `pfurlzwxdtvyljnahlnx`) was **paused for inactivity and has now been resumed and is healthy**. The
authorization was **one bounded operation only**: a **READ-ONLY object-level reconciliation of the
active production project against CarbonTally Release-1**. Prohibited: any write-capable credential
(explicitly `SUPABASE_SERVICE_KEY`); `supabase migration list --linked` if it creates a temporary login
role; every DDL/DML/GRANT/REVOKE; creating users, organisations, subscriptions, allowances or buckets;
uploading/deleting files; loading emission factors; modifying RLS, Auth or production configuration;
deploying Render/Vercel; commit; push. Required outputs: update the existing reconciliation report
**preserving prior evidence**, create this `-002` history record, answer Q1–Q10, emit one of three
mandated verdicts, and end with the exact 18-line no-change checklist. Explicit instruction: *"If only a
write-capable credential is available, STOP and report that a read-only credential is required."*

---

## 2. Files inspected

`supabase/.temp/linked-project.json`, `supabase/.temp/project-ref`, `supabase/.temp/pooler-url`,
`backend/supabase/.temp/project-ref`, root `.env.production`, `frontend/.env.production`,
`frontend/src/supabaseClient.js` (publishable-key source), `supabase/migrations/**` (all 53 — object
inventory, `CREATE TABLE`, `ADD COLUMN`, `ALTER TABLE`, `GRANT`/`REVOKE`, `to anon` scan), plus Git
metadata. Authorities: `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md`,
`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`,
`CARBONTALLY_PRODUCTION_DEPLOYMENT_READINESS_20260911.md`,
`CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md` (Part 1).

## 3. Commands run (all read-only)

```
git branch/rev-parse/log/status/status -sb/diff --cached
git ls-tree -r --name-only HEAD -- supabase/migrations            (53)
git show --name-only --diff-filter=A HEAD -- supabase/migrations  (17)
git log --oneline daad396…..HEAD -- supabase/migrations           (0)
getent hosts pvwiojoyaqywtydzcpbg.supabase.co | db.pvwiojoyaqywtydzcpbg.supabase.co |
             supabase.co | supabase.com | api.supabase.com | aws-0-eu-west-2.pooler.supabase.com
curl -sS -o /dev/null -w '%{http_code}' https://pvwiojoyaqywtydzcpbg.supabase.co/auth/v1/health
curl -sS -o /dev/null -w '%{http_code}' https://pvwiojoyaqywtydzcpbg.supabase.co/rest/v1/
env-var existence scan (SUPABASE_ACCESS_TOKEN, PGPASSWORD, PGHOST, SUPABASE_DB_* …)
ls -la ~/.supabase ; test -e ~/.supabase/access-token ; test -e ~/.pgpass ; test -e ~/.netrc
grep -rniE 'to +(anon|public)'      supabase/migrations/*.sql    (no policy/grant to anon)
grep -rniE '^\s*grant |^\s*revoke ' supabase/migrations/*.sql
grep -rliE 'create table( if not exists)? public\.<table>' …      (authoritative table names)
grep for ADD COLUMN targets in v3m9 / d21 / d22 / d27 / d33 / the 17 release-1 migrations
```

**Production API queries (HTTP GET only — PostgREST maps GET → SELECT):**

```
GET /auth/v1/health                                 (401 without key; 200 with publishable key)
GET /auth/v1/settings                                (public: providers / signup / autoconfirm)
GET /rest/v1/<table>?select=id&limit=1               (table-existence probe, ~60 tables)
GET /rest/v1/<table>?select=<column>&limit=1         (column-existence probe, ~60 columns)
GET /rest/v1/emission_factors?select=id&limit=1      (row exposure)
GET /rest/v1/emission_factors?select=id  (Prefer: count=exact, Range: 0-0)   (exact row count)
GET /storage/v1/bucket/documents · /storage/v1/object/list/documents         (bucket existence)
```

**No SQL was executed against production** (no DB session exists). `supabase migration list --linked`
was **not run** (it creates a temporary login role). **No write-verb HTTP request was issued.**

## 4. Production evidence (verbatim results)

```
reachability   pvwiojoyaqywtydzcpbg.supabase.co → 172.64.149.246 / 104.18.38.10
               /auth/v1/health (no key) 401 ; (with publishable key) 200
               {"version":"v2.196.0","name":"GoTrue","description":"GoTrue is a user registration..."}
openapi        GET /rest/v1/ → 401 "Only secret API keys can be used for this endpoint"
tables PRESENT organizations, organization_members, users, processing_entities, staff_profiles,
               staff_roles, consultant_profiles, consultant_firm_members, consultant_clients,
               customer_factors, issues, facilities, assets, suppliers, processing_assignments,
               manual_extraction_items, manual_extraction_batches, document_processing_queue,
               calculation_snapshots, emissions_logs, notifications, conversations, messages,
               domain_events, audit_trail, import_batches, emission_factors, factor_aliases,
               activity_categories, document_types
tables ABSENT  work_item_assignments (PGRST205; hint → 'public.processing_assignments'), vehicles,
               billing_plans, billing_commercial_config, billing_credit_ledger, billing_orders,
               billing_payment_records, billing_storage_usage, billing_idempotency_keys,
               consultant_custom_domains, consultant_senders, data_discovery_requests
cols ABSENT    all 35 release-1 probes → 42703, incl. manual_extraction_items.processing_origin /
               processing_entity_id / pe_qc_at / pe_qc_by / pe_reviewed_at / pe_reviewed_by /
               consultant_firm_id / processing_mode / consultant_provenance_at ;
               notifications.event_key / actor_domain ; conversations.conversation_kind / context /
               processing_entity_id ; messages.conversation_kind / context ;
               calculation_snapshots.performed_by ; document_processing_queue.automation_provider /
               automation_model / automation_model_version / automation_extracted_data ;
               consultant_clients.relationship_origin / engagement_* ;
               consultant_firm_members.can_extract/map/validate/calculate/submit/confirm_automation
cols ABSENT    organizations.white_label_enabled (d21) ; processing_assignments.entity_id and
 (pre-release-1) .manual_extraction_batch_id (d22) ; organizations.customer_type and
               consultant_clients.suspended_at/ended_at/lifecycle_updated_at (d27) ;
               calculation_snapshots.source_item_id/source_file/source_page and
               manual_extraction_items.file_id (d33) ; document_processing_queue.stage /
               attempt_count / locked_at / lock_token / max_attempts / pipeline_version /
               reprocess_count / source_item_id / extracted_data (v3m9)
cols PRESENT   14/14 positive controls — organizations.id/name/created_at, notifications.id/
 (controls)    created_at, manual_extraction_items.id/status, conversations.id, messages.id,
               calculation_snapshots.id, consultant_clients.id, assets.id, assets.organization_id,
               document_processing_queue.id, processing_assignments.id ; plus
               document_processing_queue.workflow_error_count / workflow_next_retry_at and
               emissions_logs.organization_id
factors        GET emission_factors → 200 WITH ROW DATA (anon);
               Prefer: count=exact → 206  content-range: 0-0/7049
anon isolation organizations / organization_members / notifications / conversations / usage_tracking /
               customer_subscriptions / manual_extraction_items / factor_aliases /
               activity_categories / document_types / suppliers / facilities → 200 []
storage        GET /storage/v1/bucket/documents      → 404 {"statusCode":"404",
                 "error":"Bucket not found","code":"NoSuchBucket"}
               GET /storage/v1/object/list/documents → 404 {"code":"NoSuchBucket"}
auth settings  email true ; google true ; anonymous_users false ; disable_signup false ;
               mailer_autoconfirm false ; saml_enabled false ; sms_provider twilio
```

## 5. Findings

1. **`DR-15` RESOLVED** — production is active and reachable.
2. **Production schema ≠ Release-1 (large delta).** Effective schema ≈ **migrations 1–21**; everything
   from `20260821000000` onward is unapplied (**≈32 of 53**), including **all 17 Release-1 migrations**
   (10 proven absent by direct probe; 7 index/trigger/function/vocabulary-only and unprobeable).
3. **D37 commercial/billing family absent** — `billing_plans`, `billing_commercial_config`,
   `billing_credit_ledger`, `billing_orders`, `billing_payment_records`, `billing_storage_usage`,
   `billing_idempotency_keys` → `/api/v3/commercial` and `/api/v3/billing` cannot function (new `DR-17`).
4. **`work_item_assignments` absent**, legacy `processing_assignments` present (new `DR-18`).
5. **`documents` storage bucket absent** (`NoSuchBucket`) → `DR-08` confirmed as a deployment blocker.
6. **Emission factors PRESENT — exactly 7 049 rows** → `DR-02` downgraded P0 → P2/P3 (residual is the
   repository packaging of the DEFRA source inside the excluded `output/**` tree).
7. **NEW SECURITY FINDING (`DR-16`): `emission_factors` is fully readable by the anonymous role**
   (all 7 049 rows) — a deviation from the repository model that grants nothing to `anon`. Whether RLS is
   *disabled* on that table (implying possible anonymous **write** capability) could not be determined
   read-only and was deliberately **not** probed with a write verb.
8. **Positive security signal:** every other probed tenant table returns zero rows to the anonymous role
   — row isolation is enforced.
9. **Auth verified (read-only):** email + Google enabled, anonymous users disabled, sign-up enabled,
   email confirmation required. Site URL / redirect URLs remain `REQUIRES CONSOLE VERIFICATION`.
10. **Recorded migration history remains `UNKNOWN`** (not exposed via PostgREST; no DB credential).


## 6. Decisions

* Used **only** the repository's **publishable (anon-class)** key — after proving via a repository-wide
  scan that **no migration grants anything to `anon`** — and used it **GET-only** (PostgREST maps GET to
  `SELECT`), so no statement capable of mutation was ever sent.
* **Refused** `SUPABASE_SERVICE_KEY` (write-capable, explicitly prohibited).
* **Refused** `supabase migration list --linked` (creates a temporary login role).
* **Refused** to probe write capability with a write-verb request, even to characterise `DR-16`.
* **Withdrew and re-ran** probes that had used non-authoritative names (`assets.org_id` →
  `organization_id`; `processing_assignments.processing_entity_id` → `entity_id`;
  `processing_assignments.assignee_user_id` → withdrawn; `organizations.white_label` →
  `white_label_enabled`; `domain_events.organization_id` → inconclusive), removing false diffs; and
  removed 4 non-diffs (`consultant_firms`, `entity_relationships`, `work_items`, `profiles`) because no
  repository migration creates them.
* Distinguished evidence classes: `42703` (Postgres-level, **definitive**) vs `PGRST205` (PostgREST
  cache-level) vs `NoSuchBucket` (Storage API).

## 7. Risks

* **A ~32-migration delta on a database with no rollback path** (`DR-13`) and unverified backup/PITR
  (`DR-10`) — the single largest risk of the next operation.
* **Anonymous read of the factor library** (`DR-16`) — the content is public reference data, but it
  implies `anon` may hold broader privileges; the RLS state of that table must be established.
* `PGRST205` table-absence findings are cache-level and should be re-confirmed against the catalog once
  DB access exists (column-level findings carry no such caveat).
* Reading `emission_factors` through PostgREST consumes production egress and does not reflect an
  intended public-data design — worth a product decision.

## 8. Stop-condition confirmation

**No stop condition was triggered in this operation.** Production was available, the target identity was
unambiguous, and a **provably read-only** access path (GET-only; publishable key; no `anon` grants in the
schema) was available, so the reconciliation proceeded. The prohibitions on the service key and on
`supabase migration list --linked` were honoured, and **no command of uncertain mutation safety was
executed**. Where a question required a write verb or a privileged credential, work **stopped and was
reported as `UNKNOWN`** rather than worked around.

## 9. Final verdict

> ## `NOT READY — RECONCILIATION FOUND BLOCKERS`

**Answers:** Q1 **yes, active & reachable**; Q2 **`UNKNOWN`** (recorded history unreadable);
Q3 **none of the 17 shown applied, 10 proven absent**; Q4 **no — large `DIFF`**; Q5 **`DIFF`/partial**
(tenant isolation holds; `emission_factors` anon-readable); Q6 **`UNKNOWN`** (and moot until the delta is
applied); Q7 **no bucket**; Q8 **yes — 7 049 factor rows present**; Q9 **resolve the ordered migration
delta, create the bucket, investigate the anonymous factor read, configure secrets/OCR/frontend build,
confirm backups and rehearse rollback**; Q10 **a next operation may be authorized — but it must be the
read-only history/RLS read followed by a separately authorized migration-preparation operation, not a
deployment.**

See **PART 2** of `docs/architecture/CARBONTALLY_PRODUCTION_SUPABASE_RECONCILIATION_20260911.md`
(Part 1 evidence preserved in full above it).

