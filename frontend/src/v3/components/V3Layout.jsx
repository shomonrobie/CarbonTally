// frontend/src/v3/components/V3Layout.jsx
// CarbonTally V3 application shell — role-aware navigation + shared page frame.
// Roles are detected from real V3 endpoints (org membership, staff profile,
// consultant profile). The nav only shows sections the identity can access, and
// the active organisation/client is always visible. Sign-out uses the existing
// Supabase Auth client.
import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { supabase } from '../../supabaseClient';
import { getConsultantProfile, getOpsMe, resolveV3Organization } from '../api';
import '../v3.css';

export default function V3Layout({ children }) {
  const navigate = useNavigate();
  const [org, setOrg] = useState(null);
  const [isStaff, setIsStaff] = useState(false);
  const [isConsultant, setIsConsultant] = useState(false);
  const [loaded, setLoaded] = useState(false);

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
    links.push({ to: '/home', label: 'Dashboard', end: true });
    links.push({ to: '/emissions', label: 'Emissions' });
    links.push({ to: '/documents', label: 'Documents' });
    links.push({ to: '/processing', label: 'Processing' });
    links.push({ to: '/issues', label: 'Issues' });
    links.push({ to: '/reports', label: 'Reports' });
    links.push({ to: '/messaging', label: 'Messages' });
    links.push({ to: '/existing-data', label: 'Existing data' });
    links.push({ to: '/billing', label: 'Billing' });
    links.push({ to: '/organization', label: 'Organization' });
  }
  if (isConsultant) links.push({ to: '/consultant', label: 'Consultant' });
  if (isStaff) links.push({ to: '/ops', label: 'Operations' });
  links.push({ to: '/notifications', label: 'Notifications' });

  return (
    <div className="v3-shell">
      <header className="v3-nav">
        <div className="v3-nav-brand">
          <span className="v3-nav-logo">CarbonTally</span>
          <span className="v3-nav-tag">V3</span>
        </div>
        <nav className="v3-nav-links" aria-label="V3 navigation">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              end={link.end}
              className={({ isActive }) => (isActive ? 'v3-nav-link active' : 'v3-nav-link')}
            >
              {link.label}
            </NavLink>
          ))}
          {loaded && links.length === 0 && (
            <span className="v3-nav-link" style={{ cursor: 'default', opacity: 0.7 }}>
              No organisation linked — sign in or contact an administrator.
            </span>
          )}
        </nav>
        <div className="v3-nav-context">
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
      <main className="v3-shell-main">{children}</main>
      <footer className="v3-shell-footer">
        © {new Date().getFullYear()} CarbonTally (UK) Ltd. All rights reserved.
      </footer>
    </div>
  );
}
