# backend/routes/admin/permissions.py
"""
Role and permission management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

from auth import AuthUser, require_role
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/permissions", tags=["Admin - Permissions"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class PermissionBase(BaseModel):
    """Base permission model."""
    name: str
    description: Optional[str] = None
    enabled: bool = True

class RoleCreate(BaseModel):
    """Request model for creating a role."""
    name: str
    description: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None

class RoleUpdate(BaseModel):
    """Request model for updating a role."""
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None

class RoleResponse(BaseModel):
    """Response model for a role."""
    id: str
    name: str
    description: Optional[str] = None
    permissions: Dict[str, bool]
    created_at: datetime
    updated_at: Optional[datetime] = None
    staff_count: Optional[int] = 0

class RoleListResponse(BaseModel):
    """Response model for role list."""
    success: bool
    data: List[RoleResponse]
    total: int

# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def get_role_by_id(supabase, role_id: str) -> Optional[Dict]:
    """Get a role by ID."""
    try:
        result = supabase.from_('roles') \
            .select('id, name, description, permissions, created_at, updated_at') \
            .eq('id', role_id) \
            .maybe_single() \
            .execute()
        return result.data if result.data else None
    except Exception:
        return None

async def get_staff_count_for_role(supabase, role_id: str) -> int:
    """Get the number of staff members using a role."""
    try:
        result = supabase.from_('staff_profiles') \
            .select('id', count='exact') \
            .eq('role_id', role_id) \
            .execute()
        return result.count or 0
    except Exception:
        return 0

# ==========================================
# ENDPOINTS
# ==========================================
@router.get("/roles", response_model=RoleListResponse)
async def get_roles(
    search: Optional[str] = Query(None, description="Search by role name"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get all roles with their permissions.
    Admin only endpoint with pagination and search.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Build base query
        query = supabase.from_('roles') \
            .select('id, name, description, permissions, created_at, updated_at')
        
        if search:
            query = query.ilike('name', f'%{search}%')
        
        # ✅ Get total count (with search filter applied)
        count_query = supabase.from_('roles') \
            .select('id', count='exact')
        
        if search:
            count_query = count_query.ilike('name', f'%{search}%')
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # ✅ Get paginated results
        result = query.order('name') \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Transform data with staff counts
        roles = []
        for role in (result.data or []):
            staff_count = await get_staff_count_for_role(supabase, role['id'])
            
            roles.append(RoleResponse(
                id=role['id'],
                name=role['name'],
                description=role.get('description'),
                permissions=role.get('permissions', {}),
                created_at=role['created_at'],
                updated_at=role.get('updated_at'),
                staff_count=staff_count
            ))
        
        return RoleListResponse(
            success=True,
            data=roles,
            total=total
        )
        
    except Exception as e:
        print(f"❌ Error getting roles: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get roles: {str(e)}"
        )
@router.get("/roles/{role_id}")
async def get_role(
    role_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get a specific role with permissions.
    """
    try:
        supabase = get_supabase_client()
        
        role = await get_role_by_id(supabase, role_id)
        
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        staff_count = await get_staff_count_for_role(supabase, role_id)
        
        return {
            "success": True,
            "data": {
                **role,
                "staff_count": staff_count
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get role: {str(e)}"
        )

@router.post("/roles")
async def create_role(
    role_data: RoleCreate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Create a new role with permissions.
    """
    try:
        supabase = get_supabase_client()
        
        # Validate role name
        if not role_data.name or len(role_data.name.strip()) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Role name is required"
            )
        
        # Check if role already exists
        existing = supabase.from_('roles') \
            .select('id') \
            .eq('name', role_data.name) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Role '{role_data.name}' already exists"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Create role
        result = supabase.from_('roles') \
            .insert({
                'name': role_data.name,
                'description': role_data.description,
                'permissions': role_data.permissions or {},
                'created_at': now,
                'updated_at': now
            }) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create role"
            )
        
        return {
            "success": True,
            "message": f"Role '{role_data.name}' created successfully",
            "data": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role: {str(e)}"
        )

@router.put("/roles/{role_id}")
async def update_role(
    role_id: str,
    role_data: RoleUpdate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Update a role.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if role exists
        existing = await get_role_by_id(supabase, role_id)
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Build update dict
        update_data = {}
        
        if role_data.name is not None:
            # Validate name
            if not role_data.name or len(role_data.name.strip()) == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role name cannot be empty"
                )
            
            # Check if new name conflicts
            if role_data.name != existing['name']:
                conflict = supabase.from_('roles') \
                    .select('id') \
                    .eq('name', role_data.name) \
                    .neq('id', role_id) \
                    .maybe_single() \
                    .execute()
                
                if conflict.data:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Role '{role_data.name}' already exists"
                    )
            
            update_data['name'] = role_data.name
        
        if role_data.description is not None:
            update_data['description'] = role_data.description
        
        if role_data.permissions is not None:
            update_data['permissions'] = role_data.permissions
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        # Update role
        result = supabase.from_('roles') \
            .update(update_data) \
            .eq('id', role_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update role"
            )
        
        return {
            "success": True,
            "message": "Role updated successfully",
            "data": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role: {str(e)}"
        )

@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Delete a role.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if role exists
        existing = await get_role_by_id(supabase, role_id)
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Check if any staff are using this role
        staff_count = await get_staff_count_for_role(supabase, role_id)
        
        if staff_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role '{existing['name']}' as it is used by {staff_count} staff member(s)"
            )
        
        # Delete role
        supabase.from_('roles') \
            .delete() \
            .eq('id', role_id) \
            .execute()
        
        return {
            "success": True,
            "message": f"Role '{existing['name']}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role: {str(e)}"
        )

# ==========================================
# PERMISSION HELPERS (Utility Functions)
# ==========================================

@router.get("/permissions/list")
async def list_available_permissions(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get list of all available permissions.
    Useful for UI when creating/editing roles.
    """
    try:
        # Define all available permissions
        permissions = [
            # Staff permissions
            {"name": "can_view_all", "category": "Staff", "description": "View all system data"},
            {"name": "can_manage_staff", "category": "Staff", "description": "Create, update, delete staff members"},
            {"name": "can_manage_roles", "category": "Staff", "description": "Create, update, delete roles"},
            
            # Organization permissions
            {"name": "can_view_organizations", "category": "Organizations", "description": "View organization details"},
            {"name": "can_manage_organizations", "category": "Organizations", "description": "Create, update, delete organizations"},
            
            # Data permissions
            {"name": "can_extract", "category": "Data", "description": "Extract data from documents"},
            {"name": "can_process", "category": "Data", "description": "Process documents"},
            {"name": "can_review", "category": "Data", "description": "Review extracted data"},
            {"name": "can_approve", "category": "Data", "description": "Approve reviewed data"},
            
            # Export permissions
            {"name": "can_export", "category": "Export", "description": "Export system data"},
            {"name": "can_delete", "category": "Export", "description": "Delete system data"},
        ]
        
        # Get existing roles for context
        supabase = get_supabase_client()
        result = supabase.from_('roles') \
            .select('id, name, permissions') \
            .execute()
        
        roles_data = {}
        for role in (result.data or []):
            roles_data[role['name']] = role.get('permissions', {})
        
        # Show which permissions each role has
        for perm in permissions:
            perm["roles"] = []
            for role_name, perms in roles_data.items():
                if perms.get(perm["name"], False):
                    perm["roles"].append(role_name)
        
        return {
            "success": True,
            "data": {
                "permissions": permissions,
                "total": len(permissions)
            }
        }
        
    except Exception as e:
        print(f"❌ Error listing permissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list permissions: {str(e)}"
        )

# ==========================================
# DEFAULT ROLES SETUP
# ==========================================

@router.post("/setup-defaults")
async def setup_default_roles(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Setup default roles if they don't exist.
    """
    try:
        supabase = get_supabase_client()
        
        default_roles = [
            {
                "name": "admin",
                "description": "Full system access with all permissions",
                "permissions": {
                    "can_view_all": True,
                    "can_manage_staff": True,
                    "can_manage_roles": True,
                    "can_view_organizations": True,
                    "can_manage_organizations": True,
                    "can_extract": True,
                    "can_process": True,
                    "can_review": True,
                    "can_approve": True,
                    "can_export": True,
                    "can_delete": True,
                }
            },
            {
                "name": "data_approver",
                "description": "Can approve reviewed data",
                "permissions": {
                    "can_view_all": True,
                    "can_manage_staff": False,
                    "can_manage_roles": False,
                    "can_view_organizations": True,
                    "can_manage_organizations": False,
                    "can_extract": False,
                    "can_process": False,
                    "can_review": True,
                    "can_approve": True,
                    "can_export": True,
                    "can_delete": False,
                }
            },
            {
                "name": "data_extractor",
                "description": "Can extract and process data",
                "permissions": {
                    "can_view_all": False,
                    "can_manage_staff": False,
                    "can_manage_roles": False,
                    "can_view_organizations": True,
                    "can_manage_organizations": False,
                    "can_extract": True,
                    "can_process": True,
                    "can_review": False,
                    "can_approve": False,
                    "can_export": False,
                    "can_delete": False,
                }
            },
            {
                "name": "viewer",
                "description": "Read-only access",
                "permissions": {
                    "can_view_all": False,
                    "can_manage_staff": False,
                    "can_manage_roles": False,
                    "can_view_organizations": True,
                    "can_manage_organizations": False,
                    "can_extract": False,
                    "can_process": False,
                    "can_review": False,
                    "can_approve": False,
                    "can_export": False,
                    "can_delete": False,
                }
            }
        ]
        
        created_count = 0
        existing_count = 0
        
        for role_data in default_roles:
            # Check if role exists
            existing = supabase.from_('roles') \
                .select('id') \
                .eq('name', role_data['name']) \
                .maybe_single() \
                .execute()
            
            if existing.data:
                existing_count += 1
                continue
            
            # Create role
            now = datetime.utcnow().isoformat()
            supabase.from_('roles') \
                .insert({
                    'name': role_data['name'],
                    'description': role_data['description'],
                    'permissions': role_data['permissions'],
                    'created_at': now,
                    'updated_at': now
                }) \
                .execute()
            created_count += 1
        
        return {
            "success": True,
            "message": f"Default roles setup: {created_count} created, {existing_count} existing",
            "data": {
                "created": created_count,
                "existing": existing_count
            }
        }
        
    except Exception as e:
        print(f"❌ Error setting up default roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to setup default roles: {str(e)}"
        )