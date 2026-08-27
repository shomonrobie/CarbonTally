# UI/UX Option A — Enterprise

| | |
|---|---|
| Document type | Historical UX option (preserved) |
| Project | CarbonTally |
| Architecture | CarbonTally V3 |
| Version | 1.0 |
| Status | HISTORICAL — superseded as a standalone option; **composed into the selected architecture for CarbonTally Admin / control-plane surfaces** |
| Date | 2026-08-24 |

## 1. Status note (reconciliation)

Option A is **no longer an unresolved alternative**. The Product Owner has
frozen D1–D21 and the selected architecture composes the three options:
**Option A supplies the enterprise / control-plane treatment for CarbonTally
Admin surfaces** (dense information, administration tables, system
configuration, audit/security/logging, operational monitoring). It is not the
platform-wide choice.

This document preserves the historical Option A approach as evidence.

## 2. Option A characteristics (historical)

- **Dense, information-rich enterprise UI**: data tables, dense grids, master
  lists, bulk actions, admin consoles.
- **Module-catalogue navigation** style: left-side navigation of domains and
  administration modules (organisations, users, roles, entities, consultants,
  billing, factors, audit, settings).
- **Power-user orientation**: keyboard operation, multi-select, column
  configuration, high information density.
- **Control-plane focus**: system configuration, RBAC, subscriptions, factor
  governance, logs, audit, security events, workflow/job history, failed jobs,
  health/configuration state.

## 3. Where Option A remains the target

- CarbonTally Admin surfaces (staff role `admin`): the ops "Commercial",
  "Entities", "SLA", "Staff", "Roles" tabs and any future
  platform-administration console use denser enterprise patterns.
- System settings / governance / audit / logs UX for platform administrators.
- The target admin UX may use a denser Enterprise/control-plane architecture
  (per D18).

## 4. Constraints inherited from the frozen decisions

- D4: organisation administration is never collapsed into platform
  administration; the admin control plane is a distinct surface.
- D21: even dense admin screens remain visually recognisable as CarbonTally
  (one unified design system).
- D18: do not turn the customer platform into an ERP-style module catalogue;
  Option A density is reserved for admin/control-plane surfaces.

*End of Option A. Historical evidence preserved.*
