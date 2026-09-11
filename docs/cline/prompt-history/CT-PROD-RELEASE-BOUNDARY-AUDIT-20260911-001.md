# CT-PROD-RELEASE-BOUNDARY-AUDIT-20260911-001

**Prompt Ref:** `CT-PROD-RELEASE-BOUNDARY-AUDIT-20260911-001` · **Date:** 2026-09-11
**Role:** read-only release-boundary auditor (no staging, commit, push, reset, clean, or file mutation)
**Repository:** CarbonTally · **Branch:** `main` · **HEAD confirmed:** `16391217103b98dcea520070c5a22c68f12fe607`
**Durable output:** `docs/architecture/CARBONTALLY_PRODUCTION_RELEASE_BOUNDARY_AUDIT_20260911.md`

## 1. Scope

Determine exactly which existing changes belong in the first CarbonTally production release
and which must stay outside it — read-only, addresses **P0-1 only** (no P0-2/3/4
implementation, no deploy, no Phase 7/8 work). Classify every change (R1 production
candidate, R2 test support, R3 E2E infra, R4 documentation, R5 generated, R6 secret,
R7 unrelated, R8 uncertain), trace the billing fix and the P6-2C/D/E/F runtime, establish
the migration/E2E/secret/deployment boundaries, and answer the four critical questions.
Deliver report + this history with verdict A / B / C.

## 2. Exact counts (and the 682 → 684 discrepancy, resolved)

| Metric | Value |
|---|---|
| `git status --porcelain` entries | **684** |
| untracked entries (`??`) | **246** |
| modified tracked (` M`) | **286** |
| deleted tracked (` D`) | **152** |
| untracked **files** (`git ls-files --others --exclude-standard`) | **1210** |
| staged | **0** |

The Production Readiness Audit measured 682; it is 684 because that audit **added two
documentation files** (readiness report + its history record). Nothing else changed.

## 3. Key findings

* **Billing fix (P0-2) present but uncommitted** — `backend/data/billing.py`:
  `- VALUES ($1, $2, to_char($2, 'YYYY-MM'), $3)` →
  `+ date_trunc('month', $2::timestamptz)::date, $3)`, with
  `backend/services/billing.py` (+117 lines: D6 entitlement gate/charge) as its dependency.
* **Phase-6 production runtime identified** — new: `backend/api/{pe_auth,processing_mode,
  v3_context,v3_health,v3_pe,audit_helpers}.py`, `backend/domain/processing_origin.py`,
  `backend/services/{ai_document_extraction,consultant_lifecycle,work_items}.py`; modified:
  14 API modules, 9 repositories, 4 domain modules, 3 services — including
  `backend/api/router.py`, which **mounts the new routers** (co-commit requirement).
* **17 new migrations** (all untracked, none applied) including
  `…phase5_work_item_assignments.sql` (PE workspace depends on it) and
  `…phase5_notification_event_key.sql` (D11 `event_key` depends on it); their **production
  application status is UNKNOWN — REQUIRES PO/DB VERIFICATION**.
* **Secrets provably excluded** — `git check-ignore` matches `e2e/environment/.env.e2e`,
  `e2e/environment/.env.personas` and `tests/e2e/.env.personas`; no secret-named entry in
  `git status` → **SECRET / SENSITIVE — EXCLUDE**.
* **152 tracked deletions** concentrated in agent tooling (`.windsurf/skills` 78,
  `.claude/skills` 78, `.agents/skills` 69) — a `git add -A` would silently delete them →
  P0 release risk.
* **~400 generated artifacts** (`output/**`, `screenshots/**`,
  `agent_swarm_v2_artifacts/screenshots/**`, `qa_harness/{evidence,reports}/**`) → R5, exclude.
* **E2E infrastructure** `e2e/environment/**` (74 files) + `tests/e2e/**` → R3: commit as
  reusable test content, never deploy (no production import path; outside the CRA build inputs).

## 4. Answers to the four critical questions

1. **Committable as-is? → NO** (mixed unrelated tooling, 152 deletions, ~400 artifacts).
2. **Billing fix in the release set? → YES** (`backend/data/billing.py`, uncommitted).
3. **Can the E2E environment leak into production? → NO** (ignore-proven secrets; separate
   trees; no runtime imports).
4. **Smallest safe release:** `backend/{api,data,domain,services}/**` +
   `supabase/migrations/**` (17, verified order) + `frontend/src/**` + `vercel.json` + durable
   `docs/**`, with tests/E2E/qa_harness committed as non-deployed content and everything else
   excluded.

## 5. Commands executed (all read-only)

`git rev-parse HEAD` · `git log --oneline -6` · `git status --porcelain=v1` (+ `cut`/`awk`/
`sort`/`uniq` aggregation) · `git ls-files --others --exclude-standard` ·
`git status --porcelain=v1 -- <paths>` · `git diff --stat` · `git diff -U2` ·
`git diff --cached --name-only` · `git check-ignore -v …`. **No mutating Git command ran.**

## 6. Files changed by this audit

Documentation only: the release-boundary audit report and this history record.
No code, schema, migration, RLS, role, capability, billing, fixture, harness, environment or
deployment configuration was modified.

## 7. Git status / safety confirmation

```
branch: main          HEAD: 16391217103b98dcea520070c5a22c68f12fe607
staged: 0             modified: 286   deleted: 152   untracked entries: 246
Repository modified by this audit: NO   (documentation files only)
Files staged: unchanged   Commit created: NO   Push performed: NO
Reset performed: NO       Clean performed: NO
Unrelated modifications preserved: YES
```

## 8. Verdict

**B — RELEASE BOUNDARY PARTIALLY IDENTIFIED / PO DECISIONS REQUIRED**

Release content (§11) and exclusion boundary (§12) are concrete. Three PO decisions remain
(§13): inclusion of `admin/src/**`, the intent of the 152 tracked deletions, and the
production application status of the 17 migrations. No verification, release, deployment or
production-readiness claim is made; P6-2F remains **NOT VERIFIED / NOT CLOSED**.
