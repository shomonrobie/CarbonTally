# backend/routes/organizations/members.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
import secrets
from auth import AuthUser, require_org_member, require_permission, require_org_admin, require_auth

from database import get_supabase_client
from utils.email import send_invitation_email

router = APIRouter(prefix="/api/organizations/members", tags=["Organization Members"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class OrganizationMemberCreate(BaseModel):
    """Request model for inviting a member."""
    email: EmailStr = Field(..., description="Email address of the user to invite")
    role: str = Field("viewer", description="Role: admin, editor, or viewer")
    message: Optional[str] = Field(None, description="Personal message to include in invitation")
    
    class Config:
        json_schema_extra = {
            "example": {
                "email": "john@example.com",
                "role": "editor",
                "message": "We'd love to have you join our sustainability team!"
            }
        }

class OrganizationMemberUpdate(BaseModel):
    """Request model for updating a member."""
    role: Optional[str] = Field(None, description="Role: admin, editor, or viewer")
    is_active: Optional[bool] = Field(None, description="Activate or deactivate member")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "admin",
                "is_active": True
            }
        }

class OrganizationMemberResponse(BaseModel):
    """Response model for a member."""
    id: str
    user_id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool
    joined_at: datetime
    last_active: Optional[datetime] = None
    permissions: Dict[str, bool] = {}

class OrganizationMemberListResponse(BaseModel):
    """Response model for member list."""
    organization_id: str
    organization_name: Optional[str] = None
    members: List[OrganizationMemberResponse]
    total: int
    current_user_role: str

# ==========================================
# HELPER FUNCTIONS
# ==========================================

@router.get("/user/{user_id}")
async def get_organization_by_user(
    user_id: str,
    current_user: AuthUser = Depends(require_auth)
):
    """
    Get organization details for a specific user.
    
    Returns:
        - Single organization object with role (current implementation)
        - In future: Can return multiple organizations for consultants
    
    The response format is designed to be extensible:
    - 'mode': 'single' or 'multi' (future)
    - 'organizations': Array of org objects with roles
    """
    try:
        supabase = get_supabase_client()
        
        # Get the user's organization membership
        member_result = supabase.from_('organization_members') \
            .select('organization_id, role') \
            .eq('user_id', user_id) \
            .maybe_single() \
            .execute()
        
        if not member_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User is not a member of any organization"
            )
        
        org_id = member_result.data['organization_id']
        role = member_result.data['role']
        
        # Get organization details
        org_result = supabase.from_('organizations') \
            .select('*') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        if not org_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # ✅ Return format that can be extended for multi-org support
        return {
            "mode": "single",  # Future: "multi" for consultants
            "primary_organization": org_result.data,
            "primary_role": role,
            "organizations": [
                {
                    "organization": org_result.data,
                    "role": role,
                    "is_primary": True
                }
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error fetching organization by user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch organization: {str(e)}"
        )
    
def validate_role(role: str) -> bool:
    """Validate that the role is allowed."""
    allowed_roles = ['admin', 'editor', 'viewer']
    return role in allowed_roles

def get_member_details(supabase_client, user_id: str, org_id: str) -> Optional[Dict]:
    """Get full member details with user info."""
    try:
        result = supabase_client.from_('organization_members') \
            .select('''
                id,
                role,
                is_active,
                joined_at,
                last_active,
                users!inner (
                    id,
                    email,
                    raw_user_meta_data->>'full_name' as full_name,
                    raw_user_meta_data->>'avatar_url' as avatar_url
                )
            ''') \
            .eq('organization_id', org_id) \
            .eq('user_id', user_id) \
            .maybe_single() \
            .execute()
        
        if result and result.data:
            user_data = result.data.get('users', {})
            return {
                'id': result.data['id'],
                'user_id': user_data.get('id'),
                'email': user_data.get('email'),
                'full_name': user_data.get('full_name'),
                'avatar_url': user_data.get('avatar_url'),
                'role': result.data['role'],
                'is_active': result.data.get('is_active', True),
                'joined_at': result.data.get('joined_at'),
                'last_active': result.data.get('last_active')
            }
        return None
        
    except Exception as e:
        print(f"⚠️ Error getting member details: {e}")
        return None

async def check_user_exists(supabase_client, email: str) -> tuple:
    """Check if a user exists in auth.users. Returns (exists, user_id)."""
    try:
        # Use the admin API to check user
        from supabase import Client
        result = supabase_client.from_('auth.users') \
            .select('id, email') \
            .eq('email', email) \
            .maybe_single() \
            .execute()
        
        if result and result.data:
            return True, result.data.get('id')
        return False, None
        
    except Exception as e:
        print(f"⚠️ Error checking user existence: {e}")
        return False, None

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/", response_model=OrganizationMemberListResponse)
async def get_organization_members(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get all members of the user's organization.
    """
    try:
        supabase = get_supabase_client()
        
        # Get organization details
        org_result = supabase.from_('organizations') \
            .select('id, name') \
            .eq('id', current_user.organization_id) \
            .maybe_single() \
            .execute()
        
        if not org_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Build query
        query = supabase.from_('organization_members') \
            .select('''
                id,
                role,
                is_active,
                joined_at,
                last_active,
                users!inner (
                    id,
                    email,
                    raw_user_meta_data->>'full_name' as full_name,
                    raw_user_meta_data->>'avatar_url' as avatar_url
                )
            ''') \
            .eq('organization_id', current_user.organization_id)
        
        # Apply filters
        if search:
            query = query.or_(f"users.email.ilike.%{search}%,users.raw_user_meta_data->>'full_name'.ilike.%{search}%")
        if role and validate_role(role):
            query = query.eq('role', role)
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        # Execute query
        result = query.order('joined_at', desc=True).execute()
        
        # Transform data
        members = []
        for member in result.data:
            user_data = member.get('users', {})
            members.append(OrganizationMemberResponse(
                id=member['id'],
                user_id=user_data.get('id'),
                email=user_data.get('email'),
                full_name=user_data.get('full_name'),
                avatar_url=user_data.get('avatar_url'),
                role=member['role'],
                is_active=member.get('is_active', True),
                joined_at=member.get('joined_at'),
                last_active=member.get('last_active'),
                permissions={}  # Permissions determined by role
            ))
        
        return OrganizationMemberListResponse(
            organization_id=current_user.organization_id,
            organization_name=org_result.data.get('name'),
            members=members,
            total=len(members),
            current_user_role=current_user.role
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting members: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get members: {str(e)}"
        )

@router.post("/invite")
async def invite_organization_member(
    invite_data: OrganizationMemberCreate,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Invite a new member to the organization.
    """
    try:
        supabase = get_supabase_client()
        
        # Check permission
        if not current_user.permissions.get('can_manage_org_members', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to invite members"
            )
        
        # Validate role
        if not validate_role(invite_data.role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: admin, editor, viewer"
            )
        
        # Check if user exists in auth
        user_exists, user_id = await check_user_exists(supabase, invite_data.email)
        
        if user_exists and user_id:
            # Check if already a member
            existing = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', current_user.organization_id) \
                .eq('user_id', user_id) \
                .maybe_single() \
                .execute()
            
            if existing.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="User is already a member of this organization"
                )
        
        # Generate invitation token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Create invitation
        invitation_data = {
            'email': invite_data.email,
            'organization_id': current_user.organization_id,
            'invited_by': current_user.user_id,
            'token': token,
            'status': 'pending',
            'expires_at': expires_at.isoformat(),
            'metadata': {
                'role': invite_data.role,
                'invited_by_email': current_user.email,
                'invited_by_name': f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.email,
                'message': invite_data.message
            }
        }
        
        # Check if invitation already exists
        existing_invite = supabase.from_('user_invitations') \
            .select('id, status') \
            .eq('email', invite_data.email) \
            .eq('organization_id', current_user.organization_id) \
            .eq('status', 'pending') \
            .maybe_single() \
            .execute()
        
        if existing_invite.data:
            # Update existing invitation
            result = supabase.from_('user_invitations') \
                .update(invitation_data) \
                .eq('id', existing_invite.data['id']) \
                .execute()
        else:
            # Create new invitation
            result = supabase.from_('user_invitations') \
                .insert(invitation_data) \
                .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create invitation"
            )
        
        # Get organization name
        org_result = supabase.from_('organizations') \
            .select('name') \
            .eq('id', current_user.organization_id) \
            .maybe_single() \
            .execute()
        
        org_name = org_result.data.get('name', 'CarbonTally') if org_result.data else 'CarbonTally'
        
        # Send invitation email (async)
        try:
            await send_invitation_email(
                email=invite_data.email,
                token=token,
                organization_name=org_name,
                invited_by=invitation_data['metadata']['invited_by_name'],
                role=invite_data.role,
                message=invite_data.message
            )
        except Exception as email_error:
            print(f"⚠️ Failed to send invitation email: {email_error}")
            # Continue - invitation created, email can be resent later
        
        return {
            "success": True,
            "message": f"Invitation sent to {invite_data.email}",
            "invitation_id": result.data[0]['id'],
            "expires_at": expires_at.isoformat(),
            "user_exists": user_exists
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error inviting member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to invite member: {str(e)}"
        )

@router.put("/{member_id}")
async def update_organization_member(
    member_id: str,
    update_data: OrganizationMemberUpdate,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Update a member's role or status.
    """
    try:
        supabase = get_supabase_client()
        
        # Check permission
        if not current_user.permissions.get('can_manage_org_members', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update members"
            )
        
        # Get the member
        member_result = supabase.from_('organization_members') \
            .select('user_id, organization_id, role') \
            .eq('id', member_id) \
            .maybe_single() \
            .execute()
        
        if not member_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Check if member belongs to same organization
        if member_result.data['organization_id'] != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update members in your organization"
            )
        
        # Validate role if being updated
        if update_data.role and not validate_role(update_data.role):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid role. Allowed: admin, editor, viewer"
            )
        
        # Prevent self-modification that removes admin role
        if member_result.data['user_id'] == current_user.user_id:
            if update_data.role and update_data.role != 'admin':
                # Check if this is the only admin
                admin_count = supabase.from_('organization_members') \
                    .select('id', count='exact') \
                    .eq('organization_id', current_user.organization_id) \
                    .eq('role', 'admin') \
                    .execute()
                
                if admin_count.count == 1:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot remove the last admin role from yourself"
                    )
        
        # Prevent deactivating yourself
        if update_data.is_active is False and member_result.data['user_id'] == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot deactivate yourself"
            )
        
        # Build update dict
        update_dict = {}
        if update_data.role is not None:
            update_dict['role'] = update_data.role
        if update_data.is_active is not None:
            update_dict['is_active'] = update_data.is_active
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update member
        result = supabase.from_('organization_members') \
            .update(update_dict) \
            .eq('id', member_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Member updated successfully",
            "member": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update member: {str(e)}"
        )

@router.delete("/{member_id}")
async def remove_organization_member(
    member_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Remove a member from the organization.
    """
    try:
        supabase = get_supabase_client()
        
        # Check permission
        if not current_user.permissions.get('can_manage_org_members', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to remove members"
            )
        
        # Get the member
        member_result = supabase.from_('organization_members') \
            .select('user_id, organization_id, role') \
            .eq('id', member_id) \
            .maybe_single() \
            .execute()
        
        if not member_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found"
            )
        
        # Check if member belongs to same organization
        if member_result.data['organization_id'] != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only remove members from your organization"
            )
        
        # Prevent removing yourself
        if member_result.data['user_id'] == current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="You cannot remove yourself from the organization"
            )
        
        # Check if removing last admin
        if member_result.data['role'] == 'admin':
            admin_count = supabase.from_('organization_members') \
                .select('id', count='exact') \
                .eq('organization_id', current_user.organization_id) \
                .eq('role', 'admin') \
                .execute()
            
            if admin_count.count == 1:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot remove the last admin from the organization"
                )
        
        # Delete member
        result = supabase.from_('organization_members') \
            .delete() \
            .eq('id', member_id) \
            .execute()
        
        # Get member email for audit log
        user_result = supabase.from_('auth.users') \
            .select('email') \
            .eq('id', member_result.data['user_id']) \
            .maybe_single() \
            .execute()
        
        user_email = user_result.data.get('email') if user_result.data else 'Unknown'
        
        return {
            "success": True,
            "message": f"Member {user_email} removed successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error removing member: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove member: {str(e)}"
        )

@router.post("/{member_id}/resend-invite")
async def resend_invitation(
    member_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Resend invitation to a pending member.
    """
    try:
        supabase = get_supabase_client()
        
        # Check permission
        if not current_user.permissions.get('can_manage_org_members', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to resend invitations"
            )
        
        # Get invitation
        invite_result = supabase.from_('user_invitations') \
            .select('''
                id,
                email,
                token,
                status,
                organization_id,
                metadata,
                organizations (name)
            ''') \
            .eq('organization_id', current_user.organization_id) \
            .eq('id', member_id) \
            .eq('status', 'pending') \
            .maybe_single() \
            .execute()
        
        if not invite_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pending invitation not found"
            )
        
        # Regenerate token
        new_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # Update token
        supabase.from_('user_invitations') \
            .update({
                'token': new_token,
                'expires_at': expires_at.isoformat()
            }) \
            .eq('id', invite_result.data['id']) \
            .execute()
        
        # Get organization name
        org_name = invite_result.data.get('organizations', {}).get('name', 'CarbonTally')
        
        # Get inviter name
        inviter_name = f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.email
        
        # Resend email
        try:
            await send_invitation_email(
                email=invite_result.data['email'],
                token=new_token,
                organization_name=org_name,
                invited_by=inviter_name,
                role=invite_result.data.get('metadata', {}).get('role', 'viewer'),
                message=invite_result.data.get('metadata', {}).get('message')
            )
        except Exception as email_error:
            print(f"⚠️ Failed to resend invitation email: {email_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to send email, but invitation was updated"
            )
        
        return {
            "success": True,
            "message": f"Invitation resent to {invite_result.data['email']}",
            "expires_at": expires_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error resending invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resend invitation: {str(e)}"
        )

# Add to backend/routes/organizations/members.py

# ==========================================
# Bulk Member Operations
# ==========================================

class BulkMemberUpdate(BaseModel):
    member_ids: List[str]
    updates: Dict[str, Any]  # role, is_active, etc.

@router.post("/{org_id}/members/bulk/update")
async def bulk_update_members(
    org_id: str,
    bulk_update: BulkMemberUpdate,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Bulk update organization members."""
    try:
        supabase = get_supabase_client()
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': [],
            'data': []
        }
        
        for member_id in bulk_update.member_ids:
            try:
                # Check if member exists
                existing = supabase.from_('organization_members') \
                    .select('id, role') \
                    .eq('id', member_id) \
                    .eq('organization_id', org_id) \
                    .maybe_single() \
                    .execute()
                
                if not existing.data:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'member_id': member_id,
                        'error': 'Member not found'
                    })
                    continue
                
                # Prevent removing last admin
                if bulk_update.updates.get('role') and existing.data['role'] == 'admin':
                    admin_count = supabase.from_('organization_members') \
                        .select('id', count='exact') \
                        .eq('organization_id', org_id) \
                        .eq('role', 'admin') \
                        .execute()
                    
                    if admin_count.count == 1:
                        results['failed_count'] += 1
                        results['errors'].append({
                            'member_id': member_id,
                            'error': 'Cannot remove the last admin'
                        })
                        continue
                
                # Update member
                update_data = bulk_update.updates.copy()
                update_data['updated_at'] = datetime.utcnow().isoformat()
                
                result = supabase.from_('organization_members') \
                    .update(update_data) \
                    .eq('id', member_id) \
                    .execute()
                
                if result.data:
                    results['success_count'] += 1
                    results['data'].append(result.data[0])
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'member_id': member_id,
                        'error': 'Failed to update member'
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'member_id': member_id,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Bulk update completed: {results['success_count']} successful, {results['failed_count']} failed",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update members: {str(e)}"
        )

@router.post("/{org_id}/members/bulk/remove")
async def bulk_remove_members(
    org_id: str,
    member_ids: List[str],
    current_user: AuthUser = Depends(require_org_admin())
):
    """Bulk remove members from organization."""
    try:
        supabase = get_supabase_client()
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': [],
            'data': []
        }
        
        for member_id in member_ids:
            try:
                # Check if member exists
                existing = supabase.from_('organization_members') \
                    .select('id, role') \
                    .eq('id', member_id) \
                    .eq('organization_id', org_id) \
                    .maybe_single() \
                    .execute()
                
                if not existing.data:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'member_id': member_id,
                        'error': 'Member not found'
                    })
                    continue
                
                # Prevent removing last admin
                if existing.data['role'] == 'admin':
                    admin_count = supabase.from_('organization_members') \
                        .select('id', count='exact') \
                        .eq('organization_id', org_id) \
                        .eq('role', 'admin') \
                        .execute()
                    
                    if admin_count.count == 1:
                        results['failed_count'] += 1
                        results['errors'].append({
                            'member_id': member_id,
                            'error': 'Cannot remove the last admin'
                        })
                        continue
                
                # Remove member
                result = supabase.from_('organization_members') \
                    .delete() \
                    .eq('id', member_id) \
                    .execute()
                
                if result.data:
                    results['success_count'] += 1
                    results['data'].append({
                        'member_id': member_id,
                        'removed': True
                    })
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'member_id': member_id,
                        'error': 'Failed to remove member'
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'member_id': member_id,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Bulk removal completed: {results['success_count']} successful, {results['failed_count']} failed",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk remove members: {str(e)}"
        )

@router.get("/{org_id}/members/stats")
async def get_member_stats(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get member statistics for an organization."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('organization_members') \
            .select('role, is_active', count='exact') \
            .eq('organization_id', org_id) \
            .execute()
        
        if not result.data:
            return {
                "success": True,
                "data": {
                    "total_members": 0,
                    "by_role": {},
                    "active_members": 0,
                    "inactive_members": 0
                }
            }
        
        stats = {
            'total_members': len(result.data),
            'by_role': {},
            'active_members': 0,
            'inactive_members': 0
        }
        
        for member in result.data:
            role = member.get('role', 'unknown')
            stats['by_role'][role] = stats['by_role'].get(role, 0) + 1
            
            if member.get('is_active', True):
                stats['active_members'] += 1
            else:
                stats['inactive_members'] += 1
        
        return {"success": True, "data": stats}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get member stats: {str(e)}"
        )

@router.get("/{org_id}/members/roles")
async def get_member_roles(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get available roles for organization members."""
    try:
        # Define standard roles
        roles = [
            {'name': 'admin', 'description': 'Full access to organization settings and members'},
            {'name': 'manager', 'description': 'Manage assets, data, and team members'},
            {'name': 'viewer', 'description': 'View-only access to organization data'},
            {'name': 'contributor', 'description': 'Can add and edit data but not manage members'}
        ]
        
        return {"success": True, "data": roles}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get member roles: {str(e)}"
        )
