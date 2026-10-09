# CT-CONSULTANT-PLATFORM-DECISION-REGISTER-02

## Final Consultant Platform Decision Register
**Date:** 2026-10-07  
**Status:** PO IMPLEMENTATION BASELINE

This register freezes the remaining consultant/client decisions for implementation. Existing binding PO-1 through PO-10 remain authoritative and are not reopened.

## 1. Security model

Effective client access is:

`RELATIONSHIP ∩ CLIENT ACCESS PROFILE ∩ CLIENT ROLE/CAPABILITY ∩ COMMERCIAL ENTITLEMENT`

Relationship, role, capability, profile, entitlement and branding must never substitute for one another. Branding/domain is never a security identity. Frontend controls never substitute for backend authorization.

## 2. Ratified decisions

### PD-1A — Client invitation
**A — CarbonTally-controlled secure single-use invitation.**

- Authorized consultant initiates.
- Email + permitted client role.
- Secure, single-use, expiring invitation.
- Existing users authenticate and accept; new users complete account creation.
- Acceptance creates membership only in the target Organisation.
- Token is atomically consumed and cannot be replayed.
- Consultant never receives passwords/tokens.
- Client users cannot invite other client users.
- White-Label invitation uses the consultant's verified White-Label brand/sender where entitled and configured, subject to legal/provenance requirements.

### PD-2A — Client user-role authority
**C — dual authority with explicit boundaries.**

Authorized consultant capabilities may invite, assign permitted roles, change roles, suspend/remove access and revoke invitations.

Authorized client Organisation owner/admin may manage users in their own Organisation within permitted client-role boundaries.

Neither side may grant consultant privileges, access another Organisation, modify commercial entitlement, consultant billing, White-Label entitlement or CarbonTally internal privileges.

### PD-3A — Consultant task client validation
**Server-side validation mandatory.**

`client_id` must reference an active client relationship belonging to the consultant firm. Foreign, nonexistent and inactive identifiers fail closed. Firm-wide tasks remain permitted.

### PD-5 — Relationship requests
**C + S2.**

Either party may initiate an authorized relationship change/termination request. Normal workflow is party-controlled; CarbonTally provides arbitration/escalation. Requests are confirmed, authorized and audited.

**Normal SLA target: 3 business days.** This is an operational target, not automatic approval.

### PO-1 — Mode changes
**Existing binding PO-1 preserved and operationalized; not reopened.**

Consultant submits a request. Normal effect is at billing/renewal boundary when commercially entitled. CarbonTally Admin may approve/reject, change entitlement, approve earlier transition, or prevent an invalid transition. Existing relationships/users must not be silently destroyed.

## 3. Client access profiles

Canonical profiles:

- **OFF:** no client login.
- **READ_ONLY:** view permitted data/reports/evidence and communicate with consultant; no data writes.
- **COLLABORATIVE:** controlled contribution such as permitted document upload, source-data correction/annotation; still no factor mapping or recalculation.
- **MANAGED:** curated client view; consultant operates the lifecycle.
- **RETAINED_READ_ONLY:** post-relationship historical read-only access.

### Recommended/default profile: READ_ONLY

Clients can view their own data, emissions, reports, evidence/provenance, issues and queries, respond to consultant questions, request corrections and message their consultant.

Clients cannot edit/delete data, upload documents, edit master data, edit mappings, map factors, trigger recalculation, manage users, change consultant, manage branding or access billing.

### COLLABORATIVE

Permitted limited contribution:
- permitted document upload;
- permitted source/master-data edits;
- correction/annotation of own submissions;
- workflow responses.

Still prohibited:
- unrestricted deletion;
- factor mapping/editing;
- recalculation;
- user administration;
- consultant administration;
- billing;
- branding administration.

## 4. Client deletion

**No unrestricted client deletion authority.**

Clients report/correct permitted information through controlled workflows. Evidence/calculation history must retain appropriate audit/provenance.

## 5. Client messaging

**Enabled for active client profiles that permit login.**

Allowed relationship:

`CLIENT ↔ THEIR CONSULTANT`

Use cases include data-quality questions, missing data, evidence questions, reporting questions, correction requests and workflow communication.

Never allow client-to-client, client-to-other-consultant, or unrestricted client-to-CarbonTally-internal communication.

## 6. Factor mapping / recalculation

Clients can **never** map factors, edit mappings or trigger recalculation, regardless of profile.

## 7. Client billing

No client billing surface. Managed clients cannot access consultant firm billing, purchase plans, modify consultant subscriptions or see consultant payment information. CarbonTally bills the consultant firm.

## 8. Relationship termination

Either party may initiate. Termination is authorized, confirmed, audited and non-destructive.

Never delete/clone/migrate the Organisation or destroy evidence, calculations, reports or audit history. Preserve the same Organisation ID.

## 9. Retention

**7-year default retained-read-only policy**, with legal-hold override. Existing architecture configuration remains:

```json
{"years":7,"retained_read_only":true,"legal_hold_blocks_deletion":true,"auto_delete_enabled":false}
```

This is a CarbonTally product policy, not a claim that every regulation requires exactly seven years. Admin may control the policy.

## 10. Product modes

Canonical modes:

- **STANDARD:** no client login/portal.
- **CO-BRANDED:** client portal permitted; client + consultant presentation; CarbonTally remains visible.
- **WHITE-LABEL:** client portal permitted; consultant branding; verified sender where configured; ordinary CarbonTally product branding suppressed subject to legal/provenance requirements.

Commercial entitlement remains CarbonTally-controlled.

## 11. Branding

**Firm-level only.** No per-client branding overrides.

White-Label presentation exists only in White-Label mode and when commercially entitled. Branding never establishes tenant identity.

## 12. Final approval

An authorized consultant role may perform final approval for consultant-managed Organisations. Approval requires explicit capability and records actor/capacity. Direct-customer approval remains distinct.

## 13. Header/navigation UX

User-facing product name is **CarbonTally**, never `CarbonTallyV3` or `V3`.

There must be exactly one client context. Preferred structure:

```text
CarbonTally
Consultant · Demo Lab Carbon Consultants

Working on: CT03-QA Managed Client
Consultant-managed · Active · Managed

← Back to Consultant
```

Remove duplicate `Working on:` labels, duplicate client identity, exposed V3 terminology, unnecessary Switch Client controls and raw technical IDs where human-readable names exist.

The operating context must clearly distinguish actor, subject, relationship, state and profile without repetition.

## 14. Implementation invariants

Preserve cross-tenant isolation, RLS, server authorization, Organisation identity, consultant/client identity separation, direct-customer behavior, existing commercial subscription infrastructure, audit/provenance, Organisation IDs, evidence/history and non-destructive migrations.

Do not create a second Subscription model or parallel client Organisation model. Do not put consultant users into `organization_members`. Do not infer authorization from branding/domain or relationship alone. Do not rely on frontend guards. Do not grant client factor/recalculation authority. Do not invent pricing/limits. Do not silently change PO-1 through PO-10.

## 15. Verification

Implementation is not acceptance. Cline must report exact files/migrations/API changes, authorization and profile matrices, invitation tests, tenant-isolation tests, termination/mode tests, White-Label email/branding tests, deletion/mapping/recalculation denial tests, messaging isolation, direct-customer regression, browser walkthrough/screenshots, full relevant test results, and pre-existing vs introduced failures.

Independent CoStrict verification remains mandatory before PO acceptance.

## 16. Final product principle

CarbonTally is a controlled carbon-accounting operating platform: consultants can operate clients' Organisations, while clients receive precisely bounded participation in their own data, evidence, reporting and communication.

Clients are collaborators/reviewers, not unrestricted system operators.

**Status: FINAL IMPLEMENTATION BASELINE.** Any newly discovered policy question must become a new `PD-*` decision rather than being invented during implementation.
