# backend/routes/drafts.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from auth import AuthUser, require_org_member
from database import get_supabase_client

router = APIRouter(prefix="/api/drafts", tags=["Drafts"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class DraftSaveRequest(BaseModel):
    file_id: str
    data: Dict[str, Any]
    progress: int
    sections_completed: Optional[list] = []

class DraftResponse(BaseModel):
    id: str
    file_id: str
    organization_id: str
    user_id: str
    data: Dict[str, Any]
    progress: int
    sections_completed: list
    last_updated: datetime
    created_at: datetime

class DraftListResponse(BaseModel):
    success: bool
    drafts: list
    total: int

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/save")
async def save_draft(
    draft_data: DraftSaveRequest,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Save or update a draft for manual entry.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Check if draft already exists
        existing = supabase.from_('draft_entries') \
            .select('id') \
            .eq('file_id', draft_data.file_id) \
            .eq('user_id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        now = datetime.now().isoformat()
        
        if existing.data:
            # Update existing draft
            result = supabase.from_('draft_entries') \
                .update({
                    'data': draft_data.data,
                    'progress': draft_data.progress,
                    'sections_completed': draft_data.sections_completed,
                    'last_updated': now
                }) \
                .eq('id', existing.data['id']) \
                .execute()
            
            return {
                "success": True,
                "message": "Draft updated successfully",
                "draft_id": existing.data['id'],
                "progress": draft_data.progress
            }
        else:
            # Create new draft
            result = supabase.from_('draft_entries') \
                .insert({
                    'file_id': draft_data.file_id,
                    'organization_id': org_id,
                    'user_id': current_user.user_id,
                    'data': draft_data.data,
                    'progress': draft_data.progress,
                    'sections_completed': draft_data.sections_completed,
                    'created_at': now,
                    'last_updated': now
                }) \
                .execute()
            
            if not result.data:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to save draft"
                )
            
            return {
                "success": True,
                "message": "Draft saved successfully",
                "draft_id": result.data[0]['id'],
                "progress": draft_data.progress
            }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error saving draft: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save draft: {str(e)}"
        )

@router.get("/")
async def get_drafts(
    file_id: Optional[str] = Query(None, description="Filter by file_id"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get all drafts for the current user.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        query = supabase.from_('draft_entries') \
            .select('''
                id,
                file_id,
                organization_id,
                user_id,
                data,
                progress,
                sections_completed,
                last_updated,
                created_at,
                organization_files!inner (
                    id,
                    name,
                    file_type,
                    status
                )
            ''') \
            .eq('user_id', current_user.user_id) \
            .eq('organization_id', org_id) \
            .order('last_updated', desc=True)
        
        if file_id:
            query = query.eq('file_id', file_id)
        
        count_query = supabase.from_('draft_entries') \
            .select('id', count='exact') \
            .eq('user_id', current_user.user_id) \
            .eq('organization_id', org_id)
        
        if file_id:
            count_query = count_query.eq('file_id', file_id)
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        result = query.range(offset, offset + limit - 1).execute()
        
        drafts = []
        for draft in result.data:
            file_data = draft.get('organization_files', {})
            drafts.append({
                'id': draft['id'],
                'file_id': draft['file_id'],
                'file_name': file_data.get('name', 'Unknown'),
                'file_type': file_data.get('file_type', 'OTHER'),
                'file_status': file_data.get('status', 'uploaded'),
                'data': draft.get('data', {}),
                'progress': draft.get('progress', 0),
                'sections_completed': draft.get('sections_completed', []),
                'last_updated': draft.get('last_updated'),
                'created_at': draft.get('created_at')
            })
        
        return {
            "success": True,
            "drafts": drafts,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting drafts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get drafts: {str(e)}"
        )

@router.get("/{draft_id}")
async def get_draft(
    draft_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get a specific draft by ID.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        result = supabase.from_('draft_entries') \
            .select('''
                *,
                organization_files!inner (
                    id,
                    name,
                    file_type,
                    status,
                    path
                )
            ''') \
            .eq('id', draft_id) \
            .eq('user_id', current_user.user_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        draft = result.data
        file_data = draft.get('organization_files', {})
        
        return {
            "success": True,
            "draft": {
                'id': draft['id'],
                'file_id': draft['file_id'],
                'file_name': file_data.get('name', 'Unknown'),
                'file_type': file_data.get('file_type', 'OTHER'),
                'file_status': file_data.get('status', 'uploaded'),
                'file_path': file_data.get('path'),
                'data': draft.get('data', {}),
                'progress': draft.get('progress', 0),
                'sections_completed': draft.get('sections_completed', []),
                'last_updated': draft.get('last_updated'),
                'created_at': draft.get('created_at')
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get draft: {str(e)}"
        )

@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Delete a draft.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Check if draft exists
        existing = supabase.from_('draft_entries') \
            .select('id') \
            .eq('id', draft_id) \
            .eq('user_id', current_user.user_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        supabase.from_('draft_entries') \
            .delete() \
            .eq('id', draft_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Draft deleted successfully",
            "draft_id": draft_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete draft: {str(e)}"
        )

@router.post("/{draft_id}/submit")
async def submit_draft(
    draft_id: str,
    submit_data: Dict[str, Any],
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Submit a draft and create emissions record.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Get draft
        draft_result = supabase.from_('draft_entries') \
            .select('*') \
            .eq('id', draft_id) \
            .eq('user_id', current_user.user_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not draft_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        draft = draft_result.data
        data = draft.get('data', {})
        
        # Get document
        file_result = supabase.from_('organization_files') \
            .select('status') \
            .eq('id', draft['file_id']) \
            .maybe_single() \
            .execute()
        
        if file_result.data:
            # Update document status
            now = datetime.now().isoformat()
            supabase.from_('organization_files') \
                .update({
                    'status': 'approved',
                    'status_updated_at': now,
                    'approved_at': now,
                    'approved_by': current_user.user_id,
                    'metadata': {
                        'source': 'manual_entry',
                        'extraction_result': data,
                        'submitted_at': now,
                        'submitted_by': current_user.user_id
                    }
                }) \
                .eq('id', draft['file_id']) \
                .execute()
        
        # Save to emissions_logs
        try:
            # Get DEFRA factor
            defra_result = supabase.from_('defra_conversion_factors') \
                .select('id') \
                .eq('activity_type', data.get('fuel_utility_type', 'Electricity')) \
                .eq('reporting_year', data.get('reporting_year', datetime.now().year)) \
                .maybe_single() \
                .execute()
            
            defra_factor_id = defra_result.data.get('id') if defra_result.data else None
            
            # Get asset
            asset_result = supabase.from_('assets') \
                .select('id') \
                .eq('name', data.get('asset_name', '')) \
                .eq('organization_id', org_id) \
                .maybe_single() \
                .execute()
            
            asset_id = asset_result.data.get('id') if asset_result.data else None
            
            # Calculate kg CO2e
            consumption = float(data.get('consumption', 0))
            kg_co2e = consumption * 2.68  # Default multiplier
            
            now = datetime.now().isoformat()
            
            # Save to emissions_logs
            supabase.from_('emissions_logs') \
                .insert({
                    'organization_id': org_id,
                    'asset_id': asset_id,
                    'defra_factor_id': defra_factor_id,
                    'start_date': data.get('billing_start', now[:10]),
                    'end_date': data.get('billing_start', now[:10]),
                    'raw_quantity': consumption,
                    'calculated_kg_co2e': kg_co2e,
                    'created_by_user_id': current_user.user_id,
                    'file_id': draft['file_id'],
                    'metadata': {
                        'source': 'manual_entry',
                        'draft_data': data,
                        'submitted_at': now,
                        'submitted_by': current_user.user_id
                    },
                    'created_at': now
                }) \
                .execute()
        except Exception as emission_error:
            print(f"⚠️ Error saving to emissions_logs: {emission_error}")
        
        # Delete draft
        supabase.from_('draft_entries') \
            .delete() \
            .eq('id', draft_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Draft submitted successfully",
            "draft_id": draft_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error submitting draft: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit draft: {str(e)}"
        )