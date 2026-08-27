// src/components/AppFooter.jsx — Pre-launch public website footer.
import React from 'react';
import { Link } from 'react-router-dom';

const COLUMNS = [
  {
    title: 'Platform',
    links: [
      { to: '/platform', label: 'Platform overview' },
      { to: '/processing-services', label: 'Processing services' },
      { to: '/consultants', label: 'For consultants' },
      { to: '/pricing', label: 'Pricing' },
      { to: '/glossary', label: 'Glossary' },
    ],
  },
  {
    title: 'Services',
    links: [
      { to: '/services', label: 'Services overview' },
      { to: '/platform', label: 'Evidence & traceability' },
      { to: '/platform', label: 'Reporting' },
      { to: '/processing-services', label: 'Managed processing' },
    ],
  },
  {
    title: 'Company',
    links: [
      { to: '/about', label: 'About CarbonTally' },
      { to: '/contact', label: 'Contact' },
      { to: '/carbon-reduction-plan', label: 'Carbon Reduction Plan' },
    ],
  },
];

export default function AppFooter() {
  return (
    <footer className="ct-footer">
      <div className="ct-container">
        <div className="ct-footer-grid">
          <div className="ct-footer-brand">
            <div className="ct-brand" style={{ color: '#fff' }}>
              <span className="ct-brand-mark" aria-hidden="true">🌱</span>
              <span>CarbonTally</span>
            </div>
            <p>
              Carbon data processing infrastructure: turning messy source data
              into structured, mapped, calculated and traceable emissions data.
            </p>
            <span className="ct-pre-launch">
              <span className="dot" aria-hidden="true" /> Preparing for commercial launch
            </span>
          </div>

          {COLUMNS.map((col) => (
            <div key={col.title}>
              <h4>{col.title}</h4>
              <ul>
                {col.links.map((l) => (
                  <li key={l.label}><Link to={l.to}>{l.label}</Link></li>
                ))}
              </ul>
            </div>
          ))}

          <div>
            <h4>Contact</h4>
            <ul>
              <li><a href="mailto:hello@carbontally.co.uk">hello@carbontally.co.uk</a></li>
              <li><Link to="/contact">Request launch information</Link></li>
            </ul>
          </div>
        </div>

        <div className="ct-footer-bottom">
          <p>© {new Date().getFullYear()} CarbonTally Ltd. All rights reserved.</p>
          <div className="ct-footer-legal">
            <Link to="/privacy">Privacy Policy</Link>
            <Link to="/cookies">Cookie Policy</Link>
            <Link to="/terms">Terms of Service</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}