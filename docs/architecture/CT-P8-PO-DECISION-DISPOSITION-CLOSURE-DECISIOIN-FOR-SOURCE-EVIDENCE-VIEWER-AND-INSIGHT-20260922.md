# CarbonTally — Phase 8

## Source Evidence Viewer + Insight Evidence Navigation

### PO Disposition & Closure Decision

**Date:** 2026-09-22

---

# 1. PO Decision

## DECISION: ACCEPT THE VERIFIED IMPLEMENTATION AND CLOSE THE SOURCE EVIDENCE VIEWER STAGE

**Status: CLOSED — VERIFIED PASS WITH NON-BLOCKING OBSERVATIONS**

The PO accepts the independent OHD verification result:

**`PASS WITH NON-BLOCKING OBSERVATIONS`**

for:

**Shared Source Evidence Viewer + Insight Evidence Navigation**

Verification ID:

`OHD-P8-SEV-20260922`

The implementation was independently verified at the authoritative release state and no acceptance-blocking defect was identified.

The PO therefore closes this capability.

---

# 2. Important governance decision

The PO explicitly decides:

> **No code remediation is authorized as a condition of this closure.**

In particular, this closure does **not** authorize Cline to modify:

* `source_item.file_url`;
* the customer signed-URL route;
* export/reporting;
* DM-6 globally;
* I2 authorization semantics;
* the I3 tool catalogue;
* historical data;
* database schema;
* migrations;
* retention;
* deletion;
* billing;
* metering;
* production deployment.

Any future implementation addressing these subjects requires a separate PO authorization.

This decision follows the Phase 8 governance rule that an OHD observation does not itself authorize implementation. The inventory explicitly records that C-01/C-02/C-03 are PO decisions and that C-06 is the governing closure decision.

---

# 3. Basis for closure

The repository decision inventory records:

* I6: **CLOSED — VERIFIED PASS**
* Shared Source Evidence Viewer + Insight evidence handoff: **VERIFIED — NOT PO-CLOSED**
* implementation: `999e4fb`
* independent OHD verification: `5d5f7ed`
* OHD verdict: **PASS WITH NON-BLOCKING OBSERVATIONS**
* C-06: **the governing next step for the only open stage**.

The OHD report did not identify an acceptance-blocking defect.

The inventory further records that C-01 is explicitly **not acceptance-blocking**, and C-02 and C-03 are also non-blocking for the viewer.

Therefore the PO is not required to introduce implementation changes merely to obtain closure.

---

# 4. C-01 — `source_item.file_url` below FULL

## PO decision: RATIFY CURRENT BEHAVIOUR FOR THIS RELEASE

The PO acknowledges the security observation:

`source_item.file_url` remains present below FULL even though other document-reference fields are withheld.

The PO does **not** authorize changing this behaviour as part of the current Source Evidence Viewer closure.

### Rationale

The inventory establishes that:

* the issue was verified at the current HEAD;
* OHD classified it as non-blocking;
* the OHD report offered ratification or correction as alternatives;
* no correction is currently authorized;
* changing it would alter an existing response contract and therefore requires explicit authorization.

The PO nevertheless records this as a **security-sensitive policy inconsistency**, not as a declaration that exposing the pointer is intrinsically desirable.

### Security posture

For this release:

> `source_item.file_url` is treated as an existing document-management/storage pointer whose exposure is retained by explicit PO ratification.

This ratification must **not** be interpreted as authorization to expose:

* signed URLs;
* storage credentials;
* tokens;
* unrestricted document content;
* additional storage paths;
* additional metadata.

The existing DM-6 evidence projection remains otherwise unchanged.

### Future policy

A future PO decision may determine that document/storage pointers must also be withheld below FULL.

If that decision is made, it must be separately authorized, implemented and independently verified.

---

# 5. C-02 — Customer signed-URL route outside DM-6

## PO decision: DEFER — SECURITY POLICY REVIEW

The PO does **not** modify:

`GET /api/v3/documents/{file_id}/signed-url`

as part of this closure.

The inventory confirms that this route currently relies on the existing organization-member authorization rather than the evidence-viewer's DM-6 depth policy. It also explicitly characterizes this as a larger policy question requiring a PO decision.

### PO determination

This is not silently ratified as a permanent security design.

It is recorded as:

**DEFERRED — SECURITY/POLICY DECISION REQUIRED**

The future decision must determine whether:

1. document-management access and evidence-disclosure access intentionally have different authorization models; or
2. the DM-6 evidence-depth model should become a broader document-reference policy.

No implementation may be inferred from this deferral.

---

# 6. C-03 — Export/reporting completeness inference

## PO decision: DEFER — AUDIT/PROVENANCE POLICY

The PO accepts the Source Evidence Viewer correction distinguishing:

* authoritative `source_page`;
* historical/unverified page information;
* unavailable source location.

The PO does **not** authorize changes to existing exports/reporting as part of this closure.

The inventory confirms that the remaining export/reporting inference is outside the viewer change footprint and is a pre-existing residual.

### Future policy requirement

The future PO decision must determine whether the platform should enforce a uniform rule that:

> `source_page IS NOT NULL` must not, by itself, establish evidence completeness.

Any future implementation must consider:

* historical data;
* exports;
* reporting;
* reviewer-facing displays;
* provenance semantics;
* I7 export policy.

No historical data rewriting is authorized by this decision.

---

# 7. C-04 — Foreign-organization identifiers

## PO decision: ACCEPT CURRENT PLATFORM CONVENTION

The existing 403/404 distinction is accepted for this release.

No remediation is authorized.

The inventory classifies this as a low-severity, non-blocking observation and notes that the UI collapses failure states into a non-disclosing experience.

A future platform-wide non-disclosure policy may revisit this independently.

---

# 8. C-05 — `raw_description` at CONTROLLED depth

## PO decision: RATIFY CURRENT BEHAVIOUR

The PO ratifies the current withholding of `raw_description` at CONTROLLED depth.

This is accepted as the current allowlist behaviour.

No implementation change is authorized.

The PO considers the narrower disclosure posture preferable to unintentionally exposing additional source text. Any future change must be an explicit policy decision.

---

# 9. C-06 — Source Evidence Viewer closure

## PO decision: CLOSED

The PO formally closes:

**Shared Source Evidence Viewer + Insight Evidence Navigation**

with the following final state:

**IMPLEMENTED**

→ **INDEPENDENTLY VERIFIED**

→ **PASS WITH NON-BLOCKING OBSERVATIONS**

→ **PO ACCEPTED**

→ **CLOSED**

The accepted observations are not implementation blockers.

---

# 10. What this closure accepts

The PO accepts the implemented capability including:

* shared Source Evidence Viewer;
* customer evidence access;
* Insight evidence handoff;
* bounded evidence-line resolution;
* per-request authorization;
* organization isolation;
* DM-6 evidence-depth enforcement as implemented;
* signed-document exposure restricted according to the implemented evidence policy;
* honest handling of authoritative vs unavailable/unverified source locations;
* `page_count` not being treated as an authoritative `source_page` in the corrected write path;
* read-only evidence presentation;
* no new I3 tool;
* no I3 contract change;
* no retention/erasure implementation;
* no billing/metering implementation;
* no historical-data rewrite;
* no production deployment.

The inventory records these capabilities and the implemented scope.

---

# 11. What this closure does NOT decide

The following remain unresolved and explicitly deferred:

### Security / document policy

* C-01 future treatment of `source_item.file_url`;
* C-02 platform-wide relationship between DM-6 and document signed URLs.

### Audit / provenance

* C-03 uniform export/reporting interpretation of historical `source_page`.

### Product capability

* C-08 date/amount evidence discovery;
* C-09 future I3/evidence-line-item resolvability;
* C-10 consultant/internal-staff Insight;
* C-11 `org_viewer` execution rights;
* C-12 pagination.

### I7

* C-13 retention durations;
* C-14 deletion semantics;
* C-15 export policy;
* C-16 provider/privacy decisions;
* C-17 I7 acceptance criteria.

### I8

* C-18 commercial/billing policy;
* C-19 SLOs;
* C-20 backup/recovery;
* C-21 incident/runbook;
* C-22 payment-provider determination;
* C-23 I8 acceptance criteria;
* C-24 evidence-viewing commercial posture.

The inventory records these as unresolved/not authorized and explicitly states that they must not be inferred into implementation.

---

# 12. I6 status

This closure does **not** reopen I6.

The authoritative inventory records:

**I6 UI — CLOSED — VERIFIED PASS**

with:

* implementation `09e2315`;
* OHD verification `4acc249`;
* PO closure `67d399f`.

The Source Evidence Viewer is a subsequent shared capability that integrates with the already-closed Insight UI.

Therefore:

> **CarbonTally Insight I6 is finished and closed.**

The Source Evidence Viewer closure does not represent unfinished I6 implementation.

---

# 13. I7 status

**I7 remains NOT AUTHORIZED / NOT READY.**

The PO does not authorize I7 implementation through this closure.

Before I7 can be authorized, the following must be decided:

* retention periods;
* deletion semantics;
* legal hold;
* export policy;
* provider/privacy requirements;
* I7 acceptance criteria.

The inventory explicitly classifies I7 as `NOT READY`, rather than merely awaiting implementation.

Therefore:

**No Cline I7 implementation prompt is authorized by this decision.**

---

# 14. I8 status

**I8 remains NOT AUTHORIZED AS A FULL STAGE.**

The already-approved I8-A principles remain intact:

* rate limiting;
* observability;
* provider resilience;
* deployment discipline.

But the full I8 implementation still requires decisions concerning:

* commercial/billing policy;
* usage and entitlements;
* SLOs;
* backup/recovery;
* incident/runbook;
* payment-provider facts;
* acceptance criteria.

The inventory explicitly records these prerequisites.

Therefore:

**No full I8 implementation is authorized by this decision.**

---

# 15. Production deployment

**NOT AUTHORIZED.**

This closure is an application/capability acceptance decision only.

The mandatory release chain remains:

**PO authorization → implementation → OHD verification → PO closure → controlled deployment authorization → deployment → post-deployment verification**

No production deployment follows automatically from this closure.

---

# 16. Immediate next action

There is **no Cline implementation task created by this PO decision**.

The next action is **governance/documentation only**:

1. Record this PO closure decision durably in the authoritative repository.
2. Reconcile the Phase 8 Master Specification/status records as separately authorized documentation work if the PO chooses to do so.
3. Update the Phase 8 master handover/status record.
4. Only then prepare the next PO decision package.

No application code should change as a result of this closure.

---

# 17. Final status table

| Area                                  | PO status                                                         |
| ------------------------------------- | ----------------------------------------------------------------- |
| I1                                    | **CLOSED / VERIFIED BASELINE**                                    |
| I2                                    | **CLOSED / VERIFIED PASS**                                        |
| I3                                    | **CLOSED / VERIFIED PASS**                                        |
| I4                                    | **CLOSED / VERIFIED PASS**                                        |
| I5                                    | **CLOSED / VERIFIED PASS**                                        |
| I6                                    | **CLOSED / VERIFIED PASS**                                        |
| Source Evidence Viewer                | **CLOSED / VERIFIED PASS WITH NON-BLOCKING OBSERVATIONS**         |
| C-01                                  | **RATIFIED FOR CURRENT RELEASE; FUTURE SECURITY REVIEW DEFERRED** |
| C-02                                  | **DEFERRED — SECURITY POLICY**                                    |
| C-03                                  | **DEFERRED — AUDIT/PROVENANCE POLICY**                            |
| C-04                                  | **ACCEPTED**                                                      |
| C-05                                  | **RATIFIED**                                                      |
| I7                                    | **NOT AUTHORIZED / NOT READY**                                    |
| I8                                    | **NOT AUTHORIZED AS FULL STAGE**                                  |
| Production deployment                 | **NOT AUTHORIZED**                                                |
| New implementation from this decision | **NONE**                                                          |

---

# 18. Governing PO principle

For this capability, the PO adopts the following rule:

> **A non-blocking security or audit observation does not automatically authorize remediation, and accepting a current implementation does not mean that every surrounding policy question has been permanently resolved.**

The distinction is intentional:

**Current capability:** accepted and closed.

**Security-policy questions:** explicitly recorded for future decision.

**Audit/provenance questions:** explicitly recorded for future decision.

**New implementation:** requires new authorization.

This preserves both security governance and implementation discipline without reopening already verified work.

