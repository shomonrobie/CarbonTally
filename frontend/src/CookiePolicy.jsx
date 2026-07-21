import React from 'react';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';

export default function CookiePolicy() {
  return (
    <div className="policy-page-wrapper">
      <AppHeader />
      
      <div className="policy-page">
        <div className="policy-page-header">
          <h1>Cookie Policy</h1>
          <p className="last-updated">Last updated: {new Date().toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' })}</p>
        </div>
        
        <div className="policy-content">
          <section>
            <h2>1. What Are Cookies</h2>
            <p>Cookies are small text files placed on your device when you visit a website. They are widely used to make websites work efficiently, improve user experience, and provide information to site owners.</p>
            <p>CarbonTally uses cookies and similar technologies (such as local storage and tracking pixels) on carbontally.com and within the CarbonTally platform to ensure functionality, analyse usage, and improve our services.</p>
          </section>

          <section>
            <h2>2. Types of Cookies We Use</h2>

            <h3>Strictly Necessary Cookies</h3>
            <p>Essential for the platform to function. These include session cookies for authentication, security tokens, and load-balancing cookies. They cannot be disabled.</p>
            <ul>
              <li><strong>Session ID:</strong> Maintains your logged-in session</li>
              <li><strong>CSRF Token:</strong> Prevents cross-site request forgery attacks</li>
              <li><strong>Cookie Consent:</strong> Records your cookie preferences</li>
            </ul>

            <h3>Analytics Cookies</h3>
            <p>Help us understand how visitors interact with our website by collecting anonymised usage data. We use privacy-focused analytics tools that do not track users across websites or sell data to third parties.</p>
            <ul>
              <li><strong>Google Analytics:</strong> Tracks page views, user journeys, and site performance</li>
              <li><strong>HubSpot Analytics:</strong> Analyses user behaviour and content engagement</li>
            </ul>

            <h3>Functional Cookies</h3>
            <p>Remember your preferences such as language, timezone, and display settings to provide a personalised experience when you return to the platform.</p>
            <ul>
              <li><strong>Language Preference:</strong> Saves your chosen language</li>
              <li><strong>Theme Preference:</strong> Remembers your display settings</li>
              <li><strong>Recent Activity:</strong> Tracks your recent actions for convenience</li>
            </ul>

            <h3>Marketing Cookies</h3>
            <p>Used to deliver relevant advertisements and measure the effectiveness of our marketing campaigns. These are only set with your explicit consent.</p>
            <ul>
              <li><strong>LinkedIn Insight:</strong> Tracks conversions from LinkedIn ads</li>
              <li><strong>Google Ads:</strong> Measures ad campaign effectiveness</li>
            </ul>
          </section>

          <section>
            <h2>3. Cookie Management</h2>
            <p>When you first visit carbontally.com, a cookie consent banner allows you to accept or customise which non-essential cookies you permit. You can change your preferences at any time through the cookie settings link in our website footer.</p>
            <p>You can also control cookies through your browser settings. Most browsers allow you to block or delete cookies. However, blocking strictly necessary cookies may prevent certain features of the platform from working correctly.</p>
            
            <h3>Browser Instructions:</h3>
            <ul>
              <li><strong>Google Chrome:</strong> Settings → Privacy and Security → Cookies and other site data</li>
              <li><strong>Mozilla Firefox:</strong> Options → Privacy & Security → Cookies and Site Data</li>
              <li><strong>Safari:</strong> Preferences → Privacy → Manage Website Data</li>
              <li><strong>Microsoft Edge:</strong> Settings → Privacy, search, and services → Cookies</li>
            </ul>
            <p>For more information about cookies and how to manage them, visit <a href="https://www.allaboutcookies.org" target="_blank" rel="noopener noreferrer">allaboutcookies.org</a>.</p>
          </section>

          <section>
            <h2>4. Third-Party Cookies</h2>
            <p>Some cookies are set by third-party services we use:</p>
            <ul>
              <li><strong>Google Analytics:</strong> <a href="https://policies.google.com/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a></li>
              <li><strong>HubSpot:</strong> <a href="https://legal.hubspot.com/cookie-policy" target="_blank" rel="noopener noreferrer">Cookie Policy</a></li>
              <li><strong>LinkedIn:</strong> <a href="https://www.linkedin.com/legal/cookie-policy" target="_blank" rel="noopener noreferrer">Cookie Policy</a></li>
            </ul>
          </section>

          <section>
            <h2>5. Contact Us</h2>
            <p>If you have questions about our use of cookies, please contact:</p>
            <p>CarbonTally Ltd<br />
            Email: privacy@carbontally.com</p>
          </section>
        </div>
      </div>
      
      <AppFooter />
    </div>
  );
}