# backend/routes/logs.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from auth import AuthUser, require_org_member, require_role
from database import get_supabase_client

router = APIRouter(prefix="/api/logs", tags=["Logs"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class LogEntry(BaseModel):
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/")
async def create_log(
    log_data: LogEntry,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Create a new log entry.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        
        now = datetime.now().isoformat()
        
        # Prepare log entry
        entry = {
            'user_id': current_user.user_id,
            'organization_id': org_id,
            'action': log_data.action,
            'resource_type': log_data.resource_type,
            'resource_id': log_data.resource_id,
            'details': log_data.details or {},
            'metadata': {
                **log_data.metadata or {},
                'user_email': current_user.email,
                'user_role': current_user.role,
                'timestamp': now
            },
            'created_at': now
        }
        
        # Insert into activity_logs
        result = supabase.from_('activity_logs') \
            .insert(entry) \
            .execute()
        
        return {
            "success": True,
            "message": "Log entry created",
            "log_id": result.data[0]['id'] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating log: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create log: {str(e)}"
        )

@router.get("/")
async def get_logs(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    action: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Get logs (admin/staff only).
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('activity_logs') \
            .select('*') \
            .order('created_at', desc=True)
        
        if current_user.role != 'admin':
            # Staff can only see logs for their organization
            query = query.eq('organization_id', current_user.organization_id)
        
        if action:
            query = query.eq('action', action)
        if resource_type:
            query = query.eq('resource_type', resource_type)
        
        # Get total count
        count_query = query.clone()
        count_result = count_query.select('id', count='exact').execute()
        total = count_result.count or 0
        
        # Get paginated results
        result = query.range(offset, offset + limit - 1).execute()
        
        return {
            "success": True,
            "logs": result.data or [],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get logs: {str(e)}"
        )

@router.get("/documents/{file_id}")
async def get_document_logs(
    file_id: str,
    limit: int = Query(50, ge=1, le=500),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get logs for a specific document.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('activity_logs') \
            .select('*') \
            .eq('resource_id', file_id) \
            .eq('resource_type', 'document') \
            .eq('organization_id', current_user.organization_id) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        return {
            "success": True,
            "logs": result.data or [],
            "total": len(result.data or [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document logs: {str(e)}"
        )
# backend/routes/logs.py - Add these new endpoints

@router.get("/analytics/stats")
async def get_log_stats(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get log analytics statistics.
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('activity_logs') \
            .select('action, resource_type, created_at') \
            .eq('organization_id', current_user.organization_id)
        
        if start_date:
            query = query.gte('created_at', start_date)
        if end_date:
            query = query.lte('created_at', end_date)
        
        result = query.execute()
        
        logs = result.data or []
        
        # Calculate statistics
        stats = {
            'total_logs': len(logs),
            'by_action': {},
            'by_resource_type': {},
            'by_hour': {},
            'by_day': {},
            'recent_activity': []
        }
        
        # Group by action
        for log in logs:
            action = log.get('action', 'unknown')
            stats['by_action'][action] = stats['by_action'].get(action, 0) + 1
            
            resource = log.get('resource_type', 'unknown')
            stats['by_resource_type'][resource] = stats['by_resource_type'].get(resource, 0) + 1
            
            created_at = log.get('created_at')
            if created_at:
                try:
                    dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    hour = dt.strftime('%H:00')
                    day = dt.strftime('%Y-%m-%d')
                    stats['by_hour'][hour] = stats['by_hour'].get(hour, 0) + 1
                    stats['by_day'][day] = stats['by_day'].get(day, 0) + 1
                except:
                    pass
        
        # Get recent activity
        recent = supabase.from_('activity_logs') \
            .select('*') \
            .eq('organization_id', current_user.organization_id) \
            .order('created_at', desc=True) \
            .limit(20) \
            .execute()
        
        stats['recent_activity'] = recent.data or []
        
        return {
            "success": True,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting log stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get log stats: {str(e)}"
        )

@router.get("/analytics/errors")
async def get_error_logs(
    limit: int = Query(100, ge=1, le=500),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get error logs for monitoring.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('activity_logs') \
            .select('*') \
            .eq('action', 'error_occurred') \
            .eq('organization_id', current_user.organization_id) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        return {
            "success": True,
            "errors": result.data or [],
            "total": len(result.data or [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting error logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get error logs: {str(e)}"
        )

@router.get("/analytics/users")
async def get_user_activity(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get user activity summary.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('activity_logs') \
            .select('user_id, action, count', count='exact') \
            .eq('organization_id', current_user.organization_id) \
            .group_by('user_id, action') \
            .execute()
        
        # Get user emails
        user_summary = {}
        for item in result.data:
            user_id = item.get('user_id')
            action = item.get('action')
            count = item.get('count', 0)
            
            if user_id not in user_summary:
                # Get user email
                user_result = supabase.from_('auth.users') \
                    .select('email') \
                    .eq('id', user_id) \
                    .maybe_single() \
                    .execute()
                email = user_result.data.get('email') if user_result.data else user_id
                user_summary[user_id] = {
                    'user_id': user_id,
                    'email': email,
                    'actions': {}
                }
            
            user_summary[user_id]['actions'][action] = count
        
        return {
            "success": True,
            "users": list(user_summary.values())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user activity: {str(e)}"
        )