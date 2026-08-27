import React from 'react';
import { Link } from 'react-router-dom';

export default function TermsPage() {
  return (
    <div className="policy-page">
      <div className="policy-page-header">
        <Link to="/" className="back-to-home">← Back to CarbonTally</Link>
        <h1>Terms of Service</h1>
        <p className="last-updated">Last updated: {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
      </div>
      
      <div className="policy-content">
        <section>
          <h2>1. Acceptance of Terms</h2>
          <p>By using CarbonTally's services, you agree to be bound by these Terms of Service. If you do not agree, please do not use our services.</p>
        </section>

        <section>
          <h2>2. Description of Service</h2>
          <p>CarbonTally provides carbon accounting software for UK businesses to track Scope 1, 2, and 3 emissions and generate SECR-compliant reports.</p>
        </section>

        <section>
          <h2>3. User Accounts</h2>
          <p>You are responsible for maintaining the confidentiality of your account credentials and for all activities that occur under your account.</p>
        </section>

        <section>
          <h2>4. Data Privacy</h2>
          <p>Your use of our services is governed by our <Link to="/privacy">Privacy Policy</Link> and <Link to="/cookies">Cookie Policy</Link>.</p>
        </section>

        <section>
          <h2>5. Intellectual Property</h2>
          <p>All content, features, and functionality of CarbonTally are owned by CarbonTally Ltd and are protected by intellectual property laws.</p>
        </section>

        <section>
          <h2>6. Limitation of Liability</h2>
          <p>CarbonTally provides its services "as is" and makes no warranties regarding accuracy or reliability. We are not liable for any damages arising from use of our services.</p>
        </section>

        <section>
          <h2>7. Governing Law</h2>
          <p>These terms are governed by the laws of England and Wales.</p>
        </section>

        <section>
          <h2>8. Contact</h2>
          <p>For questions about these Terms, contact us at: legal@carbontally.com</p>
        </section>
      </div>
    </div>
  );
}