// src/services/emailService.js
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

export const sendBetaConfirmationEmail = async (email, fullName = '') => {
  try {
    const response = await fetch(`${API_URL}/api/waitlist`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        email: email.trim(),
        full_name: fullName,
        source: 'landing_page'
      }),
    });

    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(data.detail || data.error || 'Failed to add to waitlist');
    }

    return data;
  } catch (error) {
    console.error('Waitlist error:', error);
    throw error;
  }
};