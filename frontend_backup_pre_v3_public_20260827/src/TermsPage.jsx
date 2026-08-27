// frontend/src/TermsPage.jsx
// Pre-launch terms of service. Accurate for the current state: pre-launch
// website access and authorised user accounts. No billing terms are claimed
// (online payments are not yet available).
import React from 'react';
import PageShell from './public/PageShell';

export default function TermsPage() {
  return (
    <PageShell
      title="Terms of Service — CarbonTally"
      description="Terms of service for the CarbonTally public website and pre-launch platform."
    >
      <div className="ct-page">
        <h1>Terms of Service</h1>
        <p className="ct-page-meta">CarbonTally Ltd · Pre-launch terms</p>

        <div className="ct-legal-note">
          These are pre-launch terms. Commercial terms, including subscription and
          processing agreements, will be provided separately when CarbonTally launches
          commercially. Review by legal counsel is required before launch.
        </div>

        <h2>1. About these terms</h2>
        <p>
          These terms govern your use of the CarbonTally public website
          (&ldquo;the site&rdquo;) and, where you are an authorised user, the CarbonTally
          platform (&ldquo;the platform&rdquo;). By using the site you accept these terms.
        </p>

        <h2>2. Pre-launch status</h2>
        <p>
          CarbonTally is preparing for commercial launch. The platform is available only
          to authorised internal and test users. Public sign-up, subscriptions and online
          payment are not currently offered.
        </p>

        <h2>3. Use of the site</h2>
        <p>
          You may use the site to learn about CarbonTally and contact us. You must not
          use the site in any way that breaches applicable law or interferes with its
          operation.
        </p>

        <h2>4. Authorised users</h2>
        <p>
          Access to the platform is granted at CarbonTally&apos;s discretion. Authorised
          users must keep their credentials confidential and are responsible for activity
          under their account. Accounts may be suspended or terminated where access is no
          longer appropriate.
        </p>

        <h2>5. No warranty; availability</h2>
        <p>
          The site and platform are provided &ldquo;as is&rdquo; during the pre-launch
          period. Features described on the site are subject to change and may be
          withdrawn, delayed or replaced.
        </p>

        <h2>6. Intellectual property</h2>
        <p>
          The site, platform and their content are owned by or licensed to CarbonTally
          Ltd. You may not reproduce, copy or redistribute them without permission,
          except as permitted by law.
        </p>

        <h2>7. Liability</h2>
        <p>
          To the extent permitted by law, CarbonTally Ltd is not liable for indirect or
          consequential losses arising from use of the pre-launch site or platform.
          Nothing in these terms limits liability that cannot be limited by law.
        </p>

        <h2>8. Changes and contact</h2>
        <p>
          We may update these terms from time to time. Questions: email{' '}
          <a href="mailto:hello@carbontally.co.uk">hello@carbontally.co.uk</a>.
        </p>
      </div>
    </PageShell>
  );
}
