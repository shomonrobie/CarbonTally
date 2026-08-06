# backend/routes/admin/bulk.py
"""
Admin bulk operations for system-wide management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from auth import AuthUser, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/bulk", tags=["Admin - Bulk Operations"])

# ==========================================
# Pydantic Models
# ==========================================

class BulkOrganizationStatusUpdate(BaseModel):
    organization_ids: List[str]
    status: str  # active, suspended, archived
    reason: Optional[str] = None

class BulkOperationResult(BaseModel):
    success_count: int
    failed_count: int
    errors: List[Dict[str, Any]]
    data: List[Dict[str, Any]]

# ==========================================
# Bulk Organization Status Update
# ==========================================

@router.post("/organizations/status")
async def bulk_update_organization_status(
    request: BulkOrganizationStatusUpdate,
    current_user: AuthUser = Depends(require_admin())
):
    """
    Bulk update organization status.
    Admin only - can activate, suspend, or archive multiple organizations.
    """
    try:
        supabase = get_supabase_client()
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': [],
            'data': []
        }
        
        for org_id in request.organization_ids:
            try:
                # Verify organization exists
                org_check = supabase.from_('organizations') \
                    .select('id, name') \
                    .eq('id', org_id) \
                    .maybe_single() \
                    .execute()
                
                if not org_check.data:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'organization_id': org_id,
                        'error': 'Organization not found'
                    })
                    continue
                
                # Update organization status
                update_data = {
                    'subscription_status': request.status,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                result = supabase.from_('organizations') \
                    .update(update_data) \
                    .eq('id', org_id) \
                    .execute()
                
                if result.data:
                    results['success_count'] += 1
                    results['data'].append({
                        'organization_id': org_id,
                        'name': org_check.data.get('name', 'Unknown'),
                        'new_status': request.status
                    })
                    
                    # Log the action
                    log_data = {
                        'organization_id': org_id,
                        'user_id': current_user.id,
                        'action': 'bulk_status_update',
                        'resource_type': 'organization',
                        'resource_id': org_id,
                        'details': {
                            'new_status': request.status,
                            'reason': request.reason
                        },
                        'created_at': datetime.utcnow().isoformat()
                    }
                    supabase.from_('activity_logs').insert(log_data).execute()
                    
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'organization_id': org_id,
                        'error': 'Failed to update status'
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'organization_id': org_id,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Bulk status update completed: {results['success_count']} successful, {results['failed_count']} failed",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update organization status: {str(e)}"
        )

@router.post("/documents/status")
async def bulk_update_document_status(
    file_ids: List[str],
    status: str,
    current_user: AuthUser = Depends(require_admin())
):
    """
    Bulk update document status.
    Admin only - can approve or reject multiple documents.
    """
    try:
        supabase = get_supabase_client()
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': [],
            'data': []
        }
        
        for file_id in file_ids:
            try:
                # Verify document exists
                doc_check = supabase.from_('organization_files') \
                    .select('id, name, organization_id') \
                    .eq('id', file_id) \
                    .maybe_single() \
                    .execute()
                
                if not doc_check.data:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'file_id': file_id,
                        'error': 'Document not found'
                    })
                    continue
                
                # Update document status
                update_data = {
                    'status': status,
                    'status_updated_at': datetime.utcnow().isoformat()
                }
                
                if status == 'approved':
                    update_data['approved_at'] = datetime.utcnow().isoformat()
                    update_data['approved_by'] = current_user.id
                elif status == 'rejected':
                    update_data['rejected_at'] = datetime.utcnow().isoformat()
                    update_data['rejected_by'] = current_user.id
                
                result = supabase.from_('organization_files') \
                    .update(update_data) \
                    .eq('id', file_id) \
                    .execute()
                
                if result.data:
                    results['success_count'] += 1
                    results['data'].append({
                        'file_id': file_id,
                        'name': doc_check.data.get('name', 'Unknown'),
                        'new_status': status
                    })
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'file_id': file_id,
                        'error': 'Failed to update status'
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'file_id': file_id,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Bulk document status update completed: {results['success_count']} successful, {results['failed_count']} failed",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk update document status: {str(e)}"
        )

@router.delete("/documents/bulk")
async def bulk_delete_documents(
    file_ids: List[str],
    current_user: AuthUser = Depends(require_admin()),
    permanent: bool = False
):
    """
    Bulk delete documents.
    Admin only - can soft delete or permanently delete multiple documents.
    """
    try:
        supabase = get_supabase_client()
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': [],
            'data': []
        }
        
        for file_id in file_ids:
            try:
                # Verify document exists
                doc_check = supabase.from_('organization_files') \
                    .select('id, name') \
                    .eq('id', file_id) \
                    .maybe_single() \
                    .execute()
                
                if not doc_check.data:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'file_id': file_id,
                        'error': 'Document not found'
                    })
                    continue
                
                if permanent:
                    # Permanently delete
                    result = supabase.from_('organization_files') \
                        .delete() \
                        .eq('id', file_id) \
                        .execute()
                else:
                    # Soft delete
                    result = supabase.from_('organization_files') \
                        .update({
                            'is_active': False,
                            'deleted_at': datetime.utcnow().isoformat()
                        }) \
                        .eq('id', file_id) \
                        .execute()
                
                if result.data:
                    results['success_count'] += 1
                    results['data'].append({
                        'file_id': file_id,
                        'name': doc_check.data.get('name', 'Unknown'),
                        'action': 'permanently_deleted' if permanent else 'soft_deleted'
                    })
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'file_id': file_id,
                        'error': 'Failed to delete document'
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'file_id': file_id,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Bulk document deletion completed: {results['success_count']} successful, {results['failed_count']} failed",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk delete documents: {str(e)}"
        )