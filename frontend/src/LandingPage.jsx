import React from 'react';

export default function LandingPage({ onGetStarted }) {
  return (
    <div className="landing-page">
      {/* --- HERO SECTION --- */}
      <header className="hero">
        <div className="hero-content">
          <div className="badge">🇬🇧 Built for UK SECR Compliance</div>
          <h1>Carbon Accounting, <span className="highlight">Simplified.</span></h1>
          <p>
            Stop using messy spreadsheets. Automate your Scope 1, 2, and 3 emissions 
            tracking with official UK DEFRA factors. Audit-ready reports in one click.
          </p>
          <div className="hero-buttons">
            <button className="btn-primary" onClick={onGetStarted}>Start Free Trial</button>
            <button className="btn-secondary" onClick={onGetStarted}>Log In</button>
          </div>
          <p className="hero-subtext">No credit card required. 14-day free trial.</p>
        </div>
        <div className="hero-image">
          {/* Placeholder for a dashboard screenshot */}
          <div className="mock-dashboard">
            <div className="mock-header">
              <div className="mock-dot red"></div>
              <div className="mock-dot yellow"></div>
              <div className="mock-dot green"></div>
            </div>
            <div className="mock-body">
              <div className="mock-chart"></div>
              <div className="mock-table">
                <div className="mock-row"></div>
                <div className="mock-row"></div>
                <div className="mock-row"></div>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* --- FEATURES SECTION --- */}
      <section className="features">
        <h2>Everything you need for compliant reporting</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <div className="icon">⛽</div>
            <h3>Scope 1: Fuel & Transport</h3>
            <p>Upload messy fuel card CSVs. We auto-map vehicles, calculate litres, and apply the correct DEFRA factors.</p>
          </div>
          <div className="feature-card">
            <div className="icon">⚡</div>
            <h3>Scope 2: Utilities</h3>
            <p>Track electricity and natural gas consumption across all your facilities in kWh, with live emissions math.</p>
          </div>
          <div className="feature-card">
            <div className="icon">🌱</div>
            <h3>Scope 3: Travel & Waste</h3>
            <p>Log business flights, rail travel, hotel stays, and waste manifests. (Available on Pro tier).</p>
          </div>
          <div className="feature-card">
            <div className="icon">📊</div>
            <h3>SECR-Ready Exports</h3>
            <p>Generate audit-ready Excel reports formatted specifically for UK Streamlined Energy and Carbon Reporting.</p>
          </div>
        </div>
      </section>

      {/* --- PRICING SECTION --- */}
      <section className="pricing">
        <h2>Simple, transparent pricing</h2>
        <div className="pricing-grid">
          <div className="pricing-card">
            <h3>Starter</h3>
            <div className="price">£0<span>/month</span></div>
            <ul>
              <li>✅ Scope 1 & Scope 2 tracking</li>
              <li>✅ Up to 5 assets/facilities</li>
              <li>✅ Basic CSV uploads</li>
              <li>✅ Email support</li>
            </ul>
            <button className="btn-outline" onClick={onGetStarted}>Get Started</button>
          </div>
          <div className="pricing-card featured">
            <div className="popular-badge">Most Popular</div>
            <h3>Pro</h3>
            <div className="price">£49<span>/month</span></div>
            <ul>
              <li>✅ <strong>Everything in Starter, plus:</strong></li>
              <li>✅ Scope 3 (Travel & Waste)</li>
              <li>✅ Unlimited assets/facilities</li>
              <li>✅ SECR Excel Export</li>
              <li>✅ Team member invites</li>
            </ul>
            <button className="btn-primary" onClick={onGetStarted}>Start Free Trial</button>
          </div>
        </div>
      </section>

      {/* --- FOOTER --- */}
      <footer className="footer">
        <div className="footer-content">
          <div className="footer-brand">
            <h3>CarbonTally</h3>
            <p>Simplified carbon accounting for UK businesses.</p>
          </div>
          <div className="footer-links">
            <a href="#features">Features</a>
            <a href="#pricing">Pricing</a>
            <a href="#" onClick={(e) => { e.preventDefault(); onGetStarted(); }}>Log In</a>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© {new Date().getFullYear()} CarbonTally Ltd. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}