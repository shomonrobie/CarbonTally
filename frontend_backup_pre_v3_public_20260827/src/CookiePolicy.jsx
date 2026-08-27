// frontend/src/CookiePolicy.jsx
// Pre-launch cookie policy. Accurate for the current site: no third-party
// advertising/marketing trackers are deployed. The platform uses browser
// localStorage for authentication sessions, which is not a cookie.
import React from 'react';
import PageShell from './public/PageShell';

export default function CookiePolicy() {
  return (
    <PageShell
      title="Cookie Policy — CarbonTally"
      description="How the CarbonTally website uses cookies and browser storage."
    >
      <div className="ct-page">
        <h1>Cookie Policy</h1>
        <p className="ct-page-meta">CarbonTally Ltd · Applies to the public website</p>

        <div className="ct-legal-note">
          This policy describes the cookies and storage the site currently uses. It will
          be updated before launch if analytics or marketing services are added. Review
          by legal counsel is recommended.
        </div>

        <h2>1. What we use</h2>
        <p>
          The CarbonTally website currently deploys no third-party advertising,
          analytics or marketing cookies.
        </p>
        <ul>
          <li>
            <strong>Local storage (not a cookie):</strong> the platform stores your
            authentication session in your browser&apos;s local storage so that
            authorised users can remain signed in. This data stays in your browser and
            is not used for tracking.
          </li>
          <li>
            <strong>Essential cookies:</strong> no essential cookies are set by the
            public website itself at this time.
          </li>
        </ul>

        <h2>2. Managing cookies</h2>
        <p>
          You can clear browser storage and cookies through your browser settings at any
          time. Clearing authentication storage will sign you out of the platform.
        </p>

        <h2>3. Future changes</h2>
        <p>
          If we add analytics, advertising or other cookies, we will update this policy
          and, where required, obtain consent before they are set.
        </p>

        <h2>4. Contact</h2>
        <p>
          Cookie enquiries: email <a href="mailto:hello@carbontally.co.uk">hello@carbontally.co.uk</a>.
        </p>
      </div>
    </PageShell>
  );
}
