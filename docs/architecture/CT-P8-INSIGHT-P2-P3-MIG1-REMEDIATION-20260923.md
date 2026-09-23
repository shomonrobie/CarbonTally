# CarbonTally Insight — MIG-1 Remediation + P2 Catalogue-Pin Cleanup

Date: 2026-09-23
Repository: `/home/shomonrobie/ct_93d5cdd` · Branch: `p8-release-reconciled` · Remote: `github`

Verification type: **Cline remediation + fresh-chain verification — NOT independent
OHD verification.** No PO closure is claimed.

## 1. Authorization and scope

PO authorization (2026-09-23), strictly limited to: (a) MIG-1 migration sequencing
remediation; (b) the P2 catalogue-pin cleanup caused by the authorized P3 tool
expansion; (c) fresh-chain migration verification; (d) regression verification
that the remediation did not break P2/P3.

Not done: D17 pin, frontend DR-007, reviewer/SLA failures, limiter cleanup, RLS
design, supplier persistence, Scope 1/2/3 work, variance/attribution,
factor-history, L7, L8, billing, P12, deployment, unrelated docs, any new Insight
capability.

## 2. Starting git state

| Item | Value |
| --- | --- |
| Branch | `p8-release-reconciled` |
| HEAD (starting) | `804bda279f5bf35172d8a81eaf0ac29fd229ff11` |
| `github/p8-release-reconciled` | identical; `HEAD...remote` = `0 0` |
| Working tree | clean except pre-existing untracked PO/ChatGPT reference documents (not touched, not committed) |

## 3. MIG-1 root cause

The P3 migration was named `20260923000000_p8_insight_data_quality_reproducibility.sql`.
Lexicographic ordering therefore placed it **before**
`20261003000000_p8_i4_insight_interactions.sql` (which creates
`public.carbontally_insight_tool_calls`) and before
`20261006000000_p8_insight_temporal_comparison.sql` (the P2 widening it extends).
Consequences: a fresh chain failed on a missing relation, and the later-sorting
migrations re-narrowed the I3 tool CHECK from 10 back to 8 names.

A **second, previously unreported** aspect was found during this remediation: the
prefix `20260923000000` was already in use by a tracked pre-existing migration,
`20260923000000_p8_rls_4a1b_anon_default_privilege_hardening.sql`, so the P3 file
also created a duplicate-timestamp ordering ambiguity (tie broken only by the
filename suffix). Both aspects are resolved by the same correction.

## 4. Migration-order evidence

Repository evidence used to choose the order (not assumption):

* `ls supabase/migrations | sort | tail` → the latest migration in the whole
  repository is `20261006000000_p8_insight_temporal_comparison.sql`;
* the Phase 8 Insight chain is `20261001` (I1 persistence) → `20261002` (I2
  authorization) → `20261003` (I4 interactions, **creates the table**) →
  `20261005` (analytics: tool CHECK → 7, adds the 15th answer state) → `20261006`
  (P2: tool CHECK → 8);
* `grep` for `carbontally_insight_tool_calls` across all migrations returns only
  four files (I4, analytics, P2, P3) — **no later migration touches the
  constraint**, so no post-P3 re-narrowing source remains once P3 is last;
* `grep` for the old prefix found exactly one functional reference
  (`backend/tests/unit/api/test_p8_insight_data_quality.py`).

Therefore the correct position is **after `20261006000000`** — the next free
timestamp slot, `20261007000000`.

## 5. Exact remediation performed

1. `git mv .../20260923000000_p8_insight_data_quality_reproducibility.sql` →
   `.../20261007000000_p8_insight_data_quality_reproducibility.sql`. **No SQL
   statement changed** — only the filename.
2. Migration header comment updated to the new filename plus an ORDERING note.
3. `backend/tests/unit/api/test_p8_insight_data_quality.py`: migration-path
   reference updated (mechanical; the test still asserts the migration content).
4. `backend/tests/unit/api/test_p8_insight_temporal_comparison.py`: P2 catalogue
   pin `assert len(TOOL_REGISTRY) == 8` → **`== 10`**, with a docstring stating the
   authorized composition. The assertion remains an **exact** count (not `>=`, not
   "contains"), so an accidental addition or removal still fails.
5. Two further **ordering pins** surfaced by the rename and updated mechanically
   (see §11.1): the I1 successor allowlist gained the P3 entry, and the I2
   latest-migration pin now names the corrected P3 filename.

## 6. Why the chosen migration order is correct

* the target table is created by `20261003000000`, which now sorts **before** the
  P3 migration — the dependency exists when it is needed;
* P2's ordering is untouched (P2 remains at `20261006000000`);
* the final constraint is therefore computed last from the P3 file, giving
  **exactly the 10 authorized tools** and removing the re-narrowing path;
* the duplicate-prefix ambiguity with the RLS migration is removed;
* no other migration was renamed, reordered or rewritten and no new migration
  architecture was introduced — the smallest correction that makes the existing
  intended chain valid (a pure rename plus one comment).

## 7. Fresh-chain verification environment

* Disposable container `ct_remedy_pg_20260923`
  (`public.ecr.aws/supabase/postgres:17.6.1.159`, port 55434) — a
  Supabase-flavoured Postgres providing the `extensions` schema, Supabase roles
  and the `auth` schema. **Never the authoritative database**; created for this
  check and removed afterwards.
* Starting state: fresh `postgres` database with **zero** target relations
  present (verified: count = 0 for `carbontally_insight_tool_calls`,
  `carbontally_insight_interactions`, `carbontally_insight_conversations`).
* Method: every `supabase/migrations/*.sql` applied individually, in the
  repository's actual sorted (lexicographic) order, with `ON_ERROR_STOP=1`, one
  psql invocation per migration, exit code recorded per file.

## 8. Fresh-chain migration results

**81 migrations applied; 80 succeeded; 1 failed** (`/tmp/fresh_chain.log`).

| Migration | Result |
| --- | --- |
| `20261001000000_p8_i1_insight_persistence.sql` | OK |
| `20261002000000_p8_i2_insight_authorization.sql` | OK |
| `20261003000000_p8_i4_insight_interactions.sql` (creates the table) | OK |
| `20261005000000_p8_insight_discovery_aggregation_rate_limit.sql` | OK |
| `20261006000000_p8_insight_temporal_comparison.sql` (P2) | OK |
| **`20261007000000_p8_insight_data_quality_reproducibility.sql` (P3, corrected)** | **OK — no missing-relation error** |

The single failure is unrelated to Insight and to this remediation:
`20260823000000_d32_private_documents_storage.sql` →
`ERROR: relation "storage.buckets" does not exist` — a **Supabase Storage schema**
dependency supplied by the storage service rather than by the Postgres image
(environment artefact). It precedes all Insight migrations and did not block them.

## 9. Final I3 10-tool constraint verification

The production constraint expression was taken **from the database** and evaluated
against a probe set:

```text
tool-name constraint: 10 of 11 probe values accepted (expect 10 of 11)
```

All ten authorized names are accepted; `unratified_tool` is rejected. The
constrained list contains exactly 10 entries — the tool set was **not** broadened
beyond the authorized ten, and the pre-P2/P2 tools remain accepted. Idempotence:
re-applying the corrected P3 file returned exit 0 with exactly one constraint
present and both P3 names intact.

## 10. Final I4 15-state verification

```text
success, zero, no_data, not_authorized, insufficient_data, needs_clarification,
tool_failure, provider_unavailable, partial, rate_limited, refused, ungrounded,
invalid_input, error, multiple_matches
```

= the fourteen Master Spec §14 states plus `multiple_matches` (added by the
2026-09-22 analytics authorization) = **15 states, `multiple_matches` present**.
Nothing was added, removed or redefined (the P3 migration touches only the
tool-name constraint).

## 11. P2 catalogue-pin cleanup

`backend/tests/unit/api/test_p8_insight_temporal_comparison.py`, test
`test_the_catalogue_gained_exactly_one_tool`:

```text
- assert len(TOOL_REGISTRY) == 8
+ assert len(TOOL_REGISTRY) == 10
```

plus a docstring documenting the authorized composition. The assertion stays an
**exact** count — not weakened to `>=`, `>`, or a containment check — so it still
detects an accidental addition or removal. No P2 production logic, planner
behaviour, arithmetic, semantics or capability was touched.

### 11.1 Additional ordering pins surfaced by the authorized rename

Two **test-ordering pins of the same class** as the authorized catalogue pin were
invalidated by moving the P3 migration to its correct position, and were updated
mechanically (`/tmp/t2.log` records them failing before the update):

| File | Pin | Before → After |
| --- | --- | --- |
| `tests/unit/data/test_i1_insight_migration.py` | I1 successor allowlist | added the `20261007000000_p8_insight_data_quality_reproducibility.sql` entry (the established per-package convention recorded in that test's own docstring) |
| `tests/unit/data/test_i2_insight_authorization_contracts.py` | `names[-1] == <latest migration>` | `20261006000000_p8_insight_temporal_comparison.sql` → `20261007000000_p8_insight_data_quality_reproducibility.sql` |

**Scope note (flagged for PO/OHD):** these two updates go beyond the literal "P2
catalogue pin" wording. They were required to avoid introducing *new* failures from
an authorized rename — leaving them red would violate the §10 verdict conditions.
Both are pure ordering/catalogue reference updates with no behavioural assertion
weakened (the I2 test still asserts the `CREATE POLICY`/`DROP POLICY` counts and
its no-table/column/index/grant invariants; the I1 test still asserts the exact
successor list). No behavioural change appeared necessary, so the §6 STOP
condition was not triggered.


## 12. P2 test results

**79 tests: 79 passed, 0 failed** (previously 78 passed / 1 failed — the catalogue
pin). Arithmetic, zero-baseline, empty-period, grouping, boundary, tenant
isolation, provenance and rate-limit tests all unchanged and green.

## 13. P3 test results

**48 tests: 48 passed, 0 failed** (behaviour unchanged; only the migration-path
reference was updated).

## 14. Relevant regression results

The 13-file Insight regression set: **299 collected, 299 passed, 0 failed**
(previously 298 passed / 1 failed — the P2 catalogue pin). No new failure was
introduced and no unrelated failure was altered, re-pinned or hidden.

## 15. Remaining unrelated / pre-existing failures

| Item | Status | Assessment |
| --- | --- | --- |
| `test_d17_provider_ownership_migration_revision.py` — `assert 81 == 71` | **unchanged pre-existing** (81 files before and after; a rename does not change the count) | D-29 stale migration-count pin; explicitly out of scope |
| frontend `dr007-investor-display-fixes.test.jsx` | **unchanged pre-existing** | not touched (no frontend change here) |
| reviewer/SLA, factor-metadata, limiter, RLS-design items | **not touched** | explicitly out of scope |

## 16. Files changed

| File | Change |
| --- | --- |
| `supabase/migrations/20261007000000_p8_insight_data_quality_reproducibility.sql` | **renamed** from `20260923000000_…` (no SQL statement changed) + header ORDERING note |
| `backend/tests/unit/api/test_p8_insight_data_quality.py` | migration-path reference (1 line) |
| `backend/tests/unit/api/test_p8_insight_temporal_comparison.py` | catalogue pin 8 → 10 + docstring |
| `backend/tests/unit/data/test_i1_insight_migration.py` | successor allowlist entry |
| `backend/tests/unit/data/test_i2_insight_authorization_contracts.py` | latest-migration pin + comment |
| `docs/architecture/CT-P8-INSIGHT-P2-P3-MIG1-REMEDIATION-20260923.md` | this report |

`git diff --stat`: **5 files changed, 35 insertions, 7 deletions** (plus this new
report) — **no production code path appears in the diff**, so P2/P3 runtime
behaviour is untouched by construction.

## 17. Commit SHA

The remediation commit (`fix(p8): MIG-1 migration sequencing remediation + P2
catalogue-pin cleanup`); SHA recorded in §18 with the push result.

## 18. Push / alignment status

* Starting HEAD: `804bda2` (aligned `0 0`).
* Push target: `github/p8-release-reconciled`.
* Final local HEAD and remote HEAD verified identical, with
  `git rev-list --left-right --count HEAD...github/p8-release-reconciled` = `0 0`.
* Working tree clean except the known pre-existing untracked PO/ChatGPT reference
  documents (never staged).
* The disposable verification container was removed.

## 19. No P2/P3 production behaviour changed

**No P2 or P3 production behaviour was intentionally — or unintentionally —
changed by this remediation.** The diff contains no file under
`backend/services/`, `backend/domain/`, `backend/api/`, `frontend/`, and the
migration's SQL body is byte-identical. Specifically untouched: P2
comparison/arithmetic, zero-baseline, empty-period and grouping semantics, P2
tenant isolation and provenance; P3 quality and reproducibility rules,
honesty/limitation semantics, tenant isolation, provenance and rate limiting. The
only behavioural-surface change is the I3 CHECK constraint's *permitted tool set*,
which is unchanged in substance (10 authorized tools before and after) — only its
**ordering position** was corrected so a fresh chain reaches that same state
instead of failing or re-narrowing to 8.

## 20. Final verdict

```text
REMEDIATION COMPLETE — READY FOR INDEPENDENT VERIFICATION
```

Basis: MIG-1 is resolved (the fresh chain applies the corrected migration last,
with no missing-relation error and no post-P3 re-narrowing path); a genuinely fresh
relevant migration chain passes (81 applied, 80 OK, the one failure being an
unrelated Supabase Storage-schema artefact); the final I3 constraint accepts
exactly the authorized 10 tools and rejects an unauthorized name; I4 remains at the
authorized 15 states including `multiple_matches`; the P2 catalogue pin is
corrected and passes; P2 (79), P3 (48) and the 299-test Insight regression all pass
with no new failure; the commit is pushed with local/remote aligned and the working
tree clean apart from the known pre-existing untracked reference documents.

This is **not** independent OHD verification and **not** a PO closure. Independent
verification and acceptance remain PO/OHD decisions.

