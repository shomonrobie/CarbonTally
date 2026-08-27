import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const consent = localStorage.getItem('cookieConsent');
    if (!consent) {
      setVisible(true);
    }
  }, []);

  const handleAccept = () => {
    localStorage.setItem('cookieConsent', 'accepted');
    setVisible(false);
  };

  const handleDecline = () => {
    localStorage.setItem('cookieConsent', 'declined');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="cookie-banner">
      <div className="cookie-banner-content">
        <p>
          We use cookies to enhance your experience. By continuing to visit this site, 
          you agree to our use of cookies. Learn more in our{' '}
          <Link to="/cookies">Cookie Policy</Link>.
        </p>
      </div>
      <div className="cookie-banner-actions">
        <button className="cookie-btn-settings" onClick={handleDecline}>
          Decline
        </button>
        <button className="cookie-btn-accept" onClick={handleAccept}>
          Accept All
        </button>
      </div>
    </div>
  );
}