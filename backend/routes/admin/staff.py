# backend/routes/admin/staff.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
import secrets
from auth import AuthUser, require_role, require_permission
from database import get_supabase_client

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
    organization_id: Optional[str] = Field(None, description="Organization ID if staff belongs to one")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@carbontally.co.uk",
                "first_name": "John",
                "last_name": "Doe",
                "role": "admin",
                "organization_id": None
            }
        }

class StaffUpdate(BaseModel):
    """Request model for updating a staff member."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    role: Optional[str] = Field(None, description="Role: admin, data_extractor, data_approver, staff, viewer")
    is_active: Optional[bool] = Field(None, description="Activate or deactivate staff member")
    organization_id: Optional[str] = Field(None, description="Organization ID")
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

async def get_user_from_auth(supabase_client, email: str) -> Optional[Dict]:
    """Get user from auth.users by email."""
    try:
        result = supabase_client.from_('auth.users') \
            .select('id, email, created_at') \
            .eq('email', email) \
            .maybe_single() \
            .execute()
        
        if result and result.data:
            return result.data
        return None
        
    except Exception as e:
        print(f"⚠️ Error getting user from auth: {e}")
        return None

async def create_auth_user(supabase_client, email: str, password: str, metadata: Dict) -> Optional[str]:
    """Create a new user in auth.users."""
    try:
        from supabase import Client
        
        # Generate temporary password
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(16))
        
        # Create user
        response = supabase_client.auth.admin.create_user({
            "email": email,
            "password": temp_password,
            "email_confirm": True,
            "user_metadata": {
                "full_name": metadata.get('full_name', ''),
                "is_staff": True,
                **metadata
            }
        })
        
        if response and hasattr(response, 'user'):
            return response.user.id
        
        return None
        
    except Exception as e:
        print(f"❌ Error creating auth user: {e}")
        return None

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/", response_model=StaffListResponse)
async def get_all_staff(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
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
        
        # Build query
        query = supabase.from_('staff_profiles') \
            .select('''
                id,
                role,
                role_id,
                is_active,
                first_name,
                last_name,
                permissions,
                extraction_count,
                accuracy_rate,
                last_login,
                total_reviews_completed,
                avg_review_time_minutes,
                created_at,
                organization_id,
                organizations (
                    id,
                    name
                ),
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
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        # Get total count
        count_query = query.clone()
        count_result = count_query.select('id', count='exact').execute()
        total = count_result.count or 0
        
        # Get paginated results
        query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
        result = query.execute()
        
        # Transform data
        staff_list = []
        active_count = 0
        
        for staff in result.data:
            org_data = staff.get('organizations', {})
            role_data = staff.get('roles', {})
            
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
                organization_id=staff.get('organization_id'),
                organization_name=org_data.get('name') if org_data else None,
                permissions=staff.get('permissions', {}) if isinstance(staff.get('permissions'), dict) else {},
                extraction_count=staff.get('extraction_count', 0),
                accuracy_rate=staff.get('accuracy_rate', 100.0),
                total_reviews_completed=staff.get('total_reviews_completed', 0),
                avg_review_time_minutes=staff.get('avg_review_time_minutes'),
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff members: {str(e)}"
        )

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
                total_reviews_completed,
                avg_review_time_minutes,
                created_at,
                organization_id,
                organizations (
                    id,
                    name
                ),
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
        org_data = staff.get('organizations', {})
        role_data = staff.get('roles', {})
        
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
            organization_id=staff.get('organization_id'),
            organization_name=org_data.get('name') if org_data else None,
            permissions=staff.get('permissions', {}) if isinstance(staff.get('permissions'), dict) else {},
            extraction_count=staff.get('extraction_count', 0),
            accuracy_rate=staff.get('accuracy_rate', 100.0),
            total_reviews_completed=staff.get('total_reviews_completed', 0),
            avg_review_time_minutes=staff.get('avg_review_time_minutes'),
            last_login=staff.get('last_login'),
            created_at=staff.get('created_at')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting staff member: {e}")
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
        
        # Validate role
        if not validate_staff_role(staff_data.role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: admin, data_extractor, data_approver, staff, viewer"
            )
        
        # Check if user exists in auth
        auth_user = await get_user_from_auth(supabase, staff_data.email)
        
        if not auth_user:
            # Create auth user
            user_id = await create_auth_user(
                supabase,
                staff_data.email,
                secrets.token_urlsafe(16),
                {
                    "full_name": f"{staff_data.first_name} {staff_data.last_name}",
                    "first_name": staff_data.first_name,
                    "last_name": staff_data.last_name
                }
            )
            
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
            
            # Check if already a staff member
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
        
        # Create staff profile
        staff_profile = {
            'id': staff_user_id,
            'email': staff_email,
            'first_name': staff_data.first_name,
            'last_name': staff_data.last_name,
            'role': staff_data.role,
            'role_id': role_id,
            'is_active': True,
            'permissions': default_permissions,
            'organization_id': staff_data.organization_id,
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
        
        # Send welcome email if new user
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
        
        # Return the created staff member
        return await get_staff_member(staff_user_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating staff member: {e}")
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
        
        # Check if staff exists
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
        
        # Prevent deactivating yourself
        if update_data.is_active is False and staff_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate yourself"
            )
        
        # Validate role if being updated
        if update_data.role and not validate_staff_role(update_data.role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: admin, data_extractor, data_approver, staff, viewer"
            )
        
        # If changing role, get new role_id and permissions
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
        
        # Build update dict
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
        if update_data.organization_id is not None:
            update_dict['organization_id'] = update_data.organization_id
        if update_data.permissions is not None:
            # Merge with existing permissions
            current_permissions = existing.data.get('permissions', {})
            if isinstance(current_permissions, dict):
                current_permissions.update(update_data.permissions)
                update_dict['permissions'] = current_permissions
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update staff profile
        result = supabase.from_('staff_profiles') \
            .update(update_dict) \
            .eq('id', staff_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update staff member"
            )
        
        # Return updated staff member
        return await get_staff_member(staff_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating staff member: {e}")
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
        
        # Check if staff exists
        existing = supabase.from_('staff_profiles') \
            .select('id, email') \
            .eq('id', staff_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Staff member not found"
            )
        
        # Prevent deleting yourself
        if staff_id == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot delete yourself"
            )
        
        # Prevent deleting the last admin
        if permanent:
            # Check if this is the last admin
            admin_count = supabase.from_('staff_profiles') \
                .select('id', count='exact') \
                .eq('role', 'admin') \
                .eq('is_active', True) \
                .execute()
            
            if admin_count.count == 1:
                # Check if this staff is an admin
                if existing.data.get('role') == 'admin':
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot delete the last admin user"
                    )
        
        if permanent:
            # Hard delete
            result = supabase.from_('staff_profiles') \
                .delete() \
                .eq('id', staff_id) \
                .execute()
            
            message = "Staff member permanently deleted"
        else:
            # Soft delete
            result = supabase.from_('staff_profiles') \
                .update({
                    'is_active': False,
                    'deleted_at': datetime.now().isoformat()
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
        
        # Check if staff exists
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
        
        # Prevent removing last admin
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
        
        # Get role_id and permissions
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
        
        # Update staff
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update staff role: {str(e)}"
        )