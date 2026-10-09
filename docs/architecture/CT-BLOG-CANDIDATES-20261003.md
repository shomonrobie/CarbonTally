# CarbonTally — Blog Candidates (Delta)

**Document ID:** `CT-BLOG-CANDIDATES-20261003`
**Task ID:** `CT-FEATURE-DELTA-02-20261003-…-HEAD`
**Date:** 2026-10-03
**Status:** DOCUMENT_ONLY — editorial candidates, gated
**Companion deliverables:** `CT-PO-CARBONTALLY-FEATURE-DELTA-CHANGELOG-20261003.md` (#1), `CT-PUBLIC-WEBSITE-FEATURE-LIST-20261003.md` (#2), `CT-FAQ-ADDITIONS-20261003.md` (#4)
**Prior convention:** `docs/architecture/CARBONTALLY_BLOG_CMS_DECISIONS.md`

---

## 0. Editorial rules

Blog copy is public copy. It therefore inherits the same four gates as the public feature list:

| Gate | Rule applied to blog copy |
|---|---|
| **G1** | Only describe shipped capability; never write a post that presents an `IMPLEMENTED_AND_WIRED`-but-unverified or unapplied feature as live |
| **G2** | No unsupported security/compliance claims; no implied certification |
| **G3** | No post may resolve or pre-empt an open PO decision (POD-A…POD-J) |
| **G4** | Every technical claim must be traceable to an FTR + evidence token |

Each candidate carries: **angle**, **audience**, **evidence anchors**, **gate status**, and a **safe-claims / do-not-say** pair. A post is publishable only in the `READY` state.

`EDITORIAL CAVEAT:` No candidate may state that a delta capability is running in production. Production returned HTTP 503 on 2026-10-03 and 52 migrations are unapplied.

## 1. Candidate register

| ID | Working title | Angle | Audience | Evidence anchors | Gate status |
|---|---|---|---|---|---|
| B-01 | *Reporting that runs itself* | Why emissions reporting should be scheduled, not remembered | Sustainability managers | FTR-362, 363, `MIG:ct02_scheduled_reporting` | `READY` |
| B-02 | *From report to recipient* | Sharing a verified report without emailing spreadsheets around | Consultants, clients | FTR-364, `MIG:ct02_report_sharing` | `READY` |
| B-03 | *Why we rebuilt document upload* | Direct-to-storage transfer, one upload gate, screening on the way in | Ops leads, IT | FTR-365…367, 370, `BE:v3_document_uploads.py` | `HOLD_G2` (see §2.1 wording) |
| B-04 | *Know what you're storing* | Making storage usage visible per organisation | Finance, IT | FTR-368, 369, `MIG:bucket_size_limit` | `READY` |
| B-05 | *Email you can rely on* | Provider-agnostic notification delivery | IT, ops | FTR-372, `BE:email_provider.py` | `READY` |
| B-06 | *Backups you can prove* | The difference between "we back up" and "we can prove we back up and restore" | CTOs, risk | FTR-355…359, `DOC:CARBONTALLY_PRODUCTION_BACKUP_RESTORE_COMPLETE_IMPLEMENTATION_20261002` | `HOLD_G3` (POD-A/POD-I) |
| B-07 | *A tamper-evident audit trail* | Why audit records need integrity guarantees | Risk, auditors | FTR-373, `MIG:ct02_audit_ledger_hardening` | `HOLD_G3` (POD-E) |
| B-08 | *Customer factors come first* | How approved customer-specific factors take precedence safely | Sustainability leads | FTR-136…138, 144–145, `DOC:CT-IMPLEMENT-04-…FACTOR-READ-REPOINT` | `READY` |
| B-09 | *Inside a release: how CarbonTally ships* | Transparency post on the p8-release-reconciled line, code-first/database-last, and why we stage migrations | Technical, trust-building | `GIT:cb70fd6..HEAD`, `MIG` ledger 46/98 | `HOLD_G3` — sensitive; requires PO approval on disclosure |

---

## 2. Draft guidance per candidate

### 2.1 B-03 — "Why we rebuilt document upload" (the one wording trap)

**Safe claims:** documents now transfer directly to storage via a short-lived signed upload URL; a single central gate enforces size and type limits; incoming files pass a security-screening step; orphaned files are reclaimed.

**Do not say:** "secure uploads", "completely safe", "certified", "no file can ever be malicious", or anything implying the signed URL itself is an authorisation boundary. Per AGENTS §68 a signed URL is sensitive and authorisation must occur before it is issued.

**Gate:** move to `READY` once the draft uses the safe phrasing in §2.1.

### 2.2 B-06 — "Backups you can prove"

**Safe claims (technical, non-teaser):** the release includes backup job orchestration, a policy surface, an explicit verification step and a backup-set registry; restore drills are recorded as evidence.

**Do not say:** that backups are live in production, or quote a recovery-time objective. Both depend on POD-A and POD-I.

### 2.3 B-07 — "A tamper-evident audit trail"

**Safe claims:** an audit-ledger hardening migration adds integrity guarantees to audit records.

**Do not say:** "retained for X days" — the current `audit_log_retention_days = 1` conflicts with auditability expectations and is POD-E.

### 2.4 B-09 — release transparency

Highest-risk candidate. It could be genuinely valuable (transparency builds trust) but it discloses the unapplied-migration gap. It requires explicit PO approval before drafting, and must describe the gap as a *deliberate staged-release discipline*, not as a defect — only if that is actually true.

---

## 3. Candidate summary

| Gate status | Count | Candidates |
|---|---|---|
| `READY` | 5 | B-01, B-02, B-04, B-05, B-08 |
| `HOLD_G2` (fixable wording) | 1 | B-03 |
| `HOLD_G3` (needs PO decision / production truth) | 3 | B-06, B-07, B-09 |

**Recommended publication order:** B-08 → B-01 → B-02 → B-04 → B-05 → B-03 (after wording fix) → *hold* B-06/B-07/B-09.

B-08 and B-01 lead because they connect to the platform's core promise (defensible numbers, traceable provenance) rather than to new infrastructure — they are honest *today* and they are the pre-existing strengths of the product.

---

## 4. Cross-checks against the prior blog convention

Per `docs/architecture/CARBONTALLY_BLOG_CMS_DECISIONS.md`, blog content is CMS-managed and must not hard-code claims that the product cannot substantiate. This candidate set is deliberately conservative:

- No post depends on a hard-coded demo string or synthetic figure.
- No post cites a production metric.
- Every technical claim is anchored to an FTR and an evidence token.
- Two candidates (B-06, B-07) are explicitly parked until the underlying migration is applied and the associated POD resolved.

<!--CTEOF-->
