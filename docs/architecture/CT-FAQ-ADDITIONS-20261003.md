# CarbonTally — FAQ Additions (Delta)

**Document ID:** `CT-FAQ-ADDITIONS-20261003`
**Task ID:** `CT-FEATURE-DELTA-02-20261003-…-HEAD`
**Date:** 2026-10-03
**Status:** DOCUMENT_ONLY — proposed FAQ entries, gated
**Companion deliverables:** `CT-PO-CARBONTALLY-FEATURE-DELTA-CHANGELOG-20261003.md` (#1), `CT-PUBLIC-WEBSITE-FEATURE-LIST-20261003.md` (#2), `CT-BLOG-CANDIDATES-20261003.md` (#3)
**Prior convention:** `docs/featurellist.md`, `docs/CarbonTally Complete Customer Feature List.md`

---

## 0. Rules for FAQ copy

FAQ answers are the most-quoted public copy, so they are held to the same four gates:

| Gate | Applied rule |
|---|---|
| **G1** | Only answer with shipped capability; never confirm a feature that is not at least `IMPLEMENTED_AND_WIRED` |
| **G2** | No unsupported security/compliance/isolation claim; state what is enforced, not what is desirable |
| **G3** | No answer may resolve an open PO decision; where one is open, the answer must say so plainly |
| **G4** | Every technical answer carries an FTR + evidence anchor |

`TRUTH NOTE:` Where an answer touches an unresolved PO decision or an unverified capability, the answer explicitly says "currently under review" rather than inventing policy (AGENTS §62, §74). This is intentional: a hedge is more trustworthy than a guess.

## 1. Proposed FAQ additions

### Q1. Can I schedule reports instead of generating them each time?
**Answer (publishable, `READY`):** Yes. The current release lets you define a reporting schedule and have reports generated automatically, and it keeps scheduled reporting separate from on-demand generation so you can use either.
**Truth anchor:** FTR-362/363, `MIG:20261023000000_ct02_scheduled_reporting.sql`, `BE:backend/services/report_schedules.py`. Status `IMPLEMENTED_AND_WIRED`.

### Q2. Can I share a report with someone else?
**Answer (publishable, `READY`):** Yes — a generated report can be shared with recipients directly from the platform rather than exporting and emailing a file.
**Truth anchor:** FTR-364, `MIG:20261022000000_ct02_report_sharing.sql`. Status `IMPLEMENTED_AND_WIRED`.

### Q3. How large a document can I upload, and where does it go?
**Answer (publishable after wording fix, `HOLD_G2`):** Documents are transferred directly into encrypted storage rather than routed through the application server, and a single central gate enforces the permitted file types and size limits. Incoming files are screened on the way in.
**Do not say:** "secure uploads", "unhackable", "certified", or anything implying the upload link alone is the authorisation boundary.
**Truth anchor:** FTR-365…367/370, `BE:backend/api/v3_document_uploads.py`, `BE:backend/services/upload_gate.py`, `document_security.py`.

### Q4. Do you back up my data — and can I prove it?
**Answer (HOLD, `HOLD_G3`):** The release includes scheduled backups, a backup policy surface, an explicit verification step and a record of backup sets, with restore drills captured as evidence. **Whether production has this capability fully enabled is confirmed only after deployment verification**, which is currently pending.
**Do not say:** that backups or restores are proven in production, or quote a recovery objective.
**Truth anchor:** FTR-355…359, `DOC:CARBONTALLY_PRODUCTION_BACKUP_RESTORE_COMPLETE_IMPLEMENTATION_20261002`. POD-A and POD-I remain open.

### Q5. Can audit records be altered after the fact?
**Answer (HOLD, `HOLD_G3`):** The release adds integrity hardening to the audit ledger so that audit records are protected against silent alteration. **The retention period applied to audit records is under review**, because the currently configured value does not yet match our auditability expectations.
**Truth anchor:** FTR-373, `MIG:20261021000000_ct02_audit_ledger_hardening.sql`; POD-E. Status `IMPLEMENTED_AND_WIRED`; **not** `TESTED`/`VERIFIED`.

### Q6. Can I see how much storage my organisation is using?
**Answer (publishable, `READY`):** Yes — the release includes per-organisation storage metering, and storage limits are aligned to the documents bucket.
**Truth anchor:** FTR-368/369, `BE:backend/services/storage_metering.py`, `MIG:…documents_bucket_size_limit`, `…step2_documents_bucket_size_alignment`. Status `IMPLEMENTED_AND_WIRED`.

### Q7. What happens if my email provider has an outage?
**Answer (publishable, `READY`):** Notifications are sent through a provider-agnostic email layer, so the platform is not tied to a single provider.
**Truth anchor:** FTR-372, `BE:backend/services/email_provider.py`, `email_sender.py`. Status `IMPLEMENTED_AND_WIRED`.

### Q8. Can I use my own emissions factors?
**Answer (publishable, `READY`):** Yes. Approved customer-specific factors take precedence over CarbonTally's generic factors, and the write path is protected so an approved customer factor cannot be silently overwritten. Every calculation keeps a record of which factor was used.
**Truth anchor:** FTR-136…138/144–145, `DOC:CT-IMPLEMENT-04-…FACTOR-READ-REPOINT`, `BE:backend/utils/factor_catalogue.py`. Status `IMPLEMENTED_AND_WIRED`.

---

## 2. Questions we must NOT answer (yet)

These are likely customer questions raised by the delta. Adding a confident answer now would breach a gate.

| Likely question | Why we must not answer yet | Gate |
|---|---|---|
| "Is the stronger isolation active on my account?" | RLS remediation is `IMPLEMENTED`, not `TESTED`/`VERIFIED`; no negative-authz run performed | G2 |
| "How long do you keep my audit logs?" | Configured value conflicts with auditability; POD-E open | G2 / G3 |
| "Do you have separate Locations and Facilities?" | `locations` table absent; POD-D open | G1 / G3 |
| "Can I manage roles in a role catalogue?" | `roles` table has 0 rows; POD-C open | G1 / G3 |
| "Which environment is production, and does it match the release?" | Production returned HTTP 503; POD-I open | G1 / G3 |
| "Are you certified / compliant with X?" | No certification evidence exists for this pass | G2 |

Each of these should be answered at the *policy* level by a PO decision first, then published.

---

## 3. Gate summary & recommended insertion points

| Gate status | Count | Entries |
|---|---|---|
| `READY` | 5 | Q1, Q2, Q6, Q7, Q8 |
| `HOLD_G2` | 1 | Q3 (wording fix) |
| `HOLD_G3` | 2 | Q4, Q5 |
| `MUST NOT ANSWER YET` | 6 | see §2 |

**Recommended FAQ grouping (customer-facing):**

- *Reporting & sharing* → Q1, Q2
- *Documents & storage* → Q3, Q6
- *Notifications* → Q7
- *Factors & methodology* → Q8
- *Data protection* (parked) → Q4, Q5

**Placement rule:** FAQ entries must sit under the same section as the corresponding feature list entry, so a customer moving from the feature list to the FAQ sees consistent wording and consistent honesty.

---

## 4. Consistency check across the four deliverables

| Claim | Feature list (#2) | Blog (#3) | FAQ (#4) | Consistent? |
|---|---|---|---|---|
| Scheduled reporting is available | P-02 `READY` | B-01 `READY` | Q1 `READY` | ✓ |
| Report sharing is available | P-03 `READY` | B-02 `READY` | Q2 `READY` | ✓ |
| Direct-to-storage upload available, careful wording | P-04 `HOLD_G2` | B-03 `HOLD_G2` | Q3 `HOLD_G2` | ✓ |
| Storage metering available | P-05 `READY` | B-04 `READY` | Q6 `READY` | ✓ |
| Provider-agnostic email | P-07 `READY` | B-05 `READY` | Q7 `READY` | ✓ |
| Backup capability exists, production unverified | P-01 `HOLD_G3` | B-06 `HOLD_G3` | Q4 `HOLD_G3` | ✓ |
| Audit ledger hardened, retention under review | P-08 `HOLD` | B-07 `HOLD_G3` | Q5 `HOLD_G3` | ✓ |
| Customer factors take precedence | U-03 `READY` | B-08 `READY` | Q8 `READY` | ✓ |

All four deliverables gate the **same** eight delta themes identically. No deliverable claims more than the delta evidence supports.

<!--CTEOF-->
