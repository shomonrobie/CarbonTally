# backend/routes/admin/reviews.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from auth import AuthUser, require_role, require_permission, require_admin

from database import get_supabase_client
from utils import get_staff_workload, get_all_staff_workload
from .workload import get_queue_stats
router = APIRouter(prefix="/api/admin/reviews", tags=["Admin - Reviews"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class AssignRequest(BaseModel):
    assigned_to: str
    note: Optional[str] = None

class CompleteRequest(BaseModel):
    notes: Optional[str] = None
    extraction_data: Optional[Dict[str, Any]] = None

class QueueFilterParams(BaseModel):
    status: Optional[str] = None
    priority: Optional[int] = None
    assigned_to: Optional[str] = None
    batch_id: Optional[str] = None
    search: Optional[str] = None
    page: int = 1
    limit: int = 20

# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def update_staff_workload(supabase, staff_id: str):
    """Update staff workload statistics."""
    try:
        # Count active reviews for staff
        active_count = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('assigned_to', staff_id) \
            .in_('status', ['assigned', 'in_progress']) \
            .execute()
        
        # Update or insert workload record
        today = datetime.now().date().isoformat()
        supabase.from_('staff_workload') \
            .upsert({
                'staff_id': staff_id,
                'assigned_reviews': active_count.count or 0,
                'last_updated': datetime.now().isoformat(),
                'date': today
            }, on_conflict='staff_id,date') \
            .execute()
    except Exception as e:
        print(f"⚠️ Error updating staff workload: {e}")

async def get_staff_workload(supabase, staff_id: str) -> Dict:
    """Get staff workload statistics."""
    try:
        result = supabase.from_('staff_workload') \
            .select('*') \
            .eq('staff_id', staff_id) \
            .eq('date', datetime.now().date().isoformat()) \
            .maybe_single() \
            .execute()
        
        if result.data:
            return result.data
        
        return {
            'assigned_reviews': 0,
            'in_progress_reviews': 0,
            'completed_today': 0,
            'workload_score': 0
        }
    except Exception:
        return {'assigned_reviews': 0, 'in_progress_reviews': 0, 'completed_today': 0, 'workload_score': 0}

# ==========================================
# ENDPOINTS
# ==========================================
@router.get("/queue")
async def get_review_queue(
    status: Optional[str] = Query(None, description="Filter by status: pending, assigned, in_progress, completed, rejected"),
    priority: Optional[int] = Query(None, description="Filter by priority: 0=Low, 1=Medium, 2=High"),
    assigned_to: Optional[str] = Query(None, description="Filter by assigned staff"),
    batch_id: Optional[str] = Query(None, description="Filter by batch ID"),
    search: Optional[str] = Query(None, description="Search by file name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Get the staff review queue with filters and pagination.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Build base query
        query = supabase.from_('manual_review_queue') \
            .select('''
                *,
                assigned_to_user:assigned_to (
                    id,
                    email,
                    first_name,
                    last_name
                ),
                assigned_by_user:assigned_by (
                    id,
                    email,
                    first_name,
                    last_name
                ),
                organization:organization_id (
                    id,
                    name
                ),
                batch:batch_id (
                    id,
                    batch_name,
                    total_files,
                    processed_files
                )
            ''')
        
        # ✅ Apply filters
        if status:
            query = query.eq('status', status)
        if priority is not None:
            query = query.eq('priority', priority)
        if assigned_to:
            query = query.eq('assigned_to', assigned_to)
        if batch_id:
            query = query.eq('batch_id', batch_id)
        if search:
            query = query.ilike('file_name', f'%{search}%')
        
        # ✅ Get total count (separate query - no .clone())
        count_query = supabase.from_('manual_review_queue') \
            .select('id', count='exact')
        
        # Apply the same filters to count_query
        if status:
            count_query = count_query.eq('status', status)
        if priority is not None:
            count_query = count_query.eq('priority', priority)
        if assigned_to:
            count_query = count_query.eq('assigned_to', assigned_to)
        if batch_id:
            count_query = count_query.eq('batch_id', batch_id)
        if search:
            count_query = count_query.ilike('file_name', f'%{search}%')
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # ✅ Apply sorting and pagination
        offset = (page - 1) * limit
        
        # ✅ Fixed: Use desc=False instead of asc=True
        result = query.order('priority', desc=True) \
            .order('created_at', desc=False) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Get queue stats
        stats = await get_queue_stats(supabase)
        
        # Calculate batch progress for each item
        queue_items = []
        for item in (result.data or []):
            # Get batch progress if item belongs to a batch
            batch_progress = None
            if item.get('batch_id'):
                batch_result = supabase.from_('upload_batches') \
                    .select('total_files, processed_files, status') \
                    .eq('id', item['batch_id']) \
                    .maybe_single() \
                    .execute()
                
                if batch_result and batch_result.data:
                    total_files = batch_result.data.get('total_files', 0)
                    processed_files = batch_result.data.get('processed_files', 0)
                    batch_progress = {
                        'total': total_files,
                        'processed': processed_files,
                        'percentage': round((processed_files / total_files * 100) if total_files > 0 else 0, 1)
                    }
            
            # Format staff names
            assigned_user = item.get('assigned_to_user', {}) or {}
            assigned_by_user = item.get('assigned_by_user', {}) or {}
            
            # Get organization name
            org_data = item.get('organization', {}) or {}
            batch_data = item.get('batch', {}) or {}
            
            queue_items.append({
                'id': item.get('id'),
                'file_name': item.get('file_name', ''),
                'file_type': item.get('file_type'),
                'file_url': item.get('file_url'),
                'data_type': item.get('data_type'),
                'status': item.get('status', 'pending'),
                'priority': item.get('priority', 0),
                'priority_score': item.get('priority_score', 0),
                'assigned_to': item.get('assigned_to'),
                'assigned_to_name': f"{assigned_user.get('first_name', '')} {assigned_user.get('last_name', '')}".strip() or assigned_user.get('email'),
                'assigned_by': item.get('assigned_by'),
                'assigned_by_name': f"{assigned_by_user.get('first_name', '')} {assigned_by_user.get('last_name', '')}".strip() or assigned_by_user.get('email'),
                'organization_id': item.get('organization_id'),
                'organization_name': org_data.get('name'),
                'batch_id': item.get('batch_id'),
                'batch_name': batch_data.get('batch_name'),
                'batch_progress': batch_progress,
                'customer_notes': item.get('customer_notes'),
                'staff_notes': item.get('staff_notes'),
                'auto_extraction_result': item.get('auto_extraction_result'),
                'manual_extraction_result': item.get('manual_extraction_result'),
                'estimated_completion_hours': item.get('estimated_completion_hours'),
                'sla_deadline': item.get('sla_deadline'),
                'sla_breached': item.get('sla_breached', False),
                'created_at': item.get('created_at'),
                'started_at': item.get('started_at'),
                'completed_at': item.get('completed_at'),
                'review_time_seconds': item.get('review_time_seconds')
            })
        
        return {
            "success": True,
            "items": queue_items,
            "total": total,
            "page": page,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting review queue: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review queue: {str(e)}"
        )
@router.get("/{review_id}")
async def get_review_details(
    review_id: str,
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Get detailed information about a specific review item.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('manual_review_queue') \
            .select('''
                *,
                assigned_to_user:assigned_to (
                    id,
                    email,
                    first_name,
                    last_name
                ),
                assigned_by_user:assigned_by (
                    id,
                    email,
                    first_name,
                    last_name
                ),
                organization:organization_id (
                    id,
                    name
                ),
                batch:batch_id (
                    id,
                    batch_name,
                    total_files,
                    processed_files,
                    status
                )
            ''') \
            .eq('id', review_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review item not found"
            )
        
        item = result.data
        
        # Get assignment history
        history_result = supabase.from_('review_assignment_history') \
            .select('''
                *,
                assigned_by_user:assigned_by (
                    id,
                    email,
                    first_name,
                    last_name
                ),
                assigned_to_user:assigned_to (
                    id,
                    email,
                    first_name,
                    last_name
                )
            ''') \
            .eq('review_id', review_id) \
            .order('created_at', desc=True) \
            .limit(20) \
            .execute()
        
        return {
            "success": True,
            "review": {
                'id': item['id'],
                'file_name': item['file_name'],
                'file_type': item['file_type'],
                'file_url': item['file_url'],
                'data_type': item['data_type'],
                'status': item['status'],
                'priority': item.get('priority', 0),
                'priority_score': item.get('priority_score', 0),
                'assigned_to': item.get('assigned_to'),
                'assigned_by': item.get('assigned_by'),
                'organization_id': item.get('organization_id'),
                'organization_name': item.get('organization', {}).get('name'),
                'batch_id': item.get('batch_id'),
                'batch_name': item.get('batch', {}).get('batch_name'),
                'customer_notes': item.get('customer_notes'),
                'staff_notes': item.get('staff_notes'),
                'auto_extraction_result': item.get('auto_extraction_result'),
                'manual_extraction_result': item.get('manual_extraction_result'),
                'estimated_completion_hours': item.get('estimated_completion_hours'),
                'sla_deadline': item.get('sla_deadline'),
                'sla_breached': item.get('sla_breached', False),
                'created_at': item.get('created_at'),
                'started_at': item.get('started_at'),
                'completed_at': item.get('completed_at'),
                'review_time_seconds': item.get('review_time_seconds')
            },
            "assignment_history": history_result.data or []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting review details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review details: {str(e)}"
        )

@router.post("/{review_id}/assign")
async def assign_review(
    review_id: str,
    assign_data: AssignRequest,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Assign a review to a staff member.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if review exists
        review_result = supabase.from_('manual_review_queue') \
            .select('*') \
            .eq('id', review_id) \
            .maybe_single() \
            .execute()
        
        if not review_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review item not found"
            )
        
        review = review_result.data
        old_assigned_to = review.get('assigned_to')
        old_status = review.get('status')
        
        # Check if staff exists
        staff_result = supabase.from_('staff_profiles') \
            .select('user_id, first_name, last_name, email') \
            .eq('user_id', assign_data.assigned_to) \
            .eq('is_active', True) \
            .maybe_single() \
            .execute()
        
        if not staff_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found or inactive"
            )
        
        now = datetime.now().isoformat()
        
        # Update review
        update_data = {
            'assigned_to': assign_data.assigned_to,
            'assigned_by': current_user.user_id,
            'status': 'assigned',
            'assigned_at': now,
            'priority': review.get('priority', 0)
        }
        
        # Set SLA deadline (24 hours by default)
        if not review.get('sla_deadline'):
            update_data['sla_deadline'] = (datetime.now() + timedelta(hours=24)).isoformat()
        
        # If reassigning, log previous assignment
        if old_assigned_to and old_assigned_to != assign_data.assigned_to:
            # Log assignment history
            supabase.from_('review_assignment_history') \
                .insert({
                    'review_id': review_id,
                    'assigned_by': current_user.user_id,
                    'assigned_to': assign_data.assigned_to,
                    'previous_assigned_to': old_assigned_to,
                    'action': 'reassign',
                    'note': assign_data.note or f"Reassigned from {old_assigned_to} to {assign_data.assigned_to}",
                    'created_at': now
                }) \
                .execute()
        else:
            # Log initial assignment
            supabase.from_('review_assignment_history') \
                .insert({
                    'review_id': review_id,
                    'assigned_by': current_user.user_id,
                    'assigned_to': assign_data.assigned_to,
                    'previous_assigned_to': None,
                    'action': 'assign',
                    'note': assign_data.note or "Initial assignment",
                    'created_at': now
                }) \
                .execute()
        
        # Update review
        result = supabase.from_('manual_review_queue') \
            .update(update_data) \
            .eq('id', review_id) \
            .execute()
        
        # Update staff workload
        await update_staff_workload(supabase, assign_data.assigned_to)
        if old_assigned_to and old_assigned_to != assign_data.assigned_to:
            await update_staff_workload(supabase, old_assigned_to)
        
        # Update document activity log
        supabase.from_('document_activity_log') \
            .insert({
                'file_id': review.get('file_id'),
                'organization_id': review.get('organization_id'),
                'user_id': current_user.user_id,
                'action': 'assigned_to_staff',
                'details': {
                    'assigned_to': assign_data.assigned_to,
                    'assigned_by': current_user.user_id,
                    'note': assign_data.note,
                    'old_assigned_to': old_assigned_to
                },
                'created_at': now
            }) \
            .execute()
        
        return {
            "success": True,
            "message": f"Review assigned to {staff_result.data.get('first_name', '')} {staff_result.data.get('last_name', '')}",
            "review_id": review_id,
            "assigned_to": assign_data.assigned_to
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error assigning review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign review: {str(e)}"
        )


@router.post("/my-queue/{review_id}/start")
async def start_review(
    review_id: str,
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Start a review - mark as in_progress.
    Only the assigned staff member or admin can start a review.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if review exists and is assigned to current user
        review_result = supabase.from_('manual_review_queue') \
            .select('*') \
            .eq('id', review_id) \
            .maybe_single() \
            .execute()
        
        if not review_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review item not found"
            )
        
        review = review_result.data
        
        # Check if assigned to current user (admin can start any)
        if not current_user.is_admin and review.get('assigned_to') != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this review"
            )
        
        # Check if already in progress
        if review.get('status') == 'in_progress':
            return {
                "success": True,
                "message": "Review is already in progress",
                "review_id": review_id,
                "status": "in_progress"
            }
        
        # Check if already completed
        if review.get('status') == 'completed':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Review is already completed"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Update review status
        result = supabase.from_('manual_review_queue') \
            .update({
                'status': 'in_progress',
                'started_at': now,
                'started_by': current_user.user_id,
                'updated_at': now
            }) \
            .eq('id', review_id) \
            .execute()
        
        # Update document status
        if review.get('file_id'):
            supabase.from_('organization_files') \
                .update({
                    'status': 'staff_review',
                    'status_updated_at': now,
                    'reviewed_by': current_user.user_id,
                    'updated_at': now
                }) \
                .eq('id', review['file_id']) \
                .execute()
        
        # Log activity
        supabase.from_('document_activity_log') \
            .insert({
                'file_id': review.get('file_id'),
                'organization_id': review.get('organization_id'),
                'user_id': current_user.user_id,
                'action': 'staff_review_started',
                'details': {
                    'review_id': review_id,
                    'staff_id': current_user.user_id,
                    'staff_name': f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.email
                },
                'created_at': now,
                'ip_address': None,  # Can be added from request
                'user_agent': None   # Can be added from request
            }) \
            .execute()
        
        return {
            "success": True,
            "message": "Review started successfully",
            "review_id": review_id,
            "status": "in_progress",
            "started_at": now
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error starting review: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start review: {str(e)}"
        )

@router.post("/{review_id}/complete")
async def complete_review(
    review_id: str,
    complete_data: CompleteRequest,
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Complete a review - mark as ready_for_review.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if review exists and is assigned to current user
        review_result = supabase.from_('manual_review_queue') \
            .select('*') \
            .eq('id', review_id) \
            .maybe_single() \
            .execute()
        
        if not review_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review item not found"
            )
        
        review = review_result.data
        
        # Check if assigned to current user or admin
        if review.get('assigned_to') != current_user.user_id and current_user.role != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not assigned to this review"
            )
        
        now = datetime.now().isoformat()
        
        # Calculate review time
        review_time = 0
        if review.get('started_at'):
            try:
                start_time = datetime.fromisoformat(review['started_at'].replace('Z', '+00:00'))
                end_time = datetime.now()
                review_time = int((end_time - start_time).total_seconds())
            except:
                pass
        
        # Update review
        update_data = {
            'status': 'ready_for_review',
            'completed_at': now,
            'completed_by': current_user.user_id,
            'staff_notes': complete_data.notes or review.get('staff_notes', ''),
            'review_time_seconds': review_time
        }
        
        if complete_data.extraction_data:
            update_data['manual_extraction_result'] = complete_data.extraction_data
        
        result = supabase.from_('manual_review_queue') \
            .update(update_data) \
            .eq('id', review_id) \
            .execute()
        
        # Update document status
        if review.get('file_id'):
            supabase.from_('organization_files') \
                .update({
                    'status': 'ready_for_review',
                    'status_updated_at': now,
                    'review_ready_at': now,
                    'reviewed_by': current_user.user_id,
                    'metadata': {
                        'review_completed_by': current_user.user_id,
                        'review_completed_at': now,
                        'staff_notes': complete_data.notes,
                        'review_time_seconds': review_time
                    }
                }) \
                .eq('id', review['file_id']) \
                .execute()
        
        # Update staff profile metrics
        staff_result = supabase.from_('staff_profiles') \
            .select('total_reviews_completed, avg_review_time_minutes') \
            .eq('user_id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if staff_result.data:
            total_completed = (staff_result.data.get('total_reviews_completed') or 0) + 1
            avg_time = staff_result.data.get('avg_review_time_minutes') or 0
            
            # Calculate new average
            avg_time_minutes = review_time / 60
            new_avg = ((avg_time * (total_completed - 1)) + avg_time_minutes) / total_completed
            
            supabase.from_('staff_profiles') \
                .update({
                    'total_reviews_completed': total_completed,
                    'avg_review_time_minutes': round(new_avg, 2)
                }) \
                .eq('user_id', current_user.user_id) \
                .execute()
        
        # Update staff workload
        await update_staff_workload(supabase, current_user.user_id)
        
        # Log activity
        supabase.from_('document_activity_log') \
            .insert({
                'file_id': review.get('file_id'),
                'organization_id': review.get('organization_id'),
                'user_id': current_user.user_id,
                'action': 'staff_review_completed',
                'details': {
                    'review_id': review_id,
                    'staff_id': current_user.user_id,
                    'review_time_seconds': review_time,
                    'notes': complete_data.notes
                },
                'created_at': now
            }) \
            .execute()
        
        return {
            "success": True,
            "message": "Review completed and ready for customer",
            "review_id": review_id,
            "status": "ready_for_review",
            "review_time_seconds": review_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error completing review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete review: {str(e)}"
        )

@router.post("/{review_id}/reject")
async def reject_review(
    review_id: str,
    reject_data: Dict[str, Any],
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Reject a review item.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if review exists
        review_result = supabase.from_('manual_review_queue') \
            .select('*') \
            .eq('id', review_id) \
            .maybe_single() \
            .execute()
        
        if not review_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review item not found"
            )
        
        review = review_result.data
        reason = reject_data.get('reason', 'No reason provided')
        
        now = datetime.now().isoformat()
        
        # Update review
        supabase.from_('manual_review_queue') \
            .update({
                'status': 'rejected',
                'completed_at': now,
                'completed_by': current_user.user_id,
                'staff_notes': f"Rejected: {reason}"
            }) \
            .eq('id', review_id) \
            .execute()
        
        # Update document status
        if review.get('file_id'):
            supabase.from_('organization_files') \
                .update({
                    'status': 'rejected',
                    'status_updated_at': now,
                    'rejected_at': now,
                    'rejection_reason': reason,
                    'reviewed_by': current_user.user_id
                }) \
                .eq('id', review['file_id']) \
                .execute()
        
        # Log activity
        supabase.from_('document_activity_log') \
            .insert({
                'file_id': review.get('file_id'),
                'organization_id': review.get('organization_id'),
                'user_id': current_user.user_id,
                'action': 'staff_review_rejected',
                'details': {
                    'review_id': review_id,
                    'reason': reason
                },
                'created_at': now
            }) \
            .execute()
        
        return {
            "success": True,
            "message": "Review rejected",
            "review_id": review_id,
            "status": "rejected"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error rejecting review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject review: {str(e)}"
        )
@router.get("/my-queue")
async def get_my_review_queue(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, description="Filter by priority"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Get reviews assigned to the current staff member.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Build query for current user's assignments
        query = supabase.from_('manual_review_queue') \
            .select('''
                *,
                organization:organization_id (
                    id,
                    name
                ),
                batch:batch_id (
                    id,
                    batch_name,
                    total_files,
                    processed_files,
                    status
                ),
                assigned_by_user:assigned_by (
                    id,
                    email,
                    first_name,
                    last_name
                )
            ''') \
            .eq('assigned_to', current_user.user_id)
        
        if status:
            query = query.eq('status', status)
        if priority is not None:
            query = query.eq('priority', priority)
        
        # ✅ Get total count (separate query - no .clone())
        count_query = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('assigned_to', current_user.user_id)
        
        if status:
            count_query = count_query.eq('status', status)
        if priority is not None:
            count_query = count_query.eq('priority', priority)
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # ✅ Get paginated results
        offset = (page - 1) * limit
        
        # ✅ Fixed: Use desc=False instead of asc=True
        result = query.order('priority', desc=True) \
            .order('created_at', desc=False) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Calculate queue stats
        stats = await get_staff_queue_stats(supabase, current_user.user_id)
        
        items = []
        for item in (result.data or []):
            # Get batch progress
            batch_progress = None
            if item.get('batch_id'):
                batch_result = supabase.from_('upload_batches') \
                    .select('total_files, processed_files, status') \
                    .eq('id', item['batch_id']) \
                    .maybe_single() \
                    .execute()
                
                if batch_result and batch_result.data:
                    total_files = batch_result.data.get('total_files', 0)
                    processed_files = batch_result.data.get('processed_files', 0)
                    batch_progress = {
                        'total': total_files,
                        'processed': processed_files,
                        'percentage': round((processed_files / total_files * 100) if total_files > 0 else 0, 1)
                    }
            
            # Get organization name
            org_data = item.get('organization', {}) or {}
            batch_data = item.get('batch', {}) or {}
            assigned_by_data = item.get('assigned_by_user', {}) or {}
            
            items.append({
                'id': item.get('id'),
                'file_name': item.get('file_name', ''),
                'file_type': item.get('file_type'),
                'file_url': item.get('file_url'),
                'data_type': item.get('data_type'),
                'status': item.get('status', 'pending'),
                'priority': item.get('priority', 0),
                'organization_id': item.get('organization_id'),
                'organization_name': org_data.get('name'),
                'batch_id': item.get('batch_id'),
                'batch_name': batch_data.get('batch_name'),
                'batch_progress': batch_progress,
                'customer_notes': item.get('customer_notes'),
                'staff_notes': item.get('staff_notes'),
                'auto_extraction_result': item.get('auto_extraction_result'),
                'manual_extraction_result': item.get('manual_extraction_result'),
                'assigned_by': item.get('assigned_by'),
                'assigned_by_name': f"{assigned_by_data.get('first_name', '')} {assigned_by_data.get('last_name', '')}".strip() or assigned_by_data.get('email'),
                'created_at': item.get('created_at'),
                'started_at': item.get('started_at'),
                'completed_at': item.get('completed_at')
            })
        
        return {
            "success": True,
            "items": items,
            "total": total,
            "page": page,
            "total_pages": (total + limit - 1) // limit if limit > 0 else 1,
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting staff queue: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff queue: {str(e)}"
        )
    
async def get_staff_queue_stats(supabase, staff_id: str) -> Dict:
    """Get queue statistics for a staff member."""
    try:
        statuses = ['pending', 'assigned', 'in_progress', 'completed', 'rejected']
        stats = {
            'pending': 0,
            'assigned': 0,
            'in_progress': 0,
            'completed': 0,
            'rejected': 0,
            'total': 0,
            'high_priority': 0
        }
        
        # ✅ Get counts for each status separately
        for status_val in statuses:
            result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', staff_id) \
                .eq('status', status_val) \
                .execute()
            stats[status_val] = result.count or 0
        
        stats['total'] = sum(stats[status] for status in statuses)
        
        # Get high priority count
        high_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('assigned_to', staff_id) \
            .eq('priority', 2) \
            .in_('status', ['pending', 'assigned', 'in_progress']) \
            .execute()
        stats['high_priority'] = high_result.count or 0
        
        return stats
        
    except Exception as e:
        print(f"⚠️ Error getting staff queue stats: {e}")
        return {
            'pending': 0, 
            'assigned': 0, 
            'in_progress': 0, 
            'completed': 0, 
            'rejected': 0, 
            'total': 0,
            'high_priority': 0
        }

# ==========================================
# Advanced Queue Management
# ==========================================

@router.get("/queue/priority")
async def get_priority_queue(
    current_user: AuthUser = Depends(require_admin()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get queue items sorted by priority."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('manual_review_queue') \
            .select('*, staff_profiles!assigned_to(first_name, last_name)') \
            .order('priority_score', desc=True) \
            .order('created_at', desc=False) \
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
            detail=f"Failed to get priority queue: {str(e)}"
        )

@router.post("/queue/reorder")
async def reorder_queue(
    reorder_data: List[Dict[str, Any]],
    current_user: AuthUser = Depends(require_admin())
):
    """Reorder items in the queue."""
    try:
        supabase = get_supabase_client()
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': []
        }
        
        for item in reorder_data:
            try:
                review_id = item.get('review_id')
                priority_score = item.get('priority_score')
                
                if not review_id:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'error': 'review_id is required',
                        'data': item
                    })
                    continue
                
                result = supabase.from_('manual_review_queue') \
                    .update({
                        'priority_score': priority_score,
                        'updated_at': datetime.utcnow().isoformat()
                    }) \
                    .eq('id', review_id) \
                    .execute()
                
                if result.data:
                    results['success_count'] += 1
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'review_id': review_id,
                        'error': 'Failed to update priority'
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'error': str(e),
                    'data': item
                })
        
        return {
            "success": True,
            "message": f"Queue reordered: {results['success_count']} updated, {results['failed_count']} failed",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reorder queue: {str(e)}"
        )

@router.get("/queue/stats/detailed")
async def get_detailed_queue_stats(
    current_user: AuthUser = Depends(require_admin())
):
    """Get detailed queue statistics."""
    try:
        supabase = get_supabase_client()
        
        # Get all queue items
        result = supabase.from_('manual_review_queue') \
            .select('status, priority, priority_score, sla_deadline, sla_breached, assigned_to, created_at') \
            .execute()
        
        if not result.data:
            return {
                "success": True,
                "data": {
                    "total": 0,
                    "by_status": {},
                    "by_priority": {},
                    "avg_priority_score": 0,
                    "sla_breaches": 0,
                    "unassigned_count": 0,
                    "avg_age_hours": 0
                }
            }
        
        stats = {
            'total': len(result.data),
            'by_status': {},
            'by_priority': {},
            'avg_priority_score': 0,
            'sla_breaches': 0,
            'unassigned_count': 0,
            'avg_age_hours': 0
        }
        
        total_priority = 0
        total_age_hours = 0
        now = datetime.utcnow()
        
        for item in result.data:
            # By status
            status = item.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # By priority
            priority = item.get('priority', 'medium')
            stats['by_priority'][priority] = stats['by_priority'].get(priority, 0) + 1
            
            # Priority score
            total_priority += item.get('priority_score', 0)
            
            # SLA breaches
            if item.get('sla_breached'):
                stats['sla_breaches'] += 1
            
            # Unassigned
            if not item.get('assigned_to'):
                stats['unassigned_count'] += 1
            
            # Age
            if item.get('created_at'):
                created = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
                age_hours = (now - created).total_seconds() / 3600
                total_age_hours += age_hours
        
        stats['avg_priority_score'] = round(total_priority / len(result.data), 2) if result.data else 0
        stats['avg_age_hours'] = round(total_age_hours / len(result.data), 2) if result.data else 0
        
        return {"success": True, "data": stats}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed queue stats: {str(e)}"
        )

@router.post("/queue/escalate")
async def escalate_review(
    review_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """Escalate a review (increase priority and notify)."""
    try:
        supabase = get_supabase_client()
        
        # Check if review exists
        existing = supabase.from_('manual_review_queue') \
            .select('*') \
            .eq('id', review_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found"
            )
        
        # Update escalation level
        new_escalation = existing.data.get('escalation_level', 0) + 1
        
        result = supabase.from_('manual_review_queue') \
            .update({
                'escalation_level': new_escalation,
                'priority_score': existing.data.get('priority_score', 0) + 20,
                'sla_deadline': (datetime.utcnow() + timedelta(hours=12)).isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }) \
            .eq('id', review_id) \
            .execute()
        
        return {
            "success": True,
            "message": f"Review escalated to level {new_escalation}",
            "data": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to escalate review: {str(e)}"
        )

@router.get("/queue/sla-monitor")
async def get_sla_monitor(
    current_user: AuthUser = Depends(require_admin())
):
    """Monitor SLA compliance for all queue items."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('manual_review_queue') \
            .select('id, sla_deadline, sla_breached, status, priority, assigned_to') \
            .eq('status', 'pending') \
            .execute()
        
        if not result.data:
            return {
                "success": True,
                "data": {
                    "total_pending": 0,
                    "at_risk": 0,
                    "breached": 0,
                    "items": []
                }
            }
        
        now = datetime.utcnow()
        monitor_data = {
            'total_pending': len(result.data),
            'at_risk': 0,
            'breached': 0,
            'items': []
        }
        
        for item in result.data:
            if item.get('sla_breached'):
                monitor_data['breached'] += 1
            elif item.get('sla_deadline'):
                deadline = datetime.fromisoformat(item['sla_deadline'].replace('Z', '+00:00'))
                time_left = (deadline - now).total_seconds() / 3600
                if time_left < 24:  # Less than 24 hours
                    monitor_data['at_risk'] += 1
                
                monitor_data['items'].append({
                    'review_id': item['id'],
                    'status': item['status'],
                    'priority': item.get('priority', 'medium'),
                    'assigned_to': item.get('assigned_to'),
                    'sla_deadline': item.get('sla_deadline'),
                    'sla_breached': item.get('sla_breached', False),
                    'hours_until_deadline': round(time_left, 2)
                })
        
        return {"success": True, "data": monitor_data}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SLA monitor: {str(e)}"
        )