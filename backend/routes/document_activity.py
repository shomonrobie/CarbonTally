# backend/routes/documents/activity.py
"""
Document activity and customer review endpoints.
"""

import json  # ✅ Added missing import
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import Response  # ✅ Added missing import
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from auth import (
    AuthUser,
    require_auth,
    require_org_member,
    require_org_member_or_internal_staff,
    require_admin,
)
from database import get_supabase_client

router = APIRouter(prefix="/api/documents", tags=["Documents - Activity"])

# ==========================================
# Pydantic Models
# ==========================================

class CustomerReviewResponse(BaseModel):
    status: str  # approved, rejected, needs_revision
    notes: Optional[str] = None

# ==========================================
# Document Activity Endpoints
# ==========================================

@router.get("/{file_id}/activity")
async def get_document_activity(
    file_id: str,
    current_user: AuthUser = Depends(require_org_member_or_internal_staff()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get activity log for a specific document."""
    try:
        supabase = get_supabase_client()
        
        # Check document exists and user has access
        doc = supabase.from_('organization_files') \
            .select('organization_id') \
            .eq('id', file_id) \
            .maybe_single() \
            .execute()
        
        if not doc.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check organization access
        if not current_user.is_admin:
            member = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', doc.data['organization_id']) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this document"
                )
        
        # Get activity logs
        result = supabase.from_('document_activity_log') \
            .select('*, users!left(email)') \
            .eq('file_id', file_id) \
            .order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document activity: {str(e)}"
        )

@router.get("/{file_id}/activity/export")
async def export_document_activity(
    file_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """Export document activity logs as CSV."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('document_activity_log') \
            .select('*, users!left(email)') \
            .eq('file_id', file_id) \
            .order('created_at', desc=True) \
            .execute()
        
        if not result.data:
            return {
                "success": True,
                "message": "No activity data to export"
            }
        
        # Generate CSV
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = ['id', 'file_id', 'organization_id', 'user_id', 'user_email', 
                  'action', 'details', 'ip_address', 'user_agent', 'created_at']
        writer.writerow(headers)
        
        for record in result.data:
            row = [
                record.get('id', ''),
                record.get('file_id', ''),
                record.get('organization_id', ''),
                record.get('user_id', ''),
                record.get('users', {}).get('email', '') if record.get('users') else '',
                record.get('action', ''),
                json.dumps(record.get('details', {})),  # ✅ json is now imported
                record.get('ip_address', ''),
                record.get('user_agent', ''),
                record.get('created_at', '')
            ]
            writer.writerow(row)
        
        return Response(  # ✅ Response is now imported
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=document_activity_{file_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export document activity: {str(e)}"
        )

# ==========================================
# Customer Review Endpoints
# ==========================================
#
# F3 (D-7) — the three handlers below were gated only by ``require_auth()``, and
# ``/{file_id}/reviews`` additionally never checked that the document belongs to
# the caller's organisation (the "# Check access" comment sat above a bare
# document lookup). They now use the organisation guard
# (``require_org_member_or_internal_staff()``: membership + the D-7 lifecycle
# decision, an INACTIVE organisation grants nothing) and ``/{file_id}/reviews``
# applies the same document-access check ``/{file_id}/activity`` already
# applies. The guard is the staff-aware variant (G2) because the plain
# ``require_org_member()`` membership test also refused CarbonTally INTERNAL
# staff, whom every other organisation guard exempts for operational oversight.
# The two ``require_admin()`` routes in this module
# (``/{file_id}/activity/export`` and ``/admin/reviews/customer``) stay
# internal-staff-only — D-7 exempts internal staff operational oversight.

@router.get("/{file_id}/reviews")
async def get_document_reviews(
    file_id: str,
    current_user: AuthUser = Depends(require_org_member_or_internal_staff()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get customer reviews for a document."""
    try:
        supabase = get_supabase_client()
        
        # Check the document exists (its organisation is the tenant boundary
        # enforced below, by the same membership lookup ``/{file_id}/activity``
        # uses — a foreign tenant's error must not disclose the document).
        doc = supabase.from_('organization_files') \
            .select('organization_id') \
            .eq('id', file_id) \
            .maybe_single() \
            .execute()
        
        if not doc.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # F3 (D-7) — organisation access: a caller who is not a member of the
        # document's organisation must not read its reviews. This is the check
        # ``/{file_id}/activity`` already applies (same message); before F3 this
        # handler read ``customer_review_log`` for ANY file id.
        if not current_user.is_admin:
            member = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', doc.data['organization_id']) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()

            if not member.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this document"
                )

        # Get reviews
        result = supabase.from_('customer_review_log') \
            .select('*, users!left(email)') \
            .eq('file_id', file_id) \
            .order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document reviews: {str(e)}"
        )

@router.post("/{file_id}/review/response")
async def respond_to_review(
    file_id: str,
    response: CustomerReviewResponse,
    current_user: AuthUser = Depends(require_org_member_or_internal_staff())
):
    """Submit customer review response."""
    try:
        supabase = get_supabase_client()
        
        # Check document exists
        doc = supabase.from_('organization_files') \
            .select('id, organization_id, status') \
            .eq('id', file_id) \
            .maybe_single() \
            .execute()
        
        if not doc.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Check if user has access to this organization
        if not current_user.is_admin:
            member = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', doc.data['organization_id']) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to review this document"
                )
        
        # Create review response
        data = {
            'file_id': file_id,
            'organization_id': doc.data['organization_id'],
            'user_id': current_user.user_id,
            'status': response.status,
            'notes': response.notes,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('customer_review_log') \
            .insert(data) \
            .execute()
        
        # Update document status
        if response.status == 'approved':
            status_update = {'status': 'approved', 'approved_at': datetime.utcnow().isoformat()}
        elif response.status == 'rejected':
            status_update = {'status': 'rejected', 'rejected_at': datetime.utcnow().isoformat()}
        else:
            status_update = {'status': 'review_ready'}
        
        supabase.from_('organization_files') \
            .update(status_update) \
            .eq('id', file_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Review response submitted successfully",
            "data": result.data[0] if result.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit review response: {str(e)}"
        )

# ==========================================
# Organization Document Activity
# ==========================================

@router.get("/organizations/{org_id}/documents/activity")
async def get_organization_document_activity(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member()),  # ✅ require_org_member is imported
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get document activity for an organization."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('document_activity_log') \
            .select('*, users!left(email), organization_files!left(name, file_type)') \
            .eq('organization_id', org_id) \
            .order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization document activity: {str(e)}"
        )

@router.get("/admin/reviews/customer")
async def get_customer_reviews_admin(
    current_user: AuthUser = Depends(require_admin()),
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get all customer reviews (admin only)."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('customer_review_log') \
            .select('*, users!left(email), organization_files!left(name)')
        
        if status:
            query = query.eq('status', status)
        
        result = query.order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer reviews: {str(e)}"
        )