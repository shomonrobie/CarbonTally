# backend/routes/admin/review_history.py
"""
Review assignment history endpoints for tracking review assignments.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime
from auth import AuthUser, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/reviews", tags=["Admin - Review History"])

@router.get("/{review_id}/history")
async def get_review_history(
    review_id: str,
    current_user: AuthUser = Depends(require_admin()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get assignment history for a specific review."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('review_assignment_history') \
            .select('*, staff_profiles!assigned_to(first_name, last_name, email)') \
            .eq('review_id', review_id) \
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
            detail=f"Failed to get review history: {str(e)}"
        )

@router.get("/history")
async def get_all_review_history(
    current_user: AuthUser = Depends(require_admin()),
    staff_id: Optional[str] = None,
    action: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all review assignment history with filters."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('review_assignment_history') \
            .select('*, staff_profiles!assigned_to(first_name, last_name, email)')
        
        if staff_id:
            query = query.eq('assigned_to', staff_id)
        if action:
            query = query.eq('action', action)
        if start_date:
            query = query.gte('created_at', start_date)
        if end_date:
            query = query.lte('created_at', end_date)
        
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
            detail=f"Failed to get review history: {str(e)}"
        )

@router.get("/history/staff/{staff_id}")
async def get_staff_assignment_history(
    staff_id: str,
    current_user: AuthUser = Depends(require_admin()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get assignment history for a specific staff member."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('review_assignment_history') \
            .select('*, manual_review_queue!review_id(file_name, file_type)') \
            .eq('assigned_to', staff_id) \
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
            detail=f"Failed to get staff assignment history: {str(e)}"
        )

@router.get("/history/audit")
async def get_review_audit_trail(
    current_user: AuthUser = Depends(require_admin()),
    review_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get review audit trail."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('review_audit_trail') \
            .select('*, staff_profiles!performed_by(first_name, last_name, email)')
        
        if review_id:
            query = query.eq('review_id', review_id)
        
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
            detail=f"Failed to get review audit trail: {str(e)}"
        )

@router.get("/history/audit/export")
async def export_review_audit_trail(
    current_user: AuthUser = Depends(require_admin()),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export review audit trail as CSV."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('review_audit_trail') \
            .select('*, staff_profiles!performed_by(first_name, last_name, email)')
        
        if start_date:
            query = query.gte('created_at', start_date)
        if end_date:
            query = query.lte('created_at', end_date)
        
        result = query.order('created_at', desc=True) \
            .limit(10000) \
            .execute()
        
        if not result.data:
            return {
                "success": True,
                "message": "No data to export"
            }
        
        # Generate CSV
        import csv
        import io
        import json
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = ['id', 'review_id', 'action', 'performed_by', 'performed_by_email', 
                  'assigned_to', 'old_value', 'new_value', 'note', 'created_at']
        writer.writerow(headers)
        
        for record in result.data:
            performed_by = record.get('staff_profiles', {})
            row = [
                record.get('id', ''),
                record.get('review_id', ''),
                record.get('action', ''),
                record.get('performed_by', ''),
                performed_by.get('email', '') if performed_by else '',
                record.get('assigned_to', ''),
                json.dumps(record.get('old_value', {})),
                json.dumps(record.get('new_value', {})),
                record.get('note', ''),
                record.get('created_at', '')
            ]
            writer.writerow(row)
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=review_audit_trail_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export review audit trail: {str(e)}"
        )