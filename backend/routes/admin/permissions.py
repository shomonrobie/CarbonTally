# backend/routes/admin/permissions.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from pydantic import BaseModel
from auth import AuthUser, require_role, get_role_permissions_from_db  # ✅ Fixed import
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/permissions", tags=["Admin - Permissions"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class RoleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    permissions: Optional[Dict[str, bool]] = None

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/roles")
async def list_roles(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """List all roles with their permissions."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('roles') \
            .select('id, name, description, permissions, created_at, updated_at') \
            .order('name') \
            .execute()
        
        return {
            "success": True,
            "roles": result.data or [],
            "total": len(result.data or [])
        }
        
    except Exception as e:
        print(f"❌ Error listing roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list roles: {str(e)}"
        )

@router.get("/roles/{role_id}")
async def get_role(
    role_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Get a specific role with permissions."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('roles') \
            .select('id, name, description, permissions, created_at, updated_at') \
            .eq('id', role_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        return {
            "success": True,
            "role": result.data
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
    """Create a new role with permissions."""
    try:
        supabase = get_supabase_client()
        
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
        
        # Create role
        now = datetime.now().isoformat()
        result = supabase.from_('roles') \
            .insert({
                'name': role_data.name,
                'description': role_data.description,
                'permissions': role_data.permissions or {},
                'created_at': now,
                'updated_at': now
            }) \
            .execute()
        
        return {
            "success": True,
            "message": f"Role '{role_data.name}' created successfully",
            "role": result.data[0] if result.data else None
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
    """Update role permissions."""
    try:
        supabase = get_supabase_client()
        
        # Check if role exists
        existing = supabase.from_('roles') \
            .select('id, name') \
            .eq('id', role_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Build update dict
        update_data = {}
        if role_data.name is not None:
            # Check if new name conflicts
            if role_data.name != existing.data['name']:
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
        
        update_data['updated_at'] = datetime.now().isoformat()
        
        # Update role
        result = supabase.from_('roles') \
            .update(update_data) \
            .eq('id', role_id) \
            .execute()
        
        return {
            "success": True,
            "message": f"Role updated successfully",
            "role": result.data[0] if result.data else None
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
    """Delete a role."""
    try:
        supabase = get_supabase_client()
        
        # Check if role exists
        existing = supabase.from_('roles') \
            .select('id, name') \
            .eq('id', role_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Check if any staff are using this role
        staff_using = supabase.from_('staff_profiles') \
            .select('id', count='exact') \
            .eq('role_id', role_id) \
            .execute()
        
        if staff_using.count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role '{existing.data['name']}' as it is used by {staff_using.count} staff members"
            )
        
        # Delete role
        supabase.from_('roles') \
            .delete() \
            .eq('id', role_id) \
            .execute()
        
        return {
            "success": True,
            "message": f"Role '{existing.data['name']}' deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role: {str(e)}"
        )