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
import { getConsultantProfile, getOpsMe, resolveV3Organization } from '../api';
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
  { to: '/review', label: 'Review & approve', icon: 'checkCircle', end: true },
  { to: '/emissions', label: 'Emissions', icon: 'emissions' },
  { to: '/reports', label: 'Reports', icon: 'reports' },
  { to: '/issues', label: 'Issues', icon: 'issues' },
  { to: '/billing', label: 'Billing', icon: 'billing' },
  { to: '/organization', label: 'Organisation', icon: 'organisation' },
  { to: '/messaging', label: 'Messaging', icon: 'messaging' },
  { to: '/existing-data', label: 'Existing data', icon: 'search' },
];

export default function V3Layout({ children }) {
  const navigate = useNavigate();
  const [org, setOrg] = useState(null);
  const [isStaff, setIsStaff] = useState(false);
  const [isConsultant, setIsConsultant] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [trayOpen, setTrayOpen] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.allSettled([
      resolveV3Organization(),
      getOpsMe().then(() => true).catch(() => false),
      getConsultantProfile().then(() => true).catch(() => false),
    ]).then(([orgResult, staffResult, consultantResult]) => {
      if (!active) return;
      const org = orgResult.status === 'fulfilled' ? orgResult.value || null : null;
      const staff = staffResult.status === 'fulfilled' && staffResult.value === true;
      const consultant = consultantResult.status === 'fulfilled' && consultantResult.value === true;
      setOrg(org);
      setIsStaff(staff);
      setIsConsultant(consultant);
      setLoaded(true);
      // D35 — an authenticated user with no org / staff / consultant
      // relationship is a brand-new customer: send them to self-service
      // onboarding instead of the legacy empty-state dead end.
      if (!org && !staff && !consultant) {
        navigate('/onboarding', { replace: true });
      }
    });
    return () => { active = false; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const onLogout = async () => {
    await supabase.auth.signOut();
    navigate('/login', { replace: true });
  };

  const links = [];
  if (org) {
    CUSTOMER_LINKS.forEach((link) => links.push({ ...link }));
  }
  if (isConsultant) links.push({ to: '/consultant', label: 'Consultant', icon: 'briefcase' });
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
    <div className="v3-shell">
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
          <span className="v3-nav-tag">V3</span>
        </div>
        <nav className="v3-nav-links" aria-label="V3 navigation">
          {linkMarkup()}
          {loaded && links.length === 0 && (
            <span className="v3-nav-link" style={{ cursor: 'default', opacity: 0.7 }}>
              No organisation linked — sign in or contact an administrator.
            </span>
          )}
        </nav>
        <div className="v3-nav-context">
          {org && <SearchBox organizationId={org.id} />}
          {org && <span className="v3-nav-org" title={org.id}>{org.name}</span>}
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
        <nav className="v3-tray-nav" aria-label="V3 tray navigation">
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
  );
}

