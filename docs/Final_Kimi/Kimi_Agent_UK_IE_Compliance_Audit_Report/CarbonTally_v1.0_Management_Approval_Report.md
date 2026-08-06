# CarbonTally v1.0 — Management Approval Report

*Prepared by the Chief Database Architect for the Product Owner — 4 August 2026. This report converts the Production Hardening Plan into decisions for sign-off. Every recommendation from that plan appears exactly once below, as something to approve, defer, or reject.*

## Executive Summary

**Total recommendations reviewed: 89.** This comprises 25 launch-gating items (Category A), 14 items scheduled for the post-launch "v1.0.x hardening window" (B-window), 30 deferred items (Category C), and 20 rejected items (Category D).

**Decision breakdown:**

- **33 approved for the v1.0 launch window** — the 25 launch-gating items plus 8 B-window items that the plan schedules to land immediately post-launch (v1.0.1) or that begin there.
- **36 deferred to v1.1 or later** — all 30 Category C items plus 6 B-window items the plan schedules at v1.0.2 or beyond.
- **20 rejected** — recommendations that conflict with an approved architecture decision, are over-engineered, low-value, or premature.

**Estimated implementation effort for the approved set: roughly 40 person-days**, derived from the plan's five delivery phases — Phase 1 (critical security, tenancy and Irish-market fixes): ~10–12 days; Phase 2 (data integrity constraints): ~8–10 days; Phase 3 (targeted performance indexes): ~4 days; Phase 4 (application-level validation pack): ~10 days; Phase 5 (compliance pack including the data-erasure procedure): ~6–8 days. The approved B-window items are included within these phase estimates. This is a small, mostly low-risk body of work, deliberately kept small by rejecting or deferring the audit's larger programmes.

**Overall production readiness score: 32/100 today, projected 85/100 once the approved hardening set completes.** The original review scored the platform 32/100 against launch criteria; the approved 33 items close every defect touching customer money, credentials, tenant isolation, compliance or a reported carbon number, while the deferred and rejected items are — by the plan's evidence — not launch-relevant at our scale. The projected 85/100 reflects a launchable product carrying known, scheduled, non-blocking hygiene debt.

**Verdict: GO WITH CONDITIONS** — the binding conditions are set out in Section 6.

---

## Section 1 — Approved Changes ✅ (APPROVE FOR V1.0)

These changes are approved for the v1.0 launch. Items A1–A25 are hard launch gates: none can be skipped. Items B1–B8 are approved on the strength of the plan's scheduling — they land in the **first post-launch patch window (v1.0.1)** or begin there, and are treated as part of the committed launch programme, not optional extras.

| ID | Recommendation | Reason | Risk if Ignored | Effort |
|---|---|---|---|---|
| A1 | Verify the customer-data isolation rules (row-level security) end-to-end, and confirm no master access key is ever exposed to customers' browsers or unfiltered in background workers. | One customer seeing another's data is a reportable ICO (UK Information Commissioner's Office) / DPC (Irish Data Protection Commission) incident and an existential trust breach for a multi-tenant financial product. | Cross-tenant data leak; regulatory report; churn. | Medium |
| A2 | Backfill and then require a customer-organisation reference on six "hot" tables (conversations, messages, upload batches, review queue, file attachments, verifications). | Rows without an organisation fall outside every isolation rule — invisible or wrongly visible. Cheap now, painful after launch. | Silent tenant-isolation holes. | Medium |
| A3 | Stop storing long-lived credentials in plain text: hash consultant API keys, password-reset tokens and invitation tokens, with key rotation support. | Plaintext credentials defeat every other control: any backup or log yields live keys. | Credential theft from a routine operational artefact. | Small |
| A4 | Correct the password-reset rule so only the token itself must be unique (not one reset per user); latest valid token wins. | As built, an attacker can repeatedly request resets to permanently block a victim's recovery. | Unauthenticated denial-of-service against any user. | Small |
| A5 | Formally decide who owns the password column on the user record; if the login platform handles passwords, retire the column and never write it. | A dormant credential column will eventually be written, creating two drifting credential stores. | Future credential-store split and audit failure. | Small |
| A6 | Verify every table relationship's delete behaviour; block dangerous auto-deletes on financial and audit records. | We must *know* what deleting a record cascades to before real customer data exists. | Accidental mass deletion of audit/financial data. | Medium |
| A7 | Clean the seed data: remove out-of-market German/French/Finnish/AI-flavoured test users; add a full Irish test organisation and site (Eircode, EUR, Irish factor). | Out-of-market pseudo-personal data must never ship; the missing Irish fixture is why the Ireland defect survived. | Launching with placeholder PII (personal data) and no Irish regression guard. | Small |
| A8 | Add customer account lifecycle flags — "active" and "archived at" — to organisations. | Without a suspend path, the only lever for a churned customer is deleting their audit evidence. | Forced to delete audit records to offboard a customer. | Small |
| A9 | Allow a supplier invoice to exist without being tied to an "asset" (relax the document-to-asset requirement). | Supplier invoices have no asset; the current rule forces fake assets into the emissions hierarchy — manufactured corruption of the core data. | Corrupted emissions data on the core entity. | Small |
| A10 | Fix the Ireland blocker: accept Eircodes on sites, make UK postcodes optional, and require one or the other. | Ireland has no postcodes; without this an Irish customer literally cannot register the site we are supposed to measure. | Irish launch customers fail at onboarding — the loudest possible failure. | Small |
| A11 | Restrict the "country" field on organisations, sites, suppliers and consultants to our launch markets (GB, IE). | Every jurisdiction rule, aggregation and billing reconciliation reads this value; free text ("UK", "England") breaks them. | Jurisdiction rules silently misapplied. | Small |
| A12 | Restrict all currency fields and the system default currency to GBP/EUR. | Every money aggregation and Stripe reconciliation keys off the currency value. | Mis-aggregated spend and billing errors. | Small |
| A13 | Add a currency field to consultant billing (the only billing table without one). | Undenominated prices in a two-currency launch are unreconcilable. | Ambiguous consultant invoices. | Small |
| A14 | Add provenance detail to emission factors (unit, scope, source, country) and enforce one row per year and activity type. | Factors currently don't state "kg CO₂e per *what*"; duplicate rows silently double-count the product's core number. | Silently wrong carbon figures. | Medium |
| A15 | Load the minimal current-year Irish emission factor set (SEAI/EPA — Sustainable Energy Authority of Ireland / Environmental Protection Agency: grid electricity, gas, common fuels). | A Dublin site computed on UK factors reports silently wrong Scope 2 emissions; wrong numbers are worse than a missing feature. | Wrong numbers filed by Irish customers; credibility collapse. | Small |
| A16 | Record the unit and scope on every emissions entry. | Unit-less quantities make the legally relevant kWh totals an inference — unauditable numbers. | Unauditable regulatory figures. | Small |
| A17 | Forbid negative values on all emission and factor figures. | One negative calculated emission silently corrupts every regulatory total it feeds. | Corrupted SECR (Streamlined Energy and Carbon Reporting) / customer reports. | Small |
| A18 | Widen the file-size field so uploads over 2 GB don't fail. | Invoice bundles can exceed 2 GB; the upload would fail at the customer's highest-value moment. Near-free now, expensive rewrite later. | Public upload failures on large documents. | Small |
| A19 | Add a content fingerprint (checksum) to uploaded documents for duplicate detection. | Deterministic duplicate detection on the primary pipeline entity; near-free on an empty table. | Undetectable duplicate invoices double-counting spend/emissions. | Small |
| A20 | Enforce uniqueness where duplicates corrupt the business: memberships, consultant-client links, monthly billing usage, report versions, and supplier VAT/company numbers. | Duplicates split billing allowances, corrupt isolation rules, and get amplified by AI supplier-matching into emissions data. | Billing errors and corrupted customer data. | Medium |
| A21 | Block writes to the old, weaker invitations table; the secure invitations table is canonical. | The weaker table — no token, expiry or status — is a live security downgrade that is still writable. | An open, weaker invitation path remains exploitable. | Small |
| A22 | Build and rehearse the "anonymise in place" data-erasure procedure (replace a person's email/name, keep the record shell), tested on staging. | Hard deletion is structurally impossible across ~40 relationships; a GDPR erasure request can arrive on day one with a one-month statutory clock. | Untested destructive script against a live customer; ICO exposure. | Medium |
| A23 | Verify data residency: hosting region is UK-London or Ireland, and backups live in the same jurisdiction. | One free check on which every enterprise questionnaire's residency claim depends. | False residency claims to enterprise buyers. | Small |
| A24 | Tidy the busiest flags and timestamps so they can never be blank (backfill, then require values with defaults) on the four hot processing tables. | A blank flag on a hot path is an ambiguous state that workers and suspension logic silently misread. | Silent misprocessing of customer documents. | Small |
| A25 | Restrict queue, billing and role "status" fields to their allowed value lists. | A typo'd status becomes a silent state that workers and billing-limit checks miss. | Silent stuck documents and billing-limit failures. | Small |
| B1 | Ship the data-retention schedule and first automated clean-up jobs (processing logs 90 days; login/email logs 12 months; activity 12–24 months; audit 24 months), plus a retention date on documents. | The plan schedules this for v1.0.1 — nothing ages out of empty tables on day one, but the capability must exist before data accumulates. | Unbounded personal-data accumulation (GDPR minimisation risk). | Medium |
| B2 | Add soft-delete for customer documents (a "deleted at" marker rather than physical removal), with all read paths respecting it. | Plan-scheduled v1.0.1; right while the table is young and cheap to add. | An accidental deletion is unrecoverable support pain. | Medium |
| B3 | Add supplier/organisation name "fuzzy search" with "did you mean?" prompts. | Plan-scheduled v1.0.1–v1.0.2; reduces duplicate supplier creation through the friendly route. | More duplicate supplier records to clean later. | Small |
| B4 | Ship the application-level validation pack: UK VAT checksum, Companies House/CRO number rules, valid postcode/Eircode shape checks, international phone formatting, and EUR defaulting for Irish customers. | Plan-scheduled v1.0.1; this is the approved replacement for the rejected database-level format checks — bad formats are stopped in the app, where format rules belong. | Bad contact/identity data enters at onboarding. | Medium |
| B5 | Harden the audit trail: remove the ability to edit or delete audit rows and drop their "last updated" markers. | Plan-scheduled v1.0.1; the honest, cheap route to tamper-evidence (replacing the rejected hash-chain). | Audit trail is mutable; weakens any dispute defence. | Small |
| B6 | Complete the privacy housekeeping: personal-data inventory, expiry on data-export files, deletion of waitlist/beta data at launch, and support-log search indexes. | Plan-scheduled v1.0.1–v1.0.2; low-cost hygiene that underpins our privacy commitments. | Stale marketing PII and slow DSAR (data subject access request) responses. | Small |
| B7 | Consolidate the two overlapping notification-delivery tables into one. | Plan-scheduled v1.0.1–v1.0.2; mirrors the approved invitations consolidation — two tables answering the same question drift. | Divergent notification records; support confusion. | Small |
| B8 | Allow customer documents to exist without a named uploading member (relax that requirement). | Plan-scheduled v1.0.1; pipeline-uploaded documents have no human uploader, so the rule currently blocks legitimate ingest paths. | Legitimate uploads rejected or forced fake attributions. | Small |

---

## Section 2 — Deferred Changes 🟡 (DEFER TO V1.1)

Genuinely good ideas whose cost, scope, or dependencies make them wrong for the launch window. Each has a named trigger or target version so it is revisited, not forgotten. The six B-window items (B9–B14) are scheduled by the plan at v1.0.2 or later and are therefore deferred here to v1.1 planning.

| ID | Recommendation | Why Deferred | Target Version |
|---|---|---|---|
| C1 | Typed invoice columns (number, date, amounts) on the documents table. | The existing data field already carries this; create typed columns only when query logs prove which are needed. | v1.1 |
| C2 | Hard uniqueness on the document fingerprint. | The fingerprint ships in v1.0; hard-blocking duplicates before we have a duplicate-resolution screen would punish legitimate re-uploads. | v1.1 |
| C3 | Allowed-value lists on the remaining ~20 status fields. | Right mechanism, but doing all of them at once is a redesign, not hardening; the risky five ship in v1.0. | v1.1 |
| C4 | Standardise IP-address storage across the log tables. | Useful for retention/privacy jobs; nothing reads these columns at launch. | v1.1 |
| C5 | Consolidate duplicated contact/identity columns (staff emails, supplier contacts, primary contacts). | Real drift but low-stakes; v1.0 convention stops new writes. | v1.1 |
| C6 | Single canonical source for "read" and "approved" states across messaging and verifications. | Heavy application rework across many surfaces; blocks nothing at launch. | v1.1 |
| C7 | One unified read-only view across the nine-plus audit/activity logs. | Right idea, but there is no auditor or support volume at launch. | v1.1 |
| C8 | County normalisation, arriving with the address-verification feature. | Nothing computes from county today; the verification loop brings normalisation for free. | v1.1 |
| C9 | Constrain the dormant tax/VAT region columns. | Rules on columns serving dormant features are ceremony; apply at feature activation. | v1.1+ |
| C10 | Recompute jobs for drifting counters, plus the remaining ~80 flag/timestamp tidy-ups. | v1.0 checks bound the damage; the real fix is worker logic best done as a sweep. | v1.1 |
| C11 | Floor-area conversion tooling and square-feet deprecation; industry-code input hint. | Labelled square-metre columns ship in the first-patch batch (see B10); only the unit-conversion machinery is deferred here. | v1.1 |
| C12 | Address-verification status fields and the Royal Mail/Eircode lookup integration. | The status fields are inert without the verification feature behind them. | v1.1 |
| C13 | Our own invoices table with sequential numbers and stored VAT evidence. | Stripe-hosted invoices cover UK/IE VAT at launch scale; a second source of truth now would drift. | v1.1 |
| C14 | Dedicated contacts and support-ticket tables. | Inline columns serve launch; freezing table shapes before the workflows are real invites rework. | v1.1 |
| C15 | Full historical Irish factor catalogue, gas-species breakdowns, and the factor-table rename. | The correctness-critical core load ships in v1.0; historical depth is breadth, not correctness. | v1.1 |
| C16 | Proper reporting-period fields and SECR qualification metadata. | An integer year can't name a financial year, but SECR is not a day-one flow; needed before the first SECR season. | v1.1 |
| C17 | Phone/timezone columns on users and organisations. | These earn their keep only with 2FA and invoicing; ship the columns with the features. | v1.1 |
| C18 | Bill-to-site meter (MPAN/MPRN — electricity/gas meter supply numbers) matching logic and site-manager contact fields. | The meter number column ships in the first-patch batch (see B10); only the supplier-matching logic is deferred here. | v1.1 |
| C19 | Per-organisation holiday calendars for support-SLA maths. | A modest v1.1 fix; four-jurisdiction modelling (rejected) is not needed. | v1.1 |
| C20 | Per-user notification channel preferences. | Preferences without per-channel delivery are inert columns. | v1.1 |
| C21 | Move typing/presence indicators to the platform's realtime service. | The interim safeguards ship in v1.0; the platform absorbs this for free when done properly. | v1.1 |
| C22 | Consultant-client identity fields, credit limits, waitlist country, and Xero/QuickBooks sync columns. | None launch-blocking; the sync columns only have meaning once an integration contract exists. | v1.1 (sync columns may slip to v2.0) |
| C23 | Evidence-gated extra indexes (document data search, message search, back-office dashboards). | Build only when query logs or committed screens prove the need — the audit's own stated criterion. | v1.1 |
| C24 | Self-service erasure UI, privacy-inventory automation, consent-capture fields. | The tested manual erasure procedure ships at launch; self-serve layers onto it later. | v1.1 |
| C25 | Merge the three processing queues into one. | The multi-stage pipeline is an approved architecture decision; v1.x manages it with contracts, not redesign. | v2.0+ |
| C26 | API-key and webhook infrastructure for an external API product. | There is no integration customer; revisit when the first one signs. | v2.0 |
| C27 | Enterprise single-sign-on (Entra ID) columns. | Trivial to add when the first enterprise procurement demands it. | v2.0 |
| C28 | Supplier-portal identity model. | Suppliers are data rows today; half-built portal columns are exactly the drift our architecture rules guard against. | v2.0 |
| C29 | Activate the dormant EU sustainability-reporting (CSRD/ESRS) fields. | EU scope is future by definition — but Ireland has transposed CSRD, so this is a standing watch item for large Irish signings. | v2.0+ (v1.1 watch item) |
| C30 | Envelope encryption (vault/KMS) for supplier bank details. | Display masking covers the launch risk; the provider decision must not be rushed inside a launch sprint. | v1.1 |
| B9 | Supplier sort-code column and last-4-only bank-detail masking in API responses. | Plan schedules the masking at v1.0.2; batch with the C30 bank-security work. | v1.1 |
| B10 | Labelled square-metre floor-area columns, site meter number, and direct site reference on emissions entries. | Plan schedules these at v1.0.2; all are useful reporting enrichments, none launch-critical. | v1.1 |
| B11 | Remaining modest value checks (timezone list, sensible date pairs, 0–100 percentages, non-negative counts). | Plan schedules at v1.0.2; the risky status/quantity checks already ship in v1.0. | v1.1 |
| B12 | Allowed-value list on the notification recipient type. | Plan schedules at v1.0.2; low-risk field behind the v1.0 queue/billing status checks. | v1.1 |
| B13 | De-duplicate the two overlapping default tax-rate columns. | Plan schedules at v1.0.2; convention prevents drift until then. | v1.1 |
| B14 | Standardise the AI confidence-score format. | Plan schedules at v1.0.2; display-level inconsistency only. | v1.1 |

---

## Section 3 — Rejected Changes 🔴 (REJECT)

Rejected on the plan's reasoning: each either conflicts with an approved architecture decision, is over-engineered for a ~50-customer pre-revenue product, is low-value, or is premature optimisation. Each rejection pairs with a cheaper control that does ship.

| ID | Recommendation | Reason Rejected |
|---|---|---|
| D1 | Format-checking rules (VAT, postcode, Eircode, phone, email, company numbers) hard-coded into the database. | Conflicts with an approved architecture decision: format rules belong in the application. Hard-coded rules reject valid edge cases and rot as third-party registries change. The approved app-layer validation pack (B4) is the correct home. |
| D2 | "Index everything" programme — roughly 60 indexes across all tables. | Over-engineered, ~3× over-scoped: many indexes would sit on tables that are static, never searched, or deleted at launch, while slowing every write on the hot path. 15–18 targeted indexes ship instead. |
| D3 | Blanket advanced search indexes on all free-form data blobs. | Over-engineered: these indexes rewrite on every update of our busiest tables, to serve queries nobody runs. One security-related exception ships; the rest are evidence-gated (C23). |
| D4 | Monthly partitioning of the nine-plus log tables. | Premature optimisation: our year-one volumes are trivially handled by ordinary indexes plus retention deletes. Documented trigger for revisiting (10–20M rows per table). |
| D5 | Cryptographic "hash chain" tamper-proofing of the audit trail. | Low value — security theatre: the party verifying the chain is the same party that could rewrite it, so it proves nothing to an external auditor. Privilege lockdown plus point-in-time backups (B5) is the honest control. |
| D6 | Merging the nine-plus audit/activity log tables into one. | Conflicts with an approved architecture decision (per-domain logs are frozen); a read-only view (C7) delivers the same benefit without rewriting every call site. |
| D7 | Replacing list-style columns with junction tables. | Conflicts with an approved architecture decision; the existing structure works fine at our scale and the churn buys nothing measurable. |
| D8 | Converting status fields to a rigid database "enum" type. | Conflicts with an approved architecture decision: that type makes every future new status value a painful schema change. Allowed-value lists (A25, C3) deliver the same protection flexibly. |
| D9 | A county lookup table (26 Irish + 6 NI + UK ceremonial counties). | Low value: nothing computes from county in either market, and it imports Dublin city/county and Derry/Londonderry edge-case debt for zero consumers. |
| D10 | UK "nation" field plus four-jurisdiction bank-holiday modelling. | Low value and over-engineered: no feature consumes it; nation is derivable from postcode area, and per-organisation holiday dates (C19) solve the real problem. |
| D11 | A second, parallel country-code column alongside the existing one. | Over-engineered: the cure for a single-source-of-truth problem cannot be a second source of truth. Restricting the existing field (A11) fixes the actual defect. |
| D12 | Industry-classification (SIC) lookup table and Companies House schema artefacts. | Low value: nothing computes from the industry code at launch; a lookup table is maintenance in search of a requirement. |
| D13 | A separate Irish company-number column alongside the existing one. | Over-engineered duplication: one company-number column with country-aware app validation serves both jurisdictions; two columns would split the uniqueness rule. |
| D14 | Forbidding two suppliers with the same name within an organisation. | An incorrect integrity rule: same-name suppliers legitimately exist (e.g. two "City Electrical" branches); the rule would force "City Electrical 2" workarounds that pollute the data. Uniqueness on VAT/company numbers (A20) plus fuzzy matching (B3) is the right control. |
| D15 | Accounting-integration identity columns added now, "just in case". | Premature: speculative columns with no integration contract invite improvised meanings the real feature must unpick. Added when Xero/QuickBooks is scoped (C22). |
| D16 | API-key and webhook tables in v1.x. | Premature: no integration customer exists to consume them. Revisit at v2.0 (C26). |
| D17 | Deleting dormant EU/US compliance columns as "scope hygiene". | Conflicts with our additive-only architecture posture and is irreversible: some of these may activate for CSRD-scope Irish customers. Dormant is not deleted (C29 watch item). |
| D18 | Our own two-factor-authentication and account-lockout columns. | Conflicts with an approved architecture decision: the login platform owns authentication; parallel auth state creates two drifting credential truths. Interim obligation: stop advertising 2FA as enforced until the platform feature ships. |
| D19 | Indexes on static reference, marketing and presence tables. | Low value and premature: on dozens-of-rows tables the index is dead weight; marketing tables are purged at launch; presence tables move to the realtime service. |
| D20 | Database triggers keeping address text blocks synchronised with structured address fields. | Over-engineered: hidden write-path machinery solving a procedural problem. A simple writing convention — structured fields are the truth, text blocks are generated displays — closes the risk. |

---

## Section 4 — Risks

The top ten remaining risks before launch, ranked. All are drawn from the plan; none is new.

1. **Critical — Unverified foundations (indexes, isolation rules, delete behaviour, table relationships).** The original schema dump showed none of these. They may exist in the actual migration files — but until someone inspects them, we are scoring an evidence pack, not a database. The migration-file inspection is the plan's "action zero" and the first binding condition.
2. **Critical — Tenant isolation must be proven, not assumed.** Whatever the migration files contain, a scripted cross-tenant penetration test must return zero leaked rows for every user role. One cross-tenant sighting after launch is a reportable ICO/DPC incident.
3. **Critical — The data-erasure procedure is launch-gated.** A GDPR deletion request can arrive on day one with a one-month statutory clock, and hard deletion is structurally impossible. The rehearsed anonymise-in-place runbook (with a clean residual-data scan) is non-negotiable.
4. **Critical — Irish market data quality.** If the Irish factor load slips, the only acceptable fallback is gating Irish sign-ups at onboarding — never shipping Irish customers UK factors and calling the result Scope 2. A wrong carbon number is worse than a missing feature.
5. **High — Irish site registration must be end-to-end proven.** The Eircode fix must be exercised by the Irish fixture test (Irish organisation, site, EUR, Irish factor) in every release candidate — this is the regression guard whose absence let the defect survive to audit.
6. **High — Seed-data cleanup.** Out-of-market test users with pseudo-personal data must be removed before launch, and replaced with the Irish fixtures. Shipping leftover test PII is a privacy incident waiting to be discovered.
7. **High — Rollback exposure on two one-way changes.** Credential hashing cannot be reversed (only re-issued) and the organisation backfill cannot be un-backfilled. Both rollbacks must be rehearsed on staging before the first deploy, and the rollback strategy formally accepted (Section 5).
8. **Medium — Processing-queue complexity.** The three overlapping processing queues are an approved architecture decision we are deliberately not redesigning. The interim safeguards (status value lists, blank-flag tidy-ups, deduplication) contain the risk, but the consolidation question returns at v2.0 planning and should be watched.
9. **Medium — Validation over-rejection.** The new app-layer validation pack risks rejecting legitimate edge-case addresses or numbers. It ships with a shadow-mode (log-only) period and per-rule feature flags so enforcement can be tuned without database change.
10. **Medium — Deferred duplicate enforcement.** Document fingerprints ship without hard uniqueness until the duplicate-resolution screen exists (v1.1). Until then duplicates are *detected* but not *prevented* — support should monitor for them in the first weeks.

---

## Section 5 — Final Approval Checklist

- ☐ I have reviewed all 33 approved recommendations in Section 1 and understand what each means for customers, compliance, cost or launch risk.
- ☐ I confirm none of the approved changes conflicts with an approved architecture decision (the plan confirms all architecture-conflicting remedies were rejected, not approved).
- ☐ I confirm UK and Ireland launch requirements are fully covered, including Irish Eircode site registration and the SEAI/EPA Irish emission-factor load, and I accept the fallback of gating Irish sign-ups if the factor load slips.
- ☐ I confirm customer-data isolation (row-level security) is unaffected by the approved changes, and that the isolation penetration test is a binding launch gate.
- ☐ I confirm the application-level impact is understood: login/reset/invite flows change, upload paths change, and the validation pack changes onboarding behaviour, with shadow-mode and feature flags as the safety mechanism.
- ☐ I confirm the rollback strategy is accepted, including the two one-way changes (credential hashing — re-issue, not reverse; organisation backfill — snapshot restore only) and their staging rehearsals.
- ☐ I confirm the deferred items (Section 2) have named target versions and will be revisited at v1.1 planning, and the rejected items (Section 3) will not be built.
- ☐ I approve implementation of the Section 1 changes as the committed launch programme.

---

## Section 6 — Go / No-Go Recommendation

**🟡 GO WITH CONDITIONS.**

CarbonTally is approved to launch in the UK and Ireland once — and only once — the following binding conditions are met, mirroring the plan's conditional-GO verdict:

1. **Every Section 1 item completed and evidenced.** All 25 launch-gating items (A1–A25) verified on staging with the named proof for each (e.g. the Irish facility registers end-to-end; the isolation penetration test returns zero cross-tenant rows; duplicate and negative-value writes are rejected). There is no partial credit: 24 of 25 is a No-Go. The eight approved B-window items (B1–B8) are committed to the v1.0.1 patch window immediately after launch.
2. **The migration-file inspection gate passed.** Before remediation is scored complete, the actual Supabase migration files must be inspected to confirm which protections (indexes, isolation policies, relationships, value rules) genuinely exist — the audit's own evidence caveat makes this the mandatory action zero.
3. **The Irish fixture test passed and made permanent.** An Irish organisation with an Eircode site, EUR currency and an Irish emission factor must register, upload and report correctly in every release candidate — and if the Irish factor load slips, Irish sign-ups are gated at onboarding rather than shipping wrong Scope 2 numbers.

With these conditions met, the remaining deferred and rejected items carry no launch risk at our scale, and the product can proceed to revenue with known, scheduled hygiene debt.
