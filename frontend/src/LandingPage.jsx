// src/LandingPage.jsx - Enhanced with traceability messaging (NO SVG imports)
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';
import CarbonTallyDemo from './components/CarbonTallyDemo';
import './css/lp2.css';

export default function LandingPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [showWaitlistModal, setShowWaitlistModal] = useState(false);

  // Animation observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('animate-in');
          }
        });
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );

    document.querySelectorAll('.animate-on-scroll').forEach((el) => {
      observer.observe(el);
    });

    return () => observer.disconnect();
  }, []);

  const handleJoinWaitlist = (e) => {
    e?.preventDefault();
    setShowWaitlistModal(true);
  };

  const handleSubmitEmail = async (e) => {
    e.preventDefault();
    
    if (!email || !email.includes('@')) {
      setError('Please enter a valid email address');
      return;
    }

    setIsSubmitting(true);
    setError('');

    // Simulate API call for demo
    setTimeout(() => {
      setIsSubmitted(true);
      setEmail('');
      setFullName('');
      setTimeout(() => {
        setShowWaitlistModal(false);
        setIsSubmitted(false);
      }, 2000);
      setIsSubmitting(false);
    }, 1500);
  };

  const handleGetStarted = () => {
    setShowWaitlistModal(true);
  };

  return (
    <div className="landing-page">
      <AppHeader showAuthButtons={true} isBetaMode={true} />

      {/* --- BETA BANNER --- */}
      <div className="beta-banner">
        <div className="beta-content">
          <span className="beta-icon">🧪</span>
          <span className="beta-text">
            <strong>Limited Beta Access</strong> — All features are ready! 
            <span className="beta-highlight">Join our beta program</span>
          </span>
          <button className="beta-btn" onClick={handleJoinWaitlist}>
            Request Beta Access →
          </button>
        </div>
      </div>

      {/* --- HERO SECTION --- */}
      <section className="hero-section" id="hero">
        <div className="hero-container">
          <div className="hero-content">
            <div className="landing-badge animate-on-scroll">
              🧪 Limited Beta — All Features Available
            </div>
            <h1 className="headline-animated animate-on-scroll">
              Turn messy carbon data into <br />
              <span className="gradient-text">traceable emissions</span>
            </h1>
            <p className="hero-description animate-on-scroll">
              CarbonTally transforms invoices, PDFs, spreadsheets, CSVs and other source data 
              into structured, calculated carbon data — with evidence linking each result back to its source.
            </p>
            
            <div className="hero-cta animate-on-scroll">
              <button className="btn-primary btn-large" onClick={handleGetStarted}>
                Start processing →
              </button>
              <button className="btn-secondary btn-large" onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}>
                Talk to us
              </button>
            </div>

            <div className="trust-indicators animate-on-scroll">
              <span>✓ Traceable Evidence</span>
              <span>✓ Audit-Ready Reports</span>
              <span>✓ UK SECR & EU CSRD</span>
            </div>
          </div>
          
          <div className="hero-visual">
            <CarbonTallyDemo />
          </div>
        </div>
      </section>

      {/* --- TRACEABILITY SECTION --- */}
      <section className="traceability-section" id="traceability">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <span className="section-badge">🔍 Full Traceability</span>
            <h2>Know where every number came from</h2>
            <p className="section-subtitle">
              Every emission has a story. CarbonTally keeps the evidence.
            </p>
          </div>

          <div className="traceability-content">
            <div className="traceability-text animate-on-scroll">
              <p className="lead-text">
                A carbon number is only useful when you can explain it.
              </p>
              <p>
                With CarbonTally, customers can trace an emission from the final CO₂e result back through:
              </p>
              <ul className="trace-steps">
                <li>
                  <span className="step-number">1</span>
                  <div className="step-content">
                    <strong>Calculation</strong>
                    <span className="step-example">500 kWh × 0.00028 kg CO₂e/kWh</span>
                  </div>
                </li>
                <li>
                  <span className="step-number">2</span>
                  <div className="step-content">
                    <strong>Emission factor</strong>
                    <span className="step-example">DEFRA 2025 — 0.00028 kg CO₂e/kWh</span>
                  </div>
                </li>
                <li>
                  <span className="step-number">3</span>
                  <div className="step-content">
                    <strong>Mapped activity</strong>
                    <span className="step-example">Electricity — 500 kWh</span>
                  </div>
                </li>
                <li>
                  <span className="step-number">4</span>
                  <div className="step-content">
                    <strong>Source document</strong>
                    <span className="step-example">INV-10482.pdf</span>
                  </div>
                </li>
              </ul>
              
              <div className="trace-result">
                <span className="result-label">Result:</span>
                <span className="result-value">0.140 kg CO₂e</span>
              </div>

              <button className="btn-outline" onClick={() => document.getElementById('evidence').scrollIntoView({ behavior: 'smooth' })}>
                See how evidence traceability works →
              </button>
            </div>

            <div className="traceability-visual animate-on-scroll">
              <div className="trace-diagram">
                <div className="trace-node">
                  <span className="trace-icon">📄</span>
                  <span>Your document</span>
                  <span className="trace-arrow">↓</span>
                </div>
                <div className="trace-node">
                  <span className="trace-icon">🔍</span>
                  <span>Extracted data</span>
                  <span className="trace-arrow">↓</span>
                </div>
                <div className="trace-node">
                  <span className="trace-icon">🗺️</span>
                  <span>Mapped activity</span>
                  <span className="trace-arrow">↓</span>
                </div>
                <div className="trace-node">
                  <span className="trace-icon">⚡</span>
                  <span>Emission factor</span>
                  <span className="trace-arrow">↓</span>
                </div>
                <div className="trace-node">
                  <span className="trace-icon">📊</span>
                  <span>Calculation</span>
                  <span className="trace-arrow">↓</span>
                </div>
                <div className="trace-node trace-final">
                  <span className="trace-icon">✅</span>
                  <span>CO₂e result</span>
                  <span className="trace-badge">Traceable</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- SOURCE CONNECTION SECTION --- */}
      <section className="source-connection-section" id="source-connection">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <span className="section-badge">🔗 Stay Connected</span>
            <h2>Your source data stays connected</h2>
            <p className="section-subtitle">
              Don't lose the connection between carbon data and the documents behind it.
            </p>
          </div>

          <div className="connection-content">
            <div className="connection-example animate-on-scroll">
              <div className="connection-flow">
                <div className="flow-step">
                  <span className="flow-icon">📄</span>
                  <span>Upload a document</span>
                </div>
                <div className="flow-arrow">↓</div>
                <div className="flow-step">
                  <span className="flow-icon">🔎</span>
                  <span>Extracted data</span>
                </div>
                <div className="flow-arrow">↓</div>
                <div className="flow-step">
                  <span className="flow-icon">🗺️</span>
                  <span>Mapped activity</span>
                </div>
                <div className="flow-arrow">↓</div>
                <div className="flow-step">
                  <span className="flow-icon">⚡</span>
                  <span>Emission factor</span>
                </div>
                <div className="flow-arrow">↓</div>
                <div className="flow-step">
                  <span className="flow-icon">📊</span>
                  <span>Calculation</span>
                </div>
                <div className="flow-arrow">↓</div>
                <div className="flow-step flow-result">
                  <span className="flow-icon">✅</span>
                  <span>CO₂e result</span>
                </div>
              </div>

              <div className="connection-bidirectional">
                <p>← You can work backwards too →</p>
              </div>
            </div>

            <div className="connection-text animate-on-scroll">
              <div className="connection-quote">
                <blockquote>
                  "Where did this emission come from?"
                </blockquote>
                <p>— You'll always have an answer.</p>
              </div>
              
              <div className="connection-benefits">
                <div className="benefit-item">
                  <span className="benefit-icon">✓</span>
                  <span>Trace every emission back to its source</span>
                </div>
                <div className="benefit-item">
                  <span className="benefit-icon">✓</span>
                  <span>Maintain audit-ready evidence trails</span>
                </div>
                <div className="benefit-item">
                  <span className="benefit-icon">✓</span>
                  <span>Build trust with stakeholders</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- MESSY DATA SECTION --- */}
      <section className="messy-data-section" id="messy-data">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <span className="section-badge">📂 Real-World Ready</span>
            <h2>Built for messy real-world data</h2>
            <p className="section-subtitle">
              Your data doesn't have to be clean before you start.
            </p>
          </div>

          <div className="messy-data-content">
            <div className="data-types animate-on-scroll">
              <h3>CarbonTally can process:</h3>
              <div className="type-grid">
                <div className="type-item">
                  <span className="type-icon">📄</span>
                  <span>PDF invoices</span>
                </div>
                <div className="type-item">
                  <span className="type-icon">📷</span>
                  <span>Scanned documents & images</span>
                </div>
                <div className="type-item">
                  <span className="type-icon">📊</span>
                  <span>Excel spreadsheets</span>
                </div>
                <div className="type-item">
                  <span className="type-icon">📋</span>
                  <span>CSV files</span>
                </div>
                <div className="type-item">
                  <span className="type-icon">🔗</span>
                  <span>JSON data</span>
                </div>
                <div className="type-item">
                  <span className="type-icon">✏️</span>
                  <span>Manual extraction</span>
                </div>
              </div>
            </div>

            <div className="processing-pipeline animate-on-scroll">
              <h3>Then CarbonTally can:</h3>
              <div className="pipeline-steps">
                <span className="pipeline-step">Extract</span>
                <span className="pipeline-arrow">→</span>
                <span className="pipeline-step">Normalize</span>
                <span className="pipeline-arrow">→</span>
                <span className="pipeline-step">Map</span>
                <span className="pipeline-arrow">→</span>
                <span className="pipeline-step">Calculate</span>
                <span className="pipeline-arrow">→</span>
                <span className="pipeline-step">Validate</span>
                <span className="pipeline-arrow">→</span>
                <span className="pipeline-step pipeline-final">Preserve evidence</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- HUMAN PROCESSING SECTION --- */}
      <section className="human-processing-section" id="human-processing">
        <div className="container">
          <div className="human-processing-content">
            <div className="human-text animate-on-scroll">
              <span className="section-badge">🤝 Human + AI</span>
              <h2>Human processing when automation isn't enough</h2>
              <p>
                When the document is too messy for automation, humans can help.
              </p>
              <p>
                Poor scans. Complicated invoices. Unstructured supplier documents.
              </p>
              <p className="highlight-text">
                CarbonTally combines automated processing with human extraction 
                and quality control through its Processing Entity network.
              </p>
              <div className="human-pipeline">
                <span>Human extraction</span>
                <span className="arrow">→</span>
                <span>Mapping</span>
                <span className="arrow">→</span>
                <span>Validation</span>
                <span className="arrow">→</span>
                <span>Calculation</span>
                <span className="arrow">→</span>
                <span>Evidence</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* --- PLATFORM SECTION --- */}
      <section className="platform-section" id="platforms">
        <div className="container">
          <div className="platform-content animate-on-scroll">
            <span className="section-badge">🏗️ Built for Platforms</span>
            <h2>For carbon platforms and consultants</h2>
            <p className="platform-subtitle">
              Don't build another data-processing team. Plug into CarbonTally.
            </p>
            
            <div className="platform-benefits">
              <div className="platform-benefit">
                <span className="benefit-icon">📄</span>
                <h4>Document extraction</h4>
                <p>Automated extraction from any document format</p>
              </div>
              <div className="platform-benefit">
                <span className="benefit-icon">👤</span>
                <h4>Manual data processing</h4>
                <p>Human-in-the-loop for complex documents</p>
              </div>
              <div className="platform-benefit">
                <span className="benefit-icon">⚡</span>
                <h4>Emission-factor mapping</h4>
                <p>Automatic mapping to official factors</p>
              </div>
              <div className="platform-benefit">
                <span className="benefit-icon">✅</span>
                <h4>Validation & evidence</h4>
                <p>Quality control with full traceability</p>
              </div>
            </div>

            <div className="platform-cta">
              <p className="platform-tagline">
                Your platform. <strong>CarbonTally underneath.</strong>
              </p>
              <button className="btn-outline" onClick={handleGetStarted}>
                Talk to us about integration →
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* --- EVIDENCE RECORD SECTION --- */}
      <section className="evidence-section" id="evidence">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <span className="section-badge">📋 Evidence Record</span>
            <h2>See the data behind the calculation</h2>
            <p className="section-subtitle">
              For each emission, CarbonTally presents the underlying evidence record.
            </p>
          </div>

          <div className="evidence-card animate-on-scroll">
            <div className="evidence-header">
              <span className="evidence-result">0.140 kg CO₂e</span>
              <span className="evidence-source">INV-10482.pdf</span>
            </div>
            <div className="evidence-details">
              <div className="evidence-row">
                <span className="evidence-label">Original source data</span>
                <span className="evidence-value">Electricity — 500 kWh</span>
              </div>
              <div className="evidence-row">
                <span className="evidence-label">Mapped activity</span>
                <span className="evidence-value">Electricity</span>
              </div>
              <div className="evidence-row">
                <span className="evidence-label">Emission factor</span>
                <span className="evidence-value">DEFRA 2025 — 0.00028 kg CO₂e/kWh</span>
              </div>
              <div className="evidence-row">
                <span className="evidence-label">Calculation</span>
                <span className="evidence-value">500 × 0.00028</span>
              </div>
              <div className="evidence-row evidence-result-row">
                <span className="evidence-label">Result</span>
                <span className="evidence-value evidence-final">0.140 kg CO₂e</span>
              </div>
            </div>
            <div className="evidence-note">
              <p>This lets your team investigate the number without asking support to explain it.</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- FEATURES SECTION --- */}
      <section className="coming-soon-features" id="features">
        <div className="container">
          <div className="coming-soon-header animate-on-scroll">
            <span className="section-badge">✅ All Features Ready</span>
            <h2>Everything you need for stress-free compliance</h2>
            <p className="section-subtitle">
              From automated data mapping to auditor-ready reports — we handle the entire carbon accounting workflow.
              <br />Request your beta access today.
            </p>
          </div>
          
          <div className="feature-grid">
            {/* 1. Automated CSV Data Stream Mapping */}
            <div className="feature-card animate-on-scroll">
              <div className="icon">📊</div>
              <h3>Automated CSV Data Stream Mapping</h3>
              <p>Drop your fleet transit logs or fuel card outputs straight into our engine. CarbonTally automatically isolates transactions, standardizes column logic, and converts metrics into certified Scope 1, 2, and 3 disclosures with zero manual intervention.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            {/* 2. Systemic "Dirty Data" Isolation & Fixes */}
            <div className="feature-card animate-on-scroll">
              <div className="icon">🔧</div>
              <h3>Systemic "Dirty Data" Isolation & Fixes</h3>
              <p>If your input file is messy, incomplete, or contains structural errors, CarbonTally doesn't crash. The platform isolates unmapped variables in an interactive interface, allowing rapid inline correction without starting over.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            {/* 3. Deterministic UK DEFRA / EU Registry Engine */}
            <div className="feature-card animate-on-scroll">
              <div className="icon">⚡</div>
              <h3>Deterministic UK DEFRA / EU Registry Engine</h3>
              <p>Bypass manual spreadsheet calculations. Our backend instantly references raw consumption metrics against up-to-date official UK DEFRA and European carbon conversion factor matrices with mathematical precision and full audit trails.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            {/* 4. One-Click Granular Log Exports */}
            <div className="feature-card animate-on-scroll">
              <div className="icon">📋</div>
              <h3>One-Click Granular Log Exports</h3>
              <p>Keep your independent financial and environmental auditors satisfied. Export clean, normalized, line-by-line database transaction sheets displaying complete calculations, transparent data lineage vectors, and full calculation methodology.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            {/* 5. Compliant Auditor & Boardroom PDF Reports */}
            <div className="feature-card animate-on-scroll">
              <div className="icon">📄</div>
              <h3>Compliant Auditor & Boardroom PDF Reports</h3>
              <p>Generate and print presentation-ready, professionally structured compliance disclosure documents that satisfy global reporting rules, including SECR, CSRD, ESRS E1, and ISSB standards — all in one click.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            {/* 6. Raw Data Bulk Export Capabilities */}
            <div className="feature-card animate-on-scroll">
              <div className="icon">💾</div>
              <h3>Raw Data Bulk Export Capabilities</h3>
              <p>Need to move your compliance metrics to external business suites or enterprise ERP frameworks? Securely export your audited data variables into standardized, highly compatible CSV sets instantly for seamless integration.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            {/* 7. Premium Managed Back-Office Operations */}
            <div className="feature-card animate-on-scroll">
              <div className="icon">👥</div>
              <h3>Premium Managed Back-Office Operations</h3>
              <p>Have an overwhelming backlog of loose, unorganized paperwork? Batch-upload up to 50 documents at once and let our dedicated data operations team organize, clean, and format them into an exportable database matrix for you — with 24-hour turnaround.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            {/* 8. Side-by-Side OCR Extraction Screen */}
            <div className="feature-card animate-on-scroll">
              <div className="icon">👁️</div>
              <h3>Side-by-Side OCR Extraction Screen</h3>
              <p>Upload any digital utility invoice or paper receipt copy. Our advanced Tesseract OCR engine scans the document layer and renders a side-by-side verification interface — allowing you to inspect text parsing errors alongside the file layout before importing.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            {/* 9. Enterprise-Grade Security */}
            <div className="feature-card animate-on-scroll">
              <div className="icon">🔒</div>
              <h3>Enterprise-Grade Security</h3>
              <p>Your data is encrypted at rest and in transit with AES-256. SOC 2 compliant infrastructure with SSO, role-based access control, detailed audit logs, and GDPR-compliant data handling for complete peace of mind.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>
          </div>
        </div>
      </section>

      {/* --- WAITLIST MODAL --- */}
      {showWaitlistModal && (
        <div className="modal-overlay" onClick={() => setShowWaitlistModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowWaitlistModal(false)}>✕</button>
            
            {isSubmitted ? (
              <div className="modal-success">
                <div className="success-icon">🎉</div>
                <h3>You're on the list!</h3>
                <p>We'll notify you when beta access is available.</p>
                <p className="success-subtext">Check your email for updates.</p>
              </div>
            ) : (
              <>
                <div className="modal-header">
                  <span className="modal-icon">🧪</span>
                  <h2>Request Beta Access</h2>
                  <p>All features are ready. Be among the first to try CarbonTally.</p>
                </div>

                <form onSubmit={handleSubmitEmail} className="modal-form">
                  <div className="form-group">
                    <label htmlFor="email">Email Address</label>
                    <input
                      id="email"
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="you@company.com"
                      required
                      disabled={isSubmitting}
                    />
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Your full name (optional)"
                    />
                  </div>

                  {error && <div className="form-error">{error}</div>}

                  <button 
                    type="submit" 
                    className="modal-submit btn-gradient"
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? 'Submitting...' : 'Request Beta Access →'}
                  </button>

                  <p className="modal-subtext">
                    ✅ No spam. Unsubscribe anytime.
                  </p>
                </form>
              </>
            )}
          </div>
        </div>
      )}

      {/* --- CTA SECTION --- */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-box animate-on-scroll">
            <div className="cta-icon">🧪</div>
            <h2>Your carbon data should be more than a number.</h2>
            <p>
              It should be: <strong>Structured. Calculated. Traceable.</strong>
            </p>
            <button className="btn-primary btn-large" onClick={handleGetStarted}>
              Start processing your data →
            </button>
            <p className="cta-subtext">✅ Full features. Limited spots. No credit card required.</p>
          </div>
        </div>
      </section>

      <AppFooter />
    </div>
  );
}