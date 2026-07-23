// backend/routes/email.js
const express = require('express');
const router = express.Router();
const { Resend } = require('resend');
const { betaConfirmationEmail, betaInviteEmail } = require('../services/emailTemplates');

const resend = new Resend(process.env.RESEND_API_KEY);

// Send beta confirmation email
router.post('/send-beta-confirmation', async (req, res) => {
  try {
    const { email, fullName } = req.body;

    if (!email) {
      return res.status(400).json({ error: 'Email is required' });
    }

    const html = betaConfirmationEmail(email, fullName);
    
    const data = await resend.emails.send({
      from: 'CarbonTally <noreply@carbontally.co.uk>',
      to: [email],
      subject: '🔬 CarbonTally Beta Access Request Received',
      html,
    });

    res.status(200).json({ 
      success: true, 
      message: 'Confirmation email sent',
      data 
    });
  } catch (error) {
    console.error('Email error:', error);
    res.status(500).json({ error: 'Failed to send email' });
  }
});

// Send beta invite email (when you want to invite someone)
router.post('/send-beta-invite', async (req, res) => {
  try {
    const { email, betaCode, fullName } = req.body;

    if (!email || !betaCode) {
      return res.status(400).json({ error: 'Email and beta code are required' });
    }

    const html = betaInviteEmail(email, betaCode, fullName);
    
    const data = await resend.emails.send({
      from: 'CarbonTally <noreply@carbontally.co.uk>',
      to: [email],
      subject: '🎉 You\'ve been invited to CarbonTally Beta!',
      html,
    });

    res.status(200).json({ 
      success: true, 
      message: 'Beta invite email sent',
      data 
    });
  } catch (error) {
    console.error('Email error:', error);
    res.status(500).json({ error: 'Failed to send email' });
  }
});

module.exports = router;