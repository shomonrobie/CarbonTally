import React from 'react';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';

export default function TermsPage() {
  return (
    <div className="policy-page-wrapper">
      <AppHeader />
      
      <div className="policy-page">
        <div className="policy-page-header">
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
            <p>Your use of our services is governed by our <a href="/privacy">Privacy Policy</a> and <a href="/cookies">Cookie Policy</a>.</p>
          </section>

          <section>
            <h2>5. Intellectual Property</h2>
            <p>All content, features, and functionality of CarbonTally are owned by CarbonTally Ltd and are protected by intellectual property laws.</p>
          </section>

          <section>
            <h2>6. User Obligations</h2>
            <p>You agree to:</p>
            <ul>
              <li>Provide accurate and complete information</li>
              <li>Use the service only for lawful purposes</li>
              <li>Not attempt to gain unauthorized access to the system</li>
              <li>Not upload malicious code or harmful content</li>
            </ul>
          </section>

          <section>
            <h2>7. Payment Terms</h2>
            <p>Subscription fees are billed in advance on a monthly or annual basis. All fees are non-refundable except as required by law.</p>
          </section>

          <section>
            <h2>8. Termination</h2>
            <p>Either party may terminate the agreement with 30 days' written notice. We may suspend or terminate your account immediately for violation of these terms.</p>
          </section>

          <section>
            <h2>9. Limitation of Liability</h2>
            <p>CarbonTally provides its services "as is" and makes no warranties regarding accuracy or reliability. To the maximum extent permitted by law, we are not liable for any indirect, incidental, or consequential damages.</p>
          </section>

          <section>
            <h2>10. Governing Law</h2>
            <p>These terms are governed by the laws of England and Wales. Any disputes shall be resolved in the courts of London, UK.</p>
          </section>

          <section>
            <h2>11. Contact</h2>
            <p>For questions about these Terms, contact us at:</p>
            <p>CarbonTally Ltd<br />
            Email: legal@carbontally.com</p>
          </section>
        </div>
      </div>
      
      <AppFooter />
    </div>
  );
}