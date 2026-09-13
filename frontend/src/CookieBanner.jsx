import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  CONSENT_ACCEPTED,
  CONSENT_DECLINED,
  readCookieConsent,
  recordCookieConsent,
} from './lib/consent';

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!readCookieConsent()) {
      setVisible(true);
    }
  }, []);

  const handleAccept = () => {
    recordCookieConsent(CONSENT_ACCEPTED);
    setVisible(false);
  };

  const handleDecline = () => {
    recordCookieConsent(CONSENT_DECLINED);
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