# backend/routes/admin/logs.py
"""
Processing and email logs endpoints for system monitoring.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from auth import AuthUser, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/logs", tags=["Admin - Logs"])

# ==========================================
# Email Logs Endpoints
# ==========================================

@router.get("/email")
async def get_email_logs(
    current_user: AuthUser = Depends(require_admin()),
    email: Optional[str] = None,
    type: Optional[str] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get email logs."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('email_logs').select('*')
        
        if email:
            query = query.eq('email', email)
        if type:
            query = query.eq('type', type)
        if status:
            query = query.eq('status', status)
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
            detail=f"Failed to get email logs: {str(e)}"
        )

@router.get("/email/{log_id}")
async def get_email_log_detail(
    log_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """Get detailed email log entry."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('email_logs') \
            .select('*') \
            .eq('id', log_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email log not found"
            )
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email log: {str(e)}"
        )

@router.get("/email/stats")
async def get_email_stats(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365)
):
    """Get email statistics."""
    try:
        supabase = get_supabase_client()
        
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Total emails
        total_result = supabase.from_('email_logs') \
            .select('id', count='exact') \
            .gte('created_at', start_date) \
            .execute()
        
        # By status
        status_result = supabase.from_('email_logs') \
            .select('status', count='exact') \
            .gte('created_at', start_date) \
            .execute()
        
        # By type
        type_result = supabase.from_('email_logs') \
            .select('type', count='exact') \
            .gte('created_at', start_date) \
            .execute()
        
        # Success rate
        success_result = supabase.from_('email_logs') \
            .select('id', count='exact') \
            .eq('status', 'sent') \
            .gte('created_at', start_date) \
            .execute()
        
        stats = {
            'total': len(total_result.data) if total_result.data else 0,
            'by_status': {},
            'by_type': {},
            'success_rate': 0
        }
        
        if status_result.data:
            for item in status_result.data:
                stats['by_status'][item['status']] = stats['by_status'].get(item['status'], 0) + 1
        
        if type_result.data:
            for item in type_result.data:
                stats['by_type'][item['type']] = stats['by_type'].get(item['type'], 0) + 1
        
        total = stats['total']
        success = len(success_result.data) if success_result.data else 0
        stats['success_rate'] = (success / total * 100) if total > 0 else 0
        
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get email stats: {str(e)}"
        )

@router.get("/email/email/{email_address}")
async def get_email_logs_by_email(
    email_address: str,
    current_user: AuthUser = Depends(require_admin()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get email logs for a specific email address."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('email_logs') \
            .select('*') \
            .eq('email', email_address) \
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
            detail=f"Failed to get email logs: {str(e)}"
        )

# ==========================================
# Processing Logs Endpoints
# ==========================================

@router.get("/processing")
async def get_processing_logs(
    current_user: AuthUser = Depends(require_admin()),
    file_id: Optional[str] = None,
    status: Optional[str] = None,
    step: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get processing logs."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('processing_logs').select('*')
        
        if file_id:
            query = query.eq('file_id', file_id)
        if status:
            query = query.eq('status', status)
        if step:
            query = query.eq('step', step)
        if start_date:
            query = query.gte('started_at', start_date)
        if end_date:
            query = query.lte('completed_at', end_date)
        
        result = query.order('started_at', desc=True) \
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
            detail=f"Failed to get processing logs: {str(e)}"
        )

@router.get("/processing/{log_id}")
async def get_processing_log_detail(
    log_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """Get detailed processing log entry."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('processing_logs') \
            .select('*') \
            .eq('id', log_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Processing log not found"
            )
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing log: {str(e)}"
        )

@router.get("/processing/file/{file_id}")
async def get_processing_logs_by_file(
    file_id: str,
    current_user: AuthUser = Depends(require_admin()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get processing logs for a specific file."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('processing_logs') \
            .select('*') \
            .eq('file_id', file_id) \
            .order('started_at', desc=True) \
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
            detail=f"Failed to get processing logs: {str(e)}"
        )

@router.get("/processing/stats")
async def get_processing_stats(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(7, ge=1, le=90)
):
    """Get processing statistics."""
    try:
        supabase = get_supabase_client()
        
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Total processes
        total_result = supabase.from_('processing_logs') \
            .select('id', count='exact') \
            .gte('started_at', start_date) \
            .execute()
        
        # By status
        status_result = supabase.from_('processing_logs') \
            .select('status', count='exact') \
            .gte('started_at', start_date) \
            .execute()
        
        # By step
        step_result = supabase.from_('processing_logs') \
            .select('step', count='exact') \
            .gte('started_at', start_date) \
            .execute()
        
        # Average duration
        duration_result = supabase.from_('processing_logs') \
            .select('duration_ms') \
            .not_.is_('duration_ms', 'null') \
            .gte('started_at', start_date) \
            .execute()
        
        stats = {
            'total': len(total_result.data) if total_result.data else 0,
            'by_status': {},
            'by_step': {},
            'average_duration_ms': 0
        }
        
        if status_result.data:
            for item in status_result.data:
                stats['by_status'][item['status']] = stats['by_status'].get(item['status'], 0) + 1
        
        if step_result.data:
            for item in step_result.data:
                stats['by_step'][item['step']] = stats['by_step'].get(item['step'], 0) + 1
        
        if duration_result.data:
            durations = [d['duration_ms'] for d in duration_result.data if d['duration_ms'] is not None]
            if durations:
                stats['average_duration_ms'] = sum(durations) / len(durations)
        
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing stats: {str(e)}"
        )