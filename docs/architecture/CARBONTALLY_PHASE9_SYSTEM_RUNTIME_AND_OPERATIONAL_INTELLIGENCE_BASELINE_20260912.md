# CarbonTally Phase 9

# System Runtime & Operational Intelligence

## Product, Technical & Governance Baseline

**Document status:** Working baseline / future-phase reference. **Not an implementation specification and not an implementation authorization.**
**Phase identifier used by this document:** 9 — System Runtime & Operational Intelligence
**Date:** 2026-09-12
**Discovery status:** NOT STARTED
**Implementation status:** NOT AUTHORIZED
**Production changes:** NONE
**Implementation authorization:** Requires future explicit PO gate
**PO ratification of the Phase 9 identifier and position:** **NOT YET OBTAINED** — the PO-ratified product-sequencing authority (`CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md`) does not name a Phase 9, and existing Phase 8 governance documents use "Phase 9" with a different meaning. See §62 (authority) and §63 (conflicts C-1, C-2, C-3).
**Document authority:** Subordinate to `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (architecture source of truth) and `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` (PO-ratified product sequencing). See §62.
**Supersession rule:** This document establishes the Phase 9 baseline. Any implementation must be preceded by formal discovery and PO ratification.

---

# 1. Purpose

Phase 9 establishes CarbonTally's **System Runtime & Operational Intelligence** capability.

The purpose is to give authorized CarbonTally administrators, operators, technical staff, and support personnel visibility into the operational health, reliability, processing activity, failures, resource usage, and runtime behaviour of the CarbonTally platform.

Phase 9 is concerned with:

> **How well CarbonTally itself is operating.**

It is not primarily concerned with customer-facing carbon accounting, carbon-management intelligence, or customer carbon reporting.

---

# 2. Why Phase 9 Exists

CarbonTally is a multi-layer SaaS platform involving:

* React frontend;
* FastAPI backend;
* Supabase PostgreSQL/Auth/Storage/Realtime;
* background processing;
* report generation;
* carbon calculations;
* emissions-factor data;
* evidence and auditability;
* email delivery;
* AI/LLM services;
* billing and usage controls;
* Vercel frontend deployment;
* Render backend deployment.

As the platform becomes production-grade, operational visibility becomes a distinct product/administrative capability.

Operational information must not be scattered indefinitely across:

* raw logs;
* database inspection;
* deployment dashboards;
* ad-hoc SQL;
* developer-only diagnostics;
* unrelated customer reports.

Phase 9 therefore provides a deliberate operational-intelligence layer.

---

# 3. Core Phase Boundary

Phase 9 answers:

> **Is CarbonTally operating correctly, reliably, securely, and efficiently?**

Phase 8 answers:

> **Can CarbonTally help customers understand, report, manage, and reduce their carbon emissions?**

Phase 7 answers:

> **Can CarbonTally provide traceable evidence and auditability supporting its carbon results and workflows?**

These responsibilities must remain distinct.

---

# 4. Phase 9 Does NOT Replace Earlier Phases

Phase 9 must not recreate functionality already belonging to earlier phases.

In particular:

### Phase 7

Remains responsible for:

* carbon evidence traceability;
* audit trail;
* evidence references;
* calculation provenance;
* factor provenance;
* workflow history;
* audit/evidence packages;
* assurance-support boundaries.

Phase 9 may report operational events relating to those systems, but must not redefine their evidence/audit semantics.

### Phase 8

Remains responsible for:

* Advanced Carbon Analytics;
* CarbonTally Insight;
* customer carbon reports;
* report lifecycle/versioning/approval;
* net-zero planning;
* data-quality intelligence;
* disclosure/reporting intelligence;
* internal benchmarking and management insights.

Phase 9 must not become a second customer carbon-reporting engine.

---

# 5. Primary Users

Initial Phase 9 users should be restricted to authorized internal operational roles.

Potential users include:

* platform administrators;
* system administrators;
* authorized CarbonTally operational staff;
* authorized technical/support personnel.

Customer users must not automatically receive access to system-wide operational intelligence.

Customer-facing operational information may be exposed only where explicitly designed and authorized.

Consultant, auditor, PE, and other external-role access must be explicitly decided rather than inferred.

---

# 6. Multi-Tenant Boundary

Phase 9 must distinguish between:

### System-level operational information

Examples:

* API health;
* background-worker health;
* deployment health;
* system-wide failures;
* infrastructure status;
* service availability.

This is privileged internal information.

### Tenant-scoped operational information

Examples:

* a customer's report-generation job;
* a customer's failed import;
* tenant-specific processing status;
* tenant-specific usage.

Tenant-scoped operational information must remain subject to normal organization/entity authorization.

### Rule

> System operational visibility must never become a cross-tenant data-leakage mechanism.

An administrator's operational access must be explicitly authorized and auditable.

---

# 7. Core Capability Areas

Phase 9 should eventually cover the following capability families.

## 7.1 Platform Health

Provide visibility into:

* API availability;
* backend health;
* frontend availability where measurable;
* database connectivity;
* Supabase connectivity;
* authentication service health;
* storage availability;
* realtime availability where relevant;
* external service availability;
* dependency health;
* service version/build information.

Health must distinguish between:

* healthy;
* degraded;
* unavailable;
* unknown.

Do not infer health from a single superficial endpoint.

---

# 8. API Runtime Intelligence

Operational visibility should include:

* request volume;
* response status distribution;
* latency;
* slow requests;
* error rates;
* endpoint-level failures;
* authentication failures;
* authorization failures;
* rate-limit events;
* dependency failures;
* timeout events.

Where feasible, provide time-windowed summaries.

Do not expose sensitive request data unnecessarily.

Request logs must not become an accidental PII store.

---

# 9. Background Jobs & Processing

Phase 9 must provide operational visibility into asynchronous processing.

Potential job classes include:

* report generation;
* calculation processing;
* factor imports;
* data imports;
* evidence processing;
* email processing;
* AI processing;
* scheduled maintenance;
* other future workers.

For each relevant job type, operational reporting should eventually support:

* queued;
* started;
* running;
* completed;
* failed;
* cancelled;
* retried;
* duration;
* failure reason;
* retry count;
* timestamps;
* originating tenant/entity where authorized;
* correlation/job identifier.

The system should make it possible to answer:

> What happened to this job?

without requiring direct database investigation.

---

# 10. Report Generation Operations

Phase 8 owns customer report semantics.

Phase 9 owns operational visibility into report generation.

Examples:

* number of reports generated;
* generation success/failure;
* queue backlog;
* generation duration;
* failed PDF creation;
* storage failures;
* generation retries;
* report-generation worker health.

Phase 9 must not modify the meaning of customer reports.

---

# 11. Carbon Calculation Operations

Phase 8/earlier carbon systems remain authoritative for calculations.

Phase 9 may provide operational information such as:

* calculation job counts;
* failed calculations;
* processing duration;
* calculation queue state;
* retries;
* abnormal processing rates;
* calculation service failures.

Phase 9 must never become an alternative calculation engine.

Operational reporting must not independently recalculate emissions merely to generate an operational dashboard.

---

# 12. Factor Import Operations

Factor datasets are critical CarbonTally infrastructure.

Phase 9 should eventually provide visibility into:

* import executions;
* import status;
* start/end times;
* dataset/version;
* records processed;
* records accepted/rejected;
* validation failures;
* mapping failures;
* import errors;
* retry status;
* importer health;
* deployment/import compatibility.

Operational reporting must reference the authoritative import records rather than duplicate them.

---

# 13. Data Processing & Data Quality Operations

Phase 9 may expose system-level processing information such as:

* failed ingestion;
* malformed input;
* processing exceptions;
* validation failures;
* rejected records;
* queue backlogs;
* processing latency.

This is different from Phase 8's customer-facing Carbon Data Quality Intelligence.

Phase 8 answers:

> Is this customer's carbon data trustworthy/complete enough for its intended use?

Phase 9 answers:

> Did the platform successfully process the data?

These must remain separate concepts.

---

# 14. Email / Notification Runtime

Operational reporting should eventually provide visibility into email and notification delivery.

Examples:

* queued messages;
* sent;
* delivered where provider data supports it;
* bounced;
* rejected;
* failed;
* provider/API failures;
* retry activity;
* delivery latency.

This may include Resend or future notification providers.

Do not expose message content unnecessarily.

Operational reporting should prefer metadata over full email contents.

---

# 15. Storage & File Operations

Operational visibility should eventually include:

* file generation failures;
* upload failures;
* download failures;
* storage availability;
* storage operation errors;
* orphaned/failed generated files where detectable;
* report-file processing failures.

Do not expose file contents merely because an operator can see file-operation metadata.

Normal authorization remains authoritative for accessing actual files.

---

# 16. AI / CarbonTally Insight Runtime

Phase 8 owns the CarbonTally Insight product and its analytical semantics.

Phase 9 should provide operational visibility into AI runtime behaviour.

Potential operational metrics:

* AI request volume;
* provider availability;
* provider failures;
* timeout rate;
* latency;
* token usage;
* estimated cost;
* allowance consumption;
* tool-call failures;
* deterministic fallback events;
* AI processing errors;
* rate-limit events.

Phase 9 must not:

* expose private Insight conversations broadly;
* bypass Insight authorization;
* treat AI logs as authoritative carbon data;
* allow operators to access customer conversations without explicit authorization.

Operational metadata and conversational content must remain separate.

---

# 17. Billing / Usage Runtime

Existing billing and usage infrastructure should eventually feed operational intelligence.

Potential metrics include:

* plan usage;
* allowance consumption;
* overage events;
* credit consumption;
* AI usage;
* report-generation usage;
* usage anomalies;
* failed billing operations;
* configuration changes.

Phase 9 must not replace the authoritative billing system.

Commercial policy remains configurable through the existing billing architecture.

---

# 18. Authentication & Authorization Operations

Operational intelligence should eventually identify:

* authentication failures;
* suspicious authentication patterns;
* authorization failures;
* expired sessions;
* token/service failures;
* permission-denied events;
* unusual access patterns where supported.

Security-sensitive operational events must be handled carefully.

Phase 9 must not weaken authentication or authorization to make operational reporting easier.

---

# 19. Security Operations

Phase 9 may eventually include operational security intelligence such as:

* repeated authorization failures;
* unusual error patterns;
* suspicious request rates;
* service-account failures;
* configuration/security events;
* security-relevant operational incidents.

This is operational intelligence, not a replacement for a dedicated security platform/SIEM.

Any security-monitoring expansion must be separately assessed.

---

# 20. Deployment & Release Runtime

Phase 9 should eventually provide operational visibility into deployment state.

Potential information:

* deployed version;
* build identifier;
* deployment timestamp;
* environment;
* service status;
* dependency version;
* startup failures;
* worker startup failures;
* configuration failures.

Relevant environments may include:

* local/development;
* staging;
* production.

Do not expose secrets or sensitive environment variables.

---

# 21. Worker & Recovery Intelligence

The platform must eventually make it possible to identify:

* worker unavailable;
* worker restarted;
* worker crash;
* queue backlog;
* repeated job failure;
* retry exhaustion;
* processing stall;
* dependency outage;
* recovery after outage.

Where appropriate, operational reports should show:

* incident start;
* incident end;
* duration;
* affected capability;
* recovery status.

---

# 22. Operational Incident Reporting

Phase 9 should eventually provide an operational incident model.

Potential incident states:

* detected;
* investigating;
* acknowledged;
* mitigating;
* resolved;
* closed.

Potential incident information:

* incident ID;
* affected service;
* severity;
* start time;
* detection source;
* impact;
* mitigation;
* resolution;
* related jobs/events;
* responsible operator;
* timestamps.

The exact incident workflow requires future discovery and PO ratification.

Do not implement an incident-management system during Phase 8.

---

# 23. Operational Dashboards

Phase 9 should eventually provide role-appropriate operational dashboards.

Potential dashboard areas:

### Executive / Platform Overview

* overall service health;
* major incidents;
* availability;
* processing health;
* high-level usage.

### Operations

* queues;
* jobs;
* failures;
* retries;
* processing latency;
* dependencies.

### Technical

* API performance;
* worker performance;
* deployments;
* errors;
* infrastructure dependencies.

### AI Operations

* provider status;
* AI requests;
* failures;
* usage;
* cost;
* fallback activity.

Exact dashboard design requires discovery.

---

# 24. Operational Reports

The eventual system should support structured operational reports rather than dashboards only.

Possible report categories:

* daily runtime summary;
* weekly operational summary;
* service health report;
* job processing report;
* failed-job report;
* incident report;
* deployment/release report;
* AI runtime report;
* usage/allowance operational report;
* data-import processing report.

These are examples, not yet an authoritative final report catalogue.

The final catalogue must be defined during Phase 9 discovery.

---

# 25. Alerts & Thresholds

Phase 9 should eventually support operational alerts for meaningful conditions.

Examples:

* service unavailable;
* error rate above threshold;
* queue backlog above threshold;
* repeated job failures;
* provider outage;
* storage failure;
* email delivery failure;
* unusual processing delay;
* allowance exhaustion;
* critical import failure.

Alert thresholds must be configurable where appropriate.

Avoid alert noise.

Do not create high-frequency monitoring that can encourage unnecessary operational activity.

---

# 26. Auditability

Operational actions must themselves be auditable where appropriate.

Examples:

* viewing sensitive operational information;
* changing operational configuration;
* changing thresholds;
* acknowledging incidents;
* resolving incidents;
* retrying jobs;
* cancelling jobs;
* changing operational settings.

Phase 9 must reuse CarbonTally's established audit architecture where appropriate.

Do not create a competing audit-trail system without explicit architectural justification.

---

# 27. Correlation & Traceability

Operational events should support correlation across relevant system components.

Where practical, use identifiers such as:

* request ID;
* correlation ID;
* job ID;
* report ID;
* calculation ID;
* import ID;
* deployment/build ID;
* incident ID.

The goal is to answer:

> What happened, where did it happen, and what other system events were related?

without duplicating authoritative domain records.

---

# 28. Observability Data Model

Phase 9 discovery must determine which information belongs in:

* application logs;
* structured operational events;
* metrics;
* job records;
* audit trail;
* incident records;
* existing domain tables;
* external monitoring systems.

Do not automatically create a giant generic `system_events` table.

The correct architecture must be determined from existing CarbonTally infrastructure and operational requirements.

---

# 29. Retention

Operational data has different retention requirements from carbon/accounting evidence.

Phase 9 discovery must explicitly determine retention periods for:

* logs;
* metrics;
* operational events;
* job records;
* incidents;
* alerts;
* AI runtime metadata;
* deployment information.

Do not assume that all operational data should be retained indefinitely.

Retention must consider:

* operational usefulness;
* cost;
* privacy;
* security;
* regulatory/legal requirements;
* incident investigation needs.

---

# 30. Privacy

Operational intelligence must follow data minimization principles.

Avoid storing or exposing:

* passwords;
* access tokens;
* API keys;
* secrets;
* unnecessary message bodies;
* unnecessary customer personal data;
* unnecessary full request payloads;
* unnecessary AI conversation content.

Logs and operational records must be designed as data products rather than unrestricted debugging dumps.

---

# 31. AI Privacy Boundary

CarbonTally Insight persistence and AI interaction data remain governed by Phase 8 decisions.

Phase 9 must not create a backdoor into:

* customer Insight conversations;
* human-to-human conversations;
* customer documents;
* evidence;
* private tenant information.

Operational staff access to sensitive AI/customer data must be separately authorized and auditable.

---

# 32. Disaster Recovery & Reliability

Phase 9 should eventually provide operational visibility supporting:

* backup status;
* backup failures;
* restore testing;
* recovery events;
* service recovery;
* RTO/RPO measurement where implemented.

The actual backup/restore architecture remains a separate technical-operational concern and must be discovered before implementation.

Phase 9 must not claim that backup/recovery capabilities exist merely because a dashboard reports them.

---

# 33. Availability & SLO/SLA Intelligence

Future discovery should determine appropriate operational objectives for:

* API availability;
* report-generation availability;
* calculation processing;
* imports;
* AI provider availability;
* email delivery;
* background workers.

Potential measurements include:

* uptime;
* error budget;
* latency objectives;
* processing completion objectives.

No SLO/SLA values are ratified by this baseline.

---

# 34. Operational Data vs Authoritative Carbon Data

This boundary is mandatory.

Operational reporting must never become authoritative for:

* emissions;
* emission factors;
* calculations;
* evidence;
* report facts;
* carbon accounting results.

Operational reports may reference these records, but the authoritative domain remains the existing CarbonTally carbon/accounting system.

---

# 35. Operational Data vs Audit Data

The audit trail answers:

> What governed/system actions need to be traceable?

Operational observability answers:

> What happened in the runtime environment?

These may reference one another, but they are not automatically the same dataset.

No duplication should be introduced without justification.

---

# 36. Operational Data vs Customer Reporting

Customer carbon reports must remain independent from internal operational dashboards.

A failed report-generation job may appear in an internal operational report.

It does not automatically belong in the customer's carbon report.

Likewise, a customer's carbon emissions do not automatically belong in a system-runtime report.

---

# 37. Administrator Controls

Future discovery should identify operational actions that may be safely exposed to administrators.

Potential actions:

* retry failed job;
* cancel queued job;
* acknowledge incident;
* resolve incident;
* inspect processing details;
* re-run approved import;
* inspect deployment status.

Any action that changes production state must have:

* explicit authorization;
* audit trail;
* clear confirmation;
* safe idempotency where applicable;
* appropriate failure handling.

Read-only operational visibility should be implemented before dangerous operational controls.

---

# 38. Read-Only First Principle

Phase 9 should follow:

> **Observe first. Act later.**

Initial operational intelligence should prioritize read-only reporting.

Destructive or state-changing operations such as:

* delete;
* purge;
* cancel;
* replay;
* retry;
* reprocess;
* restore;

must require explicit design and authorization.

---

# 39. External Monitoring Integration

Phase 9 may integrate with external operational platforms where beneficial.

Possible categories include:

* application monitoring;
* error tracking;
* uptime monitoring;
* infrastructure monitoring;
* log aggregation;
* alerting.

No specific vendor is mandated by this baseline.

The architecture should avoid unnecessary vendor lock-in.

---

# 40. Existing Infrastructure Reuse

Before implementation, Phase 9 discovery must inspect existing:

* health endpoints;
* logging;
* exception handling;
* background jobs;
* report-generation queue;
* usage tracking;
* billing infrastructure;
* audit trail;
* deployment configuration;
* Render configuration;
* Vercel configuration;
* Supabase infrastructure;
* email provider integration;
* AI runtime;
* import pipelines.

Do not build a second operational framework where an existing authoritative mechanism can be reused.

---

# 41. Existing Technical Operations Documentation

Phase 9 must incorporate the operational gaps already identified during CarbonTally technical-operations assessment.

These include areas such as:

* Render deployment reproducibility;
* backup/restore;
* worker recovery;
* calculation runbooks;
* factor-import runbooks;
* Resend operations;
* Vercel/Supabase reachability;
* broader operational runbooks.

The exact implementation status of each item must be re-verified during Phase 9 discovery rather than assumed from historical documentation.

Operations documentation that now exists in the repository (produced by the technical-operations workstream, **not** by this baseline, and **not** Phase 9 implementation):

* `docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md` — verified-evidence first-stop operations reference: service inventory, backend startup/build paths, health checks, environment variables, logging, background worker, database/migration safety, subsystem triage pointers. Explicitly **not** the full manual, and it contains no remediation scripts.
* `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` — Render configuration record. Its headline access result is **UNVERIFIED — NO SAFE ACCESS**: no Render credential/CLI existed in the assessment environment, so the live Render service configuration could not be independently inspected. "The absence of configuration evidence is **not** evidence of misconfiguration."

Phase 9 discovery must treat these as the current state of operations documentation, re-verify each claim against runtime evidence, and must not restate them as Phase 9 deliverables. The parent assessment `docs/architecture/CARBONTALLY_TECHNICAL_OPERATIONS_DOCUMENTATION_ASSESSMENT_20260912.md` remains authoritative for its own findings and is **not rewritten** by this baseline (see §63, conflict C-4).

---

# 42. Metrics & KPIs

Potential operational KPIs include:

### Reliability

* availability;
* incident count;
* incident duration;
* failure rate;
* recovery time.

### Processing

* jobs processed;
* success rate;
* failure rate;
* queue depth;
* processing latency.

### API

* request volume;
* error rate;
* latency;
* timeout rate.

### Data imports

* import success rate;
* records processed;
* rejection rate;
* duration.

### Reports

* generation volume;
* generation success rate;
* generation duration;
* PDF failure rate.

### AI

* request volume;
* provider availability;
* latency;
* failure rate;
* token usage;
* cost;
* fallback rate.

These are candidate metrics only until Phase 9 discovery ratifies the operational KPI catalogue.

---

# 43. Operational Anomaly Detection

Future Phase 9 discovery may evaluate anomaly detection for:

* unusual error spikes;
* processing delays;
* job-failure clusters;
* unusual usage;
* provider degradation;
* import anomalies.

Anomaly detection must be evidence-based.

Do not create arbitrary "health scores" without defined methodology.

---

# 44. No Arbitrary Operational Health Score

If CarbonTally eventually introduces a composite operational health score, it must have:

* explicit components;
* documented methodology;
* deterministic calculation;
* thresholds;
* explainability;
* auditability.

Do not introduce an opaque AI-generated operational score.

---

# 45. System Runtime Report Catalogue

**CANDIDATE — NOT YET PO-RATIFIED**

The final Phase 9 report catalogue must be established during discovery.

The baseline candidate categories are:

1. System Health Report
2. API Runtime Report
3. Background Job Report
4. Processing Failure Report
5. Report Generation Operations Report
6. Carbon Calculation Operations Report
7. Factor Import Operations Report
8. Data Processing Operations Report
9. Email/Notification Operations Report
10. Storage Operations Report
11. AI Runtime Report
12. Usage/Allowance Operations Report
13. Authentication/Authorization Operations Report
14. Deployment/Release Report
15. Incident Report
16. Reliability/Availability Report
17. Backup/Recovery Report
18. Operational Summary Report

**CANDIDATE — NOT YET PO-RATIFIED.** This list is not yet ratified as the final product catalogue.

Phase 9 discovery must consolidate, remove duplication, and determine which should be reports, dashboards, alerts, or external observability integrations. The final catalogue must be consolidated during Phase 9 discovery and ratified as a PO decision before implementation.

---

# 46. Non-Goals

Unless separately authorized, Phase 9 does not include:

* replacing the carbon calculation engine;
* replacing factor management;
* replacing customer reporting;
* replacing the Phase 7 audit system;
* replacing CarbonTally Insight;
* creating generic ESG reporting;
* creating unrestricted SIEM functionality;
* creating a generic enterprise monitoring platform;
* exposing private customer conversations;
* cross-tenant customer analytics;
* arbitrary AI access to system databases;
* unrestricted log access;
* automatic production remediation.

---

# 47. Governance Requirements

Phase 9 must follow the same governance discipline established for CarbonTally.

Required sequence:

**Phase 9 Baseline**

↓

**Phase 9 Discovery**

↓

**Capability Gap Analysis**

↓

**Architecture / Data Model Proposal**

↓

**PO Decision / Ratification**

↓

**Implementation Authorization**

↓

**Bounded Implementation Stages**

↓

**Independent Verification**

↓

**Phase Closure**

No implementation should be inferred merely from this baseline.

---

# 48. Required Discovery Questions

Before Phase 9 implementation, discovery must answer:

1. What operational infrastructure already exists?
2. Which runtime events are already persisted?
3. Which information exists only in logs?
4. Which metrics are externally available?
5. Which operational information requires new persistence?
6. What should remain in external observability platforms?
7. What belongs in CarbonTally's database?
8. What belongs in the existing audit trail?
9. What requires a new operational event model?
10. What requires an incident model?
11. What operational information is system-wide?
12. What is tenant-scoped?
13. Which roles can access each category?
14. Which actions are read-only?
15. Which actions may mutate runtime state?
16. What retention is required?
17. What privacy controls are required?
18. What operational reports are actually needed?
19. Which should instead be dashboards?
20. Which should instead be alerts?
21. What operational KPIs matter?
22. What external monitoring integrations are justified?
23. What backup/restore capability exists?
24. What recovery procedures exist?
25. What gaps remain in operational documentation?
26. What production monitoring is currently available?
27. What can be verified safely without production mutation?
28. What data must never appear in operational logs?
29. How will operational data be audited?
30. How will operational reporting avoid becoming a second source of truth?

---

# 49. Security Requirements

Security must remain a first-class boundary.

Phase 9 must enforce:

* role-based authorization;
* organization/entity scope where applicable;
* least privilege;
* sensitive-data minimization;
* auditability of privileged actions;
* no secret exposure;
* no unrestricted database access;
* no bypass of RLS/application authorization;
* no cross-tenant leakage;
* no AI bypass of authorization.

Operational visibility must never become an authorization bypass.

---

# 50. Testing Requirements

Future implementation must include, as appropriate:

### Unit tests

* metric calculations;
* status classification;
* threshold evaluation;
* report aggregation.

### Integration tests

* job/event ingestion;
* operational data retrieval;
* authorization;
* tenant isolation;
* incident lifecycle.

### Security tests

* unauthorized operational access;
* cross-tenant access;
* privileged-role boundaries;
* sensitive-data redaction.

### Reliability tests

* worker failure;
* retry;
* timeout;
* dependency outage;
* recovery.

### Regression tests

Existing CarbonTally behaviour must remain unaffected.

---

# 51. Production Verification

Phase 9 must distinguish:

* code-level verification;
* local verification;
* staging verification;
* production verification.

Do not claim production observability merely because code exists.

Production-specific claims require actual production evidence.

---

# 52. Documentation Requirements

Phase 9 implementation must eventually produce operational documentation covering, as applicable:

* architecture;
* operational data model;
* report catalogue;
* dashboards;
* alerts;
* role/access model;
* incident procedures;
* job recovery;
* deployment verification;
* backup/restore;
* troubleshooting;
* monitoring;
* retention;
* privacy;
* operational runbooks.

Documentation must be maintained as part of phase closure rather than reconstructed after implementation.

---

# 53. Relationship to Phase 8

Phase 8 should not be delayed waiting for the full Phase 9 implementation.

Phase 8 remains focused on the customer-facing product capabilities.

Phase 9 may consume operational information generated by Phase 8 systems, but this should not require Phase 8 to implement the entire operational intelligence layer.

Where Phase 8 creates operationally important events, those events should be designed so Phase 9 can observe them later without redesigning the underlying domain.

---

# 54. Relationship to Phase 7

Phase 7 remains closed.

Phase 9 may consume or reference Phase 7 operational information.

Phase 9 must not reopen Phase 7 merely to build operational reporting.

If implementation discovers a genuine Phase 7 defect, it must be:

1. documented;
2. evidenced;
3. separately assessed;
4. explicitly authorized before changing Phase 7.

---

# 55. Phase 9 Success Criteria

Phase 9 should ultimately allow an authorized operator to answer questions such as:

* Is CarbonTally healthy?
* Which service is degraded?
* What failed?
* When did it fail?
* What jobs are stuck?
* Which jobs are repeatedly failing?
* Are report-generation workers healthy?
* Are calculation jobs processing normally?
* Did a factor import succeed?
* Are email services working?
* Is storage working?
* Is CarbonTally Insight's provider available?
* How much AI usage is occurring?
* Are usage allowances being consumed unexpectedly?
* What deployment is running?
* Did the latest deployment introduce failures?
* Are there active incidents?
* When did an incident start?
* Has it recovered?
* What operational action was taken?
* Can the relevant event be traced?
* Can the operator investigate without directly querying production tables?
* Can all of this be done without exposing unauthorized tenant/customer data?

---

# 56. Phase 9 Design Principles

The following principles are normative:

1. **Observe before acting.**
2. **Reuse existing infrastructure before creating new infrastructure.**
3. **One source of truth per domain.**
4. **Operational intelligence must not become a second carbon engine.**
5. **Operational intelligence must not become a second audit system.**
6. **Tenant isolation is mandatory.**
7. **System-level operational access is privileged.**
8. **Sensitive data must be minimized.**
9. **AI must not bypass authorization.**
10. **Deterministic metrics must be preferred over opaque scores.**
11. **Read-only capabilities should precede state-changing controls.**
12. **Every operational mutation must be auditable.**
13. **Production claims require production evidence.**
14. **External observability systems should be reused where appropriate.**
15. **Phase boundaries must not be silently crossed.**
16. **No implementation is authorized by this baseline alone.**

---

# 57. Forgotten-Requirement Protection

This section exists specifically to prevent Phase 9 from being forgotten during later CarbonTally development.

Before Phase 9 is considered complete, the PO must explicitly confirm that discovery and implementation addressed, where applicable:

* [ ] platform health
* [ ] API runtime
* [ ] background jobs
* [ ] queue health
* [ ] report-generation operations
* [ ] carbon-calculation operations
* [ ] factor-import operations
* [ ] data-processing operations
* [ ] email/notification operations
* [ ] storage/file operations
* [ ] CarbonTally Insight runtime
* [ ] AI provider health
* [ ] AI usage/cost
* [ ] billing/allowance operations
* [ ] authentication operations
* [ ] authorization failures
* [ ] security-relevant runtime events
* [ ] deployments/releases
* [ ] worker recovery
* [ ] operational incidents
* [ ] alerts/thresholds
* [ ] availability/reliability
* [ ] backup/restore visibility
* [ ] operational dashboards
* [ ] operational reports
* [ ] operational KPI catalogue
* [ ] operational data retention
* [ ] privacy/data minimization
* [ ] privileged-access controls
* [ ] auditability
* [ ] correlation/traceability
* [ ] operational runbooks
* [ ] production verification
* [ ] disaster/recovery procedures
* [ ] external observability integration assessment

The checklist is a **governance memory aid**, not a statement that every item must necessarily become a CarbonTally-native feature.

Each item must eventually be marked:

* Implemented;
* Existing/reused;
* External system;
* Deferred;
* Not applicable;

with rationale.

---

# 58. Explicit Deferred Items

The following are intentionally deferred until Phase 9 discovery:

* final runtime-report catalogue;
* exact operational database schema;
* exact dashboard design;
* exact alerting architecture;
* exact incident workflow;
* exact operational roles;
* exact retention periods;
* exact SLO/SLA targets;
* exact external monitoring vendors;
* exact backup/restore architecture;
* exact anomaly detection methodology;
* exact operational health-score methodology;
* production monitoring architecture;
* operational notification channels.

No assumptions should be silently converted into implementation requirements.

---

# 59. Implementation Gate

This document does NOT authorize implementation.

The future implementation gate must explicitly state:

> **PHASE 9 IMPLEMENTATION AUTHORIZED**

and identify:

* approved scope;
* approved architecture;
* approved data model;
* approved roles;
* approved security model;
* approved report/dashboard catalogue;
* approved implementation stage;
* explicit exclusions;
* verification requirements.

Until that gate exists, Phase 9 remains a baseline/reference phase.

---

# 60. Final Phase Boundary

The enduring Phase 9 definition is:

> **Phase 9 — System Runtime & Operational Intelligence provides authorized operational visibility into the health, reliability, processing, failures, usage, deployment, recovery, and runtime behaviour of CarbonTally without becoming a replacement for the carbon domain, customer reporting, audit/evidence architecture, or CarbonTally Insight.**

---

# 61. Status

**PHASE 9 BASELINE ESTABLISHED**

**Discovery:** NOT STARTED

**Implementation:** NOT AUTHORIZED

**Production changes:** NONE

**Database changes:** NONE

**RLS changes:** NONE

**API changes:** NONE

**Frontend changes:** NONE

**AI changes:** NONE

**Deployment changes:** NONE

This document is a future-reference governance baseline only.

---

# 62. Document Authority, Sources Inspected & Ratification Status

## 62.1 Authority hierarchy for this document

This baseline is **subordinate** to the documents below and overrides none of them.

| Rank | Document | Authority |
|---|---|---|
| 1 | `docs/architecture/CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` | **Architecture source of truth.** Not replaced, extended or overridden by this baseline. |
| 2 | `docs/architecture/CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | **PO-ratified product sequencing** (ratified 10 Sep 2026). Ratification decision 5: "this roadmap governs product sequencing". Decision 6: only the Phase numbering defined by this Roadmap "represents the official product implementation roadmap"; other Phase-N numbering in historical/technical/audit/migration/security/UX documents "must not be interpreted as CarbonTally product phases". |
| 3 | `docs/architecture/CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md` | Phase 7 CLOSED — independently verified with accepted residuals. |
| 4 | Phase 8 governance set (discovery, report catalogue ratification, reporting lifecycle spec, product & report ratification, open-decision closure & implementation authorisation, Insight D2 ratification, Ask CarbonTally persistence discovery) | Governs Phase 8 only. Not modified by this baseline. |
| 5 | `docs/architecture/CARBONTALLY_TECHNICAL_OPERATIONS_DOCUMENTATION_ASSESSMENT_20260912.md` and `docs/operations/*` | Current operations-documentation state. Consulted as evidence, not rewritten. |
| 6 | Phase-specific specifications, implementation reports, independent verification reports | Govern their own gates. |

This baseline:

* creates no architecture, data model, role, permission, API or UI;
* authorizes no discovery, no implementation and no production change;
* does not resolve its own conflicts — see §63.

## 62.2 Sources inspected

Method: documentation review only. No application code, schema, migration, RLS, API, frontend, AI, billing or deployment file was analysed for behavioural claims. No capability is asserted as existing unless a named document establishes it. Where a claim could not be grounded in a document, it appears instead as a discovery question (§48) or a deferred item (§58).

| Document | What it establishes | How inspected |
|---|---|---|
| `CARBONTALLY_FINAL_ARCHITECTURE_BLUEPRINT_V1.3.md` (1,510 lines) | Architecture source of truth | Content searched: **zero** occurrences of "monitor", "observability", "health", "runtime" and **no** "Phase 9". The architecture source of truth does **not** currently define an operational-intelligence capability — a documented gap, not an omission of this baseline. |
| `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` | PO-ratified sequencing; ratified phase names; legacy-numbering rule | Content inspected (ratification record, §10, §11, §12, §13) |
| `CARBONTALLY_PHASE7_CLOSURE_AND_RELEASE_BOUNDARY_20260912.md` | Phase 7 = auditability + audit trail + evidence traceability + assurance-support; CLOSED | Content inspected |
| `CARBONTALLY_TECHNICAL_OPERATIONS_DOCUMENTATION_ASSESSMENT_20260912.md` | Module-by-module DOCUMENTED / PARTIALLY DOCUMENTED / NOT DOCUMENTED classification; health endpoints; worker; storage; Render risk | Content inspected |
| `docs/operations/CARBONTALLY_TECHNICAL_OPERATIONS_QUICK_REFERENCE_V1.0.md` | Current verified operations reference (service inventory, startup paths, health checks, worker, migration safety) | Content inspected |
| `docs/operations/CARBONTALLY_RENDER_DEPLOYMENT_CONFIGURATION_20260912.md` | Render configuration record; access result **UNVERIFIED — NO SAFE ACCESS** | Content inspected |
| `CARBONTALLY_PHASE8_DISCOVERY_AND_CAPABILITY_GAP_ANALYSIS_20260912.md` | Existing analytics substrate and LLM provider abstraction are reusable; uses "approved Phase 9 scope" for benchmarking | Relevant sections inspected |
| `CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` | Phase 8 non-scope includes "Phase 9+ capabilities (net-zero planning, disclosure frameworks, PCF/LCA)" | Relevant section inspected |
| `CARBONTALLY_PHASE8_OPEN_DECISION_CLOSURE_AND_IMPLEMENTATION_AUTHORISATION_20260912.md` | Decision package; documentation only; authorizes nothing (HEAD `10d43f6…`) | Header and purpose inspected |
| `CARBONTALLY_PHASE8_REPORTING_LIFECYCLE_SPEC_20260912.md`, `CARBONTALLY_PHASE8_CARBONTALLY_INSIGHT_D2_PO_RATIFICATION_20260912.md`, `CARBONTALLY_PHASE8_ASK_CARBONTALLY_PERSISTENT_CONVERSATION_AND_AI_AUDITABILITY_DISCOVERY_20260912.md` | Phase 8 report lifecycle; Insight terminology/ratification; AI auditability | Located and indexed |
| `CARBONTALLY_EVIDENCE_TRACEABILITY_AND_PROVENANCE_PRINCIPLES.md`, `CARBONTALLY_PHASE1-6_CLOSURE_AND_PHASE7_CONTINUITY_20260911.md`, `CARBONTALLY_PHASE6_CLOSURE_AND_RELEASE_BOUNDARY_20260911.md` | Evidence/provenance principles; closure lineage | Located and indexed |
| Production documents: `…DEPLOYMENT_READINESS…`, `…BACKUP_ARCHITECTURE…`, `…BACKUP_RESTORE_ROADMAP_V1.0…`, `…RELEASE_MANIFEST…`, `…PRECOMMIT_GATE…`, `…LOGIN_RUNBOOK…`, `…MIGRATION_SAFETY_PLAN…`, `…SUPABASE_RECONCILIATION…` (all 20260911) | Production readiness, backup and migration state | Located and indexed |
| Legacy "Phase 9" lineage: `CarbonTally-Phase9-Implementation-Contract-v1.0.md`, `…Phase9A-ValidationEngine…`, `…Phase9B-BenchmarkingEngine…`, `…Phase9C-ReportGenerationEngine…`, `…Phase9D-Integration-Verification…`, `…Phase10-API-Admin…` | A prior, unrelated meaning of the "Phase 9" identifier (see C-3) | Headers and scope inspected |
| `docs/cline/prompt-history/` (84 records, incl. `CT-P7-*`, `CT-P8-*`, `CT-P7P8-*`, `CT-OPS-*`, `CT-PROD-*`) | Governance trail | Directory indexed |

## 62.3 Ratification status

| Item | Status |
|---|---|
| Phase 9 identifier and position in the product sequence | **NOT PO-RATIFIED** (conflicts C-1, C-2) |
| Phase 9 scope (System Runtime & Operational Intelligence) | **NOT PO-RATIFIED** |
| Phase 9 discovery | NOT STARTED |
| Phase 9 implementation | NOT AUTHORIZED |
| Production changes | NONE |

---

# 63. Reconciliation with Existing Documentation — Conflicts & Unresolved Items

Rule applied: **no Phase 7 or Phase 8 document was modified.** Existing authoritative documents are preserved verbatim. Everything below is a future question, not a defect finding, and nothing below authorizes a change to another phase's documents.

## C-1 — Phase 9 is not named or ratified by the PO-ratified sequencing authority (MATERIAL — PO clarification required)

**Evidence.** `CARBONTALLY_MASTER_PROJECT_ROADMAP_V1.0.md` records the PO ratification of 10 Sep 2026: decision 2 names **Phase 7 — Auditor / Assurance**; decision 3 names **Phase 8 — Advanced Analytics**; both with "Detailed scope **NOT** defined" and nothing authorized. §12 closes the confirmed product sequence at Phase 8. The roadmap contains **no** "Phase 9" and no "Operational Intelligence"/"System Runtime" phase.

**Consequence.** The Phase 9 identifier and the capability scope in this document are a **working project designation**, not a ratified product phase. Discovery and implementation must not proceed on the assumption that Phase 9 exists in the official sequence.

**Action required.** PO to ratify (a) the existence and position of a Phase 9, and (b) its name and scope; **or** to re-designate this baseline's content under another approved identifier. This baseline is written so that re-designation requires no content change beyond the identifier and the conflicts in C-1/C-2.

## C-2 — Existing Phase 8 documents use "Phase 9" with a different, customer-facing meaning (MATERIAL — PO clarification required)

**Evidence.**
* `CARBONTALLY_PHASE8_PRODUCT_AND_REPORT_RATIFICATION_20260912.md` §2.2 (explicit non-scope): "No scope change to **Phase 9+ capabilities** (net-zero planning, disclosure frameworks, PCF/LCA, etc.)."
* `CARBONTALLY_PHASE8_DISCOVERY_AND_CAPABILITY_GAP_ANALYSIS_20260912.md` §14.1, quoting engine code: benchmarking is "internal / self-referential (**approved Phase 9 scope**)".

In both, "Phase 9" / "Phase 9+" denotes a **customer-facing advanced carbon capability beyond Phase 8** — net-zero, disclosure frameworks, PCF/LCA, benchmarking — which is the opposite product surface from this baseline's operational-intelligence definition.

**Consequence.** The identifier "Phase 9" is currently **overloaded** within recent Phase 8 governance. A future reader who searches for "Phase 9" will find mutually contradictory meanings, and §5 of this baseline defines a scope that those Phase 8 statements do not contemplate.

**Action required.** PO adjudication of which meaning owns the identifier. If the operational-intelligence capability takes the Phase 9 identifier, the Phase 8 usages must be re-read as "post-Phase-8 carbon capability" — but that clarification must come from the PO. The Phase 8 documents are **not** edited here.

## C-3 — A legacy "Phase 9" programme already exists in the repository (MATERIAL — traceability hazard)

**Evidence.** Tracked documents using "Phase 9" for an unrelated programme: `docs/cline/CarbonTally-Phase9-Implementation-Contract-v1.0.md` (scope: "9.1 ValidationEngine · 9.2 BenchmarkingEngine · 9.3 ReportGenerationEngine · 9.4 Integration tests"), `CarbonTally-Phase9A-ValidationEngine-v1.0.md` ("PHASE 9A COMPLETE — READY FOR PHASE 9B"), `Phase9B-BenchmarkingEngine`, `Phase9C-ReportGenerationEngine`, `Phase9D-Integration-Verification`, `CarbonTally-Phase10-API-Admin-v1.0.md`. These belong to the V2.1 backend build lineage.

**Consequence.** No architectural conflict, but a real traceability hazard: under Roadmap V1.0 decision 6 such numbering is not a product phase, yet it remains discoverable by name. Phase 9 discovery must index the legacy lineage explicitly so operational-intelligence work is never conflated with the ValidationEngine / BenchmarkingEngine / ReportGenerationEngine programme, and so legacy documents are not mistaken for prior art for this baseline. Legacy documents are **not deleted or rewritten**.

**Action required.** None before discovery; carried into discovery as a search/traceability control.

## C-4 — `docs/operations/` now exists; the technical-operations assessment records it as absent (INFORMATIONAL — temporal, no conflict)

**Evidence.** `CARBONTALLY_TECHNICAL_OPERATIONS_DOCUMENTATION_ASSESSMENT_20260912.md` §2 states: "**`docs/operations` does not exist**". The repository now contains two tracked documents there — the Quick Reference V1.0 and the Render configuration record, both under prompt `CT-OPS-QUICKREF-20260912-007`.

**Interpretation.** The assessment was accurate when written; two gaps it identified (Render capture, consolidated triage reference) have since been partially closed. The Render record's own access result remains **UNVERIFIED — NO SAFE ACCESS**, so Render deployment reproducibility stays open.

**Action required.** None. §41 cross-references both documents; the assessment is **not rewritten**.

## C-5 — Provenance of this baseline document (INFORMATIONAL — auditability)

The file named by this task was already present in the worktree as an **untracked** file (1,522 lines, mtime 2026-09-12 14:55) before this task began. No commit in the repository references it, and its originating session could not be established from git history; an earlier uncommitted session of the same baseline task is a plausible but **UNVERIFIED** explanation.

**Action taken.** The existing content was preserved in full; only the mandated missing material was added (§62–§65) plus three in-place clarifications (front-matter status and ratification status, §41 operations-document cross-references, §45 ratification marking). If the origin of the untracked draft is material to the PO, it must be established separately — git history cannot establish it.

## C-6 — Unresolved questions carried into discovery

1. Which meaning owns the identifier "Phase 9" (C-1, C-2)?
2. Is the operational-intelligence capability a *product* phase at all, or an internal platform/operations workstream that should not consume a customer-facing phase number?
3. Does the ratified sequence need extending (Phase 9, 10, …) before this baseline can be ratified, or does this content attach to the existing Phase 8 boundary?
4. Which capability areas in §64 are CarbonTally-native, which are external observability tooling, and which are already satisfied (§57 checklist)?

These questions are added to — and do not replace — the required discovery questions in §48.

---

# 64. Candidate Capability Area Register

**CANDIDATE — NOT YET PO-RATIFIED**

This register exists so that the Phase 9 capability surface cannot be silently lost between conversations or development phases. **Do not assume every item will become a CarbonTally-native feature.** Each item must eventually be classified during discovery as *Implemented* / *Existing-reused* / *External system* / *Deferred* / *Not applicable*, with rationale (§57).

| # | Candidate capability area | Discussed in this baseline | Status |
|---|---|---|---|
| 1 | Platform Health | §7.1 | CANDIDATE |
| 2 | API Runtime Intelligence | §8 | CANDIDATE |
| 3 | Background Jobs & Processing | §9 | CANDIDATE |
| 4 | Report Generation Operations | §10 | CANDIDATE |
| 5 | Carbon Calculation Operations | §11 | CANDIDATE |
| 6 | Factor Import Operations | §12 | CANDIDATE |
| 7 | Data Processing Operations | §13 | CANDIDATE |
| 8 | Email / Notification Runtime | §14 | CANDIDATE |
| 9 | Storage & File Operations | §15 | CANDIDATE |
| 10 | CarbonTally Insight / AI Runtime | §16 | CANDIDATE |
| 11 | Billing / Usage Runtime | §17 | CANDIDATE |
| 12 | Authentication & Authorization Operations | §18 | CANDIDATE |
| 13 | Security Operations | §19 | CANDIDATE |
| 14 | Deployment & Release Runtime | §20 | CANDIDATE |
| 15 | Worker & Recovery Intelligence | §21 | CANDIDATE |
| 16 | Operational Incident Reporting | §22 | CANDIDATE |
| 17 | Operational Dashboards | §23 | CANDIDATE |
| 18 | Operational Reports | §24, §45 | CANDIDATE |
| 19 | Alerts & Thresholds | §25 | CANDIDATE |
| 20 | Availability / Reliability Intelligence | §33 | CANDIDATE |
| 21 | Backup / Recovery Visibility | §32 | CANDIDATE |
| 22 | Operational KPI Reporting | §42 | CANDIDATE |
| 23 | Operational Anomaly Detection Assessment | §43 | CANDIDATE |
| 24 | Operational Runbooks / Documentation | §41, §52 | CANDIDATE |

Any further capability area identified during discovery must be **added to this register** before it is implemented, rather than implemented directly.

---

# 65. Baseline Establishment Statement

> **PHASE 9 BASELINE ESTABLISHED — DISCOVERY AND IMPLEMENTATION TO BE AUTHORIZED IN A FUTURE PHASE GATE**

| Field | State |
|---|---|
| Baseline document | ESTABLISHED (this document) |
| Discovery | **NOT STARTED** |
| Implementation | **NOT AUTHORIZED** |
| Production changes | **NONE** |
| PO ratification of the Phase 9 identifier and scope | **NOT YET OBTAINED** — conflicts C-1, C-2 in §63 |
| Implementation boundary of this baseline task | Documentation only: no application code, schema, migration, RLS, API, frontend, AI, billing, deployment or production change; Phase 7 and Phase 8 documents unmodified |

**Phase 9 discovery must open by resolving C-1 and C-2 with the Product Owner**, then proceed to the discovery questions in §48 and the capability classification required by §57. No work in §7–§45 or §64 may be treated as authorized by the existence of this document.

