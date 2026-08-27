# backend/routes/documents_main.py - Complete with Pagination, Sorting, Search

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel
from auth import AuthUser, require_org_member, require_role
from database import get_supabase_client

router = APIRouter(prefix="/api/documents", tags=["Documents"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class CustomerReviewRequest(BaseModel):
    action: str  # 'approve' or 'reject'
    notes: Optional[str] = None
    extraction_result: Optional[Dict[str, Any]] = None

class DocumentStatusUpdateRequest(BaseModel):
    status: str
    notes: Optional[str] = None
    assigned_to: Optional[str] = None

# ==========================================
# ✅ FIXED: ENDPOINTS WITH org_id PARAMETER
# ==========================================

@router.get("/stats/{org_id}")
async def get_document_stats(
    org_id: str,  # ✅ Add org_id parameter
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get document status counts for dashboard widget.
    """
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
        
        # Get all documents and count manually
        result = supabase.from_('organization_files') \
            .select('status') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .execute()
        
        # Initialize counts with zeros
        status_counts = {
            'uploaded': 0,
            'processing': 0,
            'staff_review': 0,
            'ready_for_review': 0,
            'approved': 0,
            'rejected': 0
        }
        
        total = 0
        if result.data:
            for item in result.data:
                status_val = item.get('status', 'uploaded')
                if status_val in status_counts:
                    status_counts[status_val] += 1
                total += 1
        
        return {
            "success": True,
            "stats": status_counts,
            "total": total,
            "pending_review": status_counts.get('ready_for_review', 0),
            "organization_id": org_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document stats: {str(e)}"
        )


@router.get("/{org_id}")
async def get_documents(
    org_id: str,  # ✅ Add org_id parameter
    status_val: Optional[str] = Query(None, alias="status", description="Filter by status"),
    search: Optional[str] = Query(None, description="Search in filename or metadata fields"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    sort_by: str = Query("uploaded_at", description="Sort field: name, file_type, size_bytes, status, uploaded_at"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get documents for the organization with filters, search, sort, and pagination.
    Now includes asset and customer_document information.
    """
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
        
        # ✅ Validate sort_by to prevent SQL injection
        allowed_sort_fields = ['name', 'file_type', 'size_bytes', 'status', 'uploaded_at']
        if sort_by not in allowed_sort_fields:
            sort_by = 'uploaded_at'
        
        # ✅ Validate sort_order
        if sort_order not in ['asc', 'desc']:
            sort_order = 'desc'
        
        # ✅ Build query with asset and customer_document info
        query = supabase.from_('organization_files') \
            .select('''
                id,
                name,
                path,
                size_bytes,
                file_type,
                mime_type,
                status,
                status_updated_at,
                uploaded_at,
                uploaded_by,
                reviewed_by,
                approved_by,
                approved_at,
                rejected_at,
                rejection_reason,
                is_active,
                metadata,
                customer_documents (
                    id,
                    asset_id,
                    file_type as customer_document_type,
                    status as customer_document_status,
                    upload_date,
                    assets (
                        id,
                        name,
                        type,
                        serial_number,
                        facility:facility_id (
                            id,
                            name
                        )
                    )
                )
            ''') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .order(sort_by, desc=(sort_order == 'desc'))
        
        # ✅ Apply filters
        if status_val:
            query = query.eq('status', status_val)
        
        # ✅ Filter by asset_id through customer_documents
        if asset_id:
            query = query.eq('customer_documents.asset_id', asset_id)
        
        # ✅ Apply search filter
        if search:
            query = query.or_(
                f"name.ilike.%{search}%,"
                f"metadata->>extraction_result->>asset_name.ilike.%{search}%,"
                f"metadata->>extraction_result->>fuel_utility_type.ilike.%{search}%,"
                f"metadata->>extraction_result->>facility.ilike.%{search}%"
            )
        
        # ✅ Get total count (separate query)
        count_query = supabase.from_('organization_files') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .eq('is_active', True)
        
        if status_val:
            count_query = count_query.eq('status', status_val)
        if search:
            count_query = count_query.or_(
                f"name.ilike.%{search}%,"
                f"metadata->>extraction_result->>asset_name.ilike.%{search}%,"
                f"metadata->>extraction_result->>fuel_utility_type.ilike.%{search}%,"
                f"metadata->>extraction_result->>facility.ilike.%{search}%"
            )
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # ✅ Get paginated results
        result = query.range(offset, offset + limit - 1).execute()
        
        # ✅ Transform documents
        documents = []
        for doc in result.data:
            customer_doc = doc.get('customer_documents', {}) or {}
            asset = customer_doc.get('assets', {}) or {}
            facility = asset.get('facility', {}) or {}
            
            documents.append({
                'id': doc['id'],
                'name': doc['name'],
                'file_type': doc.get('file_type', 'OTHER'),
                'size_bytes': doc.get('size_bytes', 0),
                'status': doc.get('status', 'uploaded'),
                'status_updated_at': doc.get('status_updated_at'),
                'uploaded_at': doc.get('uploaded_at'),
                'uploaded_by': doc.get('uploaded_by'),
                'reviewed_by': doc.get('reviewed_by'),
                'approved_by': doc.get('approved_by'),
                'approved_at': doc.get('approved_at'),
                'rejected_at': doc.get('rejected_at'),
                'rejection_reason': doc.get('rejection_reason'),
                'metadata': doc.get('metadata', {}),
                'customer_document_id': customer_doc.get('id'),
                'customer_document_status': customer_doc.get('customer_document_status'),
                'customer_document_type': customer_doc.get('customer_document_type'),
                'asset_id': customer_doc.get('asset_id'),
                'asset_name': asset.get('name'),
                'asset_type': asset.get('type'),
                'asset_serial_number': asset.get('serial_number'),
                'facility_id': facility.get('id'),
                'facility_name': facility.get('name')
            })
        
        # ✅ Get status counts for stats
        stats_result = supabase.from_('organization_files') \
            .select('status') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .execute()
        
        stats = {}
        if stats_result.data:
            for item in stats_result.data:
                status_key = item.get('status', 'uploaded')
                stats[status_key] = stats.get(status_key, 0) + 1
        
        # ✅ Calculate pagination metadata
        page = (offset // limit) + 1 if limit > 0 else 1
        total_pages = (total + limit - 1) // limit if limit > 0 else 1
        
        return {
            "success": True,
            "documents": documents,
            "total": total,
            "page": page,
            "total_pages": total_pages,
            "limit": limit,
            "offset": offset,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "stats": stats,
            "organization_id": org_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting documents: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get documents: {str(e)}"
        )


@router.get("/{org_id}/{file_id}/status")
async def get_document_status(
    org_id: str,  # ✅ Add org_id parameter
    file_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get detailed status of a single document.
    """
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
        
        # Get document
        doc_result = supabase.from_('organization_files') \
            .select('*') \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc = doc_result.data
        
        # Get document activity log (if table exists)
        activity_log = []
        try:
            activity_result = supabase.from_('document_activity_log') \
                .select('*') \
                .eq('file_id', file_id) \
                .order('created_at', desc=True) \
                .limit(50) \
                .execute()
            activity_log = activity_result.data or []
        except Exception as log_error:
            print(f"⚠️ document_activity_log table error: {log_error}")
        
        return {
            "success": True,
            "document": {
                "id": doc['id'],
                "name": doc['name'],
                "file_type": doc.get('file_type'),
                "size_bytes": doc.get('size_bytes'),
                "status": doc.get('status', 'uploaded'),
                "status_updated_at": doc.get('status_updated_at'),
                "uploaded_at": doc.get('uploaded_at'),
                "uploaded_by": doc.get('uploaded_by'),
                "reviewed_by": doc.get('reviewed_by'),
                "approved_by": doc.get('approved_by'),
                "approved_at": doc.get('approved_at'),
                "rejected_at": doc.get('rejected_at'),
                "rejection_reason": doc.get('rejection_reason'),
                "metadata": doc.get('metadata', {})
            },
            "activity_log": activity_log,
            "download_url": f"/api/organizations/files/{file_id}/download"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting document status: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document status: {str(e)}"
        )


@router.post("/{org_id}/{file_id}/review")
async def customer_review_document(
    org_id: str,  # ✅ Add org_id parameter
    file_id: str,
    review_data: CustomerReviewRequest,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Customer approves or rejects a document.
    Now integrated with customer_documents table.
    """
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
        
        # Get document with customer_document link
        doc_result = supabase.from_('organization_files') \
            .select('''
                *,
                customer_documents (
                    id,
                    asset_id,
                    status as customer_doc_status,
                    file_type,
                    upload_date
                )
            ''') \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not doc_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        doc = doc_result.data
        customer_doc = doc.get('customer_documents', {})
        current_status = doc.get('status', 'uploaded')
        
        # Allow review if status is ready_for_review or manual entry
        if current_status not in ['ready_for_review', 'uploaded', 'processing', 'staff_review']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot review document with status '{current_status}'. Please wait for processing or request manual extraction."
            )
        
        # Validate action
        if review_data.action not in ['approve', 'reject']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Action must be 'approve' or 'reject'"
            )
        
        now = datetime.now().isoformat()
        new_status = 'approved' if review_data.action == 'approve' else 'rejected'
        
        # Update document status
        update_data = {
            'status': new_status,
            'status_updated_at': now,
            'reviewed_by': current_user.user_id,
            'approved_by': current_user.user_id if review_data.action == 'approve' else None,
            'approved_at': now if review_data.action == 'approve' else None,
            'rejected_at': now if review_data.action == 'reject' else None,
            'rejection_reason': review_data.notes if review_data.action == 'reject' else None
        }
        
        supabase.from_('organization_files') \
            .update(update_data) \
            .eq('id', file_id) \
            .execute()
        
        # ✅ Update customer_documents status
        if customer_doc and customer_doc.get('id'):
            supabase.from_('customer_documents') \
                .update({
                    'status': new_status,
                    'verified_at': now,
                    'verified_by': current_user.user_id,
                    'updated_at': now
                }) \
                .eq('id', customer_doc['id']) \
                .execute()
        
        # Log customer review
        try:
            supabase.from_('customer_review_log') \
                .insert({
                    'file_id': file_id,
                    'organization_id': org_id,
                    'user_id': current_user.user_id,
                    'status': new_status,
                    'notes': review_data.notes,
                    'created_at': now
                }) \
                .execute()
        except Exception as log_error:
            print(f"⚠️ Error logging review: {log_error}")
        
        # If approved, save to emissions_logs
        emission_id = None
        if review_data.action == 'approve':
            # Get extraction data from the request
            extraction_data = review_data.extraction_result if hasattr(review_data, 'extraction_result') else {}
            
            if not extraction_data:
                # Try to get from metadata
                metadata = doc.get('metadata', {})
                extraction_data = metadata.get('extraction_result', {})
            
            if extraction_data:
                try:
                    # Get DEFRA factor
                    defra_result = supabase.from_('defra_conversion_factors') \
                        .select('id') \
                        .eq('activity_type', extraction_data.get('fuel_utility_type', 'Electricity')) \
                        .eq('reporting_year', extraction_data.get('reporting_year', datetime.now().year)) \
                        .maybe_single() \
                        .execute()
                    
                    defra_factor_id = defra_result.data.get('id') if defra_result.data else None
                    
                    # ✅ Get asset - use customer_document's asset_id if available
                    asset_id = None
                    if customer_doc and customer_doc.get('asset_id'):
                        asset_id = customer_doc['asset_id']
                    else:
                        # Fallback: try to find by name
                        asset_result = supabase.from_('assets') \
                            .select('id') \
                            .eq('name', extraction_data.get('asset_name', '')) \
                            .eq('organization_id', org_id) \
                            .maybe_single() \
                            .execute()
                        asset_id = asset_result.data.get('id') if asset_result.data else None
                    
                    # Calculate kg CO2e
                    consumption = float(extraction_data.get('consumption', 0))
                    kg_co2e = consumption * 2.68  # Default multiplier
                    
                    # Save to emissions_logs
                    emission_data = {
                        'organization_id': org_id,
                        'asset_id': asset_id,
                        'defra_factor_id': defra_factor_id,
                        'start_date': extraction_data.get('billing_start', now[:10]),
                        'end_date': extraction_data.get('billing_start', now[:10]),
                        'raw_quantity': consumption,
                        'calculated_kg_co2e': kg_co2e,
                        'created_by_user_id': current_user.user_id,
                        'file_id': file_id,
                        'metadata': {
                            'source': 'customer_approved',
                            'extraction_data': extraction_data,
                            'approved_at': now,
                            'approved_by': current_user.user_id
                        },
                        'created_at': now
                    }
                    
                    # ✅ Add customer_document_id if available
                    if customer_doc and customer_doc.get('id'):
                        emission_data['customer_document_id'] = customer_doc['id']
                    
                    emission_result = supabase.from_('emissions_logs') \
                        .insert(emission_data) \
                        .execute()
                    
                    if emission_result.data:
                        emission_id = emission_result.data[0]['id']
                except Exception as emission_error:
                    print(f"⚠️ Error saving to emissions_logs: {emission_error}")
        
        return {
            "success": True,
            "message": f"Document {new_status} successfully",
            "status": new_status,
            "emission_id": emission_id,
            "document_id": file_id,
            "customer_document_id": customer_doc.get('id') if customer_doc else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error reviewing document: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review document: {str(e)}"
        )


@router.post("/{org_id}/admin/{file_id}/status")
async def update_document_status(
    org_id: str,  # ✅ Add org_id parameter
    file_id: str,
    status_data: DocumentStatusUpdateRequest,
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Staff/Admin updates document status.
    Now integrated with customer_documents table.
    """
    try:
        supabase = get_supabase_client()
        
        # Get document with customer_document link
        doc_check = supabase.from_('organization_files') \
            .select('''
                organization_id, 
                status, 
                name, 
                file_type,
                customer_documents (
                    id,
                    status as customer_doc_status
                )
            ''') \
            .eq('id', file_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not doc_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # ✅ Verify the organization matches
        if doc_check.data['organization_id'] != org_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Document does not belong to this organization"
            )
        
        old_status = doc_check.data.get('status', 'uploaded')
        customer_doc = doc_check.data.get('customer_documents', {})
        
        # Validate status
        valid_statuses = ['uploaded', 'processing', 'staff_review', 'ready_for_review', 'approved', 'rejected']
        if status_data.status not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        now = datetime.now().isoformat()
        
        # Build update data
        update_data = {
            'status': status_data.status,
            'status_updated_at': now,
            'reviewed_by': current_user.user_id if status_data.status in ['staff_review', 'ready_for_review'] else None,
        }
        
        # Add specific timestamps
        if status_data.status == 'processing':
            update_data['processing_started_at'] = now
        elif status_data.status == 'ready_for_review':
            update_data['review_ready_at'] = now
        
        # If assigning to staff
        manual_review_id = None
        if status_data.assigned_to:
            try:
                queue_result = supabase.from_('manual_review_queue') \
                    .select('id') \
                    .eq('file_id', file_id) \
                    .maybe_single() \
                    .execute()
                
                if queue_result.data:
                    manual_review_id = queue_result.data['id']
                    supabase.from_('manual_review_queue') \
                        .update({
                            'assigned_to': status_data.assigned_to,
                            'assigned_at': now,
                            'assigned_by': current_user.user_id,
                            'status': 'assigned'
                        }) \
                        .eq('id', manual_review_id) \
                        .execute()
                else:
                    # Create new manual review queue entry
                    manual_review_data = {
                        'file_id': file_id,
                        'organization_id': org_id,
                        'file_name': doc_check.data.get('name', 'Unknown'),
                        'file_type': doc_check.data.get('file_type', 'PDF'),
                        'data_type': 'mixed',
                        'status': 'assigned',
                        'assigned_to': status_data.assigned_to,
                        'assigned_at': now,
                        'assigned_by': current_user.user_id,
                        'priority': 0,
                        'created_at': now
                    }
                    
                    # ✅ Include customer_document_id if available
                    if customer_doc and customer_doc.get('id'):
                        manual_review_data['customer_document_id'] = customer_doc['id']
                    
                    queue_result = supabase.from_('manual_review_queue') \
                        .insert(manual_review_data) \
                        .execute()
                    
                    if queue_result.data:
                        manual_review_id = queue_result.data[0]['id']
                        
                        # ✅ Link manual_review_queue to customer_document
                        if customer_doc and customer_doc.get('id'):
                            supabase.from_('customer_documents') \
                                .update({
                                    'manual_review_queue_id': manual_review_id,
                                    'updated_at': now
                                }) \
                                .eq('id', customer_doc['id']) \
                                .execute()
            except Exception as queue_error:
                print(f"⚠️ Error with manual_review_queue: {queue_error}")
        
        # Update document
        supabase.from_('organization_files') \
            .update(update_data) \
            .eq('id', file_id) \
            .execute()
        
        # ✅ Update customer_documents status
        if customer_doc and customer_doc.get('id'):
            # Map document status to customer_document status
            doc_status_map = {
                'uploaded': 'pending',
                'processing': 'processing',
                'staff_review': 'processing',
                'ready_for_review': 'extracted',
                'approved': 'approved',
                'rejected': 'rejected'
            }
            
            customer_status = doc_status_map.get(status_data.status, 'pending')
            
            update_customer_doc = {
                'status': customer_status,
                'updated_at': now
            }
            
            if manual_review_id:
                update_customer_doc['manual_review_queue_id'] = manual_review_id
            
            supabase.from_('customer_documents') \
                .update(update_customer_doc) \
                .eq('id', customer_doc['id']) \
                .execute()
        
        return {
            "success": True,
            "message": f"Document status updated to '{status_data.status}'",
            "old_status": old_status,
            "new_status": status_data.status,
            "document_id": file_id,
            "customer_document_id": customer_doc.get('id') if customer_doc else None,
            "manual_review_id": manual_review_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating document status: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update document status: {str(e)}"
        )