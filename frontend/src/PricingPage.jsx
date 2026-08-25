// src/PricingPage.jsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';
import './css/pricing_page.css';

export default function PricingPage() {
  const navigate = useNavigate();
  const [isAnnual, setIsAnnual] = useState(false);
  const [showWaitlistModal, setShowWaitlistModal] = useState(false);
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [selectedPlan, setSelectedPlan] = useState('');
  const [activeTab, setActiveTab] = useState('self-service');

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

  const plans = {
    selfService: [
      {
        id: 'starter',
        name: 'Starter',
        price: 49,
        description: 'For organizations getting started with structured carbon-data processing.',
        credits: 100,
        features: [
          'PDF & image document processing',
          'CSV / Excel / JSON processing',
          'Automated data extraction',
          'Emission-factor matching',
          'Emissions calculation',
          'Evidence & provenance',
          'Source-document access',
          'Basic document storage',
          'CSV / Excel exports',
          'Processing history',
          '3 team members'
        ],
        cta: 'Start with Starter',
        popular: false
      },
      {
        id: 'professional',
        name: 'Professional',
        price: 149,
        description: 'For growing organizations and carbon-accounting teams processing data regularly.',
        credits: 500,
        features: [
          'Everything in Starter',
          'Larger structured-data processing',
          'Extended document storage',
          'Advanced evidence & provenance',
          'Reverse document → emissions lookup',
          'Team workflows',
          'Up to 10 team members',
          'Processing priority',
          'Assisted Processing access',
          'Consultant workspace capabilities',
          'Larger batch processing'
        ],
        cta: 'Start with Professional',
        popular: true
      },
      {
        id: 'business',
        name: 'Business',
        price: 399,
        description: 'For organizations with larger data-processing requirements.',
        credits: 2000,
        features: [
          'Everything in Professional',
          'Higher-volume processing',
          'Larger structured datasets',
          'More document storage',
          'Up to 25 team members',
          'Advanced organization controls',
          'Priority processing',
          'Assisted Processing',
          'Managed Processing access',
          'Consultant/multi-client workflows',
          'Higher batch limits',
          'Priority support'
        ],
        cta: 'Choose Business',
        popular: false
      },
      {
        id: 'enterprise',
        name: 'Enterprise',
        price: null,
        description: 'For large organizations, carbon-accounting firms and high-volume processing requirements.',
        credits: 'Custom',
        features: [
          'Custom credit allocation',
          'Custom processing limits',
          'Large-scale document processing',
          'Enterprise storage',
          'Unlimited or negotiated team access',
          'Multiple organizations/entities',
          'API processing',
          'Managed Processing',
          'Dedicated processing workflows',
          'Custom emission-factor requirements',
          'Custom onboarding',
          'Enterprise support',
          'Contract pricing'
        ],
        cta: 'Talk to CarbonTally',
        popular: false,
        isEnterprise: true
      }
    ],
    assisted: [
      {
        id: 'simple',
        name: 'Simple',
        price: 0.99,
        description: 'Simple document processing with minimal complexity.',
        features: ['Basic extraction', 'Standard mapping', 'Simple validation'],
        cta: 'Request Assisted Processing'
      },
      {
        id: 'standard',
        name: 'Standard',
        price: 1.99,
        description: 'Standard document processing with moderate complexity.',
        features: ['Advanced extraction', 'Complex mapping', 'Full validation'],
        cta: 'Request Assisted Processing'
      },
      {
        id: 'complex',
        name: 'Complex',
        price: 3.99,
        description: 'Complex document processing requiring human review.',
        features: ['Full extraction', 'Custom mapping', 'Quality control'],
        cta: 'Request Assisted Processing'
      }
    ]
  };

  const creditTable = [
    { type: 'Simple', credits: 1 },
    { type: 'Standard', credits: 2 },
    { type: 'Complex', credits: 4 },
    { type: 'Exceptional', credits: 'Assessed' }
  ];

  const structuredDataPricing = [
    { range: 'Up to 1,000', units: 1 },
    { range: '1,001–10,000', units: 3 },
    { range: '10,001–50,000', units: 10 },
    { range: '50,001–250,000', units: 30 },
    { range: '250,001–1,000,000', units: 100 },
    { range: 'Over 1,000,000', units: 'Custom' }
  ];

  const comparisonTable = {
    headers: ['', 'Starter', 'Professional', 'Business', 'Enterprise'],
    rows: [
      { label: 'Monthly price', values: ['$49', '$149', '$399', 'Custom'] },
      { label: 'Credits', values: ['100', '500', '2,000', 'Custom'] },
      { label: 'PDF/image processing', values: ['✓', '✓', '✓', '✓'] },
      { label: 'CSV/Excel/JSON', values: ['✓', '✓', '✓', '✓'] },
      { label: 'Emission-factor mapping', values: ['✓', '✓', '✓', '✓'] },
      { label: 'Calculation', values: ['✓', '✓', '✓', '✓'] },
      { label: 'Evidence/provenance', values: ['✓', '✓', '✓', '✓'] },
      { label: 'Basic storage', values: ['✓', '✓', '✓', '✓'] },
      { label: 'Team members', values: ['3', '10', '25', 'Custom'] },
      { label: 'Assisted Processing', values: ['Access', '✓', '✓', '✓'] },
      { label: 'Managed Processing', values: ['—', 'Access', '✓', '✓'] },
      { label: 'Consultant workflows', values: ['—', '✓', '✓', '✓'] },
      { label: 'Large-volume processing', values: ['—', 'Limited', '✓', '✓'] },
      { label: 'API', values: ['—', '—', 'Access', '✓'] },
      { label: 'Enterprise support', values: ['—', '—', '—', '✓'] }
    ]
  };

  const PricingCard = ({ plan, isAnnual }) => {
    const annualPrice = plan.price ? Math.round(plan.price * 12 * 0.8) : null;
    const monthlyPrice = plan.price;

    return (
      <div className={`pricing-card animate-on-scroll ${plan.popular ? 'popular' : ''} ${plan.isEnterprise ? 'enterprise' : ''}`}>
        {plan.popular && <div className="popular-badge">Most Popular</div>}
        <div className="plan-header">
          <h3>{plan.name}</h3>
          <div className="plan-price">
            {plan.price ? (
              <>
                <span className="currency">$</span>
                <span className="amount">{isAnnual ? Math.round(plan.price * 12 * 0.8 / 12) : plan.price}</span>
                <span className="period">/month</span>
                {isAnnual && (
                  <div className="annual-note">
                    <span className="billed-annually">Billed annually</span>
                    <span className="save-badge">Save 20%</span>
                  </div>
                )}
              </>
            ) : (
              <span className="custom-price">Custom</span>
            )}
          </div>
          {plan.credits && (
            <div className="plan-credits">
              <span className="credits-count">{plan.credits}</span>
              <span className="credits-label">CarbonTally Credits / month</span>
            </div>
          )}
          <p className="plan-description">{plan.description}</p>
        </div>
        <ul className="plan-features">
          {plan.features.map((feature, index) => (
            <li key={index}>
              <span className="feature-icon">✓</span>
              {feature}
            </li>
          ))}
        </ul>
        <button 
          className={`plan-cta ${plan.popular ? 'btn-primary' : 'btn-outline'}`}
          onClick={() => {
            setSelectedPlan(plan.id);
            setShowWaitlistModal(true);
          }}
        >
          {plan.cta}
        </button>
      </div>
    );
  };

  return (
    <div className="pricing-page">
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
      <section className="pricing-hero">
        <div className="container">
          <div className="pricing-hero-content">
            <span className="section-badge">💰 Pricing</span>
            <h1>Turn your carbon data into <br /><span className="gradient-text">usable, traceable results</span></h1>
            <p className="hero-description">
              Upload your data. Process it yourself, let CarbonTally assist, or let us manage the work for you.
            </p>
            <p className="hero-sub-description">
              CarbonTally is built for organizations and carbon-accounting professionals that need to turn messy source data into structured, mapped, calculated and traceable emissions data.
            </p>
            <div className="pricing-note">
              <span className="note-icon">📌</span>
              <span>Pricing shown is a proposed baseline and may change before commercial launch.</span>
            </div>
          </div>
        </div>
      </section>

      {/* --- WORK MODE SELECTOR --- */}
      <section className="work-mode-section">
        <div className="container">
          <div className="work-mode-tabs animate-on-scroll">
            <button 
              className={`tab-btn ${activeTab === 'self-service' ? 'active' : ''}`}
              onClick={() => setActiveTab('self-service')}
            >
              <span className="tab-icon">⚡</span>
              Self-Service
            </button>
            <button 
              className={`tab-btn ${activeTab === 'assisted' ? 'active' : ''}`}
              onClick={() => setActiveTab('assisted')}
            >
              <span className="tab-icon">🤝</span>
              Assisted Processing
            </button>
            <button 
              className={`tab-btn ${activeTab === 'managed' ? 'active' : ''}`}
              onClick={() => setActiveTab('managed')}
            >
              <span className="tab-icon">👥</span>
              Managed Processing
            </button>
          </div>

          <div className="work-mode-description animate-on-scroll">
            {activeTab === 'self-service' && (
              <div className="mode-description">
                <h3>Self-Service</h3>
                <p>You upload and process your own data.</p>
                <p className="mode-subtext">Take full control of your carbon data processing workflow.</p>
              </div>
            )}
            {activeTab === 'assisted' && (
              <div className="mode-description">
                <h3>Assisted Processing</h3>
                <p>CarbonTally handles documents that need human assistance.</p>
                <p className="mode-subtext">When automated processing isn't enough, we're here to help.</p>
              </div>
            )}
            {activeTab === 'managed' && (
              <div className="mode-description">
                <h3>Managed Processing</h3>
                <p>You upload the documents. We manage the processing for you.</p>
                <p className="mode-subtext">Let us handle everything from document intake to final results.</p>
              </div>
            )}
          </div>
        </div>
      </section>

      {/* --- PRICING PLANS --- */}
      <section className="pricing-plans-section">
        <div className="container">
          {activeTab === 'self-service' && (
            <>
              <div className="billing-toggle animate-on-scroll">
                <span className={!isAnnual ? 'active' : ''}>Monthly</span>
                <label className="toggle-switch">
                  <input 
                    type="checkbox" 
                    checked={isAnnual}
                    onChange={() => setIsAnnual(!isAnnual)}
                  />
                  <span className="toggle-slider"></span>
                </label>
                <span className={isAnnual ? 'active' : ''}>
                  Annual <span className="save-badge">Save 20%</span>
                </span>
              </div>

              <div className="pricing-grid">
                {plans.selfService.map((plan) => (
                  <PricingCard key={plan.id} plan={plan} isAnnual={isAnnual} />
                ))}
              </div>

              <div className="pricing-note-bottom animate-on-scroll">
                <p>
                  <strong>Need more processing?</strong> Additional processing and Managed Processing are available.
                  <br />
                  Unused paid credits can roll over according to CarbonTally's rollover policy.
                </p>
              </div>
            </>
          )}

          {activeTab === 'assisted' && (
            <>
              <div className="assisted-grid">
                {plans.assisted.map((plan) => (
                  <div key={plan.id} className="assisted-card animate-on-scroll">
                    <div className="assisted-header">
                      <h3>{plan.name}</h3>
                      <div className="assisted-price">
                        <span className="currency">$</span>
                        <span className="amount">{plan.price}</span>
                        <span className="period">/ document</span>
                      </div>
                    </div>
                    <p className="assisted-description">{plan.description}</p>
                    <ul className="assisted-features">
                      {plan.features.map((feature, index) => (
                        <li key={index}>
                          <span className="feature-icon">✓</span>
                          {feature}
                        </li>
                      ))}
                    </ul>
                    <button 
                      className="btn-primary assisted-cta"
                      onClick={() => {
                        setSelectedPlan(plan.id);
                        setShowWaitlistModal(true);
                      }}
                    >
                      {plan.cta}
                    </button>
                  </div>
                ))}
              </div>

              <div className="assisted-example animate-on-scroll">
                <div className="example-card">
                  <h4>Example</h4>
                  <p>You have:</p>
                  <ul>
                    <li>10 Simple documents</li>
                    <li>4 Standard documents</li>
                    <li>1 Complex document</li>
                  </ul>
                  <div className="example-total">
                    <span>Estimated Assisted Processing:</span>
                    <strong>$21.85</strong>
                  </div>
                  <p className="example-note">You review the estimate and decide whether to proceed.</p>
                </div>
              </div>
            </>
          )}

          {activeTab === 'managed' && (
            <div className="managed-content">
              <div className="managed-card animate-on-scroll">
                <div className="managed-icon">👥</div>
                <h3>On-Demand Managed Batch</h3>
                <p>You upload the documents. We manage the rest.</p>
                <p className="managed-description">
                  CarbonTally can coordinate:
                </p>
                <ul className="managed-features">
                  <li>Document intake</li>
                  <li>Automated extraction</li>
                  <li>Data normalization</li>
                  <li>Emission-factor mapping</li>
                  <li>Human processing where required</li>
                  <li>Validation</li>
                  <li>Quality control</li>
                  <li>Evidence/provenance</li>
                  <li>Final results</li>
                </ul>
                <p className="managed-note">
                  You don't have to sit in front of CarbonTally and process every document yourself.
                </p>
                <button className="btn-primary" onClick={() => setShowWaitlistModal(true)}>
                  Request a Managed Batch
                </button>
              </div>

              <div className="managed-enterprise animate-on-scroll">
                <div className="enterprise-badge">Enterprise</div>
                <h3>Enterprise Managed Processing</h3>
                <p>For organizations with recurring or high-volume requirements.</p>
                <p className="enterprise-description">
                  We'll agree the workflow, volume, service requirements and commercial terms with you.
                </p>
                <button className="btn-outline" onClick={() => setShowWaitlistModal(true)}>
                  Talk to CarbonTally
                </button>
              </div>
            </div>
          )}
        </div>
      </section>

      {/* --- CREDIT INFORMATION --- */}
      <section className="credit-section">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <span className="section-badge">💳 Credits</span>
            <h2>What is a CarbonTally Credit?</h2>
            <p className="section-subtitle">
              A CarbonTally Credit represents a unit of automated processing entitlement.
              <br />
              The amount required depends on the complexity of the processing.
            </p>
          </div>

          <div className="credit-grid animate-on-scroll">
            <div className="credit-card">
              <h4>Automated Document</h4>
              <table className="credit-table">
                <thead>
                  <tr>
                    <th>Complexity</th>
                    <th>Credits</th>
                  </tr>
                </thead>
                <tbody>
                  {creditTable.map((item, index) => (
                    <tr key={index}>
                      <td>{item.type}</td>
                      <td><strong>{item.credits}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="credit-note">CarbonTally determines the processing complexity.</p>
            </div>

            <div className="credit-card">
              <h4>Structured Data</h4>
              <p className="structured-note">CSV, Excel and JSON files can contain thousands or millions of records.</p>
              <table className="credit-table">
                <thead>
                  <tr>
                    <th>Records / rows</th>
                    <th>Processing units</th>
                  </tr>
                </thead>
                <tbody>
                  {structuredDataPricing.map((item, index) => (
                    <tr key={index}>
                      <td>{item.range}</td>
                      <td><strong>{item.units}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <p className="credit-note">These are draft processing bands and may be refined as we learn from real customer workloads.</p>
            </div>
          </div>

          <div className="credit-extra animate-on-scroll">
            <div className="extra-card">
              <span className="extra-icon">💰</span>
              <h4>No Surprise Human-Processing Charges</h4>
              <p>If CarbonTally cannot confidently complete a document automatically, you have a choice:</p>
              <ul>
                <li>Fix or complete the data yourself</li>
                <li>Ask CarbonTally to process it</li>
                <li>Include it in a Managed Processing batch</li>
              </ul>
              <p className="extra-note">You remain in control.</p>
            </div>

            <div className="extra-card">
              <span className="extra-icon">🔄</span>
              <h4>Credits That Don't Simply Disappear</h4>
              <p>Our planned model allows eligible paid credits to roll over.</p>
              <p className="extra-note">Final rollover terms will be shown clearly before purchase.</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- COMPARISON TABLE --- */}
      <section className="comparison-section">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <span className="section-badge">📊 Compare Plans</span>
            <h2>Which plan is right for you?</h2>
          </div>

          <div className="comparison-table-wrapper animate-on-scroll">
            <table className="comparison-table">
              <thead>
                <tr>
                  {comparisonTable.headers.map((header, index) => (
                    <th key={index} className={index === 0 ? 'sticky-col' : ''}>
                      {header}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {comparisonTable.rows.map((row, index) => (
                  <tr key={index}>
                    <td className="sticky-col">{row.label}</td>
                    {row.values.map((value, vIndex) => (
                      <td key={vIndex} className={value === '✓' ? 'check-mark' : ''}>
                        {value}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="comparison-note animate-on-scroll">
            <p>
              <strong>Need more processing?</strong> You don't necessarily need to upgrade your subscription.
              <br />
              You can purchase additional processing capacity or use Assisted Processing, Managed Processing, or Enterprise arrangements.
            </p>
          </div>
        </div>
      </section>

      {/* --- CONSULTANT SECTION --- */}
      <section className="consultant-section">
        <div className="container">
          <div className="consultant-content animate-on-scroll">
            <span className="section-badge">👔 For Consultants</span>
            <h2>Manage multiple clients from one workspace</h2>
            <p className="consultant-description">
              CarbonTally is designed to support consultants working across multiple customer organizations.
            </p>
            <div className="consultant-features">
              <div className="consultant-feature">
                <span className="feature-icon">🏢</span>
                <span>Manage multiple client organizations</span>
              </div>
              <div className="consultant-feature">
                <span className="feature-icon">📊</span>
                <span>Process client data</span>
              </div>
              <div className="consultant-feature">
                <span className="feature-icon">👤</span>
                <span>Assign team members</span>
              </div>
              <div className="consultant-feature">
                <span className="feature-icon">✅</span>
                <span>Review evidence</span>
              </div>
              <div className="consultant-feature">
                <span className="feature-icon">⚙️</span>
                <span>Manage processing workflows</span>
              </div>
              <div className="consultant-feature">
                <span className="feature-icon">📤</span>
                <span>Export processed data</span>
              </div>
              <div className="consultant-feature">
                <span className="feature-icon">🤝</span>
                <span>Request Assisted Processing</span>
              </div>
              <div className="consultant-feature">
                <span className="feature-icon">👥</span>
                <span>Request Managed Processing</span>
              </div>
            </div>
            <p className="consultant-note">
              Your clients remain separate organizations with separate data and access controls.
            </p>
            <button className="btn-primary" onClick={() => setShowWaitlistModal(true)}>
              Talk to CarbonTally
            </button>
          </div>
        </div>
      </section>

      {/* --- FAQ SECTION --- */}
      <section className="faq-section">
        <div className="container">
          <div className="section-header animate-on-scroll">
            <span className="section-badge">❓ FAQ</span>
            <h2>Frequently Asked Questions</h2>
          </div>

          <div className="faq-grid animate-on-scroll">
            <div className="faq-item">
              <h4>Is CarbonTally a carbon-reporting platform?</h4>
              <p>CarbonTally is primarily a carbon-data processing and management platform. It is designed to transform source data into structured, mapped, calculated and traceable emissions data. It can work alongside carbon-accounting and reporting platforms rather than requiring you to replace them.</p>
            </div>

            <div className="faq-item">
              <h4>Do I have to use credits?</h4>
              <p>CarbonTally supports both a Credit-Based and a Standard commercial model. The commercial model available to you will be shown when you subscribe.</p>
            </div>

            <div className="faq-item">
              <h4>Do unused credits expire?</h4>
              <p>Our planned model allows eligible paid credits to roll over. The exact terms will be displayed before purchase.</p>
            </div>

            <div className="faq-item">
              <h4>What happens when CarbonTally cannot process my document?</h4>
              <p>You can review the result and either correct/provide the data yourself or request Assisted Processing. For larger workloads, you can also use Managed Processing.</p>
            </div>

            <div className="faq-item">
              <h4>Do I pay for the emission calculation?</h4>
              <p>No separate calculation charge is planned. The calculation is part of the processing workflow.</p>
            </div>

            <div className="faq-item">
              <h4>Can CarbonTally process my entire document collection for me?</h4>
              <p>Yes. Use Managed Processing for batches where you want CarbonTally to coordinate automated processing, human processing, QC and completion.</p>
            </div>

            <div className="faq-item">
              <h4>Can consultants manage multiple customers?</h4>
              <p>Yes. CarbonTally is designed to support consultants managing multiple client organizations while keeping each organization's data and access separate.</p>
            </div>

            <div className="faq-item">
              <h4>Can I use CarbonTally as my document repository?</h4>
              <p>Yes. Basic storage is included with your plan. Additional storage can be purchased when your document library grows.</p>
            </div>

            <div className="faq-item">
              <h4>Can I see where an emission came from?</h4>
              <p>Yes. CarbonTally's evidence workflow is designed to connect an emission result to its calculation, emission factor, extracted source data and original source document, with source-location detail where reliably available.</p>
            </div>
          </div>
        </div>
      </section>

      {/* --- CTA SECTION --- */}
      <section className="cta-section">
        <div className="container">
          <div className="cta-box animate-on-scroll">
            <div className="cta-icon">🧪</div>
            <h2>Ready to process your carbon data?</h2>
            <p>
              <strong>Start with CarbonTally.</strong>
            </p>
            <div className="cta-buttons">
              <button className="btn-primary btn-large" onClick={() => setShowWaitlistModal(true)}>
                Request Beta Access →
              </button>
              <button className="btn-secondary btn-large" onClick={() => setShowWaitlistModal(true)}>
                View Plans
              </button>
            </div>
            <p className="cta-subtext">✅ Full features. Limited spots. No credit card required.</p>
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
                  {selectedPlan && (
                    <p className="selected-plan">Selected plan: <strong>{selectedPlan}</strong></p>
                  )}
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

      <AppFooter />
    </div>
  );
}