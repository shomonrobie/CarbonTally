# backend/routes/admin/email_templates.py
"""
Email template management endpoints for CarbonTally.
Allows admin to create, update, and manage email templates.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from auth import AuthUser, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/email/templates", tags=["Admin - Email Templates"])

# ==========================================
# Pydantic Models
# ==========================================

class EmailTemplateCreate(BaseModel):
    """Model for creating a new email template."""
    name: str
    subject: str
    body: str
    type: str  # welcome, invitation, password_reset, report_ready, beta_invite, feedback_ack, review_complete, bulk_invite_summary
    variables: Optional[List[str]] = None
    is_active: bool = True
    description: Optional[str] = None

class EmailTemplateUpdate(BaseModel):
    """Model for updating an existing email template."""
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    type: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class EmailTemplatePreview(BaseModel):
    """Model for previewing an email template with variables."""
    variables: Dict[str, str]

class EmailTemplateResponse(BaseModel):
    """Model for email template response."""
    id: str
    name: str
    subject: str
    body: str
    type: str
    variables: Optional[List[str]]
    is_active: bool
    description: Optional[str]
    created_at: str
    updated_at: Optional[str]
    created_by: Optional[str]
    updated_by: Optional[str]

# ==========================================
# Default Templates
# ==========================================

DEFAULT_TEMPLATES = [
    {
        "name": "Welcome Email",
        "subject": "Welcome to CarbonTally! 🎉",
        "type": "welcome",
        "variables": ["full_name", "organization_name"],
        "description": "Sent to new users when they join CarbonTally",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Welcome to CarbonTally</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }
        .content { background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }
        .button { display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }
        .footer { background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }
        .feature { padding: 10px 0; border-bottom: 1px solid #e2e8f0; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌱 CarbonTally</h1>
        <p style="opacity: 0.8;">Welcome Aboard!</p>
    </div>
    <div class="content">
        <h2>Welcome, {{full_name}}! 👋</h2>
        <p>You've successfully joined <strong>{{organization_name}}</strong> on CarbonTally.</p>
        <p>Here's what you can do next:</p>
        <div class="feature">📊 Track your organization's carbon emissions</div>
        <div class="feature">📈 Generate compliance reports (SECR, CSRD, ISSB)</div>
        <div class="feature">🌱 Upload and process utility bills and fuel data</div>
        <div class="feature">🎯 Set and track sustainability goals</div>
        <p style="text-align: center; margin-top: 20px;">
            <a href="https://carbontally.co.uk/dashboard" class="button">Go to Dashboard →</a>
        </p>
    </div>
    <div class="footer">
        <p>© 2024 CarbonTally. All rights reserved.</p>
        <p style="font-size: 12px;">This email was sent to {{email}}</p>
    </div>
</body>
</html>
        """
    },
    {
        "name": "Organization Invitation",
        "subject": "You're Invited to {{organization_name}}",
        "type": "invitation",
        "variables": ["invited_by", "organization_name", "role", "invite_url", "message"],
        "description": "Sent when a user is invited to join an organization",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>You're Invited to {{organization_name}}</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }
        .content { background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }
        .button { display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }
        .footer { background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }
        .message-box { background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #10b981; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌱 CarbonTally</h1>
        <p style="opacity: 0.8;">Organization Invitation</p>
    </div>
    <div class="content">
        <h2>You've been invited! 🎉</h2>
        <p><strong>{{invited_by}}</strong> has invited you to join <strong>{{organization_name}}</strong> as a <strong>{{role}}</strong>.</p>
        {% if message %}
        <div class="message-box"><strong>📝 Message from {{invited_by}}:</strong><br>{{message}}</div>
        {% endif %}
        <p>Click the button below to accept the invitation:</p>
        <p style="text-align: center;">
            <a href="{{invite_url}}" class="button">Accept Invitation →</a>
        </p>
        <p style="font-size: 14px; color: #64748b; text-align: center;">
            This invitation will expire in 7 days.
        </p>
    </div>
    <div class="footer">
        <p>© 2024 CarbonTally. All rights reserved.</p>
        <p style="font-size: 12px;">This email was sent to {{email}}</p>
    </div>
</body>
</html>
        """
    },
    {
        "name": "Password Reset",
        "subject": "Reset Your CarbonTally Password",
        "type": "password_reset",
        "variables": ["reset_url"],
        "description": "Sent when a user requests a password reset",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Reset Your Password</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }
        .content { background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }
        .button { display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }
        .footer { background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }
        .warning { background: #fef3c7; padding: 12px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 15px 0; color: #92400e; }
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
            <a href="{{reset_url}}" class="button">Reset Password →</a>
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
        <p style="font-size: 12px;">This email was sent to {{email}}</p>
    </div>
</body>
</html>
        """
    },
    {
        "name": "Report Ready",
        "subject": "Your {{report_type}} Report is Ready",
        "type": "report_ready",
        "variables": ["report_type", "organization_name", "year", "total_emissions", "report_url"],
        "description": "Sent when a report is ready for download",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Your {{report_type}} Report is Ready</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }
        .content { background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }
        .button { display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }
        .stats { background: #f1f5f9; padding: 20px; border-radius: 8px; margin: 15px 0; }
        .footer { background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌱 CarbonTally</h1>
        <p style="opacity: 0.8;">Report Ready</p>
    </div>
    <div class="content">
        <h2>Your Report is Ready! 📊</h2>
        <p>Your <strong>{{report_type}}</strong> report for <strong>{{organization_name}}</strong> ({{year}}) has been generated.</p>
        <div class="stats">
            <h3 style="margin-top: 0;">📈 Summary</h3>
            <p><strong>Total Emissions:</strong> {{total_emissions}} tonnes CO₂e</p>
            <p><strong>Reporting Year:</strong> {{year}}</p>
            <p><strong>Report Type:</strong> {{report_type}}</p>
        </div>
        <p style="text-align: center;">
            <a href="{{report_url}}" class="button">View Report →</a>
        </p>
    </div>
    <div class="footer">
        <p>© 2024 CarbonTally. All rights reserved.</p>
        <p style="font-size: 12px;">This email was sent to {{email}}</p>
    </div>
</body>
</html>
        """
    },
    {
        "name": "Beta Invite",
        "subject": "You're Invited to CarbonTally Beta! 🚀",
        "type": "beta_invite",
        "variables": ["beta_code", "invited_by", "signup_url"],
        "description": "Sent when a user is invited to the beta program",
        "body": """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>You're Invited to CarbonTally Beta</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }
        .content { background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }
        .button { display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }
        .code-box { background: #1e293b; color: #10b981; padding: 15px; border-radius: 8px; font-size: 24px; font-weight: bold; text-align: center; letter-spacing: 4px; margin: 15px 0; }
        .footer { background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🌱 CarbonTally</h1>
        <p style="opacity: 0.8;">Beta Access Invitation</p>
    </div>
    <div class="content">
        <h2>You've been invited to the Beta! 🚀</h2>
        <p><strong>{{invited_by}}</strong> has invited you to join the CarbonTally beta program.</p>
        <p>Your beta access code is:</p>
        <div class="code-box">{{beta_code}}</div>
        <p style="text-align: center;">
            <a href="{{signup_url}}" class="button">Join Beta →</a>
        </p>
        <p style="font-size: 14px; color: #64748b; text-align: center;">
            This invite will expire in 30 days.
        </p>
    </div>
    <div class="footer">
        <p>© 2024 CarbonTally. All rights reserved.</p>
        <p style="font-size: 12px;">This email was sent to {{email}}</p>
    </div>
</body>
</html>
        """
    }
]

# ==========================================
# Helper Functions
# ==========================================

async def get_default_templates(supabase):
    """Get default templates from database or create them."""
    result = supabase.from_('email_templates') \
        .select('id') \
        .limit(1) \
        .execute()
    
    # If no templates exist, create defaults
    if not result.data:
        for template in DEFAULT_TEMPLATES:
            data = {
                'name': template['name'],
                'subject': template['subject'],
                'body': template['body'],
                'type': template['type'],
                'variables': template.get('variables', []),
                'is_active': True,
                'description': template.get('description', ''),
                'created_at': datetime.utcnow().isoformat()
            }
            supabase.from_('email_templates').insert(data).execute()
        
        # Get the newly created templates
        result = supabase.from_('email_templates') \
            .select('*') \
            .execute()
    
    return result.data if result.data else []

# ==========================================
# Endpoints
# ==========================================

@router.get("")
async def get_email_templates(
    current_user: AuthUser = Depends(require_admin()),
    type: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all email templates.
    Admin only - view and manage email templates.
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('email_templates').select('*')
        
        if type:
            query = query.eq('type', type)
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        result = query.order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # If no templates exist, return defaults
        if not result.data:
            defaults = await get_default_templates(supabase)
            return {
                "success": True,
                "data": defaults,
                "total": len(defaults),
                "message": "Default templates loaded"
            }
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email templates: {str(e)}"
        )

@router.get("/{template_id}")
async def get_email_template(
    template_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """
    Get email template by ID.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('email_templates') \
            .select('*') \
            .eq('id', template_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email template not found"
            )
        
        return {"success": True, "data": result.data}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email template: {str(e)}"
        )

@router.post("")
async def create_email_template(
    template: EmailTemplateCreate,
    current_user: AuthUser = Depends(require_admin())
):
    """
    Create a new email template.
    """
    try:
        supabase = get_supabase_client()
        
        data = template.dict()
        data['created_at'] = datetime.utcnow().isoformat()
        data['updated_at'] = datetime.utcnow().isoformat()
        data['created_by'] = current_user.user_id
        
        result = supabase.from_('email_templates') \
            .insert(data) \
            .execute()
        
        return {
            "success": True,
            "message": "Email template created successfully",
            "data": result.data[0] if result.data else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create email template: {str(e)}"
        )

@router.put("/{template_id}")
async def update_email_template(
    template_id: str,
    template: EmailTemplateUpdate,
    current_user: AuthUser = Depends(require_admin())
):
    """
    Update an email template.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if template exists
        existing = supabase.from_('email_templates') \
            .select('id') \
            .eq('id', template_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email template not found"
            )
        
        data = template.dict(exclude_none=True)
        data['updated_at'] = datetime.utcnow().isoformat()
        data['updated_by'] = current_user.user_id
        
        result = supabase.from_('email_templates') \
            .update(data) \
            .eq('id', template_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Email template updated successfully",
            "data": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update email template: {str(e)}"
        )

@router.delete("/{template_id}")
async def delete_email_template(
    template_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """
    Delete an email template.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if template exists
        existing = supabase.from_('email_templates') \
            .select('id') \
            .eq('id', template_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email template not found"
            )
        
        result = supabase.from_('email_templates') \
            .delete() \
            .eq('id', template_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Email template deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete email template: {str(e)}"
        )

@router.post("/{template_id}/preview")
async def preview_email_template(
    template_id: str,
    preview_data: EmailTemplatePreview,
    current_user: AuthUser = Depends(require_admin())
):
    """
    Preview an email template with variables.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('email_templates') \
            .select('*') \
            .eq('id', template_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email template not found"
            )
        
        template = result.data
        subject = template['subject']
        body = template['body']
        
        # Replace variables
        variables = preview_data.variables
        for key, value in variables.items():
            subject = subject.replace(f'{{{{{key}}}}}', str(value))
            body = body.replace(f'{{{{{key}}}}}', str(value))
        
        return {
            "success": True,
            "data": {
                "subject": subject,
                "body": body,
                "variables_used": variables
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview email template: {str(e)}"
        )

@router.post("/reset-defaults")
async def reset_to_default_templates(
    current_user: AuthUser = Depends(require_admin())
):
    """
    Reset all templates to default values.
    Warning: This will overwrite all existing templates!
    """
    try:
        supabase = get_supabase_client()
        
        # Delete all existing templates
        supabase.from_('email_templates').delete().execute()
        
        # Insert default templates
        for template in DEFAULT_TEMPLATES:
            data = {
                'name': template['name'],
                'subject': template['subject'],
                'body': template['body'],
                'type': template['type'],
                'variables': template.get('variables', []),
                'is_active': True,
                'description': template.get('description', ''),
                'created_at': datetime.utcnow().isoformat(),
                'created_by': current_user.user_id
            }
            supabase.from_('email_templates').insert(data).execute()
        
        # Get all templates
        result = supabase.from_('email_templates') \
            .select('*') \
            .execute()
        
        return {
            "success": True,
            "message": "All templates reset to defaults",
            "data": result.data,
            "total": len(result.data)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset templates: {str(e)}"
        )

@router.get("/types")
async def get_template_types(
    current_user: AuthUser = Depends(require_admin())
):
    """
    Get all available template types.
    """
    try:
        # Define available types
        types = [
            {"value": "welcome", "label": "Welcome Email"},
            {"value": "invitation", "label": "Organization Invitation"},
            {"value": "password_reset", "label": "Password Reset"},
            {"value": "report_ready", "label": "Report Ready"},
            {"value": "beta_invite", "label": "Beta Invite"},
            {"value": "feedback_ack", "label": "Feedback Acknowledgement"},
            {"value": "review_complete", "label": "Review Complete"},
            {"value": "bulk_invite_summary", "label": "Bulk Invite Summary"},
            {"value": "payment_confirmation", "label": "Payment Confirmation"},
            {"value": "subscription_renewal", "label": "Subscription Renewal"},
        ]
        
        return {
            "success": True,
            "data": types
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template types: {str(e)}"
        )