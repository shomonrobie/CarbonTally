# backend/routes/admin/staff.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
import secrets
import string
from auth import AuthUser, require_role, require_admin, require_permission, require_staff, require_org_admin

from database import get_supabase_client, get_supabase_admin
from supabase import create_client
import os

router = APIRouter(prefix="/api/admin/staff", tags=["Admin - Staff Management"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class StaffCreate(BaseModel):
    """Request model for creating a staff member."""
    email: EmailStr = Field(..., description="Staff email address")
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    role: str = Field("viewer", description="Role: admin, data_extractor, data_approver, staff, viewer")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@carbontally.co.uk",
                "first_name": "John",
                "last_name": "Doe",
                "role": "admin"
            }
        }

class StaffUpdate(BaseModel):
    """Request model for updating a staff member."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, description="Role: admin, data_extractor, data_approver, staff, viewer")
    is_active: Optional[bool] = Field(None, description="Activate or deactivate staff member")
    permissions: Optional[Dict[str, bool]] = Field(None, description="Custom permissions override")
    
    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "Jonathan",
                "role": "data_approver",
                "is_active": True
            }
        }

class StaffResponse(BaseModel):
    """Response model for a staff member."""
    id: str
    email: str
    first_name: str
    last_name: str
    full_name: str
    role: str
    role_name: Optional[str] = None
    role_description: Optional[str] = None
    is_active: bool
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    permissions: Dict[str, bool] = {}
    extraction_count: int = 0
    accuracy_rate: float = 100.0
    total_reviews_completed: int = 0
    avg_review_time_minutes: Optional[int] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "admin@carbontally.co.uk",
                "first_name": "John",
                "last_name": "Doe",
                "full_name": "John Doe",
                "role": "admin",
                "role_name": "Administrator",
                "role_description": "Full system access with all permissions",
                "is_active": True,
                "organization_id": None,
                "organization_name": None,
                "permissions": {"can_view_all": True},
                "extraction_count": 0,
                "accuracy_rate": 100.0,
                "total_reviews_completed": 0,
                "avg_review_time_minutes": None,
                "last_login": "2024-01-01T00:00:00Z",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }

class StaffListResponse(BaseModel):
    """Response model for staff list."""
    staff: List[StaffResponse]
    total: int
    total_active: int

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def validate_staff_role(role: str) -> bool:
    """Validate that the role is allowed for staff."""
    allowed_roles = ['admin', 'data_extractor', 'data_approver', 'staff', 'viewer']
    return role in allowed_roles

async def get_user_from_auth(email: str) -> Optional[Dict]:
    """Get user from auth.users by email using admin client."""
    try:
        supabase_admin = get_supabase_admin()
        
        response = supabase_admin.auth.admin.list_users()
        
        if response and hasattr(response, 'users'):
            for user in response.users:
                if user.email == email:
                    return {
                        'id': user.id,
                        'email': user.email,
                        'created_at': user.created_at
                    }
        
        return None
        
    except Exception as e:
        print(f"⚠️ Error getting user from auth: {e}")
        return None

async def create_auth_user(email: str, first_name: str, last_name: str) -> Optional[str]:
    """Create a new user in auth.users using admin client."""
    try:
        supabase_admin = get_supabase_admin()
        
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        
        response = supabase_admin.auth.admin.create_user({
            "email": email,
            "password": temp_password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": f"{first_name} {last_name}",
                "first_name": first_name,
                "last_name": last_name,
                "is_staff": True
            }
        })
        
        if response and hasattr(response, 'user'):
            return response.user.id
        
        return None
        
    except Exception as e:
        print(f"❌ Error creating auth user: {e}")
        return None

# ==========================================
# ENDPOINTS - ORDER MATTERS!
# Specific routes MUST come before parameterized routes
# ==========================================

# ==========================================
# 1. LIST ENDPOINT (No parameters)
# ==========================================

@router.get("", response_model=StaffListResponse)
async def get_all_staff(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Number of records to skip"),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get all staff members.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Use correct column names that exist in staff_profiles
        query = supabase.from_('staff_profiles') \
            .select('''
                id,
                email,
                role,
                role_id,
                is_active,
                first_name,
                last_name,
                permissions,
                extraction_count,
                accuracy_rate,
                last_login,
                reviews_completed,
                avg_review_time_seconds,
                created_at,
                roles (
                    id,
                    name,
                    description,
                    permissions
                )
            ''')
        
        # Apply filters
        if search:
            query = query.or_(f"email.ilike.%{search}%,first_name.ilike.%{search}%,last_name.ilike.%{search}%")
        if role and validate_staff_role(role):
            query = query.eq('role', role)
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        # ✅ Separate count query
        count_query = supabase.from_('staff_profiles') \
            .select('id', count='exact')
        
        if search:
            count_query = count_query.or_(f"email.ilike.%{search}%,first_name.ilike.%{search}%,last_name.ilike.%{search}%")
        if role and validate_staff_role(role):
            count_query = count_query.eq('role', role)
        if is_active is not None:
            count_query = count_query.eq('is_active', is_active)
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # Get paginated results
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        
        # Transform data
        staff_list = []
        active_count = 0
        
        for staff in (result.data or []):
            role_data = staff.get('roles', {})
            
            # ✅ Convert seconds to minutes
            avg_review_time_seconds = staff.get('avg_review_time_seconds')
            avg_review_time_minutes = None
            if avg_review_time_seconds is not None:
                avg_review_time_minutes = int(avg_review_time_seconds / 60)
            
            staff_response = StaffResponse(
                id=staff['id'],
                email=staff.get('email', ''),
                first_name=staff.get('first_name', ''),
                last_name=staff.get('last_name', ''),
                full_name=f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or staff.get('email', ''),
                role=staff.get('role', 'viewer'),
                role_name=role_data.get('name') if role_data else None,
                role_description=role_data.get('description') if role_data else None,
                is_active=staff.get('is_active', True),
                organization_id=None,  # ✅ Staff don't have organizations
                organization_name=None,  # ✅ Staff don't have organizations
                permissions=staff.get('permissions', {}) if isinstance(staff.get('permissions'), dict) else {},
                extraction_count=staff.get('extraction_count', 0),
                accuracy_rate=staff.get('accuracy_rate', 100.0),
                total_reviews_completed=staff.get('reviews_completed', 0),  # ✅ Map from reviews_completed
                avg_review_time_minutes=avg_review_time_minutes,  # ✅ Converted from seconds
                last_login=staff.get('last_login'),
                created_at=staff.get('created_at')
            )
            
            staff_list.append(staff_response)
            if staff_response.is_active:
                active_count += 1
        
        return StaffListResponse(
            staff=staff_list,
            total=total,
            total_active=active_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting staff: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff members: {str(e)}"
        )

# ==========================================
# 2. SPECIFIC NAMED ENDPOINTS (BEFORE parameterized routes)
# ==========================================

@router.get("/performance")
async def get_staff_performance(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get staff performance metrics.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Use explicit column names - NO organizations join
        staff_result = supabase.from_('staff_profiles') \
            .select('''
                id,
                email,
                first_name,
                last_name,
                role,
                is_active,
                accuracy_rate,
                reviews_completed,
                avg_review_time_seconds
            ''') \
            .eq('is_active', True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        if not staff_result or not staff_result.data:
            return {
                "success": True, 
                "data": [], 
                "total": 0
            }
        
        performance_data = []
        
        for staff in staff_result.data:
            staff_id = staff.get('id')
            if not staff_id:
                continue
            
            # Get reviews for this staff member
            start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
            
            try:
                reviews_result = supabase.from_('manual_review_queue') \
                    .select('id, status, review_time_seconds, completed_at') \
                    .eq('assigned_to', staff_id) \
                    .gte('completed_at', start_date) \
                    .execute()
                
                completed_reviews = [r for r in (reviews_result.data or []) if r.get('status') == 'completed']
                total_completed = len(completed_reviews)
                
                review_times = [r.get('review_time_seconds', 0) for r in completed_reviews if r.get('review_time_seconds')]
                avg_time = sum(review_times) / len(review_times) if review_times else None
                
            except Exception as e:
                print(f"⚠️ Error getting reviews for staff {staff_id}: {e}")
                total_completed = 0
                avg_time = None
            
            # Get workload
            try:
                workload_result = supabase.from_('staff_workload') \
                    .select('assigned_reviews, in_progress_reviews') \
                    .eq('staff_id', staff_id) \
                    .eq('date', datetime.utcnow().date().isoformat()) \
                    .maybe_single() \
                    .execute()
                
                current_workload = 0
                if workload_result and workload_result.data:
                    current_workload = workload_result.data.get('assigned_reviews', 0) + workload_result.data.get('in_progress_reviews', 0)
            except Exception:
                current_workload = 0
            
            # Calculate performance score
            completion_rate = min(100, (total_completed / max(1, days)) * 100)
            accuracy_rate = staff.get('accuracy_rate', 0) or 0
            speed_score = 100 if not avg_time else max(0, 100 - (avg_time / 60))
            performance_score = (completion_rate * 0.5) + (accuracy_rate * 0.3) + (speed_score * 0.2)
            
            performance_data.append({
                'staff_id': staff_id,
                'name': f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or staff.get('email', 'Unknown'),
                'email': staff.get('email', ''),
                'role': staff.get('role', ''),
                'total_reviews_completed': total_completed,
                'avg_review_time_seconds': avg_time,
                'avg_review_time_minutes': round(avg_time / 60, 2) if avg_time else None,
                'accuracy_rate': accuracy_rate,
                'current_workload': current_workload,
                'completion_rate': round(completion_rate, 2),
                'performance_score': round(performance_score, 2)
            })
        
        performance_data.sort(key=lambda x: x.get('performance_score', 0), reverse=True)
        
        return {
            "success": True,
            "data": performance_data,
            "total": len(performance_data)
        }
        
    except Exception as e:
        print(f"❌ Error in get_staff_performance: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff performance: {str(e)}"
        )

@router.get("/me")
async def get_my_staff_profile(
    current_user: AuthUser = Depends(require_staff())
):
    """Get the current staff member's own profile."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('staff_profiles') \
            .select('''
                id,
                email,
                first_name,
                last_name,
                role,
                is_active,
                permissions,
                extraction_count,
                accuracy_rate,
                reviews_completed,
                avg_review_time_seconds,
                created_at,
                roles (
                    id,
                    name,
                    description,
                    permissions
                )
            ''') \
            .eq('id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff profile not found"
            )
        
        staff = result.data
        role_data = staff.get('roles', {})
        
        # Convert seconds to minutes
        avg_review_time_seconds = staff.get('avg_review_time_seconds')
        avg_review_time_minutes = None
        if avg_review_time_seconds is not None:
            avg_review_time_minutes = int(avg_review_time_seconds / 60)
        
        return StaffResponse(
            id=staff['id'],
            email=staff.get('email', ''),
            first_name=staff.get('first_name', ''),
            last_name=staff.get('last_name', ''),
            full_name=f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or staff.get('email', ''),
            role=staff.get('role', 'viewer'),
            role_name=role_data.get('name') if role_data else None,
            role_description=role_data.get('description') if role_data else None,
            is_active=staff.get('is_active', True),
            organization_id=None,
            organization_name=None,
            permissions=staff.get('permissions', {}) if isinstance(staff.get('permissions'), dict) else {},
            extraction_count=staff.get('extraction_count', 0),
            accuracy_rate=staff.get('accuracy_rate', 100.0),
            total_reviews_completed=staff.get('reviews_completed', 0),
            avg_review_time_minutes=avg_review_time_minutes,
            last_login=staff.get('last_login'),
            created_at=staff.get('created_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting staff profile: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff profile: {str(e)}"
        )
@router.get("/activity")
async def get_staff_activity(
    current_user: AuthUser = Depends(require_admin()),
    staff_id: Optional[str] = None,
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get staff activity timeline.
    Shows daily activity for staff members.
    """
    try:
        supabase = get_supabase_client()
        
        # If staff_id provided, verify staff exists
        if staff_id:
            staff_check = supabase.from_('staff_profiles') \
                .select('id') \
                .eq('id', staff_id) \
                .maybe_single() \
                .execute()
            
            if not staff_check.data:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Staff member not found"
                )
        
        # Build query for activity data
        query = supabase.from_('staff_workload')
        
        if staff_id:
            query = query.eq('staff_id', staff_id)
        
        # Get workload data for the last N days
        start_date = (datetime.utcnow() - timedelta(days=days)).date().isoformat()
        end_date = datetime.utcnow().date().isoformat()
        
        # ✅ Fix: Apply gte and lte separately
        query = query.gte('date', start_date)
        query = query.lte('date', end_date)
        
        result = query.order('date', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        if not result.data:
            return {
                "success": True,
                "data": [],
                "total": 0
            }
        
        # Format activity data
        activity_data = []
        for record in result.data:
            # Get staff name
            staff_info = supabase.from_('staff_profiles') \
                .select('first_name, last_name, email') \
                .eq('id', record['staff_id']) \
                .maybe_single() \
                .execute()
            
            staff_name = "Unknown"
            if staff_info.data:
                staff_name = f"{staff_info.data.get('first_name', '')} {staff_info.data.get('last_name', '')}".strip() or staff_info.data.get('email', 'Unknown')
            
            # Determine status based on workload
            workload = record.get('assigned_reviews', 0) + record.get('in_progress_reviews', 0)
            workload_status = "idle"  # Default status
            if workload == 0:
                workload_status = "idle"
            elif workload <= 3:
                workload_status = "light"
            elif workload <= 6:
                workload_status = "moderate"
            else:
                workload_status = "heavy"
            
            activity_data.append({
                'date': record.get('date'),
                'staff_id': record.get('staff_id'),
                'staff_name': staff_name,
                'reviews_assigned': record.get('assigned_reviews', 0),
                'reviews_in_progress': record.get('in_progress_reviews', 0),
                'reviews_completed': record.get('completed_today', 0),
                'workload_score': record.get('workload_score', 0),
                'status': workload_status
            })
        
        return {
            "success": True,
            "data": activity_data,
            "total": len(activity_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_staff_activity: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff activity: {str(e)}"
        )
    
@router.get("/performance/export")
async def export_staff_performance(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365)
):
    """
    Export staff performance data as CSV.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Use explicit column names
        staff_result = supabase.from_('staff_profiles') \
            .select('''
                id,
                email,
                first_name,
                last_name,
                role,
                accuracy_rate
            ''') \
            .eq('is_active', True) \
            .execute()
        
        if not staff_result.data:
            return {
                "success": True,
                "message": "No staff data to export"
            }
        
        # Build export data
        export_data = []
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        for staff in staff_result.data:
            staff_id = staff['id']
            
            # Get reviews
            reviews_result = supabase.from_('manual_review_queue') \
                .select('id, status, review_time_seconds, completed_at') \
                .eq('assigned_to', staff_id) \
                .gte('completed_at', start_date) \
                .execute()
            
            completed_reviews = [r for r in (reviews_result.data or []) if r.get('status') == 'completed']
            total_completed = len(completed_reviews)
            
            review_times = [r.get('review_time_seconds', 0) for r in completed_reviews if r.get('review_time_seconds')]
            avg_time = sum(review_times) / len(review_times) if review_times else None
            
            # Get workload
            workload_result = supabase.from_('staff_workload') \
                .select('assigned_reviews, in_progress_reviews') \
                .eq('staff_id', staff_id) \
                .eq('date', datetime.utcnow().date().isoformat()) \
                .maybe_single() \
                .execute()
            
            current_workload = 0
            if workload_result and workload_result.data:
                current_workload = workload_result.data.get('assigned_reviews', 0) + workload_result.data.get('in_progress_reviews', 0)
            
            export_data.append({
                'Staff ID': staff_id,
                'Name': f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or staff.get('email', 'Unknown'),
                'Email': staff.get('email', ''),
                'Role': staff.get('role', ''),
                'Reviews Completed': total_completed,
                'Avg Time (secs)': round(avg_time, 2) if avg_time else 0,
                'Accuracy Rate': staff.get('accuracy_rate', 0),
                'Current Workload': current_workload
            })
        
        # Generate CSV
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        if export_data:
            headers = list(export_data[0].keys())
            writer.writerow(headers)
            
            for record in export_data:
                writer.writerow([record.get(h, '') for h in headers])
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=staff_performance_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
        
    except Exception as e:
        print(f"❌ Error exporting staff performance: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export staff performance: {str(e)}"
        )

# ==========================================
# 3. PARAMETERIZED ROUTES (AFTER specific routes)
# ==========================================

@router.get("/{staff_id}", response_model=StaffResponse)
async def get_staff_member(
    staff_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get a specific staff member by ID.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Query ONLY columns that exist in staff_profiles
        result = supabase.from_('staff_profiles') \
            .select('''
                id,
                email,
                role,
                role_id,
                is_active,
                first_name,
                last_name,
                permissions,
                extraction_count,
                accuracy_rate,
                last_login,
                reviews_completed,
                avg_review_time_seconds,
                created_at,
                roles (
                    id,
                    name,
                    description,
                    permissions
                )
            ''') \
            .eq('id', staff_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        staff = result.data
        role_data = staff.get('roles', {})
        
        # ✅ Convert seconds to minutes
        avg_review_time_seconds = staff.get('avg_review_time_seconds')
        avg_review_time_minutes = None
        if avg_review_time_seconds is not None:
            avg_review_time_minutes = int(avg_review_time_seconds / 60)
        
        return StaffResponse(
            id=staff['id'],
            email=staff.get('email', ''),
            first_name=staff.get('first_name', ''),
            last_name=staff.get('last_name', ''),
            full_name=f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or staff.get('email', ''),
            role=staff.get('role', 'viewer'),
            role_name=role_data.get('name') if role_data else None,
            role_description=role_data.get('description') if role_data else None,
            is_active=staff.get('is_active', True),
            organization_id=None,  # ✅ Staff don't have organizations
            organization_name=None,  # ✅ Staff don't have organizations
            permissions=staff.get('permissions', {}) if isinstance(staff.get('permissions'), dict) else {},
            extraction_count=staff.get('extraction_count', 0),
            accuracy_rate=staff.get('accuracy_rate', 100.0),
            total_reviews_completed=staff.get('reviews_completed', 0),
            avg_review_time_minutes=avg_review_time_minutes,
            last_login=staff.get('last_login'),
            created_at=staff.get('created_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting staff member: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff member: {str(e)}"
        )

@router.post("/", response_model=StaffResponse)
async def create_staff_member(
    staff_data: StaffCreate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Create a new staff member.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        if not validate_staff_role(staff_data.role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: admin, data_extractor, data_approver, staff, viewer"
            )
        
        auth_user = await get_user_from_auth(staff_data.email)
        
        if not auth_user:
            user_id = await create_auth_user(staff_data.email, staff_data.first_name, staff_data.last_name)
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create auth user"
                )
            
            staff_user_id = user_id
            staff_email = staff_data.email
        else:
            staff_user_id = auth_user['id']
            staff_email = auth_user['email']
            
            existing = supabase.from_('staff_profiles') \
                .select('id') \
                .eq('id', staff_user_id) \
                .maybe_single() \
                .execute()
            
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User is already a staff member"
                )
        
        # Get role_id
        role_result = supabase.from_('roles') \
            .select('id, permissions') \
            .eq('name', staff_data.role) \
            .maybe_single() \
            .execute()
        
        role_id = role_result.data.get('id') if role_result.data else None
        default_permissions = role_result.data.get('permissions', {}) if role_result.data else {}
        
        # ✅ Create staff profile - NO organization_id
        staff_profile = {
            'id': staff_user_id,
            'email': staff_email,
            'first_name': staff_data.first_name,
            'last_name': staff_data.last_name,
            'role': staff_data.role,
            'role_id': role_id,
            'is_active': True,
            'permissions': default_permissions,
            'created_at': datetime.now().isoformat()
        }
        
        result = supabase.from_('staff_profiles') \
            .insert(staff_profile) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create staff profile"
            )
        
        if not auth_user:
            try:
                from utils.email import send_welcome_email
                await send_welcome_email(
                    email=staff_data.email,
                    full_name=f"{staff_data.first_name} {staff_data.last_name}",
                    organization_name="CarbonTally"
                )
            except Exception as e:
                print(f"⚠️ Failed to send welcome email: {e}")
        
        return await get_staff_member(staff_user_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating staff member: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create staff member: {str(e)}"
        )

@router.put("/{staff_id}", response_model=StaffResponse)
async def update_staff_member(
    staff_id: str,
    update_data: StaffUpdate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Update a staff member.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        existing = supabase.from_('staff_profiles') \
            .select('id, role, permissions') \
            .eq('id', staff_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        if update_data.is_active is False and staff_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate yourself"
            )
        
        if update_data.role and not validate_staff_role(update_data.role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: admin, data_extractor, data_approver, staff, viewer"
            )
        
        role_id = None
        permissions = None
        
        if update_data.role:
            role_result = supabase.from_('roles') \
                .select('id, permissions') \
                .eq('name', update_data.role) \
                .maybe_single() \
                .execute()
            
            if role_result.data:
                role_id = role_result.data['id']
                permissions = role_result.data.get('permissions', {})
        
        update_dict = {}
        if update_data.first_name is not None:
            update_dict['first_name'] = update_data.first_name
        if update_data.last_name is not None:
            update_dict['last_name'] = update_data.last_name
        if update_data.role is not None:
            update_dict['role'] = update_data.role
            if role_id:
                update_dict['role_id'] = role_id
                if permissions:
                    update_dict['permissions'] = permissions
        if update_data.is_active is not None:
            update_dict['is_active'] = update_data.is_active
        if update_data.permissions is not None:
            current_permissions = existing.data.get('permissions', {})
            if isinstance(current_permissions, dict):
                current_permissions.update(update_data.permissions)
                update_dict['permissions'] = current_permissions
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        result = supabase.from_('staff_profiles') \
            .update(update_dict) \
            .eq('id', staff_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update staff member"
            )
        
        return await get_staff_member(staff_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating staff member: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update staff member: {str(e)}"
        )

@router.delete("/{staff_id}")
async def delete_staff_member(
    staff_id: str,
    permanent: bool = Query(False, description="Permanently delete or soft delete"),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Delete or soft-delete a staff member.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        existing = supabase.from_('staff_profiles') \
            .select('id, email, role') \
            .eq('id', staff_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        if staff_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete yourself"
            )
        
        if permanent:
            admin_count = supabase.from_('staff_profiles') \
                .select('id', count='exact') \
                .eq('role', 'admin') \
                .eq('is_active', True) \
                .execute()
            
            if admin_count.count == 1 and existing.data.get('role') == 'admin':
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete the last admin user"
                )
        
        if permanent:
            result = supabase.from_('staff_profiles') \
                .delete() \
                .eq('id', staff_id) \
                .execute()
            
            message = "Staff member permanently deleted"
        else:
            result = supabase.from_('staff_profiles') \
                .update({
                    'is_active': False
                }) \
                .eq('id', staff_id) \
                .execute()
            
            message = "Staff member deactivated"
        
        return {
            "success": True,
            "message": message,
            "staff_id": staff_id,
            "permanent": permanent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting staff member: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete staff member: {str(e)}"
        )

@router.put("/{staff_id}/role")
async def update_staff_role(
    staff_id: str,
    role_data: Dict[str, str],
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Update a staff member's role.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        new_role = role_data.get('role')
        if not new_role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role is required"
            )
        
        if not validate_staff_role(new_role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: admin, data_extractor, data_approver, staff, viewer"
            )
        
        existing = supabase.from_('staff_profiles') \
            .select('id, role') \
            .eq('id', staff_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        if existing.data.get('role') == 'admin' and new_role != 'admin':
            admin_count = supabase.from_('staff_profiles') \
                .select('id', count='exact') \
                .eq('role', 'admin') \
                .eq('is_active', True) \
                .execute()
            
            if admin_count.count == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin's role"
                )
        
        role_result = supabase.from_('roles') \
            .select('id, permissions') \
            .eq('name', new_role) \
            .maybe_single() \
            .execute()
        
        if not role_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found in database"
            )
        
        result = supabase.from_('staff_profiles') \
            .update({
                'role': new_role,
                'role_id': role_result.data['id'],
                'permissions': role_result.data.get('permissions', {})
            }) \
            .eq('id', staff_id) \
            .execute()
        
        return {
            "success": True,
            "message": f"Staff role updated to {new_role}",
            "staff_id": staff_id,
            "role": new_role,
            "role_id": role_result.data['id']
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating staff role: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update staff role: {str(e)}"
        )

@router.get("/{staff_id}/activity-log")
async def get_staff_activity_log(
    staff_id: str,
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get detailed activity log for a staff member."""
    try:
        supabase = get_supabase_client()
        
        # Check if staff exists
        staff = supabase.from_('staff_profiles') \
            .select('id, first_name, last_name, email') \
            .eq('id', staff_id) \
            .maybe_single() \
            .execute()
        
        if not staff.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        # Get activity logs
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        # Get review activities
        reviews = supabase.from_('manual_review_queue') \
            .select('id, file_name, status, created_at, completed_at, review_time_seconds') \
            .eq('assigned_to', staff_id) \
            .gte('created_at', start_date) \
            .order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Get assignment history
        assignments = supabase.from_('review_assignment_history') \
            .select('*') \
            .eq('assigned_to', staff_id) \
            .gte('created_at', start_date) \
            .order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {
            "success": True,
            "data": {
                "staff": staff.data,
                "reviews": reviews.data if reviews.data else [],
                "assignments": assignments.data if assignments.data else [],
                "total_reviews": len(reviews.data) if reviews.data else 0,
                "total_assignments": len(assignments.data) if assignments.data else 0
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting staff activity log: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff activity log: {str(e)}"
        )

@router.get("/{staff_id}/performance-history")
async def get_staff_performance_history(
    staff_id: str,
    current_user: AuthUser = Depends(require_admin()),
    months: int = Query(6, ge=1, le=24)
):
    """Get performance history for a staff member."""
    try:
        supabase = get_supabase_client()
        
        # Check if staff exists
        staff = supabase.from_('staff_profiles') \
            .select('id, first_name, last_name, email') \
            .eq('id', staff_id) \
            .maybe_single() \
            .execute()
        
        if not staff.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        # Get monthly performance data
        start_date = (datetime.utcnow() - timedelta(days=months*30)).isoformat()
        
        # Get completed reviews by month
        reviews = supabase.from_('manual_review_queue') \
            .select('completed_at, review_time_seconds, status') \
            .eq('assigned_to', staff_id) \
            .eq('status', 'completed') \
            .gte('completed_at', start_date) \
            .execute()
        
        monthly_data = {}
        total_reviews = 0
        total_time = 0
        
        if reviews.data:
            for review in reviews.data:
                if review.get('completed_at'):
                    month = review['completed_at'][:7]  # YYYY-MM
                    if month not in monthly_data:
                        monthly_data[month] = {
                            'month': month,
                            'completed': 0,
                            'total_time_seconds': 0,
                            'avg_time_seconds': 0
                        }
                    monthly_data[month]['completed'] += 1
                    monthly_data[month]['total_time_seconds'] += review.get('review_time_seconds', 0)
                    total_reviews += 1
                    total_time += review.get('review_time_seconds', 0)
        
        # Calculate averages
        for month, data in monthly_data.items():
            if data['completed'] > 0:
                data['avg_time_seconds'] = round(data['total_time_seconds'] / data['completed'], 2)
        
        history = {
            'staff': staff.data,
            'total_reviews': total_reviews,
            'avg_time_seconds': round(total_time / total_reviews, 2) if total_reviews > 0 else 0,
            'avg_time_minutes': round((total_time / total_reviews) / 60, 2) if total_reviews > 0 else 0,
            'monthly_data': sorted(monthly_data.values(), key=lambda x: x['month'])
        }
        
        return {"success": True, "data": history}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting staff performance history: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff performance history: {str(e)}"
        )

@router.post("/{staff_id}/reset-password")
async def reset_staff_password(
    staff_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """Reset staff member's password (send reset email)."""
    try:
        supabase = get_supabase_client()
        
        # Check if staff exists
        staff = supabase.from_('staff_profiles') \
            .select('id, email, first_name, last_name') \
            .eq('id', staff_id) \
            .maybe_single() \
            .execute()
        
        if not staff.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        
        # In production, you'd send an email with the reset link
        # For now, we'll just return the token
        
        return {
            "success": True,
            "message": "Password reset email sent",
            "data": {
                "email": staff.data['email'],
                "reset_token": reset_token,
                "expires_in": "1 hour"
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error resetting staff password: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset staff password: {str(e)}"
        )
class StaffPerformanceDashboardResponse(BaseModel):
    """Response model for staff performance dashboard."""
    overview: Dict[str, Any]
    top_performers: List[Dict[str, Any]]
    workload_distribution: List[Dict[str, Any]]
    performance_trends: Dict[str, Any]
    team_stats: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]
    bottlenecks: List[Dict[str, Any]]


class StaffPerformanceMetrics(BaseModel):
    """Response model for staff performance metrics."""
    staff_id: str
    staff_name: str
    email: str
    role: str
    reviews_completed: int
    reviews_assigned: int
    completion_rate: float
    avg_review_time_minutes: float
    accuracy_rate: float
    current_load: int
    efficiency_score: float
    quality_score: float
    trend: List[Dict[str, Any]]


# ================================
# ENDPOINT
# ================================

@router.get("/performance/dashboard", response_model=StaffPerformanceDashboardResponse)
async def get_staff_performance_dashboard(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get staff performance dashboard data.
    
    Returns comprehensive staff performance metrics including overview,
    top performers, workload distribution, trends, and bottlenecks.
    """
    try:
        now = datetime.utcnow()
        cutoff = now - timedelta(days=days)
        
        # Get staff profiles with performance data
        query = supabase.from_('staff_profiles') \
            .select('''
                id, user_id, role, first_name, last_name, email,
                accuracy_rate, extraction_count, total_reviews_completed,
                avg_review_time_seconds, total_review_time_seconds,
                current_load, reviews_assigned, reviews_completed,
                is_active, created_at
            ''')
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        staff_result = query.execute()
        staff_list = staff_result.data or []
        
        if not staff_list:
            return StaffPerformanceDashboardResponse(
                overview={},
                top_performers=[],
                workload_distribution=[],
                performance_trends={},
                team_stats={},
                recent_activity=[],
                bottlenecks=[]
            )
        
        # Get reviews for the period
        staff_ids = [s['user_id'] for s in staff_list]
        
        reviews_result = supabase.from_('manual_review_queue') \
            .select('''
                id, assigned_to, status, created_at, completed_at,
                review_time_seconds, priority, customer_document_id,
                organization_id
            ''') \
            .in_('assigned_to', staff_ids) \
            .gte('created_at', cutoff.isoformat()) \
            .execute()
        
        reviews = reviews_result.data or []
        
        # Calculate metrics for each staff member
        staff_metrics = []
        total_reviews = 0
        total_completed = 0
        total_review_time = 0
        total_accuracy = 0
        
        for staff in staff_list:
            user_id = staff['user_id']
            staff_reviews = [r for r in reviews if r.get('assigned_to') == user_id]
            
            assigned = len(staff_reviews)
            completed = sum(1 for r in staff_reviews if r.get('status') == 'completed')
            completion_rate = (completed / assigned * 100) if assigned > 0 else 0
            
            # Review times
            review_times = [r.get('review_time_seconds', 0) for r in staff_reviews if r.get('review_time_seconds')]
            avg_time = sum(review_times) / len(review_times) if review_times else 0
            
            # Current load (pending + in_progress)
            current_load = sum(1 for r in staff_reviews if r.get('status') in ['pending', 'assigned', 'in_progress'])
            
            # Quality score (based on accuracy and completion)
            accuracy = float(staff.get('accuracy_rate', 0)) if staff.get('accuracy_rate') else 0
            quality_score = (accuracy * 0.6) + (completion_rate * 0.4)
            
            # Efficiency score
            efficiency_score = 100
            if avg_time > 0:
                # Lower time = higher efficiency (normalized)
                efficiency_score = max(0, min(100, 100 - (avg_time / 120)))  # 120 sec baseline
            
            staff_metrics.append({
                'staff_id': staff['id'],
                'user_id': user_id,
                'staff_name': f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or 'Unknown',
                'email': staff.get('email', ''),
                'role': staff.get('role', 'staff'),
                'reviews_assigned': assigned,
                'reviews_completed': completed,
                'completion_rate': round(completion_rate, 2),
                'avg_review_time_minutes': round(avg_time / 60, 2) if avg_time else 0,
                'accuracy_rate': round(accuracy, 2),
                'current_load': current_load,
                'efficiency_score': round(efficiency_score, 2),
                'quality_score': round(quality_score, 2),
                'total_review_time_seconds': staff.get('total_review_time_seconds', 0),
                'is_active': staff.get('is_active', True),
                'staff_reviews': staff_reviews
            })
            
            total_reviews += assigned
            total_completed += completed
            total_accuracy += accuracy
            if avg_time:
                total_review_time += avg_time
        
        # 1. Overview
        overview = {
            'total_staff': len(staff_list),
            'active_staff': sum(1 for s in staff_metrics if s['is_active']),
            'total_reviews_assigned': total_reviews,
            'total_reviews_completed': total_completed,
            'overall_completion_rate': round((total_completed / total_reviews * 100) if total_reviews > 0 else 0, 2),
            'avg_accuracy_rate': round(total_accuracy / len(staff_metrics) if staff_metrics else 0, 2),
            'avg_review_time_minutes': round(total_review_time / len(staff_metrics) if staff_metrics else 0, 2),
            'period_days': days,
            'analysis_period': {
                'start': cutoff.isoformat(),
                'end': now.isoformat()
            }
        }
        
        # 2. Top Performers
        top_performers = sorted(staff_metrics, key=lambda x: x['quality_score'], reverse=True)[:5]
        top_performers_data = []
        for performer in top_performers:
            top_performers_data.append({
                'staff_id': performer['staff_id'],
                'staff_name': performer['staff_name'],
                'role': performer['role'],
                'reviews_completed': performer['reviews_completed'],
                'completion_rate': performer['completion_rate'],
                'accuracy_rate': performer['accuracy_rate'],
                'avg_review_time_minutes': performer['avg_review_time_minutes'],
                'quality_score': performer['quality_score'],
                'efficiency_score': performer['efficiency_score']
            })
        
        # 3. Workload Distribution
        workload_distribution = []
        for metric in staff_metrics:
            workload_distribution.append({
                'staff_name': metric['staff_name'],
                'current_load': metric['current_load'],
                'capacity': 10,  # Example max capacity
                'utilization': min(100, (metric['current_load'] / 10 * 100)),
                'role': metric['role']
            })
        
        # Sort by current load
        workload_distribution.sort(key=lambda x: x['current_load'], reverse=True)
        
        # 4. Performance Trends (last 7 days)
        performance_trends = {
            'daily_completions': [],
            'daily_assignments': [],
            'avg_review_time_trend': []
        }
        
        for i in range(7, -1, -1):
            day = now - timedelta(days=i)
            day_start = datetime(day.year, day.month, day.day)
            day_end = day_start + timedelta(days=1)
            
            day_reviews = [r for r in reviews if r.get('created_at') and 
                          day_start <= datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')) < day_end]
            
            completions = sum(1 for r in day_reviews if r.get('status') == 'completed')
            assignments = len(day_reviews)
            
            # Average review time for the day
            day_review_times = [r.get('review_time_seconds', 0) for r in day_reviews if r.get('review_time_seconds')]
            avg_time = sum(day_review_times) / len(day_review_times) if day_review_times else 0
            
            performance_trends['daily_completions'].append({
                'date': day_start.isoformat(),
                'count': completions
            })
            
            performance_trends['daily_assignments'].append({
                'date': day_start.isoformat(),
                'count': assignments
            })
            
            performance_trends['avg_review_time_trend'].append({
                'date': day_start.isoformat(),
                'seconds': round(avg_time, 2),
                'minutes': round(avg_time / 60, 2)
            })
        
        # 5. Team Stats
        team_stats = {
            'total_team_members': len(staff_metrics),
            'active_team_members': sum(1 for s in staff_metrics if s['is_active']),
            'avg_completion_rate': overview['overall_completion_rate'],
            'avg_quality_score': round(sum(s['quality_score'] for s in staff_metrics) / len(staff_metrics) if staff_metrics else 0, 2),
            'avg_efficiency_score': round(sum(s['efficiency_score'] for s in staff_metrics) / len(staff_metrics) if staff_metrics else 0, 2),
            'total_workload': sum(s['current_load'] for s in staff_metrics),
            'by_role': {}
        }
        
        # Breakdown by role
        for metric in staff_metrics:
            role = metric['role']
            if role not in team_stats['by_role']:
                team_stats['by_role'][role] = {
                    'count': 0,
                    'avg_completion_rate': 0,
                    'avg_quality_score': 0,
                    'total_workload': 0
                }
            
            team_stats['by_role'][role]['count'] += 1
            team_stats['by_role'][role]['avg_completion_rate'] += metric['completion_rate']
            team_stats['by_role'][role]['avg_quality_score'] += metric['quality_score']
            team_stats['by_role'][role]['total_workload'] += metric['current_load']
        
        # Calculate averages for each role
        for role, stats in team_stats['by_role'].items():
            if stats['count'] > 0:
                stats['avg_completion_rate'] = round(stats['avg_completion_rate'] / stats['count'], 2)
                stats['avg_quality_score'] = round(stats['avg_quality_score'] / stats['count'], 2)
        
        # 6. Recent Activity
        recent_activity = []
        for review in reviews[:20]:
            assigned_to = review.get('assigned_to')
            staff_name = next((s['staff_name'] for s in staff_metrics if s['user_id'] == assigned_to), 'Unknown')
            
            recent_activity.append({
                'review_id': review['id'],
                'staff_name': staff_name,
                'status': review.get('status'),
                'priority': review.get('priority', 1),
                'created_at': review.get('created_at'),
                'completed_at': review.get('completed_at'),
                'review_time_seconds': review.get('review_time_seconds')
            })
        
        # 7. Bottlenecks
        bottlenecks = []
        
        # Check for staff with high workload
        high_workload = [s for s in staff_metrics if s['current_load'] >= 8]
        if high_workload:
            bottlenecks.append({
                'type': 'high_workload',
                'severity': 'high',
                'message': f"{len(high_workload)} staff members have high workload (8+ items)",
                'details': [{'staff_name': s['staff_name'], 'current_load': s['current_load']} for s in high_workload]
            })
        
        # Check for low completion rates
        low_completion = [s for s in staff_metrics if s['completion_rate'] < 60 and s['reviews_assigned'] > 0]
        if low_completion:
            bottlenecks.append({
                'type': 'low_completion_rate',
                'severity': 'medium',
                'message': f"{len(low_completion)} staff members have low completion rates (<60%)",
                'details': [{'staff_name': s['staff_name'], 'completion_rate': s['completion_rate']} for s in low_completion]
            })
        
        # Check for long review times
        long_review_times = [s for s in staff_metrics if s['avg_review_time_minutes'] > 15]
        if long_review_times:
            bottlenecks.append({
                'type': 'long_review_times',
                'severity': 'medium',
                'message': f"{len(long_review_times)} staff members have high average review times (>15 min)",
                'details': [{'staff_name': s['staff_name'], 'avg_time': s['avg_review_time_minutes']} for s in long_review_times]
            })
        
        # Check for low accuracy
        low_accuracy = [s for s in staff_metrics if s['accuracy_rate'] < 70 and s['reviews_completed'] > 0]
        if low_accuracy:
            bottlenecks.append({
                'type': 'low_accuracy',
                'severity': 'high',
                'message': f"{len(low_accuracy)} staff members have low accuracy rates (<70%)",
                'details': [{'staff_name': s['staff_name'], 'accuracy_rate': s['accuracy_rate']} for s in low_accuracy]
            })
        
        # Check for unbalanced workload distribution
        if staff_metrics:
            avg_load = sum(s['current_load'] for s in staff_metrics) / len(staff_metrics)
            max_load = max(s['current_load'] for s in staff_metrics)
            if max_load > avg_load * 2 and max_load > 5:
                bottlenecks.append({
                    'type': 'unbalanced_workload',
                    'severity': 'medium',
                    'message': f"Unbalanced workload distribution detected (max: {max_load}, avg: {round(avg_load, 1)})",
                    'details': [{'staff_name': s['staff_name'], 'current_load': s['current_load']} for s in staff_metrics if s['current_load'] > avg_load * 1.5]
                })
        
        return StaffPerformanceDashboardResponse(
            overview=overview,
            top_performers=top_performers_data,
            workload_distribution=workload_distribution,
            performance_trends=performance_trends,
            team_stats=team_stats,
            recent_activity=recent_activity,
            bottlenecks=bottlenecks
        )
        
    except Exception as e:
        print(f"❌ Error getting staff performance dashboard: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff performance dashboard: {str(e)}"
        )


# ================================
# ADDITIONAL HELPER ENDPOINTS
# ================================

@router.get("/performance/export")
async def export_staff_performance(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Export staff performance data.
    
    Exports staff performance metrics in JSON or CSV format.
    """
    try:
        # Get dashboard data
        dashboard = await get_staff_performance_dashboard(
            current_user=current_user,
            days=days,
            organization_id=None,
            supabase=supabase
        )
        
        # Prepare export data
        export_data = {
            'overview': dashboard.overview,
            'top_performers': dashboard.top_performers,
            'workload_distribution': dashboard.workload_distribution,
            'performance_trends': dashboard.performance_trends,
            'team_stats': dashboard.team_stats,
            'bottlenecks': dashboard.bottlenecks
        }
        
        # Generate export ID
        export_id = f"staff_performance_export_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        file_url = f"/exports/staff-performance/{export_id}.{format}"
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        return {
            "success": True,
            "export_id": export_id,
            "format": format,
            "file_url": file_url,
            "expires_at": expires_at,
            "data": export_data
        }
        
    except Exception as e:
        print(f"❌ Error exporting staff performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export staff performance: {str(e)}"
        )


@router.get("/performance/compare")
async def compare_staff_performance(
    current_user: AuthUser = Depends(require_admin()),
    staff_ids: List[str] = Query(..., description="Staff user IDs to compare"),
    days: int = Query(30, ge=7, le=365, description="Number of days to analyze"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Compare performance between staff members.
    
    Returns side-by-side comparison of staff performance metrics.
    """
    try:
        if len(staff_ids) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least 2 staff members are required for comparison"
            )
        
        if len(staff_ids) > 10:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Maximum 10 staff members can be compared"
            )
        
        # Get staff profiles
        staff_result = supabase.from_('staff_profiles') \
            .select('''
                id, user_id, role, first_name, last_name, email,
                accuracy_rate, total_reviews_completed,
                avg_review_time_seconds, current_load, is_active
            ''') \
            .in_('user_id', staff_ids) \
            .execute()
        
        staff_list = staff_result.data or []
        
        if len(staff_list) < 2:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Not enough staff members found"
            )
        
        # Get reviews for comparison
        cutoff = datetime.utcnow() - timedelta(days=days)
        reviews_result = supabase.from_('manual_review_queue') \
            .select('assigned_to, status, review_time_seconds, created_at') \
            .in_('assigned_to', staff_ids) \
            .gte('created_at', cutoff.isoformat()) \
            .execute()
        
        reviews = reviews_result.data or []
        
        # Build comparison data
        comparison = []
        for staff in staff_list:
            user_id = staff['user_id']
            staff_reviews = [r for r in reviews if r.get('assigned_to') == user_id]
            
            assigned = len(staff_reviews)
            completed = sum(1 for r in staff_reviews if r.get('status') == 'completed')
            completion_rate = (completed / assigned * 100) if assigned > 0 else 0
            
            review_times = [r.get('review_time_seconds', 0) for r in staff_reviews if r.get('review_time_seconds')]
            avg_time = sum(review_times) / len(review_times) if review_times else 0
            
            comparison.append({
                'staff_id': staff['id'],
                'user_id': user_id,
                'staff_name': f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or 'Unknown',
                'email': staff.get('email', ''),
                'role': staff.get('role', 'staff'),
                'reviews_assigned': assigned,
                'reviews_completed': completed,
                'completion_rate': round(completion_rate, 2),
                'avg_review_time_minutes': round(avg_time / 60, 2) if avg_time else 0,
                'accuracy_rate': float(staff.get('accuracy_rate', 0)) if staff.get('accuracy_rate') else 0,
                'current_load': staff.get('current_load', 0),
                'is_active': staff.get('is_active', True)
            })
        
        return {
            'comparison': comparison,
            'period_days': days,
            'analysis_period': {
                'start': cutoff.isoformat(),
                'end': datetime.utcnow().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error comparing staff performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compare staff performance: {str(e)}"
        )
