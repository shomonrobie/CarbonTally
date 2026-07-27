# backend/utils/email.py
import os
import resend
from typing import Optional
from datetime import datetime

# Initialize Resend
resend.api_key = os.getenv("RESEND_API_KEY")

async def send_email(
    to: str,
    subject: str,
    html_content: str,
    from_email: str = "CarbonTally <notifications@carbontally.co.uk>"
) -> bool:
    """
    Generic email sending function.
    """
    try:
        response = resend.Emails.send({
            "from": from_email,
            "to": [to],
            "subject": subject,
            "html": html_content,
        })
        print(f"✅ Email sent to {to}: {subject}")
        return True
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False

async def send_invitation_email(
    email: str,
    token: str,
    organization_name: str,
    invited_by: str,
    role: str,
    message: Optional[str] = None
) -> bool:
    """
    Send organization invitation email.
    """
    invite_url = f"https://carbontally.co.uk/accept-invite?token={token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>You're Invited to {organization_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            .message-box {{ background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #10b981; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Organization Invitation</p>
        </div>
        <div class="content">
            <h2>You've been invited! 🎉</h2>
            <p><strong>{invited_by}</strong> has invited you to join <strong>{organization_name}</strong> as a <strong>{role}</strong>.</p>
            {f'<div class="message-box"><strong>📝 Message from {invited_by}:</strong><br>{message}</div>' if message else ''}
            <p>Click the button below to accept the invitation:</p>
            <p style="text-align: center;">
                <a href="{invite_url}" class="button">Accept Invitation →</a>
            </p>
            <p style="font-size: 14px; color: #64748b; text-align: center;">
                This invitation will expire in 7 days.
            </p>
        </div>
        <div class="footer">
            <p>© 2024 CarbonTally. All rights reserved.</p>
            <p style="font-size: 12px;">This email was sent to {email}</p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(
        to=email,
        subject=f"Invitation to join {organization_name} on CarbonTally",
        html_content=html_content
    )

async def send_welcome_email(
    email: str,
    full_name: str,
    organization_name: str
) -> bool:
    """
    Send welcome email to new user.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Welcome to CarbonTally!</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Welcome Aboard!</p>
        </div>
        <div class="content">
            <h2>Welcome, {full_name}! 👋</h2>
            <p>You've successfully joined <strong>{organization_name}</strong> on CarbonTally.</p>
            <p>Here's what you can do next:</p>
            <ul>
                <li>📊 Track your organization's carbon emissions</li>
                <li>📈 Generate compliance reports (SECR, CSRD, ISSB)</li>
                <li>🌱 Upload and process utility bills and fuel data</li>
                <li>🎯 Set and track sustainability goals</li>
            </ul>
            <p style="text-align: center;">
                <a href="https://carbontally.co.uk/dashboard" class="button">Go to Dashboard →</a>
            </p>
        </div>
        <div class="footer">
            <p>© 2024 CarbonTally. All rights reserved.</p>
            <p style="font-size: 12px;">This email was sent to {email}</p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(
        to=email,
        subject=f"Welcome to CarbonTally! 🎉",
        html_content=html_content
    )

async def send_password_reset_email(
    email: str,
    reset_token: str
) -> bool:
    """
    Send password reset email.
    """
    reset_url = f"https://carbontally.co.uk/reset-password?token={reset_token}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Reset Your Password</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            .warning {{ background: #fef3c7; padding: 12px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 15px 0; color: #92400e; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Password Reset</p>
        </div>
        <div class="content">
            <h2>Reset Your Password</h2>
            <p>We received a request to reset your CarbonTally password.</p>
            <p>Click the button below to set a new password:</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">Reset Password →</a>
            </p>
            <div class="warning">
                <strong>⚠️ Security Notice:</strong> This link will expire in 1 hour. If you didn't request this, please ignore this email.
            </div>
            <p style="font-size: 14px; color: #64748b; text-align: center;">
                For security, never share this link with anyone.
            </p>
        </div>
        <div class="footer">
            <p>© 2024 CarbonTally. All rights reserved.</p>
            <p style="font-size: 12px;">This email was sent to {email}</p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(
        to=email,
        subject="Reset Your CarbonTally Password",
        html_content=html_content
    )

async def send_emission_report_email(
    email: str,
    report_type: str,
    organization_name: str,
    year: int,
    total_emissions: float,
    report_url: str
) -> bool:
    """
    Send emission report ready notification.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Your {report_type} Report is Ready</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
            .stats {{ background: #f1f5f9; padding: 20px; border-radius: 8px; margin: 15px 0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Report Ready</p>
        </div>
        <div class="content">
            <h2>Your Report is Ready! 📊</h2>
            <p>Your <strong>{report_type}</strong> report for <strong>{organization_name}</strong> ({year}) has been generated.</p>
            
            <div class="stats">
                <h3 style="margin-top: 0;">📈 Summary</h3>
                <p><strong>Total Emissions:</strong> {total_emissions:,.2f} tonnes CO₂e</p>
                <p><strong>Reporting Year:</strong> {year}</p>
                <p><strong>Report Type:</strong> {report_type}</p>
            </div>
            
            <p>Click the button below to view and download your report:</p>
            <p style="text-align: center;">
                <a href="{report_url}" class="button">View Report →</a>
            </p>
        </div>
        <div class="footer">
            <p>© 2024 CarbonTally. All rights reserved.</p>
            <p style="font-size: 12px;">This email was sent to {email}</p>
        </div>
    </body>
    </html>
    """
    
    return await send_email(
        to=email,
        subject=f"Your {report_type} Report is Ready",
        html_content=html_content
    )