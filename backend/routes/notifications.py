# backend/routes/notifications.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from auth import AuthUser, require_auth, require_org_admin, require_org_member, require_permission, require_role
from database import get_supabase_client
import resend
import os

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class CustomerManualExtractionRequest(BaseModel):
    """Request model for customer manual extraction notification."""
    review_id: str = Field(..., description="ID of the review queue item")
    organization_id: str = Field(..., description="Organization ID")
    file_name: str = Field(..., description="Name of the processed file")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "review_id": "550e8400-e29b-41d4-a716-446655440000",
                "organization_id": "2b7a2e09-2cc3-461e-84e6-81137eb63ab3",
                "file_name": "utility_bill_jan2024.pdf"
            }
        }

class BatchCompletionRequest(BaseModel):
    """Request model for batch completion notification."""
    batch_id: str = Field(..., description="ID of the batch")
    organization_id: str = Field(..., description="Organization ID")
    customer_email: Optional[EmailStr] = Field(None, description="Customer email (optional)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                "organization_id": "2b7a2e09-2cc3-461e-84e6-81137eb63ab3"
            }
        }

class StaffNotificationRequest(BaseModel):
    """Request model for staff notification."""
    subject: str = Field(..., description="Email subject")
    message: str = Field(..., description="Email message")
    staff_emails: Optional[List[EmailStr]] = Field(None, description="List of staff emails")
    role_filter: Optional[str] = Field(None, description="Filter staff by role")
    
    class Config:
        json_schema_extra = {
            "example": {
                "subject": "New Batch Ready for Review",
                "message": "A new batch has been uploaded and requires review.",
                "role_filter": "data_approver"
            }
        }

class NotificationResponse(BaseModel):
    """Response model for notifications."""
    success: bool
    message: str
    recipients: Optional[List[str]] = None
    sent_count: Optional[int] = None
    error: Optional[str] = None

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def send_email(to: str, subject: str, html_content: str, from_email: str = "CarbonTally <notifications@carbontally.co.uk>") -> bool:
    """
    Generic email sending function using Resend.
    """
    try:
        resend.api_key = os.getenv("RESEND_API_KEY")
        
        if not resend.api_key:
            print("⚠️ RESEND_API_KEY not set, skipping email")
            return False
        
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

async def get_customer_email(supabase_client, organization_id: str) -> Optional[str]:
    """Get customer email from organization."""
    try:
        # Try to get from organization members
        result = supabase_client.from_('organization_members') \
            .select('users!inner (email)') \
            .eq('organization_id', organization_id) \
            .eq('role', 'admin') \
            .limit(1) \
            .execute()
        
        if result.data and result.data[0].get('users'):
            return result.data[0]['users']['email']
        
        # Fallback: get from organization table
        org_result = supabase_client.from_('organizations') \
            .select('primary_contact_email') \
            .eq('id', organization_id) \
            .maybe_single() \
            .execute()
        
        if org_result.data and org_result.data.get('primary_contact_email'):
            return org_result.data['primary_contact_email']
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error getting customer email: {e}")
        return None

async def get_staff_emails(supabase_client, role_filter: Optional[str] = None) -> List[str]:
    """Get staff emails from staff_profiles."""
    try:
        query = supabase_client.from_('staff_profiles') \
            .select('email') \
            .eq('is_active', True)
        
        if role_filter:
            query = query.eq('role', role_filter)
        
        result = query.execute()
        
        return [s['email'] for s in result.data if s.get('email')]
        
    except Exception as e:
        print(f"⚠️ Error getting staff emails: {e}")
        return []

def get_manual_extraction_email_html(file_name: str, review_id: str, organization_name: str = "Your Organization") -> str:
    """Generate HTML for manual extraction notification email."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Your Document Has Been Processed</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            .info-box {{ background: #f1f5f9; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #10b981; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Document Processed Successfully</p>
        </div>
        <div class="content">
            <h2>✅ Your Document Has Been Processed</h2>
            <p>Great news! Our team has manually reviewed and extracted the data from your uploaded document:</p>
            
            <div class="info-box">
                <p style="margin: 0.5rem 0;"><strong>📄 Document:</strong> {file_name}</p>
                <p style="margin: 0.5rem 0;"><strong>🏢 Organization:</strong> {organization_name}</p>
                <p style="margin: 0.5rem 0;"><strong>📋 Review ID:</strong> <code style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px;">{review_id}</code></p>
                <p style="margin: 0.5rem 0;"><strong>✅ Status:</strong> <span style="color: #10b981; font-weight: bold;">Ready for Your Review</span></p>
            </div>
            
            <p>The extracted data is now available in your CarbonTally dashboard. Please review it and click "Approve" to commit it to your emissions records.</p>
            
            <p style="text-align: center;">
                <a href="https://carbontally.co.uk/dashboard" class="button">📊 Review & Approve Data →</a>
            </p>
            
            <p style="color: #64748b; font-size: 0.875rem; margin-top: 2rem;">
                If you have any questions or need adjustments, please reply to this email or contact our support team.
            </p>
        </div>
        <div class="footer">
            <p>© 2024 CarbonTally. All rights reserved.</p>
            <p style="font-size: 12px;">This is an automated message. Please do not reply directly to this email.</p>
        </div>
    </body>
    </html>
    """

def get_batch_completion_email_html(batch_name: str, total_files: int, organization_name: str = "Your Organization") -> str:
    """Generate HTML for batch completion notification email."""
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Your Batch Upload Is Ready</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
            .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
            .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
            .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            .stats-box {{ background: #f0fdf4; padding: 15px; border-radius: 8px; margin: 15px 0; border-left: 4px solid #10b981; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🌱 CarbonTally</h1>
            <p style="opacity: 0.8;">Batch Processing Complete</p>
        </div>
        <div class="content">
            <h2>✅ Your Batch Upload Is Ready!</h2>
            <p>Our team has finished manually reviewing and extracting the data from your bulk upload.</p>
            
            <div class="stats-box">
                <p style="margin: 0.5rem 0;"><strong>📦 Batch Name:</strong> {batch_name}</p>
                <p style="margin: 0.5rem 0;"><strong>🏢 Organization:</strong> {organization_name}</p>
                <p style="margin: 0.5rem 0;"><strong>📄 Files Processed:</strong> {total_files} documents</p>
                <p style="margin: 0.5rem 0;"><strong>✅ Status:</strong> <span style="color: #10b981; font-weight: bold;">Ready for Review</span></p>
            </div>
            
            <p>All extracted emissions data has been mapped to your facilities and assets. You can now review the data and generate your SECR compliance report with a single click.</p>
            
            <p style="text-align: center;">
                <a href="https://carbontally.co.uk/dashboard" class="button">📊 Review Data & Generate Report →</a>
            </p>
            
            <p style="color: #64748b; font-size: 0.875rem; margin-top: 2rem;">
                If you notice any discrepancies or need adjustments, simply reply to this email and our support team will assist you.
            </p>
        </div>
        <div class="footer">
            <p>© 2024 CarbonTally. All rights reserved.</p>
            <p style="font-size: 12px;">This is an automated message. Please do not reply directly to this email.</p>
        </div>
    </body>
    </html>
    """

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/customer/manual-extraction", response_model=NotificationResponse)
async def notify_customer_manual_extraction(
    notification_data: CustomerManualExtractionRequest,
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Notify customer that manual extraction is complete.
    Available to admins and staff.
    """
    try:
        supabase = get_supabase_client()
        
        review_id = notification_data.review_id
        organization_id = notification_data.organization_id
        file_name = notification_data.file_name
        
        # Get customer email
        customer_email = notification_data.customer_email
        if not customer_email:
            customer_email = await get_customer_email(supabase, organization_id)
        
        if not customer_email:
            return NotificationResponse(
                success=False,
                message="Customer email not found",
                error="No customer email found for this organization"
            )
        
        # Get organization name
        org_result = supabase.from_('organizations') \
            .select('name') \
            .eq('id', organization_id) \
            .maybe_single() \
            .execute()
        
        organization_name = org_result.data.get('name', 'Your Organization') if org_result.data else 'Your Organization'
        
        # Update review queue status
        supabase.from_('manual_review_queue') \
            .update({
                'customer_notified': True,
                'customer_notified_at': datetime.now().isoformat(),
                'customer_notified_by': current_user.user_id
            }) \
            .eq('id', review_id) \
            .execute()
        
        # Send email
        email_html = get_manual_extraction_email_html(
            file_name=file_name,
            review_id=review_id,
            organization_name=organization_name
        )
        
        email_sent = send_email(
            to=customer_email,
            subject=f"✅ Your Document Has Been Processed: {file_name}",
            html_content=email_html
        )
        
        if email_sent:
            return NotificationResponse(
                success=True,
                message=f"Customer notification sent to {customer_email}",
                recipients=[customer_email],
                sent_count=1
            )
        else:
            return NotificationResponse(
                success=False,
                message="Email failed to send",
                error="Email service error",
                recipients=[customer_email]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sending customer notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

@router.post("/batch/completion", response_model=NotificationResponse)
async def notify_batch_completion(
    notification_data: BatchCompletionRequest,
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Notify customer that batch processing is complete.
    Available to admins and staff.
    """
    try:
        supabase = get_supabase_client()
        
        batch_id = notification_data.batch_id
        organization_id = notification_data.organization_id
        
        # Get batch details
        batch_result = supabase.from_('upload_batches') \
            .select('batch_name, total_files, status') \
            .eq('id', batch_id) \
            .maybe_single() \
            .execute()
        
        if not batch_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        batch_info = batch_result.data
        batch_name = batch_info.get('batch_name', 'Your Documents')
        total_files = batch_info.get('total_files', 0)
        
        # Get customer email
        customer_email = notification_data.customer_email
        if not customer_email:
            customer_email = await get_customer_email(supabase, organization_id)
        
        if not customer_email:
            return NotificationResponse(
                success=False,
                message="Customer email not found",
                error="No customer email found for this organization"
            )
        
        # Get organization name
        org_result = supabase.from_('organizations') \
            .select('name') \
            .eq('id', organization_id) \
            .maybe_single() \
            .execute()
        
        organization_name = org_result.data.get('name', 'Your Organization') if org_result.data else 'Your Organization'
        
        # Update batch status
        supabase.from_('upload_batches') \
            .update({
                'customer_notified': True,
                'customer_notified_at': datetime.now().isoformat(),
                'customer_notified_by': current_user.user_id
            }) \
            .eq('id', batch_id) \
            .execute()
        
        # Send email
        email_html = get_batch_completion_email_html(
            batch_name=batch_name,
            total_files=total_files,
            organization_name=organization_name
        )
        
        email_sent = send_email(
            to=customer_email,
            subject=f"✅ Your Batch Upload Is Ready: {batch_name}",
            html_content=email_html
        )
        
        if email_sent:
            return NotificationResponse(
                success=True,
                message=f"Batch completion email sent to {customer_email}",
                recipients=[customer_email],
                sent_count=1
            )
        else:
            return NotificationResponse(
                success=False,
                message="Email failed to send",
                error="Email service error",
                recipients=[customer_email]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sending batch completion notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

@router.post("/staff", response_model=NotificationResponse)
async def notify_staff(
    notification_data: StaffNotificationRequest,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Send notification to staff members.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # Get staff emails
        staff_emails = notification_data.staff_emails
        if not staff_emails:
            staff_emails = await get_staff_emails(
                supabase,
                notification_data.role_filter
            )
        
        if not staff_emails:
            return NotificationResponse(
                success=False,
                message="No staff emails found",
                error="No staff members with the specified role"
            )
        
        # Build email HTML
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{notification_data.subject}</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
                .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌱 CarbonTally</h1>
                <p style="opacity: 0.8;">Staff Notification</p>
            </div>
            <div class="content">
                <h2>{notification_data.subject}</h2>
                <p>{notification_data.message}</p>
                <p style="color: #64748b; font-size: 0.875rem; margin-top: 2rem;">
                    Sent by: {current_user.email}
                </p>
            </div>
            <div class="footer">
                <p>© 2024 CarbonTally. All rights reserved.</p>
                <p style="font-size: 12px;">This is a staff notification.</p>
            </div>
        </body>
        </html>
        """
        
        # Send to all staff
        sent_count = 0
        failed_emails = []
        
        for email in staff_emails:
            try:
                email_sent = send_email(
                    to=email,
                    subject=notification_data.subject,
                    html_content=html_content
                )
                if email_sent:
                    sent_count += 1
                else:
                    failed_emails.append(email)
            except Exception as email_error:
                print(f"⚠️ Failed to send to {email}: {email_error}")
                failed_emails.append(email)
        
        return NotificationResponse(
            success=sent_count > 0,
            message=f"Sent to {sent_count} staff members",
            recipients=[e for e in staff_emails if e not in failed_emails],
            sent_count=sent_count,
            error=f"Failed: {', '.join(failed_emails)}" if failed_emails else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sending staff notification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send notification: {str(e)}"
        )

@router.get("/templates")
async def get_notification_templates(
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Get available notification templates.
    Available to admins and staff.
    """
    templates = {
        "manual_extraction": {
            "name": "Manual Extraction Complete",
            "description": "Notify customer when manual extraction is complete",
            "variables": ["file_name", "review_id", "organization_name"]
        },
        "batch_completion": {
            "name": "Batch Upload Complete",
            "description": "Notify customer when batch upload is processed",
            "variables": ["batch_name", "total_files", "organization_name"]
        },
        "staff_alert": {
            "name": "Staff Alert",
            "description": "Send alert to staff members",
            "variables": ["subject", "message", "sender"]
        }
    }
    
    return {
        "success": True,
        "templates": templates,
        "total": len(templates)
    }