# backend/routes/admin/assignments.py
from fastapi import APIRouter, Depends, HTTPException,  status as http_status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel
from auth import AuthUser, require_role
from database import get_supabase_client
from utils import get_staff_workload  # ✅ Import from utils

router = APIRouter(prefix="/api/admin/assignments", tags=["Admin - Assignments"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class AssignRequest(BaseModel):
    staff_user_id: str
    note: Optional[str] = None
    deadline: Optional[str] = None

class BatchAssignRequest(BaseModel):
    staff_user_id: str
    note: Optional[str] = None
    deadline: Optional[str] = None

# ==========================================
# ENDPOINTS
# ==========================================
@router.get("/available")
async def get_available_reviews(
    status: Optional[str] = Query(None, description="Filter by status"),
    priority: Optional[int] = Query(None, description="Filter by priority"),
    search: Optional[str] = Query(None, description="Search by file name"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get all pending reviews available for assignment.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Build query for pending and unassigned reviews
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
                )
            ''') \
            .eq('status', 'pending') \
            .is_('assigned_to', 'null')
        
        if priority is not None:
            query = query.eq('priority', priority)
        if search:
            query = query.ilike('file_name', f'%{search}%')
        
        # ✅ Get total count (separate query - no .clone())
        count_query = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('status', 'pending') \
            .is_('assigned_to', 'null')
        
        if priority is not None:
            count_query = count_query.eq('priority', priority)
        if search:
            count_query = count_query.ilike('file_name', f'%{search}%')
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # Get paginated results
        offset = (page - 1) * limit
        result = query.order('priority', desc=True) \
            .order('created_at') \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # ✅ Get queue stats (group in Python instead of using group_by)
        stats_result = supabase.from_('manual_review_queue') \
            .select('status') \
            .execute()
        
        stats = {
            'pending': 0,
            'assigned': 0,
            'in_progress': 0,
            'completed': 0,
            'rejected': 0
        }
        
        for item in (stats_result.data or []):
            status_val = item.get('status', 'pending')
            if status_val in stats:
                stats[status_val] += 1
        
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
                
                if batch_result.data:
                    total_files = batch_result.data.get('total_files', 0)
                    processed_files = batch_result.data.get('processed_files', 0)
                    batch_progress = {
                        'total': total_files,
                        'processed': processed_files,
                        'percentage': round((processed_files / total_files * 100) if total_files > 0 else 0, 1)
                    }
            
            # Get organization name
            org_name = None
            if item.get('organization'):
                org_name = item.get('organization', {}).get('name')
            
            # Get batch name
            batch_name = None
            if item.get('batch'):
                batch_name = item.get('batch', {}).get('batch_name')
            
            items.append({
                'id': item['id'],
                'file_name': item.get('file_name', ''),
                'file_type': item.get('file_type'),
                'file_url': item.get('file_url'),
                'data_type': item.get('data_type'),
                'status': item.get('status', 'pending'),
                'priority': item.get('priority', 0),
                'organization_id': item.get('organization_id'),
                'organization_name': org_name,
                'batch_id': item.get('batch_id'),
                'batch_name': batch_name,
                'batch_progress': batch_progress,
                'customer_notes': item.get('customer_notes'),
                'created_at': item.get('created_at')
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
        print(f"❌ Error getting available reviews: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get available reviews: {str(e)}"
        )
@router.get("/staff")
async def get_staff_list(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get list of staff members with their workload.
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
            workload = await get_staff_workload(supabase, staff['user_id'])
            
            staff_list.append({
                'id': staff['user_id'],
                'name': f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or staff.get('email', 'Unknown'),
                'email': staff.get('email'),
                'first_name': staff.get('first_name'),
                'last_name': staff.get('last_name'),
                'assigned': workload['assigned'],
                'in_progress': workload['in_progress'],
                'completed': workload['completed'],
                'total': workload['total'],
                'total_completed': staff.get('total_reviews_completed', 0),
                'avg_time': staff.get('avg_review_time_minutes', 0)
            })
        
        return {
            "success": True,
            "staff": staff_list,
            "total": len(staff_list)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting staff list: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff list: {str(e)}"
        )

@router.post("/batch/{batch_id}/assign")
async def assign_batch(
    batch_id: str,
    assign_data: BatchAssignRequest,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Assign all pending files in a batch to a staff member.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if batch exists
        batch_result = supabase.from_('upload_batches') \
            .select('*') \
            .eq('id', batch_id) \
            .maybe_single() \
            .execute()
        
        if not batch_result.data:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # Check if staff exists
        staff_result = supabase.from_('staff_profiles') \
            .select('user_id, first_name, last_name, email') \
            .eq('user_id', assign_data.staff_user_id) \
            .eq('is_active', True) \
            .maybe_single() \
            .execute()
        
        if not staff_result.data:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail="Staff member not found or inactive"
            )
        
        # Get all pending reviews in this batch
        pending_reviews = supabase.from_('manual_review_queue') \
            .select('id') \
            .eq('batch_id', batch_id) \
            .eq('status', 'pending') \
            .is_('assigned_to', 'null') \
            .execute()
        
        if not pending_reviews.data:
            raise HTTPException(
                status_code=http_status.HTTP_400_BAD_REQUEST,
                detail="No pending reviews found in this batch"
            )
        
        now = datetime.now().isoformat()
        assigned_count = 0
        
        # Assign each pending review
        for review in pending_reviews.data:
            review_id = review['id']
            
            # Get review details
            review_result = supabase.from_('manual_review_queue') \
                .select('priority, file_id') \
                .eq('id', review_id) \
                .maybe_single() \
                .execute()
            
            if review_result.data:
                # Update review
                update_data = {
                    'assigned_to': assign_data.staff_user_id,
                    'assigned_by': current_user.user_id,
                    'status': 'assigned',
                    'assigned_at': now,
                    'staff_notes': assign_data.note,
                    'priority': review_result.data.get('priority', 0)
                }
                
                if assign_data.deadline:
                    update_data['sla_deadline'] = assign_data.deadline
                else:
                    update_data['sla_deadline'] = (datetime.now() + timedelta(hours=24)).isoformat()
                
                supabase.from_('manual_review_queue') \
                    .update(update_data) \
                    .eq('id', review_id) \
                    .execute()
                
                # Log assignment
                supabase.from_('review_assignment_history') \
                    .insert({
                        'review_id': review_id,
                        'assigned_by': current_user.user_id,
                        'assigned_to': assign_data.staff_user_id,
                        'previous_assigned_to': None,
                        'action': 'assign_batch',
                        'note': assign_data.note or f"Batch assignment: {batch_result.data.get('batch_name', 'Unknown')}",
                        'created_at': now
                    }) \
                    .execute()
                
                # Update document status
                if review_result.data.get('file_id'):
                    supabase.from_('organization_files') \
                        .update({
                            'status': 'staff_review',
                            'status_updated_at': now,
                            'reviewed_by': assign_data.staff_user_id
                        }) \
                        .eq('id', review_result.data['file_id']) \
                        .execute()
                
                assigned_count += 1
        
        # Update batch status
        supabase.from_('upload_batches') \
            .update({
                'status': 'in_progress',
                'metadata': {
                    'assigned_to': assign_data.staff_user_id,
                    'assigned_by': current_user.user_id,
                    'assigned_at': now,
                    'assigned_count': assigned_count
                }
            }) \
            .eq('id', batch_id) \
            .execute()
        
        return {
            "success": True,
            "message": f"Assigned {assigned_count} files from batch to {staff_result.data.get('first_name', '')} {staff_result.data.get('last_name', '')}",
            "batch_id": batch_id,
            "assigned_count": assigned_count,
            "assigned_to": assign_data.staff_user_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error assigning batch: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign batch: {str(e)}"
        )
@router.get("/assignment-stats")
async def get_assignment_stats(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get assignment statistics.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Get all review queue data without group_by
        queue_result = supabase.from_('manual_review_queue') \
            .select('status') \
            .execute()
        
        # ✅ Group in Python
        stats = {
            'pending': 0,
            'assigned': 0,
            'in_progress': 0,
            'completed': 0,
            'rejected': 0
        }
        
        for item in (queue_result.data or []):
            status_val = item.get('status', 'pending')
            if status_val in stats:
                stats[status_val] += 1
        
        # Get staff workload summary
        staff_summary = []
        staff_result = supabase.from_('staff_profiles') \
            .select('id, first_name, last_name, email') \
            .eq('is_active', True) \
            .execute()
        
        for staff in (staff_result.data or []):
            # Get assigned reviews count
            assigned_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', staff['id']) \
                .in_('status', ['assigned', 'pending']) \
                .execute()
            
            # Get in-progress reviews count
            in_progress_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', staff['id']) \
                .eq('status', 'in_progress') \
                .execute()
            
            # Get completed reviews count
            completed_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', staff['id']) \
                .eq('status', 'completed') \
                .execute()
            
            assigned = assigned_result.count or 0
            in_progress = in_progress_result.count or 0
            completed = completed_result.count or 0
            
            staff_summary.append({
                'id': staff['id'],
                'name': f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or staff.get('email', 'Unknown'),
                'assigned': assigned,
                'in_progress': in_progress,
                'completed': completed,
                'total': assigned + in_progress + completed
            })
        
        return {
            "success": True,
            "stats": stats,
            "staff_summary": staff_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting assignment stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assignment stats: {str(e)}"
        )