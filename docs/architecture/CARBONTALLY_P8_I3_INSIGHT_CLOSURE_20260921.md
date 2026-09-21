# CarbonTally — PO I3 Closure Record

**Workstream:** CarbonTally Insight — I3 Controlled Read-Only Tools  
**Phase:** Phase 8  
**Status:** **CLOSED — VERIFIED PASS**  
**Verified application/remediation revision:** `651f8c1aa60c635ec1e4da482cfcd651d6657fe8` (`651f8c1`)  
**OHD verification:** `PASS — I3 REMEDIATION VERIFIED`  
**OHD verification report commit:** `7faaa57`  
**Branch:** `p8-release-reconciled`  
**Closure authority:** Product Owner (PO)  
**Closure date:** 2026-09-21

---

## 1. PO Closure Decision

**PO DECISION: I3 IS CLOSED.**

I3 — CarbonTally Insight Controlled Read-Only Tools — is formally closed as:

> **I3 CLOSED — VERIFIED PASS at `651f8c1`.**

The closure is based on the independent OHD re-verification of the I3 remediation.

OHD's final verdict was:

> **PASS — I3 REMEDIATION VERIFIED**

The OHD report was committed as `7faaa57`. That commit contains verification evidence only and does not change the verified application revision.

---

## 2. Scope Closed

The closed I3 scope is the PO-ratified controlled read-only tool catalogue:

1. `report_lookup`
2. `report_version_lookup`
3. `report_evidence_lookup`
4. `calculation_snapshot_lookup`

The closed scope includes:

- closed/allowlisted tool registry;
- validated tool inputs;
- current I2 authorization;
- resolved-object organization re-check;
- bounded structured results;
- deterministic execution;
- explicit result/error statuses;
- reference/locator semantics;
- field allowlists;
- read-only behaviour;
- real repository wiring;
- HTTP-path execution;
- no arbitrary SQL;
- no mutation;
- no LLM/provider dependency.

---

## 3. OHD Remediation Verification

OHD independently verified the two previously blocking I3 defects.

### D-01 — Real `report_evidence_lookup` wiring

**RESOLVED AND VERIFIED.**

OHD exercised the real `get_repositories()` factory rather than a test-injected attribute.

Verified:

- `RepositoryBundle` contains `disclosure_projection`;
- it is a `DisclosureProjectionRepository`;
- all required read methods exist;
- `report_evidence_lookup` succeeds through the real HTTP path against real rows;
- success/no-data/not-authorized semantics are correct;
- cross-scope and suspended-organization access are denied;
- malformed input fails closed;
- reference re-resolution respects revocation and restoration;
- no write path was introduced;
- table counts remained unchanged.

OHD also proved the new wiring tests are sensitive by showing their assertions fail against the pre-remediation source and pass after remediation.

### D-02 — Circular import

**RESOLVED AND VERIFIED.**

OHD independently confirmed that:

- `services.insight_tools`;
- `api.router`;
- `api.v3_insight_tools`;
- `main`

can load independently without the previous service→API module-load cycle.

Runtime delegation to the I2 authorization boundary remains intact.

---

## 4. Verification Results

### I3 + wiring

**35 collected / 35 passed / 0 failed**

### Focused I1/I2 + Insight

**63 / 63 passed**

This included live RLS coverage.

### Full unit suite

**2,889 collected / 2,877 passed / 4 failed / 0 errors / 8 skipped**

OHD compared the results against the pre-remediation run and confirmed the failure set was unchanged.

The four failures were independently classified as pre-existing and unrelated to the I3 remediation:

- three route-enumeration failures associated with the FastAPI version's lazy `_IncludedRouter`;
- one migration-count failure (`71` versus `77`) with zero migrations added by the I3 line.

These failures do not block I3 closure.

---

## 5. Integrity Verification

OHD verified:

- I1/I2 application integrity against `177dff5`;
- Insight migrations unchanged;
- five I1/I2 verification suites unchanged;
- zero migrations introduced across the I3 line;
- remediation footprint matched the declared five-file set;
- working tree clean;
- `github/p8-release-reconciled` aligned with the target;
- no unrelated application changes.

The remediation also made the explicitly recorded additive changes to shared `backend/api/dependencies.py` required to provide the real `disclosure_projection` repository dependency.

---

## 6. I2 Boundary Reconfirmed

OHD re-ran the material authorization matrix, including:

- owner;
- admin;
- member;
- viewer;
- consultant with and without grant;
- staff with and without permission;
- auditor persona;
- non-member;
- forged-role variants;
- cross-organization;
- PE denial;
- anonymous access;
- revocation;
- restoration.

Authorization was re-evaluated on every protected read.

No I2 regression was identified.

---

## 7. I4–I8 Boundary

No I4–I8 functionality was introduced.

Specifically, this closure does not authorize or include:

- LLM/provider integration;
- RAG;
- embeddings;
- LangChain;
- canonical AI interaction persistence;
- canonical AI audit persistence;
- context orchestration;
- Insight UI;
- retention;
- export;
- billing;
- autonomous/consequential actions;
- additional tools;
- additional personas;
- new permissions.

The `invocation` record remains response-only and is not an I4 canonical interaction record.

---

## 8. Non-Blocking Observations

The following remain recorded for future work and do not block I3 closure:

- foreign versus absent identifiers continue to distinguish `not_authorized` from `no_data`;
- the original test suite retains some duck-typed repository-bundle patterns, now bounded by the real-wiring tests;
- server-side log lines can contain the offending parameter value and must remain subject to future logging/privacy policy;
- the deferred `authorize_insight_scope` import remains inside `_authorize()` rather than at module level.

No remediation is authorized under this closure unless separately approved.

---

## 9. Master Specification State

The consolidated Master Specification is updated to:

**`CARBONTALLY_PHASE8_INSIGHT_MASTER_SPECIFICATION_v1.1_20260921.md`**

It records:

> **I3 CLOSED — VERIFIED PASS**

at `651f8c1`, with OHD verification report `7faaa57`.

The Master Specification remains a product/architecture/control reference. It does not itself authorize I4–I8.

---

## 10. Final PO Status

| Stage | Status |
|---|---|
| D1 | **COMPLETE** |
| D2 | **RATIFIED** |
| I1 | **IMPLEMENTED / VERIFIED BASELINE** |
| I2 | **CLOSED — VERIFIED PASS** |
| I3 | **CLOSED — VERIFIED PASS** |
| I4 | **NOT AUTHORIZED** |
| I5 | **NOT AUTHORIZED** |
| I6 | **NOT AUTHORIZED** |
| I7 | **NOT AUTHORIZED** |
| I8 | **NOT AUTHORIZED** |

### Final decision

> **I3 CLOSED — VERIFIED PASS at `651f8c1`.**
>
> **OHD independent verification: PASS.**
>
> **OHD report: `7faaa57`.**
>
> **No blocking I3 findings remain.**
>
> **I4–I8 remain NOT AUTHORIZED.**
>
> **A separate PO decision is required before I4 implementation begins.**

**PO closure state: CLOSED.**
