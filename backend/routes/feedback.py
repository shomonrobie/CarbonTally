# backend/routes/feedback.py
"""
User feedback collection and management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from auth import AuthUser, require_auth, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/feedback", tags=["Feedback"])

# ==========================================
# Pydantic Models
# ==========================================

class FeedbackCreate(BaseModel):
    type: str  # bug, feature, suggestion, question
    title: str
    description: str
    severity: Optional[str] = None  # low, medium, high, critical
    rating: Optional[int] = None  # 1-5
    screenshot_url: Optional[str] = None
    browser_info: Optional[str] = None
    os_info: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class FeedbackUpdate(BaseModel):
    status: Optional[str] = None  # pending, in_progress, resolved, closed
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    severity: Optional[str] = None

# ==========================================
# Endpoints
# ==========================================

@router.post("", status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    feedback: FeedbackCreate,
    current_user: AuthUser = Depends(require_auth())
):
    """Submit user feedback."""
    try:
        supabase = get_supabase_client()
        
        data = {
            'user_id': current_user.user_id,
            'user_email': current_user.email,
            'organization_id': current_user.organization_id,
            'type': feedback.type,
            'title': feedback.title,
            'description': feedback.description,
            'severity': feedback.severity or 'medium',
            'rating': feedback.rating,
            'screenshot_url': feedback.screenshot_url,
            'browser_info': feedback.browser_info,
            'os_info': feedback.os_info,
            'url': feedback.url,
            'metadata': feedback.metadata,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('user_feedback') \
            .insert(data) \
            .execute()
        
        return {
            "success": True,
            "message": "Feedback submitted successfully",
            "data": result.data[0] if result.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}"
        )

@router.get("")
async def get_user_feedback(
    current_user: AuthUser = Depends(require_auth()),
    status_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get user's own feedback submissions."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('user_feedback') \
            .select('*') \
            .eq('user_id', current_user.user_id)
        
        if status_filter:
            query = query.eq('status', status_filter)
        if type_filter:
            query = query.eq('type', type_filter)
        
        result = query.order('created_at', desc=True) \
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
            detail=f"Failed to get feedback: {str(e)}"
        )

@router.get("/{feedback_id}")
async def get_feedback_detail(
    feedback_id: str,
    current_user: AuthUser = Depends(require_auth())
):
    """Get feedback details."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('user_feedback') \
            .select('*') \
            .eq('id', feedback_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        # Check permissions
        if result.data['user_id'] != current_user.user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this feedback"
            )
        
        return {"success": True, "data": result.data}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback: {str(e)}"
        )

@router.put("/{feedback_id}")
async def update_feedback_status(
    feedback_id: str,
    update: FeedbackUpdate,
    current_user: AuthUser = Depends(require_admin())
):
    """Update feedback status (Admin only)."""
    try:
        supabase = get_supabase_client()
        
        # Check if feedback exists
        existing = supabase.from_('user_feedback') \
            .select('id') \
            .eq('id', feedback_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback not found"
            )
        
        data = update.dict(exclude_none=True)
        data['updated_at'] = datetime.utcnow().isoformat()
        
        if update.status == 'resolved':
            data['resolved_at'] = datetime.utcnow().isoformat()
        
        result = supabase.from_('user_feedback') \
            .update(data) \
            .eq('id', feedback_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Feedback updated successfully",
            "data": result.data[0] if result.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update feedback: {str(e)}"
        )

@router.get("/admin/feedback/pending")  # ✅ Changed from /admin/pending
async def get_pending_feedback(
    current_user: AuthUser = Depends(require_admin()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get pending feedback (Admin only)."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('user_feedback') \
            .select('*') \
            .eq('status', 'pending') \
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
            detail=f"Failed to get pending feedback: {str(e)}"
        )

@router.get("/admin/feedback/stats")  # ✅ Changed from /admin/stats
async def get_feedback_stats(
    current_user: AuthUser = Depends(require_admin())
):
    """Get feedback statistics (Admin only)."""
    try:
        supabase = get_supabase_client()
        
        # Get counts by status
        status_result = supabase.from_('user_feedback') \
            .select('status', count='exact') \
            .execute()
        
        # Get counts by type
        type_result = supabase.from_('user_feedback') \
            .select('type', count='exact') \
            .execute()
        
        # Get average rating
        rating_result = supabase.from_('user_feedback') \
            .select('rating') \
            .not_.is_('rating', 'null') \
            .execute()
        
        stats = {
            'total': len(status_result.data) if status_result.data else 0,
            'by_status': {},
            'by_type': {},
            'average_rating': 0
        }
        
        if status_result.data:
            for item in status_result.data:
                stats['by_status'][item['status']] = stats['by_status'].get(item['status'], 0) + 1
        
        if type_result.data:
            for item in type_result.data:
                stats['by_type'][item['type']] = stats['by_type'].get(item['type'], 0) + 1
        
        if rating_result.data:
            ratings = [r['rating'] for r in rating_result.data if r['rating'] is not None]
            if ratings:
                stats['average_rating'] = sum(ratings) / len(ratings)
        
        return {"success": True, "data": stats}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get feedback stats: {str(e)}"
        )