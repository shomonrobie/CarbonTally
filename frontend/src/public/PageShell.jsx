// frontend/src/public/PageShell.jsx
// Shared pre-launch public page shell: launch banner + header + page content
// + footer. Sets the document title and meta description for the page (SPA
// client-side SEO; the static index.html provides the site-level baseline).
import React, { useEffect } from 'react';
import AppHeader from '../components/AppHeader';
import AppFooter from '../components/AppFooter';
import './public-site.css';

const SITE_URL = 'https://carbontally.co.uk';

export function setPageMeta(title, description) {
  if (title) document.title = title;
  const meta = document.querySelector('meta[name="description"]');
  if (meta && description) meta.setAttribute('content', description);
}

export default function PageShell({ title, description, children }) {
  useEffect(() => {
    setPageMeta(title, description);
  }, [title, description]);

  return (
    <div className="ct-site">
      <div className="ct-launch-banner">
        CarbonTally is preparing for commercial launch.{' '}
        <a href="/contact">Request launch information →</a>
      </div>
      <AppHeader />
      <main className="ct-main">{children}</main>
      <AppFooter />
      <CanonicalLink />
    </div>
  );
}

// Keeps the canonical URL in sync with the current route. Updates the
// static <link> from index.html in place so there is never more than one.
function CanonicalLink() {
  useEffect(() => {
    const href = `${SITE_URL}${window.location.pathname}`;
    let link = document.querySelector('link[rel="canonical"]');
    if (!link) {
      link = document.createElement('link');
      link.rel = 'canonical';
      document.head.appendChild(link);
    }
    link.setAttribute('href', href);
  }, []);
  return null;
}
