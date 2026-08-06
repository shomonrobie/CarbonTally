# backend/routes/customer_documents.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta
from enum import Enum
from supabase import Client
import uuid

from auth import AuthUser, require_org_member, require_role
from database import get_supabase_client

# ✅ FIX: Change prefix to include organization_id
router = APIRouter(prefix="/api/customer-documents", tags=["Customer Documents"])

# ================================
# PYDANTIC MODELS (unchanged)
# ================================

class DocumentStatsResponse(BaseModel):
    total_documents: int
    pending_review: int
    approved: int
    rejected: int
    under_review: int
    by_status: Dict[str, int]
    by_asset: Dict[str, int]
    by_type: Dict[str, int]
    recent_uploads: int

class PendingDocumentResponse(BaseModel):
    id: str
    file_name: str
    file_url: str
    file_type: str
    status: str
    upload_date: Optional[datetime]
    asset_id: str
    asset_name: str
    organization_id: str
    organization_name: str
    manual_review_queue_id: Optional[str]
    priority: Optional[int]
    assigned_to: Optional[str]
    assigned_to_name: Optional[str]
    created_at: datetime

class AssetDocumentsResponse(BaseModel):
    asset_id: str
    asset_name: str
    total_documents: int
    documents: List[Dict[str, Any]]

class ExtractionDataResponse(BaseModel):
    document_id: str
    file_name: str
    file_url: str
    extraction_data: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    status: str
    asset_id: str
    asset_name: str
    verified_at: Optional[datetime]
    verified_by: Optional[str]

class VerificationRequest(BaseModel):
    status: str
    notes: Optional[str] = None
    extraction_data: Optional[Dict[str, Any]] = None

    @field_validator('status')
    @classmethod
    def validate_status(cls, v: str) -> str:
        if v not in ['approved', 'rejected']:
            raise ValueError("Status must be 'approved' or 'rejected'")
        return v

class ReviewRequestResponse(BaseModel):
    success: bool
    message: str
    review_queue_id: Optional[str]
    assigned_to: Optional[str]

class ManualReviewRequest(BaseModel):
    priority: Optional[int] = Field(1, ge=1, le=5)
    notes: Optional[str] = None
    assigned_to: Optional[str] = None

# ================================
# ✅ FIXED: ENDPOINTS WITH org_id PARAMETER
# ================================

@router.get("/stats/{org_id}")
async def get_document_statistics(
    org_id: str,  # ✅ Add org_id parameter
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get comprehensive statistics about customer documents for an organization."""
    try:
        # ✅ Verify user has access to this organization
        member_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this organization"
            )
        
        # Get all documents for the organization
        docs_result = supabase.from_('customer_documents') \
            .select('id, status, asset_id, file_type, upload_date, created_at, assets(name)') \
            .eq('organization_id', org_id) \
            .execute()
        
        documents = docs_result.data or []
        
        # Calculate statistics
        total = len(documents)
        status_counts = {}
        pending = 0
        approved = 0
        rejected = 0
        under_review = 0
        
        for doc in documents:
            status = doc.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
            
            if status in ['uploaded', 'processing']:
                pending += 1
            elif status == 'approved':
                approved += 1
            elif status == 'rejected':
                rejected += 1
            elif status in ['staff_review', 'ready_for_review']:
                under_review += 1
        
        # Asset counts
        asset_counts = {}
        for doc in documents:
            asset_id = doc.get('asset_id')
            if asset_id:
                asset_name = doc.get('assets', {}).get('name', 'Unknown')
                key = f"{asset_id}::{asset_name}"
                asset_counts[key] = asset_counts.get(key, 0) + 1
        
        # Type counts
        type_counts = {}
        for doc in documents:
            file_type = doc.get('file_type', 'unknown')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        # Recent uploads (last 24 hours)
        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent = sum(1 for doc in documents 
                    if doc.get('upload_date') and doc['upload_date'] >= cutoff)
        
        return {
            "success": True,
            "data": {
                "total_documents": total,
                "pending_review": pending,
                "approved": approved,
                "rejected": rejected,
                "under_review": under_review,
                "by_status": status_counts,
                "by_asset": asset_counts,
                "by_type": type_counts,
                "recent_uploads": recent
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document statistics: {str(e)}"
        )


@router.get("/pending/{org_id}")
async def get_pending_documents(
    org_id: str,  # ✅ Add org_id parameter
    current_user: AuthUser = Depends(require_org_member()),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all pending documents that need customer review for an organization."""
    try:
        # ✅ Verify user has access to this organization
        member_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this organization"
            )
        
        docs_result = supabase.from_('customer_documents') \
            .select('''
                id, file_name, file_url, file_type, status, upload_date, 
                created_at, asset_id, organization_id,
                assets!inner(name),
                organizations!inner(name),
                manual_review_queue!left(id, priority, assigned_to, staff_profiles!left(user_id, first_name, last_name))
            ''') \
            .eq('organization_id', org_id) \
            .in_('status', ['uploaded', 'processing', 'ready_for_review']) \
            .order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        documents = docs_result.data or []
        
        pending_docs = []
        for doc in documents:
            asset_name = doc.get('assets', {}).get('name', 'Unknown Asset') if doc.get('assets') else 'Unknown Asset'
            org_name = doc.get('organizations', {}).get('name', 'Unknown Organization') if doc.get('organizations') else 'Unknown Organization'
            
            manual_review = doc.get('manual_review_queue', {})
            staff_profile = manual_review.get('staff_profiles', {}) if manual_review else {}
            
            pending_docs.append({
                'id': doc['id'],
                'file_name': doc['file_name'],
                'file_url': doc['file_url'],
                'file_type': doc.get('file_type', 'unknown'),
                'status': doc['status'],
                'upload_date': doc.get('upload_date'),
                'asset_id': doc['asset_id'],
                'asset_name': asset_name,
                'organization_id': doc['organization_id'],
                'organization_name': org_name,
                'manual_review_queue_id': manual_review.get('id') if manual_review else None,
                'priority': manual_review.get('priority') if manual_review else None,
                'assigned_to': manual_review.get('assigned_to') if manual_review else None,
                'assigned_to_name': f"{staff_profile.get('first_name', '')} {staff_profile.get('last_name', '')}".strip() if staff_profile else None,
                'created_at': doc['created_at']
            })
        
        return {
            "success": True,
            "documents": pending_docs,
            "total": len(pending_docs)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting pending documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending documents: {str(e)}"
        )


@router.get("/documents/{org_id}")
async def get_customer_documents(
    org_id: str,  # ✅ Add org_id parameter
    asset_id: Optional[str] = Query(None, description="Filter by asset"),
    status: Optional[str] = Query(None, description="Filter by status"),
    file_type: Optional[str] = Query(None, description="Filter by file type"),
    document_type_code: Optional[str] = Query(None, description="Filter by document type"),
    search: Optional[str] = Query(None, description="Search in file name"),
    start_date: Optional[str] = Query(None, description="Start date for uploads"),
    end_date: Optional[str] = Query(None, description="End date for uploads"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_org_member())
):
    """Get all documents for an organization with asset info and document types."""
    try:
        supabase = get_supabase_client()
        
        # ✅ Verify user has access to this organization
        member_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this organization"
            )
        
        # Build query
        query = supabase.from_('customer_documents') \
            .select('''
                *,
                assets (
                    id,
                    name,
                    type,
                    facility:facility_id (
                        id,
                        name
                    )
                ),
                document_types (
                    id,
                    code,
                    name,
                    category,
                    description,
                    requires_asset,
                    requires_date_range,
                    requires_facility
                ),
                manual_review_queue (
                    id,
                    status as extraction_status,
                    assigned_to
                )
            ''') \
            .eq('organization_id', org_id)
        
        # Apply filters
        if asset_id:
            query = query.eq('asset_id', asset_id)
        if status:
            query = query.eq('status', status)
        if file_type:
            query = query.eq('file_type', file_type)
        if document_type_code:
            query = query.eq('document_type_code', document_type_code)
        if search:
            query = query.ilike('file_name', f'%{search}%')
        if start_date:
            query = query.gte('upload_date', start_date)
        if end_date:
            query = query.lte('upload_date', end_date)
        
        # Count query
        count_query = supabase.from_('customer_documents') \
            .select('id', count='exact') \
            .eq('organization_id', org_id)
        
        if asset_id:
            count_query = count_query.eq('asset_id', asset_id)
        if status:
            count_query = count_query.eq('status', status)
        if file_type:
            count_query = count_query.eq('file_type', file_type)
        if document_type_code:
            count_query = count_query.eq('document_type_code', document_type_code)
        if search:
            count_query = count_query.ilike('file_name', f'%{search}%')
        if start_date:
            count_query = count_query.gte('upload_date', start_date)
        if end_date:
            count_query = count_query.lte('upload_date', end_date)
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # Get paginated results
        result = query.order('upload_date', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Format response
        documents = []
        for doc in (result.data or []):
            asset = doc.get('assets', {}) or {}
            facility = asset.get('facility', {}) or {}
            review_queue = doc.get('manual_review_queue', {}) or {}
            doc_type = doc.get('document_types', {}) or {}
            
            documents.append({
                'id': doc['id'],
                'organization_id': doc['organization_id'],
                'asset_id': doc.get('asset_id'),
                'asset_name': asset.get('name'),
                'asset_type': asset.get('type'),
                'facility_name': facility.get('name'),
                'file_name': doc['file_name'],
                'file_url': doc['file_url'],
                'file_type': doc.get('file_type', 'other'),
                'status': doc.get('status', 'pending'),
                'upload_date': doc.get('upload_date'),
                'created_at': doc.get('created_at'),
                'updated_at': doc.get('updated_at'),
                'document_type_code': doc.get('document_type_code'),
                'document_type_name': doc_type.get('name'),
                'document_type_category': doc_type.get('category'),
                'billing_period_start': doc.get('billing_period_start'),
                'billing_period_end': doc.get('billing_period_end'),
                'organization_notes': doc.get('organization_notes')
            })
        
        return {
            "success": True,
            "documents": documents,
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting customer documents: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer documents: {str(e)}"
        )


# Continue with other endpoints following the same pattern...
# All endpoints should accept org_id as a path parameter

@router.get("/assets/{asset_id}", response_model=List[Dict[str, Any]])
async def get_documents_for_asset(
    asset_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get all documents for a specific asset.
    
    Returns all documents associated with the given asset ID.
    """
    try:
        # Verify asset exists and user has access
        asset_result = supabase.from_('assets') \
            .select('id, name, organization_id, organizations(name)') \
            .eq('id', asset_id) \
            .maybe_single() \
            .execute()
        
        if not asset_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        asset = asset_result.data
        org_id = asset.get('organization_id')
        
        # Verify user belongs to the organization
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this asset"
                )
        
        # Get documents for this asset
        docs_result = supabase.from_('customer_documents') \
            .select('''
                id, organization_id, asset_id, file_name, file_url, 
                file_type, status, upload_date, created_at, updated_at,
                organizations(name)
            ''') \
            .eq('asset_id', asset_id) \
            .order('created_at', desc=True) \
            .execute()
        
        documents = docs_result.data or []
        
        # Enrich response
        enriched_docs = []
        for doc in documents:
            enriched_docs.append({
                'id': doc['id'],
                'organization_id': doc['organization_id'],
                'organization_name': doc.get('organizations', {}).get('name', 'Unknown') if doc.get('organizations') else 'Unknown',
                'asset_id': doc['asset_id'],
                'asset_name': asset.get('name', 'Unknown Asset'),
                'file_name': doc['file_name'],
                'file_url': doc['file_url'],
                'file_type': doc.get('file_type', 'unknown'),
                'status': doc['status'],
                'upload_date': doc.get('upload_date'),
                'created_at': doc['created_at'],
                'updated_at': doc.get('updated_at')
            })
        
        return {
            "success": True,
            "asset_id": asset_id,
            "asset_name": asset.get('name', 'Unknown Asset'),
            "organization_id": org_id,
            "organization_name": asset.get('organizations', {}).get('name', 'Unknown') if asset.get('organizations') else 'Unknown',
            "total_documents": len(enriched_docs),
            "documents": enriched_docs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting documents for asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents for asset: {str(e)}"
        )


@router.get("/{document_id}", response_model=Dict[str, Any])
async def get_customer_document(
    document_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get detailed information about a specific customer document.
    
    Returns complete document details including associated data.
    """
    try:
        # Get document with joins
        result = supabase.from_('customer_documents') \
            .select('''
                id, organization_id, asset_id, file_name, file_url, 
                file_type, status, upload_date, extraction_data,
                metadata, verified_at, verified_by, created_at, updated_at,
                manual_review_queue_id,
                assets(name, type, description),
                organizations(name),
                staff_profiles!verified_by(first_name, last_name, email)
            ''') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc = result.data
        
        # Verify user belongs to the organization
        org_id = doc.get('organization_id') or doc.get('assets', {}).get('organization_id')
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )
        
        # Get verifier details
        verifier_name = None
        verifier_email = None
        staff_profile = doc.get('staff_profiles', {}) if doc.get('staff_profiles') else {}
        if staff_profile:
            first_name = staff_profile.get('first_name', '')
            last_name = staff_profile.get('last_name', '')
            verifier_name = f"{first_name} {last_name}".strip() or None
            verifier_email = staff_profile.get('email')
        
        # Get review queue details if exists
        review_queue = None
        if doc.get('manual_review_queue_id'):
            queue_result = supabase.from_('manual_review_queue') \
                .select('''
                    id, status, priority, assigned_to, assigned_by,
                    staff_profiles!assigned_to(first_name, last_name, email)
                ''') \
                .eq('id', doc['manual_review_queue_id']) \
                .maybe_single() \
                .execute()
            
            if queue_result.data:
                queue_data = queue_result.data
                assigned_staff = queue_data.get('staff_profiles', {}) if queue_data.get('staff_profiles') else {}
                review_queue = {
                    'id': queue_data['id'],
                    'status': queue_data.get('status'),
                    'priority': queue_data.get('priority'),
                    'assigned_to': queue_data.get('assigned_to'),
                    'assigned_to_name': f"{assigned_staff.get('first_name', '')} {assigned_staff.get('last_name', '')}".strip() or None if assigned_staff else None,
                    'assigned_to_email': assigned_staff.get('email') if assigned_staff else None
                }
        
        # Build response
        return {
            "success": True,
            "document": {
                'id': doc['id'],
                'organization_id': doc['organization_id'],
                'organization_name': doc.get('organizations', {}).get('name', 'Unknown') if doc.get('organizations') else 'Unknown',
                'asset_id': doc['asset_id'],
                'asset_name': doc.get('assets', {}).get('name', 'Unknown Asset') if doc.get('assets') else 'Unknown Asset',
                'asset_type': doc.get('assets', {}).get('type') if doc.get('assets') else None,
                'asset_description': doc.get('assets', {}).get('description') if doc.get('assets') else None,
                'file_name': doc['file_name'],
                'file_url': doc['file_url'],
                'file_type': doc.get('file_type', 'unknown'),
                'status': doc['status'],
                'upload_date': doc.get('upload_date'),
                'extraction_data': doc.get('extraction_data'),
                'metadata': doc.get('metadata'),
                'verified_at': doc.get('verified_at'),
                'verified_by': doc.get('verified_by'),
                'verifier_name': verifier_name,
                'verifier_email': verifier_email,
                'created_at': doc['created_at'],
                'updated_at': doc.get('updated_at'),
                'manual_review_queue': review_queue
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting customer document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get customer document: {str(e)}"
        )
    
@router.get("/{document_id}/extraction", response_model=ExtractionDataResponse)
async def get_extraction_details(
    document_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get extraction data for a specific document."""
    try:
        # First get the document with organization info
        doc_result = supabase.from_('customer_documents') \
            .select('organization_id, asset_id, assets(organization_id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Verify user has access to this organization
        org_id = doc_result.data.get('organization_id') or doc_result.data.get('assets', {}).get('organization_id')
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has no associated organization"
            )
        
        member_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this document"
            )
        
        # Get full document with extraction data
        result = supabase.from_('customer_documents') \
            .select('''
                id, file_name, file_url, status, extraction_data, 
                metadata, asset_id, verified_at, verified_by,
                assets(name),
                staff_profiles!verified_by(first_name, last_name)
            ''') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc = result.data
        asset_name = doc.get('assets', {}).get('name', 'Unknown Asset') if doc.get('assets') else 'Unknown Asset'
        
        verified_by_name = None
        staff_profile = doc.get('staff_profiles', {}) if doc.get('staff_profiles') else {}
        if staff_profile:
            first_name = staff_profile.get('first_name', '')
            last_name = staff_profile.get('last_name', '')
            verified_by_name = f"{first_name} {last_name}".strip()
        
        return ExtractionDataResponse(
            document_id=doc['id'],
            file_name=doc['file_name'],
            file_url=doc['file_url'],
            extraction_data=doc.get('extraction_data'),
            metadata=doc.get('metadata'),
            status=doc['status'],
            asset_id=doc['asset_id'],
            asset_name=asset_name,
            verified_at=doc.get('verified_at'),
            verified_by=verified_by_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting extraction details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get extraction details: {str(e)}"
        )


@router.post("/{document_id}/verify")
async def verify_document(
    document_id: str,
    verification_data: VerificationRequest,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Verify a document (approve or reject)."""
    try:
        # Get document and verify access
        doc_result = supabase.from_('customer_documents') \
            .select('organization_id, status, file_name, asset_id, metadata, assets(organization_id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        org_id = doc_result.data.get('organization_id') or doc_result.data.get('assets', {}).get('organization_id')
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has no associated organization"
            )
        
        member_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this document"
            )
        
        # Prevent re-verification
        if doc_result.data['status'] in ['approved', 'rejected']:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Document already {doc_result.data['status']}"
            )
        
        # Update document
        now = datetime.utcnow().isoformat()
        update_data = {
            'status': verification_data.status,
            'verified_at': now,
            'verified_by': current_user.id,
            'updated_at': now
        }
        
        if verification_data.extraction_data is not None:
            update_data['extraction_data'] = verification_data.extraction_data
        
        if verification_data.notes:
            metadata = doc_result.data.get('metadata', {})
            metadata['verification_notes'] = verification_data.notes
            update_data['metadata'] = metadata
        
        result = supabase.from_('customer_documents') \
            .update(update_data) \
            .eq('id', document_id) \
            .execute()
        
        # Create audit log
        try:
            audit_data = {
                'user_id': current_user.id,
                'organization_id': org_id,
                'action_type': 'verification',
                'resource_type': 'customer_document',
                'resource_id': document_id,
                'action': verification_data.status,
                'description': f"Document {verification_data.status}: {doc_result.data.get('file_name', document_id)}",
                'old_data': {'status': doc_result.data.get('status')},
                'new_data': {'status': verification_data.status},
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error creating audit log: {audit_error}")
        
        return {
            "success": True,
            "message": f"Document {verification_data.status} successfully",
            "document_id": document_id,
            "status": verification_data.status
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error verifying document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify document: {str(e)}"
        )


@router.post("/{document_id}/request-review", response_model=ReviewRequestResponse)
async def request_staff_review(
    document_id: str,
    review_request: ManualReviewRequest,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Request staff review for a document."""
    try:
        # Get document and verify access
        doc_result = supabase.from_('customer_documents') \
            .select('organization_id, status, file_name, file_url, file_type, asset_id, metadata, assets(organization_id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        org_id = doc_result.data.get('organization_id') or doc_result.data.get('assets', {}).get('organization_id')
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has no associated organization"
            )
        
        member_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this document"
            )
        
        # Check if already in review queue
        existing = supabase.from_('manual_review_queue') \
            .select('id, status') \
            .eq('customer_document_id', document_id) \
            .in_('status', ['pending', 'in_progress', 'assigned']) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            return ReviewRequestResponse(
                success=True,
                message=f"Document already in review queue (status: {existing.data['status']})",
                review_queue_id=existing.data['id'],
                assigned_to=None
            )
        
        # Create review queue entry
        now = datetime.utcnow().isoformat()
        
        assigned_to = None
        if review_request.assigned_to:
            staff_check = supabase.from_('staff_profiles') \
                .select('id, user_id') \
                .eq('user_id', review_request.assigned_to) \
                .eq('organization_id', org_id) \
                .maybe_single() \
                .execute()
            
            if staff_check.data:
                assigned_to = review_request.assigned_to
        
        queue_data = {
            'organization_id': org_id,
            'customer_document_id': document_id,
            'file_url': doc_result.data.get('file_url'),
            'file_name': doc_result.data.get('file_name'),
            'file_type': doc_result.data.get('file_type', 'unknown'),
            'data_type': doc_result.data.get('file_type', 'unknown'),
            'status': 'pending' if not assigned_to else 'assigned',
            'priority': review_request.priority or 1,
            'assigned_to': assigned_to,
            'assigned_by': current_user.id if assigned_to else None,
            'customer_notes': review_request.notes,
            'created_at': now,
            'updated_at': now
        }
        
        result = supabase.from_('manual_review_queue') \
            .insert(queue_data) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create review queue entry"
            )
        
        queue_id = result.data[0]['id']
        
        # Update document status
        supabase.from_('customer_documents') \
            .update({
                'status': 'staff_review',
                'manual_review_queue_id': queue_id,
                'updated_at': now
            }) \
            .eq('id', document_id) \
            .execute()
        
        # Create audit log
        try:
            audit_data = {
                'user_id': current_user.id,
                'organization_id': org_id,
                'action_type': 'review_request',
                'resource_type': 'customer_document',
                'resource_id': document_id,
                'action': 'request_review',
                'description': f"Requested staff review for document: {doc_result.data.get('file_name', document_id)}",
                'new_data': {'queue_id': queue_id, 'assigned_to': assigned_to, 'priority': review_request.priority},
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error creating audit log: {audit_error}")
        
        assigned_name = None
        if assigned_to:
            staff_result = supabase.from_('staff_profiles') \
                .select('first_name, last_name') \
                .eq('user_id', assigned_to) \
                .maybe_single() \
                .execute()
            
            if staff_result.data:
                first = staff_result.data.get('first_name', '')
                last = staff_result.data.get('last_name', '')
                assigned_name = f"{first} {last}".strip()
        
        return ReviewRequestResponse(
            success=True,
            message="Staff review requested successfully",
            review_queue_id=queue_id,
            assigned_to=assigned_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error requesting staff review: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request staff review: {str(e)}"
        )
@router.post("/staff/organize/{document_id}")
async def organize_document_for_customer(
    document_id: str,
    data: Dict[str, Any],
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Staff can organize a document by assigning the correct type and metadata.
    Used when customers upload documents without proper classification.
    """
    try:
        supabase = get_supabase_client()
        
        # Get document
        doc = supabase.from_('customer_documents') \
            .select('*, organizations!inner(name)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc.data:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Validate document type
        if data.get('document_type_code'):
            type_check = supabase.from_('document_types') \
                .select('id, name, category, requires_asset, requires_date_range, requires_facility') \
                .eq('code', data['document_type_code']) \
                .eq('is_active', True) \
                .maybe_single() \
                .execute()
            
            if not type_check.data:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid document type: {data['document_type_code']}"
                )
            
            doc_type = type_check.data
            
            # Validate required fields based on document type
            if doc_type.get('requires_asset') and not data.get('asset_id'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Document type '{doc_type['name']}' requires an asset"
                )
            
            if doc_type.get('requires_date_range') and not (data.get('billing_period_start') and data.get('billing_period_end')):
                raise HTTPException(
                    status_code=400,
                    detail=f"Document type '{doc_type['name']}' requires date range"
                )
            
            if doc_type.get('requires_facility') and not data.get('facility_id'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Document type '{doc_type['name']}' requires a facility"
                )
        
        # Verify asset belongs to organization
        if data.get('asset_id'):
            asset_check = supabase.from_('assets') \
                .select('id, name, facility_id') \
                .eq('id', data['asset_id']) \
                .eq('facility.organization_id', doc.data['organization_id']) \
                .maybe_single() \
                .execute()
            
            if not asset_check.data:
                raise HTTPException(
                    status_code=400,
                    detail="Asset not found or does not belong to this organization"
                )
            
            data['facility_id'] = asset_check.data.get('facility_id')
        
        # Update document
        now = datetime.now().isoformat()
        update_data = {
            'document_type_code': data.get('document_type_code'),
            'document_type_id': doc_type['id'] if data.get('document_type_code') else None,
            'asset_id': data.get('asset_id'),
            'facility_id': data.get('facility_id'),
            'billing_period_start': data.get('billing_period_start'),
            'billing_period_end': data.get('billing_period_end'),
            'organization_classification': 'staff_assigned',
            'classification_by': current_user.user_id,
            'classification_at': now,
            'organization_notes': data.get('notes'),
            'status': 'organized',
            'updated_at': now
        }
        
        result = supabase.from_('customer_documents') \
            .update(update_data) \
            .eq('id', document_id) \
            .execute()
        
        # Create extraction task if requested
        if data.get('auto_extract', True):
            await create_extraction_task(supabase, document_id, current_user)
        
        return {
            "success": True,
            "message": "Document organized successfully",
            "document": result.data[0] if result.data else None,
            "document_type": doc_type if data.get('document_type_code') else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error organizing document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

async def create_extraction_task(supabase, document_id: str, current_user):
    """Helper function to create extraction task."""
    try:
        # Get document details
        doc = supabase.from_('customer_documents') \
            .select('*, organizations!inner(id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc.data:
            return
        
        # Create manual review queue entry
        queue_data = {
            'organization_id': doc.data['organization_id'],
            'file_url': doc.data['file_url'],
            'file_name': doc.data['file_name'],
            'file_type': doc.data['file_type'],
            'data_type': 'mixed',
            'status': 'pending',
            'priority': 0,
            'customer_notes': doc.data.get('organization_notes', ''),
            'customer_document_id': document_id,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.from_('manual_review_queue') \
            .insert(queue_data) \
            .execute()
        
        if result.data:
            # Update customer_document with review queue ID
            supabase.from_('customer_documents') \
                .update({
                    'manual_review_queue_id': result.data[0]['id'],
                    'updated_at': datetime.now().isoformat()
                }) \
                .eq('id', document_id) \
                .execute()
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        print(f"⚠️ Error creating extraction task: {e}")
        return None

# ================================
# ADDITIONAL PYDANTIC MODELS
# ================================

class DocumentHistoryResponse(BaseModel):
    """Response model for document history."""
    id: str
    document_id: str
    action: str
    action_type: str
    description: Optional[str]
    old_status: Optional[str]
    new_status: Optional[str]
    user_id: Optional[str]
    user_name: Optional[str]
    user_email: Optional[str]
    created_at: datetime
    details: Optional[Dict[str, Any]]


class DocumentNoteCreate(BaseModel):
    """Request model for creating a document note."""
    content: str = Field(..., description="Note content")
    is_internal: bool = Field(False, description="Internal note (staff only)")

    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Note content cannot be empty")
        if len(v) > 5000:
            raise ValueError("Note exceeds maximum length of 5000 characters")
        return v.strip()


class DocumentNoteResponse(BaseModel):
    """Response model for document note."""
    id: str
    document_id: str
    user_id: str
    user_name: Optional[str]
    user_email: Optional[str]
    content: str
    is_internal: bool
    created_at: datetime
    updated_at: Optional[datetime]


class DocumentVersionResponse(BaseModel):
    """Response model for document version."""
    id: str
    document_id: str
    version_number: int
    file_url: str
    file_name: str
    file_size: Optional[int]
    changes: Optional[Dict[str, Any]]
    created_by: Optional[str]
    created_by_name: Optional[str]
    created_at: datetime


class DocumentVersionCreate(BaseModel):
    """Request model for creating a document version."""
    file_url: str = Field(..., description="URL to the new version file")
    file_name: str = Field(..., description="Name of the new version file")
    file_size: Optional[int] = Field(None, description="File size in bytes")
    changes: Optional[Dict[str, Any]] = Field(None, description="Description of changes")


class DetailedStatsResponse(BaseModel):
    """Response model for detailed document statistics."""
    overview: Dict[str, Any]
    status_trend: List[Dict[str, Any]]
    timeline: List[Dict[str, Any]]
    categories: Dict[str, Any]
    performance: Dict[str, Any]
    top_documents: List[Dict[str, Any]]


# ================================
# NEW ENDPOINTS
# ================================

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get download URL for a document."""
    try:
        # Get document and verify access
        doc_result = supabase.from_('customer_documents') \
            .select('id, file_url, file_name, organization_id, assets(organization_id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc = doc_result.data
        
        # Get organization ID
        org_id = doc.get('organization_id') or doc.get('assets', {}).get('organization_id')
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Document has no associated organization"
            )
        
        # Verify user belongs to the organization
        member_check = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this document"
            )
        
        # Log download activity
        try:
            now = datetime.utcnow().isoformat()
            audit_data = {
                'user_id': current_user.id,
                'organization_id': org_id,
                'action_type': 'download',
                'resource_type': 'customer_document',
                'resource_id': document_id,
                'action': 'download',
                'description': f"Downloaded document: {doc.get('file_name', document_id)}",
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error logging download: {audit_error}")
        
        return {
            "success": True,
            "document_id": document_id,
            "file_url": doc['file_url'],
            "file_name": doc.get('file_name', 'document'),
            "message": "Download URL retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting download URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get download URL: {str(e)}"
        )


@router.get("/{document_id}/history", response_model=List[DocumentHistoryResponse])
async def get_document_history(
    document_id: str,
    limit: int = Query(50, ge=1, le=200, description="Number of history entries to return"),
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get document history/audit trail."""
    try:
        # Verify access
        doc_result = supabase.from_('customer_documents') \
            .select('id, organization_id, assets(organization_id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        org_id = doc_result.data.get('organization_id') or doc_result.data.get('assets', {}).get('organization_id')
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )
        
        # Get audit logs for this document
        result = supabase.from_('audit_logs') \
            .select('''
                id, action_type, action, description, 
                old_data, new_data, changes, created_at,
                user_id, staff_id, organization_member_id
            ''') \
            .eq('resource_id', document_id) \
            .eq('resource_type', 'customer_document') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        logs = result.data or []
        
        # Enrich with user details
        history = []
        for log in logs:
            user_id = log.get('user_id') or log.get('staff_id') or log.get('organization_member_id')
            user_name = None
            user_email = None
            
            if user_id:
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', user_id) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    user_email = user_result.data.get('email')
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
            
            # Extract status changes
            old_status = None
            new_status = None
            if log.get('old_data') and isinstance(log.get('old_data'), dict):
                old_status = log['old_data'].get('status')
            if log.get('new_data') and isinstance(log.get('new_data'), dict):
                new_status = log['new_data'].get('status')
            
            history.append(DocumentHistoryResponse(
                id=log['id'],
                document_id=document_id,
                action=log.get('action', 'unknown'),
                action_type=log.get('action_type', 'unknown'),
                description=log.get('description'),
                old_status=old_status,
                new_status=new_status,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                created_at=log['created_at'],
                details=log.get('changes') or log.get('new_data') or None
            ))
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document history: {str(e)}"
        )


@router.get("/{document_id}/notes", response_model=List[DocumentNoteResponse])
async def get_document_notes(
    document_id: str,
    include_internal: bool = Query(False, description="Include internal notes (staff only)"),
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get notes for a document."""
    try:
        # Verify access
        doc_result = supabase.from_('customer_documents') \
            .select('id, organization_id, assets(organization_id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        org_id = doc_result.data.get('organization_id') or doc_result.data.get('assets', {}).get('organization_id')
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )
        
        # Check if user is staff for internal notes
        is_staff = False
        if include_internal:
            staff_check = supabase.from_('staff_profiles') \
                .select('id') \
                .eq('user_id', current_user.id) \
                .maybe_single() \
                .execute()
            is_staff = bool(staff_check.data)
        
        # Get notes from metadata
        result = supabase.from_('customer_documents') \
            .select('metadata') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        notes = []
        if result.data and result.data.get('metadata'):
            metadata = result.data['metadata']
            all_notes = metadata.get('notes', [])
            
            for note in all_notes:
                # Filter internal notes if not staff
                if note.get('is_internal', False) and not (include_internal and is_staff):
                    continue
                
                # Get user details
                user_id = note.get('user_id')
                user_name = None
                user_email = None
                if user_id:
                    user_result = supabase.from_('auth.users') \
                        .select('email, raw_user_meta_data') \
                        .eq('id', user_id) \
                        .maybe_single() \
                        .execute()
                    
                    if user_result.data:
                        user_email = user_result.data.get('email')
                        raw_meta = user_result.data.get('raw_user_meta_data', {})
                        user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
                
                notes.append(DocumentNoteResponse(
                    id=note.get('id', str(uuid.uuid4())),
                    document_id=document_id,
                    user_id=user_id,
                    user_name=user_name,
                    user_email=user_email,
                    content=note.get('content', ''),
                    is_internal=note.get('is_internal', False),
                    created_at=datetime.fromisoformat(note.get('created_at')) if note.get('created_at') else datetime.utcnow(),
                    updated_at=datetime.fromisoformat(note.get('updated_at')) if note.get('updated_at') else None
                ))
        
        # Sort by created_at descending
        notes.sort(key=lambda x: x.created_at, reverse=True)
        
        return notes
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document notes: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document notes: {str(e)}"
        )


@router.post("/{document_id}/notes", response_model=DocumentNoteResponse)
async def add_document_note(
    document_id: str,
    note_data: DocumentNoteCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Add a note to a document."""
    try:
        # Verify access
        doc_result = supabase.from_('customer_documents') \
            .select('id, organization_id, metadata, assets(organization_id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc = doc_result.data
        org_id = doc.get('organization_id') or doc.get('assets', {}).get('organization_id')
        
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )
        
        # Check if internal note and user is staff
        if note_data.is_internal:
            staff_check = supabase.from_('staff_profiles') \
                .select('id') \
                .eq('user_id', current_user.id) \
                .maybe_single() \
                .execute()
            
            if not staff_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only staff members can create internal notes"
                )
        
        now = datetime.utcnow().isoformat()
        
        # Create note
        note = {
            'id': str(uuid.uuid4()),
            'user_id': current_user.id,
            'content': note_data.content,
            'is_internal': note_data.is_internal,
            'created_at': now,
            'updated_at': now
        }
        
        # Update document metadata
        metadata = doc.get('metadata', {})
        if 'notes' not in metadata:
            metadata['notes'] = []
        metadata['notes'].append(note)
        
        update_result = supabase.from_('customer_documents') \
            .update({
                'metadata': metadata,
                'updated_at': now
            }) \
            .eq('id', document_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to add note"
            )
        
        # Get user details for response
        user_name = None
        user_email = None
        user_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.id) \
            .maybe_single() \
            .execute()
        
        if user_result.data:
            user_email = user_result.data.get('email')
            raw_meta = user_result.data.get('raw_user_meta_data', {})
            user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
        
        return DocumentNoteResponse(
            id=note['id'],
            document_id=document_id,
            user_id=current_user.id,
            user_name=user_name,
            user_email=user_email,
            content=note['content'],
            is_internal=note['is_internal'],
            created_at=datetime.fromisoformat(note['created_at']),
            updated_at=datetime.fromisoformat(note['updated_at'])
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error adding document note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add note: {str(e)}"
        )


@router.get("/{document_id}/versions", response_model=List[DocumentVersionResponse])
async def get_document_versions(
    document_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all versions of a document."""
    try:
        # Verify access
        doc_result = supabase.from_('customer_documents') \
            .select('id, organization_id, metadata, assets(organization_id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc = doc_result.data
        org_id = doc.get('organization_id') or doc.get('assets', {}).get('organization_id')
        
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )
        
        # Get versions from metadata
        metadata = doc.get('metadata', {})
        versions = metadata.get('versions', [])
        
        # Include current version as first entry
        current_version = {
            'id': str(uuid.uuid4()),
            'version_number': len(versions) + 1,
            'file_url': doc.get('file_url'),
            'file_name': doc.get('file_name'),
            'file_size': metadata.get('file_size'),
            'changes': {'type': 'current', 'description': 'Current version'},
            'created_by': doc.get('organization_member_id'),
            'created_at': doc.get('created_at')
        }
        
        # Add current version first, then historical versions
        all_versions = [current_version] + versions
        
        # Enrich with user details
        response_versions = []
        for v in all_versions:
            created_by_name = None
            if v.get('created_by'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', v['created_by']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
            
            response_versions.append(DocumentVersionResponse(
                id=v.get('id', str(uuid.uuid4())),
                document_id=document_id,
                version_number=v.get('version_number', 1),
                file_url=v.get('file_url', ''),
                file_name=v.get('file_name', ''),
                file_size=v.get('file_size'),
                changes=v.get('changes'),
                created_by=v.get('created_by'),
                created_by_name=created_by_name,
                created_at=datetime.fromisoformat(v['created_at']) if isinstance(v.get('created_at'), str) else v.get('created_at', datetime.utcnow())
            ))
        
        # Sort by version number descending
        response_versions.sort(key=lambda x: x.version_number, reverse=True)
        
        return response_versions
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document versions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document versions: {str(e)}"
        )


@router.post("/{document_id}/versions", response_model=DocumentVersionResponse)
async def create_document_version(
    document_id: str,
    version_data: DocumentVersionCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a new version of a document."""
    try:
        # Verify access
        doc_result = supabase.from_('customer_documents') \
            .select('id, organization_id, file_url, file_name, metadata, assets(organization_id)') \
            .eq('id', document_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc = doc_result.data
        org_id = doc.get('organization_id') or doc.get('assets', {}).get('organization_id')
        
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this document"
                )
        
        now = datetime.utcnow().isoformat()
        
        # Get current versions
        metadata = doc.get('metadata', {})
        versions = metadata.get('versions', [])
        
        # Save current version to history
        current_version = {
            'id': str(uuid.uuid4()),
            'version_number': len(versions) + 1,
            'file_url': doc.get('file_url'),
            'file_name': doc.get('file_name'),
            'file_size': metadata.get('file_size'),
            'changes': {'type': 'previous', 'description': 'Previous version before update'},
            'created_by': doc.get('organization_member_id') or doc.get('created_by'),
            'created_at': doc.get('created_at') or now
        }
        versions.append(current_version)
        
        # Update document with new version
        update_data = {
            'file_url': version_data.file_url,
            'file_name': version_data.file_name,
            'updated_at': now
        }
        
        # Update metadata
        metadata['versions'] = versions
        metadata['file_size'] = version_data.file_size
        metadata['version_history'] = metadata.get('version_history', []) + [{
            'version': len(versions),
            'timestamp': now,
            'changes': version_data.changes,
            'created_by': current_user.id
        }]
        
        update_data['metadata'] = metadata
        
        result = supabase.from_('customer_documents') \
            .update(update_data) \
            .eq('id', document_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create new version"
            )
        
        # Get user details
        created_by_name = None
        user_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.id) \
            .maybe_single() \
            .execute()
        
        if user_result.data:
            raw_meta = user_result.data.get('raw_user_meta_data', {})
            created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
        
        # Create audit log
        try:
            audit_data = {
                'user_id': current_user.id,
                'organization_id': org_id,
                'action_type': 'version_created',
                'resource_type': 'customer_document',
                'resource_id': document_id,
                'action': 'create_version',
                'description': f"Created new version of document: {version_data.file_name}",
                'new_data': {'version': len(versions), 'changes': version_data.changes},
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error creating audit log: {audit_error}")
        
        return DocumentVersionResponse(
            id=str(uuid.uuid4()),
            document_id=document_id,
            version_number=len(versions) + 1,
            file_url=version_data.file_url,
            file_name=version_data.file_name,
            file_size=version_data.file_size,
            changes=version_data.changes,
            created_by=current_user.id,
            created_by_name=created_by_name,
            created_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating document version: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create document version: {str(e)}"
        )


@router.get("/stats/detailed", response_model=DetailedStatsResponse)
async def get_detailed_document_stats(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    days: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get detailed document statistics."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.id) \
            .execute()
        
        if not orgs_result.data:
            return DetailedStatsResponse(
                overview={},
                status_trend=[],
                timeline=[],
                categories={},
                performance={},
                top_documents=[]
            )
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        # Filter by organization if specified
        if organization_id:
            if organization_id not in org_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this organization"
                )
            org_ids = [organization_id]
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get all documents
        docs_result = supabase.from_('customer_documents') \
            .select('''
                id, status, file_type, created_at, verified_at, verified_by,
                asset_id, assets(name)
            ''') \
            .in_('organization_id', org_ids) \
            .gte('created_at', cutoff.isoformat()) \
            .execute()
        
        documents = docs_result.data or []
        total = len(documents)
        
        # Overview stats
        overview = {
            'total_documents': total,
            'unique_assets': len(set(d.get('asset_id') for d in documents if d.get('asset_id'))),
            'date_range': {
                'start': cutoff.isoformat(),
                'end': datetime.utcnow().isoformat(),
                'days': days
            }
        }
        
        # Status trend (daily)
        status_trend = []
        for i in range(min(days, 30)):
            day = datetime.utcnow() - timedelta(days=i)
            day_start = datetime(day.year, day.month, day.day)
            day_end = day_start + timedelta(days=1)
            
            day_docs = [d for d in documents if d.get('created_at') and 
                       day_start <= datetime.fromisoformat(d['created_at'].replace('Z', '+00:00')) < day_end]
            
            status_trend.append({
                'date': day_start.isoformat(),
                'total': len(day_docs),
                'uploaded': sum(1 for d in day_docs if d.get('status') == 'uploaded'),
                'processing': sum(1 for d in day_docs if d.get('status') == 'processing'),
                'approved': sum(1 for d in day_docs if d.get('status') == 'approved'),
                'rejected': sum(1 for d in day_docs if d.get('status') == 'rejected')
            })
        
        status_trend.reverse()
        
        # Timeline (hourly for last 7 days)
        timeline = []
        for i in range(7):
            day = datetime.utcnow() - timedelta(days=i)
            day_start = datetime(day.year, day.month, day.day)
            day_end = day_start + timedelta(days=1)
            
            day_docs = [d for d in documents if d.get('created_at') and 
                       day_start <= datetime.fromisoformat(d['created_at'].replace('Z', '+00:00')) < day_end]
            
            timeline.append({
                'date': day_start.isoformat(),
                'count': len(day_docs),
                'statuses': {
                    'uploaded': sum(1 for d in day_docs if d.get('status') == 'uploaded'),
                    'processing': sum(1 for d in day_docs if d.get('status') == 'processing'),
                    'approved': sum(1 for d in day_docs if d.get('status') == 'approved'),
                    'rejected': sum(1 for d in day_docs if d.get('status') == 'rejected'),
                    'staff_review': sum(1 for d in day_docs if d.get('status') == 'staff_review'),
                    'ready_for_review': sum(1 for d in day_docs if d.get('status') == 'ready_for_review')
                }
            })
        
        timeline.reverse()
        
        # Categories breakdown
        categories = {
            'by_status': {},
            'by_type': {},
            'by_asset': []
        }
        
        for doc in documents:
            status = doc.get('status', 'unknown')
            categories['by_status'][status] = categories['by_status'].get(status, 0) + 1
            
            file_type = doc.get('file_type', 'unknown')
            categories['by_type'][file_type] = categories['by_type'].get(file_type, 0) + 1
        
        # By asset
        asset_counts = {}
        for doc in documents:
            asset_id = doc.get('asset_id')
            if asset_id:
                asset_name = doc.get('assets', {}).get('name', 'Unknown') if doc.get('assets') else 'Unknown'
                if asset_id not in asset_counts:
                    asset_counts[asset_id] = {
                        'asset_id': asset_id,
                        'asset_name': asset_name,
                        'count': 0,
                        'approved': 0,
                        'rejected': 0
                    }
                asset_counts[asset_id]['count'] += 1
                if doc.get('status') == 'approved':
                    asset_counts[asset_id]['approved'] += 1
                elif doc.get('status') == 'rejected':
                    asset_counts[asset_id]['rejected'] += 1
        
        categories['by_asset'] = list(asset_counts.values())
        
        # Performance metrics
        verified = sum(1 for d in documents if d.get('status') in ['approved', 'rejected'])
        approved = sum(1 for d in documents if d.get('status') == 'approved')
        rejected = sum(1 for d in documents if d.get('status') == 'rejected')
        
        # Average verification time
        verification_times = []
        for doc in documents:
            if doc.get('verified_at') and doc.get('created_at'):
                created_at = datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))
                verified_at = datetime.fromisoformat(doc['verified_at'].replace('Z', '+00:00'))
                hours = (verified_at - created_at).total_seconds() / 3600
                verification_times.append(hours)
        
        avg_verification_time = sum(verification_times) / len(verification_times) if verification_times else 0
        
        performance = {
            'verification_rate': round((verified / total * 100) if total > 0 else 0, 2),
            'approval_rate': round((approved / verified * 100) if verified > 0 else 0, 2),
            'rejection_rate': round((rejected / verified * 100) if verified > 0 else 0, 2),
            'average_verification_hours': round(avg_verification_time, 2),
            'total_verified': verified,
            'total_approved': approved,
            'total_rejected': rejected
        }
        
        # Top documents (most recent)
        top_documents = []
        for doc in documents[:10]:
            asset_name = doc.get('assets', {}).get('name', 'Unknown') if doc.get('assets') else 'Unknown'
            top_documents.append({
                'id': doc['id'],
                'file_name': doc.get('file_name', 'Unknown'),
                'status': doc.get('status', 'unknown'),
                'asset_name': asset_name,
                'created_at': doc.get('created_at')
            })
        
        return DetailedStatsResponse(
            overview=overview,
            status_trend=status_trend,
            timeline=timeline,
            categories=categories,
            performance=performance,
            top_documents=top_documents
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting detailed stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get detailed stats: {str(e)}"
        )
