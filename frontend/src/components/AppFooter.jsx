import React from 'react';
import { Link } from 'react-router-dom';

export default function AppFooter() {
  return (
    <footer className="main-footer">
      <div className="footer-container">
        <div className="footer-grid">
          {/* Brand Column */}
          <div className="footer-column brand-column">
            <div className="footer-logo">
              <span className="logo-icon">🌱</span>
              <span className="logo-text">CarbonTally</span>
            </div>
            <p className="footer-description">
              Simplified carbon accounting for UK businesses. Track, report, and reduce 
              your carbon footprint with confidence.
            </p>
            <div className="social-links">
              <a href="#" aria-label="LinkedIn">in</a>
              <a href="#" aria-label="Twitter">𝕏</a>
              <a href="#" aria-label="YouTube">▶</a>
            </div>
          </div>

          {/* Product Column */}
          <div className="footer-column">
            <h4>Product</h4>
            <ul>
              <li><a href="/#features">Features</a></li>
              <li><a href="/#pricing">Pricing</a></li>
              <li><a href="#">Integrations</a></li>
              <li><a href="#">Changelog</a></li>
              <li><a href="#">Roadmap</a></li>
            </ul>
          </div>

          {/* Solutions Column */}
          <div className="footer-column">
            <h4>Solutions</h4>
            <ul>
              <li><a href="#">SECR Reporting</a></li>
              <li><a href="#">ESG Compliance</a></li>
              <li><a href="#">Supply Chain</a></li>
              <li><a href="#">Real Estate</a></li>
              <li><a href="#">Manufacturing</a></li>
            </ul>
          </div>

          {/* Resources Column */}
          <div className="footer-column">
            <h4>Resources</h4>
            <ul>
              <li><a href="#">Blog</a></li>
              <li><a href="#">Documentation</a></li>
              <li><a href="#">Help Center</a></li>
              <li><a href="#">API Reference</a></li>
              <li><a href="#">Community</a></li>
            </ul>
          </div>

          {/* Company Column */}
          <div className="footer-column">
            <h4>Company</h4>
            <ul>
              <li><a href="#">About</a></li>
              <li><a href="#">Careers</a></li>
              <li><a href="#">Contact</a></li>
              <li><Link to="/carbon-reduction-plan">Carbon Reduction Plan</Link></li>
              <li><Link to="/privacy">Privacy Policy</Link></li>
              <li><Link to="/terms">Terms of Service</Link></li>
            </ul>
          </div>
        </div>

        {/* Footer Bottom with GDPR Links */}
        <div className="footer-bottom">
          <div className="footer-bottom-content">
            <p>© {new Date().getFullYear()} CarbonTally Ltd. All rights reserved.</p>
            <div className="footer-legal-links">
              <Link to="/privacy">Privacy Policy</Link>
              <Link to="/cookies">Cookie Policy</Link>
              <Link to="/terms">Terms</Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}