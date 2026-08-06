# backend/routes/drafts_enhanced.py
"""
Enhanced draft management endpoints for section-level control.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
from auth import AuthUser, require_auth, require_org_member
from database import get_supabase_client

router = APIRouter(prefix="/api/drafts", tags=["Drafts - Enhanced"])

# ==========================================
# Pydantic Models
# ==========================================

class SectionUpdate(BaseModel):
    section_id: str
    data: Dict[str, Any]
    completed: bool = False

class SectionProgress(BaseModel):
    section_id: str
    completed: bool
    data: Optional[Dict[str, Any]] = None

# ==========================================
# Draft Section Endpoints
# ==========================================

@router.get("/{draft_id}/sections")
async def get_draft_sections(
    draft_id: str,
    current_user: AuthUser = Depends(require_auth())
):
    """Get all sections of a draft."""
    try:
        supabase = get_supabase_client()
        
        # Check draft exists and user has access
        draft = supabase.from_('draft_entries') \
            .select('*') \
            .eq('id', draft_id) \
            .maybe_single() \
            .execute()
        
        if not draft.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Check access
        if draft.data['user_id'] != current_user.id and not current_user.is_admin:
            # Check if user is organization member
            if draft.data.get('organization_id'):
                member = supabase.from_('organization_members') \
                    .select('id') \
                    .eq('organization_id', draft.data['organization_id']) \
                    .eq('user_id', current_user.id) \
                    .maybe_single() \
                    .execute()
                
                if not member.data:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to view this draft"
                    )
        
        # Get or create sections
        if 'sections' not in draft.data or not draft.data['sections']:
            # Create default sections
            default_sections = {
                'sections': {
                    'general_info': {'completed': False, 'data': {}},
                    'emissions_data': {'completed': False, 'data': {}},
                    'scope_1': {'completed': False, 'data': {}},
                    'scope_2': {'completed': False, 'data': {}},
                    'scope_3': {'completed': False, 'data': {}},
                    'summary': {'completed': False, 'data': {}}
                }
            }
            
            result = supabase.from_('draft_entries') \
                .update(default_sections) \
                .eq('id', draft_id) \
                .execute()
            
            return {
                "success": True,
                "data": default_sections['sections']
            }
        
        return {
            "success": True,
            "data": draft.data['sections']
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get draft sections: {str(e)}"
        )

@router.post("/{draft_id}/sections/{section_id}")
async def update_draft_section(
    draft_id: str,
    section_id: str,
    section_data: SectionUpdate,
    current_user: AuthUser = Depends(require_auth())
):
    """Update a specific draft section."""
    try:
        supabase = get_supabase_client()
        
        # Check draft exists
        draft = supabase.from_('draft_entries') \
            .select('*') \
            .eq('id', draft_id) \
            .maybe_single() \
            .execute()
        
        if not draft.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Check access
        if draft.data['user_id'] != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to edit this draft"
            )
        
        # Get current sections
        sections = draft.data.get('sections', {})
        
        # Update section
        sections[section_id] = {
            'data': section_data.data,
            'completed': section_data.completed,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Update progress
        completed_sections = sum(1 for s in sections.values() if s.get('completed', False))
        total_sections = len(sections) if sections else 1
        progress = int((completed_sections / total_sections) * 100) if total_sections > 0 else 0
        
        update_data = {
            'sections': sections,
            'sections_completed': [s for s, v in sections.items() if v.get('completed', False)],
            'progress': progress,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('draft_entries') \
            .update(update_data) \
            .eq('id', draft_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Section updated successfully",
            "data": {
                'section': sections[section_id],
                'progress': progress,
                'completed_sections': completed_sections,
                'total_sections': total_sections
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update section: {str(e)}"
        )

@router.delete("/{draft_id}/sections/{section_id}")
async def delete_draft_section(
    draft_id: str,
    section_id: str,
    current_user: AuthUser = Depends(require_auth())
):
    """Delete a draft section (reset to empty)."""
    try:
        supabase = get_supabase_client()
        
        # Check draft exists
        draft = supabase.from_('draft_entries') \
            .select('*') \
            .eq('id', draft_id) \
            .maybe_single() \
            .execute()
        
        if not draft.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Check access
        if draft.data['user_id'] != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to edit this draft"
            )
        
        # Reset section
        sections = draft.data.get('sections', {})
        sections[section_id] = {
            'data': {},
            'completed': False,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Update progress
        completed_sections = sum(1 for s in sections.values() if s.get('completed', False))
        total_sections = len(sections) if sections else 1
        progress = int((completed_sections / total_sections) * 100) if total_sections > 0 else 0
        
        update_data = {
            'sections': sections,
            'sections_completed': [s for s, v in sections.items() if v.get('completed', False)],
            'progress': progress,
            'last_updated': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('draft_entries') \
            .update(update_data) \
            .eq('id', draft_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Section reset successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete section: {str(e)}"
        )

@router.get("/{draft_id}/progress")
async def get_draft_progress(
    draft_id: str,
    current_user: AuthUser = Depends(require_auth())
):
    """Get draft completion progress."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('draft_entries') \
            .select('progress, sections, sections_completed, last_updated') \
            .eq('id', draft_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        sections = result.data.get('sections', {})
        completed_sections = result.data.get('sections_completed', [])
        total_sections = len(sections) if sections else 1
        
        return {
            "success": True,
            "data": {
                "progress": result.data.get('progress', 0),
                "total_sections": total_sections,
                "completed_sections": len(completed_sections),
                "sections_completed": completed_sections,
                "last_updated": result.data.get('last_updated')
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get draft progress: {str(e)}"
        )

@router.post("/{draft_id}/validate")
async def validate_draft(
    draft_id: str,
    current_user: AuthUser = Depends(require_auth())
):
    """Validate draft completeness."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('draft_entries') \
            .select('*') \
            .eq('id', draft_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        sections = result.data.get('sections', {})
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'sections': {}
        }
        
        # Validate each section
        for section_id, section_data in sections.items():
            is_completed = section_data.get('completed', False)
            data = section_data.get('data', {})
            
            if is_completed and not data:
                validation_results['errors'].append(f"Section '{section_id}' is marked completed but has no data")
                validation_results['valid'] = False
            
            if data and not is_completed:
                validation_results['warnings'].append(f"Section '{section_id}' has data but is not marked completed")
            
            validation_results['sections'][section_id] = {
                'has_data': bool(data),
                'completed': is_completed,
                'valid': bool(data) if is_completed else True
            }
        
        return {
            "success": True,
            "data": validation_results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate draft: {str(e)}"
        )

@router.post("/{draft_id}/publish")
async def publish_draft(
    draft_id: str,
    current_user: AuthUser = Depends(require_auth())
):
    """Publish a completed draft."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('draft_entries') \
            .select('*') \
            .eq('id', draft_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Draft not found"
            )
        
        # Check if all sections are completed
        sections = result.data.get('sections', {})
        all_completed = all(s.get('completed', False) for s in sections.values())
        
        if not all_completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot publish draft: not all sections are completed"
            )
        
        # Mark as published
        update_data = {
            'status': 'published',
            'published_at': datetime.utcnow().isoformat(),
            'last_updated': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('draft_entries') \
            .update(update_data) \
            .eq('id', draft_id) \
            .execute()
        
        # Create emission records from draft data
        # This would be implementation-specific based on your data structure
        
        return {
            "success": True,
            "message": "Draft published successfully",
            "data": result.data[0] if result.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to publish draft: {str(e)}"
        )