# CarbonTally Phase 8 — S6 DECISION PACKAGE (plain business language)

**Prepared for:** Product Owner · **Date:** 2026-09-14
**Status of S6:** **NOT STARTED — awaiting this decision.** No S6 implementation has been performed.
**Basis:** `CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md` §16/§34, the ratified B4 decisions
(`B4-D4`/`B4-D9`/`B4-D10`), the B4 closure `…052`, and live inspection of the database.

---

## 1. What S6 actually is — in one paragraph

CarbonTally can already generate a draft carbon report and **store it as a version** with a
lifecycle state (draft → reviewed → approved → final). All of that works **behind the scenes** and
is protected server-side — but **there is no screen for it**. S6 is the **user-facing layer** for
that lifecycle: the screens a customer (or a consultant working on the customer's behalf) uses to
*see* a draft, *send it for review*, *request changes*, *approve it* and *finalise it* — plus one
open question about **comments** attached to a report during that review.

S6 adds **no new engine and no new calculation**: every action it offers already exists as a secure
API. S6 is a **presentation/UX batch** — which is exactly why it needs your decisions about *who
sees what* rather than new technical work.

---

## 2. What user functionality S6 adds

| Today | After S6 |
|---|---|
| A report version exists with a state, but nobody can see or change that state in the product | A customer/consultant can see the report's **state** and its **history** of versions |
| No buttons to move a version forward | **Submit for review**, **Request changes**, **Reject**, **Approve**, **Finalise** — each offered only where the server would allow it |
| No visible link between a report line and the data behind it | A **drill-down** from a reported figure to the persisted inputs and the supporting evidence |
| Comments are impossible | A decision to make (see §4) |
| "Approve" would be an invisible, unaudited act | Approval/finalisation become **explicit, attributed, audited** actions |

**Practical value:** the customer can actually *use* the reporting work CarbonTally has done,
instead of it being a black box; approval becomes a real, recorded business act; and reviewers can
see what they are approving.

---

## 3. Three terms that need plain definitions

**"Report-lifecycle UI"** = the screens for the *state* of a report version and the actions on it.
It is **not** report *content* and not the PDF. Concretely: a list of versions (draft, reviewed,
approved, final, changes-requested); a clear indication of *what is expected next* and *who may do
it*; the action buttons; and an audit-style history of who did what, when.

**"Comments visibility"** = if we let people write notes on a report during review, **who is allowed
to read each note**. Two different kinds exist in practice:
* **internal notes** — staff/consultant working notes (e.g. "mapping looks wrong, check the
  supplier") which a customer must **never** see; and
* **shared notes** — review remarks intended for the customer (e.g. "please supply the missing
  invoice for Q3").

Without a visibility rule, an internal note could be shown to a customer, or a customer's question
could be hidden from the reviewer. That is the risk this decision closes.

**"A7"** is the internal reference for **that visibility rule** — the decision that says internal
notes stay internal and shared notes are visible to the customer. `A9` is its companion: whether an
**unresolved "change request" comment blocks approval**. Both were **deliberately left open** and
deferred to S6 by the ratified B4 decision (`B4-D4`/`B4-D9`), which kept comments **out of B4**

---

## 4. The decisions you need to make

### Decision S6-1 — **Is S6 in scope at all, and when?**
*What it means:* do we build the customer-facing lifecycle screens now, later, or not at all
(leaving the lifecycle as an API-only capability)?
*Options:* **(a)** build S6 now as a bounded UI batch; **(b)** defer S6 (lifecycle stays API-only,
invisible to customers); **(c)** build only the read-only parts (state + history + drill-down) and
leave the action buttons for later.
*Recommendation:* **(c) then (a)** — start with visibility (low risk, immediate value, no new write
paths), then add the actions. A customer who cannot see the state cannot benefit from the approval
workflow at all.
*Consequence:* (b) leaves a working but unusable capability; (a) is the complete outcome; (c)
delivers most of the value with the smallest behavioural surface.

### Decision S6-2 — **Do we activate report comments, or leave them dormant?**
*What it means:* the database table for report comments exists but has never been used (0 rows).
Activating it means real users can write notes on a report.
*Options:* **(a)** activate comments as part of S6; **(b)** leave comments dormant and ship only the
state/action UI; **(c)** activate a **single shared thread only** (no internal notes yet).
*Recommendation:* **(b) for the first S6 release**, then (a) as a second bounded release. Reason:
comments carry the visibility and blocking questions below, and the lifecycle UI is independently
valuable and much safer to land first.
*Consequence:* (a) makes S6 bigger and pulls two policy decisions into the same release as the UI;
(b) keeps the first release small and reversible.

### Decision S6-3 — **The visibility rule (`A7`)**
*What it means:* who may read which comment.
*Options:* **(a)** the recommended split — internal notes are staff/consultant-only, shared notes are
visible to the customer; **(b)** one shared thread visible to everyone on the report; **(c)**
everything internal (customers see no comments at all).
*Recommendation:* **(a)** — it matches the specification's recommendation, protects internal working
notes, and still lets us ask the customer for information in writing.
*Consequence:* choosing (b) risks exposing internal working notes; (c) removes the ability to ask the
customer for missing information inside the product.

### Decision S6-4 — **Do unresolved "change requests" block approval? (`A9`)**
*What it means:* if a reviewer asks for changes and nobody closes the request, may the report still
be approved?
*Options:* **(a)** yes, an unresolved change request **blocks** approval (specification
recommendation); **(b)** it warns but does not block.
*Recommendation:* **(a)** — a warning that can be ignored makes the review step cosmetic.
*Note:* this interacts with your earlier **evidence-gap** ruling: CarbonTally must **never block**
approval merely because *evidence is missing*. Blocking on an *unresolved change request* is a
different thing — a deliberate human action that was never closed — so (a) remains consistent. If
you would rather keep every non-technical gate open, choose (b).
*Consequence:* (a) makes approval meaningful and auditable; (b) keeps approval possible in all cases.

### Decision S6-5 — **Who may comment and who may act** (confirm the boundaries)
*What it means:* the recommendation is that reviewers/approvers, consultants (within an active grant)
and internal staff (per permission) may comment; customers may comment on their own report; and
**only the customer's Owner/Admin may approve or finalise** (already ratified as `B4-D1` —
consultants and internal staff may never).
*Recommendation:* confirm the recommendation, and confirm that **the UI never becomes the security
boundary** — the server refuses anything the UI should not offer.
*Consequence:* if consultants should also be able to *approve*, that would **contradict the ratified
`B4-D1`** and would need that decision reopened explicitly — it will not be assumed.

### Decision S6-6 — **Where do the screens live, and what should they look like?**
*What it means:* S6 is a customer/consultant-facing batch, so it must live in the **authenticated
workspace** and use the **ratified design system** (D21), not a new one-off visual style.
*Options:* **(a)** a report page with a version panel + action bar; **(b)** a dedicated
review/approval inbox listing everything awaiting my action.
*Recommendation:* **(a) first, (b) later** — (a) is the natural home and answers "what happens next?"
on the report itself; (b) becomes valuable once volume grows.
*Consequence:* (b) as a first step risks duplicating navigation before the single-report experience
exists.

---

## 5. What S6 explicitly does NOT include

* No report **content** changes, no calculation changes, no new report types.
* No change to the frozen-final-PDF behaviour (`B4` is closed).
* No AI narrative (`S8` — separate authorisation, preconditions unmet).
* No consultant white-label or billing work.
* No reopening of B1–B4, and no change to the already-ratified approval authority (`B4-D1`).
* No OHD work (out of scope for this cycle).

## 6. If you want to proceed

A single reply covering **S6-1 to S6-6** is enough to raise the S6 implementation authorisation.
Anything you leave unanswered will be treated as **not decided** and will stop the affected part of
S6 rather than being inferred.

precisely so they would be decided here, together with the interface.
