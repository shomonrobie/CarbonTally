// RV-2 — DataSecurity is now a PUBLIC page (/data-security).
// Smoke test: renders standalone (anonymous access) and the /privacy link
// resolves correctly.
//
// NOTE: `react-router-dom` is stubbed because the installed
// react-router-dom@7 package cannot be resolved under Jest
// ("Cannot find module 'react-router/dom'") — a PRE-EXISTING dependency
// issue intentionally NOT fixed in this task. Stubbing keeps this suite
// runnable so the RV-2 page behaviour itself is still verified.
import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';

jest.mock('react-router-dom', () => {
  const ReactActual = require('react');
  const Link = ({ to, children, className, ...rest }) =>
    ReactActual.createElement('a', { href: to, className }, children);
  const NavLink = Link;
  const useNavigate = () => jest.fn();
  return { Link, NavLink, useNavigate };
});

import DataSecurity from './DataSecurity';

describe('DataSecurity public page (RV-2)', () => {
  test('renders standalone without authentication', () => {
    render(<DataSecurity />);
    expect(
      screen.getByRole('heading', { level: 1, name: /data security at carbontally/i })
    ).toBeInTheDocument();
  });

  test('privacy link resolves to /privacy', () => {
    render(<DataSecurity />);
    const privacyLink = screen.getByRole('link', { name: /view privacy policy/i });
    expect(privacyLink).toHaveAttribute('href', '/privacy');
  });

  test('contact link resolves to /contact', () => {
    render(<DataSecurity />);
    const contactLink = screen.getByRole('link', { name: /contact carbontally/i });
    expect(contactLink).toHaveAttribute('href', '/contact');
  });
});

