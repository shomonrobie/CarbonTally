import React from 'react';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';

export default function PrivacyPolicy() {
  return (
    <div className="policy-page-wrapper">
      <AppHeader />
      
      <div className="policy-page">
        <div className="policy-page-header">
          <h1>Privacy Policy</h1>
          <p className="last-updated">Last updated: {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
        </div>
        
        <div className="policy-content">
          <section>
            <h2>1. Introduction</h2>
            <p>CarbonTally Ltd ("we", "our", "us") is committed to protecting and respecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your personal data in compliance with the UK General Data Protection Regulation (UK GDPR) and the Data Protection Act 2018.</p>
            <p>This policy applies to our website, carbon accounting platform, and any related services (collectively, the "Services").</p>
          </section>

          <section>
            <h2>2. Data Controller Information</h2>
            <p><strong>CarbonTally Ltd</strong> is the data controller for the purposes of UK GDPR.</p>
            <p><strong>Registered Address:</strong> [Your Company Address]<br />
            <strong>Company Number:</strong> [Your Company Number]<br />
            <strong>Email:</strong> dpo@carbontally.com<br />
            <strong>Phone:</strong> [Your Phone Number]</p>
          </section>

          <section>
            <h2>3. Information We Collect</h2>
            <p>We may collect and process the following categories of personal data:</p>
            
            <h3>3.1 Identity and Contact Data</h3>
            <ul>
              <li>Full name, job title, and company name</li>
              <li>Email address, phone number, and postal address</li>
              <li>User credentials and profile information</li>
            </ul>

            <h3>3.2 Emissions and Reporting Data</h3>
            <ul>
              <li>Scope 1, 2, and 3 emissions data</li>
              <li>Utility consumption records (electricity, gas, fuel)</li>
              <li>Business travel and logistics information</li>
              <li>Waste and recycling data</li>
            </ul>

            <h3>3.3 Technical and Usage Data</h3>
            <ul>
              <li>IP address, browser type, and device information</li>
              <li>Operating system and platform details</li>
              <li>Pages visited, time spent, and click patterns</li>
              <li>Cookies and tracking technologies (see our <a href="/cookies">Cookie Policy</a>)</li>
            </ul>

            <h3>3.4 Marketing and Communications Data</h3>
            <ul>
              <li>Your preferences for receiving marketing communications</li>
              <li>Your communication preferences and survey responses</li>
            </ul>
          </section>

          <section>
            <h2>4. Legal Basis for Processing</h2>
            <p>We process your personal data under the following lawful bases under UK GDPR Article 6:</p>
            <ul>
              <li><strong>Consent (Article 6(1)(a)):</strong> Where you have given clear consent for us to process your data for specific purposes (e.g., marketing communications).</li>
              <li><strong>Contract (Article 6(1)(b)):</strong> Where processing is necessary for the performance of a contract with you or to take steps at your request before entering into a contract.</li>
              <li><strong>Legal Obligation (Article 6(1)(c)):</strong> Where processing is necessary for compliance with a legal obligation to which we are subject (e.g., SECR reporting requirements, tax compliance).</li>
              <li><strong>Legitimate Interests (Article 6(1)(f)):</strong> Where processing is necessary for our legitimate business interests, provided these do not override your fundamental rights and freedoms.</li>
            </ul>
          </section>

          <section>
            <h2>5. How We Use Your Data</h2>
            <p>We use your personal data for the following purposes:</p>
            <ul>
              <li><strong>Service Delivery:</strong> To provide, maintain, and improve our carbon accounting platform and generate SECR-compliant reports.</li>
              <li><strong>Account Management:</strong> To create and manage your account, process payments, and provide customer support.</li>
              <li><strong>Communications:</strong> To send you service notifications, updates, and security alerts.</li>
              <li><strong>Compliance:</strong> To comply with UK regulatory requirements, including SECR, HMRC reporting, and environmental regulations.</li>
              <li><strong>Analytics and Improvement:</strong> To analyse usage patterns, improve user experience, and develop new features.</li>
              <li><strong>Marketing:</strong> To send you promotional materials and personalised offers (where you have consented).</li>
            </ul>
          </section>

          <section>
            <h2>6. Data Sharing and Disclosure</h2>
            <p>We may share your personal data with the following categories of recipients:</p>
            <ul>
              <li><strong>Service Providers:</strong> Hosting providers, email delivery services, analytics providers, and payment processors.</li>
              <li><strong>Regulatory Bodies:</strong> HMRC, Environment Agency, and other UK regulators where required by law.</li>
              <li><strong>Professional Advisors:</strong> Accountants, legal counsel, and auditors.</li>
              <li><strong>Business Transfers:</strong> In the event of a merger, acquisition, or sale of assets.</li>
            </ul>
            <p>We never sell your personal data to third parties.</p>
          </section>

          <section>
            <h2>7. Data Security</h2>
            <p>We implement appropriate technical and organisational measures to protect your personal data, including encryption, access controls, and regular security audits.</p>
          </section>

          <section>
            <h2>8. Data Retention</h2>
            <p>We retain your personal data for as long as necessary to fulfil the purposes for which it was collected, including:</p>
            <ul>
              <li><strong>Active Accounts:</strong> Data is retained for the duration of your account plus 6 years to comply with HMRC and SECR requirements.</li>
              <li><strong>Inactive Accounts:</strong> After account closure, we retain data for 6 years for legal and regulatory compliance.</li>
              <li><strong>Marketing Data:</strong> Retained until you withdraw consent or 5 years after last interaction.</li>
            </ul>
          </section>

          <section>
            <h2>9. Your Data Protection Rights</h2>
            <p>Under UK GDPR, you have the following rights:</p>
            <ul>
              <li><strong>Right to Access:</strong> Request a copy of your personal data</li>
              <li><strong>Right to Rectification:</strong> Request correction of inaccurate data</li>
              <li><strong>Right to Erasure:</strong> Request deletion of your data ("right to be forgotten")</li>
              <li><strong>Right to Restrict Processing:</strong> Request restriction of processing</li>
              <li><strong>Right to Data Portability:</strong> Request transfer of your data</li>
              <li><strong>Right to Object:</strong> Object to processing based on legitimate interests</li>
              <li><strong>Right to Withdraw Consent:</strong> Withdraw consent at any time</li>
            </ul>
            <p>To exercise these rights, contact us at <strong>dpo@carbontally.com</strong>.</p>
          </section>

          <section>
            <h2>10. Contact Us</h2>
            <p><strong>Data Protection Officer</strong><br />
            CarbonTally Ltd<br />
            Email: dpo@carbontally.com</p>
            <p>You have the right to lodge a complaint with the UK Information Commissioner's Office (ICO) at <a href="https://ico.org.uk" target="_blank" rel="noopener noreferrer">ico.org.uk</a>.</p>
          </section>
        </div>
      </div>
      
      <AppFooter />
    </div>
  );
}