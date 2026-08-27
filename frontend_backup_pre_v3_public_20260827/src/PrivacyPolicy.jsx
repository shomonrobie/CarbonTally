// frontend/src/PrivacyPolicy.jsx
// Pre-launch privacy policy. No placeholders, no unsupported analytics
// claims. Content is accurate for the current site and should be reviewed
// by legal counsel before commercial launch.
import React from 'react';
import PageShell from './public/PageShell';

export default function PrivacyPolicy() {
  return (
    <PageShell
      title="Privacy Policy — CarbonTally"
      description="How CarbonTally handles personal data across the public website and the platform."
    >
      <div className="ct-page">
        <h1>Privacy Policy</h1>
        <p className="ct-page-meta">CarbonTally Ltd · Applies to the public website and the CarbonTally platform</p>

        <div className="ct-legal-note">
          This policy reflects CarbonTally&apos;s current pre-launch state. It will be
          reviewed and updated by legal counsel before commercial launch.
        </div>

        <h2>1. Who we are</h2>
        <p>
          CarbonTally Ltd provides the CarbonTally carbon data processing and accounting
          platform. Where this policy says &ldquo;we&rdquo;, &ldquo;us&rdquo; or
          &ldquo;our&rdquo;, it means CarbonTally Ltd.
        </p>

        <h2>2. What this policy covers</h2>
        <p>
          This policy explains how personal data is collected and used when you visit the
          public website (the &ldquo;site&rdquo;) or use the platform as an authorised
          user.
        </p>

        <h2>3. Information you provide to us</h2>
        <ul>
          <li><strong>Contact correspondence.</strong> If you email us (for example, to request launch information), we use your email address and the contents of your message to respond to you.</li>
          <li><strong>Platform accounts.</strong> Authorised users of the platform provide an email address and password (authentication is provided by Supabase Auth).</li>
          <li><strong>Organisation data.</strong> Authorised users may provide organisation details and upload source documents containing data relating to their business activities.</li>
        </ul>

        <h2>4. Information we collect automatically</h2>
        <p>
          The site stores authentication session details in your browser (via
          localStorage) so that authorised users can remain signed in. The site currently
          deploys no third-party advertising or marketing trackers.
        </p>

        <h2>5. How we use information</h2>
        <ul>
          <li>To respond to enquiries and provide launch information.</li>
          <li>To provide, secure and improve the platform for authorised users.</li>
          <li>To comply with legal obligations.</li>
        </ul>

        <h2>6. Legal basis (UK GDPR)</h2>
        <p>
          We process personal data on the basis of contract (where you are an authorised
          platform user), legitimate interests (operating and securing the service), and
          legal obligation. Consent is used where required and can be withdrawn at any
          time.
        </p>

        <h2>7. Sharing</h2>
        <p>
          We do not sell personal data. Personal data is shared only with service
          providers who help operate the platform (for example, hosting and email
          infrastructure), under appropriate safeguards, and where required by law.
        </p>

        <h2>8. Security and retention</h2>
        <p>
          Platform data is protected by access controls, row-level security and private,
          org-scoped document storage. We retain personal data only as long as necessary
          for the purposes described above or as required by law.
        </p>

        <h2>9. Your rights</h2>
        <p>
          You may request access to, correction of, or deletion of your personal data, and
          may object to or restrict certain processing. To exercise these rights, contact
          us at the address below.
        </p>

        <h2>10. Contact</h2>
        <p>
          Privacy enquiries: email <a href="mailto:hello@carbontally.co.uk">hello@carbontally.co.uk</a>.
        </p>
      </div>
    </PageShell>
  );
}
