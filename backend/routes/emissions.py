# backend/routes/emissions.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
from database import get_supabase_client
from auth import AuthUser, require_auth, require_org_member, require_org_admin
from supabase import Client
router = APIRouter(prefix="/api", tags=["Emissions"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class EmissionCreate(BaseModel):
    organization_id: str
    asset_id: Optional[str] = None
    defra_factor_id: Optional[str] = None
    start_date: str
    end_date: str
    raw_quantity: float
    calculated_kg_co2e: float
    metadata: Optional[Dict[str, Any]] = None

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/emissions")
async def create_emission_record(
    emission_data: EmissionCreate,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Create a new emission record.
    Used by ManualEntryStandalone to save manually entered data.
    """
    try:
        supabase = get_supabase_client()
        
        # Verify organization access
        if current_user.organization_id != emission_data.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this organization"
            )
        
        # Prepare record
        now = datetime.now().isoformat()
        
        # ✅ Fix: Build metadata properly
        metadata = {
            'created_by_email': current_user.email,
            'created_by_role': current_user.role,
            'source': 'manual_entry',
            'entry_timestamp': now
        }
        
        # Add custom metadata if provided
        if emission_data.metadata:
            metadata.update(emission_data.metadata)
        
        record = {
            'organization_id': emission_data.organization_id,
            'asset_id': emission_data.asset_id,
            'defra_factor_id': emission_data.defra_factor_id,
            'start_date': emission_data.start_date,
            'end_date': emission_data.end_date,
            'raw_quantity': emission_data.raw_quantity,
            'calculated_kg_co2e': emission_data.calculated_kg_co2e,
            'created_by_user_id': current_user.user_id,
            'created_at': now,
            'metadata': metadata
        }
        
        result = supabase.from_('emissions_logs') \
            .insert(record) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save emission record"
            )
        
        return {
            "success": True,
            "message": "Emission record saved successfully",
            "emission_id": result.data[0]['id'],
            "record": result.data[0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating emission record: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save emission record: {str(e)}"
        )
@router.get("/{org_id}/emissions")
async def get_emissions_for_organization(
    org_id: str,  # ✅ Add org_id parameter
    limit: int = Query(100, ge=1, le=10000),
    offset: int = Query(0, ge=0),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    scope: Optional[str] = Query(None, description="Scope: 1, 2, or 3"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get emissions for a specific organization.
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
        
        # Build query
        query = supabase.from_('emissions_logs') \
            .select('''
                id,
                start_date,
                end_date,
                raw_quantity,
                calculated_kg_co2e,
                metadata,
                assets (
                    id,
                    name,
                    type,
                    facility_id,
                    facilities (
                        id,
                        name
                    )
                ),
                defra_conversion_factors (
                    id,
                    activity_type,
                    co2e_multiplier,
                    reporting_year
                )
            ''') \
            .eq('organization_id', org_id)
        
        # Apply filters
        if start_date:
            query = query.gte('start_date', start_date)
        if end_date:
            query = query.lte('end_date', end_date)
        if scope:
            query = query.contains('metadata', {'scope': scope})
        if asset_id:
            query = query.eq('asset_id', asset_id)
        
        # Get count
        count_query = supabase.from_('emissions_logs') \
            .select('id', count='exact') \
            .eq('organization_id', org_id)
        
        if start_date:
            count_query = count_query.gte('start_date', start_date)
        if end_date:
            count_query = count_query.lte('end_date', end_date)
        if scope:
            count_query = count_query.contains('metadata', {'scope': scope})
        if asset_id:
            count_query = count_query.eq('asset_id', asset_id)
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # Get paginated results
        result = query.order('start_date', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Transform data
        emissions = []
        for record in result.data or []:
            asset = record.get('assets', {})
            facility = asset.get('facilities', {})
            defra = record.get('defra_conversion_factors', {})
            
            emissions.append({
                'id': record['id'],
                'start_date': record.get('start_date'),
                'end_date': record.get('end_date'),
                'raw_quantity': record.get('raw_quantity', 0),
                'calculated_kg_co2e': record.get('calculated_kg_co2e', 0),
                'tonnes_co2e': record.get('calculated_kg_co2e', 0) / 1000 if record.get('calculated_kg_co2e') else 0,
                'asset_id': asset.get('id'),
                'asset_name': asset.get('name'),
                'asset_type': asset.get('type'),
                'facility_id': facility.get('id'),
                'facility_name': facility.get('name'),
                'defra_factor_id': defra.get('id'),
                'activity_type': defra.get('activity_type'),
                'co2e_multiplier': defra.get('co2e_multiplier'),
                'reporting_year': defra.get('reporting_year'),
                'metadata': record.get('metadata', {})
            })
        
        # Calculate summary
        total_kg = sum(e['calculated_kg_co2e'] for e in emissions)
        total_tonnes = total_kg / 1000 if total_kg else 0
        
        scope_breakdown = {
            'scope1': 0,
            'scope2': 0,
            'scope3': 0
        }
        
        for e in emissions:
            scope = e.get('metadata', {}).get('scope', 'Unknown')
            if scope == 'Scope 1' or scope == '1':
                scope_breakdown['scope1'] += e['calculated_kg_co2e']
            elif scope == 'Scope 2' or scope == '2':
                scope_breakdown['scope2'] += e['calculated_kg_co2e']
            elif scope == 'Scope 3' or scope == '3':
                scope_breakdown['scope3'] += e['calculated_kg_co2e']
        
        # Convert to tonnes
        scope_breakdown = {k: v / 1000 for k, v in scope_breakdown.items()}
        
        return {
            "success": True,
            "organization_id": org_id,
            "emissions": emissions,
            "total": total,
            "limit": limit,
            "offset": offset,
            "summary": {
                "total_kg": total_kg,
                "total_tonnes": total_tonnes,
                "scope_breakdown": scope_breakdown,
                "record_count": len(emissions)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting emissions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emissions: {str(e)}"
        )

@router.delete("/emissions/{record_id}")
async def delete_emission_record(
    record_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Delete an emission record.
    """
    try:
        supabase = get_supabase_client()
        
        # Verify the record belongs to the user's organization
        record = supabase.from_('emissions_logs') \
            .select('organization_id') \
            .eq('id', record_id) \
            .maybe_single() \
            .execute()
        
        if not record.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Record not found"
            )
        
        if record.data['organization_id'] != current_user.organization_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to delete this record"
            )
        
        result = supabase.from_('emissions_logs') \
            .delete() \
            .eq('id', record_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Record deleted successfully",
            "record_id": record_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting emission record: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete emission record: {str(e)}"
        )
# Add to backend/routes/emissions.py

# ==========================================
# Emissions Update Endpoints
# ==========================================

class EmissionUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    raw_quantity: Optional[float] = None
    calculated_kg_co2e: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None

class BulkEmissionCreate(BaseModel):
    emissions: List[Dict[str, Any]]

@router.put("/emissions/{record_id}")
async def update_emission_record(
    record_id: str,
    update_data: EmissionUpdate,
    current_user: AuthUser = Depends(require_auth())
):
    """Update an existing emission record."""
    try:
        supabase = get_supabase_client()
        
        # Check if record exists and user has access
        existing = supabase.from_('emissions_logs') \
            .select('id, organization_id') \
            .eq('id', record_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Emission record not found"
            )
        
        # Check organization access
        if not current_user.is_admin:
            member = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', existing.data['organization_id']) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to update this record"
                )
        
        # Update record
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.utcnow().isoformat()
        
        result = supabase.from_('emissions_logs') \
            .update(data) \
            .eq('id', record_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Emission record updated successfully",
            "data": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update emission record: {str(e)}"
        )

@router.post("/emissions/bulk")
async def bulk_create_emissions(
    bulk_data: BulkEmissionCreate,
    current_user: AuthUser = Depends(require_auth())
):
    """Bulk create emission records."""
    try:
        supabase = get_supabase_client()
        
        results = {
            'success_count': 0,
            'failed_count': 0,
            'errors': [],
            'data': []
        }
        
        for emission in bulk_data.emissions:
            try:
                # Validate required fields
                if not emission.get('organization_id'):
                    results['failed_count'] += 1
                    results['errors'].append({
                        'error': 'organization_id is required',
                        'data': emission
                    })
                    continue
                
                # Check organization access
                if not current_user.is_admin:
                    member = supabase.from_('organization_members') \
                        .select('id') \
                        .eq('organization_id', emission['organization_id']) \
                        .eq('user_id', current_user.user_id) \
                        .maybe_single() \
                        .execute()
                    
                    if not member.data:
                        results['failed_count'] += 1
                        results['errors'].append({
                            'error': 'Not authorized for this organization',
                            'data': emission
                        })
                        continue
                
                # Add created_by
                emission['created_by_user_id'] = current_user.user_id
                emission['created_at'] = datetime.utcnow().isoformat()
                
                result = supabase.from_('emissions_logs') \
                    .insert(emission) \
                    .execute()
                
                if result.data:
                    results['success_count'] += 1
                    results['data'].append(result.data[0])
                else:
                    results['failed_count'] += 1
                    results['errors'].append({
                        'error': 'Failed to create record',
                        'data': emission
                    })
                    
            except Exception as e:
                results['failed_count'] += 1
                results['errors'].append({
                    'error': str(e),
                    'data': emission
                })
        
        return {
            "success": True,
            "message": f"Bulk creation completed: {results['success_count']} successful, {results['failed_count']} failed",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create emissions: {str(e)}"
        )

@router.get("/emissions/stats")
async def get_emission_stats(
    current_user: AuthUser = Depends(require_auth()),
    organization_id: Optional[str] = None
):
    """Get emission statistics."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('emissions_logs').select('*')
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        elif not current_user.is_admin:
            # Get user's organizations
            orgs = supabase.from_('organization_members') \
                .select('organization_id') \
                .eq('user_id', current_user.user_id) \
                .execute()
            
            if orgs.data:
                org_ids = [o['organization_id'] for o in orgs.data]
                query = query.in_('organization_id', org_ids)
        
        result = query.execute()
        
        if not result.data:
            return {
                "success": True,
                "data": {
                    "total_records": 0,
                    "total_emissions_kg_co2e": 0,
                    "by_scope": {},
                    "by_year": {}
                }
            }
        
        # Calculate stats
        total_emissions = sum(r.get('calculated_kg_co2e', 0) for r in result.data)
        
        stats = {
            'total_records': len(result.data),
            'total_emissions_kg_co2e': round(total_emissions, 2),
            'by_scope': {},
            'by_year': {}
        }
        
        # Group by year
        for record in result.data:
            if record.get('start_date'):
                year = record['start_date'].split('-')[0]
                stats['by_year'][year] = stats['by_year'].get(year, 0) + record.get('calculated_kg_co2e', 0)
        
        return {"success": True, "data": stats}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emission stats: {str(e)}"
        )

@router.get("/emissions/export")
async def export_emissions(
    current_user: AuthUser = Depends(require_auth()),
    organization_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Export emissions data as CSV."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('emissions_logs') \
            .select('*, organizations!left(name), assets!left(name, type)')
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        elif not current_user.is_admin:
            orgs = supabase.from_('organization_members') \
                .select('organization_id') \
                .eq('user_id', current_user.user_id) \
                .execute()
            
            if orgs.data:
                org_ids = [o['organization_id'] for o in orgs.data]
                query = query.in_('organization_id', org_ids)
        
        if start_date:
            query = query.gte('start_date', start_date)
        if end_date:
            query = query.lte('end_date', end_date)
        
        result = query.execute()
        
        if not result.data:
            return {
                "success": True,
                "message": "No data to export"
            }
        
        # Generate CSV
        import csv
        import io
        output = io.StringIO()
        writer = csv.writer(output)
        
        headers = ['id', 'organization_id', 'organization_name', 'asset_id', 'asset_name', 
                  'asset_type', 'start_date', 'end_date', 'raw_quantity', 'calculated_kg_co2e',
                  'created_by_user_id', 'created_at']
        writer.writerow(headers)
        
        for record in result.data:
            row = [
                record.get('id', ''),
                record.get('organization_id', ''),
                record.get('organizations', {}).get('name', '') if record.get('organizations') else '',
                record.get('asset_id', ''),
                record.get('assets', {}).get('name', '') if record.get('assets') else '',
                record.get('assets', {}).get('type', '') if record.get('assets') else '',
                record.get('start_date', ''),
                record.get('end_date', ''),
                record.get('raw_quantity', ''),
                record.get('calculated_kg_co2e', ''),
                record.get('created_by_user_id', ''),
                record.get('created_at', '')
            ]
            writer.writerow(row)
        
        from fastapi.responses import Response
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=emissions_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export emissions: {str(e)}"
        )

@router.post("/emissions/verify")
async def verify_emissions(
    record_ids: List[str],
    current_user: AuthUser = Depends(require_auth())
):
    """Verify emission records (mark as verified)."""
    try:
        supabase = get_supabase_client()
        
        results = {
            'verified': 0,
            'failed': 0,
            'errors': []
        }
        
        for record_id in record_ids:
            try:
                # Check if record exists
                existing = supabase.from_('emissions_logs') \
                    .select('id, organization_id') \
                    .eq('id', record_id) \
                    .maybe_single() \
                    .execute()
                
                if not existing.data:
                    results['failed'] += 1
                    results['errors'].append({
                        'record_id': record_id,
                        'error': 'Record not found'
                    })
                    continue
                
                # Update record
                result = supabase.from_('emissions_logs') \
                    .update({
                        'verified_at': datetime.utcnow().isoformat(),
                        'verified_by': current_user.user_id,
                        'updated_at': datetime.utcnow().isoformat()
                    }) \
                    .eq('id', record_id) \
                    .execute()
                
                if result.data:
                    results['verified'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'record_id': record_id,
                        'error': 'Failed to verify'
                    })
                    
            except Exception as e:
                results['failed'] += 1
                results['errors'].append({
                    'record_id': record_id,
                    'error': str(e)
                })
        
        return {
            "success": True,
            "message": f"Verification completed: {results['verified']} verified, {results['failed']} failed",
            "data": results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to verify emissions: {str(e)}"
        )

class EmissionsByDocumentTypeResponse(BaseModel):
    """Response model for emissions by document type."""
    document_type: str
    document_type_name: str
    total_emissions: float
    record_count: int
    average_emissions: float
    percentage_of_total: float


class VerificationHistoryResponse(BaseModel):
    """Response model for emissions verification history."""
    id: str
    record_id: str
    action_type: str
    action: str
    description: Optional[str]
    old_status: Optional[str]
    new_status: Optional[str]
    user_id: Optional[str]
    user_name: Optional[str]
    user_email: Optional[str]
    created_at: datetime
    details: Optional[Dict[str, Any]]


class BulkEmissionsAction(BaseModel):
    """Request model for bulk emissions action."""
    record_ids: List[str] = Field(..., description="List of emissions record IDs")
    notes: Optional[str] = Field(None, description="Notes for the action")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class BulkEmissionsResponse(BaseModel):
    """Response model for bulk emissions operations."""
    success: bool
    total: int
    succeeded: int
    failed: int
    results: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]


# ================================
# ENDPOINTS
# ================================

@router.get("/by-document-type", response_model=List[EmissionsByDocumentTypeResponse])
async def get_emissions_by_document_type(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get emissions breakdown by document type.
    
    Returns total emissions, record count, and average emissions for each document type.
    """
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
        
        # Build query
        query = supabase.from_('emissions_logs') \
            .select('''
                id, calculated_kg_co2e, customer_document_id,
                customer_documents!left(document_type_code, document_type_id, document_types!left(code, name))
            ''') \
            .in_('organization_id', org_ids)
        
        if start_date:
            query = query.gte('created_at', start_date.isoformat())
        if end_date:
            query = query.lte('created_at', end_date.isoformat())
        
        result = query.execute()
        emissions = result.data or []
        
        # Group by document type
        type_stats = {}
        total_all_emissions = 0
        
        for e in emissions:
            # Get document type info from customer_documents
            doc = e.get('customer_documents', {}) if e.get('customer_documents') else {}
            doc_type = doc.get('document_types', {}) if doc.get('document_types') else {}
            
            doc_type_code = doc.get('document_type_code') or doc_type.get('code') or 'unknown'
            doc_type_name = doc_type.get('name') or doc.get('document_type_code') or 'Unknown'
            
            co2e = e.get('calculated_kg_co2e', 0)
            total_all_emissions += co2e
            
            key = doc_type_code
            if key not in type_stats:
                type_stats[key] = {
                    'document_type': key,
                    'document_type_name': doc_type_name,
                    'total_emissions': 0,
                    'record_count': 0
                }
            
            type_stats[key]['total_emissions'] += co2e
            type_stats[key]['record_count'] += 1
        
        # Calculate averages and percentages
        response = []
        for doc_type, stats in type_stats.items():
            avg_emissions = stats['total_emissions'] / stats['record_count'] if stats['record_count'] > 0 else 0
            percentage = (stats['total_emissions'] / total_all_emissions * 100) if total_all_emissions > 0 else 0
            
            response.append(EmissionsByDocumentTypeResponse(
                document_type=stats['document_type'],
                document_type_name=stats['document_type_name'],
                total_emissions=round(stats['total_emissions'], 2),
                record_count=stats['record_count'],
                average_emissions=round(avg_emissions, 2),
                percentage_of_total=round(percentage, 2)
            ))
        
        # Sort by total emissions descending
        response.sort(key=lambda x: x.total_emissions, reverse=True)
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting emissions by document type: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emissions by document type: {str(e)}"
        )


@router.get("/{record_id}/verification-history", response_model=List[VerificationHistoryResponse])
async def get_emissions_verification_history(
    record_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get verification history for an emissions record.
    
    Returns audit trail of all changes and verifications for the emissions record.
    """
    try:
        # Get emissions record and verify access
        record_result = supabase.from_('emissions_logs') \
            .select('id, organization_id, asset_id, assets(organization_id)') \
            .eq('id', record_id) \
            .maybe_single() \
            .execute()
        
        if not record_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Emissions record not found"
            )
        
        record = record_result.data
        org_id = record.get('organization_id') or record.get('assets', {}).get('organization_id')
        
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
                    detail="You don't have access to this emissions record"
                )
        
        # Get audit logs for this emissions record
        result = supabase.from_('audit_logs') \
            .select('''
                id, action_type, action, description,
                old_data, new_data, changes, created_at,
                user_id, staff_id, organization_member_id
            ''') \
            .eq('resource_id', record_id) \
            .eq('resource_type', 'emissions_log') \
            .order('created_at', desc=True) \
            .execute()
        
        logs = result.data or []
        
        # Also check if there are any verification-specific logs
        verif_logs = supabase.from_('verification_activity_log') \
            .select('''
                id, user_id, action_type, action_details,
                ip_address, created_at
            ''') \
            .eq('verification_id', record_id) \
            .execute()
        
        if verif_logs.data:
            logs.extend(verif_logs.data)
        
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
            
            # Get action type
            action_type = log.get('action_type', 'unknown')
            if 'action_type' in log and 'action' in log:
                # If both exist, combine them
                pass
            
            history.append(VerificationHistoryResponse(
                id=log['id'],
                record_id=record_id,
                action_type=log.get('action_type', 'unknown'),
                action=log.get('action', 'unknown'),
                description=log.get('description'),
                old_status=old_status,
                new_status=new_status,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                created_at=log['created_at'],
                details=log.get('action_details') or log.get('changes') or log.get('new_data') or None
            ))
        
        # Sort by created_at descending
        history.sort(key=lambda x: x.created_at, reverse=True)
        
        return history
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting emissions verification history: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emissions verification history: {str(e)}"
        )


@router.post("/bulk/approve", response_model=BulkEmissionsResponse)
async def bulk_approve_emissions(
    bulk_data: BulkEmissionsAction,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Approve multiple emissions records in bulk.
    
    Updates the status of multiple emissions records to 'approved'.
    """
    try:
        now = datetime.utcnow().isoformat()
        succeeded = []
        failed = []
        
        for record_id in bulk_data.record_ids:
            try:
                # Get record and verify access
                record_result = supabase.from_('emissions_logs') \
                    .select('id, organization_id, status, asset_id, assets(organization_id)') \
                    .eq('id', record_id) \
                    .maybe_single() \
                    .execute()
                
                if not record_result.data:
                    failed.append({
                        'record_id': record_id,
                        'error': 'Emissions record not found'
                    })
                    continue
                
                record = record_result.data
                org_id = record.get('organization_id') or record.get('assets', {}).get('organization_id')
                
                if org_id:
                    member_check = supabase.from_('organization_members') \
                        .select('id') \
                        .eq('organization_id', org_id) \
                        .eq('user_id', current_user.user_id) \
                        .maybe_single() \
                        .execute()
                    
                    if not member_check.data:
                        failed.append({
                            'record_id': record_id,
                            'error': 'You don\'t have access to this record'
                        })
                        continue
                
                # Check current status
                current_status = record.get('status', 'unknown')
                if current_status in ['approved', 'rejected']:
                    failed.append({
                        'record_id': record_id,
                        'error': f'Record already {current_status}'
                    })
                    continue
                
                # Update record
                update_data = {
                    'status': 'approved',
                    'updated_at': now
                }
                
                if bulk_data.notes:
                    # Add notes to metadata
                    metadata = record.get('metadata', {})
                    metadata['approval_notes'] = bulk_data.notes
                    update_data['metadata'] = metadata
                
                if bulk_data.metadata:
                    if 'metadata' in update_data:
                        update_data['metadata'].update(bulk_data.metadata)
                    else:
                        update_data['metadata'] = bulk_data.metadata
                
                result = supabase.from_('emissions_logs') \
                    .update(update_data) \
                    .eq('id', record_id) \
                    .execute()
                
                if result.data:
                    # Create audit log
                    try:
                        audit_data = {
                            'user_id': current_user.user_id,
                            'organization_id': org_id,
                            'action_type': 'bulk_approval',
                            'resource_type': 'emissions_log',
                            'resource_id': record_id,
                            'action': 'approve',
                            'description': f"Bulk approved emissions record",
                            'old_data': {'status': current_status},
                            'new_data': {'status': 'approved'},
                            'created_at': now
                        }
                        supabase.from_('audit_logs').insert(audit_data).execute()
                    except Exception as audit_error:
                        print(f"⚠️ Error creating audit log: {audit_error}")
                    
                    succeeded.append({
                        'record_id': record_id,
                        'status': 'approved'
                    })
                else:
                    failed.append({
                        'record_id': record_id,
                        'error': 'Failed to approve record'
                    })
                    
            except Exception as e:
                failed.append({
                    'record_id': record_id,
                    'error': str(e)
                })
        
        return BulkEmissionsResponse(
            success=len(succeeded) > 0,
            total=len(bulk_data.record_ids),
            succeeded=len(succeeded),
            failed=len(failed),
            results=succeeded,
            errors=failed
        )
        
    except Exception as e:
        print(f"❌ Error in bulk approval: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to approve bulk emissions records: {str(e)}"
        )


@router.post("/bulk/reject", response_model=BulkEmissionsResponse)
async def bulk_reject_emissions(
    bulk_data: BulkEmissionsAction,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Reject multiple emissions records in bulk.
    
    Updates the status of multiple emissions records to 'rejected'.
    """
    try:
        now = datetime.utcnow().isoformat()
        succeeded = []
        failed = []
        
        for record_id in bulk_data.record_ids:
            try:
                # Get record and verify access
                record_result = supabase.from_('emissions_logs') \
                    .select('id, organization_id, status, asset_id, assets(organization_id)') \
                    .eq('id', record_id) \
                    .maybe_single() \
                    .execute()
                
                if not record_result.data:
                    failed.append({
                        'record_id': record_id,
                        'error': 'Emissions record not found'
                    })
                    continue
                
                record = record_result.data
                org_id = record.get('organization_id') or record.get('assets', {}).get('organization_id')
                
                if org_id:
                    member_check = supabase.from_('organization_members') \
                        .select('id') \
                        .eq('organization_id', org_id) \
                        .eq('user_id', current_user.user_id) \
                        .maybe_single() \
                        .execute()
                    
                    if not member_check.data:
                        failed.append({
                            'record_id': record_id,
                            'error': 'You don\'t have access to this record'
                        })
                        continue
                
                # Check current status
                current_status = record.get('status', 'unknown')
                if current_status in ['approved', 'rejected']:
                    failed.append({
                        'record_id': record_id,
                        'error': f'Record already {current_status}'
                    })
                    continue
                
                # Update record
                update_data = {
                    'status': 'rejected',
                    'updated_at': now
                }
                
                if bulk_data.notes:
                    # Add notes to metadata
                    metadata = record.get('metadata', {})
                    metadata['rejection_notes'] = bulk_data.notes
                    update_data['metadata'] = metadata
                
                if bulk_data.metadata:
                    if 'metadata' in update_data:
                        update_data['metadata'].update(bulk_data.metadata)
                    else:
                        update_data['metadata'] = bulk_data.metadata
                
                result = supabase.from_('emissions_logs') \
                    .update(update_data) \
                    .eq('id', record_id) \
                    .execute()
                
                if result.data:
                    # Create audit log
                    try:
                        audit_data = {
                            'user_id': current_user.user_id,
                            'organization_id': org_id,
                            'action_type': 'bulk_rejection',
                            'resource_type': 'emissions_log',
                            'resource_id': record_id,
                            'action': 'reject',
                            'description': f"Bulk rejected emissions record",
                            'old_data': {'status': current_status},
                            'new_data': {'status': 'rejected'},
                            'created_at': now
                        }
                        supabase.from_('audit_logs').insert(audit_data).execute()
                    except Exception as audit_error:
                        print(f"⚠️ Error creating audit log: {audit_error}")
                    
                    succeeded.append({
                        'record_id': record_id,
                        'status': 'rejected'
                    })
                else:
                    failed.append({
                        'record_id': record_id,
                        'error': 'Failed to reject record'
                    })
                    
            except Exception as e:
                failed.append({
                    'record_id': record_id,
                    'error': str(e)
                })
        
        return BulkEmissionsResponse(
            success=len(succeeded) > 0,
            total=len(bulk_data.record_ids),
            succeeded=len(succeeded),
            failed=len(failed),
            results=succeeded,
            errors=failed
        )
        
    except Exception as e:
        print(f"❌ Error in bulk rejection: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reject bulk emissions records: {str(e)}"
        )


# ================================
# ADDITIONAL HELPER ENDPOINTS
# ================================

@router.get("/stats/summary")
async def get_emissions_summary(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    period: str = Query("month", regex="^(week|month|quarter|year)$", description="Time period"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get summary statistics for emissions.
    
    Returns total emissions, average, and counts by period.
    """
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return {
                "total_emissions": 0,
                "average_emissions": 0,
                "record_count": 0,
                "period": period
            }
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        if organization_id:
            if organization_id not in org_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this organization"
                )
            org_ids = [organization_id]
        
        # Determine date range
        now = datetime.utcnow()
        if period == "week":
            start_date = now - timedelta(days=7)
        elif period == "month":
            start_date = now - timedelta(days=30)
        elif period == "quarter":
            start_date = now - timedelta(days=90)
        else:  # year
            start_date = now - timedelta(days=365)
        
        # Get emissions
        result = supabase.from_('emissions_logs') \
            .select('calculated_kg_co2e') \
            .in_('organization_id', org_ids) \
            .gte('created_at', start_date.isoformat()) \
            .execute()
        
        emissions = result.data or []
        
        if not emissions:
            return {
                "total_emissions": 0,
                "average_emissions": 0,
                "record_count": 0,
                "period": period,
                "start_date": start_date.isoformat(),
                "end_date": now.isoformat()
            }
        
        total = sum(e.get('calculated_kg_co2e', 0) for e in emissions)
        avg = total / len(emissions) if emissions else 0
        
        # Get count of unique documents with emissions
        doc_result = supabase.from_('emissions_logs') \
            .select('customer_document_id', count='exact') \
            .in_('organization_id', org_ids) \
            .not_.is_('customer_document_id', 'null') \
            .gte('created_at', start_date.isoformat()) \
            .execute()
        
        document_count = doc_result.count if hasattr(doc_result, 'count') else 0
        
        return {
            "total_emissions": round(total, 2),
            "average_emissions": round(avg, 2),
            "record_count": len(emissions),
            "document_count": document_count,
            "period": period,
            "start_date": start_date.isoformat(),
            "end_date": now.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting emissions summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emissions summary: {str(e)}"
        )


@router.get("/by-asset")
async def get_emissions_by_asset(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    limit: int = Query(10, ge=1, le=50, description="Number of assets to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get emissions breakdown by asset.
    
    Returns total emissions for each asset, sorted by highest emissions.
    """
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
        
        # Get emissions with asset info
        result = supabase.from_('emissions_logs') \
            .select('''
                asset_id,
                assets(name, type),
                calculated_kg_co2e
            ''') \
            .in_('organization_id', org_ids) \
            .not_.is_('asset_id', 'null') \
            .execute()
        
        emissions = result.data or []
        
        # Group by asset
        asset_emissions = {}
        for e in emissions:
            asset_id = e.get('asset_id')
            if asset_id:
                asset_name = e.get('assets', {}).get('name', 'Unknown') if e.get('assets') else 'Unknown'
                asset_type = e.get('assets', {}).get('type', 'unknown') if e.get('assets') else 'unknown'
                
                if asset_id not in asset_emissions:
                    asset_emissions[asset_id] = {
                        'asset_id': asset_id,
                        'asset_name': asset_name,
                        'asset_type': asset_type,
                        'total_emissions': 0,
                        'record_count': 0
                    }
                
                asset_emissions[asset_id]['total_emissions'] += e.get('calculated_kg_co2e', 0)
                asset_emissions[asset_id]['record_count'] += 1
        
        # Convert to list and sort
        results = list(asset_emissions.values())
        results.sort(key=lambda x: x['total_emissions'], reverse=True)
        
        # Limit results
        results = results[:limit]
        
        # Round emissions
        for r in results:
            r['total_emissions'] = round(r['total_emissions'], 2)
        
        return results
        
    except Exception as e:
        print(f"❌ Error getting emissions by asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emissions by asset: {str(e)}"
        )


@router.get("/verification-pending")
async def get_pending_emissions_verifications(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    limit: int = Query(50, ge=1, le=200, description="Number of records to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get emissions records pending verification.
    
    Returns emissions records with status 'pending' or 'submitted'.
    """
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
        
        result = supabase.from_('emissions_logs') \
            .select('''
                id, organization_id, asset_id, calculated_kg_co2e,
                start_date, end_date, created_at, status,
                assets(name),
                organizations(name)
            ''') \
            .in_('organization_id', org_ids) \
            .in_('status', ['pending', 'submitted', 'under_review']) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        records = result.data or []
        
        # Enrich response
        enriched = []
        for record in records:
            enriched.append({
                'id': record['id'],
                'organization_id': record.get('organization_id'),
                'organization_name': record.get('organizations', {}).get('name') if record.get('organizations') else None,
                'asset_id': record.get('asset_id'),
                'asset_name': record.get('assets', {}).get('name') if record.get('assets') else None,
                'calculated_kg_co2e': record.get('calculated_kg_co2e', 0),
                'start_date': record.get('start_date'),
                'end_date': record.get('end_date'),
                'created_at': record.get('created_at'),
                'status': record.get('status', 'pending')
            })
        
        return enriched
        
    except Exception as e:
        print(f"❌ Error getting pending emissions verifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending emissions verifications: {str(e)}"
        )
