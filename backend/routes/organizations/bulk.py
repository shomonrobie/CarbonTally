# backend/routes/organizations/bulk.py
"""
Bulk operations for organizations, members, and assets.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from auth import AuthUser, require_org_admin, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/organizations", tags=["Organizations - Bulk Operations"])

# ==========================================
# Pydantic Models
# ==========================================

class BulkMemberInvite(BaseModel):
    email: str
    role: str = "viewer"

class BulkMemberInviteRequest(BaseModel):
    invites: List[BulkMemberInvite]
    send_notifications: bool = True

class BulkAssetCreate(BaseModel):
    name: str
    facility_id: str
    description: Optional[str] = None
    type: Optional[str] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class BulkAssetCreateRequest(BaseModel):
    assets: List[BulkAssetCreate]

class BulkOperationResult(BaseModel):
    success_count: int
    failed_count: int
    errors: List[Dict[str, Any]]
    data: List[Dict[str, Any]]

# ==========================================
# Bulk Member Invite Endpoints
# ==========================================

@router.post("/{org_id}/members/bulk/invite")
async def bulk_invite_members(
    org_id: str,
    request: BulkMemberInviteRequest,
    current_user: AuthUser = Depends(require_org_admin())
):
    """
    Bulk invite members to an organization.
    """
    try:
        supabase = get_supabase_client()
        
        # Verify organization exists
        org_check = supabase.from_('organizations') \
            .select('id, name') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        if not org_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': [],
            'data': []
        }
        
        for invite in request.invites:
            try:
                # Check if user exists in auth.users
                user_result = supabase.from_('auth.users') \
                    .select('id, email') \
                    .eq('email', invite.email) \
                    .maybe_single() \
                    .execute()
                
                if not user_result.data:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'email': invite.email,
                        'error': 'User not found. Please ask them to sign up first.'
                    })
                    continue
                
                user_id = user_result.data['id']
                
                # Check if already a member
                existing = supabase.from_('organization_members') \
                    .select('id') \
                    .eq('organization_id', org_id) \
                    .eq('user_id', user_id) \
                    .maybe_single() \
                    .execute()
                
                if existing.data:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'email': invite.email,
                        'error': 'User is already a member of this organization'
                    })
                    continue
                
                # Add to organization_members
                member_data = {
                    'organization_id': org_id,
                    'user_id': user_id,
                    'role': invite.role,
                    'is_active': True,
                    'created_at': datetime.utcnow().isoformat()
                }
                
                result = supabase.from_('organization_members') \
                    .insert(member_data) \
                    .execute()
                
                if result.data:
                    results['success_count'] += 1
                    results['data'].append({
                        'email': invite.email,
                        'role': invite.role,
                        'user_id': user_id,
                        'member_id': result.data[0]['id']
                    })
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'email': invite.email,
                        'error': 'Failed to add member'
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'email': invite.email,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Bulk invite completed: {results['success_count']} successful, {results['failed_count']} failed",
            "data": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk invite members: {str(e)}"
        )

@router.post("/{org_id}/assets/bulk/create")
async def bulk_create_assets(
    org_id: str,
    request: BulkAssetCreateRequest,
    current_user: AuthUser = Depends(require_org_admin())
):
    """
    Bulk create assets for an organization.
    """
    try:
        supabase = get_supabase_client()
        
        # Verify organization exists
        org_check = supabase.from_('organizations') \
            .select('id') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        if not org_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': [],
            'data': []
        }
        
        for asset in request.assets:
            try:
                # Verify facility exists and belongs to organization
                facility_check = supabase.from_('facilities') \
                    .select('id') \
                    .eq('id', asset.facility_id) \
                    .eq('organization_id', org_id) \
                    .maybe_single() \
                    .execute()
                
                if not facility_check.data:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'name': asset.name,
                        'facility_id': asset.facility_id,
                        'error': 'Facility not found or does not belong to this organization'
                    })
                    continue
                
                # Create asset
                asset_data = {
                    'name': asset.name,
                    'facility_id': asset.facility_id,
                    'description': asset.description,
                    'type': asset.type,
                    'capacity': asset.capacity,
                    'capacity_unit': asset.capacity_unit,
                    'serial_number': asset.serial_number,
                    'installation_date': asset.installation_date,
                    'metadata': asset.metadata,
                    'is_active': True,
                    'created_at': datetime.utcnow().isoformat()
                }
                
                result = supabase.from_('assets') \
                    .insert(asset_data) \
                    .execute()
                
                if result.data:
                    results['success_count'] += 1
                    results['data'].append({
                        'name': asset.name,
                        'asset_id': result.data[0]['id'],
                        'facility_id': asset.facility_id
                    })
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'name': asset.name,
                        'error': 'Failed to create asset'
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'name': asset.name,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Bulk asset creation completed: {results['success_count']} successful, {results['failed_count']} failed",
            "data": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create assets: {str(e)}"
        )