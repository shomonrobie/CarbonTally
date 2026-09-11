// frontend/src/v3/pe/PEShell.jsx
// V1.2 FINAL — dedicated Processing Entity application shell for the /pe
// surface (PE → /pe → PEShell).
//
// This shell is intentionally NOT the shared V3Layout: it never renders
// Operations, Customer, Consultant or CarbonTally Admin navigation. The only
// destination a PE member needs is the PE application itself ("Work" → /pe),
// plus sign-out. Entity name + frozen role chip come from the server
// (GET /api/v3/pe/me); navigation is UX only — the /api/v3/pe/* endpoints and
// RLS remain the authoritative authorization boundary (defence-in-depth).
//
// Shared D21 primitives/styles are reused (same token classes); this is a
// separate component + markup, not the shared application shell.
import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { supabase } from '../../supabaseClient';
import { getPeMe } from '../api';
import Icon from '../components/ui/Icon';
import Drawer from '../components/ui/Drawer';
import PeNotificationsBell from './PeNotificationsBell';
import '../tokens.css';
import '../v3.css';
import '../components/ui/ui.css';
import './pe.css';

// PE-specific navigation — the PE application surface (all inside PEShell).
const PE_LINKS = [
  { to: '/pe', label: 'Work', icon: 'processing', end: true },
  { to: '/pe/assignments', label: 'Assignments', icon: 'list', end: false },
  { to: '/pe/messages', label: 'Messages', icon: 'messaging', end: false },
];

export default function PEShell({ children }) {
  const navigate = useNavigate();
  const [me, setMe] = useState(null);
  const [contextError, setContextError] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [trayOpen, setTrayOpen] = useState(false);

  useEffect(() => {
    let active = true;
    (async () => {
      try {
        const body = await getPeMe();
        if (!active) return;
        setMe(body);
        setContextError(false);
      } catch (_e) {
        if (!active) return;
        // Fail-closed: render a controlled banner; the route pages surface
        // their own server-scoped errors. Never guess a role/entity here.
        setContextError(true);
      } finally {
        if (active) setLoaded(true);
      }
    })();
    return () => { active = false; };
  }, []);

  const onLogout = async () => {
    await supabase.auth.signOut();
    navigate('/login', { replace: true });
  };

  const linkMarkup = () =>
    PE_LINKS.map((link) => (
      <NavLink
        key={link.to}
        to={link.to}
        end={link.end}
        className={({ isActive }) => `v3-nav-link${isActive ? ' active' : ''}`}
      >
        {link.icon && <Icon name={link.icon} size={15} aria-hidden="true" />}
        {link.label}
      </NavLink>
    ));

  const entityName = me?.entity?.name;
  const roleName = me?.role?.label || me?.role?.role_name || me?.profile?.role_name;

  return (
    <div className="v3-shell pe-shell">
      {contextError && (
        <div
          role="alert"
          className="pe-context-banner"
        >
          <span>We couldn&apos;t load your Processing Entity workspace just now. Please try again.</span>
          <button type="button" onClick={() => window.location.reload()}>
            Retry
          </button>
        </div>
      )}

      <header className="v3-nav pe-nav">
        <button
          type="button"
          className="v3-nav-menu-btn"
          aria-label="Open Processing Entity navigation menu"
          aria-expanded={trayOpen}
          onClick={() => setTrayOpen(true)}
        >
          <Icon name="menu" size={20} aria-hidden="true" />
        </button>

        <div className="v3-nav-brand">
          <span className="v3-nav-logo">CarbonTally</span>
          <span className="v3-nav-tag pe-tag">Processing Entity workspace</span>
        </div>

        <nav className="v3-nav-links" aria-label="Processing Entity navigation">
          {linkMarkup()}
        </nav>

        <div className="v3-nav-context pe-nav-context">
          {entityName && (
            <span className="v3-nav-org" title={entityName}>{entityName}</span>
          )}
          {roleName && <span className="v3-nav-badge pe-role-chip">{roleName}</span>}
          {loaded && <PeNotificationsBell />}
          {loaded && (
            <button className="v3-nav-logout" onClick={onLogout} type="button">
              Sign out
            </button>
          )}
        </div>
      </header>

      {/* Tablet/mobile tray navigation (D20) */}
      <Drawer open={trayOpen} onClose={() => setTrayOpen(false)} title="Processing Entity workspace" side="left">
        <nav className="v3-tray-nav" aria-label="Processing Entity tray navigation">
          {linkMarkup()}
          {entityName && (
            <div className="v3-tray-org">
              <span className="v3-nav-org" title={entityName}>{entityName}</span>
            </div>
          )}
          <div className="v3-tray-actions">
            {roleName && <span className="v3-nav-badge pe-role-chip">{roleName}</span>}
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
  );
}
