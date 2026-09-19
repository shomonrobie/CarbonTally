# CT-STEP2-F039-1-ADJUDICATION-LIFECYCLE-058

```text
STARTING SHA  00856dd494c1a23b7a2d46b39a758cdd9c3cd869  (p8-release-reconciled, tree clean)
FINAL SHA     recorded in the completion summary (HEAD == origin verified after push)
BRANCH        p8-release-reconciled — no reset / rebase / force-push
MIGRATIONS    NONE added or changed — the 055 schema is used exactly as delivered
PRODUCTION    NOT touched · no production migration · NOTHING DEPLOYED
UI / D19      NOT modified
```

## FILES CHANGED (two commits)

```text
7db2ede  backend/data/activity_clarifications.py                    (evidence layer)
         backend/tests/unit/data/test_activity_clarifications_repository.py  (+5 tests)
022f2d4  backend/api/v3_activity_clarifications.py                  (F2/F3/F4 + versioned writes)
         backend/tests/unit/api/test_v3_activity_clarifications_api.py       (+4 tests)
SERVICE CHANGES   NONE — see F1
```

## REPOSITORY CHANGES (7db2ede)

```text
resolve_evidence(item_id, activity)  server-derived context item → batch → organization;
                                     source_evidence_ref from the persisted file identity; unit/scope
                                     ONLY from the persisted extracted_data line whose text matches the
                                     extracted activity exactly
_line_evidence(...)                  zero or several matches → (None, None): nothing invented, no
                                     client value substituted (the safe path)
evidence_signature(a, unit, scope)   the D-F039-1-I signature — sha256 over exactly the three mandated
                                     fields, nothing else, generated server-side
effective_compatible(...)            (row, compatible): true only when the stored signature equals the
                                     CURRENT evidence signature; a row with no stored signature is NOT
                                     compatible (no proof ⇒ no reuse)
apply_versioned / effective / history / supersede   (056, unchanged) — now the API's persistence path
```

## API CHANGES (022f2d4)

```text
F2 provenance  `item_id` is a lookup key only: the server resolves it, rejects unknown items (404) and
               items belonging to another organisation (403, no write), and stores the derived
               item_key / batch_key / source_evidence_ref. No client provenance is trusted.
F3 decline     /decline runs the SAME assessment as the clarification path and refuses (409, zero DB
               writes) when the activity is not clarification-required.
F4 unit/scope  `unit`/`scope` removed from `ClarificationSubmitIn` — with `extra="forbid"` submitting
               them is a 422. Authoritative values come from the persisted line; absent a match they
               are None and the existing policy decides.
versioning     both write paths persist through `apply_versioned` (v1 / replay / v2 + supersede) with
               the bounded context key, the evidence signature and the evidence context.
unchanged      semantic-only requests; factor metadata still server-only; authorization still via
               `ensure_processing_org_access`; no new role, grant or policy.
```


## TESTS ADDED AND EXACT RESULTS

```text
ADDED (9)
  repository — signature coverage/normalisation · provenance + authoritative unit derivation ·
    unmatched/ambiguous line ⇒ no unit and no invention · compatible signature accepted · changed
    evidence and missing signature rejected
  API — decline refused on a deterministic activity (409, no write) · forged body unit/scope ⇒ 422 ·
    authoritative evidence derived from the persisted item (item_key, source ref, context key,
    signature) · cross-organisation item ⇒ 403 with no write
SUITES RUN (pytest exit code 0 = all collected tests passed)
  tests/unit/api/test_v3_activity_clarifications_api.py           exit 0  (31 tests)
  tests/unit/data/test_activity_clarifications_repository.py      exit 0  (17 tests)
  tests/unit/services                                            exit 0
  tests/unit/engines/test_factor_selection_policy.py (D-A/D-FS)   exit 0
  tests/unit/engines/test_activity_clarification_041.py          exit 0
  tests/unit/engines/test_activity_clarification_043.py          exit 0
```
No broader aggregate is claimed and no previously recorded total is presented as re-run.

## F1 — NOT IMPLEMENTED (the remaining blocker)

`services/automatic_processing.py` still diverts to `clarification_required`; the persisted
adjudication is not yet consumed there. Everything it needs now exists — the 055 schema, the bounded
context key, `effective_compatible()` for D-039-1-I compatibility and `resolve_clarification()` for
policy re-entry — so it is a bounded edit at the gate (≈lines 1288–1307) plus service tests. Until
then the end-to-end invariant stops at "policy input persisted", not "subsequent processing consumes".

## CONFLICT / RE-EVALUATION AND FACTOR-SET SAFETY

`effective_compatible()` implements D-039-1-G/-I: matching signature ⇒ reusable as semantic evidence;
a different signature ⇒ not applied, with the previous version preserved (only `is_current` is ever
flipped) and `re_evaluation_required` available. Factor metadata is stored per version and no code path
rewrites it, so a factor-set change cannot rewrite history. The consumption side (where the service
would mark re-evaluation) belongs to F1 and is not yet wired.

## DISPOSABLE DB / RLS

No new DDL or lifecycle round-trip ran this window; 055's verification remains the standing evidence
(schema applied, one-current invariant enforced, v1 preserved, replay rejected). The code added here
was verified by unit tests only — not against the live disposable database. RLS, grants and the four
tenant policies are untouched, and production was never contacted.

## KNOWN PRE-EXISTING FAILURES

`F-051-1` still pins 71 migrations; the tree holds 74 (unchanged — no migration added). NOT modified.
`test_review_sla_surfaces`, `test_p6_1b_*`, the stale disposable integration environment and the
missing 7049-factor dataset were not touched, and no baseline comparison was run for them.

## VERDICT

**IMPLEMENTATION PARTIAL — F2 provenance, F3 decline gate and F4 authoritative unit/scope are
implemented and tested, together with the D-F039-1-I evidence signature and versioned persistence on
the write path. F1 consumption by automatic processing, the current/history read endpoints and the
service-level lifecycle tests remain unimplemented.**

No independent verification was performed, no PO closure is claimed, production was not touched, and
nothing was deployed.
