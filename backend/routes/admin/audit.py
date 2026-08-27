# backend/routes/admin/audit.py
"""
Audit and activity logging endpoints for system monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query, Response  # ✅ Add Response here
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from auth import AuthUser, require_admin, require_auth, require_org_member
from database import get_supabase_client
import csv
import io
import json

router = APIRouter(prefix="/api/admin/audit", tags=["Admin - Audit"])

# ==========================================
# Pydantic Models
# ==========================================

class ActivityFilter(BaseModel):
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# ==========================================
# Activity Log Endpoints
# ==========================================

@router.get("/activity")
async def get_activity_logs(
    current_user: AuthUser = Depends(require_admin()),
    user_id: Optional[str] = None,
    action: Optional[str] = None,
    resource_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get system activity logs."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('activity_logs').select('*')
        
        if user_id:
            query = query.eq('user_id', user_id)
        if action:
            query = query.eq('action', action)
        if resource_type:
            query = query.eq('resource_type', resource_type)
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
            detail=f"Failed to get activity logs: {str(e)}"
        )

@router.get("/activity/{log_id}")
async def get_activity_log_detail(
    log_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """Get detailed activity log entry."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('activity_logs') \
            .select('*') \
            .eq('id', log_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Activity log not found"
            )
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get activity log: {str(e)}"
        )

@router.get("/activity/export")
async def export_activity_logs(
    current_user: AuthUser = Depends(require_admin()),
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    action: Optional[str] = None
):
    """Export activity logs as CSV."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('activity_logs').select('*')
        
        if start_date:
            query = query.gte('created_at', start_date)
        if end_date:
            query = query.lte('created_at', end_date)
        if action:
            query = query.eq('action', action)
        
        result = query.order('created_at', desc=True) \
            .limit(10000) \
            .execute()
        
        if not result.data:
            return {
                "success": True,
                "message": "No data to export"
            }
        
        # Generate CSV
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Headers
        headers = ['id', 'user_id', 'organization_id', 'action', 'resource_type', 
                  'resource_id', 'details', 'ip_address', 'user_agent', 'created_at']
        writer.writerow(headers)
        
        # Data
        for record in result.data:
            row = []
            for header in headers:
                value = record.get(header)
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                elif value is None:
                    value = ""
                row.append(value)
            writer.writerow(row)        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=activity_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export activity logs: {str(e)}"
        )

@router.get("/activity/search")
async def search_activity_logs(
    current_user: AuthUser = Depends(require_admin()),
    search_term: str = Query(..., min_length=1),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Search activity logs."""
    try:
        supabase = get_supabase_client()
        
        # Search across multiple fields
        result = supabase.from_('activity_logs') \
            .select('*') \
            .or_(f"action.ilike.%{search_term}%,details.ilike.%{search_term}%,resource_type.ilike.%{search_term}%") \
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
            detail=f"Failed to search activity logs: {str(e)}"
        )