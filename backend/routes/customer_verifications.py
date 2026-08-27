# backend/routes/customer_verifications.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta
from supabase import Client
import uuid

from auth import AuthUser, require_org_member
from database import get_supabase_client

router = APIRouter(prefix="/api/customer/verifications", tags=["Customer Verifications"])


# ================================
# PYDANTIC MODELS
# ================================

class VerificationStatus(str):
    """Verification status constants."""
    PENDING = 'pending'
    SUBMITTED = 'submitted'
    UNDER_REVIEW = 'under_review'
    VERIFIED = 'verified'
    REJECTED = 'rejected'
    REVISION_REQUESTED = 'revision_requested'
    ESCALATED = 'escalated'


class VerificationCreate(BaseModel):
    """Request model for submitting a verification."""
    customer_document_id: str = Field(..., description="ID of the document to verify")
    notes: Optional[str] = Field(None, description="Additional notes")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class VerificationUpdateRequest(BaseModel):
    """Request model for verification actions."""
    notes: Optional[str] = Field(None, description="Notes for the action")
    reason: Optional[str] = Field(None, description="Reason for rejection or revision")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class VerificationResponse(BaseModel):
    """Response model for a verification."""
    id: str
    customer_document_id: Optional[str]
    organization_id: Optional[str]
    customer_member_id: Optional[str]
    status: str
    notes: Optional[str]
    submitted_at: Optional[datetime]
    submitted_by: Optional[str]
    verified_at: Optional[datetime]
    verified_by: Optional[str]
    rejected_at: Optional[datetime]
    rejected_by: Optional[str]
    rejected_reason: Optional[str]
    revision_requested_at: Optional[datetime]
    revision_requested_by: Optional[str]
    revision_notes: Optional[str]
    is_escalated: Optional[bool]
    escalation_reason: Optional[str]
    escalated_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    # Enriched fields
    document_name: Optional[str]
    document_url: Optional[str]
    submitter_name: Optional[str]
    submitter_email: Optional[str]
    verifier_name: Optional[str]
    verifier_email: Optional[str]


class VerificationsListResponse(BaseModel):
    """Response model for verifications list."""
    verifications: List[VerificationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class VerificationActionResponse(BaseModel):
    """Response model for verification actions."""
    success: bool
    message: str
    verification_id: str
    new_status: str
    actioned_by: str
    actioned_at: datetime


# ================================
# ENDPOINTS
# ================================

@router.get("/", response_model=VerificationsListResponse)
async def list_verifications(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    status: Optional[str] = Query(None, description="Filter by status"),
    document_id: Optional[str] = Query(None, description="Filter by document ID"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    supabase: Client = Depends(get_supabase_client)
):
    """List verifications for the current user's organizations."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return VerificationsListResponse(
                verifications=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0
            )
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        # Build query
        query = supabase.from_('customer_verifications') \
            .select('''
                id, customer_document_id, organization_id, customer_member_id,
                status, notes, submitted_at, submitted_by, verified_at,
                verified_by, rejected_at, rejected_by, rejected_reason,
                revision_requested_at, revision_requested_by, revision_notes,
                is_escalated, escalation_reason, escalated_at, metadata,
                created_at, updated_at
            ''')
        
        # Apply filters
        if organization_id:
            if organization_id not in org_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this organization"
                )
            query = query.eq('organization_id', organization_id)
        else:
            query = query.in_('organization_id', org_ids)
        
        if status:
            query = query.eq('status', status)
        
        if document_id:
            query = query.eq('customer_document_id', document_id)
        
        if start_date:
            query = query.gte('created_at', start_date.isoformat())
        
        if end_date:
            query = query.lte('created_at', end_date.isoformat())
        
        # Get total count
        count_query = supabase.from_('customer_verifications') \
            .select('id', count='exact')
        
        if organization_id:
            count_query = count_query.eq('organization_id', organization_id)
        else:
            count_query = count_query.in_('organization_id', org_ids)
        
        if status:
            count_query = count_query.eq('status', status)
        if document_id:
            count_query = count_query.eq('customer_document_id', document_id)
        if start_date:
            count_query = count_query.gte('created_at', start_date.isoformat())
        if end_date:
            count_query = count_query.lte('created_at', end_date.isoformat())
        
        count_result = count_query.execute()
        total = count_result.count if hasattr(count_result, 'count') else 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        result = query.order('created_at', desc=True) \
            .range(offset, offset + page_size - 1) \
            .execute()
        
        verifications = result.data or []
        
        # Enrich verifications with additional data
        enriched = []
        for verif in verifications:
            # Get document details
            document_name = None
            document_url = None
            if verif.get('customer_document_id'):
                doc_result = supabase.from_('customer_documents') \
                    .select('file_name, file_url') \
                    .eq('id', verif['customer_document_id']) \
                    .maybe_single() \
                    .execute()
                
                if doc_result.data:
                    document_name = doc_result.data.get('file_name')
                    document_url = doc_result.data.get('file_url')
            
            # Get submitter details
            submitter_name = None
            submitter_email = None
            if verif.get('submitted_by'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', verif['submitted_by']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    submitter_email = user_result.data.get('email')
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    submitter_name = raw_meta.get('full_name') or raw_meta.get('name') or submitter_email
            
            # Get verifier details
            verifier_name = None
            verifier_email = None
            if verif.get('verified_by'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', verif['verified_by']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    verifier_email = user_result.data.get('email')
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    verifier_name = raw_meta.get('full_name') or raw_meta.get('name') or verifier_email
            
            enriched.append(VerificationResponse(
                id=verif['id'],
                customer_document_id=verif.get('customer_document_id'),
                organization_id=verif.get('organization_id'),
                customer_member_id=verif.get('customer_member_id'),
                status=verif['status'],
                notes=verif.get('notes'),
                submitted_at=verif.get('submitted_at'),
                submitted_by=verif.get('submitted_by'),
                verified_at=verif.get('verified_at'),
                verified_by=verif.get('verified_by'),
                rejected_at=verif.get('rejected_at'),
                rejected_by=verif.get('rejected_by'),
                rejected_reason=verif.get('rejected_reason'),
                revision_requested_at=verif.get('revision_requested_at'),
                revision_requested_by=verif.get('revision_requested_by'),
                revision_notes=verif.get('revision_notes'),
                is_escalated=verif.get('is_escalated', False),
                escalation_reason=verif.get('escalation_reason'),
                escalated_at=verif.get('escalated_at'),
                metadata=verif.get('metadata'),
                created_at=verif['created_at'],
                updated_at=verif['updated_at'],
                document_name=document_name,
                document_url=document_url,
                submitter_name=submitter_name,
                submitter_email=submitter_email,
                verifier_name=verifier_name,
                verifier_email=verifier_email
            ))
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return VerificationsListResponse(
            verifications=enriched,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error listing verifications: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list verifications: {str(e)}"
        )


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification_detail(
    verification_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get verification details by ID."""
    try:
        # Get verification
        result = supabase.from_('customer_verifications') \
            .select('''
                id, customer_document_id, organization_id, customer_member_id,
                status, notes, submitted_at, submitted_by, verified_at,
                verified_by, rejected_at, rejected_by, rejected_reason,
                revision_requested_at, revision_requested_by, revision_notes,
                is_escalated, escalation_reason, escalated_at, metadata,
                created_at, updated_at
            ''') \
            .eq('id', verification_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification not found"
            )
        
        verif = result.data
        
        # Verify user has access
        org_id = verif.get('organization_id')
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this verification"
                )
        
        # Get document details
        document_name = None
        document_url = None
        if verif.get('customer_document_id'):
            doc_result = supabase.from_('customer_documents') \
                .select('file_name, file_url') \
                .eq('id', verif['customer_document_id']) \
                .maybe_single() \
                .execute()
            
            if doc_result.data:
                document_name = doc_result.data.get('file_name')
                document_url = doc_result.data.get('file_url')
        
        # Get submitter details
        submitter_name = None
        submitter_email = None
        if verif.get('submitted_by'):
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', verif['submitted_by']) \
                .maybe_single() \
                .execute()
            
            if user_result.data:
                submitter_email = user_result.data.get('email')
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                submitter_name = raw_meta.get('full_name') or raw_meta.get('name') or submitter_email
        
        # Get verifier details
        verifier_name = None
        verifier_email = None
        if verif.get('verified_by'):
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', verif['verified_by']) \
                .maybe_single() \
                .execute()
            
            if user_result.data:
                verifier_email = user_result.data.get('email')
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                verifier_name = raw_meta.get('full_name') or raw_meta.get('name') or verifier_email
        
        return VerificationResponse(
            id=verif['id'],
            customer_document_id=verif.get('customer_document_id'),
            organization_id=verif.get('organization_id'),
            customer_member_id=verif.get('customer_member_id'),
            status=verif['status'],
            notes=verif.get('notes'),
            submitted_at=verif.get('submitted_at'),
            submitted_by=verif.get('submitted_by'),
            verified_at=verif.get('verified_at'),
            verified_by=verif.get('verified_by'),
            rejected_at=verif.get('rejected_at'),
            rejected_by=verif.get('rejected_by'),
            rejected_reason=verif.get('rejected_reason'),
            revision_requested_at=verif.get('revision_requested_at'),
            revision_requested_by=verif.get('revision_requested_by'),
            revision_notes=verif.get('revision_notes'),
            is_escalated=verif.get('is_escalated', False),
            escalation_reason=verif.get('escalation_reason'),
            escalated_at=verif.get('escalated_at'),
            metadata=verif.get('metadata'),
            created_at=verif['created_at'],
            updated_at=verif['updated_at'],
            document_name=document_name,
            document_url=document_url,
            submitter_name=submitter_name,
            submitter_email=submitter_email,
            verifier_name=verifier_name,
            verifier_email=verifier_email
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting verification detail: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get verification detail: {str(e)}"
        )


@router.post("/", response_model=VerificationResponse)
async def submit_verification(
    verification_data: VerificationCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Submit a new verification request."""
    try:
        # Get the document
        doc_result = supabase.from_('customer_documents') \
            .select('id, organization_id, asset_id, status, assets(organization_id)') \
            .eq('id', verification_data.customer_document_id) \
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
            .eq('user_id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if not member_check.data:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't belong to this organization"
            )
        
        # Check if verification already exists
        existing = supabase.from_('customer_verifications') \
            .select('id, status') \
            .eq('customer_document_id', verification_data.customer_document_id) \
            .in_('status', ['submitted', 'under_review', 'pending']) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Verification already exists with status: {existing.data['status']}"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Create verification
        verif_data = {
            'customer_document_id': verification_data.customer_document_id,
            'organization_id': org_id,
            'customer_member_id': member_check.data['id'],
            'status': 'submitted',
            'notes': verification_data.notes,
            'submitted_at': now,
            'submitted_by': current_user.user_id,
            'metadata': verification_data.metadata or {},
            'created_at': now,
            'updated_at': now
        }
        
        result = supabase.from_('customer_verifications') \
            .insert(verif_data) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to submit verification"
            )
        
        # Update document status
        supabase.from_('customer_documents') \
            .update({
                'status': 'ready_for_review',
                'updated_at': now
            }) \
            .eq('id', verification_data.customer_document_id) \
            .execute()
        
        # Create audit log
        try:
            audit_data = {
                'user_id': current_user.user_id,
                'organization_id': org_id,
                'action_type': 'verification_submission',
                'resource_type': 'customer_verification',
                'resource_id': result.data[0]['id'],
                'action': 'submit',
                'description': f"Submitted verification for document: {doc.get('id')}",
                'new_data': {'status': 'submitted'},
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error creating audit log: {audit_error}")
        
        # Get the full verification
        return await get_verification_detail(result.data[0]['id'], current_user, supabase)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error submitting verification: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit verification: {str(e)}"
        )


@router.put("/{verification_id}/approve", response_model=VerificationActionResponse)
async def approve_verification(
    verification_id: str,
    update_data: VerificationUpdateRequest,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Approve a verification."""
    try:
        # Get verification
        verif_result = supabase.from_('customer_verifications') \
            .select('''
                id, status, customer_document_id, organization_id,
                customer_member_id
            ''') \
            .eq('id', verification_id) \
            .maybe_single() \
            .execute()
        
        if not verif_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification not found"
            )
        
        verif = verif_result.data
        
        # Verify user has access
        org_id = verif.get('organization_id')
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this verification"
                )
        
        # Check if already approved
        if verif['status'] == 'verified':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification is already approved"
            )
        
        if verif['status'] == 'rejected':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot approve a rejected verification"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Update verification
        update_data_dict = {
            'status': 'verified',
            'verified_at': now,
            'verified_by': current_user.user_id,
            'updated_at': now
        }
        
        if update_data.notes:
            update_data_dict['notes'] = update_data.notes
        
        if update_data.metadata:
            update_data_dict['metadata'] = update_data.metadata
        
        result = supabase.from_('customer_verifications') \
            .update(update_data_dict) \
            .eq('id', verification_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to approve verification"
            )
        
        # Update document status
        if verif.get('customer_document_id'):
            supabase.from_('customer_documents') \
                .update({
                    'status': 'approved',
                    'verified_at': now,
                    'verified_by': current_user.user_id,
                    'updated_at': now
                }) \
                .eq('id', verif['customer_document_id']) \
                .execute()
        
        # Create audit log
        try:
            audit_data = {
                'user_id': current_user.user_id,
                'organization_id': org_id,
                'action_type': 'verification_approval',
                'resource_type': 'customer_verification',
                'resource_id': verification_id,
                'action': 'approve',
                'description': f"Approved verification {verification_id}",
                'old_data': {'status': verif['status']},
                'new_data': {'status': 'verified'},
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error creating audit log: {audit_error}")
        
        return VerificationActionResponse(
            success=True,
            message="Verification approved successfully",
            verification_id=verification_id,
            new_status='verified',
            actioned_by=current_user.user_id,
            actioned_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error approving verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve verification: {str(e)}"
        )


@router.put("/{verification_id}/reject", response_model=VerificationActionResponse)
async def reject_verification(
    verification_id: str,
    update_data: VerificationUpdateRequest,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Reject a verification."""
    try:
        # Get verification
        verif_result = supabase.from_('customer_verifications') \
            .select('''
                id, status, customer_document_id, organization_id,
                customer_member_id
            ''') \
            .eq('id', verification_id) \
            .maybe_single() \
            .execute()
        
        if not verif_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification not found"
            )
        
        verif = verif_result.data
        
        # Verify user has access
        org_id = verif.get('organization_id')
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this verification"
                )
        
        # Check if already rejected
        if verif['status'] == 'rejected':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification is already rejected"
            )
        
        if verif['status'] == 'verified':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot reject an approved verification"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Update verification
        update_data_dict = {
            'status': 'rejected',
            'rejected_at': now,
            'rejected_by': current_user.user_id,
            'rejected_reason': update_data.reason or update_data.notes or "No reason provided",
            'updated_at': now
        }
        
        if update_data.notes:
            update_data_dict['notes'] = update_data.notes
        
        if update_data.metadata:
            update_data_dict['metadata'] = update_data.metadata
        
        result = supabase.from_('customer_verifications') \
            .update(update_data_dict) \
            .eq('id', verification_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to reject verification"
            )
        
        # Update document status
        if verif.get('customer_document_id'):
            supabase.from_('customer_documents') \
                .update({
                    'status': 'rejected',
                    'updated_at': now
                }) \
                .eq('id', verif['customer_document_id']) \
                .execute()
        
        # Create audit log
        try:
            audit_data = {
                'user_id': current_user.user_id,
                'organization_id': org_id,
                'action_type': 'verification_rejection',
                'resource_type': 'customer_verification',
                'resource_id': verification_id,
                'action': 'reject',
                'description': f"Rejected verification {verification_id}",
                'old_data': {'status': verif['status']},
                'new_data': {'status': 'rejected', 'reason': update_data.reason},
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error creating audit log: {audit_error}")
        
        return VerificationActionResponse(
            success=True,
            message="Verification rejected successfully",
            verification_id=verification_id,
            new_status='rejected',
            actioned_by=current_user.user_id,
            actioned_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error rejecting verification: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject verification: {str(e)}"
        )


@router.put("/{verification_id}/revision", response_model=VerificationActionResponse)
async def request_revision(
    verification_id: str,
    update_data: VerificationUpdateRequest,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Request revision for a verification."""
    try:
        # Get verification
        verif_result = supabase.from_('customer_verifications') \
            .select('''
                id, status, customer_document_id, organization_id,
                customer_member_id
            ''') \
            .eq('id', verification_id) \
            .maybe_single() \
            .execute()
        
        if not verif_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification not found"
            )
        
        verif = verif_result.data
        
        # Verify user has access
        org_id = verif.get('organization_id')
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this verification"
                )
        
        # Check if already in revision
        if verif['status'] == 'revision_requested':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Revision has already been requested"
            )
        
        if verif['status'] == 'verified':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot request revision for an approved verification"
            )
        
        if verif['status'] == 'rejected':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot request revision for a rejected verification"
            )
        
        now = datetime.utcnow().isoformat()
        
        # Update verification
        update_data_dict = {
            'status': 'revision_requested',
            'revision_requested_at': now,
            'revision_requested_by': current_user.user_id,
            'revision_notes': update_data.reason or update_data.notes or "Revision requested",
            'updated_at': now
        }
        
        if update_data.notes:
            update_data_dict['notes'] = update_data.notes
        
        if update_data.metadata:
            update_data_dict['metadata'] = update_data.metadata
        
        result = supabase.from_('customer_verifications') \
            .update(update_data_dict) \
            .eq('id', verification_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to request revision"
            )
        
        # Update document status
        if verif.get('customer_document_id'):
            supabase.from_('customer_documents') \
                .update({
                    'status': 'processing',
                    'updated_at': now
                }) \
                .eq('id', verif['customer_document_id']) \
                .execute()
        
        # Create audit log
        try:
            audit_data = {
                'user_id': current_user.user_id,
                'organization_id': org_id,
                'action_type': 'verification_revision',
                'resource_type': 'customer_verification',
                'resource_id': verification_id,
                'action': 'request_revision',
                'description': f"Requested revision for verification {verification_id}",
                'old_data': {'status': verif['status']},
                'new_data': {'status': 'revision_requested', 'notes': update_data.reason},
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error creating audit log: {audit_error}")
        
        return VerificationActionResponse(
            success=True,
            message="Revision requested successfully",
            verification_id=verification_id,
            new_status='revision_requested',
            actioned_by=current_user.user_id,
            actioned_at=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error requesting revision: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to request revision: {str(e)}"
        )


# ================================
# ADDITIONAL HELPER ENDPOINTS
# ================================

@router.get("/statuses")
async def get_verification_statuses(
    current_user: AuthUser = Depends(require_org_member())
):
    """Get list of possible verification statuses."""
    return {
        "statuses": [
            {"value": "pending", "label": "Pending"},
            {"value": "submitted", "label": "Submitted"},
            {"value": "under_review", "label": "Under Review"},
            {"value": "verified", "label": "Verified"},
            {"value": "rejected", "label": "Rejected"},
            {"value": "revision_requested", "label": "Revision Requested"},
            {"value": "escalated", "label": "Escalated"}
        ]
    }


@router.get("/stats")
async def get_verification_stats(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get verification statistics."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return {
                "total": 0,
                "by_status": {},
                "pending": 0,
                "approved": 0,
                "rejected": 0,
                "revision_requested": 0,
                "submitted_today": 0,
                "submitted_this_week": 0
            }
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        # Get all verifications
        result = supabase.from_('customer_verifications') \
            .select('status, created_at') \
            .in_('organization_id', org_ids) \
            .execute()
        
        verifications = result.data or []
        
        # Calculate stats
        total = len(verifications)
        
        by_status = {}
        for v in verifications:
            status = v.get('status', 'unknown')
            by_status[status] = by_status.get(status, 0) + 1
        
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_start = today_start - timedelta(days=now.weekday())
        
        submitted_today = sum(1 for v in verifications 
                              if v.get('created_at') and v['created_at'] >= today_start)
        submitted_this_week = sum(1 for v in verifications 
                                  if v.get('created_at') and v['created_at'] >= week_start)
        
        return {
            "total": total,
            "by_status": by_status,
            "pending": by_status.get('pending', 0) + by_status.get('submitted', 0),
            "approved": by_status.get('verified', 0),
            "rejected": by_status.get('rejected', 0),
            "revision_requested": by_status.get('revision_requested', 0),
            "submitted_today": submitted_today,
            "submitted_this_week": submitted_this_week
        }
        
    except Exception as e:
        print(f"❌ Error getting verification stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get verification stats: {str(e)}"
        )
# ================================
# ADDITIONAL PYDANTIC MODELS
# ================================

class VerificationHistoryResponse(BaseModel):
    """Response model for verification history."""
    id: str
    verification_id: str
    action_type: str
    action_details: Optional[Dict[str, Any]]
    old_status: Optional[str]
    new_status: Optional[str]
    user_id: Optional[str]
    user_name: Optional[str]
    user_email: Optional[str]
    ip_address: Optional[str]
    created_at: datetime


class BulkVerificationCreate(BaseModel):
    """Request model for bulk verification submission."""
    document_ids: List[str] = Field(..., description="List of document IDs to verify")
    notes: Optional[str] = Field(None, description="Notes for all verifications")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BulkVerificationAction(BaseModel):
    """Request model for bulk verification action."""
    verification_ids: List[str] = Field(..., description="List of verification IDs")
    notes: Optional[str] = Field(None, description="Notes for the action")
    reason: Optional[str] = Field(None, description="Reason for rejection or revision")


class BulkVerificationResponse(BaseModel):
    """Response model for bulk verification operations."""
    success: bool
    total: int
    succeeded: int
    failed: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


class VerificationTimelineResponse(BaseModel):
    """Response model for verification timeline."""
    period: str
    submitted: int
    verified: int
    rejected: int
    revision_requested: int
    escalated: int
    total: int


class DetailedVerificationStatsResponse(BaseModel):
    """Response model for detailed verification statistics."""
    overview: Dict[str, Any]
    status_breakdown: Dict[str, int]
    timeline: List[VerificationTimelineResponse]
    by_organization: List[Dict[str, Any]]
    by_user: List[Dict[str, Any]]
    performance: Dict[str, Any]
    recent_activity: List[Dict[str, Any]]


# ================================
# NEW ENDPOINTS
# ================================

@router.get("/{verification_id}/history", response_model=List[VerificationHistoryResponse])
async def get_verification_history(
    verification_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get history/audit trail for a verification."""
    try:
        # Get verification and verify access
        verif_result = supabase.from_('customer_verifications') \
            .select('id, organization_id') \
            .eq('id', verification_id) \
            .maybe_single() \
            .execute()
        
        if not verif_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification not found"
            )
        
        org_id = verif_result.data.get('organization_id')
        if org_id:
            member_check = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this verification"
                )
        
        # Get history from verification_activity_log
        result = supabase.from_('verification_activity_log') \
            .select('''
                id, verification_id, user_id, action_type,
                action_details, ip_address, user_agent, created_at
            ''') \
            .eq('verification_id', verification_id) \
            .order('created_at', desc=True) \
            .execute()
        
        logs = result.data or []
        
        # Also check the verification table itself for status changes
        verif_full = supabase.from_('customer_verifications') \
            .select('''
                status, submitted_at, submitted_by, verified_at,
                verified_by, rejected_at, rejected_by, rejected_reason,
                revision_requested_at, revision_requested_by,
                created_at, updated_at
            ''') \
            .eq('id', verification_id) \
            .maybe_single() \
            .execute()
        
        # Enrich with user details
        history = []
        for log in logs:
            user_id = log.get('user_id')
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
            
            # Extract status changes from action_details
            old_status = None
            new_status = None
            if log.get('action_details') and isinstance(log.get('action_details'), dict):
                old_status = log['action_details'].get('old_status')
                new_status = log['action_details'].get('new_status')
            
            history.append(VerificationHistoryResponse(
                id=log['id'],
                verification_id=log['verification_id'],
                action_type=log.get('action_type', 'unknown'),
                action_details=log.get('action_details'),
                old_status=old_status,
                new_status=new_status,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                ip_address=log.get('ip_address'),
                created_at=log['created_at']
            ))
        
        # If no history logs, create entries from verification status changes
        if not history and verif_full.data:
            v = verif_full.data
            
            # Submitted entry
            if v.get('submitted_at'):
                user_name = None
                if v.get('submitted_by'):
                    user_result = supabase.from_('auth.users') \
                        .select('email, raw_user_meta_data') \
                        .eq('id', v['submitted_by']) \
                        .maybe_single() \
                        .execute()
                    
                    if user_result.data:
                        raw_meta = user_result.data.get('raw_user_meta_data', {})
                        user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
                
                history.append(VerificationHistoryResponse(
                    id=str(uuid.uuid4()),
                    verification_id=verification_id,
                    action_type='submission',
                    action_details={'status': 'submitted'},
                    old_status=None,
                    new_status='submitted',
                    user_id=v.get('submitted_by'),
                    user_name=user_name,
                    user_email=None,
                    ip_address=None,
                    created_at=v['submitted_at']
                ))
            
            # Verified entry
            if v.get('verified_at'):
                user_name = None
                if v.get('verified_by'):
                    user_result = supabase.from_('auth.users') \
                        .select('email, raw_user_meta_data') \
                        .eq('id', v['verified_by']) \
                        .maybe_single() \
                        .execute()
                    
                    if user_result.data:
                        raw_meta = user_result.data.get('raw_user_meta_data', {})
                        user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
                
                history.append(VerificationHistoryResponse(
                    id=str(uuid.uuid4()),
                    verification_id=verification_id,
                    action_type='verification',
                    action_details={'status': 'verified', 'notes': v.get('notes')},
                    old_status='submitted',
                    new_status='verified',
                    user_id=v.get('verified_by'),
                    user_name=user_name,
                    user_email=None,
                    ip_address=None,
                    created_at=v['verified_at']
                ))
            
            # Rejected entry
            if v.get('rejected_at'):
                user_name = None
                if v.get('rejected_by'):
                    user_result = supabase.from_('auth.users') \
                        .select('email, raw_user_meta_data') \
                        .eq('id', v['rejected_by']) \
                        .maybe_single() \
                        .execute()
                    
                    if user_result.data:
                        raw_meta = user_result.data.get('raw_user_meta_data', {})
                        user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
                
                history.append(VerificationHistoryResponse(
                    id=str(uuid.uuid4()),
                    verification_id=verification_id,
                    action_type='rejection',
                    action_details={'status': 'rejected', 'reason': v.get('rejected_reason')},
                    old_status='submitted',
                    new_status='rejected',
                    user_id=v.get('rejected_by'),
                    user_name=user_name,
                    user_email=None,
                    ip_address=None,
                    created_at=v['rejected_at']
                ))
            
            # Revision requested entry
            if v.get('revision_requested_at'):
                user_name = None
                if v.get('revision_requested_by'):
                    user_result = supabase.from_('auth.users') \
                        .select('email, raw_user_meta_data') \
                        .eq('id', v['revision_requested_by']) \
                        .maybe_single() \
                        .execute()
                    
                    if user_result.data:
                        raw_meta = user_result.data.get('raw_user_meta_data', {})
                        user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
                
                history.append(VerificationHistoryResponse(
                    id=str(uuid.uuid4()),
                    verification_id=verification_id,
                    action_type='revision_request',
                    action_details={'status': 'revision_requested', 'notes': v.get('revision_notes')},
                    old_status='submitted',
                    new_status='revision_requested',
                    user_id=v.get('revision_requested_by'),
                    user_name=user_name,
                    user_email=None,
                    ip_address=None,
                    created_at=v['revision_requested_at']
                ))
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting verification history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get verification history: {str(e)}"
        )


@router.post("/bulk", response_model=BulkVerificationResponse)
async def bulk_submit_verifications(
    bulk_data: BulkVerificationCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Submit multiple verifications in bulk."""
    try:
        now = datetime.utcnow().isoformat()
        succeeded = []
        failed = []
        
        for doc_id in bulk_data.document_ids:
            try:
                # Get document
                doc_result = supabase.from_('customer_documents') \
                    .select('id, organization_id, asset_id, status, assets(organization_id)') \
                    .eq('id', doc_id) \
                    .maybe_single() \
                    .execute()
                
                if not doc_result.data:
                    failed.append({
                        'document_id': doc_id,
                        'error': 'Document not found'
                    })
                    continue
                
                doc = doc_result.data
                org_id = doc.get('organization_id') or doc.get('assets', {}).get('organization_id')
                
                if not org_id:
                    failed.append({
                        'document_id': doc_id,
                        'error': 'Document has no associated organization'
                    })
                    continue
                
                # Verify user belongs to organization
                member_check = supabase.from_('organization_members') \
                    .select('id') \
                    .eq('organization_id', org_id) \
                    .eq('user_id', current_user.user_id) \
                    .maybe_single() \
                    .execute()
                
                if not member_check.data:
                    failed.append({
                        'document_id': doc_id,
                        'error': 'You don\'t belong to this organization'
                    })
                    continue
                
                # Check if verification already exists
                existing = supabase.from_('customer_verifications') \
                    .select('id, status') \
                    .eq('customer_document_id', doc_id) \
                    .in_('status', ['submitted', 'under_review', 'pending']) \
                    .maybe_single() \
                    .execute()
                
                if existing.data:
                    failed.append({
                        'document_id': doc_id,
                        'error': f'Verification already exists with status: {existing.data["status"]}'
                    })
                    continue
                
                # Create verification
                verif_data = {
                    'customer_document_id': doc_id,
                    'organization_id': org_id,
                    'customer_member_id': member_check.data['id'],
                    'status': 'submitted',
                    'notes': bulk_data.notes,
                    'submitted_at': now,
                    'submitted_by': current_user.user_id,
                    'metadata': bulk_data.metadata or {},
                    'created_at': now,
                    'updated_at': now
                }
                
                result = supabase.from_('customer_verifications') \
                    .insert(verif_data) \
                    .execute()
                
                if result.data:
                    # Update document status
                    supabase.from_('customer_documents') \
                        .update({
                            'status': 'ready_for_review',
                            'updated_at': now
                        }) \
                        .eq('id', doc_id) \
                        .execute()
                    
                    succeeded.append({
                        'document_id': doc_id,
                        'verification_id': result.data[0]['id'],
                        'status': 'submitted'
                    })
                else:
                    failed.append({
                        'document_id': doc_id,
                        'error': 'Failed to create verification'
                    })
                    
            except Exception as e:
                failed.append({
                    'document_id': doc_id,
                    'error': str(e)
                })
        
        return BulkVerificationResponse(
            success=len(succeeded) > 0,
            total=len(bulk_data.document_ids),
            succeeded=len(succeeded),
            failed=len(failed),
            results=succeeded,
            errors=failed
        )
        
    except Exception as e:
        print(f"❌ Error in bulk submission: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit bulk verifications: {str(e)}"
        )


@router.post("/bulk/approve", response_model=BulkVerificationResponse)
async def bulk_approve_verifications(
    bulk_data: BulkVerificationAction,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Approve multiple verifications in bulk."""
    try:
        now = datetime.utcnow().isoformat()
        succeeded = []
        failed = []
        
        for verif_id in bulk_data.verification_ids:
            try:
                # Get verification
                verif_result = supabase.from_('customer_verifications') \
                    .select('id, status, customer_document_id, organization_id') \
                    .eq('id', verif_id) \
                    .maybe_single() \
                    .execute()
                
                if not verif_result.data:
                    failed.append({
                        'verification_id': verif_id,
                        'error': 'Verification not found'
                    })
                    continue
                
                verif = verif_result.data
                org_id = verif.get('organization_id')
                
                if org_id:
                    member_check = supabase.from_('organization_members') \
                        .select('id') \
                        .eq('organization_id', org_id) \
                        .eq('user_id', current_user.user_id) \
                        .maybe_single() \
                        .execute()
                    
                    if not member_check.data:
                        failed.append({
                            'verification_id': verif_id,
                            'error': 'You don\'t have access to this verification'
                        })
                        continue
                
                if verif['status'] in ['verified', 'rejected']:
                    failed.append({
                        'verification_id': verif_id,
                        'error': f'Verification already {verif["status"]}'
                    })
                    continue
                
                # Update verification
                update_data = {
                    'status': 'verified',
                    'verified_at': now,
                    'verified_by': current_user.user_id,
                    'updated_at': now
                }
                
                if bulk_data.notes:
                    update_data['notes'] = bulk_data.notes
                
                result = supabase.from_('customer_verifications') \
                    .update(update_data) \
                    .eq('id', verif_id) \
                    .execute()
                
                if result.data:
                    # Update document status
                    if verif.get('customer_document_id'):
                        supabase.from_('customer_documents') \
                            .update({
                                'status': 'approved',
                                'verified_at': now,
                                'verified_by': current_user.user_id,
                                'updated_at': now
                            }) \
                            .eq('id', verif['customer_document_id']) \
                            .execute()
                    
                    succeeded.append({
                        'verification_id': verif_id,
                        'document_id': verif.get('customer_document_id'),
                        'status': 'verified'
                    })
                else:
                    failed.append({
                        'verification_id': verif_id,
                        'error': 'Failed to approve verification'
                    })
                    
            except Exception as e:
                failed.append({
                    'verification_id': verif_id,
                    'error': str(e)
                })
        
        return BulkVerificationResponse(
            success=len(succeeded) > 0,
            total=len(bulk_data.verification_ids),
            succeeded=len(succeeded),
            failed=len(failed),
            results=succeeded,
            errors=failed
        )
        
    except Exception as e:
        print(f"❌ Error in bulk approval: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve bulk verifications: {str(e)}"
        )


@router.get("/timeline", response_model=List[VerificationTimelineResponse])
async def get_verification_timeline(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    months: int = Query(6, ge=1, le=24, description="Number of months to include"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get verification timeline data."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return []
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        if organization_id:
            if organization_id not in org_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this organization"
                )
            org_ids = [organization_id]
        
        # Get verifications in date range
        cutoff = datetime.utcnow() - timedelta(days=months * 30)
        
        result = supabase.from_('customer_verifications') \
            .select('status, created_at, submitted_at, verified_at, rejected_at, revision_requested_at') \
            .in_('organization_id', org_ids) \
            .gte('created_at', cutoff.isoformat()) \
            .execute()
        
        verifications = result.data or []
        
        # Group by month
        timeline = {}
        for v in verifications:
            created_at = v.get('created_at') or v.get('submitted_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                month_key = created_at.strftime('%Y-%m')
                if month_key not in timeline:
                    timeline[month_key] = {
                        'period': month_key,
                        'submitted': 0,
                        'verified': 0,
                        'rejected': 0,
                        'revision_requested': 0,
                        'escalated': 0,
                        'total': 0
                    }
                
                status = v.get('status', 'unknown')
                if status == 'submitted':
                    timeline[month_key]['submitted'] += 1
                elif status == 'verified':
                    timeline[month_key]['verified'] += 1
                elif status == 'rejected':
                    timeline[month_key]['rejected'] += 1
                elif status == 'revision_requested':
                    timeline[month_key]['revision_requested'] += 1
                elif status == 'escalated':
                    timeline[month_key]['escalated'] += 1
                
                timeline[month_key]['total'] += 1
        
        # Convert to list and sort by period
        timeline_list = [VerificationTimelineResponse(**data) for data in timeline.values()]
        timeline_list.sort(key=lambda x: x.period)
        
        return timeline_list
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting verification timeline: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get verification timeline: {str(e)}"
        )


@router.get("/stats/detailed", response_model=DetailedVerificationStatsResponse)
async def get_detailed_verification_stats(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    days: int = Query(90, ge=7, le=365, description="Number of days to analyze"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get detailed verification statistics."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return DetailedVerificationStatsResponse(
                overview={},
                status_breakdown={},
                timeline=[],
                by_organization=[],
                by_user=[],
                performance={},
                recent_activity=[]
            )
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        if organization_id:
            if organization_id not in org_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this organization"
                )
            org_ids = [organization_id]
        
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get all verifications
        result = supabase.from_('customer_verifications') \
            .select('''
                id, status, submitted_at, verified_at, rejected_at,
                revision_requested_at, created_at, updated_at,
                organization_id, submitted_by, verified_by,
                customer_document_id
            ''') \
            .in_('organization_id', org_ids) \
            .gte('created_at', cutoff.isoformat()) \
            .execute()
        
        verifications = result.data or []
        total = len(verifications)
        
        # Overview
        overview = {
            'total_verifications': total,
            'unique_organizations': len(set(v.get('organization_id') for v in verifications if v.get('organization_id'))),
            'date_range': {
                'start': cutoff.isoformat(),
                'end': datetime.utcnow().isoformat(),
                'days': days
            }
        }
        
        # Status breakdown
        status_breakdown = {}
        for v in verifications:
            status = v.get('status', 'unknown')
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
        
        # Timeline (grouped by week)
        timeline_data = {}
        for v in verifications:
            created_at = v.get('created_at') or v.get('submitted_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                week_key = created_at.strftime('%Y-W%W')
                if week_key not in timeline_data:
                    timeline_data[week_key] = {
                        'period': week_key,
                        'submitted': 0,
                        'verified': 0,
                        'rejected': 0,
                        'revision_requested': 0,
                        'escalated': 0,
                        'total': 0
                    }
                
                status = v.get('status', 'unknown')
                if status == 'submitted':
                    timeline_data[week_key]['submitted'] += 1
                elif status == 'verified':
                    timeline_data[week_key]['verified'] += 1
                elif status == 'rejected':
                    timeline_data[week_key]['rejected'] += 1
                elif status == 'revision_requested':
                    timeline_data[week_key]['revision_requested'] += 1
                elif status == 'escalated':
                    timeline_data[week_key]['escalated'] += 1
                
                timeline_data[week_key]['total'] += 1
        
        timeline = [VerificationTimelineResponse(**data) for data in timeline_data.values()]
        timeline.sort(key=lambda x: x.period)
        
        # By organization
        org_stats = {}
        for v in verifications:
            org_id = v.get('organization_id')
            if org_id:
                if org_id not in org_stats:
                    org_stats[org_id] = {
                        'organization_id': org_id,
                        'organization_name': None,
                        'total': 0,
                        'verified': 0,
                        'rejected': 0,
                        'pending': 0
                    }
                
                org_stats[org_id]['total'] += 1
                status = v.get('status', 'unknown')
                if status == 'verified':
                    org_stats[org_id]['verified'] += 1
                elif status == 'rejected':
                    org_stats[org_id]['rejected'] += 1
                elif status in ['submitted', 'pending', 'under_review']:
                    org_stats[org_id]['pending'] += 1
        
        # Get organization names
        for org_id in org_stats:
            org_result = supabase.from_('organizations') \
                .select('name') \
                .eq('id', org_id) \
                .maybe_single() \
                .execute()
            
            if org_result.data:
                org_stats[org_id]['organization_name'] = org_result.data.get('name')
        
        by_organization = list(org_stats.values())
        by_organization.sort(key=lambda x: x['total'], reverse=True)
        
        # By user
        user_stats = {}
        for v in verifications:
            user_id = v.get('submitted_by')
            if user_id:
                if user_id not in user_stats:
                    user_stats[user_id] = {
                        'user_id': user_id,
                        'user_name': None,
                        'user_email': None,
                        'submitted': 0,
                        'verified': 0,
                        'rejected': 0
                    }
                
                status = v.get('status', 'unknown')
                if status == 'submitted':
                    user_stats[user_id]['submitted'] += 1
                elif status == 'verified':
                    user_stats[user_id]['verified'] += 1
                elif status == 'rejected':
                    user_stats[user_id]['rejected'] += 1
        
        # Get user names
        for user_id in user_stats:
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', user_id) \
                .maybe_single() \
                .execute()
            
            if user_result.data:
                user_stats[user_id]['user_email'] = user_result.data.get('email')
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                user_stats[user_id]['user_name'] = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
        
        by_user = list(user_stats.values())
        by_user.sort(key=lambda x: x['submitted'], reverse=True)
        
        # Performance metrics
        verified = sum(1 for v in verifications if v.get('status') == 'verified')
        rejected = sum(1 for v in verifications if v.get('status') == 'rejected')
        pending = sum(1 for v in verifications if v.get('status') in ['submitted', 'pending', 'under_review'])
        
        # Average time to verify
        verification_times = []
        for v in verifications:
            if v.get('verified_at') and v.get('submitted_at'):
                submitted_at = datetime.fromisoformat(v['submitted_at'].replace('Z', '+00:00')) if isinstance(v['submitted_at'], str) else v['submitted_at']
                verified_at = datetime.fromisoformat(v['verified_at'].replace('Z', '+00:00')) if isinstance(v['verified_at'], str) else v['verified_at']
                hours = (verified_at - submitted_at).total_seconds() / 3600
                verification_times.append(hours)
        
        avg_verification_time = sum(verification_times) / len(verification_times) if verification_times else 0
        
        performance = {
            'total_verified': verified,
            'total_rejected': rejected,
            'total_pending': pending,
            'verification_rate': round((verified / total * 100) if total > 0 else 0, 2),
            'rejection_rate': round((rejected / total * 100) if total > 0 else 0, 2),
            'average_verification_hours': round(avg_verification_time, 2),
            'verification_count': len(verification_times)
        }
        
        # Recent activity
        recent_activity = []
        for v in verifications[:10]:
            # Get document name
            doc_name = None
            if v.get('customer_document_id'):
                doc_result = supabase.from_('customer_documents') \
                    .select('file_name') \
                    .eq('id', v['customer_document_id']) \
                    .maybe_single() \
                    .execute()
                
                if doc_result.data:
                    doc_name = doc_result.data.get('file_name')
            
            recent_activity.append({
                'id': v['id'],
                'status': v.get('status'),
                'submitted_at': v.get('submitted_at'),
                'verified_at': v.get('verified_at'),
                'document_name': doc_name,
                'verification_type': v.get('status')
            })
        
        return DetailedVerificationStatsResponse(
            overview=overview,
            status_breakdown=status_breakdown,
            timeline=timeline,
            by_organization=by_organization[:10],
            by_user=by_user[:10],
            performance=performance,
            recent_activity=recent_activity
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