# CarbonTally V3 — MASTER UX RECOMMENDATION (Approved Reconciliation)

| | |
|---|---|
| Document type | Approved UX recommendation / reconciliation decisions |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | **APPROVED** (feeds the frozen D1–D21 baseline) |
| Date | 2026-08-24 |
| Authority | Product Owner decision baseline D1–D21 + reconciliation against current implementation |

## 1. Purpose

This document records the approved UX recommendation for CarbonTally V3 and
the reconciliation decisions that resolve conflicts between the target UX and
the current implementation. It is the bridge between the Product Owner's
frozen decisions (D1–D21) and the detailed screen/workflow/design deliverables.

## 2. Selected architecture (approved)

| Surface | Approach |
|---|---|
| Platform (authenticated, all roles) | **Option B — workflow-first** |
| Customer / onboarding / evidence | **Option C — modern/guided** |
| CarbonTally Admin / control plane | **Option A — enterprise/dense** |
| Processing workbench | **Split-screen + top workflow navigation (D19)** |
| Visual system | **One unified design system (D21)** |

## 3. Reconciliation decisions

| # | Topic | Recommendation | Status vs implementation |
|---|---|---|---|
| R1 | Customer navigation | Home, Documents, Processing, Emissions, Reports, Issues, Billing, Organisation (D18) | PARTIALLY IMPLEMENTED — "Dashboard" label to become "Home"; "Messages" → "Messaging" copy; add Custom Factors under Organisation |
| R2 | Organisation navigation | Overview, Locations, Facilities, Assets, Vehicles, Suppliers, Members, Custom Factors, Activity, Settings | PARTIALLY IMPLEMENTED — Facilities/Assets/Suppliers/Members exist; Vehicles missing (G-P1-2); Locations distinct surface missing (**N2**: engineering decides dedicated table vs Facilities reuse); Custom Factors/Activity/Settings target |
| R3 | Workbench | Top workflow navigation + split panes; presets 40/60, 50/50, 60/40; PE no-download preserved | PARTIALLY IMPLEMENTED — split panes exist in ExtractionPanel/WorkItemWorkspace/EntityExtractionWorkspace; explicit top workflow nav wizard + presets + confidence/evidence links are target |
| R4 | Customer review vs approval | Separate surfaces; approval evidence-first with Approve/Reject | BACKEND READY / UI MISSING for a dedicated customer approve surface; `customer-review` route exists |
| R5 | Custom factors | Org-scoped surface with lifecycle + approval + precedence UI | BACKEND READY / UI MISSING (API + RLS exist; no V3 UI tab) |
| R6 | Issues | First-class operational issue object, distinct from conversations (ADR-V3-009); ops triage | IMPLEMENTED (backend + customer/ops/entity surfaces); ops triage polish target |
| R7 | Evidence | Universal evidence trail (D33); "where did this come from?" | PARTIALLY IMPLEMENTED — evidence records in reports/emissions; universal evidence UI target |
| R8 | Status vocabulary | Single visual/textual treatment per status; reconcile with backend ITEM/BATCH/REPORT/ISSUE/ENTITY statuses | PARTIALLY IMPLEMENTED — v3.css badges cover a subset; vocabulary doc in design system |
| R9 | Design tokens | One token system; consolidate `v3.css`/`App.css`/`ops.css`/`admin.css`/`consultant.css`/`reports.css` | INCONSISTENT — two green primaries (#2f855a v3 vs #2d6a4f App.css); consolidation is P0/P1 |
| R10 | Consultant UX | Active-client model; explicit client banner; white-label foundation | IMPLEMENTED |
| R11 | PE UX | Entity-scoped work surface; no customer access; mediated clarification | IMPLEMENTED (D22); **N1** confirms no direct Customer↔PE messaging — clarification stays in the controlled workflow (G-P1-1) |
| R12 | Staff UX | Ops hub: Dashboard, Data entry, Review, QC, Staff, Roles, Entities, SLA, Commercial | IMPLEMENTED |
| R13 | Admin UX | Dense control-plane for platform admin; org admin stays in customer surface | PARTIALLY IMPLEMENTED — Commercial/Entities/SLA tabs are admin-dense; broader admin console target |
| R14 | Mobile | Desktop primary for processing; mobile monitoring/light review; adaptive trays on tablet | PARTIALLY IMPLEMENTED — grid collapse at ≤900px; tray-based workbench is target |
| R15 | Public site | Pre-launch, GBP indicative pricing, "Request launch information", no fake waitlist; claims match capability | LIVE AHEAD OF COMMITTED — live site matches target; committed baseline still has beta/waitlist modal |

## 4. Role UX recommendations (summary)

- **Customer**: attention dashboard → documents → processing status → review →
  approve → evidence → reports → emissions → notifications.
- **Consultant**: active client → client switching → client status → workflow
  → issues → reports → evidence.
- **Processing Entity**: assigned work → queue → priority → source document →
  extraction → validation → review → QC → clarification → evidence (entity
  scoped).
- **CarbonTally Staff**: operational queue → assignments → extraction → review
  → QC → PE coordination → issues → escalation → evidence.
- **CarbonTally Admin**: organisations → users → roles → Processing Entities →
  consultants → billing → subscriptions → pricing → factor governance →
  system configuration → audit → security → logs → operational monitoring.

## 5. Interaction principles

1. Workflow-first, attention-driven navigation (D18).
2. Split-screen workbench with top workflow navigation for source+structured
   work (D19).
3. Status never communicated by colour alone (D21.4).
4. Evidence and provenance visible wherever a number is shown (D33).
5. Server-authoritative calculations/factors; human review gates (D16).
6. Explicit organisation/client context at all times (D3/D8).
7. PE boundary: work-access only, no customer/consultant access, CarbonTally
   mediated communication (D6/D18).
8. Consistent visual identity across all surfaces (D21).

## 6. Handoff

Detailed deliverables: screen inventory, workflow map, ASCII designs,
implementation matrix, design system (see `MASTER_INDEX.md` reading order).

*End of master UX recommendation. Approved reconciliation. Documentation-only.*
