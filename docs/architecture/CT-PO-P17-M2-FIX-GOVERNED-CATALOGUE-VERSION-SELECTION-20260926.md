# CT-PO-P17-M2 — Governed Catalogue Version Selection (DEF-1 fix)

> **Task:** P17-M2, closing `DEF-1` from
> `CT-PO-P17-M-INDEPENDENT-VERIFICATION-CAPABILITY-TRUTH-SURFACE-20260926.md`.
> **Repo:** `/home/shomonrobie/ct_93d5cdd`, branch `p8-release-reconciled`,
> baseline `41e6c616f32b448f9d78760a08c26da67b4b9281`.
> **Report state:** implementation + evidence complete; committed, not pushed.

---

## 1. Task identity

### 1.1 What this task had to do

`P17-M` independently falsified the claim that framework-version selection for the
capability truth surface (`GET /api/v3/capabilities`) is safe:

> **DEF-1** — the capability statement can be silently *upgraded* by a competing
> governed version. Selection was
> `next(candidate for candidate in candidates if any(is_governed_requirement_code(code) …))`
> over candidates ordered `IN_FORCE` → `source_tier` → `version_label`, so one
> `INSERT` of a tier-1 `IN_FORCE` version carrying **one** governed-looking
> requirement code made that version the product capability catalogue. The
> surface then answered **HTTP 200** with a narrower and stronger claim
> (`SUPPORTED` where the governed truth is `PARTIALLY_SUPPORTED`; rollup
> `1/0/0/0` instead of `4/6/3/2`).

P17-M's recommended correction (§16/§21) was: *anchor selection to a governed
identity; decide whether a competing `IN_FORCE` version must be ignored, or must
force a refusal.*

This task implements that correction:

1. **Identity-anchored selection.** A framework version is the governed
   capability catalogue **only** if its requirement rows are the **complete**
   frozen governed identity set (18 identities) **and carry nothing else**.
   Position is never consulted; `status`, `source_tier` and `version_label` can
   no longer decide a product claim.
2. **Fail closed on true ambiguity.** Two versions that each carry the complete
   governed identity set are an ambiguous governed state: the surface returns
   **503** with no claim rather than choosing.
3. **Prove it adversarially on real PostgreSQL**, including that the competitor
   really *was* selectable by the pre-fix rule (so the test is not vacuous).

### 1.2 What this task must not do

* No schema change, no migration, no new vocabulary, no new column.
* No change to the frozen `M-1` mapping, the 18-row catalogue, or the four-way
  rollup (`4/6/3/2`).
* No change to tenancy, RLS, grants or the authentication posture of the surface.
* No change to what the surface *claims* when the governed catalogue is intact —
  the canonical payload must be unchanged.
* No invented routes, no invented response schema (`AGENTS.md §65`).
* No silent catalogue transition. A catalogue transition remains a PO decision
  (`AGENTS.md §62`).

### 1.3 What "verified" means in this report

* **IMPLEMENTED** — code present in the working tree (claimed).
* **TESTED** — a named test executed and passed (evidence file named).
* **VERIFIED** — executed against real PostgreSQL / real ASGI route / real DOM,
  with the adversarial state proved to be genuinely adversarial.
* **ACCEPTED** — *not claimed here.* No investor or PO acceptance is asserted.

---

## 2. Baseline

| Item | Value |
|---|---|
| Worktree | `/home/shomonrobie/ct_93d5cdd` |
| Branch | `p8-release-reconciled` |
| HEAD at start | `41e6c616f32b448f9d78760a08c26da67b4b9281` |
| Baseline verify worktree | `/tmp/ct_base_verify` (unmodified HEAD) |
| Disposable clone (target) | `ct_iv_p17m2_20260926` (127.0.0.1:54426) |
| Disposable clone (no catalogue) | `ct_p17m_nocat_20260926` (127.0.0.1:54426) |

Modified: `backend/domain/capability_catalogue.py`, `backend/data/disclosure.py`,
`backend/api/v3_disclosure.py`,
`backend/tests/integration/test_p17l_capability_truth_surface_runtime.py`.
Created: the three new P17-M2 test modules. No migration, no `.env`, no secret.

`git status` also shows **pre-existing, unrelated** modifications this task did
**not** touch and did **not** stage: `.gitignore` (line-ending churn, 108/107),
plus untracked pre-existing docs/reports and two zero-byte files (`8`, `=`).
They are left exactly as found.

---

## 3. Sources

1. `docs/architecture/CT-PO-P17-M-INDEPENDENT-VERIFICATION-CAPABILITY-TRUTH-SURFACE-20260926.md`
   — §10 (adversarial test), §16 (DEF-1), §21 (verdict + consequential follows).
2. `docs/architecture/CT-PO-P17-L-CAPABILITY-TRUTH-SURFACE-20260926.md`
   — the governed surface this fix protects.
3. `docs/architecture/CT-PO-P17-DECISION-03-PO-FREEZE-CAPABILITY-STATUS-INVESTOR-SURFACE-20260926.md`
   — the frozen claim table (`M-1`, `M-6`), which neither the fix nor the
   competitor may alter.
4. `AGENTS.md` — §62 (PO decision rule), §65 (API contract), §66/§67
   (database/RLS), §73/§74 (acceptance language, no false completion), §55.1
   (F-046-1 destructive-harness safety).
5. Current runtime truth: the code, the disposable clones, and the executed runs
   named in this report.

---

## 4. Root cause

Pre-fix, in the route (`backend/api/v3_disclosure.py`):

```python
candidates = await catalog.capability_catalogue_candidates()
selected = next(
    (
        candidate
        for candidate in candidates
        if any(
            is_governed_requirement_code(code)
            for code in (candidate.get("requirement_codes") or [])
        )
    ),
    None,
)
```

and in the read model (`backend/data/disclosure.py`),
`capability_catalogue_candidates()` ordered rows

```sql
ORDER BY (fv.status = 'IN_FORCE') DESC, fv.source_tier, fv.version_label, fv.id
```

Three independent mistakes compose into the defect:

1. **`any` instead of the whole identity set.** "Governed-looking" was satisfied
   by *one* code. A version carrying a subset, or the complete set plus residue,
   or an unrelated row whose code happened to match the grammar, passed.
2. **`next(...)` over an ordered sequence.** The first passing candidate won, so
   the *ordering fields* — not the governed identity — decided the product claim.
3. **The ordering fields are ordinary data.** `status`, `source_tier` and
   `version_label` are plan columns; a tier-1 `IN_FORCE` competitor with an early
   label sorts ahead of the governed version. The governed catalogue was
   replaceable by an ordinary `INSERT`.

The projection then cooperated: it is happy to state a *partial* claim, so the
surface returned **200** carrying the competitor's narrower, upgraded claim. No
governance event stood behind that change.

---

## 5. The defect, formally

Let `G` be the frozen governed identity set (18 identities), `codes(v)` the
requirement codes of version `v`, and `≺` the read-model ordering.

* **Pre-fix selector:** the first `v` in `≺` order with `codes(v) ∩ G ≠ ∅`.
* **Pre-fix outcome:** the claim is a function of `≺`, which is derived from
  data, not from governance.
* **Variants that defeat it** (all reproduced here on real PostgreSQL):
  * **A — one-code hijack.** `codes(v*) = {one governed code}` ⇒ `v*` is served,
    publishing a 1-row catalogue (`1/0/0/0`).
  * **B — upgrade.** `codes(v*) = {one governed code with a raised `M-1` value}`,
    e.g. `MISSING_CAPABILITY → SUPPORTED` ⇒ rollup `5/6/3/1`
    (`UPGRADED_ROLLUP` in the integration suite models exactly this harm).
  * **C — complete-set-plus-residue.** `codes(v*) = G ∪ {residue}` ⇒ selected on
    the strength of a governed code; projecting it then *raises*
    (`DisclosureViolation`: a non-governed row has no governed dimension), so the
    defect was simultaneously a **truth** defect and an **availability** defect.

* **Post-fix selector:** the unique `v` with `codes(v) ≠ ∅`, `codes(v) ⊆ G` and
  `G ⊆ codes(v)` — i.e. `codes(v) = G`, since `G` is closed, "complete and nothing
  else" is exactly identity equality.
  * none ⇒ `None` (no claim; **503**);
  * one ⇒ that version, **whatever its position**;
  * more than one ⇒ ambiguous governed state ⇒ `DisclosureViolation` ⇒ **503**.

---

## 6. The correction — the identity anchor

`backend/domain/capability_catalogue.py` (additive; nothing existing removed):

```python
def governed_requirement_identities() -> frozenset[str]:
    """Every governed disclosure requirement identity, as one closed set."""
    identities = {"GP-S1"}
    identities.update(f"GP-S2-{suffix}" for suffix in _SCOPE2_METHOD_BY_SUFFIX)
    identities.update(
        f"GP-S3-CAT-{category:02d}" for category in range(1, SCOPE3_CATEGORY_COUNT + 1)
    )
    for identity in sorted(identities):  # pragma: no cover - closed registry
        if not is_governed_requirement_code(identity):
            raise DisclosureViolation(
                f"P17-M2: {identity!r} is in the governed identity set but is not a "
                "governed requirement identity"
            )
    return frozenset(identities)


GOVERNED_CATALOGUE_IDENTITIES: frozenset[str] = governed_requirement_identities()
```

Two properties matter and are separately tested:

* **Derived, not re-typed.** The set is built from the closed registries that
  already define the grammar (`_SCOPE2_METHOD_BY_SUFFIX`, `SCOPE3_CATEGORY_COUNT`),
  so the identity set and the identity grammar cannot drift apart. The
  self-check raises rather than serving a set the grammar would reject.
* **No new vocabulary.** The set contains exactly the 18 requirement codes that
  already exist in the persisted catalogue; no new token, column or status is
  introduced.

```python
def is_governed_catalogue_version(candidate: Mapping[str, Any]) -> bool:
    codes = [str(code) for code in (candidate.get("requirement_codes") or [])]
    if not codes:
        return False
    if not all(is_governed_requirement_code(code) for code in codes):
        return False
    return GOVERNED_CATALOGUE_IDENTITIES <= set(codes)
```

The rule reads only `requirement_codes`. It never reads `status`, `source_tier`,
`version_label` or the candidate's index.

---

## 7. Selector semantics

```python
def select_governed_catalogue_version(
    candidates: Sequence[Mapping[str, Any]],
) -> Optional[dict[str, Any]]:
    governed = [
        dict(candidate)
        for candidate in _dicts(candidates)
        if is_governed_catalogue_version(candidate)
    ]
    if not governed:
        return None
    if len(governed) > 1:
        labels = ", ".join(
            sorted(str(item.get("version_label") or "") for item in governed)
        )
        raise DisclosureViolation(
            "P17-M2: "
            f"{len(governed)} framework versions each carry the complete governed "
            f"requirement identity set ({labels}); the governed capability catalogue "
            "is ambiguous, so no capability statement can be made until an explicit "
            "governed catalogue transition resolves it"
        )
    return governed[0]
```

| State | Selector | Surface |
|---|---|---|
| Exactly one version with `codes(v) = G` | that version | **200** + canonical claim |
| No version with `codes(v) = G` | `None` | **503**, no claim |
| Two or more versions with `codes(v) = G` | `DisclosureViolation` | **503**, no claim |

Consequences that the tests pin down:

* **Order-independence.** `governed` is filtered, not searched: reversing,
  shuffling or prefixing the candidate list cannot change the answer
  (`test_selector_ignores_position`, `test_the_shipped_route_selects_by_identity`).
* **Proportionality.** A near-miss, an empty version, or unrelated residue does
  **not** create a second catalogue, so the surface stays healthy (**200**) rather
  than 503-ing on unrelated data
  (`test_a_near_miss_code_offered_first_neither_hijacks_nor_ambiguates`,
  `test_a_version_with_no_requirement_rows_is_not_a_candidate_at_all`).
* **Fail closed only when genuinely ambiguous.** Ambiguity requires *two complete
  governed versions* — a governance state that cannot be resolved by data
  ordering and must not be guessed (`test_a_complete_competitor_offered_first_…`).

---

## 8. Route change (`backend/api/v3_disclosure.py`)

The route no longer examines requirement codes at all; it delegates:

```python
    candidates = await catalog.capability_catalogue_candidates()
    try:
        selected = select_governed_catalogue_version(candidates)
    except DisclosureViolation as exc:
        # More than one version claims the catalogue identity: an ambiguous
        # governed state yields NO claim, never a chosen one.
        logger.error("capability surface: ambiguous governed catalogue (%s)", exc)
        raise HTTPException(
            status_code=503,
            detail=(
                "The governed capability catalogue is ambiguous, so no capability "
                "statement can be made until it is resolved."
            ),
        ) from exc
    if selected is None:
        logger.error(
            "capability surface: no framework version carries a governed requirement catalogue"
        )
        raise HTTPException(
            status_code=503,
            detail=(
                "The governed capability catalogue is not provisioned, so no "
                "capability statement can be made."
            ),
        )
```

* The `any(is_governed_requirement_code(...))` expression is **deleted**; the
  route contains no requirement-code test of its own.
* Two distinct 503 paths, both claim-free:
  * **ambiguous** — `DisclosureViolation` from the selector (two complete
    governed versions);
  * **not provisioned** — `selected is None`, or the framework row absent.
* Nothing else about the route changed: same path, same method, same auth
  dependency, same response model, same tenancy handling.

---

## 9. Read-model change (`backend/data/disclosure.py`)

The ordering in `capability_catalogue_candidates()` was made **total and
deterministic** (`fv.id` as the final tie-break), because the selector must never
depend on database order. It is now explicitly *not* a precedence rule:

```sql
ORDER BY (fv.status = 'IN_FORCE') DESC, fv.source_tier ASC, fv.version_label ASC, fv.id ASC
```

The `ORDER BY` is retained deliberately — it makes
`capability_catalogue_candidates()` reproducible and keeps the "which version is
offered first" evidence available — but it is now **evidence, not authority**.
This is asserted both statically (the shipped SQL text is read and checked) and
behaviourally (a competitor that really does sort first still cannot win).

---

## 10. What was *not* changed

| Area | Status |
|---|---|
| Frozen `M-1` mapping (18 rows) | untouched — asserted row-by-row against the frozen image |
| Rollup | untouched — still `4/6/3/2`; never a total or percentage |
| Projection / `DisclosureViolation` behaviour | untouched |
| Schema, migrations, grants, RLS | untouched; **no migration added** |
| Authentication / tenancy of the route | untouched |
| The canonical 200 payload | untouched — asserted equal to the pre-fix payload |
| `UPGRADED_ROLLUP` (`5/6/3/1`) | test-only fixture modelling the DEF-1 harm; **never** a served value |
| P17-K / P17-L behaviour | unchanged; regression suite green |

---

## 11. Fail-closed taxonomy

| Condition | HTTP | Claim served | Evidence |
|---|---|---|---|
| Catalogue intact (one complete governed version) | 200 | canonical `4/6/3/2` + 18 rows | integration #4, #12, #13, #15 |
| No version carries the governed identity set | 503 | none | integration #12, #14 |
| Two complete governed versions (ambiguous) | 503 | none | integration #8 |
| Projection refuses (non-governed row, placeholder, …) | 503 | none | pre-existing behaviour, integration #7 |

The 503 bodies are user-facing prose with no technical detail (`AGENTS.md §46`),
no UUID, no SQL. The technical reason is logged server-side
(`logger.error("capability surface: ambiguous governed catalogue (%s)", exc)`).

Crucially, **`503` is never a downgraded `200`**: a claim that cannot be stated
honestly is not stated at all. "Show less, never something stronger."

---

## 12. PO decision boundary

The fix deliberately does **not** decide *which* catalogue is the product truth.
That is a governance act (`AGENTS.md §62`):

* If exactly one version carries the complete governed identity set, the surface
  states it. No PO input needed — this is the existing ratified catalogue.
* If **two** versions do, the surface refuses (503) and the selector's message
  names both versions by label so the operator can see the collision. Choosing
  between them — i.e. performing a catalogue transition — is **PO DECISION
  REQUIRED**, and is not performed by ordering, by tier, by `IN_FORCE`, or by an
  in-code guess.
* Adding or retiring a governed requirement identity is likewise a PO decision;
  the fix only *reads* the closed registry that already encodes that decision.

This is the difference between *implementing* a truth rule and *inventing*
business policy: the code enforces the identity the catalogue already has, and
abstains when the identity is genuinely contested.

---

## 13. Unit evidence — domain identity rule

`backend/tests/unit/domain/test_p17m2_governed_catalogue_identity.py` — 30 items, all passing.

| Group | What is pinned |
|---|---|
| Identity set shape | `len(GOVERNED_CATALOGUE_IDENTITIES) == 18`; exactly `GP-S1`, `GP-S2-LB`, `GP-S2-MB`, `GP-S3-CAT-01…15`; the set is a `frozenset`, and every member is proven a governed identity by the set's own builder (a drift raises `DisclosureViolation` inside `governed_requirement_identities()`) |
| Membership grammar | near-misses rejected as identities *and* as set members: `GP-S3-CAT-16`, `GP-S3-CAT-0`, `GP-S2-XX`, `GP-S3`, `""` |
| The defect mechanism | `_pre_fix_rule()` reproduces the pre-fix `any(is_governed_requirement_code(...))`-with-ordering predicate and returns the **adversary** for `DEF-1`'s exact candidate set — so the fixtures are proven to still reproduce `DEF-1`, and the shipped rule is shown to select the governed version instead |
| Identity rule | complete set ⇒ catalogue; complete-minus-one (all 18 tested) ⇒ not; complete set **plus** a non-governed row ⇒ not; any single governed code alone (all 18 tested) ⇒ not; empty ⇒ not |
| Order freedom | `select_governed_catalogue_version` returns the governed version for four orderings of the same list: `governed-first`, `hijack-first`, `two-hijacks-before`, `narrower-before-governed` |
| Attribute blindness | 12 parametrised cases (4 × `status ∈ {IN_FORCE, SUPERSEDED, DRAFT, WITHDRAWN}` × 3 × `source_tier ∈ {1,2,3}`) in which the governed version is relabelled `zzz-late-label` **and placed after** the adversary: the adversary is still not the catalogue and the governed version still is — selection is provably independent of every ordering field |
| Ambiguity | two complete versions ⇒ `DisclosureViolation`, in both list orders; one complete + one incomplete ⇒ no violation; the message names the colliding labels |
| Selector contract | `None` ⇒ no violation; a single candidate ⇒ returned unchanged as a **copy** (mutating the result does not mutate the caller's list, and no field is added or rewritten) |
| Structural guards | `inspect.getsource` on the route asserts it delegates to `select_governed_catalogue_version`, and that `is_governed_requirement_code`, `requirement_codes` and `next(` no longer appear in it; the three helpers are asserted to declare no new capability/applicability vocabulary and no nested second rule |

The "attribute blindness" and "order freedom" parametrisations are the direct
regression against `DEF-1`: they demonstrate the fix is *structural* — the
ordering fields cannot reach the decision at all — rather than a re-tuning of
the sort order.

---

## 14. Unit evidence — API/route rule

`backend/tests/unit/api/test_p17m2_governed_catalogue_version_selection.py` — 10 items (8 functions, one parametrised 3 ways), all passing.
Real route mounted on a real `FastAPI` app with `get_current_user` / `get_pool`
overridden and a **faked** read model, so route-level behaviour is exercised
without a database:

* baseline — canonical 200 (`18` rows, rollup `4/6/3/2`, frozen `M-1` values),
  and the surface reads **only** the version it selected (`requested_version_ids
  == [GOVERNED_VERSION_ID]`);
* `DEF-1`, three hostile shapes, each asserted to **lead** the candidate list
  (so a regression to positional selection fails here even if nothing else
  changed): `one-governed-code-upgraded-to-SUPPORTED`,
  `complete-set-plus-extra-code`, `non-governed-codes-only` ⇒ canonical 200 in
  every case, and the hostile id/label appears nowhere in the response text;
* `DEF-1`'s mechanism is re-proven in-process: `is_governed_requirement_code`
  still returns `True` for `GP-S3-CAT-01`, the adversary still looks
  `IN_FORCE`/tier `1`/lexically earlier, yet `is_governed_catalogue_version` is
  `False` for it and `True` for the real catalogue;
* no silent upgrade: `GP-S3-CAT-01` is served as `PARTIALLY_SUPPORTED` with
  `supported = True`, the governed `framework_version_label`, tier `1` and the
  unresolved-identifier provenance marker; `1/0/0/0` is unreachable;
* two complete governed versions ⇒ **503**, the body says *ambiguous*, and
  **no** version is read (`requested_version_ids == []`);
* no catalogue at all ⇒ **503** stating *not provisioned*, and again no version
  is read;
* a malformed governed value (`PARTIAL`, an Axis-A token) ⇒ **503**, and the
  token appears nowhere in the body;
* two different tenant identities (one with an organisation, one without) under
  the attack receive a **byte-identical** serialised claim.

The complementary structural assertion — that the route no longer contains the
pre-fix predicate, no `next(`, and no `requirement_codes` access at all — lives
in the domain module (`test_the_route_no_longer_implements_the_pre_fix_selection_rule`).

---

## 15. Integration evidence — selection on a real database

File: `backend/tests/integration/test_p17m2_governed_catalogue_selection_runtime.py` (new).
Target: `INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_iv_p17m2_20260926` (disposable clone).
Result: **`22 passed in 2.92s`, `EXIT=0`** (raw log `/tmp/m2_int3.txt`).

The suite runs the **production** read model, selector, projection and route
against real PostgreSQL rows; only the connection is shimmed (`_TxPool`) and
every scenario runs inside a transaction that is **always rolled back**, so the
clone is left as found.

| Group | Items |
|---|---|
| Target & persisted truth (preconditions) | `test_the_target_is_a_disposable_clone`; `test_the_persisted_catalogue_is_the_complete_governed_identity_set`; `test_the_persisted_rows_match_the_frozen_m1_image`; `test_the_governed_identity_set_is_closed_and_matches_the_grammar` |
| Baseline over HTTP | `test_the_route_serves_the_canonical_claim_on_the_real_database`; `test_the_selector_ignores_position_on_real_candidates` |
| The attack (added this session) | `test_a_one_code_competitor_offered_first_cannot_hijack_the_catalogue`; `test_a_complete_competitor_is_ambiguous_and_the_surface_fails_closed`; `test_the_surface_serves_the_canonical_claim_once_the_ambiguity_is_gone`; `test_a_near_miss_code_offered_first_neither_hijacks_nor_ambiguates` × 6 params (`gp-s3-cat-01`, `GP-S3-CAT-1`, `GP-S3-CAT-01 `, `GP-S3-CAT-16`, `GP-S4-CAT-01`, `B1RT_068e737e`); `test_a_version_with_the_complete_set_plus_residue_is_not_the_catalogue`; `test_a_version_with_no_requirement_rows_is_not_a_candidate_at_all` |
| Honest refusal | `test_a_database_without_the_catalogue_states_no_claim` |
| Tenancy invariance | `test_two_real_tenants_receive_the_same_claim_under_the_attack` |
| Shipped-artefact structure (no side effects) | `test_the_shipped_route_selects_by_identity_not_by_position`; `test_the_shipped_order_by_is_not_a_precedence_rule`; `test_the_read_path_writes_nothing` |

Three claims in this suite are what make the fix *provable* rather than merely
*tested*:

1. **The competitor really was selectable before the fix.** The module replays
   the pre-fix predicate (`_legacy_rule_selection`) over the rows the shipped
   read model returns for the adversarial state, and asserts it picks the
   competitor — so the regression cannot pass by accident if the fixtures ever
   stop reproducing `DEF-1`.
2. **The shipped SQL no longer offers an authority ordering to lean on.** The
   outer `ORDER BY` of `capability_catalogue_candidates` is asserted to be
   exactly `f.code, fv.version_label, fv.id` — a reproducibility key — with
   `IN_FORCE`, `source_tier`, `status`, `verified_at` and `NULLS` all
   **forbidden** from that clause, and no `DRAFT`/`SUPERSEDED` literal in the
   statement. Those words survive only inside the *projection* (the payload must
   still report them honestly).
3. **The route cannot silently reintroduce a positional rule.** Source is read
   from disk and asserted to contain the delegation
   (`select_governed_catalogue_version(candidates)`), the `if selected is None`
   fail-closed branch, at least three `status_code=503` branches and the
   governed refusal wording — and to **not** contain
   `is_governed_requirement_code` anywhere in the module, nor the pre-fix
   `next(candidate for candidate in candidates …)` expression, nor
   `source_tier`/`IN_FORCE`/`version_label`/`ORDER BY` inside the handler body.

---

## 16. Integration regression — P17-K and P17-L unchanged

Same disposable clone, via the corrected runner `/tmp/run_m2_reg2.sh`; raw log
`/tmp/m2_reg2.txt`.

| Suite | Items | Result |
|---|---|---|
| P17-K governed capability catalogue runtime | 24 passed | `INT_EXIT=0` |
| P17-L capability truth surface runtime | 37 passed | `INT_EXIT=0` |

These are the suites that establish the *surrounding* invariants the fix must
not weaken: governed constants and check constraints equal the source, the `M-1`
image is non-upgrading, no Axis-A token or applicability vocabulary is persisted
or renderable, provenance exists on every row, no official identifier is
invented, the rollup is never a total, the catalogue carries no tenant column
and no FK to a tenant table, two tenant contexts see identical truth, and the
`F-046-1` safety probe refuses persistent environments **before** any
`TRUNCATE`.

**Runner defect found and corrected (a harness defect, not a product defect).**
The first regression runner named `tests/unit/api/test_p17_acting_for.py`, but
that module lives at `tests/unit/domain/test_p17_acting_for.py`; the batch exited
`4` (usage error, zero tests collected). `/tmp/run_m2_reg2.sh` corrects the path
and the batch is green. Recorded so a rerun is not misread as a capability
failure.

**Verification-hygiene finding in P17-L (also corrected).** That module had
re-implemented the pre-fix selection rule inside its own
`_select_catalogue_version` helper (`any(is_governed_requirement_code(...))` over
the candidates, take the first hit). The helper now calls the **shipped**
selector, so the suite can no longer stay green while the route's rule differs —
precisely the duplicated-rule drift that allowed `DEF-1` to survive a green
suite. The change is a pure helper substitution: no test body or expected value
in that module was altered, and all 37 items pass unchanged.


Focused unit batch (same runner), log `/tmp/m2_unit_focus.txt` — **457 passed,
`UNIT_EXIT=0`**, across: `test_p17m2_governed_catalogue_identity.py`,
`test_p17m2_governed_catalogue_version_selection.py`,
`test_p17l_capability_truth_surface.py`,
`test_capability_catalogue_projection.py`, `test_disclosure.py`,
`test_disclosure_exposure.py`, `test_disclosure_projection.py`,
`test_disclosure_narrative.py`, `test_p17_scope2.py`, `test_p17_scope3.py`,
`test_p17_cams.py`, `test_p17_10_product_contract.py`, `test_p17_acting_for.py`,
`test_v3_disclosure_api.py`, `test_v3_disclosure_finalisation_api.py`,
`test_v3_disclosure_narrative_api.py`, `test_v3_new_capabilities.py`.

---

## 17. Frontend evidence

Command: `npm test -- --ci capability-truth-surface` in `frontend/`; raw log
`/tmp/fe_cap.txt`. **1 suite passed, 19 tests passed, 19 total, `EXIT=0`**
(`src/v3/__tests__/capability-truth-surface.test.jsx`).

No frontend source change was required or made: the fix changes *which* governed
rows are served, not the payload's shape, vocabulary, ordering or fields. The
suite nevertheless re-verifies the rendering contract under the new server
behaviour — both surfaces render the same governed value per requirement, no
Axis-A token, placeholder or emissions figure is renderable, the four-way rollup
renders with its counts and never as a total or percentage, provenance and the
unresolved marker are rendered, the customer surface points at its own results
while the product surface is labelled product-level, an unrecognised capability
value is still rendered verbatim, and a failing load shows a bounded error with
retry and **no claim**. Because no frontend source changed, no rebuild or
redeploy is implied by this work.

---

## 18. Baseline comparison — pre-existing failures, unaffected by the fix

Comparison run (`/tmp/base_cmp.txt`, `EXIT=1` in both trees) over five modules
unrelated to this change:

| Tree | Revision | Result |
|---|---|---|
| Fixed working tree | `41e6c61` + P17-M2 patch | 9 failed — `FIXED_EXIT=1` |
| Clean worktree `/tmp/ct_base_verify` (unpatched `HEAD`) | `41e6c61` | **the identical 9 failed** — `BASE_EXIT=1` |

The failure set is identical in both trees (and in the earlier clean-worktree
log `/tmp/base_verify.txt`):

```
test_i1_insight_migration.py::test_i1_migration_is_the_latest_migration
test_i2_insight_authorization_contracts.py::test_i2_migration_is_the_latest_and_scoped_to_one_policy
test_d17_provider_ownership_migration_revision.py::TestRevisionScope::test_migration_ordering_is_unchanged
test_review_sla_surfaces.py::test_canonical_ops_sla_surface_registered
test_review_sla_surfaces.py::test_canonical_ops_review_assign_registered
test_review_sla_surfaces.py::test_admin_legacy_compat_surface_retained
test_extraction_suggestions.py::test_suggest_parses_clean_invoice
test_extraction_suggestions.py::test_suggest_missing_fields_leave_unresolved
test_extraction_suggestions.py::test_suggest_no_fabrication_on_garbage
```

All nine are migration/ordering and review-SLA/extraction-suggestion
expectations in modules this task never touched, and they fail identically with
and without the patch. They are **pre-existing and outside P17-M2 scope**;
recorded so the closure is not contaminated by them and a future session does
not attribute them to this fix.

---

## 19. Verification environment and safety (`F-046-1`)

The integration harness performs destructive setup: `backend/tests/integration/
conftest.py`'s `pool` fixture runs `TRUNCATE … RESTART IDENTITY CASCADE` against
whatever `INTEGRATION_DATABASE_URL` names. Every run in this task therefore
targeted a **disposable clone** on `127.0.0.1:54426` (`postgres:postgres`), never
the investor demo, never persistent QA, never production:

| Clone | Purpose |
|---|---|
| `ct_iv_p17m2_20260926` | main P17-M2 / P17-K / P17-L verification target |
| `ct_iv_p17m2_clean_20260926` | ambiguity-free control state |
| `ct_p17l_surface_20260926` | truth-surface lineage |
| `ct_p17m_nocat_20260926` | no-catalogue (honest-refusal) state |

Safety is asserted, not assumed, at three levels:

* the `F-046-1` probe refuses any target whose name matches
  `qa` / `demo` / `investor` / `prod` / `live` (and the forbidden main databases)
  with an explicit `F-046-1` error **before** any destructive statement executes
  (`conftest.py` lines 43–124) — proven by
  `test_the_f046_1_probe_refuses_persistent_environments` (P17-K) and
  `test_the_safety_probe_refuses_the_demo_database_before_any_truncate` (P17-L);
* the new module asserts its own target is a disposable clone
  (`test_the_target_is_a_disposable_clone`) before exercising anything;
* `test_the_demo_database_catalogue_is_untouched_by_this_work` (P17-L) confirms
  the demo catalogue is unchanged, and the new module's connection shim
  (`_TxPool`, produced by the `_rolled_back` fixture) keeps every scenario inside
  a transaction that is always rolled back, so no clone was left mutated either.

The read path is additionally proven non-mutating by
`test_the_read_path_writes_nothing`: the shipped statements contain no
`INSERT`/`UPDATE`/`DELETE`/`TRUNCATE`/`ALTER`, and a real request leaves the table
digests and row counts identical.

## 20. Security, tenancy and authorization review

**What the endpoint is.** `GET /api/v3/capabilities` is a *product-level*
statement ("what does CarbonTally support?") behind `get_current_user`: it
requires authentication, takes no tenant parameter, issues no tenant-predicated
query, and answers identically for every authenticated caller. Both properties
are asserted — `test_the_route_refuses_an_unauthenticated_caller` (authentication
required) and `test_the_product_surface_answers_without_any_tenant_context`
(identity-independent) — and the fix changes neither.

**No authorization regression.** The patch touches selection only: it changes
*which persisted rows are read*, not who may read them, not which dependency
guards the route, not any RLS policy, not any storage path, not any response
field. No `Depends`, no `get_current_user`/`get_pool` wiring, no policy, no grant,
no `security.py` and no migration is modified — the diff is confined to
`domain/capability_catalogue.py`, `api/v3_disclosure.py`,
`data/disclosure.py` plus tests.

**Tenancy isolation preserved and re-proven.** P17-L asserts the catalogue carries
no tenant column and no FK to a tenant table
(`test_the_catalogue_tables_carry_no_tenant_column`,
`test_no_foreign_key_leads_from_the_catalogue_to_a_tenant_table`), issues no
tenant query (`test_no_tenant_query_is_issued_by_the_read_model`), leaks no tenant
token (`test_no_tenant_token_is_returned`) and yields identical truth for two
tenant contexts (`test_two_tenant_contexts_see_identical_capability_truth`);
P17-K adds `test_isolation_row_8_tenant_context_cannot_change_the_catalogue` and
`test_isolation_row_8_the_catalogue_query_has_no_tenant_predicate`. This work adds
two more: `test_two_real_tenants_receive_the_same_claim_under_the_attack`
(integration, real rows) and the identity-parametrised API item in which two
identity shapes receive a byte-identical serialised claim. Because selection is
now purely identity-anchored, the attack surface the defect opened — steering a
shared, tenant-free answer through a competing version's *attributes* — is closed
by construction.

**Boundary impact: none elsewhere.** No other endpoint, no extraction / mapping /
calculation path, no customer-factor precedence, no messaging and no Processing
Entity boundary is touched; no new privileged operation, no new role capability
and no new API route is introduced. This is a new-behaviour-*removing* change: it
can only turn a previously-wrong 200 into a correct 200 or a 503.

**Secrets and logging.** No credential, token, signed URL or DSN literal is added:
the new integration module reads its target from the environment
(`INTEGRATION_DATABASE_URL`, and the DSN behind the `NO_CATALOGUE_ENV` constant)
and verifies the target is disposable before use.

---


---

## 21. `DEF-1` closure matrix

| `DEF-1` claim (as reported) | Before | After | Evidence |
|---|---|---|---|
| A version with **one** governed-looking requirement code could win the catalogue election | `any(is_governed_requirement_code(...))` over candidates ordered `IN_FORCE` → `source_tier` → `version_label`, then `next(...)` | the candidate must carry the **complete** 18-identity set and **no** non-governed code; position never consulted | domain unit (18 single-code + 18 complete-minus-one + residue cases); API 3 hostile shapes; integration 7 attack items |
| Capability claims could be **silently upgraded** by a competitor | the competitor's partial rows were served as the catalogue | the adversary is rejected, the governed version is served, `GP-S3-CAT-01` stays `PARTIALLY_SUPPORTED`, and `1/0/0/0` is unreachable | API no-upgrade item; integration `test_a_one_code_competitor_offered_first_cannot_hijack_the_catalogue` |
| Ambiguity would resolve silently by ordering | the first plausible row won | **two** complete governed versions ⇒ `DisclosureViolation` ⇒ **503**, no version read, body says *ambiguous*, in both list orders | domain ambiguity cases; API ambiguity item; integration `test_a_complete_competitor_is_ambiguous_and_the_surface_fails_closed` |
| A missing catalogue could produce a partial claim | ordering could land on an unrelated version | no candidate ⇒ **503** stating *not provisioned*, `requested_version_ids == []` | API no-catalogue item; integration `test_a_database_without_the_catalogue_states_no_claim` |
| Ordering attributes could still steer selection | `status`, `source_tier`, `version_label` decided | 12 attribute-blind cases + 4 orderings; route source asserted free of the ordering words; SQL outer `ORDER BY` asserted a pure reproducibility key | domain blindness/order items; integration `test_the_shipped_order_by_is_not_a_precedence_rule` |
| The rule could be reintroduced positionally | — | the pre-fix predicate is asserted **absent** from the module and `next(...)` asserted absent, while the regression is proven to still reproduce `DEF-1` | domain structural guards; integration `test_the_shipped_route_selects_by_identity_not_by_position` + the `_legacy_rule_selection` replay |

Equally important is what did **not** change: **no schema change, no migration, no
new vocabulary, no RLS change, no authorization change, no API contract change,
no frontend change.** The governed `M-1` mapping and the `4 / 6 / 3 / 2` rollup are
untouched; `UPGRADED_ROLLUP` (`5 / 6 / 3 / 1`) exists only as a test fixture used
to prove the upgrade is unreachable.

---

## 22. Limitations and standing risks

1. **Author-verified, not independently verified.** This closure was implemented
   and verified by the same agent in this environment. No independent OHD/QA
   re-audit of the fixed surface has been performed. Status is therefore
   *IMPLEMENTED + TESTED*, **not** *ACCEPTED*; the recommended next step is an
   independent negative re-test of `GET /api/v3/capabilities` reproducing
   `DEF-1` against a disposable clone.
2. **Fail-closed is visible to callers.** A database holding **two** complete
   governed versions, or none at all, returns **503 for every caller** until an
   operator resolves it. That is the intended behaviour (no claim beats an
   unverified claim), but it is operationally noticeable, and this fix
   deliberately does **not** auto-resolve ambiguity — picking a winner would be a
   business decision, not an implementation one (§12).
3. **Pre-existing unrelated failures remain.** The same 9 failures in
   migration/ordering and review-SLA/extraction-suggestion modules occur with and
   without this patch (§18). They are out of scope here and remain open.
4. **No deployed end-to-end run.** Evidence is: domain unit, API-level ASGI
   in-process route calls, real-PostgreSQL integration, and the Jest frontend
   suite. No run against a long-lived server process plus a built frontend
   bundle was performed in this session.
5. **No persistent state was mutated.** The adversarial catalogue states exist
   only inside rolled-back transactions on disposable clones; the investor demo
   and persistent QA were not written to.
6. **No dependency, schema or configuration change.** Nothing was added to
   `requirements`, package manifests, environment templates or migrations, so
   there is no deployment step beyond shipping the three source files.
7. **Unpushed at report time.** The change is committed locally on
   `p8-release-reconciled` and **not pushed**; no PR has been opened.

---

## 23. Files, inventory and reproduction

### Production (modified — 3 files)

| File | Change |
|---|---|
| `backend/domain/capability_catalogue.py` | governed identity set + `is_governed_catalogue_version()` + `select_governed_catalogue_version()` (fail-closed, ambiguity-aware) |
| `backend/api/v3_disclosure.py` | `GET /capabilities` delegates selection to the domain selector; three `503` fail-closed branches; handler no longer reads any ordering attribute |
| `backend/data/disclosure.py` | candidate projection exposes `requirement_codes`; outer `ORDER BY` reduced to the reproducibility key `f.code, f.version_label, f.id` |

### Tests (new / modified)

| File | Items |
|---|---|
| `backend/tests/unit/domain/test_p17m2_governed_catalogue_identity.py` | new — 30 |
| `backend/tests/unit/api/test_p17m2_governed_catalogue_version_selection.py` | new — 10 |
| `backend/tests/integration/test_p17m2_governed_catalogue_selection_runtime.py` | new — 22 |
| `backend/tests/integration/test_p17l_capability_truth_surface_runtime.py` | modified — selection helper aligned to the identity rule (existing assertions unchanged) |
| `frontend/src/v3/__tests__/capability-truth-surface.test.jsx` | unchanged — re-run as regression evidence (19) |

### Documentation

`docs/architecture/CT-PO-P17-M2-FIX-GOVERNED-CATALOGUE-VERSION-SELECTION-20260926.md`
(this report).

### Reproduction

```bash
# unit (domain + API, no database)
cd backend && python -m pytest tests/unit/domain/test_p17m2_governed_catalogue_identity.py \
  tests/unit/api/test_p17m2_governed_catalogue_version_selection.py -q -rA

# integration — DISPOSABLE CLONE ONLY (F-046-1)
INTEGRATION_DATABASE_URL=postgresql://postgres:postgres@127.0.0.1:54426/ct_iv_p17m2_20260926 \
  python -m pytest tests/integration/test_p17m2_governed_catalogue_selection_runtime.py -q -rA

# surrounding regression
INTEGRATION_DATABASE_URL=… python -m pytest tests/integration/test_p17k_governed_capability_catalogue_runtime.py \
  tests/integration/test_p17l_capability_truth_surface_runtime.py -q

# frontend
cd frontend && npm test -- --ci capability-truth-surface
```

Environment used: interpreter `/home/shomonrobie/carbon_tally/backend/.venv`
(Python 3.14), suites launched with `cwd` inside the repository under test
(`/home/shomonrobie/ct_93d5cdd/backend` and `/home/shomonrobie/ct_93d5cdd/frontend`);
no dependency was installed or upgraded. Because the tests import
`domain.capability_catalogue` and call the new selector, importing the
*unpatched* tree would fail with `AttributeError` — so a green run also proves
the patched sources were the ones executed.

Observed: domain 30 passed · API 10 passed · integration 22 passed (`EXIT=0`) ·
focused unit batch 457 passed (`UNIT_EXIT=0`) · P17-K 24 + P17-L 37 passed
(`INT_EXIT=0`) · frontend 19 passed (`EXIT=0`).

---

## 24. Verdict

**`DEF-1` (P17-M2) — FIXED, and closed at four levels of evidence.**

| Dimension | State |
|---|---|
| Implemented | **Yes** — 3 production files; identity-anchored selection; ambiguity and absence both fail closed |
| Tested | **Yes** — 30 domain unit + 10 API + 22 real-DB integration (new), 457 focused unit + 24 P17-K + 37 P17-L regression, 19 frontend |
| Verified | **By the author**, on `41e6c61` + patch, in this environment; baseline comparison isolates the 9 unrelated pre-existing failures |
| Accepted | **Not claimed** — requires independent re-audit |
| Pushed | **No** — local commit on `p8-release-reconciled` only |

Residual work, in priority order:

1. Independent OHD/QA negative re-test of the `DEF-1` scenario on the fixed
   surface, plus the ambiguity and no-catalogue 503 paths.
2. Decide (PO/ops) how an ambiguous-catalogue state should be surfaced
   operationally and who resolves it; no automatic resolution is implemented.
3. Open tracking for the 9 pre-existing unrelated test failures if they are not
   already tracked.



