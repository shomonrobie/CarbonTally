// frontend/src/v3/components/V3Layout.jsx
// CarbonTally V3 application shell — role-aware top navigation (D18) + shared
// page frame.
//
// Roles are detected from real V3 endpoints (org membership, staff profile,
// consultant profile). The nav only shows sections the identity can access,
// the active organisation/client is always visible, and on tablet/mobile the
// nav collapses to a tray drawer (D20). Sign-out uses the existing Supabase
// Auth client.
//
// Security note: this shell is UX navigation only — the backend/RLS remain
// the authoritative boundary (D25). It never grants access.
import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { supabase } from '../../supabaseClient';
import { getMeContext, getClientWorkspaceContext } from '../api';
import { ClientAccessProvider } from '../clientAccess';
import Icon from './ui/Icon';
import Drawer from './ui/Drawer';
import SearchBox from './SearchBox';
import '../tokens.css';
import '../v3.css';
import './ui/ui.css';

// D18 — customer navigation model (R1): Home, Documents, Processing,
// Emissions, Reports, Issues, Billing, Organisation + Messaging + Existing data.
const CUSTOMER_LINKS = [
  { to: '/home', label: 'Home', icon: 'home', end: true },
  { to: '/documents', label: 'Documents', icon: 'documents' },
  { to: '/processing', label: 'Processing', icon: 'processing' },
  // CT-MP-SUB-004 — one added entry in the existing D18 customer model
  // (CT-UX-MP-SUB-003 §8): the customer's OWN Manual Processing service state.
  { to: '/manual-processing', label: 'Manual processing', icon: 'processing' },
  { to: '/review', label: 'Review & approve', icon: 'checkCircle', end: true },
  { to: '/emissions', label: 'Emissions', icon: 'emissions' },
  { to: '/reports', label: 'Reports', icon: 'reports' },
  { to: '/issues', label: 'Issues', icon: 'issues' },
  { to: '/billing', label: 'Billing', icon: 'billing' },
  { to: '/organization', label: 'Organisation', icon: 'organisation' },
  { to: '/messaging', label: 'Messaging', icon: 'messaging' },
  // I6 — the authenticated Insight workspace (PO I6-1/I6-2): one added entry in
  // the existing D18 customer model, not a navigation redesign.
  { to: '/insight', label: 'Insight', icon: 'insight' },
  { to: '/existing-data', label: 'Existing data', icon: 'search' },
  // P17-L — the governed capability truth surface. One added entry in the
  // existing D18 customer model (no navigation redesign): the customer asks
  // "what does CarbonTally support?" here, and "what does my data say?" on
  // Emissions and Reports (`DECISION-03 §8`).
  { to: '/capabilities', label: 'Capabilities', icon: 'list' },
];

export default function V3Layout({ children, navPrefix = '', clientId = null }) {
  const navigate = useNavigate();
  const [org, setOrg] = useState(null);
  const [isStaff, setIsStaff] = useState(false);
  const [isConsultant, setIsConsultant] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [trayOpen, setTrayOpen] = useState(false);
  const [contextError, setContextError] = useState(false);
  const [attempt, setAttempt] = useState(0);
  // CT-CONSULTANT-CLIENT-PLANE-AUTH-REMEDIATION-05 — the presentation-only
  // client-access view (profile/state/capabilities) for a consultant-managed
  // client's own user; null (unrestricted) for a direct customer, consultant
  // and staff. The backend enforces the identical ceiling regardless.
  const [clientAccess, setClientAccess] = useState(null);

  useEffect(() => {
    let active = true;
    // Phase 3 / P1-B — the shell resolves the actor through the single
    // server-authoritative /api/v3/me/context endpoint. A resolution failure
    // renders a controlled error/retry banner and NEVER navigates anyone to
    // onboarding (the old hardcoded navigate('/onboarding') is gone).
    (async () => {
      try {
        const context = await getMeContext();
        if (!active) return;
        const destination = context.destination || context.primary_workspace;
        if (destination === '/onboarding') {
          navigate('/onboarding', { replace: true });
          return;
        }
        // V1.2 FINAL (PEShell) — Processing Entity staff belong to the dedicated
        // PE application (/pe), never the shared shell. Any shared-shell page a
        // PE member opens (e.g. /notifications) redirects to /pe so the PE
        // surface never exposes Operations/Customer/Consultant/Admin nav.
        if (context.actor_type === 'entity_staff') {
          navigate('/pe', { replace: true });
          return;
        }
        if (context.actor_type === 'customer') {
          setOrg(context.organization || null);
        } else if (context.actor_type === 'consultant' && clientId) {
          // PD-1/PD-3 — a consultant-managed client renders as a NORMAL
          // CarbonTally Organisation. Resolve the selected client's
          // organisation so the shared Organisation navigation is available;
          // the backend re-authorises the active consultant-client grant on
          // every request, so this context grants nothing on its own.
          try {
            const clientContext = await getClientWorkspaceContext(clientId);
            const client = clientContext?.client || null;
            setOrg(
              client?.organization_id
                ? {
                  id: client.organization_id,
                  name: clientContext?.organization?.name || client.client_name,
                }
                : null,
            );
          } catch (_e) {
            setOrg(null);
          }
        } else {
          setOrg(null);
        }
        setIsStaff(context.actor_type === 'staff' || context.actor_type === 'entity_staff');
        setIsConsultant(context.actor_type === 'consultant');
        setClientAccess(
          context.actor_type === 'customer' ? (context.client_access || null) : null,
        );
        setContextError(false);
        setLoaded(true);
      } catch (_e) {
        if (!active) return;
        // Fail-closed: stay on the (role-gated, data-protected) surface with a
        // controlled error instead of guessing the actor's workspace.
        setContextError(true);
        setLoaded(true);
      }
    })();
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [attempt, clientId]);

  const onLogout = async () => {
    await supabase.auth.signOut();
    navigate('/login', { replace: true });
  };

  const links = [];
  if (org) {
    // When a consultant is operating a managed client, the SAME Organisation
    // destinations are rendered under the selected client's route prefix (PD-1:
    // same product surface, different actor/authorisation context).
    // PD-6 — Billing is deliberately NOT carried into the client Organisation
    // context: CarbonTally bills consultant FIRMS, so a managed client's billing
    // is not the consultant's billing and must not be offered as if it were.
    CUSTOMER_LINKS
      .filter((link) => !(navPrefix && link.to === '/billing'))
      .forEach((link) => links.push({ ...link, to: `${navPrefix}${link.to}` }));
  }
  if (isConsultant) {
    // CT-CONSULTANT-PLATFORM-CLOSURE-01 §11 — inside a managed client's
    // operating plane (navPrefix set) the ONLY return path to the Consultant
    // Plane is the context bar's single "← Back to Consultant" (ClientOrgShell).
    // The shared nav therefore shows the plain "Consultant" hub entry ONLY on
    // the firm plane; inside the client plane it is removed so there is exactly
    // one consultant return/context affordance and no duplicated hub item. The
    // prior UX-NAV-01A rationale (keep a plain hub entry) is superseded here by
    // the client-plane nav-cleanup decision.
    if (!navPrefix) {
      links.push({
        to: '/consultant',
        label: 'Consultant',
        icon: 'briefcase',
      });
    }
  }
  if (isStaff) links.push({ to: '/ops', label: 'Operations', icon: 'tool' });
  links.push({ to: '/notifications', label: 'Notifications', icon: 'notifications' });

  const navLinkClass = ({ isActive }) => (isActive ? 'v3-nav-link active' : 'v3-nav-link');

  const linkMarkup = () => (
    links.map((link) => (
      <NavLink
        key={link.to}
        to={link.to}
        end={link.end}
        className={navLinkClass}
        onClick={() => setTrayOpen(false)}
      >
        <Icon name={link.icon} size={15} aria-hidden="true" />
        {link.label}
      </NavLink>
    ))
  );

  return (
    <ClientAccessProvider value={clientAccess}>
    <div className="v3-shell">
      {contextError && (
        <div
          role="alert"
          style={{
            padding: '0.75rem 1rem',
            background: '#fef2f2',
            color: '#b91c1c',
            borderBottom: '1px solid #fecaca',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
          }}
        >
          <span>We couldn&apos;t load your workspace just now. Please try again.</span>
          <button
            type="button"
            onClick={() => { setContextError(false); setAttempt((n) => n + 1); }}
            style={{
              background: 'transparent',
              border: '1px solid #b91c1c',
              borderRadius: 6,
              padding: '0.3rem 0.75rem',
              cursor: 'pointer',
            }}
          >
            Retry
          </button>
        </div>
      )}
      <header className="v3-nav">
        <button
          type="button"
          className="v3-nav-menu-btn"
          aria-label="Open navigation menu"
          aria-expanded={trayOpen}
          onClick={() => setTrayOpen(true)}
        >
          <Icon name="menu" size={20} aria-hidden="true" />
        </button>
        <div className="v3-nav-brand">
          <span className="v3-nav-logo">CarbonTally</span>
        </div>
        <nav className="v3-nav-links" aria-label="Primary navigation">
          {linkMarkup()}
          {loaded && links.length === 0 && (
            <span className="v3-nav-link" style={{ cursor: 'default', opacity: 0.7 }}>
              No organisation linked — sign in or contact an administrator.
            </span>
          )}
        </nav>
        <div className="v3-nav-context">
          {org && <SearchBox organizationId={org.id} />}
          {org && (
            <span className="v3-nav-org" title={org.id}>
              {isConsultant && navPrefix ? `Working on: ${org.name}` : org.name}
            </span>
          )}
          {isStaff && <span className="v3-nav-badge">Staff</span>}
          {isConsultant && <span className="v3-nav-badge consultant">Consultant</span>}
          {loaded && (
            <button className="v3-nav-logout" onClick={onLogout} type="button">
              Sign out
            </button>
          )}
        </div>
      </header>

      {/* Tablet/mobile tray navigation (D20) */}
      <Drawer open={trayOpen} onClose={() => setTrayOpen(false)} title="Navigation" side="left">
        <nav className="v3-tray-nav" aria-label="Tray navigation">
          {linkMarkup()}
          {org && (
            <div className="v3-tray-org">
              <span className="v3-nav-org" title={org.id}>{org.name}</span>
            </div>
          )}
          <div className="v3-tray-actions">
            {isStaff && <span className="v3-nav-badge">Staff</span>}
            {isConsultant && <span className="v3-nav-badge consultant">Consultant</span>}
            <button className="v3-nav-logout" onClick={onLogout} type="button">
              Sign out
            </button>
          </div>
        </nav>
      </Drawer>

      <main className="v3-shell-main">{children}</main>
      <footer className="v3-shell-footer">
        © {new Date().getFullYear()} CarbonTally (UK) Ltd. All rights reserved.
      </footer>
    </div>
    </ClientAccessProvider>
  );
}

