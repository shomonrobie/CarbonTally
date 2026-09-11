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
        <p className="ct-page-meta">CarbonTally Ltd · Applies to the public website and the CarbonTally platform · Last updated: 11 September 2026</p>

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
          <li><strong>Platform accounts.</strong> Authorised users of the platform provide an email address, and sign in either with a password or with <strong>Google sign-in</strong> (authentication is provided by Supabase Auth).</li>
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

        <h2>11. Signing in to CarbonTally (authentication)</h2>
        <p>
          Access to the CarbonTally platform is restricted to authorised users. Two sign-in
          methods are supported:
        </p>
        <ul>
          <li>
            <strong>Email and password.</strong> Your email address and password are used to
            authenticate you. Passwords are handled by our authentication provider (Supabase
            Auth); CarbonTally does not store your password in readable form.
          </li>
          <li>
            <strong>Google sign-in (optional).</strong> If you choose Google sign-in, you are
            taken to Google&rsquo;s own sign-in screen. Google authenticates you and returns a
            limited set of account details to CarbonTally &mdash; in practice your email address
            and basic profile information. <strong>CarbonTally never receives your Google
            password.</strong> Your use of Google sign-in is also subject to Google&rsquo;s own
            privacy policy and account settings.
          </li>
        </ul>
        <p>
          Authentication is operated on our behalf by <strong>Supabase</strong> (Supabase Auth),
          which processes account credentials and session tokens for the purpose of signing
          users in. CarbonTally&rsquo;s application data and uploaded documents are stored in
          Supabase infrastructure with access controls and row-level security applied.
        </p>

        <h2>12. Cookies and session technologies</h2>
        <p>
          The site does not use advertising or marketing cookies, and it deploys no third-party
          advertising trackers. To keep authorised users signed in, the site stores a
          server-issued session token in your browser (via <code>localStorage</code>), together
          with the minimum authentication state needed to restore your session after a page
          refresh. Signing out (or the token expiring) removes that state. Because this storage
          is required to provide the sign-in functionality you have requested, it is essential
          to the operation of the platform rather than optional tracking.
        </p>

        <h2>13. Service availability and sign-in interruptions</h2>
        <p>
          From time to time our authentication provider may be temporarily unavailable. When
          that happens you may be unable to sign in for a short period. This does
          <strong>not</strong> mean that your account or your organisation&rsquo;s data has been
          deleted or lost: stored data remains in place and sign-in becomes available again once
          the service recovers. Where this occurs, CarbonTally shows you a branded notice
          explaining that sign-in is temporarily unavailable, rather than a raw technical error.
        </p>
      </div>
    </PageShell>
  );
}
