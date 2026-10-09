# CarbonTally — Public Website Feature List (Delta)

**Document ID:** `CT-PUBLIC-WEBSITE-FEATURE-LIST-20261003`
**Task ID:** `CT-FEATURE-DELTA-02-20261003-…-HEAD`
**Date:** 2026-10-03
**Status:** DOCUMENT_ONLY — publication candidates, gated
**Companion deliverables:** `CT-PO-CARBONTALLY-FEATURE-DELTA-CHANGELOG-20261003.md` (#1), `CT-BLOG-CANDIDATES-20261003.md` (#3), `CT-FAQ-ADDITIONS-20261003.md` (#4)

---

## 0. Purpose & publication discipline

This document proposes **public-facing feature list entries** for the CarbonTally marketing surface, derived strictly from the delta evidenced in deliverable #1. Nothing here is a commitment to publish; it is a **gated candidate set**.

Public claims carry a higher evidentiary bar than internal ones. The CarbonTally public website speaks to prospective customers, and per AGENTS §74/§85 an impressively-worded but unverified capability is worse than an unlisted capability.

### 0.1 The four publication gates

Every candidate must pass **all four** gates before it may be published.

| Gate | Name | Rule |
|---|---|---|
| **G1** | Truth gate | A claim may only be published if the feature is at least `IMPLEMENTED_AND_WIRED` at HEAD. `SCHEMA_ONLY`, `DOCUMENTED_ONLY`, `HISTORICAL_ONLY`, `CODE_ONLY`, `SUPERSEDED`, `DEPRECATED` and `UNKNOWN` features may **not** be published as live capabilities. |
| **G2** | Security gate | No claim may imply a security, isolation, compliance or certification property that is not enforced server-side and evidenced. Words such as "isolated", "secure", "compliant", "certified", "audited" require an explicit evidence token. The UI is not a security boundary (AGENTS §7, §44). |
| **G3** | PO-decision gate | Nothing that depends on an unresolved PO decision (POD-A…POD-J) may be published as definitive. Such items are `HOLD_G3`. |
| **G4** | Evidence gate | Every publishable claim must map to a baseline/new FTR id plus an evidence token (`BE:`/`DB:`/`MIG:`/`UI:`/`DOC:`). Unsourced copy is not publishable. |

### 0.2 Gate status legend

`READY` = passes all four gates, may be published now.
`HOLD_G1` = feature not yet at `IMPLEMENTED_AND_WIRED`.
`HOLD_G2` = security wording unsupported by evidence.
`HOLD_G3` = blocked by an open PO decision.
`HOLD_G4` = insufficient evidence token.

### 0.3 Standing caveat for every entry

> **Migrations unapplied / production unverified.** As of 2026-10-03 the release tree is 52 migrations ahead of every durable database and the production API returned HTTP 503. Every "new in the delta" capability below is `IMPLEMENTED_AND_WIRED` in the canonical tree but is **not `TESTED` or `VERIFIED`**. Public copy must therefore describe capabilities as available **from the current release**, not as "live in production today".

---

## 1. New capabilities to add to the public list (delta)

| # | Proposed public entry | Capability (plain language) | FTR | Gates | Status |
|---|---|---|---|---|---|
| P-01 | **Backup & restore you can see** | Scheduled backups with a verification step, a history view and a policy you control | FTR-355…359, 360, 361 | G1 ✓ · G2 ✓ · G3 ⚠ (POD-A) · G4 ✓ | `HOLD_G3` until production is live |
| P-02 | **Scheduled reporting** | Reports that generate on a schedule you set, not only on demand | FTR-362, 363 | G1 ✓ · G2 ✓ · G3 ✓ · G4 ✓ | `READY` (describe as "from current release") |
| P-03 | **Share a report** | Send a generated report to the right recipients without leaving the platform | FTR-364 | G1 ✓ · G2 ✓ · G3 ✓ · G4 ✓ | `READY` |
| P-04 | **Fast, safe large-file uploads** | Documents upload directly to secure storage with a central size/type gate | FTR-365…367 | G1 ✓ · G2 ⚠ ("secure") · G3 ✓ · G4 ✓ | `HOLD_G2` — replace "secure" with "encrypted in transit and scanned"; then `READY` |
| P-05 | **Storage you can measure** | See how much storage your organisation is using | FTR-368, 369 | G1 ✓ · G2 ✓ · G3 ✓ · G4 ✓ | `READY` |
| P-06 | **Document safety checks** | Incoming documents are screened, and orphaned files are cleaned up automatically | FTR-370, 371 | G1 ✓ · G2 ✓ · G3 ✓ · G4 ✓ | `READY` |
| P-07 | **More reliable notifications** | A provider-agnostic email layer so notifications keep flowing even if one provider has an issue | FTR-372 | G1 ✓ · G2 ✓ · G3 ✓ · G4 ✓ | `READY` |
| P-08 | **A stronger audit trail** | Audit records written so they cannot be quietly altered | FTR-373 | G1 ✓ · G2 ⚠ · G3 ⚠ (POD-E) · G4 ✓ | `HOLD_G2`/`HOLD_G3` — "cannot be altered" needs the hardening migration applied **and** the retention conflict (POD-E) resolved |

---

## 2. Upgraded capabilities — revised public wording

Where a baseline feature was already public, the delta justifies stronger (but still honest) wording.

| # | Feature | Baseline public wording (implied) | Proposed revised wording | Gates | Status |
|---|---|---|---|---|---|
| U-01 | Reporting | "Generate reports" | "Generate reports on demand **or on a schedule, and share them directly**" | G1 ✓ G2 ✓ G3 ✓ G4 ✓ | `READY` |
| U-02 | Documents | "Upload documents" | "Upload large documents with **direct-to-storage transfer and automatic screening**" | G1 ✓ G2 ⚠ (see P-04) G3 ✓ G4 ✓ | `HOLD_G2` |
| U-03 | Emission factors | "Use CarbonTally's factor library" | "Use CarbonTally's factor library, **with approved customer factors taking precedence and protected from accidental overwrite**" | G1 ✓ G2 ✓ G3 ✓ G4 ✓ | `READY` |
| U-04 | Audit | "Activity is logged" | "Activity is logged **with a hardened audit ledger**" | G1 ✓ G2 ⚠ G3 ⚠ (POD-E) G4 ✓ | `HOLD_G3` |
| U-05 | Notifications | "Email notifications" | "Email notifications **with provider redundancy**" | G1 ✓ G2 ✓ G3 ✓ G4 ✓ | `READY` |
| U-06 | Administration | "Configure your workspace" | "Configure your workspace **including backup policy and retention settings**" | G1 ✓ G2 ✓ G3 ⚠ (POD-E/G) G4 ✓ | `HOLD_G3` |

---

## 3. Items that must NOT be published (and why)

| Item | Reason | Gate |
|---|---|---|
| Any claim that backups/RLS hardening are **live in production** | Production returned HTTP 503; 52 migrations unapplied | G1 / standing caveat |
| "Cross-organisation data is provably isolated" | RLS remediation is `IMPLEMENTED`, not `TESTED`/`VERIFIED` (no negative-authz run) | G2 |
| "Locations" as a standalone master-data concept | `locations` table absent; POD-D open | G1 / G3 |
| "Role catalogue" / "roles management" | `roles` table has **0 rows**; POD-C open | G1 / G3 |
| "Accounting dimensions" as a configurable dimension framework | Realised as 10 columns, not a table; POD-B open | G1 / G3 |
| SEO/PWA capabilities | CAP-010 not individually catalogued; POD-J open | G1 / G4 |
| Persisted API runtime metrics (X7) | CAP-122 not individually catalogued; POD-J open | G1 / G4 |
| "1-day audit-log retention" (or any specific retention figure) | Conflicts with auditability expectations; POD-E open | G2 / G3 |

---

## 4. Recommended public-list ordering (business-first)

Following AGENTS §75 (business outcomes over implementation detail), the public list should lead with outcomes:

1. **Turn messy source data into defensible emissions numbers** (baseline core — unchanged)
2. **Trace every number back to its source** (provenance — unchanged)
3. **Review and approve before anything is reported** (workflow — unchanged)
4. **Scheduled reporting and report sharing** *(new — P-02, P-03)*
5. **Fast, screened document ingestion** *(new — P-04, P-06, U-02)*
6. **Storage visibility** *(new — P-05)*
7. **Reliable notifications** *(new — P-07, U-05)*
8. **Backup and restore** *(new — P-01, HOLD_G3)*
9. **A stronger audit trail** *(new — P-08, HOLD)*

---

## 5. Gate summary

| Status | Count | Items |
|---|---|---|
| `READY` | 8 | P-02, P-03, P-05, P-06, P-07, U-01, U-03, U-05 |
| `HOLD_G2` | 2 | P-04, U-02 |
| `HOLD_G3` | 2 (+2 with G2) | P-01, U-06; P-08 & U-04 |
| `NEVER (this delta)` | 8 | see §3 |

**Bottom line:** six genuinely new capabilities (scheduled reporting, report sharing, storage visibility, document screening, storage metering, notification redundancy) plus three wording upgrades are publishable **now** with careful phrasing. Backup and audit-hardening copy must wait for production verification and the POD decisions — publishing them early would violate G1/G3 and AGENTS §74.

<!--CTEOF-->
