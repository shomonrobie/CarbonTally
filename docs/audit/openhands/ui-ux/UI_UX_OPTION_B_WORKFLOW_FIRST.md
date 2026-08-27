# UI/UX Option B — Workflow-First

| | |
|---|---|
| Document type | Historical UX option (preserved) — **SELECTED as the platform architecture** |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | HISTORICAL record of the option; **selected as the platform baseline (D18)** |
| Date | 2026-08-24 |

## 1. Status note (reconciliation)

Option B is the **selected platform architecture** (frozen in D18 —
workflow-first authenticated navigation). This document preserves the
historical Option B approach and records how it maps onto the frozen decision.

## 2. Option B characteristics (historical)

- **Workflow-first navigation**: the authenticated UX answers "what needs my
  attention?" rather than "which database module do I want?".
- Customer primary navigation: Home, Documents, Processing, Emissions,
  Reports, Issues, Billing, Organisation (D18).
- Operational roles prioritise Queue, Assignments, Work, Review, QC, Issues,
  Evidence.
- **Split-screen workbench with top workflow navigation** for
  source+structured-data work (D19): source document pane + structured data
  pane; 40/60, 50/50, 60/40 presets.
- No left-side application navigation inside the workbench.
- Not an ERP-style module catalogue.

## 3. Current implementation alignment

The current V3 authenticated surfaces already implement workflow-first
navigation:

- `V3Layout.jsx`: top navigation rail (Dashboard, Emissions, Documents,
  Processing, Issues, Reports, Messages, Existing data, Billing, Organization,
  Consultant, Operations, Notifications), role-aware.
- `OperationsPage.jsx`: ops hub with tabs (Dashboard, Data entry, Review, QC,
  Staff, Roles, Entities, SLA, Commercial).
- `ExtractionPanel.jsx` / `WorkItemWorkspace.jsx` / `EntityExtractionWorkspace.jsx`:
  split-screen source + structured data with top-level stage actions.

## 4. Gaps to close (workflow-first alignment)

- Rename "Dashboard" → "Home" to match D18 (frontend copy).
- "Messages" → "Messaging" copy alignment.
- Add secondary Organisation entries: Locations, Facilities, Assets, Vehicles,
  Suppliers, Members, **Custom Factors**, Activity, Settings (D17/D18).
- Ensure the workbench uses explicit top workflow navigation
  (Queue → Extract → Map → Validate → Review → QC → Evidence) with pane
  presets (D19).
- See `UI_UX_IMPLEMENTATION_MATRIX.md` for the detailed rows.

*End of Option B. Historical evidence preserved; selected as the platform baseline.*
