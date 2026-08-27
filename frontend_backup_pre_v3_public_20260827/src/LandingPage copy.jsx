// src/LandingPage.jsx - Slideshow without overlay text
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppHeader from './components/AppHeader';
import AppFooter from './components/AppFooter';
import './LandingPage.css';

// Import your dashboard images
import carbonTallyUpload from './images/carbon_tally_upload_main.png';
import uploadImage from './images/carbon_tally_upload.gif';
import emissionsTrendImage from './images/emissions_trend.png';
import executiveOverviewImage from './images/executive_overview.png';
import CarbonTallyDemo from './components/CarbonTallyDemo';


export default function LandingPage() {
  const navigate = useNavigate();
  const [currentSlide, setCurrentSlide] = useState(0);
  const [email, setEmail] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [error, setError] = useState('');
  const [showWaitlistModal, setShowWaitlistModal] = useState(false);

  // Slides data
  const slides = [
    {
      image: carbonTallyUpload,
      alt: 'CarbonTally Dashboard Preview',
    },
    {
      image: emissionsTrendImage,
      alt: 'CarbonTally Emission Report',
    },
    {
      image: executiveOverviewImage,
      alt: 'CarbonTally Executive Overview',
    }
  ];

  // Auto-slide every 5 seconds
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentSlide((prev) => (prev + 1) % slides.length);
    }, 5000);
    return () => clearInterval(timer);
  }, [slides.length]);

  // Navigation functions
  const plusSlides = (n) => {
    setCurrentSlide((prev) => (prev + n + slides.length) % slides.length);
  };

  const goToSlide = (index) => {
    setCurrentSlide(index);
  };

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
    e.preventDefault();
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

  try {
    const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/api/waitlist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        email: email.trim(),
        full_name: '',
        source: 'landing_page'
      }),
    });

    const data = await response.json();

    if (data.success) {
      setIsSubmitted(true);
      setEmail('');
      setTimeout(() => {
        setShowWaitlistModal(false);
        setIsSubmitted(false);
      }, 2000);
    } else {
      if (data.error === 'Already on waitlist') {
        setError('This email is already on our waitlist!');
      } else {
        setError(data.error || 'Failed to join waitlist. Please try again.');
      }
    }
  } catch (error) {
    console.error('Waitlist error:', error);
    setError('Failed to join waitlist. Please try again.');
  } finally {
    setIsSubmitting(false);
  }
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
      <section className="hero-section">
         <CarbonTallyDemo />
               
      </section>
      {/* --- HERO SECTION WITH SLIDESHOW (NO OVERLAY TEXT) --- */}
      <section className="hero-with-image">
        <div className="hero-image-wrapper animate-on-scroll">
          <div className="hero-image-container">
            
            {/* Slideshow Container */}
            <div className="hero-image-slideshow-container">
              
              {/* Slides */}
              {slides.map((slide, index) => (
                <div 
                  key={index}
                  className={`mySlides fade ${index === currentSlide ? 'active' : ''}`}
                  style={{ display: index === currentSlide ? 'block' : 'none' }}
                >
                  <img 
                    src={slide.image} 
                    alt={slide.alt} 
                    className="hero-main-image"
                  />
                </div>
              ))}

              {/* Navigation Buttons */}
              <a className="prev" onClick={() => plusSlides(-1)}>&#10094;</a>
              <a className="next" onClick={() => plusSlides(1)}>&#10095;</a>
            </div>

            {/* Dots/Indicators */}
            <div className="dots-container">
              {slides.map((_, index) => (
                <span 
                  key={index}
                  className={`dot ${index === currentSlide ? 'active' : ''}`} 
                  onClick={() => goToSlide(index)}
                ></span>
              ))}
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
              All features are fully functional and ready for beta testing. 
              <br />Request your beta access today.
            </p>
          </div>
          
          <div className="feature-grid">
            <div className="feature-card animate-on-scroll">
              <div className="icon">🤖</div>
              <h3>AI-Powered Document Extraction</h3>
              <p>Upload messy PDFs, images, or CSVs. Our AI auto-extracts consumption data, assets, and dates, applying the correct DEFRA factors instantly.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            <div className="feature-card animate-on-scroll">
              <div className="icon">📦</div>
              <h3>Enterprise Bulk Upload</h3>
              <p>Drop up to 50 utility bills or fuel invoices at once. Complex documents are intelligently queued for expert manual verification within 24 hours.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            <div className="feature-card animate-on-scroll">
              <div className="icon">🌍</div>
              <h3>Comprehensive Scope 1, 2 & 3</h3>
              <p>Track emissions across all facilities and assets. From company vehicles and natural gas to business travel, flights, and waste management.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            <div className="feature-card animate-on-scroll">
              <div className="icon">🇬🇧</div>
              <h3>UK SECR Automation</h3>
              <p>Generate beautiful, branded, audit-ready PDF reports with a single click. Includes executive summaries, scope breakdowns, and official compliance statements.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            <div className="feature-card animate-on-scroll">
              <div className="icon">📊</div>
              <h3>Big 4 Auditor Excel Exports</h3>
              <p>Export your granular GHG inventory in the exact multi-tab format required by auditors. Features automatic GHG Protocol Scope 3 category mapping.</p>
              <span className="feature-status status-ready">✅ Ready</span>
            </div>

            <div className="feature-card animate-on-scroll">
              <div className="icon">🔒</div>
              <h3>Enterprise-Grade Security</h3>
              <p>Your data is encrypted at rest and in transit. SOC 2 compliant with SSO, role-based access, and detailed audit logs.</p>
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
            <h2>Ready to try CarbonTally?</h2>
            <p>
              All features are fully functional and ready for testing.
              <br />
              <strong>Limited beta spots available — request yours today.</strong>
            </p>
            <button className="btn-primary btn-large" onClick={handleGetStarted}>
              Request Beta Access
            </button>
            <p className="cta-subtext">✅ Full features. Limited spots. No credit card required.</p>
          </div>
        </div>
      </section>

      <AppFooter />
    </div>
  );
}