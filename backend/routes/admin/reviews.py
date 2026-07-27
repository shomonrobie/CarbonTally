# backend/routes/admin/reviews.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from auth import AuthUser, require_role, require_permission
from database import get_supabase_client

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
        
        # Build base query
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
        
        # Apply filters
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
        
        # Get total count
        count_query = query.clone()
        count_result = count_query.select('id', count='exact').execute()
        total = count_result.count or 0
        
        # Apply sorting and pagination
        offset = (page - 1) * limit
        result = query.order('priority', desc=True) \
            .order('created_at', asc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Get queue stats
        stats = await get_queue_stats(supabase)
        
        # Calculate batch progress for each item
        queue_items = []
        for item in result.data:
            # Get batch progress if item belongs to a batch
            batch_progress = None
            if item.get('batch_id'):
                batch_result = supabase.from_('upload_batches') \
                    .select('total_files, processed_files, status') \
                    .eq('id', item['batch_id']) \
                    .maybe_single() \
                    .execute()
                
                if batch_result.data:
                    total_files = batch_result.data.get('total_files', 0)
                    processed_files = batch_result.data.get('processed_files', 0)
                    batch_progress = {
                        'total': total_files,
                        'processed': processed_files,
                        'percentage': round((processed_files / total_files * 100) if total_files > 0 else 0, 1)
                    }
            
            # Format staff names
            assigned_user = item.get('assigned_to_user', {})
            assigned_by_user = item.get('assigned_by_user', {})
            
            queue_items.append({
                'id': item['id'],
                'file_name': item['file_name'],
                'file_type': item['file_type'],
                'file_url': item['file_url'],
                'data_type': item['data_type'],
                'status': item['status'],
                'priority': item.get('priority', 0),
                'priority_score': item.get('priority_score', 0),
                'assigned_to': item.get('assigned_to'),
                'assigned_to_name': f"{assigned_user.get('first_name', '')} {assigned_user.get('last_name', '')}".strip() or assigned_user.get('email'),
                'assigned_by': item.get('assigned_by'),
                'assigned_by_name': f"{assigned_by_user.get('first_name', '')} {assigned_by_user.get('last_name', '')}".strip() or assigned_by_user.get('email'),
                'organization_id': item.get('organization_id'),
                'organization_name': item.get('organization', {}).get('name'),
                'batch_id': item.get('batch_id'),
                'batch_name': item.get('batch', {}).get('batch_name'),
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

async def get_queue_stats(supabase) -> Dict:
    """Get queue statistics."""
    try:
        result = supabase.from_('manual_review_queue') \
            .select('status, count', count='exact') \
            .group_by('status') \
            .execute()
        
        stats = {
            'pending': 0,
            'assigned': 0,
            'in_progress': 0,
            'completed': 0,
            'rejected': 0,
            'total': 0
        }
        
        for item in result.data:
            status_val = item.get('status', 'pending')
            if status_val in stats:
                stats[status_val] = item.get('count', 0)
        
        stats['total'] = sum(stats.values())
        
        # Get high priority count
        high_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('priority', 2) \
            .in_('status', ['pending', 'assigned', 'in_progress']) \
            .execute()
        stats['high_priority'] = high_result.count or 0
        
        # Get SLA breached count
        now = datetime.now().isoformat()
        sla_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('sla_breached', True) \
            .in_('status', ['pending', 'assigned', 'in_progress']) \
            .execute()
        stats['sla_breached'] = sla_result.count or 0
        
        return stats
        
    except Exception as e:
        print(f"⚠️ Error getting queue stats: {e}")
        return {'pending': 0, 'assigned': 0, 'in_progress': 0, 'completed': 0, 'rejected': 0, 'total': 0}

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

@router.post("/{review_id}/start")
async def start_review(
    review_id: str,
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Start reviewing - mark as in_progress.
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
        
        # Update review status
        result = supabase.from_('manual_review_queue') \
            .update({
                'status': 'in_progress',
                'started_at': now
            }) \
            .eq('id', review_id) \
            .execute()
        
        # Update document status
        if review.get('file_id'):
            supabase.from_('organization_files') \
                .update({
                    'status': 'staff_review',
                    'status_updated_at': now,
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
                'action': 'staff_review_started',
                'details': {
                    'review_id': review_id,
                    'staff_id': current_user.user_id
                },
                'created_at': now
            }) \
            .execute()
        
        return {
            "success": True,
            "message": "Review started",
            "review_id": review_id,
            "status": "in_progress"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error starting review: {e}")
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

@router.get("/staff/workload")
async def get_staff_workloads(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get workload for all staff members.
    """
    try:
        supabase = get_supabase_client()
        
        # Get all active staff
        staff_result = supabase.from_('staff_profiles') \
            .select('''
                user_id,
                first_name,
                last_name,
                email,
                total_reviews_completed,
                avg_review_time_minutes
            ''') \
            .eq('is_active', True) \
            .order('first_name') \
            .execute()
        
        staff_list = []
        for staff in staff_result.data:
            # Get current workload
            workload = await get_staff_workload(supabase, staff['user_id'])
            
            # Get assigned reviews count
            assigned_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', staff['user_id']) \
                .in_('status', ['assigned', 'in_progress']) \
                .execute()
            
            staff_list.append({
                'id': staff['user_id'],
                'name': f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or staff.get('email', 'Unknown'),
                'email': staff.get('email'),
                'assigned_reviews': assigned_result.count or 0,
                'in_progress_reviews': workload.get('in_progress_reviews', 0),
                'total_completed': staff.get('total_reviews_completed', 0),
                'avg_time_minutes': staff.get('avg_review_time_minutes', 0),
                'workload_score': workload.get('workload_score', 0)
            })
        
        return {
            "success": True,
            "staff": staff_list,
            "total": len(staff_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting staff workloads: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff workloads: {str(e)}"
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
        
        # Build query for current user's assignments
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
        
        # Get total count
        count_query = query.clone()
        count_result = count_query.select('id', count='exact').execute()
        total = count_result.count or 0
        
        # Get paginated results
        offset = (page - 1) * limit
        result = query.order('priority', desc=True) \
            .order('created_at', asc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Calculate queue stats
        stats = await get_staff_queue_stats(supabase, current_user.user_id)
        
        items = []
        for item in result.data:
            # Get batch progress
            batch_progress = None
            if item.get('batch_id'):
                batch_result = supabase.from_('upload_batches') \
                    .select('total_files, processed_files, status') \
                    .eq('id', item['batch_id']) \
                    .maybe_single() \
                    .execute()
                
                if batch_result.data:
                    total_files = batch_result.data.get('total_files', 0)
                    processed_files = batch_result.data.get('processed_files', 0)
                    batch_progress = {
                        'total': total_files,
                        'processed': processed_files,
                        'percentage': round((processed_files / total_files * 100) if total_files > 0 else 0, 1)
                    }
            
            items.append({
                'id': item['id'],
                'file_name': item['file_name'],
                'file_type': item['file_type'],
                'file_url': item['file_url'],
                'data_type': item['data_type'],
                'status': item['status'],
                'priority': item.get('priority', 0),
                'organization_id': item.get('organization_id'),
                'organization_name': item.get('organization', {}).get('name'),
                'batch_id': item.get('batch_id'),
                'batch_name': item.get('batch', {}).get('batch_name'),
                'batch_progress': batch_progress,
                'customer_notes': item.get('customer_notes'),
                'staff_notes': item.get('staff_notes'),
                'auto_extraction_result': item.get('auto_extraction_result'),
                'manual_extraction_result': item.get('manual_extraction_result'),
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff queue: {str(e)}"
        )

async def get_staff_queue_stats(supabase, staff_id: str) -> Dict:
    """Get queue statistics for a staff member."""
    try:
        result = supabase.from_('manual_review_queue') \
            .select('status, count', count='exact') \
            .eq('assigned_to', staff_id) \
            .group_by('status') \
            .execute()
        
        stats = {
            'pending': 0,
            'assigned': 0,
            'in_progress': 0,
            'completed': 0,
            'rejected': 0,
            'total': 0
        }
        
        for item in result.data:
            status_val = item.get('status', 'pending')
            if status_val in stats:
                stats[status_val] = item.get('count', 0)
        
        stats['total'] = sum(stats.values())
        
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
        return {'pending': 0, 'assigned': 0, 'in_progress': 0, 'completed': 0, 'rejected': 0, 'total': 0}

@router.post("/my-queue/{review_id}/start")
async def start_review(
    review_id: str,
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Start a review - mark as in_progress.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if review exists and is assigned to current user
        review_result = supabase.from_('manual_review_queue') \
            .select('*') \
            .eq('id', review_id) \
            .eq('assigned_to', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if not review_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review item not found or not assigned to you"
            )
        
        review = review_result.data
        now = datetime.now().isoformat()
        
        # Update review status
        supabase.from_('manual_review_queue') \
            .update({
                'status': 'in_progress',
                'started_at': now
            }) \
            .eq('id', review_id) \
            .execute()
        
        # Update document status
        if review.get('file_id'):
            supabase.from_('organization_files') \
                .update({
                    'status': 'staff_review',
                    'status_updated_at': now,
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
                'action': 'staff_review_started',
                'details': {
                    'review_id': review_id,
                    'staff_id': current_user.user_id
                },
                'created_at': now
            }) \
            .execute()
        
        return {
            "success": True,
            "message": "Review started",
            "review_id": review_id,
            "status": "in_progress"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error starting review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start review: {str(e)}"
        )
