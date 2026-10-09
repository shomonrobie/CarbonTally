// frontend/src/v3/consultant/ClientOrgShell.jsx
// CT-CONSULTANT-ORGANISATION-PARITY-IMPLEMENTATION-01 (PD-1/PD-3/PD-9).
// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01 (UX-01..UX-05) — client OPERATING PLANE.
//
// A consultant-managed client is a NORMAL CarbonTally Organisation: the SAME
// product surface, a different ACTOR and AUTHORISATION CONTEXT. This shell puts
// the selected client's organisation in context, presents WHO the actor is (the
// consultant firm) and WHAT is being operated (the client organisation), gives a
// single always-visible return path to the Consultant Plane, then renders the
// existing customer Organisation pages inside the shared V3Layout under the
// client's route prefix.
//
// CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A (UX-05/AC-07) — the in-workspace
// "Switch client" dropdown is REMOVED. The consultant already selects a client
// through Clients → Open workspace, so re-selecting inside the workspace was a
// second, redundant selector. The URL remains client-specific
// (/consultant/clients/:clientId/*) and the backend re-authorises the grant.
//
// It grants nothing. The client id arrives in the URL; every API call is
// re-authorised server-side against the caller's ACTIVE consultant-client grant,
// so navigating to another client's id yields a controlled denial/empty state
// rather than data (AGENTS.md 14/44).
import React, { useCallback, useEffect, useMemo, useState } from 'react';
import { Link, Navigate, useParams } from 'react-router-dom';
import V3Layout from '../components/V3Layout';
import {
  getClientWorkspaceContext,
  getConsultantProfile,
  listConsultantClients,
  setActiveConsultantClientId,
} from '../api';
import { EmptyState, ErrorState, LoadingState } from '../components/ui/StateViews';
import {
  ConsultantClientProvider,
  clientPortalLabel,
  relationshipLabel,
} from './ConsultantClientContext';
import './consultant.css';

/**
 * `/consultant/clients/:clientId` -> the client's Organisation Home. The selected
 * client is always identified in the URL, so the active context (PD-9) can never
 * be ambiguous.
 */
export function ClientOrgIndex() {
  const { clientId } = useParams();
  return <Navigate to={`/consultant/clients/${clientId}/home`} replace />;
}

function ContextBar({ state }) {
  const { client, organization, firmName } = state;
  const clientName = client?.client_name || organization?.name || 'this client';

  return (
    <div className="v3-client-context" data-testid="client-operating-context">
      <Link className="v3-btn v3-btn-sm" to="/consultant">
        ← Back to Consultant
      </Link>
      <div className="v3-client-context-identity">
        <div className="v3-client-context-actor">
          <span className="v3-client-context-key">Consultant</span>
          <span className="v3-client-context-firm">{firmName || 'Your firm'}</span>
        </div>
        <div className="v3-client-context-subject">
          <span className="v3-client-context-key">Working on</span>
          <span className="v3-client-context-client">{clientName}</span>
          <span className="v3-client-context-rel">{relationshipLabel(client)}</span>
          <span className="v3-client-context-portal">{clientPortalLabel(client)}</span>
        </div>
      </div>
      {/* CT-CONSULTANT-UX-NAVIGATION-REMEDIATION-01A (UX-05/AC-07) — NO
          "Switch client" control here. The consultant picks a client in the
          Consultant Plane (Clients → Open workspace); to change client they take
          the single "← Back to Consultant" path above. This bar DISPLAYS context,
          it does not select it. */}
    </div>
  );
}

export default function ClientOrgShell({ children }) {
  const { clientId } = useParams();
  const [state, setState] = useState({ status: 'loading' });

  // Persist the selected managed client alongside the route param so the shared
  // page components (which resolve their organisation through
  // `resolveV3Organization`) can find it. The route param stays authoritative.
  useEffect(() => {
    setActiveConsultantClientId(clientId || null);
  }, [clientId]);

  const load = useCallback(async () => {
    setState((prev) => ({ ...prev, status: 'loading' }));
    try {
      const context = await getClientWorkspaceContext(clientId);
      // Firm name + authorised client set are presentation context; their failure
      // must not block the (re-authorised) client workspace.
      const [profile, clientList] = await Promise.all([
        getConsultantProfile().catch(() => null),
        listConsultantClients().catch(() => ({ clients: [] })),
      ]);
      const client = context?.client || null;
      if (!client?.organization_id) {
        setState({
          status: 'notfound',
          client: null,
          organization: null,
          firmName: profile?.company_name || null,
          clients: clientList?.clients || [],
        });
        return;
      }
      setState({
        status: 'ready',
        client,
        organization: context.organization || null,
        firmName: profile?.company_name || null,
        clients: clientList?.clients || [],
      });
    } catch (_e) {
      // Generic denial: never reveal whether the client exists (AGENTS.md 21/45).
      setState({ status: 'denied', client: null, organization: null, firmName: null, clients: [] });
    }
  }, [clientId]);

  useEffect(() => { load(); }, [load]);

  const providerValue = useMemo(() => ({
    active: state.status === 'ready',
    clientId,
    client: state.client || null,
    organization: state.organization || null,
    firmName: state.firmName || null,
    clients: state.clients || [],
  }), [state, clientId]);

  let body;
  if (state.status === 'loading') {
    body = <LoadingState label="Loading client workspace…" />;
  } else if (state.status === 'denied') {
    body = (
      <ErrorState
        title="Client not available"
        message="This client organisation is not available. It may not be linked to your firm, or your firm's access to it has changed."
        onRetry={load}
      />
    );
  } else if (state.status === 'notfound') {
    body = (
      <EmptyState title="Client not found">
        This client has no linked organisation. Return to the Consultant Plane and
        choose a client from your portfolio.
      </EmptyState>
    );
  } else {
    body = children;
  }

  return (
    <ConsultantClientProvider value={providerValue}>
      <V3Layout navPrefix={`/consultant/clients/${clientId}`} clientId={clientId}>
        {state.status === 'ready' && <ContextBar state={state} />}
        {body}
      </V3Layout>
    </ConsultantClientProvider>
  );
}
