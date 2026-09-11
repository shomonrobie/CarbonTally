# CarbonTally — Group Data Retention, Archival and Technical Anonymization Policy

**Document type:** Corporate operational policy (internal standard)
**Document status:** DRAFT for review by qualified legal counsel (UK / Ireland / EU) and Product Owner ratification
**Version:** 0.1 (draft)
**Effective date:** [EFFECTIVE DATE — TO BE INSERTED UPON RATIFICATION]
**Last updated:** 30 August 2026
**Document owner:** [TO BE ASSIGNED — e.g., Chief Operating Officer / Data Protection Officer function]
**Review cycle:** Annual, or on material change to processing, law, or the AI training programme
**Classification:** Internal — Confidential (contains the company's operational and AI-training data strategy)

> **Governing statement.** This policy establishes CarbonTally's formal operating standard for the retention, archival and technical anonymization of data across all production systems. Where a section describes a capability that is not yet implemented, the capability is expressly marked **[PRODUCT GAP — REQUIRES IMPLEMENTATION]** and listed in Section 12. Nothing in this policy is legal advice, and nothing constitutes a certification of GDPR, SECR, CSRD or EU AI Act compliance. The legal bases and statutory periods cited require confirmation by qualified counsel prior to ratification (Section 15).

---

## 1. Purpose and Scope

### 1.1 Purpose

1.1.1 This policy defines how CarbonTally retains, archives, transitions, anonymizes and — where required — deletes data across its production estate, in a manner that:

(a) satisfies UK GDPR, the UK Data Protection Act 2018, the EU GDPR, and the Irish Data Protection Act 2018, as applicable to each data subject population;
(b) preserves CarbonTally's business value in historical emissions telemetry, Scope 1/2/3 data points and emission matrices by converting them into **anonymized, aggregated datasets** that may lawfully be retained and used for machine-learning and AI optimisation purposes outside the scope of data-protection law (Recital 26, GDPR / UK GDPR);
(c) enforces a strict **30-day rolling backup rotation** for active disaster-recovery (DR) infrastructure, accepting that data cannot be surgically removed from cold backup blobs without corrupting the snapshot, and relying on natural lifecycle expiry to purge anonymized-or-deleted records from backups within 30 days;
(d) respects mandatory statutory retention for corporate tax, financial and environmental-compliance records (6–7 years, Section 9); and
(e) aligns with the EU AI Act's data-governance expectations for any training datasets used to develop CarbonTally models.

### 1.2 Systems in scope

| System / estate | Provider / host | Data held | Retention treatment under this policy |
|---|---|---|---|
| Primary relational database | Supabase PostgreSQL (project `pvwiojoyaqywtydzcpbg.supabase.co`; region to be confirmed) | Organisations, members, facilities, assets, vehicles, suppliers, extraction items, emissions logs, calculation snapshots, audit logs, messaging, notifications, billing records | Table-by-table per Schedule A |
| Object storage | Supabase Storage (`documents` bucket) | Uploaded documents (PDF/CSV/XLSX/images) | Account PII / document lifecycle per §6 |
| Authentication store | Supabase Auth | Credentials, sessions, OAuth identities, user profiles | Deletion/anonymization per §6–§7 |
| Realtime | Supabase Realtime | Message/notification streams | Retention via database records |
| Backend API / processing | Render | Transient processing, server logs, OCR artefacts, environment config | Logs per Schedule A; in-memory processing not retained |
| Frontend / CDN | Vercel | Static assets, client transit, edge logs | Logs per Schedule A |
| Transactional email | Resend | Recipient addresses, email content | Business correspondence per Schedule A |
| Disaster-recovery backups | Provider-managed (Supabase PITR/backups) | Full snapshots of database + storage | §8 — 30-day rolling rotation |
| AI training datasets (future) | To be determined | Anonymized aggregated emissions datasets | §10 — retained indefinitely under anonymity |

### 1.3 Out of scope / boundaries

1.3.1 **Public website marketing data.** Separate handling for any future marketing analytics will be governed by the Privacy Policy and Cookie Policy, and is not covered by this policy except where it flows into the datasets below.

1.3.2 **Customer-owned environments.** Data held in customer systems or consultant/Processing Entity systems outside CarbonTally's control is outside this policy; customer responsibility applies.

1.3.3 **Special-category data.** CarbonTally does not intentionally process special-category data (UK GDPR Art. 9 / GDPR Art. 9) and requires that customers do not upload it without written arrangement. Any accidental ingestion is handled under the incident procedure (§14).

## 2. Policy Principles and Legal Basis

2.1 **Anonymization over hard deletion.** CarbonTally's strategic default is that historical emissions telemetry is **not** destroyed. Account PII and corporate tenant identifiers are permanently and irreversibly stripped (Section 7), and the residual operational data is aggregated into anonymous datasets retained indefinitely for AI development.

2.2 **Legal foundation — Recital 26.** The principles of data protection do not apply to anonymous information — information relating to an identified or identifiable natural person whose identity cannot be re-identified by reasonable means. To rely on Recital 26 (and its UK GDPR counterpart), anonymization must be **irreversible** and CarbonTally must not retain a key, mapping, or other means of re-identification. This policy therefore prohibits pseudonymization-only treatment of records entering the anonymized dataset. `[LEGAL REVIEW — confirm Recital 26 reliance with counsel for the UK, EU and Irish regimes]`

2.3 **Controller/processor roles.** Where CarbonTally processes customer data as a processor, retention and deletion are performed only on documented instructions (via the Service and the DPA). Where CarbonTally processes account, billing, support and usage data as a controller, this policy governs directly. The DPA (draft) and Terms of Service (draft) are incorporated by reference.

2.4 **No data invented and no data silently retained.** Retention durations are configured explicitly (`system_settings`), surfaced at `/api/v3/settings/retention`, and enforced server-side. No retention value is invented by the enforcement code. `[LEGAL REVIEW]`

## 3. Definitions

3.1 **Account PII** — personal data identifying an individual account holder or member (name, email, password hashes, OAuth identity, IP address, personal contact details), and personal data embedded in documents.

3.2 **Corporate tenant identifiers** — organisation name, company number, registered/geographic address, consultant/client identifiers and other attributes that identify the corporate tenant to which records belong.

3.3 **Operational / emissions telemetry** — extraction items, activity quantities, mapped factors, unit values, Scope 1/2/3 classifications, calculation results, emission matrices, validation outcomes and quality metrics, stripped of identifiers.

3.4 **Anonymized Aggregated Dataset** — data that has undergone irreversible technical anonymization (Section 7) and is aggregated to a level where no data subject or tenant is identifiable.

3.5 **Quarantine** — the post-deletion window during which an account's data is hidden from production but recoverable, to catch accidental deletion.

3.6 **DR archive / backup blob** — a snapshot, point-in-time-restore (PITR) or archive copy held for disaster recovery, in which target-row deletion is not technically feasible without corrupting the snapshot.

3.7 **Model inversion / linkage attack** — an attempt to infer individual records or re-identify data subjects from aggregate or model outputs.

3.8 **Retention Period** — the period for which a data category is retained in identifiable form (Schedule A), after which it is anonymized (default) or deleted (where required).

## 4. Data Classification

| Class | Description | Examples | Treatment |
|---|---|---|---|
| **C1 — Account PII** | Identifies a natural person | Name, email, password hash, session, OAuth identity, IP address | Deletion or irreversible anonymization on account deletion (§6) |
| **C2 — Corporate tenant identity** | Identifies the tenant | Company name, company number, address, tenant UUID, consultant/client mapping | Stripped irreversibly on account deletion (§6–§7) |
| **C3 — Business/operational records (identifiable)** | Records tied to tenant/individual during statutory retention | Invoices, tax-relevant records, SECR/CSRD supporting records, correspondence | Retained per Schedule A (§9), then anonymized/deleted |
| **C4 — Operational emissions telemetry (identifiable)** | Emissions data linked to tenant via keys | Extraction items, emissions logs, calculation snapshots, factor mappings | Anonymized per §7 at end of retention |
| **C5 — Anonymized aggregated data** | No identifier, aggregated | Aggregated emission matrices, model training sets | Retained indefinitely (§10) |
| **C6 — Audit & evidence records** | Immutable provenance chain | `audit_logs`, `calculation_snapshots` (append-only), evidence records | Never purged by retention jobs; subject to statutory/contractual limits §9.6 `[LEGAL REVIEW]` |

## 5. Retention Schedule

5.1 The authoritative retention durations are set in **Schedule A** (Section 16). Durations are configuration-driven via `system_settings` (`document_retention_days`, `data_retention_days`, `audit_log_retention_days`, `backup_retention_days`) and enforced server-side at `/api/v3/settings/retention`. `[PRODUCT GAP — see Section 12 for enforcement status]`

5.2 Default durations proposed for ratification:

| Domain | Proposed period | Rationale | Marker |
|---|---|---|---|
| Account PII (C1) | Deleted/anonymized at account deletion | Erasure principle | §6 |
| Documents (C4/C1) | 30 days post-account-deletion (via quarantine), else per configured `document_retention_days` | Quarantine + lifecycle | §6–§8 |
| Business/tax/financial records (C3) | 6–7 years from end of relevant accounting period | UK/Ireland statutory (Section 9) | §9 |
| Operational emissions telemetry (C4) | End of statutory retention, then anonymized | Business value + Recital 26 | §7 |
| Anonymized aggregated data (C5) | Indefinite | Recital 26; AI training | §10 |
| Audit/evidence (C6) | Indefinite (immutable) unless law requires otherwise | Auditability invariant | §9.6 |
| Backups (DR blobs) | 30-day rolling rotation | §8 | §8 |

5.3 No duration is applied to a domain unless it is configured; `None` means "not configured — never purged". `[PRODUCT GAP — see §12]`

## 6. Account Deletion and the 30-Day Transition Window

### 6.1 Operational flow

The account-deletion lifecycle is:

```
Deletion triggered
   → (1) Quarantine / soft-delete hide        [Day 0 – Day 14–30]
   → (2) Cooling-off / accidental-closure catch[Day 14 – Day 30]
   → (3) Irreversible cryptographic strip of
         Account PII + corporate tenant keys   [Day 30]
   → (4) Residual data moves to the Anonymized
         Aggregated Data Warehouse             [Day 30]
   → (5) Natural expiry from DR backups        [Day 30 – Day 60]
```

### 6.2 Stage 1 — Trigger and quarantine (Day 0)

6.2.1 Deletion is triggered by the account owner (or by CarbonTally per the Terms, e.g., termination for breach).

6.2.2 On trigger, all account data is **hidden from production access** (soft-delete convention using `deleted_at`), including: authentication disabled, workspaces inaccessible, documents and extracted data unavailable to users and Processing Entities, messaging suspended.

6.2.3 A 14-day to 30-day quarantine window is applied to catch accidental closures and to allow the customer to exercise any statutory or contractual withdrawal right. During quarantine the account is recoverable in full by the owner. `[PRODUCT GAP — quarantine/recovery UI does not yet exist; see §12]`

### 6.3 Stage 2 — Cooling-off (Day 14–30)

6.3.1 During the window, CarbonTally notifies the account owner of the imminent irreversible anonymization, including the exact date on which the account and its identifiers will be stripped. No further action is required from the owner; the process proceeds automatically.

6.3.2 The account may be restored in full at any point before the end of the window.

### 6.4 Stage 3 — Irreversible stripping (Day 30)

6.4.1 At the end of the window, a scripted, irreversible process executes:

(a) **Account PII (C1):** cryptographic destruction of PII fields (names, emails, password hashes, OAuth identities, session records) — overwritten or destroyed such that the data cannot be recovered from the primary database;
(b) **Corporate tenant identifiers (C2):** destruction of tenant keys and attributes (company name, company number, address, tenant UUID, consultant/client mapping);
(c) **Document bytes:** destruction of stored document objects (and database rows referencing them) in line with the existing permanent-delete convention (`DELETE .../files/{file_id}/permanent`);
(d) **Linkage tables:** destruction of membership, invitation, role and participant mappings.

6.4.2 The output is a **de-identified residual dataset** containing only operational telemetry (C4) with no direct or indirect link to the deleted account. `[PRODUCT GAP — the deletion and stripping pipeline does not yet exist; see §12]`

### 6.5 Stage 4 — Transfer to the Anonymized Aggregated Data Warehouse (Day 30)

6.5.1 Residual de-identified records enter the anonymization and aggregation pipeline (Section 7) and are written to the Anonymized Aggregated Data Warehouse.

6.5.2 No record enters the warehouse unless it satisfies the anonymization acceptance criteria in Section 7.6.

### 6.6 Stage 5 — Backup expiry (Day 30–60)

6.6.1 Records removed from production are **not restored** from DR archives (Section 8) and expire naturally through the 30-day backup rotation.

## 7. Anonymization and Aggregation Rigor

### 7.1 Objective

7.1.1 The objective is to break, permanently and irreversibly, the **direct and indirect identification linkability** of the data, such that re-identification is not reasonably possible by any means likely to be used (Recital 26 / UK GDPR, and the Article 29 WP / EDPB guidance on anonymization techniques), and to mitigate model-inversion and linkage attacks.

### 7.2 Techniques employed (required standard)

7.2.1 **Key / attribute destruction.** Unique identifiers (UUIDs, membership keys, derived identifiers) are destroyed — not merely replaced with stable pseudonyms.

7.2.2 **Field suppression.** PII fields (names, emails, addresses, contact data, free-text fields that may contain names) are removed.

7.2.3 **Generalisation / binning.** Continuous attributes (e.g., quantities, distances, fuel volumes) are binned where their precise value could uniquely identify a tenant; temporal fields are generalised to periods where needed.

7.2.4 **Aggregation.** Records are aggregated to tenant-independent statistics (e.g., industry-sector × activity-type × region matrices) such that no cell is attributable to a single tenant or individual.

7.2.5 **k-anonymity floor.** Aggregated outputs must satisfy a k-anonymity threshold (recommended k ≥ 20) on any quasi-identifier combination; cells below the floor are suppressed or merged. `[PRODUCT GAP — no anonymization engine exists; the k value requires PO + counsel sign-off]`

7.2.6 **No retained mapping.** No key, hash, salt, lookup table, or re-identification script is retained that could reverse the process. Irreversibility is a design invariant and is verified by test.

### 7.3 Prohibited practices

7.3.1 Pseudonymization-only treatment (reversible key retained) is **not** anonymization and does **not** remove data from the scope of data protection law.

7.3.2 Use of reversible encryption or hashing with a retained key, or storage of the original identifiers in a secondary location, is prohibited for data designated for the anonymized warehouse.

### 7.4 Re-identification risk assessment

7.4.1 Before any dataset enters the warehouse, a documented re-identification risk assessment is performed, considering:

(a) the identifiability of the population (e.g., rare activity types, small tenant counts in a sector);
(b) quasi-identifiers present in operational telemetry (sector, region, activity type, quantity bands, date);
(c) the likelihood and impact of re-identification, including model-inversion risk if the dataset is used to train models; and
(d) the risk of linkage with external datasets.

7.4.2 The assessment is recorded in the dataset's entry in the AI Training Data Register (Section 10). `[PRODUCT GAP — register does not yet exist]`

### 7.5 Verification and testing

7.5.1 Anonymization outputs are validated by automated tests that assert: no PII fields present; no tenant keys present; k-anonymity floor satisfied; no known re-identification script succeeds; and determinism/irreversibility properties hold.

7.5.2 A documented sample is subject to manual adversarial review before first use of any new dataset class. `[PRODUCT GAP]`

### 7.6 Acceptance criteria (gate)

7.6.1 A dataset may enter the warehouse only when all of: (a) key destruction verified; (b) PII suppression verified; (c) k-anonymity floor met; (d) risk assessment completed; (e) no retained mapping exists. The gate is enforced by the engineering pipeline and evidenced in the dataset record.

## 8. The 30-Day Backup Mitigation Strategy

### 8.1 Context and technical limitation

8.1.1 CarbonTally operates provider-managed disaster-recovery backups (Supabase-managed backups/PITR for the database and storage). **It is not technically feasible to surgically delete an individual account's rows or objects from a cold backup blob without corrupting the snapshot.** This policy therefore does not attempt target-deletion within backups.

### 8.2 The 30-day rolling rotation standard

8.2.1 All active DR infrastructure operates a **strict 30-day rolling rotation**: no backup snapshot is retained for more than 30 days from capture, enforced by automated lifecycle policies at the provider level and verified by CarbonTally. `[PRODUCT GAP — rotation configuration at the provider level must be verified/enforced; see §12]`

8.2.2 If an account is deleted or anonymized on day D, its records will be absent from any snapshot captured after D, and the last snapshot containing them (captured before D) will **naturally expire at or before D+30** through the rotation.

### 8.3 Non-restoration commitment

8.3.1 Records that have been deleted or anonymized are **never restored** from backup into active production, except where the record is still within the quarantine window (Section 6.2.3) and restoration is part of the authorised recovery process.

8.3.2 Backup restoration is performed only for the DR purposes documented in the incident and business-continuity procedure, and never to resurrect data after the quarantine window has closed.

### 8.4 Verification

8.4.1 Automated checks confirm: (a) backup age never exceeds 30 days; (b) rotation lifecycle policies are active; (c) restoration drill logs demonstrate that post-anonymization restoration does not occur. Findings are reported to the Data Protection function. `[PRODUCT GAP — monitoring/verification does not yet exist]`

## 9. Regulatory Justifications for Retention (Pre-Stripping Periods)

### 9.1 Statutory corporate and tax retention (United Kingdom)

9.1.1 **Companies Act 2006, s.388** requires companies to keep accounting records for **6 years** (public companies) or **3 years** (private companies) from the end of the financial year. HMRC requires records to support tax returns for **6 years** (including VAT, PAYE and corporation tax). CarbonTally standardises on **6 years** from the end of the relevant accounting period as the minimum pre-stripping period for financial and tax-relevant records. `[LEGAL REVIEW]`

### 9.2 Statutory corporate and tax retention (Ireland)

9.2.1 **Companies Act 2014, s.283** requires companies to preserve accounting records for **6 years** after the transactions they record; the **Taxes Consolidation Act 1997, s.886** requires records for **6 years** for tax purposes. CarbonTally standardises on **6 years** for Irish-relevant records. `[LEGAL REVIEW — confirm the treatment of any "7-year" contractual or sector convention; a 7-year band may be applied as a compliance margin where customers contractually require it]`

### 9.3 The 6–7 year pre-stripping band

9.3.1 Where records are required for corporate tax, financial audit, or mandatory environmental reporting, they are retained in identifiable form for **6 years minimum**, and up to **7 years** where a contractual, sector or regulatory requirement so dictates, measured from the end of the relevant accounting/reporting period (the "**6–7 year band**").

9.3.2 At the end of the band, records are processed in accordance with Section 6–7 (anonymized by default; hard-deleted where required by law or contract).

9.3.3 Records are retained only to the extent required; the band is not a reason to retain data that was never subject to the statutory obligation.

### 9.4 SECR (UK) — Companies (Strategic Report) (Climate-related Financial Disclosure) Regulations 2022

9.4.1 SECR disclosure forms part of the strategic report filed at Companies House and becomes part of the public record. The **supporting underlying data** (activity data, calculations, evidence) is retained for at least the 6–7 year band to support the disclosure, potential restatement, audit and regulator enquiries.

9.4.2 CarbonTally does not guarantee statutory compliance (see the Terms of Service draft); this section supports the data-retention rationale only.

### 9.5 CSRD (EU) — Directive (EU) 2022/2464

9.5.1 For customers in scope of CSRD, sustainability information is subject to assurance and may need to be supported after reporting. Underlying data supporting CSRD reporting is retained for the 6–7 year band, aligned with the customer's financial record retention obligations. `[LEGAL REVIEW — confirm interaction with customer-specific regimes]`

### 9.6 Audit and evidence records — the exception

9.6.1 `audit_logs`, `calculation_snapshots` and evidence records are **append-only and immutable** by design. They are **not subject to retention purging** (a CarbonTally security/auditability invariant). Retention of such records beyond the statutory band is limited to what is required for legal or regulatory purposes and is documented. This exception requires legal confirmation before customer-facing statements are made. `[LEGAL REVIEW]`

### 9.7 Limitation of actions

9.7.1 Contractual limitation periods (e.g., 6 years for simple contracts under the Limitation Act 1980 in England and Wales) are a further rationale for the 6-year minimum retention of contract and billing records. `[LEGAL REVIEW — confirm for Irish law: Limitation Act 1957 (6 years)]`

## 10. AI Training Data Governance (EU AI Act alignment)

### 10.1 Scope

10.1.1 CarbonTally intends to use Anonymized Aggregated Datasets (C5) to train machine-learning and AI optimisation models for extraction, mapping, factor matching and validation. This section governs those datasets.

### 10.2 Training on anonymized data only

10.2.1 **No non-anonymized customer data is used for AI training.** Only datasets that have passed the Section 7 gate (irreversible anonymization, aggregation, k-anonymity floor, risk assessment) may enter any training pipeline. This is a hard control, not a preference.

10.2.2 Any future AI-assisted processing of live customer documents (as contemplated by the Terms of Service draft §10) is a separate processing activity with its own subprocessor and transfer controls, and is not governed by this training section.

### 10.3 EU AI Act alignment

10.3.1 **Data governance (Art. 10):** training datasets are documented for accuracy, representativeness and bias; the anonymization gate and the AI Training Data Register implement the data-governance expectations. As at the date of this draft, the general-purpose-AI obligations of the AI Act are in force; CarbonTally will maintain the relevant documentation (model cards / technical documentation) before any model is deployed. `[LEGAL REVIEW — confirm applicable AI Act obligations as of deployment date]`

10.3.2 **No unlawful extraction:** datasets are derived solely from data CarbonTally processes lawfully; no web-scraping or unlawful acquisition of personal data is used for training.

10.3.3 **Copyright/transparency:** where training uses any third-party or generated content, the AI Act transparency and documentation requirements are applied. `[LEGAL REVIEW]`

### 10.4 AI Training Data Register

10.4.1 A register is maintained recording, for each training dataset: source, anonymization method and version, risk assessment, k-anonymity floor applied, verification evidence, retention status (indefinite), and AI Act documentation references. `[PRODUCT GAP — register does not yet exist]`

## 11. Roles and Responsibilities

| Role | Responsibilities |
|---|---|
| **Data Protection function / DPO (if appointed)** | Owns this policy; advises on legal bases; reviews risk assessments; approves dataset entries; liaises with supervisory authorities; reports to the Board. `[LEGAL REVIEW — confirm whether a DPO is required]` |
| **Engineering** | Implements and tests deletion, anonymization, aggregation, scheduler and backup-rotation controls; maintains the register; performs the §7 verification tests. |
| **Operations / Security** | Operates the DR rotation, incident response, access controls; verifies non-restoration; monitors retention jobs. |
| **Product / Data Science** | Designs aggregation schemas; documents training datasets; operates the AI gate; ensures no non-anonymized data enters training. |
| **Legal counsel (external)** | Confirms statutory periods, Recital 26 reliance, AI Act and cross-border positions before ratification. |
| **All staff** | No manual deletion/anonymization of production data outside documented procedures. |

## 12. Implementation Status and Product Gaps

**Honest statement:** this policy sets the target operating standard. The following capabilities are **not yet implemented** in the current product and must be delivered before the associated sections can be asserted as live:

| # | Required capability | Policy § | Current status | Owner | Priority |
|---|---|---|---|---|---|
| 1 | Account and organisation deletion endpoints + UI | §6 | **Not implemented** — no deletion endpoints exist (audit, 2026-08-30) | Engineering | P0 |
| 2 | Quarantine (14–30 day) + recovery UI | §6.2 | **Not implemented** | Engineering | P0 |
| 3 | Irreversible PII/tenant-key stripping pipeline | §6.4 | **Not implemented** — no anonymization code exists in the codebase | Engineering + Data Science | P0 |
| 4 | Anonymization engine (suppression, generalisation, aggregation, k-anonymity, verification) | §7 | **Not implemented** | Data Science + Engineering | P0 |
| 5 | Anonymized Aggregated Data Warehouse | §6.5 | **Not implemented** | Engineering | P1 |
| 6 | Retention scheduler (automated `enforce_retention --apply` on a schedule) | §5 | **Partial** — CLI exists (`backend/tools/enforce_retention.py`), dry-run default, no scheduler; only `document_retention_days` enforced (soft-delete) | Engineering | P1 |
| 7 | Backup rotation verification + provider lifecycle enforcement | §8.2 | **Not verified** — provider-managed; rotation config must be confirmed | Ops + Engineering | P1 |
| 8 | Backup non-restoration monitoring | §8.4 | **Not implemented** | Ops | P2 |
| 9 | AI Training Data Register + model documentation | §10.4 | **Not implemented** — AI features are not yet wired into production | Data Science + Engineering | P1 |
| 10 | Hard-delete support for records requiring deletion (vs anonymization) | §6/§7 | **Partial** — document permanent-delete exists at v2 (`/api/organizations/files/{file_id}/permanent`); no user-facing deletion UI | Engineering | P1 |

12.2 Until items 1–4 are delivered, customer-facing documents (Privacy Policy draft §8) must continue to state the limitation honestly, and deletion requests are handled manually where operationally possible.

## 13. Monitoring, Auditing and Compliance

13.1 Retention and anonymization operations are logged and auditable; audit and evidence tables are never purged by retention jobs.

13.2 Quarterly compliance checks verify: configured durations match Schedule A; enforcement runs are logged with `dry_run=False` evidence; backup age ≤ 30 days; no restoration of post-anonymization records; dataset gate evidence exists for every warehouse dataset.

13.3 Material deviations are escalated to the Data Protection function and the Board, recorded in the Legal Risk Register, and remediated on a defined timeline.

## 14. Breach and Incident Handling

14.1 A Personal Data Breach (including any incident that could compromise the irreversibility of anonymization or cause re-identification) is handled under the incident procedure and the DPA draft §8 (notification to affected controllers without undue delay; assistance with supervisory-authority notification).

14.2 Anonymization failures (e.g., a dataset found to contain identifiers) are treated as incidents; the dataset is quarantined from training, corrected or destroyed, and the §7 verification suite is updated.

## 15. Review, Ratification and Change Control

15.1 This policy is ratified by the Product Owner and reviewed by qualified legal counsel in the UK, Ireland and the EU before it is adopted as live. Legal review items are marked `[LEGAL REVIEW]` throughout.

15.2 The policy is reviewed annually, or on: a change to processing that materially affects retention/anonymization; activation of AI training; a change in law (GDPR, DPA 2018, Companies Act, SECR/CSRD, EU AI Act); or a change of hosting/provider.

15.3 Changes are versioned below; each version records owner and summary.

| Version | Date | Change summary | Owner |
|---|---|---|---|
| 0.1 | 2026-08-30 | Draft created; target operating standard; current-implementation gaps flagged in §12 | [OpenHands audit draft] |

---

## 16. Schedule A — Retention Schedule (template table)

*Durations are defaults for ratification; the authoritative values are the configured `system_settings` values. "→ Anonymize" means the record enters the §7 pipeline at the end of the period.*

| Ref | Data category | Class | Retained (identifiable) | Post-retention action | Statutory basis (where applicable) | Marker |
|---|---|---|---|---|---|---|
| A-1 | Account & authentication records (email, password hash, sessions, OAuth identity) | C1 | Until account deletion + quarantine window (≤ 30 days) | Irreversible destruction | UK GDPR / GDPR / Irish DPA 2018 (erasure) | §6 |
| A-2 | Organisation profile & corporate identifiers (name, company number, address, tenant keys) | C2 | Until account deletion + quarantine (≤ 30 days) | Irreversible destruction | Recital 26 objective; deletion policy | §6–§7 |
| A-3 | Uploaded documents | C1/C4 | Until account deletion + quarantine; else configured `document_retention_days` | Destruction (permanent delete) or anonymization of extracted content | Retention settings; DPA | §6, §8 |
| A-4 | Financial / tax / invoice records | C3 | **6 years** (min) from end of accounting period; up to **7 years** where required | Anonymization (default) or deletion | UK CA 2006 s.388; HMRC 6yr; Ireland CA 2014 s.283; TCA 1997 s.886 | §9 |
| A-5 | SECR / CSRD supporting records | C3/C4 | **6–7 years** from end of reporting period | Anonymization | SECR Regs 2022; CSRD (EU) 2022/2464 | §9 |
| A-6 | Operational emissions telemetry (extraction items, emissions logs, snapshots) | C4 | Until end of statutory retention band; else configured `data_retention_days` | **Anonymization (default)** | Recital 26; business value | §7 |
| A-7 | Anonymized aggregated datasets / AI training sets | C5 | **Indefinite** | None (retained) | Recital 26 — outside data-protection scope | §10 |
| A-8 | Audit logs, calculation snapshots (append-only), evidence | C6 | **Indefinite** (immutable); subject to §9.6 | None — never purged by retention | Auditability invariant | §9.6 |
| A-9 | Server / application logs | — | 30 days (proposed; configured `backup_retention_days` / log policy) | Deletion | Operational | §5 |
| A-10 | Messaging & notifications | C1 | Until account deletion; else per configured policy | Deletion / anonymization | Contract | §6 |
| A-11 | DR backups / snapshots | — | **30-day rolling rotation** | Natural lifecycle expiry | §8 | §8 |
| A-12 | Billing records (provider-neutral) | C3 | 6–7 years from end of accounting period | Anonymization | Tax statute | §9 |

---

## 17. Document control and distribution

17.1 This policy is distributed to the Board, the Data Protection function, Engineering, Operations, Product/Data Science and Legal counsel.

17.2 The approved version is published internally; external references (Privacy Policy draft §8, DPA draft §11, Terms of Service draft §17) are updated to link to it once ratified.
