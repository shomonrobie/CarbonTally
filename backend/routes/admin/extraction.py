# backend/routes/admin/extraction.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from auth import AuthUser, require_role, require_permission
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/extraction", tags=["Admin - Extraction Management"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class ExtractionApprovalRequest(BaseModel):
    """Request model for approving extraction."""
    review_id: str = Field(..., description="ID of the review queue item")
    organization_id: str = Field(..., description="Organization ID")
    extraction_result: Dict[str, Any] = Field(..., description="Extraction result data")
    reporting_year: Optional[int] = Field(None, description="Override reporting year")
    approved_by_user_id: Optional[str] = Field(None, description="User ID who approved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "review_id": "550e8400-e29b-41d4-a716-446655440000",
                "organization_id": "2b7a2e09-2cc3-461e-84e6-81137eb63ab3",
                "extraction_result": {
                    "billing_start": "2024-01-01",
                    "consumption": 1000,
                    "fuel_utility_type": "Electricity",
                    "asset_name": "Main Office"
                },
                "reporting_year": 2024
            }
        }

class ManualReviewNoteRequest(BaseModel):
    """Request model for adding manual review note."""
    review_id: str = Field(..., description="ID of the review queue item")
    special_instructions: str = Field(..., min_length=1, description="Special instructions or note")
    
    class Config:
        json_schema_extra = {
            "example": {
                "review_id": "550e8400-e29b-41d4-a716-446655440000",
                "special_instructions": "Please verify the electricity consumption values"
            }
        }

class BatchApprovalRequest(BaseModel):
    """Request model for approving a PDF batch."""
    batch_id: str = Field(..., description="ID of the batch")
    data_streams: List[Dict[str, Any]] = Field(..., description="Data streams from extraction")
    review_ids: Optional[List[str]] = Field(None, description="Review IDs to mark as approved")
    
    class Config:
        json_schema_extra = {
            "example": {
                "batch_id": "550e8400-e29b-41d4-a716-446655440000",
                "data_streams": [
                    {"stream_name": "utility_1", "extracted_fields": {"consumption": 1000}}
                ],
                "review_ids": ["550e8400-e29b-41d4-a716-446655440001"]
            }
        }

class ExtractionApprovalResponse(BaseModel):
    """Response model for extraction approval."""
    success: bool
    message: str
    emission_id: Optional[str] = None
    calculated_kg_co2e: Optional[float] = None
    reporting_year: Optional[int] = None
    review_status: Optional[str] = None

# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def calculate_emissions_with_defra(
    supabase_client,
    activity_type: str,
    consumption: float,
    start_date: str,
    override_year: Optional[int] = None
) -> Dict[str, Any]:
    """
    Calculate emissions using DEFRA factors.
    This is a refactored version of your existing function.
    """
    try:
        # Auto-detect year from start_date
        try:
            detected_year = int(str(start_date).split('-')[0])
        except (ValueError, IndexError):
            detected_year = datetime.now().year
        
        # Apply override if provided
        reporting_year = override_year if override_year else detected_year
        
        # Get emission factor
        from main import get_emission_factor
        factor_data = get_emission_factor(supabase_client, activity_type, reporting_year)
        
        multiplier = factor_data['multiplier']
        calculated_kg_co2e = round(consumption * multiplier, 4)
        
        return {
            "reporting_year": factor_data['reporting_year'],
            "multiplier_used": multiplier,
            "calculated_kg_co2e": calculated_kg_co2e,
            "is_fallback": factor_data.get('is_fallback', False),
            "factor_id": factor_data.get('factor_id')
        }
        
    except Exception as e:
        print(f"❌ Error calculating emissions: {e}")
        raise

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/approve", response_model=ExtractionApprovalResponse)
async def approve_extraction(
    approval_data: ExtractionApprovalRequest,
    current_user: AuthUser = Depends(require_role(["admin", "data_approver"]))
):
    """
    Approve extraction and save to emissions logs.
    Available to admins and data approvers.
    """
    try:
        supabase = get_supabase_client()
        
        # Extract data from request
        review_id = approval_data.review_id
        organization_id = approval_data.organization_id
        extraction_result = approval_data.extraction_result
        override_year = approval_data.reporting_year
        
        # Validate required fields
        required_fields = ['billing_start', 'consumption', 'fuel_utility_type']
        for field in required_fields:
            if field not in extraction_result:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        billing_start = extraction_result.get('billing_start')
        consumption = float(extraction_result.get('consumption', 0))
        fuel_utility_type = extraction_result.get('fuel_utility_type')
        asset_name = extraction_result.get('asset_name')
        
        if consumption <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Consumption must be greater than 0"
            )
        
        # Calculate emissions
        calculation = await calculate_emissions_with_defra(
            supabase_client=supabase,
            activity_type=fuel_utility_type,
            consumption=consumption,
            start_date=billing_start,
            override_year=override_year
        )
        
        # Fetch asset_id from asset_name
        asset_id = None
        if asset_name:
            asset_result = supabase.from_('assets') \
                .select('id') \
                .eq('name', asset_name) \
                .eq('organization_id', organization_id) \
                .maybe_single() \
                .execute()
            
            if asset_result.data:
                asset_id = asset_result.data['id']
        
        # Get DEFRA factor_id
        factor_id = None
        factor_result = supabase.from_('defra_conversion_factors') \
            .select('id') \
            .eq('activity_type', fuel_utility_type) \
            .eq('reporting_year', calculation['reporting_year']) \
            .maybe_single() \
            .execute()
        
        if factor_result.data:
            factor_id = factor_result.data['id']
        
        # Insert into emissions_logs
        emission_log_data = {
            'organization_id': organization_id,
            'asset_id': asset_id,
            'defra_factor_id': factor_id,
            'start_date': billing_start,
            'end_date': billing_start,  # For simplicity, use same date
            'raw_quantity': consumption,
            'calculated_kg_co2e': calculation['calculated_kg_co2e'],
            'created_by_user_id': approval_data.approved_by_user_id or current_user.user_id,
            'metadata': {
                'fuel_type': fuel_utility_type,
                'reporting_year': calculation['reporting_year'],
                'multiplier_used': calculation['multiplier_used'],
                'source': 'manual_review' if review_id else 'auto_extraction',
                'review_id': review_id,
                'approved_by': current_user.email,
                'approved_at': datetime.now().isoformat()
            }
        }
        
        emissions_result = supabase.from_('emissions_logs') \
            .insert(emission_log_data) \
            .execute()
        
        if not emissions_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save emissions record"
            )
        
        emission_id = emissions_result.data[0]['id']
        
        # Update review queue status if review_id provided
        review_status = None
        if review_id:
            review_update = supabase.from_('manual_review_queue') \
                .update({
                    'status': 'approved',
                    'approved_at': datetime.now().isoformat(),
                    'approved_by': current_user.user_id,
                    'emission_log_id': emission_id
                }) \
                .eq('id', review_id) \
                .execute()
            
            if review_update.data:
                review_status = 'approved'
        
        return ExtractionApprovalResponse(
            success=True,
            message="Emissions record saved successfully",
            emission_id=emission_id,
            calculated_kg_co2e=calculation['calculated_kg_co2e'],
            reporting_year=calculation['reporting_year'],
            review_status=review_status
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error approving extraction: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve extraction: {str(e)}"
        )

@router.post("/manual-review-note")
async def add_manual_review_note(
    note_data: ManualReviewNoteRequest,
    current_user: AuthUser = Depends(require_role(["admin", "staff"]))
):
    """
    Add a note to a manual review item.
    Available to admins and staff.
    """
    try:
        supabase = get_supabase_client()
        
        review_id = note_data.review_id
        special_instructions = note_data.special_instructions.strip()
        
        if not review_id or not special_instructions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="review_id and special_instructions are required"
            )
        
        # Fetch current queue item to get existing notes
        current_item = supabase.from_('manual_review_queue') \
            .select('customer_notes') \
            .eq('id', review_id) \
            .maybe_single() \
            .execute()
        
        if not current_item.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review item not found"
            )
        
        existing_notes = current_item.data.get('customer_notes') or ""
        
        # Append new note with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        note_entry = f"\n[{timestamp}] {current_user.email}: {special_instructions}"
        
        if "📝 CUSTOMER NOTE:" in existing_notes:
            updated_notes = f"{existing_notes}{note_entry}"
        else:
            updated_notes = f"{existing_notes} | 📝 CUSTOMER NOTE:{note_entry}"
        
        # Update the database
        result = supabase.from_('manual_review_queue') \
            .update({
                'customer_notes': updated_notes,
                'updated_at': datetime.now().isoformat()
            }) \
            .eq('id', review_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Note added successfully",
            "review_id": review_id,
            "added_by": current_user.email,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error adding manual review note: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add note: {str(e)}"
        )

@router.post("/batch/approve")
async def approve_pdf_batch(
    batch_data: BatchApprovalRequest,
    current_user: AuthUser = Depends(require_role(["admin", "data_approver"]))
):
    """
    Approve a PDF batch and commit records.
    Available to admins and data approvers.
    """
    try:
        supabase = get_supabase_client()
        
        batch_id = batch_data.batch_id
        data_streams = batch_data.data_streams
        review_ids = batch_data.review_ids or []
        
        if not batch_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="batch_id is required"
            )
        
        if not data_streams:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data streams to approve"
            )
        
        # Validate batch exists
        batch_result = supabase.from_('upload_batches') \
            .select('organization_id, status, batch_name') \
            .eq('id', batch_id) \
            .maybe_single() \
            .execute()
        
        if not batch_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        organization_id = batch_result.data['organization_id']
        
        # Process each data stream
        approved_records = []
        errors = []
        
        for stream in data_streams:
            try:
                # Extract stream data
                stream_name = stream.get('stream_name', 'unknown')
                extracted_fields = stream.get('extracted_fields', {})
                
                # Validate required fields
                if 'consumption' not in extracted_fields:
                    errors.append(f"Stream '{stream_name}': missing consumption")
                    continue
                
                # Prepare extraction result
                extraction_result = {
                    'billing_start': extracted_fields.get('billing_start', datetime.now().strftime('%Y-%m-%d')),
                    'consumption': extracted_fields.get('consumption'),
                    'fuel_utility_type': extracted_fields.get('fuel_utility_type', 'Electricity'),
                    'asset_name': extracted_fields.get('asset_name')
                }
                
                # Approve this record
                approval_request = ExtractionApprovalRequest(
                    review_id=None,  # Not tied to a specific review
                    organization_id=organization_id,
                    extraction_result=extraction_result,
                    reporting_year=extracted_fields.get('reporting_year')
                )
                
                # Call approve_extraction
                approval_response = await approve_extraction(
                    approval_request,
                    current_user
                )
                
                approved_records.append({
                    'stream': stream_name,
                    'emission_id': approval_response.emission_id,
                    'kg_co2e': approval_response.calculated_kg_co2e
                })
                
            except Exception as stream_error:
                errors.append(f"Stream '{stream.get('stream_name', 'unknown')}': {str(stream_error)}")
                continue
        
        # Update batch status
        supabase.from_('upload_batches') \
            .update({
                'status': 'completed',
                'completed_at': datetime.now().isoformat(),
                'approved_by': current_user.user_id,
                'approved_at': datetime.now().isoformat(),
                'metadata': {
                    'approved_records': len(approved_records),
                    'errors': errors if errors else None
                }
            }) \
            .eq('id', batch_id) \
            .execute()
        
        # Update review queue items if review_ids provided
        for review_id in review_ids:
            supabase.from_('manual_review_queue') \
                .update({
                    'status': 'approved',
                    'approved_at': datetime.now().isoformat(),
                    'approved_by': current_user.user_id
                }) \
                .eq('id', review_id) \
                .execute()
        
        return {
            "success": True,
            "message": f"Batch approved successfully. {len(approved_records)} records committed.",
            "batch_id": batch_id,
            "records_committed": len(approved_records),
            "approved_records": approved_records,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error approving batch: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve batch: {str(e)}"
        )

@router.get("/reviews/pending")
async def get_pending_reviews(
    organization_id: Optional[str] = None,
    limit: int = 100,
    current_user: AuthUser = Depends(require_role(["admin", "staff", "data_approver"]))
):
    """
    Get pending manual reviews.
    Available to admins, staff, and data approvers.
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('manual_review_queue') \
            .select('''
                *,
                organizations (name),
                assets (name),
                uploaded_by (email)
            ''') \
            .eq('status', 'pending') \
            .order('priority') \
            .order('created_at')
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        result = query.limit(limit).execute()
        
        return {
            "success": True,
            "reviews": result.data,
            "total": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        print(f"❌ Error getting pending reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending reviews: {str(e)}"
        )