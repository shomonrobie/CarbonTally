# SHARED EVIDENCE & FINDING CONTRACT
### The canonical data interchange between QA Harness and the Audit Swarm

**Status:** PROPOSAL v1 — for Product Owner review. No code changed.
**Scope:** Defines the shared machine-readable contracts that both
`saas-qa-harness` (deterministic) and `saas-audit-swarm` (AI-optional)
consume and emit, plus explicit compatibility mappings from the two current
CarbonTally implementations.

---

## 1. Design principles

1. **One schema, two producers.** Evidence and findings written by the QA
   Harness are read by the Audit Swarm without conversion beyond a thin
   file adapter.
2. **Versioned.** Every artifact carries `schema_version`. New fields are
   additive; removed fields are deprecated for two minor versions.
3. **Provenance-first.** Every finding cites evidence by
   `EvidenceReference` (id + sha256). Nothing may be "confirmed" without a
   referenced evidence record.
4. **Redacted by default.** All `data` payloads pass the shared redactor
   before serialization. Artifacts (screenshots/traces) are referenced, not
   embedded, and remain outside git.
5. **AI is labeled.** Findings produced by a model carry `ai_generated:
   true` and a `confidence`; they are never promoted to CONFIRMED by an
   automated path (see §6).

---

## 2. EvidencePacket (shared)

```jsonc
{
  "schema_version": "1.0",
  "evidence_id": "db_schema_1639121",
  "kind": "db",                       // enum, see below
  "source": "db_collector",           // producer module
  "run_id": "20260831T062613_1639121",
  "profile_id": "carbontally",
  "created_at": "2026-08-31T06:26:13Z",
  "sha256": "<hex of canonical data JSON>",
  "data": { /* redacted, JSON-serializable */ },
  "artifact": [                        // optional binary artifacts
    {
      "kind": "screenshot",
      "path": "screenshots/..._home_route.png",
      "sha256": "<hex>",
      "persona": "customer_owner",
      "viewport": "desktop-1440"
    }
  ]
}
```

### `kind` enum (additive)

| kind | producers | content |
|---|---|---|
| `db` | qa_harness `db/`, audit-swarm `db_collector` | schema/columns/indexes/constraints, RLS state+policies, integrity/orphan probes, migrations diff |
| `api` | qa_harness `api/`, audit-swarm `api_collector` | probe responses, OpenAPI, routes source, contract diff |
| `frontend` | audit-swarm `frontend_collector` | route/component map, API-call map, dead-UI candidates |
| `browser` | qa_harness `browser/`, audit-swarm `browser_driver` | page snapshots (safe dict), route protection, landing |
| `screenshot` | both | PNG artifact reference |
| `console` | both | console logs |
| `network` | both | failed requests / HAR |
| `trace` | both | Playwright trace reference |
| `workflow` | qa_harness `workflows/` | workflow execution transcript |
| `repo` | audit-swarm `fresh_start` | repository map (source files, blocked paths) |
| `runtime` | both | environment manifest (versions, URLs redacted) |
| `note` | both | explicit status notes (`db_unavailable`, `browser_unavailable`) |

### Adapter contract

The Audit Swarm reads QA Harness output through
`evidence/adapters/qa_harness.py`:

```
Input:  qa_harness evidence dir  (evidence/<kind>/<run>_<role>_<route>_<name>.json)
Output: List[EvidencePacket]
Rules:  filename tokens → run_id/role/route/name
        kind directory → packet.kind
        sha256 computed on redacted data
```

No change to qa_harness runtime format is required for the first release;
the adapter is additive.

---

## 3. Finding (shared)

```jsonc
{
  "schema_version": "1.0",
  "finding_id": "CT-DB-001",          // profile-scoped, deterministic
  "title": "…",
  "category": "database",             // enum §3.1
  "severity": "P1",                   // enum §3.2
  "confidence": "HIGH",               // HIGH | MEDIUM | LOW
  "classification": "CONFIRMED",      // enum §3.3
  "persona": "customer_owner",        // optional; profile identity id
  "location": "path | route | table | endpoint",
  "expected": "…",
  "actual": "…",
  "evidence": [ { "evidence_id": "…", "sha256": "…", "path": "…" } ],
  "reproduction": "…",
  "impact": "…",
  "recommendation": "…",
  "source_agent": "db_agent | run_db | …",
  "ai_generated": false,
  "status": "OPEN",                   // OPEN | FIXED | VERIFIED | …
  "created_at": "ISO-8601",
  "meta": {}
}
```

### 3.1 category (additive)

`database, api, frontend, ux, security, architecture, functionality,
performance, accessibility, reliability, messaging, reporting, compliance,
observability, other`

### 3.2 severity

| value | meaning |
|---|---|
| `P0` | security boundary break, data loss, total workflow block |
| `P1` | material workflow broken, major security/tenant risk |
| `P2` | degraded workflow, incorrect behaviour, notable UX break |
| `P3` | cosmetic / minor friction |
| `INFO` | observation, no defect claimed |

### 3.3 classification — unified vocabulary

| value | means | counts as defect? |
|---|---|---|
| `CONFIRMED` | deterministic evidence; re-verified | yes |
| `LIKELY` | strong evidence, one weak link | yes (priority 2) |
| `POSSIBLE` | plausible, evidence incomplete | review |
| `RE_VERIFY` | candidate; needs one confirming run | yes (on confirm) |
| `HARNESS_DEFECT` | the tool's own request was wrong | no |
| `HARNESS_RUNTIME_ERROR` | tooling failure (timeout, missing tool) | no |
| `AUTHENTICATION_FAILURE` | login/credential problem | no |
| `INCONCLUSIVE` | probe could not exercise intent | no |
| `SKIPPED` / `BLOCKED` | not run (tool unavailable / boundary) | no |
| `FALSE_POSITIVE` | disproven | no |
| `DUPLICATE` | merged into another finding | no |
| `PO_DECISION` | ambiguous requirement; product decision needed | no |
| `INSUFFICIENT_EVIDENCE` | cannot classify | no |

---

## 4. Supporting shared types

### RunContext
```
{ run_id, profile_id, environment, git_sha, read_only, started_at,
  ai_enabled, model_provider?, checkpoint? }
```

### EvidenceReference
```
{ evidence_id, sha256, path }        # path relative to the evidence root
```

### Persona / Identity
```
Identity { id, role, tenant, label, is_demo, credential_source }
CredentialSource { type: env|file|secret_manager, ref: "DATABASE_URL",
                   format: "dsn|password|token" }
```
**No passwords/keys in profiles.** Credential resolution happens at run time
(see `APPLICATION_PROFILE_SPEC.md` §5 and `STANDALONE_ARCHITECTURE.md` §7).

### Report (shared envelope)
```
Report { schema_version, run_id, profile_id, generated_at,
         summary, counts {by_severity, by_classification},
         sections: [ {title, kind, findings:[finding_id]} ],
         verdict?  # acceptance verdict (harness) — optional for swarm
       }
```
The Audit Swarm may add analysis sections; the harness may add the verdict.
Prose renderers (Markdown) are per-tool.

---

## 5. Compatibility mapping (existing V1.2/V1 data)

| current qa_harness | current audit-swarm | unified |
|---|---|---|
| `REAL` / `APPLICATION_DEFECT` | `CONFIRMED` | `CONFIRMED` |
| `RE-VERIFY` | `LIKELY`/`POSSIBLE` | `RE_VERIFY` (swarm maps RE_VERIFY→LIKELY when evidence strong) |
| `HARNESS_CONTRACT_DEFECT` | — | `HARNESS_DEFECT` |
| `HARNESS_RUNTIME_ERROR` | `HARNESS_RUNTIME_ERROR` | `HARNESS_RUNTIME_ERROR` |
| `INCONCLUSIVE` | `INSUFFICIENT_EVIDENCE` | `INCONCLUSIVE` |
| `SKIPPED`/`BLOCKED` | `SKIPPED`/`BLOCKED` | `SKIPPED`/`BLOCKED` |
| `PO_DECISION_REQUIRED` | `PO_DECISION` | `PO_DECISION` |
| `AUTHENTICATION_FAILURE` | — | `AUTHENTICATION_FAILURE` |
| — | `FALSE_POSITIVE` | `FALSE_POSITIVE` |
| — | `DUPLICATE` | `DUPLICATE` |
| severity `P0..P3` | severity `P0..P3, INFO` | `P0..P3, INFO` |
| categories `DB/RLS/API/AUTH/WF/UI/UX/SEC/A11Y` | categories `database/…` | unified enum (RLS→database; AUTH→security; A11Y→accessibility; WF→functionality) |

A `MAPPING.md` inside the contracts package will document and unit-test this
table; `normalize.py` (audit-swarm) and the qa_harness finding store each
gain a `to_unified()` that applies it.

---

## 6. AI findings policy (non-negotiable)

1. `ai_generated=true` is mandatory on any model-produced finding.
2. An AI finding's `classification` may be `LIKELY`, `POSSIBLE`, or
   `INSUFFICIENT_EVIDENCE` at most; **never `CONFIRMED`** from the model.
3. Promotion to `CONFIRMED` requires: (a) a cited EvidencePacket, and
   (b) either a deterministic re-probe or explicit human/PO confirmation.
4. The Cross-check stage may *downgrade* classifications; it may not
   upgrade AI findings automatically.

---

*End of SHARED_EVIDENCE_FINDING_CONTRACT.md. See APPLICATION_PROFILE_SPEC.md
for the profile schema and STANDALONE_ARCHITECTURE.md for the pipeline.*
