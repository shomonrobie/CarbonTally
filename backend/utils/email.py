# backend/utils/email.py
"""
Email utilities for CarbonTally
"""

import os
import resend
from typing import Optional, Dict, Any
from datetime import datetime
import json

# Initialize Resend
resend.api_key = os.getenv("RESEND_API_KEY")

# ==========================================
# Core Email Functions
# ==========================================

async def send_email(
    to: str,
    subject: str,
    html_content: str,
    from_email: str = "CarbonTally <notifications@carbontally.co.uk>"
) -> bool:
    """Generic email sending function."""
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

# ==========================================
# Template Rendering Functions
# ==========================================

def render_template(template: Dict[str, Any], variables: Dict[str, str]) -> str:
    """
    Render an email template with variables.
    """
    content = template.get('body', '')
    for key, value in variables.items():
        content = content.replace(f'{{{{{key}}}}}', str(value))
    return content

def render_template_subject(template: Dict[str, Any], variables: Dict[str, str]) -> str:
    """
    Render an email template subject with variables.
    """
    subject = template.get('subject', '')
    for key, value in variables.items():
        subject = subject.replace(f'{{{{{key}}}}}', str(value))
    return subject

# ==========================================
# Template-Based Email Functions
# ==========================================

async def send_email_from_db_template(
    supabase,
    to: str,
    template_type: str,
    variables: Dict[str, str],
    from_email: str = "CarbonTally <notifications@carbontally.co.uk>"
) -> bool:
    """
    Send an email using a template from the database.
    """
    try:
        # Get template from database
        result = supabase.from_('email_templates') \
            .select('*') \
            .eq('type', template_type) \
            .eq('is_active', True) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            print(f"❌ Template not found: {template_type}")
            return False
        
        template = result.data
        
        # Replace variables
        subject = template['subject']
        body = template['body']
        
        for key, value in variables.items():
            subject = subject.replace(f'{{{{{key}}}}}', str(value))
            body = body.replace(f'{{{{{key}}}}}', str(value))
        
        return await send_email(
            to=to,
            subject=subject,
            html_content=body,
            from_email=from_email
        )
        
    except Exception as e:
        print(f"❌ Template email error: {e}")
        return False

# ==========================================
# Specific Email Functions
# ==========================================

async def send_invitation_email(
    supabase,
    email: str,
    token: str,
    organization_name: str,
    invited_by: str,
    role: str,
    message: Optional[str] = None
) -> bool:
    """
    Send organization invitation email.
    Uses database template if available, otherwise falls back to inline.
    """
    invite_url = f"https://carbontally.co.uk/accept-invite?token={token}"
    
    # Try database template first
    try:
        return await send_email_from_db_template(
            supabase,
            email,
            "invitation",
            {
                "invited_by": invited_by,
                "organization_name": organization_name,
                "role": role,
                "invite_url": invite_url,
                "message": message or "",
                "email": email
            }
        )
    except Exception:
        # Fallback to inline template
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
    supabase,
    email: str,
    full_name: str,
    organization_name: str
) -> bool:
    """
    Send welcome email to new user.
    """
    # Try database template first
    try:
        return await send_email_from_db_template(
            supabase,
            email,
            "welcome",
            {
                "full_name": full_name,
                "organization_name": organization_name,
                "email": email
            }
        )
    except Exception:
        # Fallback to inline template
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

async def send_beta_invite_email(
    email: str,
    beta_code: str,
    invited_by: str
) -> bool:
    """
    Send beta access invitation email.
    """
    signup_url = f"https://carbontally.co.uk/beta/signup?code={beta_code}"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>You're Invited to CarbonTally Beta</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
            .code-box {{ background: #1e293b; color: #10b981; padding: 15px; border-radius: 8px; font-size: 24px; font-weight: bold; text-align: center; letter-spacing: 4px; margin: 15px 0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Beta Access Invitation</p>
        </div>
        <div class="content">
            <h2>You've been invited to the Beta! 🚀</h2>
            <p><strong>{invited_by}</strong> has invited you to join the CarbonTally beta program.</p>
            <p>Your beta access code is:</p>
            <div class="code-box">{beta_code}</div>
            <p style="text-align: center;">
                <a href="{signup_url}" class="button">Join Beta →</a>
            </p>
            <p style="font-size: 14px; color: #64748b; text-align: center;">
                This invite will expire in 30 days.
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
        subject="You're Invited to CarbonTally Beta! 🚀",
        html_content=html_content
    )

async def send_feedback_acknowledgement_email(
    email: str,
    feedback_type: str,
    title: str
) -> bool:
    """
    Send feedback acknowledgement email.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Thank You for Your Feedback</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            .feedback-box {{ background: #f1f5f9; padding: 15px; border-radius: 8px; border-left: 4px solid #10b981; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Feedback Received</p>
        </div>
        <div class="content">
            <h2>Thank You! 🙏</h2>
            <p>Thank you for your <strong>{feedback_type}</strong> feedback:</p>
            <div class="feedback-box">
                <strong>Title:</strong> {title}
            </div>
            <p>Our team will review your feedback and get back to you if we need more information.</p>
            <p>Your input helps us make CarbonTally better for everyone!</p>
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
        subject="Thank You for Your Feedback! 🙏",
        html_content=html_content
    )

async def send_review_completion_email(
    email: str,
    document_name: str,
    status: str,
    notes: Optional[str] = None
) -> bool:
    """
    Send document review completion email.
    """
    status_emoji = "✅" if status == "approved" else "❌"
    status_text = "Approved" if status == "approved" else "Rejected"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Document Review Complete</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            .status-box {{ padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center; font-size: 18px; font-weight: bold; }}
            .approved {{ background: #d1fae5; color: #065f46; border: 2px solid #10b981; }}
            .rejected {{ background: #fee2e2; color: #991b1b; border: 2px solid #ef4444; }}
            .notes-box {{ background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Document Review Complete</p>
        </div>
        <div class="content">
            <h2>Review Complete {status_emoji}</h2>
            <p>Your document <strong>"{document_name}"</strong> has been reviewed.</p>
            
            <div class="status-box {status}">
                {status_emoji} {status_text}
            </div>
            
            {f'<div class="notes-box"><strong>📝 Reviewer Notes:</strong><br>{notes}</div>' if notes else ''}
            
            <p>You can view the full review details in your dashboard.</p>
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
        subject=f"Document Review {status_text} - {document_name}",
        html_content=html_content
    )

async def send_bulk_invite_summary_email(
    email: str,
    organization_name: str,
    successful_invites: int,
    failed_invites: int
) -> bool:
    """
    Send bulk invite summary email.
    """
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Bulk Invite Summary</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            .stats {{ display: flex; justify-content: space-around; padding: 20px; }}
            .stat-item {{ text-align: center; }}
            .stat-number {{ font-size: 32px; font-weight: bold; color: #0f172a; }}
            .stat-label {{ color: #64748b; font-size: 14px; }}
            .success {{ color: #10b981; }}
            .failed {{ color: #ef4444; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Bulk Invite Summary</p>
        </div>
        <div class="content">
            <h2>Bulk Invite Completed 📊</h2>
            <p>Your bulk invitation to <strong>{organization_name}</strong> has been processed.</p>
            
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number success">{successful_invites}</div>
                    <div class="stat-label">✅ Successful</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number failed">{failed_invites}</div>
                    <div class="stat-label">❌ Failed</div>
                </div>
            </div>
            
            <p style="text-align: center; font-size: 14px; color: #64748b;">
                View full details in your dashboard.
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
        subject=f"Bulk Invite Summary - {organization_name}",
        html_content=html_content
    )

# ==========================================
# Email Logging Helper
# ==========================================

async def log_email(
    supabase,
    email: str,
    email_type: str,
    status: str,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log email send attempts to the database.
    """
    try:
        log_data = {
            'email': email,
            'type': email_type,
            'status': status,
            'error_message': error_message,
            'metadata': metadata or {},
            'created_at': datetime.utcnow().isoformat()
        }
        
        supabase.from_('email_logs') \
            .insert(log_data) \
            .execute()
    except Exception as e:
        print(f"⚠️ Failed to log email: {e}")

# ==========================================
# Email Validation Helper
# ==========================================

def validate_email(email: str) -> bool:
    """
    Basic email validation.
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))