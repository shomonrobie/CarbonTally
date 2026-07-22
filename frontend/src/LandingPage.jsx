// src/LandingPage.js - Fixed version

import React from 'react';
import { useNavigate } from 'react-router-dom';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';
import carbonTallyGif from './images/carbon_tally_ui_upload.png'; // Adjust the path based on your folder structure

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
            <div className="landing-badge">Built for UK SECR Compliance</div>
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
            <img 
              src={carbonTallyGif} 
              alt="CarbonTally Dashboard Preview" 
              className="hero-gif"
            />
          </div>
        </div>
      </section>

            {/* --- FEATURES SECTION --- */}
      <section className="features" id="features">
        <div className="container">
          <h2 className="fade-in-up">Everything you need for compliant, stress-free reporting</h2>
          <p className="section-subtitle fade-in-up delay-1">
            From messy invoices to audit-ready global reports. We handle the heavy lifting.
          </p>
          
          <div className="feature-grid">
            <div className="feature-card fade-in-up delay-2">
              <div className="icon">🤖</div>
              <h3>AI-Powered Document Extraction</h3>
              <p>Upload messy PDFs, images, or CSVs. Our AI auto-extracts consumption data, assets, and dates, applying the correct DEFRA factors instantly.</p>
            </div>
            
            <div className="feature-card fade-in-up delay-3">
              <div className="icon">📦</div>
              <h3>Enterprise Bulk Upload</h3>
              <p>Drop up to 50 utility bills or fuel invoices at once. Complex documents are intelligently queued for expert manual verification within 24 hours.</p>
            </div>
            
            <div className="feature-card fade-in-up delay-4">
              <div className="icon">🌍</div>
              <h3>Comprehensive Scope 1, 2 & 3</h3>
              <p>Track emissions across all facilities and assets. From company vehicles and natural gas to business travel, flights, and waste management.</p>
            </div>
            
            <div className="feature-card fade-in-up delay-5">
              <div className="icon">🇬🇧</div>
              <h3>UK SECR Automation</h3>
              <p>Generate beautiful, branded, audit-ready PDF reports with a single click. Includes executive summaries, scope breakdowns, and official compliance statements.</p>
            </div>
            
            <div className="feature-card fade-in-up delay-6">
              <div className="icon">EU</div>
              <h3>EU CSRD & ESRS E1</h3>
              <p>Full compliance with European Sustainability Reporting Standards. Double materiality assessments and granular GHG Protocol mapping included.</p>
            </div>
            
            <div className="feature-card fade-in-up delay-7">
              <div className="icon">📊</div>
              <h3>Big 4 Auditor Excel Exports</h3>
              <p>Export your granular GHG inventory in the exact multi-tab format required by auditors. Features automatic GHG Protocol Scope 3 category mapping.</p>
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