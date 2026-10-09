// frontend/src/v3/clientAccess.jsx
// CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05 — the CLIENT-ACCESS view for a
// consultant-managed client's own user.
//
// Authority: docs/architecture/CT-CONSULTANT-PO-CONSOLIDATION-01.md §8.2/§8.3
// and Research/CT-CONSULTANT-MODEL-UIUX-DESIGN-01 §8 ("Plane C … is Plane B
// rendered for the client's own users, with … profile-driven capabilities"). A
// consultant-managed client reaches the SAME Organisation surface a direct
// customer uses, but its effective capabilities are bounded by the
// consultant-client relationship's ACCESS PROFILE.
//
// This context is PRESENTATION ONLY — it decides whether an affordance is
// *offered*. The server is the security boundary: api/client_access_guard.py
// enforces the identical ceiling on every organisation-plane write, so hiding a
// control here never grants or withholds access on its own (AGENTS.md §44).
//
// The default is "no client restriction": a direct customer, a consultant
// operating a client, and CarbonTally staff all receive `available: false` and
// `can()` → true, so their surfaces are unchanged.
import React, { createContext, useContext } from 'react';

const UNRESTRICTED = {
  available: false,
  profile: null,
  state: null,
  capabilities: null,
  // Unknown / not-applicable → allowed (historical behaviour).
  can: () => true,
};

export const ClientAccessContext = createContext(UNRESTRICTED);

/** Read the client-access view (unrestricted outside a consultant-managed client). */
export function useClientAccess() {
  return useContext(ClientAccessContext);
}

export function ClientAccessProvider({ value, children }) {
  const view =
    value && value.capabilities
      ? {
          available: true,
          profile: value.profile || null,
          state: value.state || null,
          capabilities: value.capabilities,
          // Fail OPEN in the UI only when the server has not yet told us: an
          // explicit `false` hides the control; anything else keeps it. The
          // backend still denies regardless of what the UI shows.
          can: (op) => value.capabilities[op] !== false,
        }
      : UNRESTRICTED;
  return (
    <ClientAccessContext.Provider value={view}>
      {children}
    </ClientAccessContext.Provider>
  );
}
