# CarbonTally V3 — D27 Read-Only Audit Inventory (Part 1)

Produced before implementation (2026-08-22). Classification: IMPLEMENTED /
PARTIALLY IMPLEMENTED / MISSING / SECURITY RISK / UX GAP / EXTERNAL
CONFIGURATION REQUIRED.

## Architecture / tenancy

| Item | Classification | Notes |
|---|---|---|
| `organizations` as data-tenancy anchor | IMPLEMENTED | unchanged; no generic tenant/workspace abstraction |
| D15 active consultant grant (RLS `is_org_consultant` + API `ensure_consultant_org_access`) | IMPLEMENTED | only `status='active'` grants access |
| D20 scope-first staff authorization | IMPLEMENTED | internal vs entity staff boundary on `AuthUser`; legacy guards scoped |
| D21 white-label branding foundation | IMPLEMENTED | `consultant_profiles` branding + `white_label_enabled` + BrandContext |
| D22 entity work assignment + extraction workspace | IMPLEMENTED | `manual_extraction_batches.entity_id` + entity-scoped workspace |
| D23 extraction UX | IMPLEMENTED | ops/entity extraction surfaces |
| Phase 9 RLS recursion fix | IMPLEMENTED | SECURITY DEFINER helpers + rewritten policies |

## D19 scope

| Item | Classification | Notes |
|---|---|---|
| Consultant lifecycle ACTIVE/SUSPENDED/ENDED | MISSING (pre-D27) → **IMPLEMENTED (D27)** | lifecycle columns + transitions + RLS/API + audit |
| Customer-initiated direct onboarding | MISSING (pre-D27) → **IMPLEMENTED (D27)** | `/api/v3/discovery/*` |
| Existing-data discovery | MISSING (pre-D27) → **IMPLEMENTED (D27)** | candidate signals only; safe data counts |
| Secure verification | MISSING (pre-D27) → **IMPLEMENTED (D27)** | email code / staff mediation; never name/domain-based |
| USE ALL / PARTIAL / DISCARD | MISSING (pre-D27) → **IMPLEMENTED (D27)** | partial = recorded selection (no unsafe copy) |
| DISCARD = no deletion | MISSING (pre-D27) → **IMPLEMENTED (D27)** | recorded decision only |
| In-place org identity preservation | MISSING (pre-D27) → **IMPLEMENTED (D27)** | existing `organizations.id` adopted; no copy |
| Consultant access termination | MISSING (pre-D27) → **IMPLEMENTED (D27)** | adoption ends ACTIVE grants; API + RLS deny |

## White-label / communication

| Item | Classification | Notes |
|---|---|---|
| Custom-domain lifecycle | MISSING (pre-D27) → **IMPLEMENTED (foundation)** | Vercel DNS routing is EXTERNAL CONFIGURATION REQUIRED |
| Custom email sender | MISSING (pre-D27) → **IMPLEMENTED (foundation)** | Resend verification EXTERNAL CONFIGURATION REQUIRED |
| Consultant-branded communication | PARTIALLY IMPLEMENTED | BrandContext on reports/PDF; per-consultant email templates FUTURE |
| White-label PDF rendering | MISSING (pre-D27) → **IMPLEMENTED (D27)** | `engines/pdf_render.py` (reportlab) |
| Consultant-client messaging | MISSING (pre-D27) → **IMPLEMENTED (D27)** | Realtime RLS fix + `/api/v3/messaging/*` + UI |
| Processing Entity boundary | IMPLEMENTED (preserved) | no entity messaging; mediated clarification only |

## Product surfaces

| Item | Classification | Notes |
|---|---|---|
| Customer onboarding | IMPLEMENTED | + D27 existing-data flow |
| Consultant onboarding | IMPLEMENTED | profile + team + invites + client management |
| Entity onboarding | PARTIALLY IMPLEMENTED | provisioning + workspace; invitation acceptance flow FUTURE |
| Google OAuth | EXTERNAL CONFIGURATION REQUIRED | Supabase dashboard |
| MFA / 2FA | EXTERNAL CONFIGURATION REQUIRED | Supabase MFA |
| Customer Issues UI | IMPLEMENTED (D25) | customer replies FUTURE |
| Notifications UI | IMPLEMENTED (D25/D26) | per-recipient + pagination |
| SLA UI | IMPLEMENTED (D25) | reuses existing SLA architecture |
| Frontend route guards | IMPLEMENTED (D25) | RoleRoute; backend/RLS authoritative |
| Staff-role reference | IMPLEMENTED (D25) | read-only catalog |
| Export | PARTIALLY IMPLEMENTED | emissions/documents CSV/JSON; full-org export FUTURE |
| Import (customer data) | MISSING / DESIGN ONLY | safe import undefined → not built |
| D19 event audit logging | MISSING (pre-D27) → **IMPLEMENTED (D27)** | discovery + lifecycle + white-label audited |

## Security / UX / infra

| Item | Classification | Notes |
|---|---|---|
| `conversation_participants` RLS | SECURITY RISK (pre-D27: zero policies = deny-all) → **FIXED (D27)** | recursion-safe participant policies |
| `ensure_org_access` no-bound-org bypass | SECURITY RISK (D20 documented) | already mitigated by D20 for entity staff; `/api/v2/business/*` pairing reviewed in D20 |
| `services/email_service.py` syntax error | SECURITY/QUALITY (pre-existing) | not imported by V3; V3 email is `services/v3_email.py` |
| Entity staff messaging exposure | SECURITY RISK (pre-D27: no path) → **VERIFIED DENIED (D27)** | test enforces 403 |
| Four workspace UI consistency | UX GAP (minor) | D27 additions use the existing design system; browser audit pending |
| Vercel/Render/Supabase/Resend production config | EXTERNAL CONFIGURATION REQUIRED | documented in the D27 report §30 |

*End of audit inventory.*
