# backend/routes/organizations/data.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import pandas as pd
import io
from auth import AuthUser, require_org_member, require_permission
from database import get_supabase_client

router = APIRouter(prefix="/api/organizations/data", tags=["Organization Data"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class EmissionsRecord(BaseModel):
    """Emissions record model."""
    id: str
    start_date: datetime
    end_date: Optional[datetime] = None
    quantity: float
    kg_co2e: float
    tonnes_co2e: float
    activity_type: Optional[str] = None
    asset: Optional[str] = None
    metadata: Dict[str, Any] = {}

class EmissionsSummary(BaseModel):
    """Emissions summary model."""
    total_kg_co2e: float
    total_tonnes_co2e: float
    total_records: int
    by_scope: Dict[str, float] = {}
    by_month: Dict[str, float] = {}
    by_asset: Dict[str, float] = {}

class EmissionsResponse(BaseModel):
    """Emissions response model."""
    organization_id: str
    organization_name: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    records: List[EmissionsRecord]
    summary: EmissionsSummary

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def calculate_emissions_summary(records: List[Dict]) -> EmissionsSummary:
    """Calculate summary statistics from emissions records."""
    total_kg = sum(r.get('calculated_kg_co2e', 0) for r in records)
    
    # By scope
    by_scope = {}
    for record in records:
        scope = record.get('metadata', {}).get('scope', 'Unknown')
        by_scope[scope] = by_scope.get(scope, 0) + record.get('calculated_kg_co2e', 0)
    
    # By month
    by_month = {}
    for record in records:
        date_str = record.get('start_date', '')
        if date_str:
            month = date_str[:7]  # YYYY-MM
            by_month[month] = by_month.get(month, 0) + record.get('calculated_kg_co2e', 0)
    
    # By asset
    by_asset = {}
    for record in records:
        asset = record.get('assets', {}).get('name', 'Unknown')
        by_asset[asset] = by_asset.get(asset, 0) + record.get('calculated_kg_co2e', 0)
    
    return EmissionsSummary(
        total_kg_co2e=total_kg,
        total_tonnes_co2e=total_kg / 1000,
        total_records=len(records),
        by_scope=by_scope,
        by_month=by_month,
        by_asset=by_asset
    )

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/{org_id}/emissions-data", response_model=EmissionsResponse)
async def get_organization_emissions(
    org_id: str,  # ✅ Keep this parameter
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    scope: Optional[str] = Query(None, description="Scope: 1, 2, or 3"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get emissions data for the organization.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ FIX: Use org_id from path, not current_user.organization_id
        # Verify user has access to this organization
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
        
        # Get organization name
        org_result = supabase.from_('organizations') \
            .select('name') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        org_name = org_result.data.get('name') if org_result.data else None
        
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
                    name,
                    facility_id,
                    facilities (name)
                ),
                defra_conversion_factors (
                    activity_type,
                    co2e_multiplier,
                    reporting_year
                )
            ''') \
            .eq('organization_id', org_id)  # ✅ Use org_id from path
        
        # Apply filters
        if start_date:
            query = query.gte('start_date', start_date)
        if end_date:
            query = query.lte('end_date', end_date)
        if scope:
            query = query.contains('metadata', {'scope': scope})
        if asset_id:
            query = query.eq('asset_id', asset_id)
        if activity_type:
            query = query.contains('metadata', {'activity_type': activity_type})
        
        # Execute query
        result = query.order('start_date', desc=True).execute()
        
        # Transform data
        records = []
        for record in result.data:
            defra = record.get('defra_conversion_factors', {})
            asset = record.get('assets', {})
            
            records.append({
                'id': record['id'],
                'start_date': record['start_date'],
                'end_date': record.get('end_date'),
                'quantity': record.get('raw_quantity', 0),
                'kg_co2e': record.get('calculated_kg_co2e', 0),
                'tonnes_co2e': record.get('calculated_kg_co2e', 0) / 1000,
                'activity_type': defra.get('activity_type'),
                'asset': asset.get('name') if asset else None,
                'metadata': record.get('metadata', {})
            })
        
        return {
            "records": records,
            "total": len(records)
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

@router.get("/{org_id}/emissions/export-csv")
async def export_emissions_csv(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Export emissions data as CSV.
    """
    try:
        from fastapi.responses import StreamingResponse
        
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Build query
        query = supabase.from_('emissions_logs') \
            .select('''
                start_date,
                end_date,
                raw_quantity,
                calculated_kg_co2e,
                metadata,
                assets (name),
                defra_conversion_factors (activity_type, co2e_multiplier, reporting_year)
            ''') \
            .eq('organization_id', org_id)
        
        if start_date:
            query = query.gte('start_date', start_date)
        if end_date:
            query = query.lte('end_date', end_date)
        
        result = query.order('start_date', desc=True).execute()
        
        # Transform to CSV
        data = []
        for record in result.data:
            data.append({
                'Date': record.get('start_date', ''),
                'Quantity': record.get('raw_quantity', 0),
                'Unit': record.get('metadata', {}).get('unit', ''),
                'Activity Type': record.get('defra_conversion_factors', {}).get('activity_type', ''),
                'Asset': record.get('assets', {}).get('name', ''),
                'kg CO2e': record.get('calculated_kg_co2e', 0),
                'Tonnes CO2e': record.get('calculated_kg_co2e', 0) / 1000,
                'Scope': record.get('metadata', {}).get('scope', ''),
                'Reporting Year': record.get('defra_conversion_factors', {}).get('reporting_year', ''),
                'Multiplier': record.get('defra_conversion_factors', {}).get('co2e_multiplier', 0)
            })
        
        # Create DataFrame and CSV
        df = pd.DataFrame(data)
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)
        
        # Generate filename
        filename = f"emissions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            iter([csv_buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error exporting emissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export emissions: {str(e)}"
        )

@router.get("/organizations/{org_id}/assets ")
async def get_organization_assets(
    facility_id: Optional[str] = Query(None, description="Filter by facility"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get all assets for the organization.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Get facilities
        facilities_query = supabase.from_('facilities') \
            .select('id, name, address, type') \
            .eq('organization_id', org_id)
        
        if facility_id:
            facilities_query = facilities_query.eq('id', facility_id)
        
        facilities_result = facilities_query.execute()
        facilities = facilities_result.data or []
        
        # Get assets for each facility
        assets = []
        for facility in facilities:
            assets_result = supabase.from_('assets') \
                .select('''
                    id,
                    name,
                    type,
                    description,
                    created_at,
                    metadata
                ''') \
                .eq('facility_id', facility['id']) \
                .execute()
            
            facility_assets = assets_result.data or []
            for asset in facility_assets:
                asset['facility'] = facility
                assets.append(asset)
        
        # Also get assets without facility (if any)
        assets_no_facility = supabase.from_('assets') \
            .select('''
                id,
                name,
                type,
                description,
                created_at,
                metadata
            ''') \
            .eq('organization_id', org_id) \
            .is_('facility_id', 'null') \
            .execute()
        
        for asset in assets_no_facility.data or []:
            asset['facility'] = None
            assets.append(asset)
        
        return {
            "organization_id": org_id,
            "facilities": facilities,
            "assets": assets,
            "total": len(assets)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assets: {str(e)}"
        )

@router.get("/{org_id}/defra-factors")
async def get_organization_defra_factors(  # ✅ Renamed
    org_id: str,
    reporting_year: Optional[int] = Query(None, description="Reporting year"),
    activity_type: Optional[str] = Query(None, description="Filter by activity type"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get available DEFRA factors for the organization.
    """
    try:
        supabase = get_supabase_client()
        
        # Verify organization access
        if not current_user.is_admin:
            member = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', org_id) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized for this organization"
                )
        
        query = supabase.from_('defra_conversion_factors') \
            .select('id, activity_type, co2e_multiplier, reporting_year')
        
        if reporting_year:
            query = query.eq('reporting_year', reporting_year)
        if activity_type:
            query = query.ilike('activity_type', f'%{activity_type}%')
        
        result = query.order('reporting_year', desc=True).order('activity_type').execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data) if result.data else 0
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting organization DEFRA factors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DEFRA factors: {str(e)}"
        )
