# backend/routes/organizations/team.py - Fixed Version (No Direct Join)

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from auth import AuthUser, require_org_member
from database import get_supabase_client
import os

router = APIRouter(prefix="/api/organizations/team", tags=["Team Management"])

class MemberUpdate(BaseModel):
    role: str

@router.get("/{org_id}/members")
async def get_team_members(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get team members with email from auth.users (separate queries)."""
    try:
        supabase = get_supabase_client()
        
        # ✅ Step 1: Get organization members
        members_result = supabase.from_('organization_members') \
            .select('id, role, user_id, created_at, is_active') \
            .eq('organization_id', org_id) \
            .order('created_at', desc=True) \
            .execute()
        
        print(f"📊 Found {len(members_result.data or [])} members in organization_members")
        
        if not members_result.data:
            return {"success": True, "members": [], "total": 0}
        
        # ✅ Step 2: Get user details from auth.users for each member
        members = []
        for member in members_result.data:
            user_id = member['user_id']
            
            try:
                # Query auth.users for this specific user
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', user_id) \
                    .maybe_single() \
                    .execute()
                
                if user_result and user_result.data:
                    user_data = user_result.data
                    email = user_data.get('email', 'Unknown')
                    raw_meta = user_data.get('raw_user_meta_data', {})
                    full_name = raw_meta.get('full_name') or raw_meta.get('name') or 'Team Member'
                    avatar_url = raw_meta.get('avatar_url', None)
                else:
                    # User not found in auth.users
                    email = f"User {user_id[:8]}"
                    full_name = 'Team Member'
                    avatar_url = None
                    
            except Exception as user_error:
                print(f"⚠️ Error fetching user {user_id}: {user_error}")
                email = f"User {user_id[:8]}"
                full_name = 'Team Member'
                avatar_url = None
            
            members.append({
                'id': member['id'],
                'user_id': user_id,
                'role': member['role'],
                'created_at': member['created_at'],
                'is_active': member.get('is_active', True),
                'email': email,
                'full_name': full_name,
                'avatar_url': avatar_url
            })
        
        print(f"✅ Returning {len(members)} members with details")
        for m in members:
            print(f"  - {m['email']} ({m['role']})")
        
        return {
            "success": True,
            "members": members,
            "total": len(members)
        }
        
    except Exception as e:
        print(f"❌ Error getting team members: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get team members: {str(e)}"
        )

@router.post("/{org_id}/invite")
async def invite_team_member(
    org_id: str,
    invite_data: Dict[str, Any],
    current_user: AuthUser = Depends(require_org_member())
):
    """Invite a team member by email."""
    try:
        supabase = get_supabase_client()
        email = invite_data.get('email')
        role = invite_data.get('role', 'viewer')
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email is required"
            )
        
        # Check if user exists in auth.users
        user_result = supabase.from_('auth.users') \
            .select('id, email') \
            .eq('email', email) \
            .maybe_single() \
            .execute()
        
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{email}' not found. Please ask them to sign up first."
            )
        
        user_id = user_result.data['id']
        
        # Check if already a member
        existing = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', user_id) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this organization"
            )
        
        # Add to organization_members
        result = supabase.from_('organization_members') \
            .insert({
                'organization_id': org_id,
                'user_id': user_id,
                'role': role,
                'is_active': True
            }) \
            .execute()
        
        return {
            "success": True,
            "message": f"User '{email}' invited as {role}",
            "member": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inviting team member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite team member: {str(e)}"
        )

@router.patch("/{org_id}/members/{member_id}")
async def update_member_role(
    org_id: str,
    member_id: str,
    update_data: MemberUpdate,
    current_user: AuthUser = Depends(require_org_member())
):
    """Update a member's role."""
    try:
        supabase = get_supabase_client()
        
        # Check if member exists and belongs to org
        existing = supabase.from_('organization_members') \
            .select('id, user_id, role') \
            .eq('id', member_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Prevent removing last admin
        if existing.data['role'] == 'admin' and update_data.role != 'admin':
            admin_count = supabase.from_('organization_members') \
                .select('id', count='exact') \
                .eq('organization_id', org_id) \
                .eq('role', 'admin') \
                .execute()
            
            if admin_count.count == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin role"
                )
        
        # Update role
        result = supabase.from_('organization_members') \
            .update({'role': update_data.role}) \
            .eq('id', member_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Role updated successfully",
            "member": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating member role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member role: {str(e)}"
        )

@router.delete("/{org_id}/members/{member_id}")
async def remove_member(
    org_id: str,
    member_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Remove a member from the organization."""
    try:
        supabase = get_supabase_client()
        
        # Check if member exists and belongs to org
        existing = supabase.from_('organization_members') \
            .select('id, user_id, role') \
            .eq('id', member_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Prevent removing last admin
        if existing.data['role'] == 'admin':
            admin_count = supabase.from_('organization_members') \
                .select('id', count='exact') \
                .eq('organization_id', org_id) \
                .eq('role', 'admin') \
                .execute()
            
            if admin_count.count == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin"
                )
        
        # Delete member
        result = supabase.from_('organization_members') \
            .delete() \
            .eq('id', member_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Member removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error removing member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )