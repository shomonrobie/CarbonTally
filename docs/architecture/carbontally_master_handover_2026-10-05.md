# CarbonTally Master Handover — October 5, 2026

**Purpose:** authoritative restart point for the next CarbonTally conversation.

**Prepared:** 2026-10-05  
**Project:** CarbonTally  
**Current posture:** PRE-PRODUCTION / NOT AUTHORIZED FOR PRODUCTION DEPLOYMENT

---

## 1. Executive Summary

CarbonTally has a substantial implemented and verified engineering foundation, including Phase 8 capabilities, Demo Lab isolation, subscription/entitlement groundwork, Manual Processing routing/coverage, and the notification implementation for the newly authorized Manual Processing document lifecycle.

However, the latest hands-on PO review of the running UI exposed a broader **product/UX coherence gap** that was not adequately covered by the previous engineering verification process.

The immediate next objective is therefore **not another isolated implementation task**.

The next objective is:

> **Conduct a read-only CarbonTally Product Reality / Persona E2E Audit across the major user roles and workflows, identify all product, UX, terminology, permission, navigation, and workflow gaps, then make explicit PO decisions before further implementation.**

The most important product direction already emerging from the PO review is:

> **A consultant-managed client is still a normal CarbonTally customer organisation. The primary difference from a direct customer is the management relationship and permissions, not a reduced product/dashboard.**

This handover intentionally distinguishes:
- CLOSED decisions
- IMPLEMENTED capabilities
- VERIFIED capabilities
- IN PROGRESS
- REQUIRED BEFORE PRODUCTION
- NEWLY DISCOVERED / PO DECISION REQUIRED
- DEFERRED / NOT YET AUTHORIZED

No production migration, production deployment, production credential use, or production cutover is authorized by this handover.

---

# 2. Governance Rules

These remain authoritative:

1. **Implementation is not independent verification.**
2. **Independent verification is not PO acceptance.**
3. **PO acceptance is not production authorization.**
4. Do not claim a task is accepted unless the PO explicitly accepts it.
5. Cline may implement only an explicitly authorized scope.
6. CoStrict/OHD must independently verify implementation without fixing it during verification.
7. Do not silently resolve ambiguous product decisions in code.
8. No production migration, deployment, Supabase link, or production data mutation without explicit authorization.
9. Preserve the Demo Lab as the safe runtime/QA environment.
10. Keep CarbonTally running locally during active work; reuse healthy services and start only missing services.
11. Do not create duplicate architectures where an existing authoritative subsystem can be extended.
12. User-facing UI should communicate business concepts, not expose backend implementation vocabulary unnecessarily.
13. Technical identifiers such as UUIDs may remain available for diagnostics/audit, but should not normally be the primary human-facing label.

---

# 3. Current Runtime / Demo Lab

## Local runtime

- Frontend: `http://localhost:3000`
- Backend: `http://127.0.0.1:8070`
- Demo Lab gateway: `http://127.0.0.1:54430`
- Demo Lab DB: `carbontally_demo_local` on `127.0.0.1:54426`
- Docker service: `carbontally_demo_lab_storage`
- Demo credentials: `~/ct_local_env/demo_lab/credentials.local.json`

Important:
- Do not use `:3100` for normal CarbonTally QA.
- A previous `:3100` origin caused authentication/CORS confusion.
- Reuse healthy services; do not unnecessarily stop/restart them.
- Leave the local runtime available for PO manual testing.

## Production safety

- Production Supabase ref: `pvwiojoyaqywtydzcpbg`
- Supabase CLI is NOT linked to production.
- Never run `supabase link --project-ref ...` for production as part of ordinary QA.
- Production remains untouched and is not authorized for deployment/migration.

---

# 4. Repository / Release Baseline

The most recent Manual Processing / notification work was performed against:

- Branch: `p8-release-reconciled`
- Reported frozen release SHA: `375a48dc1b9e9cfd74090bbf747554ae997acb59`

The worktree has historically been intentionally dirty with multiple implementation/report artifacts and unrelated/pre-existing changes. Do not reset, clean, or discard worktree changes merely to simplify a task.

Before any new implementation:
- inspect current `git status`;
- inspect current HEAD;
- understand existing dirty/untracked work;
- do not assume the old handover's repository SHA is still current.

---

# 5. Major Engineering Capabilities Already Implemented

## 5.1 Phase 8 foundation

Phase 8 implementation work has been substantially completed across the reporting/insight/tooling foundation.

Important governance:
- preserve independently verified I1/I2 authorization boundaries;
- read tools are server-side, read-only, bounded, deterministic, authorization-aware;
- stored references are locators, never authorization grants;
- no arbitrary SQL/query execution;
- no mutation through read-tool paths.

The ratified initial I3 catalogue included:
1. `report_lookup`
2. `report_version_lookup`
3. `report_evidence_lookup`
4. `calculation_snapshot_lookup`

Do not expand the tool catalogue without PO authorization.

---

## 5.2 DEFRA 2025 importer

The DEFRA 2025 importer was reported production-verified at the implementation stage.

Delivered areas included:
- parser
- mapper
- validator
- exporter
- CLI

Scratch files were cleaned.

The importer is part of the factor/data foundation and should not be recreated as a new system.

---

## 5.3 Manual Processing commercial model

The Manual Processing commercial model was explicitly decided and implemented around:

> `manual_processing_effective = subscription_entitled AND governance_enabled`

Entitlement sources:
- direct customer subscription;
- consultant-sponsored subscription coverage.

Consultant sponsorship:
- is a commercial entitlement mechanism;
- is not automatic operational activation;
- does not automatically assign a Processing Entity;
- may cover all eligible clients or selected clients;
- is tied to the consultant firm's organisation subscription;
- requires active consultant-client relationship and explicit coverage.

Backward compatibility:
- `assisted_processing_available` remains a backward-compatible alias;
- canonical feature flag is `features.manual_processing.enabled`.

Important:
- commercial entitlement and operational routing are distinct concepts internally;
- the UI currently exposes this distinction too technically and requires product/UX redesign.

---

## 5.4 Manual Processing routing

Implemented areas include:
- routing to Processing Entities;
- consultant-sponsored coverage;
- selected/all eligible client coverage;
- Admin operational controls;
- routing audit events;
- preservation of existing human/internal assignment behaviour where required.

A separate allocation table/migration was introduced but is subject to the PD-6 migration review gate before use outside the already authorized lab context.

---

## 5.5 Demo Lab Manual Processing fixture

Task:
`CT-MP-SUB-004-PD5-FIXTURE-01`

Implemented:
- deterministic/resettable Manual Processing coverage fixture;
- browser fixture;
- documentation;
- verification support.

Independent verification:
`CT-MP-SUB-004-PD5-VERIFY-01`

Verdict:
> **VERIFIED — TARGETED GAPS CLOSED**

Independently checked:
- fixture convergence;
- reset/apply determinism;
- positive and negative customer states;
- consultant selected/all coverage;
- Admin coverage states;
- API behaviour;
- tenant isolation/security;
- base Demo Lab regression;
- production safety.

Known low-severity findings:
- N-1: fixture reset invalidates existing lab auth tokens until re-login; accepted as QA caveat.
- N-2: documentation attribution issue concerning a pre-existing `tools/demo_lab/stack.py` change; accepted as documentation issue.

PD-5 fixture work is complete.

---

# 6. Notification Architecture and Manual Processing Notifications

## 6.1 Existing notification foundation

CarbonTally already has a durable notification subsystem:
- `public.notifications`
- `public.notification_delivery`
- idempotent event-key uniqueness
- `NotificationsRepository.create_idempotent`
- delivery recording
- notification inbox API
- existing X2 email/retry infrastructure
- existing D40 recipient-scoped inbox architecture
- existing D11 consultant lifecycle event conventions

Realtime is not the authoritative delivery mechanism.

The notification database/API remains authoritative.

---

## 6.2 PO decisions for Manual Processing notifications

The following are CLOSED:

### N1
When Manual Processing work is assigned to a Processing Entity/PE:
- mandatory in-app notification;
- near-real-time expected;
- recipient is the responsible PE/assigned human where applicable.

### N2
When a Manual Processing batch requires validator assignment:
- mandatory in-app notification to the responsible CarbonTally validator.

### N3
When a document/batch enters Manual Processing:
- mandatory in-app notification to the responsible/submitting consultant;
- do not broadcast to all firm members.

### N4
When Manual Processing reaches terminal successful/validated completion:
- mandatory in-app notification to the **original uploader**;
- do not assume uploader is the responsible consultant;
- do not notify the client under this decision.

### Channel
- Email was NOT authorized for N1-N4 in this release.
- No user/org/Admin off-switch or notification preference system was authorized for N1-N4.
- Durable DB notification is the source of truth.
- Realtime is not a delivery dependency.

### Coverage allocation/release
Manual Processing coverage allocation/release remains:
> **AUDIT-ONLY**
and does not itself create proactive notifications.

---

## 6.3 Notification implementation

Task:
`CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-IMPLEMENT-04`

Implementation completed.

Self-verification:
- task suite: 60/60;
- regression rail: 364/364;
- no notification/task failures attributable to the task;
- full suite had 124 failures, but 0 were attributed to this task.

Full-suite failures were classified as pre-existing/environment/live-DB/tooling issues, including:
- migration-frontier guard failures;
- extraction-suggestion failures;
- environment-dependent discovery test;
- live-DB schema/index/constraint/factor/environment guard failures.

Implementation report status:
> **IMPLEMENTED AND SELF-VERIFIED — READY FOR INDEPENDENT VERIFICATION**

Important limitations retained:
- N3 attribution model requires PO/product review if future semantics change;
- N4 uploader provenance depends on existing item→document linkage;
- existing Realtime filter defect (`user_id` vs `recipient_id`) remains unfixed;
- API refetch remains authoritative;
- no preference/opt-out UI;
- live Supabase Realtime E2E was out of scope.

---

# 7. Manual Processing Independent Verification Status

The next intended task was:

`CT-MP-SUB-004-PROD-READINESS-NOTIFICATION-VERIFY-05`

An independent verification prompt was prepared covering:
- N1;
- N2;
- N3;
- N4;
- coverage allocation/release audit-only behaviour;
- source/code trace;
- Demo Lab runtime;
- idempotency;
- security/tenant isolation;
- API retrieval;
- notification regressions;
- browser verification;
- PO actor matrix;
- production safety.

However:

> **DO NOT start or continue this verification as the immediate next task yet.**

Reason:
the PO's hands-on UI review has now exposed broader product/UX/workflow problems that affect the coherence of the Manual Processing user journey.

The verification should resume after the product reality audit and resulting authorized fixes, unless the PO explicitly decides otherwise.

---

# 8. Production Readiness Decisions Already Made

## CLOSED / ACCEPTED

- F-1: UI implementation authorization issue resolved by PO decision.
- F-2: no internal CarbonTally staff access to customer Manual Processing route; current stricter 403 behaviour accepted.
- F-3: unrelated ConsultantPage copy changes accepted without remediation.
- F-5: Demo Lab positive coverage fixture implemented and independently verified.
- F-6: Admin operational tab remains labelled **Manual Processing**.
- F-8: active consultant firm members may read coverage; `manage_clients` required for allocate/release.
- F-10: merged customer copy accepted.
- NV-1: closed.
- NV-2: closed.
- NV-3: closed.
- NV-4: closed.
- NV-7: pixel-level D2 comparison not required by PO.
- NV-8: closed.
- N-1: accepted QA caveat.
- N-2: accepted documentation issue.
- P-1: no dedicated production SLO for Manual Processing coverage operations in this release.
- P-2 coverage allocation/release: audit-only.

## REQUIRED BEFORE PRODUCTION

- F-4: test/tooling baseline reliability.
- F-7: precise exception handling for allocation errors.
- F-9: idempotency/concurrency correctness.
- F-11: proper Admin eligible-client selector instead of raw client ID entry.
- NV-5: responsive UI verification.
- NV-6: accessibility verification.

## NOT REQUIRED / CLOSED

- NV-7: pixel-level visual D2 comparison.

## P-1

Decision:
> No dedicated production SLO for Manual Processing coverage operations in this release.

Local engineering budgets remain non-production engineering checks.

A future platform-wide SLO policy is a separate product/engineering decision.

---

# 9. New Product/UX Findings From PO Manual QA

These are **NEW findings**, not yet all converted into formal implementation authorization.

## 9.1 Manual Processing configuration is not understandable

The Admin UI currently exposes concepts such as:
- subscription;
- governance;
- routing;
- Processing Entity;
- commercial coverage;
- operational routing outcome.

The phrase:
> **"Manual Processing - subscription to routing"**

is not acceptable as normal product language.

The UI should explain the business relationship, not expose implementation terminology.

---

## 9.2 Subscription, entitlement, coverage, governance and routing are not clearly separated for users

The underlying concepts are legitimate:

1. subscription;
2. entitlement;
3. consultant coverage;
4. governance/enablement;
5. operational routing;
6. Processing Entity assignment.

But the current UI makes them difficult to understand and act upon.

The product must define a clear journey:

> subscription → entitlement → coverage (where applicable) → operational enablement → routing → processing → validation → completion

without requiring the user to understand backend architecture.

---

## 9.3 Admin has no obvious business-facing way to enable Manual Processing

The PO observed that there is no clear option in Internal Operations to allow/configure Manual Processing for customers.

This creates a fundamental product question:

> If Manual Processing is not enabled, how does a customer obtain/activate the service?

This requires a coherent subscription/entitlement/configuration journey.

---

## 9.4 Commercial Coverage is currently too diagnostic/technical

The current screen exposes:
- consultant firm IDs;
- organisation UUIDs;
- consultant relationship IDs;
- grant IDs;
- raw entitlement state;
- FIN-06 governance state;
- routing outcomes.

These can remain as technical diagnostics, but they should not be the primary operational UX.

Preferred direction:
- human-readable organisation names;
- human-readable consultant firm;
- subscription state;
- coverage mode;
- covered client count;
- clear actions;
- technical details expandable/secondary.

---

## 9.5 UUIDs should not be primary business labels

Examples observed:
- organisation UUID;
- consultant relationship UUID;
- grant UUID;
- audit actor UUID;
- audit resource/entity UUID.

Primary UI should show:
- person name;
- organisation name;
- consultant firm name;
- business resource name.

Technical IDs may be shown under:
> Technical details

or equivalent.

---

## 9.6 Audit UI needs human-readable actor/resource resolution

Current audit display can expose:
- actor UUID;
- resource/entity UUID.

Preferred:
> Kira Walsh released Manual Processing coverage for Demo Lab Client A.

Technical identifiers remain available for traceability.

This is not a reduction in auditability; it improves human auditability while preserving technical provenance.

---

## 9.7 Consultant coverage UX is incomplete

The consultant currently sees a state resembling:
> No consultant coverage active

without an understandable path to select/configure which subscription/coverage applies.

The intended model should be:

> Consultant firm subscription → coverage configuration → all eligible clients OR selected clients.

The consultant should not have to repeatedly select an underlying subscription if the subscription belongs to the firm.

---

## 9.8 Consultant-managed clients should be full CarbonTally organisations

This is the most important newly emerging product direction.

PO intent:

> **A consultant client is a normal CarbonTally customer organisation.**

The difference is:
- who manages the organisation;
- the consultant-client relationship;
- permissions.

The client should not become a reduced or separate "mini CarbonTally" product.

Expected core organisation surfaces should remain available subject to role permissions, including areas such as:
- Overview & Settings;
- Locations;
- Facilities & Assets;
- Vehicles;
- Suppliers;
- Members & Invitations;
- Custom Factors;
- Activity;
- Audit & Evidence;
- Documents;
- Processing;
- Reports;
- Billing/Subscription where appropriate.

This direction still requires a formal PO decision record before implementation.

---

## 9.9 Consultant client management permissions need explicit design

The current consultant experience does not expose the same organisation management capabilities as a direct customer.

Need explicit permission design for:
- consultant firm owner;
- consultant member;
- client owner/admin;
- client member.

The desired model is:
> same organisation product surface + role/relationship-based permissions

rather than:
> separate reduced dashboard.

---

## 9.10 Consultant batch/multi-document upload appears missing/incomplete

PO observed that consultants cannot upload multiple documents.

This should be treated as a functional workflow gap.

The intended experience is that consultant uploads to a managed client should use the same underlying document processing pipeline as direct customers.

Both paths must be tested:
- direct customer batch upload;
- consultant → client batch upload.

---

## 9.11 Billing terminology may contain legacy/conflicting concepts

The Billing UI includes terminology such as:
- Assisted Processing estimate;
- Managed Processing;
while current product decisions use:
- Manual Processing.

This must be fact-found before renaming or removing anything.

Possible explanations include:
- legacy feature;
- separate commercial service;
- alias;
- obsolete workflow.

Do not implement a rename until the product meaning is established.

---

## 9.12 Empty states often lack next-step guidance

Examples:
- no active subscription;
- no consultant coverage;
- no Manual Processing entitlement;
- no processing state.

The UI should answer:
1. Why is this empty?
2. What can I do?
3. Who can change it?
4. What happens next?

---

## 9.13 Assignment page may have an authorization/functional defect

PO observed an Admin Assignment screen displaying a failure such as:
> Failed to load / You don't have permission to access this area.

This must be code-traced before classification.

Possible outcomes:
- intentional security boundary;
- incorrect Admin authorization;
- broken route;
- stale runtime evidence.

Do not assume.

---

## 9.14 Settings page has visible UX issues

Observed:
- contradictory environment wording in Analytics section;
- retention values need stronger effective-policy/status presentation;
- too much flat navigation;
- technical wording;
- weak state hierarchy.

The Analytics text appears internally contradictory:
> production environment
and
> not a production environment.

This must be corrected.

---

# 10. New Product Principle Proposed by PO

This is the central direction to formalize:

> **CarbonTally should model consultant-managed clients as ordinary customer organisations with a managing-consultant relationship, not as a separate reduced product type.**

Conceptually:

```text
                 CarbonTally Organisation
                           |
             +-------------+-------------+
             |                           |
      Direct customer            Consultant-managed
             |                           |
       Customer staff             Consultant firm
```

Both should share the same core organisation capabilities.

The distinction should be represented by:
- relationship;
- roles;
- permissions;
- management responsibilities;
- commercial sponsorship where applicable.

This principle should guide future UX, permissions, billing, document processing and reporting design.

**Formal PO ratification is still required before implementation.**

---

# 11. Billing / Subscription Pluggability

A separate architectural concern remains:

> Billing/subscription should ultimately be provider-neutral and pluggable.

Desired conceptual architecture:

```text
Payment Provider
       ↓
Billing Adapter
       ↓
CarbonTally Subscription Service
       ↓
Feature Entitlement
       ↓
Manual Processing / Other Features
```

CarbonTally product logic should depend on the CarbonTally subscription/entitlement contract, not directly on a specific payment provider.

Potential concepts:
- `BillingProvider` adapter;
- `SubscriptionService`;
- provider customer mapping;
- checkout;
- normalized webhooks;
- canonical subscription lifecycle;
- provider-independent/manual/offline billing;
- webhook idempotency;
- entitlement auditability.

**Status:** NOT YET IMPLEMENTED AS A FORMAL PLUGGABLE BILLING MODULE.

Next step should be a separate **read-only billing/subscription pluggability fact-find**, followed by PO architecture decision, then implementation and independent verification.

Do not implement this inside the current notification/UI remediation work.

---

# 12. What Is Implemented vs Pending

## IMPLEMENTED

- Phase 8/I1/I2 foundation and authorized I3 read-tool foundation.
- DEFRA 2025 importer.
- Demo Lab isolated runtime and actor matrix.
- Manual Processing commercial entitlement foundation.
- Direct and consultant-sponsored Manual Processing coverage.
- Selected/all consultant coverage.
- Manual Processing operational routing.
- Admin Manual Processing operational controls.
- Deterministic Demo Lab Manual Processing fixture.
- Independent PD-5 fixture verification.
- Durable notification infrastructure.
- Manual Processing N1-N4 notification implementation.
- Notification task self-verification: 60/60 task tests and 364/364 regression rail.
- Local runtime/QA procedures.

## VERIFIED INDEPENDENTLY

- PD-5 Demo Lab fixture and targeted Manual Processing coverage behaviour.
- Security/tenant isolation for the verified fixture.
- Browser positive/negative coverage states within the PD-5 scope.
- Base Demo Lab regression.
- Production safety for that verification scope.

## IMPLEMENTED BUT NOT YET INDEPENDENTLY VERIFIED

- N1-N4 Manual Processing notification implementation.

## REQUIRED BEFORE PRODUCTION

- F-4 tooling/test baseline reliability.
- F-7 precise exception handling.
- F-9 allocation idempotency/concurrency.
- F-11 Admin eligible-client selector.
- NV-5 responsive verification.
- NV-6 accessibility verification.
- Resolution of newly discovered critical product/UX workflow gaps after PO decisions.

## NEWLY DISCOVERED / PRODUCT REVIEW REQUIRED

- Manual Processing subscription/enablement UX.
- Subscription vs entitlement vs coverage vs routing information architecture.
- Consultant-managed client organisation model.
- Consultant client full organisation dashboard.
- Consultant client permissions/editing.
- Consultant batch upload.
- Billing terminology reconciliation.
- Human-readable identifiers across Admin/audit.
- Assignment authorization issue investigation.
- Settings/environment wording and retention UX.
- Cross-role navigation/workflow coherence.
- Empty/error state guidance.

## DEFERRED / NOT YET AUTHORIZED

- Production migration/deployment.
- Provider-specific billing implementation.
- Platform-wide production SLO policy.
- Email delivery for N1-N4.
- User/org notification preferences/off-switch.
- Realtime delivery dependency/fix.
- Pixel-level D2 visual comparison (PO closed NV-7).
- Any new roles/privilege model without PO decision.
- Any expansion of I3 tool catalogue without authorization.

---

# 13. Immediate Next Task

## TASK: CarbonTally Product Reality / Persona E2E Audit

**Status:** NOT YET IMPLEMENTED — NEXT AUTHORIZED FACT-FIND SHOULD BE READ-ONLY.

Purpose:

> Systematically inspect the product as real users, not merely as backend/test cases.

Actors:

1. Direct customer owner/admin
2. Direct customer member
3. Consultant firm owner
4. Consultant firm member
5. Consultant-managed client owner/admin
6. Consultant-managed client member
7. Processing Entity / PE
8. CarbonTally validator
9. CarbonTally internal operations staff
10. Platform Admin

Journeys should include:

- onboarding;
- organisation setup;
- subscription/billing;
- Manual Processing;
- consultant sponsorship;
- coverage;
- document upload;
- batch upload;
- automatic processing;
- Manual Processing entry;
- PE assignment;
- validator assignment;
- completion;
- notifications;
- review;
- emissions;
- reports;
- audit;
- members/permissions;
- organisation settings;
- consultant client management.

The audit must identify:
- BUG;
- UX DEFECT;
- PRODUCT GAP;
- TERMINOLOGY PROBLEM;
- PERMISSION GAP;
- LEGACY/CONFLICTING FEATURE;
- EXPECTED BEHAVIOUR;
- ALREADY DECIDED / NO CHANGE.

No code changes.

No migration.

No production access.

No commit/push.

Do not fix findings during fact-find.

Deliver a permanent report with the task ID in its filename.

---

# 14. Proposed Next Governance Sequence

After the Product Reality Audit:

### Step 1 — PO review
You and I review every finding.

### Step 2 — PO decision record
Mark each:
- CLOSED;
- ACCEPT;
- REQUIRED;
- DEFER;
- NOT AUTHORIZED;
- IMPLEMENT.

### Step 3 — Product/UX architecture specification
Create the authoritative:
- organisation model;
- consultant relationship model;
- navigation model;
- subscription/entitlement model;
- Manual Processing UX;
- permission matrix;
- terminology glossary.

### Step 4 — Cline implementation
Cline implements only the explicitly authorized scope.

### Step 5 — CoStrict independent verification
Independent verification with no implementation fixes.

### Step 6 — PO manual QA
You use the running application as each actor.

### Step 7 — Production gates
Return to:
- F-4;
- F-7;
- F-9;
- F-11;
- NV-5;
- NV-6;
and any remaining approved product gates.

### Step 8 — Production readiness
Only after PO acceptance and explicit production authorization.

---

# 15. CrewAI Decision

No CrewAI implementation is authorized yet.

The current conclusion is:

> The main weakness was not insufficient agents; it was insufficient product-reality review methodology.

CrewAI may become useful later for a repeatable multi-perspective Product Reality Audit, but first define and validate the methodology manually.

If adopted later, possible bounded roles include:
- Product/UX analyst;
- architecture/domain analyst;
- authorization/security analyst;
- QA workflow analyst;
- accessibility/responsive analyst;
- implementation agent (Cline remains suitable);
- independent verifier (CoStrict remains separate).

Agents must not make PO/product decisions autonomously.

---

# 16. Critical Working Principles for the Next Chat

1. Do not start by coding.
2. Do not assume current UI accurately represents the intended product model.
3. Do not treat backend architecture as user-facing terminology.
4. Do not create separate reduced functionality merely because a customer is consultant-managed.
5. Do not expose UUIDs as primary business labels.
6. Do not silently remove/rename legacy billing features.
7. Do not add new permissions/roles without explicit PO decision.
8. Do not treat implementation reports as acceptance.
9. Do not deploy or migrate production.
10. Keep the local Demo Lab running for manual QA.
11. Preserve existing verified security/RLS boundaries.
12. Use the Product Reality Audit as the next discovery layer.

---

# 17. Final Status

## CLOSED
- PD-1 through PD-6 decisions as previously ratified.
- PD-5 fixture.
- Coverage allocation/release notification policy: audit-only.
- Manual Processing notification channel policy: in-app only for N1-N4.
- NV-7.
- Accepted low-severity QA/documentation findings.

## IMPLEMENTED
- Manual Processing entitlement/coverage/routing foundation.
- Demo Lab fixture.
- Notification implementation N1-N4.
- Supporting tests and documentation.

## VERIFIED
- PD-5 targeted fixture and security/browser scope.

## IMPLEMENTED — AWAITING INDEPENDENT VERIFICATION
- N1-N4 Manual Processing notification implementation.

## REQUIRED BEFORE PRODUCTION
- F-4, F-7, F-9, F-11, NV-5, NV-6.
- Approved product/UX remediation resulting from the new Product Reality Audit.

## OPEN / PO DECISION REQUIRED
- Consultant-managed client = full CarbonTally organisation model.
- Consultant client permissions/editing.
- Consultant batch upload.
- Manual Processing subscription/enablement UX.
- Commercial Coverage UX.
- Billing terminology reconciliation.
- Admin/assignment authorization behaviour where observed.
- Cross-role navigation and workflow coherence.

## NOT AUTHORIZED
- Production deployment/migration.
- Provider-specific billing implementation.
- Email for N1-N4.
- Notification preference/off-switch system.
- New roles/privilege models.
- New I3 tools beyond the ratified four.

---

# 18. Restart Instruction

The next CarbonTally conversation should begin from this handover.

**Do not resume with notification verification.**

Begin with:

> **CT-PRODUCT-REALITY-AUDIT-01 — Read-only CarbonTally Product Reality / Persona E2E Audit**

The goal is to discover the full set of product/UX/workflow/permission inconsistencies before authorizing further implementation.

This handover is the current working baseline as of **October 5, 2026**.
