# backend/utils/staff_workload.py
"""
Staff workload utilities for CarbonTally.
Shared functions for calculating staff workload across multiple modules.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, date
from database import get_supabase_client

async def get_staff_workload(supabase, staff_id: str) -> Dict:
    """
    Get staff workload statistics for a specific staff member.
    
    Args:
        supabase: Supabase client instance
        staff_id: Staff member ID
    
    Returns:
        Dict with workload statistics
    """
    try:
        # ✅ Get assigned count
        assigned_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('assigned_to', staff_id) \
            .eq('status', 'assigned') \
            .execute()
        assigned = assigned_result.count or 0
        
        # ✅ Get in_progress count
        in_progress_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('assigned_to', staff_id) \
            .eq('status', 'in_progress') \
            .execute()
        in_progress = in_progress_result.count or 0
        
        # ✅ Get completed count
        completed_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('assigned_to', staff_id) \
            .eq('status', 'completed') \
            .execute()
        completed = completed_result.count or 0
        
        workload = {
            'assigned': assigned,
            'in_progress': in_progress,
            'completed': completed,
            'total': assigned + in_progress
        }
        
        # Get workload score from staff_workload table if exists
        try:
            from datetime import date
            workload_result = supabase.from_('staff_workload') \
                .select('workload_score') \
                .eq('staff_id', staff_id) \
                .eq('date', date.today().isoformat()) \
                .maybe_single() \
                .execute()
            
            if workload_result and workload_result.data:
                workload['workload_score'] = workload_result.data.get('workload_score', 0)
            else:
                # Calculate simple workload score
                workload['workload_score'] = workload['total'] * 10 + workload['completed'] * 5
        except Exception:
            workload['workload_score'] = workload['total'] * 10 + workload['completed'] * 5
        
        return workload
        
    except Exception as e:
        print(f"⚠️ Error getting staff workload for {staff_id}: {e}")
        return {'assigned': 0, 'in_progress': 0, 'completed': 0, 'total': 0, 'workload_score': 0}
    
async def get_all_staff_workload(supabase, date_filter: Optional[str] = None) -> List[Dict]:
    """
    Get workload for all active staff members.
    
    Args:
        supabase: Supabase client instance
        date_filter: Optional date filter (YYYY-MM-DD)
    
    Returns:
        List of staff workload dictionaries
    """
    try:
        # Get all active staff
        staff_result = supabase.from_('staff_profiles') \
            .select('id, first_name, last_name, email, role, is_active') \
            .eq('is_active', True) \
            .execute()
        
        if not staff_result.data:
            return []
        
        staff_list = []
        for staff in staff_result.data:
            staff_id = staff.get('id')
            if not staff_id:
                continue
            
            # Get current workload
            workload = await get_staff_workload(supabase, staff_id)
            
            staff_list.append({
                'id': staff_id,
                'name': f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or staff.get('email', 'Unknown'),
                'email': staff.get('email', ''),
                'role': staff.get('role', 'staff'),
                'assigned_reviews': workload.get('assigned', 0),
                'in_progress_reviews': workload.get('in_progress', 0),
                'completed_today': workload.get('completed', 0),
                'total_active': workload.get('total', 0),
                'workload_score': workload.get('workload_score', 0)
            })
        
        # Sort by workload score (highest first)
        staff_list.sort(key=lambda x: x.get('workload_score', 0), reverse=True)
        
        return staff_list
        
    except Exception as e:
        print(f"⚠️ Error getting all staff workload: {e}")
        return []


async def get_staff_workload_from_table(supabase, staff_id: str) -> Dict:
    """
    Get staff workload from the staff_workload table.
    Used when you need the stored/calculated workload from the table.
    
    Args:
        supabase: Supabase client instance
        staff_id: Staff member ID
    
    Returns:
        Dict with workload data from the table
    """
    try:
        result = supabase.from_('staff_workload') \
            .select('*') \
            .eq('staff_id', staff_id) \
            .eq('date', date.today().isoformat()) \
            .maybe_single() \
            .execute()
        
        if result.data:
            return result.data
        
        return {
            'assigned_reviews': 0,
            'in_progress_reviews': 0,
            'completed_today': 0,
            'workload_score': 0,
            'pending_reviews': 0,
            'last_updated': None
        }
        
    except Exception as e:
        print(f"⚠️ Error getting staff workload from table for {staff_id}: {e}")
        return {
            'assigned_reviews': 0,
            'in_progress_reviews': 0,
            'completed_today': 0,
            'workload_score': 0,
            'pending_reviews': 0,
            'last_updated': None
        }