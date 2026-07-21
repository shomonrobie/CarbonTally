import React from 'react';
import { useNavigate } from 'react-router-dom';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';
import carbonTallyGif from './images/carbon_tally_upload.gif'; // Adjust the path based on your folder structure

export default function LandingPage() {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    navigate('/login');
  };

  return (
    <div className="landing-page">
      <AppHeader />
      
      {/* --- HERO SECTION --- */}
      <section className="hero-section">
        <div className="hero-container">
          <div className="hero-content">
            <div className="badge">Built for UK SECR Compliance</div>
            <h1 className="headline-animated">Carbon Accounting, <span className="highlight">Simplified.</span></h1>
            <p className="hero-description">
              Stop using messy spreadsheets. Automate your Scope 1, 2, and 3 emissions 
              tracking with official UK DEFRA factors. Audit-ready reports in one click.
            </p>
            <div className="hero-buttons">
              <button className="btn-primary btn-gradient" onClick={handleGetStarted}>
                Start Free Trial
              </button>
              <button className="btn-secondary" onClick={handleGetStarted}>
                Log In
              </button>
            </div>
            <p className="hero-subtext">No credit card required. 14-day free trial.</p>
          </div>
          <div className="hero-image">
            {/* Replace the mock-dashboard with your GIF */}
            <img 
              src={carbonTallyGif} 
              alt="CarbonTally Dashboard Preview" 
              className="hero-gif"
              style={{
                width: '100%',
                maxWidth: '600px',
                borderRadius: '12px',
                boxShadow: '0 20px 60px rgba(0,0,0,0.15)',
                border: '1px solid rgba(255,255,255,0.1)'
              }}
            />
          </div>
        </div>
      </section>

      {/* --- FEATURES SECTION --- */}
      <section className="features" id="features">
        <div className="container">
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
        </div>
      </section>

      {/* --- PRICING SECTION --- */}
      <section className="pricing" id="pricing">
        <div className="container">
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
              <button className="btn-outline" onClick={handleGetStarted}>
                Get Started
              </button>
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
              <button className="btn-primary btn-gradient" onClick={handleGetStarted}>
                Start Free Trial
              </button>
            </div>
          </div>
        </div>
      </section>

      <AppFooter />
    </div>
  );
}