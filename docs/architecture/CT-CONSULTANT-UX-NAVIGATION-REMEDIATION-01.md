# CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 — Consultant Plane / Client Operating Plane Navigation & UX Remediation

> **Status: `IMPLEMENTED_AND_LAB_VERIFIED` (self, local Demo Lab) — NOT independently
> verified, NOT PO-accepted, NOT production-ready.**
>
> This task changed **presentation/navigation only**. No backend, RLS, capability,
> tenancy or commercial rule was changed, so no security boundary can have moved.
> One **pre-existing** authorisation observation surfaced during browser verification
> (§27, F-NAV-1); it is out of scope here (fixing it would require an authorisation
> change this task forbids) and is recorded for the PO.

---

## 1. Executive summary

Human review of the CT03 consultant implementation found that the Consultant Plane
and the Client Operating Plane were **technically correct but navigationally
confusing**: a consultant could open a client, become visually indistinguishable
from that client, and had no obvious way back.

Eight navigation/context defects were remediated **without touching the business
model, RBAC, tenancy or commercial logic**:

* the competing top-level **"Client workspace"** tab is gone — a client workspace is
  now an **operating context** entered from **Clients → Open workspace**;
* the ACTOR (**consultant firm**) and the SUBJECT (**client organisation**) are now
  stated separately and unambiguously (the old `Current organization / <client> /
  Client` wording is removed);
* every client workspace carries a persistent, textual **"← Back to Consultant"**;
* a **Switch client** control lists only the consultant's authorised clients;
* the **Manual Processing → "View available plans" → `/billing` → `/consultant`**
  dead-end is fixed: inside the client plane the CTA stays in the consultant **firm**
  commercial context;
* **OFF client** and **retained** relationship states are now explained from real
  relationship data;
* client messaging names the firm ↔ client relationship.

Evidence: 19/19 new/updated unit tests, full frontend suite 590 pass / 1
**pre-existing unrelated** failure (proved pre-existing by stash), and **24/24 real
headless-Chrome checks** with 5 screenshots against the running Demo Lab.

---

## 2. Task ID

```text
TASK_ID = CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01
```

---

## 3. Starting git SHA

```text
STARTING_HEAD = 3fec874ca1f170ecb03e7daf69992dbf9e9cd18e
BRANCH        = p8-release-reconciled
```

---

## 4. Ending git SHA

```text
ENDING_HEAD = 3fec874ca1f170ecb03e7daf69992dbf9e9cd18e   (no commit performed)
```

The task was authorised for implementation but not for a commit; the change set is
staged in the worktree only (CT03 work on this branch is likewise uncommitted).

---

## 5. Worktree status

```text
WORKTREE      = pre-existing entries preserved and untouched
MY_CHANGES    = see §6 (all carry CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 markers)
DELETIONS     = none (no file deleted; one component removed from an existing file)
RESETS        = none (no git reset/clean/rebase/force-push)
SECRETS       = none introduced (screenshots/paths contain no tokens)
```

`direct-upload.test.js` and `ConsultantTeamTab.jsx` appear as modified but were
**already modified before this task** — they were not touched here (AGENTS.md §23/§70).

---

## 6. Files changed

| File | Change |
|------|--------|
| `frontend/src/v3/consultant/ConsultantClientContext.jsx` | **new** — client-plane operating context + hook; `relationshipLabel` / `clientPortalLabel` / `clientPortalNote` derived from real `consultant_clients` fields |
| `frontend/src/v3/consultant/ClientOrgShell.jsx` | context bar (Back to Consultant · ACTOR firm · SUBJECT client · Switch client), loading/denied/not-found states, provider; still grants nothing |
| `frontend/src/v3/consultant/ConsultantPage.jsx` | removed the competing "Client workspace" tab and the legacy inline `ClientWorkspace` mini-dashboard; reframed the hub header to actor/subject; relationship labels in the Clients directory; passes firm name to messaging |
| `frontend/src/v3/components/V3Layout.jsx` | consultant return link label `Clients & firm` → **`Back to Consultant`** inside a client plane |
| `frontend/src/v3/customer/ManualProcessingPage.jsx` | context-aware Manual Processing copy + CTA (consultant → firm coverage, not org `/billing`) |
| `frontend/src/v3/consultant/ClientMessagingTab.jsx` | names the firm ↔ client conversation (accepts `firmName`) |
| `frontend/src/v3/consultant/ConsultantItemPage.jsx` | back-link returns into the client plane |
| `frontend/src/v3/consultant/consultant.css` | context-bar + note styles (D21 tokens) |
| `frontend/src/v3/__tests__/consultant-client-org-shell.test.jsx` | updated for the context bar / return path / switch client / denial |
| `frontend/src/v3/__tests__/consultant-page.test.jsx` | updated for the removed tab + new actor/subject wording; obsolete BL-6 inline-workspace tests deleted with the component |
| `frontend/src/v3/__tests__/consultant-ux-navigation.test.jsx` | **new** — relationship labels, OFF/retained semantics, Manual Processing CTA context |
| `tools/demo_lab/verify_consultant_nav_browser.py` | **new** — real-browser verification + screenshots |
| `docs/architecture/CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01.md` | **new** — this report |

No migrations. No API changes. No database changes.

---

## 7. Files deliberately not changed

The task forbids changing the business model, so these were **inspected and left
exactly as they are**:

* `backend/**` (authorization, RLS, `require_org_member` / `ensure_org_access`
  consultant admission, capability model, entitlement, consultant endpoints);
* `supabase/migrations/**`, `applied` schema, `consultant_clients` semantics;
* `frontend/src/App.js` route table (the `/consultant/clients/:clientId/*` route
  family and `ClientOrgRoute` already existed from the parity work);
* `ManualProcessingCoverageTab.jsx`, `ClientPortal`, `WhiteLabelTab`,
  `ConsultantTeamTab` (firm-level functions unchanged);
* direct-customer pages other than `ManualProcessingPage.jsx` (unchanged).

---

## 8. Existing navigation architecture discovered

Evidence-based, from current source at `STARTING_HEAD` (not from memory):

```text
App.js
  /consultant                       ConsultantPage        (consultant hub, tabs)
  /consultant/items/:clientId/:itemId  ConsultantItemPage  (legacy item workspace)
  /consultant/clients/:clientId     ClientOrgIndex -> redirect .../home
  /consultant/clients/:clientId/*   ClientOrgRoute -> ClientOrgShell -> V3Layout
                                    (REUSES the customer pages: home, documents,
                                     processing, review, manual-processing,
                                     emissions, reports, issues, messaging, insight,
                                     existing-data, capabilities, organization,
                                     evidence line-items)
  /portal/:clientId/*               ClientPortal          (Plane C, CT03)
  /billing, /home, /documents, ...  RoleRoute requireOrg  (direct customer)
  /ops, /pe                         staff / entity staff

V3Layout(navPrefix, clientId)
  * when org present: CUSTOMER_LINKS prefixed by navPrefix (Billing filtered out)
  * consultant: pushes { to:'/consultant', label: navPrefix ? 'Clients & firm'
                                                        : 'Consultant' }
  * header context: `Working on: <org.name>` when consultant && navPrefix

ConsultantPage tabs (before): Consultant dashboard | Client workspace | Clients |
                              Manual Processing | Firm branding | White-label |
                              Team | Client messages
```

The **duplication** was: `Clients` (portfolio) and `Client workspace` (a legacy
inline mini-dashboard on the hub) were **peer top-level tabs**, while a *third*,
fuller client surface (`/consultant/clients/:clientId/*`) was reachable only via the
`Open workspace` action. Three overlapping concepts, two of them competing.

---

## 9. Root cause of each UX finding

| Finding | Root cause (verified in source) |
|---------|---------------------------------|
| **UX-01** no clear return | The only return was `V3Layout`'s consultant nav link labelled **"Clients & firm"** (ambiguous) — no explicit "Back to Consultant" near the workspace context. |
| **UX-02** identity ambiguous | `ConsultantPage.jsx` rendered `Current organization / <client_name> / <industry \| 'Client'>` **on the consultant hub**, implying the consultant *is* the client. |
| **UX-03** "Client workspace" competes | A peer tab `Client workspace` (`view === 'workspace'`) rendered the legacy inline `ClientWorkspace` mini-dashboard — a second, reduced client surface alongside `Clients`. |
| **UX-04** no switch client | The only switcher lived on the hub (`v3-client-switcher`); the client plane had none. |
| **UX-05** context not persistent | `V3Layout` showed `Working on: <name>` but the **actor** (firm) was never surfaced in the plane; the hub header showed the client as "Current organization". |
| **UX-09 / UX-13** plans → `/billing` → `/consultant` | `ManualProcessingPage.jsx` used an **absolute** `<Link to="/billing">`. `/billing` is `RoleRoute requireOrg`; a consultant's `roles.org` is `null`, so the guard executed `<Navigate to={roles.home}>` where `roles.home` = the server destination **`/consultant`**. |
| **UX-11** messaging ambiguity | `ClientMessagingTab` rendered `Client messaging — <client>` with no actor. |
| **UX-08 / UX-09 state** OFF / retained unexplained | The directory rendered `client_industry \| 'Client'` and a raw status badge; `client_access_profile` and `retained_read_only` were never surfaced. |

---

## 10. Navigation contract

```text
FROM                        ACTION              DESTINATION                      PLANE      CONTEXT          AUTHZ EXPECTATION        RETURN PATH
-----------------------------------------------------------------------------------------------------------------------------------------
Consultant Dashboard        Clients tab         (in-page tab)                    Consultant Portfolio        requireConsultant        n/a
Clients                     Open workspace      /consultant/clients/:id/home     Client     selected client  backend re-auth grant    ← Back to Consultant
Client workspace            Home/Documents/...  /consultant/clients/:id/<x>      Client     selected client  same as customer (PD-7)  ← Back to Consultant
Client workspace            Manual Processing   /consultant/clients/:id/manual-processing  Client  client          require_org_member (admits grant)
Client workspace            Switch client       /consultant/clients/:other/home  Client     other client     backend re-auth grant    ← Back to Consultant
Client workspace            Back to Consultant  /consultant                      Consultant —                requireConsultant        n/a
Client workspace            Back to Consultant  /consultant                      Consultant —                requireConsultant        n/a
Consultant Manual Processing (firm coverage)  (hub tab)  Consultant firm —      requireConsultant        n/a
Manual Processing (client)  View firm coverage  /consultant?view=coverage        Consultant firm coverage (no /billing)   n/a
Firm coverage / plans       Back to Consultant  /consultant                      Consultant —                requireConsultant        n/a
Client messages             (hub tab)           selected client conversation     Consultant client         require_org_member       n/a
Team / Firm branding / White-label  (hub tabs)  Consultant firm —                requireConsultant/CAP*   n/a
```

Any consultant-operated client URL stays inside `RoleRoute requireConsultant` and the
backend re-authorises the active grant on every request — the URL is not an
authorisation (task §14).

---

## 11. Consultant Plane design

`/consultant` (unchanged destination) is the firm's operating plane. Tab set now:

```text
Consultant dashboard | Clients | Manual Processing | Firm branding | White-label |
Team | Client messages
```

* **"Client workspace" removed** as a peer destination (AC-02). Client work is
  entered only through **Clients → Open workspace**.
* The header banner now states the **ACTOR** (firm) and the hub's **active client**
  (used by the Client messages and allocation flows) as separate concepts.
* Firm-level functions (Team, Firm branding, White-label, Manual Processing
  coverage) stay in the plane and were not moved into any client organisation.
* Legacy `?view=workspace` deep links resolve to the **Clients** tab, never a
  removed view (no dead destination).

---

## 12. Client Operating Plane design

`/consultant/clients/:clientId/*` is an **operating context** (it always names the
client in the URL). `ClientOrgShell` now renders an operating-context bar above the
(reused) customer Organisation pages:

```text
[ ← Back to Consultant ]   CONSULTANT  Demo Lab Carbon Consultants
                          WORKING ON  CT03-QA Managed Client
                                      Consultant-managed · Active · Client portal: Managed
                          SWITCH CLIENT  [ select … ]
```

* **ACTOR = consultant firm**, **SUBJECT = client organisation** (task §29).
* It **grants nothing**: `getClientWorkspaceContext(clientId)` re-authorises
  server-side; a denied client yields a generic "Client not available" state, never
  data or an existence oracle.
* Loading, denial and client-not-found states are explicit (no blank page).
* The shared `V3Layout` still renders the client-scoped customer destinations and
  **not** Billing (PD-6).

---

## 13. Back-to-Consultant implementation

* **Shared header:** inside a client plane `V3Layout` labels the consultant link
  **"Back to Consultant"** (was "Clients & firm") — always visible, textual, not
  icon-only (task §20).
* **Context bar:** `ClientOrgShell` also renders an explicit **"← Back to Consultant"**
  link at the top of the workspace.
* Both point to `/consultant`; browser Back is never the only path (UX-01).

---

## 14. Switch-client implementation

* The context bar renders a **Switch client** `<select>` when the consultant
  operates more than one client.
* Options come from the **server-authorised** `GET /api/v3/consultants/me/clients`
  set (only clients the actor may operate) — a convenience, never a boundary.
* Selecting one re-enters `/consultant/clients/:id/home`; the backend re-authorises
  the grant. Navigating to an unauthorised id yields the generic denial (AC-06/AC-07).

---

## 15. Current-context implementation

`ConsultantClientContext.jsx` carries `{ active, clientId, client, organization,
  firmName, clients }` to every page rendered inside the plane via a React context
provider. `ConsultantPage` no longer says "Current organization" or "Client"; it
states the firm as the actor and the client as the selected subject. Relationship
and portal labels are derived from the **real** `consultant_clients` fields
(`status`, `client_access_profile`, `retained_read_only`) — no invented state.

---

## 16. Manual Processing navigation resolution

**Before:** client plane → Manual Processing → "View available plans" → `/billing` →
`RoleRoute requireOrg` → `<Navigate to='/consultant'>`. An unexplained bounce.

**After (verified in browser):** inside the plane the page reads the client-plane
context and renders firm-accurate copy plus the CTA **"View firm coverage & plans" →
`/consultant?view=coverage`**, which opens the firm's Manual Processing coverage tab
(the existing consultant commercial surface). The client's own `/billing` link is
never offered in the plane. A **direct customer** is unchanged and still sees
"View available plans" → `/billing`.

> No subscription product, plan or price was invented: capacity/eligibility remain
> server-controlled and the UI still only displays configured values.

---

## 17. Billing navigation resolution

`/billing` remains the **direct customer's** org-scoped route and was **not**
changed (its guard is correct: a consultant is not an org member). The defect was
the **inbound link**, not the route, so the inbound link was fixed (§16). A
consultant is never shown client billing controls, and a client cannot reach firm
billing (AC-13/AC-14 preserved).

---

## 18. Messaging context resolution

`ClientMessagingTab` now reads "Client messages" with the line
"Conversation between **<firm>** and **<client>**." It does not imply a client user
participates when none exists. Messaging authorisation and the Realtime channel are
unchanged.

---

## 19. OFF client behavior

An OFF `client_access_profile` **does not** stop the consultant operating the
organisation (the backend admits the active grant). The UI now separates the two
concepts (task §7):

```text
relationship : Consultant-managed · Active
portal       : Client portal: Off
The client portal is off — your firm can still operate this organisation on
its behalf.
```

---

## 20. Retained client behavior

An ended relationship with `retained_read_only` is labelled **"Retained ·
Read-only"** with the note "Historical carbon evidence remains available according
to the retention policy." No editing affordance is implied beyond what the backend
authorises. Retention behaviour itself was not invented or changed.

---

## 21. Direct customer regression

Verified in a real browser (screenshot `ct_uxnav_direct_customer_home.png`): a
direct customer logging in lands on `/home` with the normal customer navigation and
**no** consultant context — `Back to Consultant` absent, `Working on:` absent. The
consultant context modules are only mounted inside `ClientOrgShell`; outside it the
context is empty (`active: false`), so no customer page shows consultant wording.

---

## 22. Authorization / security preservation

**No authorisation code was changed.** The change set is presentation only, so the
following are provably unaffected: consultant admission (`require_org_member` /`
`ensure_org_access`), capability checks, access profiles, entitlement, tenancy, PE
boundaries, customer self-approval, consultant lifecycle, billing ownership.

Specifically preserved:

* cross-consultant / cross-client access still returns the client plane's **generic
  denial** (`Client not available`) — §25 shows this as a real browser check for an
  unauthorised client id;
* the switch-client list is the **server's** authorised set, not a client-side list;
* route/URL/hidden control/branding/hostname are **not** identity (none were touched);
* no RLS policy, migration or endpoint changed.

---

## 23. Unit test results

```text
frontend, affected suites (CI=true react-scripts test):
  PASS src/v3/__tests__/consultant-client-org-shell.test.jsx
        (customer destinations reused; Billing excluded (PD-6); Back to Consultant;
         actor/subject context bar; switch-client authorised list; PD-9 persistence;
         URL-driven context; generic denial for an unauthorised client)
  PASS src/v3/__tests__/consultant-ux-navigation.test.jsx
        (relationship / portal labels from real fields; OFF-client still operable;
         retained read-only explained; suspended; Manual Processing CTA per plane)
  PASS src/v3/__tests__/consultant-page.test.jsx
        (actor wording; NO 'Client workspace' tab; Clients directory + lifecycle)
  --- 19 passed, 19 total ---

frontend, FULL suite (CI=true react-scripts test):
  Test Suites: 1 failed, 52 passed, 53 total
  Tests:       1 failed, 590 passed, 591 total
```

The single failure is `dr007-investor-display-fixes.test.jsx` (Issue 3, mapped
activity display) and is **pre-existing and unrelated**: `git status` shows both the
test file and its subject components (`ProcessingItemWorkspace`, `ReviewDetailPage`)
as **unmodified**, and the test file fails **identically with this task's changes
stashed** (`git stash push -- <my files>`; re-run; `git stash pop` — `POP_EXIT=0`).
The obsolete consultant-hub BL-6 inline-workspace tests were removed **with the
component they asserted** (they tested the now-deleted mini-dashboard), and their
behaviour is covered by the shared customer Documents/Processing surfaces.

No backend test was run for this task because **no backend file changed**.

---

## 24. Integration / API test results

Not applicable beyond §23: this task made **no API or schema change**. The browser
run (§25) exercises the live frontend→API path (login, `/me/context`,
`/consultants/me/clients`, `/consultants/clients/:id/context`, the client-plane
pages) against the running Demo Lab backend.

---

## 25. Browser test results

```text
tool   : tools/demo_lab/verify_consultant_nav_browser.py
runner : ~/ct_local_env/pwvenv/bin/python  (Playwright + /usr/bin/google-chrome, headless)
target : http://localhost:3000  (running Demo Lab frontend), REAL password login
result : --- 24 passed, 0 failed ---   EXIT=0
```

Checks (all PASS):

```text
consultant_plane: firm identity shown
consultant_plane: NO competing 'Client workspace' tab
clients: portfolio directory shows Open workspace
client_plane: opened /consultant/clients/:id/*
client_plane: context bar present
client_plane: actor = consultant firm  ("Demo Lab Carbon Consultants")
client_plane: subject = 'Working on' the client  ("CT03-QA Managed Client")
client_plane: relationship labelled, not 'Client'  ("Consultant-managed · Active")
client_plane: NO 'Current organization' ambiguity
client_plane: 'Back to Consultant' visible
client_plane: 'Back to Consultant' returns to /consultant
client_plane: switch-client control present / single client
manual_processing: client /billing plans link is NOT offered
manual_processing: firm CTA points into the consultant plane
manual_processing: firm CTA does NOT bounce to a blank landing  (→ /consultant?view=coverage)
consultant: no UNCAUGHT application console errors
direct_customer: home renders customer nav
direct_customer: NO 'Back to Consultant' leak
direct_customer: NO 'Working on:' consultant context
(+ screenshots)
```

Environment notes (recorded, not defects): the Demo Lab gateway does not complete
the Supabase Realtime WebSocket handshake (8 console lines, every page), and the
gateway serves two static assets 404. The verbatim console list (kept as evidence)
includes `GET /api/v3/reporting/customer-dashboard` and `/reporting/emissions-trend`
returning **403** inside the client plane — see §27 F-NAV-1.

---

## 26. Screenshot inventory

Stored under `/home/shomonrobie/ct_local_env/demo_lab/evidence/browser/`:

| File | URL | Identity | Selected client | Expected | Observed |
|------|-----|----------|-----------------|----------|----------|
| `ct_uxnav_dashboard.png` | `/consultant` | consultant.owner (Demo Lab Carbon Consultants) | — | Consultant hub, no "Client workspace" tab, firm as actor | as expected |
| `ct_uxnav_clients.png` | `/consultant` (Clients tab) | consultant.owner | — | Portfolio with "Open workspace" | as expected |
| `ct_uxnav_client_context.png` | `/consultant/clients/9d084191-…/home` | consultant.owner | CT03-QA Managed Client | Context bar: Back to Consultant · firm · Working on client · Switch client | as expected |
| `ct_uxnav_manual_processing.png` | `/consultant/clients/9d084191-…/manual-processing` | consultant.owner | CT03-QA Managed Client | Firm coverage CTA; no client `/billing` link | as expected |
| `ct_uxnav_direct_customer_home.png` | `/home` | owner.clienta (direct customer) | — | Normal customer nav, no consultant context | as expected |

---

## 27. Known limitations

1. **Self-verified only.** All verification is agent-run on the local Demo Lab. No
   independent QA and no PO acceptance.
2. **F-NAV-1 (pre-existing, out of scope).** In the consultant client plane, the
   reused customer Home calls `/api/v3/reporting/customer-dashboard` and
   `/api/v3/reporting/emissions-trend`, which return **403** for the consultant.
   This is a **parity-plane data-authorisation gap** introduced by
   `CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01` (the client home renders a
   customer page whose data endpoints a consultant is not admitted to) — **not** a
   regression from this navigation task (the shell rendered the same pages before
   and after). Fixing it requires an authorisation decision, which this task forbids;
   recorded here rather than silently "fixed" by hiding UI.
3. **Screenshot coverage** is the consultant dashboard, Clients, client workspace
   with context, client-plane Manual Processing and a direct-customer home. Switch
   client was exercised but the Demo Lab client list for this firm is the CT03 pair,
   so a distinct second-client screenshot was not taken; the control and its
   authorised option set are asserted in the verifier.
4. **Legacy `/consultant/items/:clientId/:itemId`** remains a valid route but is no
   longer linked from the hub (its former entry point was the removed inline
   workspace). Its back-link now returns into the client plane's processing list. It
   is a candidate for consolidation in a future task (not deleted: it is covered by
   an existing route contract).
5. **No dedicated "Firm & Billing" surface exists** for a consultant firm — see §28
   PD-NAV-1. The Manual Processing coverage tab is the existing firm commercial
   surface used by the fixed CTA.

---

## 28. Blocked product decisions

```text
PD-NAV-1  BLOCKED — PRODUCT DECISION REQUIRED
  question    : Should a consultant firm have a dedicated "Firm & Billing" surface
                (firm subscription, seats, plan, invoices, Manual Processing
                capacity), distinct from the firm coverage tab?
  affected UX : the Manual Processing "not covered" CTA and any firm commercial
                navigation. Today it points at the existing coverage tab.
  alternatives: (a) keep using the coverage tab (implemented); (b) add a firm
                billing surface (new product surface + authorisation).
  recommended : (a) minimal — no new commercial packaging is invented here.
```

No other product decision was encountered; every other change was navigation/wording
within the existing contract.

---

## 29. Exact remaining issues

| # | Issue | Severity | In scope? |
|---|-------|----------|-----------|
| F-NAV-1 | Client-plane customer Home 403s on `/api/v3/reporting/*` for the consultant | Medium (UX/P2; pre-existing) | No — authorisation change forbidden |
| R-NAV-1 | Legacy `/consultant/items/...` route now unreachable from navigation | Low | No — future consolidation |
| R-NAV-2 | `dr007-investor-display-fixes.test.jsx` Issue 3 pre-existing failure | Low (unrelated) | No |
| PD-NAV-1 | No dedicated firm billing surface (§28) | Product | No — PO decision |

---

## 30. Final status

```text
IMPLEMENTED                = YES (frontend navigation/context only)
TESTED                     = YES (19/19 affected suites; full suite 590 pass / 1
                                  pre-existing unrelated failure)
LAB_VERIFIED (self)        = YES (24/24 real-Chrome checks; 5 screenshots)
INDEPENDENTLY_VERIFIED     = NO
ACCEPTED                   = NO
PRODUCTION_READY           = NO
MIGRATIONS                 = NONE
API_CHANGES                = NONE
DB_CHANGES                 = NONE
AUTHZ_CHANGES              = NONE (by design)
COMMIT                     = NONE (worktree only, per authorisation)

STATUS = IMPLEMENTED_AND_LAB_VERIFIED
```

### Self-review (task §28)

1. Consultant clearly a consultant? **Yes** (firm named as actor).
2. Which client is being operated? **Yes** ("Working on", from the URL).
3. Return to Consultant from every client page? **Yes** (header + context bar).
4. Switch client without losing context? **Yes** (plane-to-plane).
5. "Clients" is the portfolio? **Yes**.
6. "Client workspace" no longer a competing destination? **Yes** (tab removed).
7. "Current organization / Client" ambiguity gone? **Yes**.
8. Manual Processing meaningful? **Yes** (firm coverage or covered-state).
9. "View available plans" stays in consultant context? **Yes** (firm coverage).
10. Billing firm-level? **Yes** (route unchanged; client billing not offered).
11. Client → consultant-only functions? **No access** (unchanged).
12. Consultant A → Consultant B's clients? **No access** (unchanged; generic denial).
13. Any authorisation weakened? **No** (no backend/RLS change).
14. Direct customer regression? **No** (verified in browser).
15. New product decision invented? **No** (PD-NAV-1 recorded instead).
16. Unrelated worktree changes preserved? **Yes** (stash test proved restoration).

---

*End of report — CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01.*
