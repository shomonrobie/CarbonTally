# CarbonTally WS4 — Gate 5 — T2 Implementation Report
**Task T2: runtime attribution facts (provider-label helper) in `infra/ai_runtime.py`**

- **Date:** 4 September 2026
- **Git HEAD (verified):** `1639121` — nothing committed or pushed.
- **Accepted design:** `docs/architecture/CARBONTALLY_WS4_GATE5_DESIGN_READINESS_REPORT.md`
  (verdict **GATE 5 IMPLEMENTATION READY**).
- **Predecessor task:** **T1 — COMPLETE / ACCEPTED** (schema columns
  `automation_provider` / `automation_model` / `automation_model_version` added
  to `document_processing_queue` by migration
  `20260905010000_gate5_t1_automation_provenance.sql`).
- **Gate 4:** PASSED/ACCEPTED — not reopened, not modified. **Gate 5 has NOT
  passed.**

---

## 1. Exact T2 task executed

T2 from the accepted design report's implementation work breakdown (item 2):

> **T2 — Runtime attribution facts.** `infra/ai_runtime.py` provider-label helper
> (host-derived) exposing provider/model (and optional version) without secrets;
> unit test.

Executed exactly (no reinterpretation, no expansion):

1. **`backend/infra/ai_runtime.py`** — added, purely additively:
   - `provider_label(base_url)` — a pure, host-derived provider-label helper.
     Well-known OpenAI/Anthropic-compatible endpoint domains map to canonical
     short labels (`openai.com` → `openai`, `anthropic.com` → `anthropic`,
     `openrouter.ai` → `openrouter`); any other/custom gateway host returns the
     endpoint hostname itself (capped at the 120-char
     `automation_provider` column length). Never fabricates a canonical name
     (design risk R1).
   - `_host_of(base_url)` — internal URL-host parser (scheme-less input accepted;
     port ignored; blank/malformed → `None`).
   - `configured_ai_attribution(model_version=None)` — exposes the configured
     runtime attribution facts `{"provider", "model", "model_version"}`. Reads
     only the **identity** environment variables
     (`CARBONTALLY_AI_BASE_URL`, `CARBONTALLY_AI_MODEL`); the API key is
     intentionally never read. `model_version` stays `None` unless truthfully
     supplied — never fabricated/guessed from the model id (design risk R2).
     Unconfigured runtime → all `None`.
   - Module docstring updated to document the T2 helpers. **No config additions,
     no secrets, no new dependencies.**
2. **`backend/tests/unit/infra/test_ai_runtime.py`** — new focused unit test file
   (15 tests) covering `provider_label` (known hosts, subdomains, scheme-less,
   port, unknown-host fallback, blank/None) and `configured_ai_attribution`
   (not-configured → all None; configured identity; **secret never present in
   the result even when `CARBONTALLY_AI_API_KEY` is set**; unknown-gateway host
   fallback; explicit truthfully-known `model_version`; blank version → None).
3. No database, migration, API, worker, or service change was made (those belong
   to T3–T8).

---

## 2. Files changed

| File | Change |
|---|---|
| `backend/infra/ai_runtime.py` | **Modified** (additive) — `provider_label`, `_host_of`, `configured_ai_attribution`, provider-domain constants, docstring. |
| `backend/tests/unit/infra/test_ai_runtime.py` | **New** — 15 focused unit tests for the T2 helpers. |
| `docs/architecture/CARBONTALLY_WS4_GATE5_T2_REPORT.md` | **New** — this report (required deliverable). |

Note: `backend/infra/ai_runtime.py` is **untracked** in the current git snapshot
(pre-existing repository state — the file existed and was read before this task;
T2 only edited it). No file was committed or staged.

---

## 3. Migrations

**None.** T2 is a pure Python helper addition with unit tests; the T1 migration
is already applied and accepted and was not touched.

---

## 4. Tests executed

Focused verification for T2 only — no Gate-5 acceptance matrix, no database
tests:

1. `pytest tests/unit/infra/test_ai_runtime.py` (15 new tests).
2. `pytest tests/unit/infra/` (full infra unit directory — regression assurance
   for the modified module area).

---

## 5. Results

| Test run | Result |
|---|---|
| `tests/unit/infra/test_ai_runtime.py` | **15 passed** in 0.09s (exit 0) |
| `tests/unit/infra/` (full infra unit suite) | **all passed** (86 collected, exit 0) |

Key assertions exercised and green:
- `provider_label("https://api.openai.com/v1") == "openai"` (and anthropic /
  openrouter equivalents; subdomain; scheme-less; port variants).
- Unknown gateway `https://llm-gw.example.test/v1` → host-derived label
  `"llm-gw.example.test"` (truthful fallback, never fabricated).
- `configured_ai_attribution()` returns all-`None` when unconfigured, or with
  only one of base-url/model present.
- With `CARBONTALLY_AI_API_KEY=sk-super-secret-value` set in the environment,
  the returned facts contain **no** key material and no `api_key` key.
- `model_version` is `None` by default and only set when truthfully supplied;
  blank → `None`.

---

## 6. Data-integrity impact

**None.** T2 changes no data, no schema, and no state. No demo/investor rows were
read or mutated; no fixture was required (pure functions + env). No before/after
database counts apply (no database interaction).

---

## 7. Security impact

- The API key is never read by the new code and cannot appear in the returned
  facts (unit-asserted). The module still never logs or persists credentials.
- No database/RLS/API/authorization surface was touched; no new endpoint, no new
  role, no new principal. The machine actor label `automatic_pipeline` is **not**
  introduced by T2 (it belongs to the T4 audit-event work) and nothing in T2 can
  make an automated execution a user/PE member/D38 assignee/authorization
  principal.
- Provider/model identity strings carry no secrets.

---

## 8. Confirmation: T3–T8 were not executed

Confirmed. This session performed **T2 only**. No worker/service capture (T3),
no extraction audit event (T4), no API payload change (T5), no write-once guard
trigger/tests (T6), no full regression suite (T7), and no Gate-5 fixture /
acceptance run (T8) were performed. Nothing was committed or pushed.

---

## 9. Remaining Gate 5 work

Per the accepted design report (§12), after T2 the following remain:

- **T3** — Capture in the worker path (persist the write-once block on the
  extraction→mapping advance; attempted-model truthfulness in AI-failure
  envelopes).
- **T4** — Extraction audit event (`automatic_processing:extracted`, machine
  actor `automatic_pipeline`).
- **T5** — API surface (`automation` block in `_job_payload`).
- **T6** — Write-once hardening (DB guard trigger + immutability tests) —
  deferred from T1 by design.
- **T7** — Full regression suite (unit + API positive/negative).
- **T8** — Verification-only Gate-5 fixture run + acceptance evidence.

**Gate 5 is NOT passed** and no acceptance claim is made by this report.

---

## 10. Blockers discovered

**None.** No architecture decision beyond the accepted design was required; T2
introduces no conflict with Gate 4 or the frozen architecture. No data-safety
concern arose.

---

## FINAL VERDICT

**T2 COMPLETE**

Gate 5 has **not** been executed or passed. Nothing was committed or pushed.

