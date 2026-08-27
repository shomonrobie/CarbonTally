// CompanyNamePrompt.jsx
import React, { useState } from 'react';
import './css/CompanyNamePrompt.css';

function CompanyNamePrompt({ onSave, onSkip, email, user }) {
  const [orgName, setOrgName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!orgName.trim()) {
      setError('Please enter your organization name');
      return;
    }
    
    setError('');
    setLoading(true);
    
    try {
      await onSave({ name: orgName.trim() });
    } catch (err) {
      setError('Failed to save: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="company-prompt-overlay">
      <div className="company-prompt-modal">
        <h2>🏢 Welcome to CarbonTally!</h2>
        <p className="prompt-subtitle">
          Please enter your organization name to continue.
          {email && <span className="user-email"> ({email})</span>}
        </p>
        
        {error && <div className="error-message">{error}</div>}
        
        <form onSubmit={handleSubmit} className="company-form">
          <div className="form-group">
            <label htmlFor="orgName">Organization Name *</label>
            <input
              id="orgName"
              type="text"
              value={orgName}
              onChange={(e) => {
                setOrgName(e.target.value);
                setError('');
              }}
              placeholder="e.g., ABC Logistics Ltd"
              required
              autoFocus
              disabled={loading}
            />
          </div>
          
          <div className="button-group">
            <button 
              type="submit" 
              className="save-button"
              disabled={loading}
            >
              {loading ? 'Saving...' : 'Save Organization'}
            </button>
            <button 
              type="button" 
              onClick={onSkip}
              className="skip-button"
              disabled={loading}
            >
              Skip for now
            </button>
          </div>
          
          <p className="prompt-note">
            ⚡ You can always update this later in your profile settings.
          </p>
        </form>
      </div>
    </div>
  );
}

export default CompanyNamePrompt;