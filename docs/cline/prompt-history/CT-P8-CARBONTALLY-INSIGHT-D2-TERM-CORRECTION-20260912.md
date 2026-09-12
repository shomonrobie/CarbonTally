# CT-P8-CARBONTALLY-INSIGHT-D2-TERM-CORRECTION-20260912

**Prompt ID:** `CT-P8-CARBONTALLY-INSIGHT-D2-TERM-CORRECTION-20260912`
**Date:** 2026-09-12
**Task purpose:** Small documentation-only correction to the completed D2 PO ratification, making
**CarbonTally Insight** the canonical technical/domain terminology for new implementation (in
addition to the working customer-facing product name), and superseding D1's `ask_*` proposal for
new implementation.
**Type:** DOCUMENTATION CORRECTION ONLY. No implementation. No I1.
**Task status:** `COMPLETED — D2 TERMINOLOGY CORRECTED`

## Repository State at Start

| Item | Value |
|---|---|
| Branch | `main` |
| Starting HEAD | `d91ace593d9f90dbcfc046cb720c37733b0cbbc9` (the D2 ratification commit) |
| Relation to origin | 10 commits ahead of `origin/main`, **not pushed** |
| Pre-existing modified | 208 |
| Pre-existing untracked | 52 |
| Staged | 0 |

## Context

D2 was completed and committed as `d91ace5`. The D2 document recorded:

* customer-facing product name = **CarbonTally Insight**;
* technical domain = `ask_conversations`, `ask_messages`, `ask_interactions` (the D1 proposal),
  described as "unchanged technical domain terminology".

Since D2 was completed, the Product Owner made a **further naming decision**:

> **CarbonTally Insight is now the canonical new technical/domain terminology as well as the
> working customer-facing product name.**

This correction records that decision before I1 begins.

## The Correction Applied

### New canonical terminology (for NEW implementation)

```text
CarbonTally Insight
carbontally_insight_conversations
carbontally_insight_messages
carbontally_insight_interactions
CarbonTallyInsightConversation
CarbonTallyInsightMessage
CarbonTallyInsightInteraction
```

Plus the corresponding `CarbonTallyInsight` naming for new domain/service/module identifiers where
technically appropriate. **The API route namespace was NOT decided by this task** and was not
invented or implemented.

### Supersession rule recorded (normative)

> **CarbonTally Insight is both the working customer-facing product name and the canonical
> technical/domain terminology for new implementation.**

And explicitly recorded:

> *"Ask CarbonTally" was the discovery-stage working name. The Product Owner subsequently ratified
> "CarbonTally Insight" as the working customer-facing product name and canonical technical/domain
> terminology. New implementation must use CarbonTally Insight terminology.*

Consequence: **I1 must not create `ask_*` objects merely because they appeared in the D1 proposal.**

## Sections Corrected in the D2 Document

| Section | Correction applied |
|---|---|
| **Header** | Added a **Revision 2 — terminology correction** notice recording the new canonical position and stating that the I1 boundary is unchanged |
| **§3.2** | Replaced the normative terminology table with the required three-row table (product / canonical technical / historical-superseded); added the required blockquote; retained the superseded blockquote only to make the supersession explicit |
| **§3.2.1** (new) | Listed the canonical new-implementation identifiers (tables + classes) and stated that the API route namespace is not decided |
| **§3.2.2** (new) | Scoped the canonical naming to new implementation from I1 onward; no repository-wide rename |
| **§3.4** | Removed the "no new namespace introduction" prohibition and the "no change to `ask_*` technical naming" line; clarified that no existing artefact is renamed |
| **§3.4.1** (new) | Added that **new implementation MUST use the canonical naming**, that **there is no prohibition on introducing the CarbonTally Insight namespace**, and that **D2 itself does not implement the namespace** |
| **§3.6** | Rewrote the alias note as a **historical references** note covering "Ask CarbonTally" and the `ask_*` identifiers, with the required explicit statement and the no-broad-rename position |
| **§3.8** (new) | Added the **terminology supersession rule** (canonical vs superseded table, rationale, four normative consequences) — placed after §3.7 to keep numeric order |
| **§5.5** | Persisted-domain naming now states the canonical `carbontally_insight_*` terminology and that I1 must not create `ask_*` objects |
| **§6.3** | Substrate row changed to **CarbonTally Insight bounded domain (`carbontally_insight_*`)** |
| **§24.5** | I1 naming constraint now explicitly binds I1 to **CarbonTally Insight / `carbontally_insight_*` terminology for all new persistence/domain objects** |
| **§27 R1** | Updated to the required ratified wording (product name + canonical technical/domain name; provisional and not trademark-cleared; `ask_*` superseded; no broad legacy rename required) |
| **§27.1** | Added **R24** recording Revision 2 as a ratified decision |
| **§28** | Added a **Revision 2 status** block: `D2 TERMINOLOGY CORRECTED — CARBONTALLY INSIGHT IS CANONICAL FOR NEW IMPLEMENTATION`, and that I1 implementation has not been performed |

## What Was NOT Done (scope discipline)

* **D1 was not rewritten.** `docs/architecture/CARBONTALLY_PHASE8_ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md`
  retains its discovery-stage terminology as historical record.
* **No broad repository-wide rename** was performed.
* **No unrelated documentation** was modified.
* **`ask_*` occurrences in the D2 document were retained where they correctly describe the
  superseded/historical position** — every remaining occurrence is explicitly framed as
  superseded or as a "must not create" rule.
* **No API route namespace** was decided, invented, or implemented.
* **No application code, migration, RLS policy, table, API, service, tool, frontend, provider,
  billing or production change** was made.
* **The I1 boundary was not expanded** — §24 is unchanged.

## I1 Boundary (unchanged, restated)

I1 remains: dedicated Insight conversation persistence; dedicated Insight message persistence;
initial repository/domain layer; minimal create/list/read; organization scoping; explicit RLS
design; appropriate indexes/constraints; basic persistence API foundation.

I1 does **not** authorise: I2, I3, I4, I5, I6, I7, I8, RAG, LangChain, AI provider integration,
AI tools, frontend implementation, billing, consultant access, auditor access, PE access, or report
lifecycle changes.

**The only change is the naming of the objects I1 will create** (canonical
`carbontally_insight_*` rather than the D1-proposed `ask_*`).

## Verification Performed

| # | Requirement | Result |
|---|---|---|
| 1 | Only the D2 terminology document + prompt-history file changed | ✔ |
| 2 | No application code changed | ✔ |
| 3 | No database migration changed/created | ✔ |
| 4 | No RLS policy changed | ✔ |
| 5 | No API/frontend/provider/billing code changed | ✔ |
| 6 | No production system touched | ✔ |
| 7 | Existing dirty/untracked work preserved | ✔ (208 / 52 before and after) |
| 8 | No broad repository-wide rename performed | ✔ (only the single D2 file edited; no table/route/class renamed) |
| 9 | `git status --short` shown | ✔ (Git section below) |
| 10 | Exact commit hash shown | ✔ (Git section below) |

Secret scan of both files found no credentials, tokens, signed URLs or keys.

## Files Changed

| File | Change |
|---|---|
| `docs/architecture/CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md` | **modified** (Revision 2 terminology correction) |
| `docs/cline/prompt-history/CT-P8-CARBONTALLY-INSIGHT-D2-TERM-CORRECTION-20260912.md` | **created** |

No other file was created, modified or deleted.

## Git

| Item | Value |
|---|---|
| Starting HEAD | `d91ace593d9f90dbcfc046cb720c37733b0cbbc9` |
| Commit message | `docs: align CarbonTally Insight technical terminology` |
| Commit scope | The two documentation files above only |
| Push | **not pushed** |
| Prior D2 commit | `d91ace5` **not amended** — a separate correction commit preserves governance history |
| Unrelated work | preserved — untouched, unstaged, uncommitted |

## Implementation Statement

**No implementation was performed.** I1 was **NOT** begun. No RAG, no LangChain, no AI tools, no
provider integration, no frontend, no billing, no report-lifecycle change, no production access.

## Final Status

# D2 TERMINOLOGY CORRECTED — CARBONTALLY INSIGHT IS CANONICAL FOR NEW IMPLEMENTATION

> I1 implementation has NOT been performed.
