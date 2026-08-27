// src/components/AppHeader.jsx — Pre-launch public website header.
// CarbonTally is preparing for commercial launch: the header presents the
// product, leads to the launch/contact page, and offers a discreet sign-in
// for internal / test users. No beta, waitlist or free-trial CTA.
import React, { useState } from 'react';
import { Link, NavLink, useNavigate } from 'react-router-dom';

const NAV_LINKS = [
  { to: '/platform', label: 'Platform' },
  { to: '/services', label: 'Services' },
  { to: '/processing-services', label: 'Processing' },
  { to: '/consultants', label: 'Consultants' },
  { to: '/pricing', label: 'Pricing' },
  { to: '/about', label: 'About' },
];

export default function AppHeader() {
  const navigate = useNavigate();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const close = () => setIsMobileMenuOpen(false);

  return (
    <header className="ct-header">
      <div className="ct-container ct-header-inner">
        <Link to="/" className="ct-brand" onClick={close}>
          <span className="ct-brand-mark" aria-hidden="true">🌱</span>
          <span>CarbonTally</span>
        </Link>

        <button
          className="ct-burger"
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          aria-label={isMobileMenuOpen ? 'Close menu' : 'Open menu'}
          aria-expanded={isMobileMenuOpen}
        >
          <span className="ct-burger-line" />
          <span className="ct-burger-line" />
          <span className="ct-burger-line" />
        </button>

        <nav className={`ct-nav${isMobileMenuOpen ? ' ct-open' : ''}`} aria-label="Main navigation">
          {NAV_LINKS.map((l) => (
            <NavLink key={l.to} to={l.to} onClick={close}>{l.label}</NavLink>
          ))}
          <NavLink to="/contact" className="ct-mobile-cta" onClick={close}>Contact</NavLink>
        </nav>

        <div className="ct-header-actions">
          <span className="ct-pre-launch" title="CarbonTally is preparing for commercial launch">
            <span className="dot" aria-hidden="true" /> Pre-launch
          </span>
          <Link to="/login" className="ct-signin" onClick={close}>Sign in</Link>
          <button
            className="ct-btn ct-btn-primary"
            onClick={() => { close(); navigate('/contact'); }}
          >
            Request launch information
          </button>
        </div>
      </div>
    </header>
  );
}