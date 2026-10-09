// frontend/src/v3/consultant/ConsultantClientContext.jsx
// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 (UX-01..UX-05, AC-03/AC-04/AC-07).
//
// The CONSULTANT CLIENT OPERATING PLANE context.
//
// A consultant firm is the ACTOR; a managed client organisation is the SUBJECT
// being operated. When the consultant enters /consultant/clients/:clientId/* the
// same authenticated consultant session continues — the consultant does NOT
// become a member of the client organisation (AGENTS.md §29, product model §1).
//
// This module carries that operating context to every page rendered inside the
// client plane (including shared customer pages such as Manual Processing), so
// the plane can present the actor/subject relationship consistently and adapt its
// copy without guessing from the URL.
//
// It grants NOTHING. The client id in the URL is re-authorised server-side on
// every request (PD-3/PD-7); this is presentation context only, never an
// authorisation and never a tenancy boundary (AGENTS.md §14/§44).
import React, { createContext, useContext } from 'react';

const EMPTY_CONTEXT = {
  // `false` in the direct-customer plane and in the consultant hub. Consumers use
  // this to decide whether they are operating a client FOR a consultant firm.
  active: false,
  clientId: null,
  client: null,
  organization: null,
  firmName: null,
  // Only the clients the current consultant actor is authorised to operate (the
  // server returns the active-grant set from /me/clients). Never used as an
  // authorisation — selecting one re-enters the plane, where the backend re-checks.
  clients: [],
  switchClient: null,
};

export const ConsultantClientContext = createContext(EMPTY_CONTEXT);

/** Read the consultant client operating-plane context (no-op outside the plane). */
export function useConsultantClientContext() {
  return useContext(ConsultantClientContext);
}

export function ConsultantClientProvider({ value, children }) {
  return (
    <ConsultantClientContext.Provider value={{ ...EMPTY_CONTEXT, ...value }}>
      {children}
    </ConsultantClientContext.Provider>
  );
}

// Relationship label for a managed client, derived from the REAL relationship
// fields the backend returns on consultant_clients (no invented state):
//   status             : active | suspended | ended | terminated | pending
//   client_access_profile : off | read_only | collaborative | managed
//   retained_read_only : bool (PO-10 retention)
// It states the consultant's own relationship first, then the CLIENT PORTAL
// access separately, because the two are independent (an OFF portal does not
// stop the consultant operating — task §7).
const ACCESS_PROFILE_LABEL = {
  managed: 'Managed',
  collaborative: 'Collaborative',
  read_only: 'Read-only',
  off: 'Off',
};

export function relationshipLabel(client) {
  if (!client) return '';
  const status = client.status || 'active';
  if (status === 'ended' || status === 'terminated') {
    return client.retained_read_only ? 'Retained · Read-only' : 'Relationship ended';
  }
  if (status === 'suspended') return 'Consultant-managed · Suspended';
  if (status === 'pending') return 'Consultant-managed · Pending';
  return 'Consultant-managed · Active';
}

/** Client-portal access label, shown SEPARATELY from consultant operational access. */
export function clientPortalLabel(client) {
  if (!client) return '';
  const profile = client.client_access_profile || 'off';
  if ((client.status || 'active') === 'ended' || client.status === 'terminated') {
    return client.retained_read_only ? 'Retained read-only access' : 'No portal access';
  }
  return profile === 'off'
    ? 'Client portal: Off'
    : `Client portal: ${ACCESS_PROFILE_LABEL[profile] || 'On'}`;
}

/**
 * One-sentence explanation of an unusual relationship state, so the consultant is
 * never left guessing (task §7 OFF client, §8 retained client). Returns '' when no
 * explanation is warranted (the common active/managed case). It states only what
 * the real relationship fields say — no invented capability.
 */
export function clientPortalNote(client) {
  if (!client) return '';
  const status = client.status || 'active';
  const profile = client.client_access_profile || 'off';
  if (status === 'ended' || status === 'terminated') {
    return client.retained_read_only
      ? 'Historical carbon evidence remains available according to the retention policy.'
      : '';
  }
  if (profile === 'off') {
    return 'The client portal is off — your firm can still operate this organisation on the client’s behalf.';
  }
  return '';
}
