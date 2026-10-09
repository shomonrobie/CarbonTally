CT-GAP-IMPLEMENTATION-MASTER-2026-09-30-001
Evaluation of CoStrict Reports & Consolidated Implementation Report

Document ID: CT-GAP-IMPLEMENTATION-MASTER-2026-09-30-001
Inputs: CT-GAP4, CT-GAP5, CT-GAP6 current-state research reports
Purpose: Evaluate report quality, reconcile findings, and define implementation path for missing features
Mode: Strategic / architectural — no code
Part 1: Evaluation of the CoStrict Reports
1.1 Report Quality Assessment
Dimension	Gap 4 (Supplier Portal)	Gap 5 (Conversational AI)	Gap 6 (Auditor Portal)
Overall stage classification	ABSENT (with reusable upstream)	SUBSTANTIALLY BUILT	ABSENT (with reusable upstream)
Evidence density	High — file paths, migration lines, route tables	Very high — line-level citations, chain traces	High — route/UI/migration tables
Honesty about unknowns	Strong — flags flagship-absent tables	Strong — flags BLOCKED_BY_SCHEMA and naming conflict	Strong — flags unapplied P7/S2 migrations
False-positive discipline	Good — separates SCHEMA_ONLY from BACKEND_ONLY	Excellent — separates Insight-as-is from Copilot-readiness	Good — flags orphan legacy routes
Repo-label reconciliation	Explicit — "Gap 4" is external, not in repo	Explicit — "Copilot" is a forbidden product name	Explicit — "Gap 6" is external
Confidence in findings	High	High	High
Weakness	Historical design docs (MIGRATION_004_SUPPLIER_MANAGEMENT.sql) not fully mined	Audit-target deviation (ai_content_history non-reuse) needs PO ruling	Historical PO position on auditor-as-non-user needs mining
1.2 Cross-Cutting Findings (Present in All Three)
#	Finding	Impact
1	"Gap N" is an external programme label, not a repo concept	Do not search repo for "Gap 4/5/6" — use feature IDs
2	Schema durability is the #1 risk. Multiple migrations are BLOCKED_BY_SCHEMA or unapplied in flagship	Every build must first confirm applied state in the authoritative DB
3	Reuse-first architecture is sound. Primitives exist for all three gaps	Build cost is lower than greenfield — but schema gaps remain
4	No live DB reads were performed	Applied state is UNKNOWN for all migrations cited
5	Historical PO decisions constrain design (auditor ≠ tenant user; Copilot name forbidden)	Design must respect ratified positions
6	Clone-only tables (evidence_line_items, provenance_line_links, insight tables, P17 columns) create a "works in dev, absent in prod" trap	Phase 0 must be schema reconciliation
1.3 Where the Reports Disagree or Leave Ambiguity
Issue	Gap 4	Gap 5	Gap 6	Resolution Needed
Audit target	n/a	Insight tables used, ai_content_history dormant	Audit trail exists, no auditor scope	PO ruling: keep insight tables or migrate to ai_content_history?
Identity model	Supplier identity undecided	n/a	Auditor identity undecided	PO ruling: login-less token vs authenticated principal?
Export format	n/a	n/a	audit-package.json exists but not auditor-named	PO ruling: extend or new format?
Product naming	n/a	"Copilot" forbidden	n/a	Confirm "Ask CarbonTally" / "CarbonTally Insight"
Part 2: Consolidated Implementation Report
2.0 Phase 0 — Pre-Build Schema Reconciliation (Mandatory)

Why: All three reports flag BLOCKED_BY_SCHEMA / unapplied migrations. Any build on top of absent tables will fail in production.
#	Action	Owner	Output
0.1	Read-only DB introspection on authoritative environment (information_schema.tables, columns, pg_policies)	Engineering / DBA	Applied-state matrix
0.2	Confirm applied state of Insight family (20261001000000 → 20261007000000)	Engineering	Insight tables present?
0.3	Confirm applied state of P8-B2 (20260916000000, 20260916010000)	Engineering	Evidence line items / provenance links present?
0.4	Confirm applied state of P7 audit immutability (20260912000000) and S2 is_current (20260921000000)	Engineering	Audit immutability enforced?
0.5	Confirm applied state of P17 dimension columns (20261010000000, 20261014000000)	Engineering	Supplier/facility dimensions present?
0.6	Produce "Applied-State Truth Table" doc	Engineering	Single source of truth for Phase 1+
0.7	PO ruling on audit target, identity model, product naming	PO	Decision register update

Gate: No build phase begins until Phase 0 is complete. This is a hard dependency for all three gaps.

Estimated effort: 1–2 weeks (mostly read-only + one PO review).
2.1 Gap 4 — Supplier Engagement Portal

Current state: ABSENT. Reusable: suppliers CRUD, messaging, notifications, documents, bulk upload, evidence, reporting.

Critical design decision (PO ruling required):

    Supplier identity model: login-less tokenised link vs authenticated supplier principal

    Data model: supplier submissions as customer_documents records vs new supplier_response object

    Factor capture: extend suppliers.emission_factor_* columns vs new supplier_factors table

Build Phases
Phase	Deliverable	Reuse	New Build	Effort
4.1 Supplier identity & invitation	Supplier invite table with token + expiry; login-less magic-link route; invitation email via Resend	user_invitations pattern (expires_at), password_reset_tokens pattern, Resend (services/email_service.py)	supplier_invitations table, supplier_access_tokens, POST /api/v3/supplier-portal/auth, unauthenticated route family	3–4 weeks
4.2 Data request questionnaire	Questionnaire definition model; issuance to supplier; response capture	document_types taxonomy (classify, not questionnaire), issue lifecycle pattern (FTR-131)	supplier_questionnaires, supplier_questionnaire_questions, supplier_questionnaire_responses, supplier_questionnaire_answers tables; admin UI for authoring; supplier UI for responding	5–6 weeks
4.3 Supplier activity-data upload	CSV/Excel template download; supplier upload endpoint; attribution to supplier	BulkUpload.jsx, upload_batches, import_batches, customer_documents	Supplier-scoped upload route, supplier attribution column, template generator	3–4 weeks
4.4 Supplier factor capture	Supplier-provided emission factors; approval path; provenance link	suppliers.emission_factor_* columns (exist), customer_factors (factor_source free-text)	supplier_factors table OR customer_factors.supplier_id FK + supplier_factor flag; approval workflow; factor selection policy extension (FTR-113)	3–4 weeks
4.5 Supplier progress dashboard	Per-supplier request state; completeness metric; reminder/nudging	/api/v3/reporting/* patterns, notifications	supplier_request_status view/table; completeness endpoint; dashboard UI; reminder job	4–5 weeks
4.6 Supplier → evidence linkage	Supplier-submitted data joins evidence trail	evidence_line_items, provenance_line_links, calculation_snapshots.source_line_item_id	Supplier-source object; join into evidence line items; provenance chain from supplier → snapshot	3–4 weeks
4.7 Supplier messaging/notification wiring	Supplier outreach via existing transport	conversations, conversation_participants, messages, notifications, notification_delivery	Supplier participant type; supplier recipient resolver; event keys	2–3 weeks
4.8 CBAM/CSRD supplier-data scaffolding	CBAM goods taxonomy; CSRD Scope-3 data collection form	Disclosure model foundation (FTR-226)	CBAM Annex I taxonomy, embedded emissions boundary templates, CSRD Scope-3 forms	4–6 weeks (parallelisable)

Gap 4 total: ~6–9 months for full scope; MVP (4.1 + 4.3 + 4.4 + 4.6) in ~3 months.

Highest-risk dependency: Supplier identity model PO ruling. Without it, 4.1 blocks everything.
2.2 Gap 5 — Conversational AI / Copilot

Current state: SUBSTANTIALLY BUILT (CarbonTally Insight I1–I6 exists, wired end-to-end).

Critical guardrails (from report):

    "Copilot" is a forbidden product name (D2 §3.5). Use "Ask CarbonTally" / "CarbonTally Insight".

    Audit trail uses carbontally_insight_interactions + audit_trail, not ai_content_history. PO ruling needed if this is acceptable.

    Citation enforcement is structured-output level, not machine-bound per-claim. PO ruling on required strength.

Build Phases
Phase	Deliverable	Reuse	New Build	Effort
5.1 Schema application	Apply/confirm Insight migrations in authoritative DB	All Insight code exists	Migration application only	1 week (ops)
5.2 Provider configuration	Configure LLM provider in each environment where conversational UX is expected	infra/llm_client.py, infra/ai_runtime.py, env vars	Ops config only	2–3 days
5.3 On-demand chart generation	Chart intent in planner; chart rendering in Insight UI; reuse aggregate tool output	insight_aggregation, insight_temporal_comparison (chart-ready structured data); /api/v3/reporting/* series; InsightComparison.jsx table pattern; recharts (already in dashboard)	Chart intent classifier; chart spec model; InsightChart.jsx; chart-ready response shape in interaction outcome	4–5 weeks
5.4 Machine-enforced citation binding	Every narration claim bound to a reference; refusal if claim has no reference	InsightReference typed locators (domain/insight_tool.py), narration prompt guardrails	Post-narration validation layer; claim→reference matcher; fallback to structured answer if binding fails	3–4 weeks
5.5 Generalised table rendering	Beyond temporal comparison — any aggregate as a table	InsightComparison.jsx table pattern	Generic table renderer keyed by tool output schema	2–3 weeks
5.6 Audit target reconciliation	Decision: keep insight tables + audit_trail, or add ai_content_history mirror	Both exist	If mirror required: writer for ai_content_history from interaction events	1–2 weeks (if required)
5.7 Product naming rollout	Rename public surfaces to "Ask CarbonTally" / "CarbonTally Insight"	Existing UI	Copy + nav rename; no code change	1 week

Gap 5 total: ~2–3 months (post Phase 0). The conversational spine exists; this is hardening, not greenfield.

Highest-risk dependency: Schema application (5.1) and provider configuration (5.2) must precede chart/citation work, or the features will not be testable end-to-end.
2.3 Gap 6 — Auditor Read-Only Portal

Current state: ABSENT. Reusable: role model, RoleRoute, evidence trail, secure document viewer, audit console, audit-package export.

Critical design decision (PO ruling required):

    Historical position: auditor is NOT a tenant user — "customer-authorized export/evidence workflows are preferred over direct auditor tenant access unless separately authorized."

    This means Gap 6 may be two different products depending on ruling:

        Model A (non-user grant): Time-bound, login-less evidence/export grant to an unauthenticated recipient

        Model B (authenticated principal): New auditor role/principal with read-only tenant access

The report strongly suggests Model A is the ratified direction. Confirm before building.
Build Phases
Phase	Deliverable	Reuse	New Build	Effort
6.0 PO ruling	Confirm Model A vs Model B	—	Decision register	1 week
6.1 Auditor access grant model	Time-bound grant with expiry + revocation + audit	report_shares pattern (expiry, revoked_at, access_count)	auditor_access_grants table; issue/revoke service; server-side expiry enforcement	3–4 weeks
6.2 Auditor-facing route family	Read-only routes for evidence, audit trail, exports	RoleRoute.jsx, insight_authz.py refusal-by-default pattern	Auditor scope in RoleRoute (if Model B) OR unauthenticated token-gated routes (if Model A)	2–3 weeks
6.3 Auditor-scoped evidence viewer	Evidence trail + source document viewer, auditor-scoped	EvidenceTrail.jsx, SourceEvidenceViewer.jsx, /api/v3/evidence/line-items/{id}	Auditor projection/filter; auditor accepted on endpoint (or token-gated)	2–3 weeks
6.4 Auditor no-edit document boundary	Server-enforced no-download for auditor scope	SecureDocumentViewer.jsx (allowDownload=false), signed-URL service (services/storage.py)	Auditor download policy; signed-URL policy per auditor grant	1–2 weeks
6.5 Auditor-scoped audit trail	Audit-readiness + audit-activity scoped to grant	ensure_org_audit_access pattern, /api/v3/reporting/audit-*	Auditor branch in ensure_org_audit_access OR token-gated variant	2–3 weeks
6.6 Auditor export format	Auditor-named format with engagement metadata	audit-package.json (data/reporting.py:1152)	auditor-package.json schema; engagement block; time-bound delivery	2–3 weeks
6.7 Auditor section in package	Engagement scope, access window, recipient identity	audit-package.json sections	New auditor section; PO decision on fields	1 week
6.8 Report version immutability (dependency)	Confirm report_versions.is_current rule applied	20260921000000_p8_s2_*	Apply migration	3 days (ops)
6.9 Audit immutability (dependency)	Confirm P7 audit immutability applied	20260912000000_p7_*	Apply migration	3 days (ops)
6.10 Gap 7 assurance integration (if required)	Assurance statement upload + linkage	Document upload (FTR-092), report versions (FTR-223)	assurance_statements table; linkage to report versions; status flag	3–4 weeks (if in scope)

Gap 6 total: ~3–4 months for Model A (non-user grant), ~4–5 months for Model B (authenticated principal).

Highest-risk dependency: PO ruling (6.0) on identity model. Model A and Model B diverge on every subsequent phase.
Part 3: Cross-Gap Sequencing & Dependencies
3.1 Dependency Graph
text

Phase 0 (Schema Reconciliation)
   ├── 0.7 PO rulings: audit target, identity models, product naming
   │
   ├── Gap 5 (Insight hardening)
   │     ├── 5.1 Apply Insight migrations ─── blocks all Gap 5 features
   │     ├── 5.2 Provider config ──────────── blocks chart/citation testing
   │     └── 5.3–5.7 Hardening
   │
   ├── Gap 6 (Auditor portal)
   │     ├── 6.0 PO ruling ───────────────── blocks 6.1+
   │     ├── 6.8/6.9 Apply P7/S2 ──────────── blocks auditor immutability guarantees
   │     └── 6.1–6.7 Build
   │
   └── Gap 4 (Supplier portal)
         ├── 4.1 Supplier identity ────────── blocks 4.2, 4.3, 4.5, 4.7
         ├── 0.3 P8-B2 applied ────────────── blocks 4.6 evidence linkage
         └── 4.2–4.8 Build

3.2 Recommended Sequence
Quarter	Gap 5 (Insight)	Gap 6 (Auditor)	Gap 4 (Supplier)
Q1	5.1 schema, 5.2 provider, 5.7 naming	6.0 PO ruling, 6.8/6.9 migrations	0.3 P8-B2 check, 4.1 identity
Q2	5.3 charts, 5.4 citations, 5.5 tables	6.1 grants, 6.2 routes, 6.3 evidence	4.2 questionnaire, 4.3 upload
Q3	5.6 audit target	6.4 no-edit, 6.5 audit trail, 6.6 export	4.4 factors, 4.5 dashboard
Q4	—	6.7 package section, 6.10 assurance	4.6 evidence linkage, 4.7 messaging, 4.8 CBAM/CSRD

Rationale for sequence:

    Gap 5 first — smallest build distance (hardening, not greenfield), highest visibility for investor demos, unblocks consultant sales narrative.

    Gap 6 second — medium build distance, required for CSRD assurance credibility.

    Gap 4 third — largest build, but CBAM/CSRD supplier data is a long-term moat; start identity early in parallel.

Part 4: Open Decisions Required from PO
#	Decision	Blocks	Report Reference
D1	Audit target: keep carbontally_insight_interactions + audit_trail, or add ai_content_history mirror?	Gap 5.6	Gap 5 §2.6
D2	Citation strength: is structured references[] sufficient, or is machine-bound per-claim citation required?	Gap 5.4	Gap 5 §2.3
D3	Chart dimensions: which aggregate results must be chartable?	Gap 5.3	Gap 5 §2.4
D4	Product naming: confirm "Ask CarbonTally" / "CarbonTally Insight" (not Copilot)	Gap 5.7	Gap 5 §1
D5	Auditor identity model: Model A (non-user grant) or Model B (authenticated principal)?	Gap 6 all	Gap 6 §1, §2.1
D6	Auditor export format: extend audit-package.json or new auditor-package.json?	Gap 6.6	Gap 6 §2.7
D7	Auditor package section: what fields (engagement id, scope period, access window, recipient identity)?	Gap 6.7	Gap 6 §2.8
D8	Supplier identity model: login-less token vs authenticated supplier principal?	Gap 4.1	Gap 4 §2.1
D9	Supplier data model: documents reuse vs new supplier_response object?	Gap 4.2, 4.3, 4.6	Gap 4 §2.2, §2.6
D10	Supplier factor capture: extend suppliers.emission_factor_* or new supplier_factors table?	Gap 4.4	Gap 4 §2.4
D11	Gap 7 scope: is assurance-statement integration a hard dependency for Gap 6?	Gap 6.10	Gap 6 §3, §10
D12	Authoritative DB: which environment is authoritative for applying blocked migrations?	Phase 0	All three §9
Part 5: Risk Register
Risk	Probability	Impact	Mitigation
Schema not applied in flagship	High	Critical — blocks all three gaps	Phase 0 mandatory gate
PO decisions delay Phase 0	Medium	High — blocks 4.1, 6.1	Escalate D1–D12 in single review session
Evidence tables absent in prod	High	High — blocks Gap 4.6, Gap 6.3	Confirm in Phase 0; apply if needed
Insight tables absent in prod	High	High — blocks Gap 5 entirely	Confirm in Phase 0; apply if needed
"Copilot" name used in marketing	Medium	Medium — violates ratified D2 §3.5	Audit public site and marketing copy
Auditor-as-user model built, then reversed	Medium	High — wasted build	Enforce 6.0 PO ruling gate before 6.1
Supplier identity model built, then reversed	Medium	High — wasted build	Enforce 4.1 PO ruling gate before 4.2
CBAM taxonomy built before CSRD clarity	Medium	Medium — rework	Sequence 4.8 after 4.1–4.4 proven
LLM provider not configured in demo env	Medium	Medium — narration degrades to structured	Confirm in 5.2; document env requirements
Part 6: Summary — What Needs to Be Done
Immediate (0–4 weeks)

    Phase 0 schema reconciliation — read-only DB introspection across all three gaps.

    PO decision session — resolve D1–D12 in one sitting.

    Apply blocking migrations — Insight family, P8-B2, P7, S2 — in authoritative DB.

Short-term (1–3 months)

    Gap 5 hardening — charts, citation binding, naming rollout. Lowest cost, highest visibility.

    Gap 6 foundation — auditor grant model, route family, evidence scope.

    Gap 4 identity — supplier invitation + tokenised access.

Medium-term (3–6 months)

    Gap 4 core — questionnaire, upload, factor capture.

    Gap 6 delivery — no-edit boundary, audit trail scope, export format.

    Gap 5 completion — audit target reconciliation, generalised table rendering.

Long-term (6–12 months)

    Gap 4 evidence linkage — supplier → evidence trail join.

    Gap 4 CBAM/CSRD scaffolding — regulatory extension.

    Gap 6 assurance integration — if Gap 7 is in scope.

Part 7: Bottom Line

The CoStrict reports are high-quality, evidence-dense, and honest. They correctly identify that:

    Gap 5 is not greenfield — Insight exists; the gap is charts, citation hardening, and schema application.

    Gap 4 and Gap 6 are absent — but both have mature reuse stacks, so the build is integration, not invention.

    Schema durability is the universal blocker — every gap depends on migrations that may not be applied in the authoritative environment.

    PO decisions gate the largest build risks — auditor identity and supplier identity models determine whether months of work are spent in the right direction.

The single most important action is Phase 0: confirm schema state and resolve the twelve PO decisions. Everything else is sequenced execution once those two gates are cleared.

The single largest strategic opportunity is Gap 5 — because the conversational spine already exists, hardening it into an evidence-cited, audit-defensible Copilot (renamed "Ask CarbonTally") is a 2–3 month effort that directly strengthens the consultant workspace moat and investor demo narrative. It should be first in the build sequence, not last.
