// src/services/emailTemplates.js

// Beta confirmation email template
export const betaConfirmationEmail = (email, fullName = '') => {
  const name = fullName || email.split('@')[0];
  
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Beta Access Request Received</title>
        <style>
          body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            line-height: 1.6; 
            color: #1e293b;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
          }
          .header {
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 12px 12px 0 0;
          }
          .header h1 {
            margin: 0;
            font-size: 28px;
          }
          .content {
            background: #f8fafc;
            padding: 40px 30px;
            border-left: 1px solid #e2e8f0;
            border-right: 1px solid #e2e8f0;
          }
          .content h2 {
            color: #0f172a;
            margin-top: 0;
          }
          .content p {
            color: #475569;
          }
          .feature-list {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
            margin: 20px 0;
          }
          .feature-list li {
            padding: 8px 0;
            border-bottom: 1px solid #f1f5f9;
          }
          .feature-list li:last-child {
            border-bottom: none;
          }
          .footer {
            background: #f1f5f9;
            padding: 20px 30px;
            text-align: center;
            border-radius: 0 0 12px 12px;
            border: 1px solid #e2e8f0;
            color: #64748b;
            font-size: 14px;
          }
          .button {
            display: inline-block;
            padding: 12px 24px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin: 10px 0;
          }
          .button:hover {
            background: linear-gradient(135deg, #059669, #047857);
          }
          .badge {
            display: inline-block;
            background: #dbeafe;
            color: #1e40af;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
          }
          @media (max-width: 480px) {
            .header { padding: 20px; }
            .content { padding: 20px; }
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>🌱 CarbonTally</h1>
          <p style="margin: 5px 0 0; opacity: 0.8;">Beta Access Request Received</p>
        </div>
        
        <div class="content">
          <h2>Hi ${name}! 👋</h2>
          
          <p>Thank you for requesting early access to CarbonTally's beta program. We're thrilled to have you on board!</p>
          
          <p><strong>Here's what happens next:</strong></p>
          
          <div class="feature-list">
            <ul style="list-style: none; padding: 0;">
              <li>✅ <strong>Step 1:</strong> We'll review your request within 24 hours</li>
              <li>✅ <strong>Step 2:</strong> You'll receive a beta invite with your unique access code</li>
              <li>✅ <strong>Step 3:</strong> Start tracking your carbon emissions immediately</li>
            </ul>
          </div>
          
          <p style="text-align: center;">
            <a href="https://carbontally.co.uk" class="button">Visit CarbonTally</a>
          </p>
          
          <p style="font-size: 14px; color: #64748b;">
            <span class="badge">🧪 Limited Beta</span> 
            <span style="margin-left: 10px;">All features are ready for testing</span>
          </p>
          
          <p style="font-size: 14px; color: #94a3b8; margin-top: 20px;">
            Questions? Reply to this email or visit our <a href="https://carbontally.co.uk/support" style="color: #10b981;">support page</a>.
          </p>
        </div>
        
        <div class="footer">
          <p style="margin: 0;">
            © 2024 CarbonTally. All rights reserved.<br>
            <span style="color: #94a3b8; font-size: 12px;">
              This email was sent to ${email}
            </span>
          </p>
        </div>
      </body>
    </html>
  `;
};

// Beta invite email template (for when you're ready to invite them)
export const betaInviteEmail = (email, betaCode, fullName = '') => {
  const name = fullName || email.split('@')[0];
  const signupUrl = `https://carbontally.co.uk/signup?code=${betaCode}`;
  
  return `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Your Beta Access is Ready!</title>
        <style>
          body { 
            font-family: 'Segoe UI', Arial, sans-serif; 
            line-height: 1.6; 
            color: #1e293b;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
          }
          .header {
            background: linear-gradient(135deg, #0f172a, #1e293b);
            color: white;
            padding: 30px;
            text-align: center;
            border-radius: 12px 12px 0 0;
          }
          .header h1 {
            margin: 0;
            font-size: 28px;
          }
          .content {
            background: #f8fafc;
            padding: 40px 30px;
            border-left: 1px solid #e2e8f0;
            border-right: 1px solid #e2e8f0;
          }
          .code-box {
            background: white;
            padding: 20px;
            border-radius: 8px;
            border: 2px dashed #10b981;
            text-align: center;
            margin: 20px 0;
          }
          .code-box .code {
            font-size: 32px;
            font-weight: 700;
            color: #059669;
            letter-spacing: 2px;
            font-family: monospace;
          }
          .button {
            display: inline-block;
            padding: 14px 28px;
            background: linear-gradient(135deg, #10b981, #059669);
            color: white;
            text-decoration: none;
            border-radius: 8px;
            font-weight: 600;
            margin: 10px 0;
          }
          .footer {
            background: #f1f5f9;
            padding: 20px 30px;
            text-align: center;
            border-radius: 0 0 12px 12px;
            border: 1px solid #e2e8f0;
            color: #64748b;
            font-size: 14px;
          }
        </style>
      </head>
      <body>
        <div class="header">
          <h1>🌱 CarbonTally</h1>
          <p style="margin: 5px 0 0; opacity: 0.8;">You're Invited!</p>
        </div>
        
        <div class="content">
          <h2>Hi ${name}! 🎉</h2>
          
          <p>Great news! You've been selected for CarbonTally's beta program.</p>
          
          <p><strong>Your beta access code:</strong></p>
          
          <div class="code-box">
            <div class="code">${betaCode}</div>
            <p style="margin: 10px 0 0; color: #64748b; font-size: 14px;">
              Use this code to activate your account
            </p>
          </div>
          
          <p style="text-align: center;">
            <a href="${signupUrl}" class="button">Claim Your Beta Access →</a>
          </p>
          
          <p style="font-size: 14px; color: #64748b; text-align: center;">
            This code expires in 30 days
          </p>
        </div>
        
        <div class="footer">
          <p style="margin: 0;">
            © 2024 CarbonTally. All rights reserved.
          </p>
        </div>
      </body>
    </html>
  `;
};