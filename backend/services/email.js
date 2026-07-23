// backend/services/email.js
const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: process.env.SMTP_PORT,
  secure: true,
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS,
  },
});

exports.sendBetaInviteEmail = async (email, betaCode, inviteUrl) => {
  const mailOptions = {
    from: process.env.SMTP_FROM,
    to: email,
    subject: '🧪 You\'ve been invited to CarbonTally Beta!',
    html: `
      <h2>Welcome to CarbonTally Beta! 🎉</h2>
      <p>You've been selected to try CarbonTally's carbon accounting platform.</p>
      <p>Your beta access code: <strong>${betaCode}</strong></p>
      <a href="${inviteUrl}" style="
        display: inline-block;
        padding: 12px 24px;
        background: #10b981;
        color: white;
        text-decoration: none;
        border-radius: 8px;
        margin: 20px 0;
      ">Claim Your Beta Access →</a>
      <p>This code will expire in 30 days.</p>
    `,
  };

  await transporter.sendMail(mailOptions);
};