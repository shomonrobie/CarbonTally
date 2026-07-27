# backend/routes/organizations/analytics.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from auth import AuthUser, require_org_member
from database import get_supabase_client

router = APIRouter(prefix="/api/organizations/analytics", tags=["Organization Analytics"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class EmissionsTrendPoint(BaseModel):
    """Single data point for emissions trend."""
    period: str  # YYYY-MM or YYYY-QQ or YYYY
    kg_co2e: float
    tonnes_co2e: float
    record_count: int

class EmissionsTrendResponse(BaseModel):
    """Response for emissions trend analysis."""
    organization_id: str
    organization_name: Optional[str] = None
    period_type: str  # 'monthly', 'quarterly', 'yearly'
    data: List[EmissionsTrendPoint]
    summary: Dict[str, Any]

class ScopeComparisonResponse(BaseModel):
    """Response for scope comparison."""
    organization_id: str
    organization_name: Optional[str] = None
    scopes: Dict[str, float]  # scope_1, scope_2, scope_3 in tonnes
    percentages: Dict[str, float]
    total_tonnes: float
    year: int

class AssetPerformanceResponse(BaseModel):
    """Response for asset performance."""
    asset_id: str
    asset_name: str
    asset_type: Optional[str] = None
    facility_name: Optional[str] = None
    total_emissions_tonnes: float
    emissions_per_unit: Optional[float] = None  # emissions per capacity unit
    record_count: int
    last_record_date: Optional[datetime] = None

class AssetPerformanceListResponse(BaseModel):
    """Response for asset performance list."""
    assets: List[AssetPerformanceResponse]
    total_assets: int
    total_emissions_tonnes: float

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_quarter(date_str: str) -> str:
    """Get quarter from date string."""
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        quarter = (dt.month - 1) // 3 + 1
        return f"{dt.year}-Q{quarter}"
    except:
        return date_str[:7] if date_str else 'Unknown'

def get_month(date_str: str) -> str:
    """Get month from date string."""
    try:
        return date_str[:7] if date_str else 'Unknown'
    except:
        return 'Unknown'

async def get_organization_name(supabase_client, org_id: str) -> Optional[str]:
    """Get organization name."""
    try:
        result = supabase_client.from_('organizations') \
            .select('name') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        return result.data.get('name') if result.data else None
    except:
        return None

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/emissions-trend", response_model=EmissionsTrendResponse)
async def get_emissions_trend(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    period: str = Query("monthly", description="Period: monthly, quarterly, yearly"),
    scope: Optional[str] = Query(None, description="Filter by scope (1, 2, or 3)"),
    asset_id: Optional[str] = Query(None, description="Filter by asset ID"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get emissions trend data for the organization.
    """
    try:
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
                id,
                start_date,
                calculated_kg_co2e,
                metadata,
                assets (name)
            ''') \
            .eq('organization_id', org_id)
        
        # Apply filters
        if start_date:
            query = query.gte('start_date', start_date)
        if end_date:
            query = query.lte('start_date', end_date)
        if scope:
            query = query.contains('metadata', {'scope': scope})
        if asset_id:
            query = query.eq('asset_id', asset_id)
        
        # Execute query
        result = query.order('start_date', asc=True).execute()
        
        if not result.data:
            return EmissionsTrendResponse(
                organization_id=org_id,
                organization_name=await get_organization_name(supabase, org_id),
                period_type=period,
                data=[],
                summary={"message": "No emissions data found"}
            )
        
        # Group by period
        grouped_data = {}
        for record in result.data:
            date_str = record.get('start_date', '')
            if not date_str:
                continue
            
            if period == 'yearly':
                key = date_str[:4] if date_str else 'Unknown'
            elif period == 'quarterly':
                key = get_quarter(date_str)
            else:  # monthly
                key = get_month(date_str)
            
            if key not in grouped_data:
                grouped_data[key] = {
                    'total_kg': 0,
                    'count': 0
                }
            
            grouped_data[key]['total_kg'] += record.get('calculated_kg_co2e', 0)
            grouped_data[key]['count'] += 1
        
        # Convert to response format
        trend_data = []
        for period_key in sorted(grouped_data.keys()):
            kg_value = grouped_data[period_key]['total_kg']
            trend_data.append(EmissionsTrendPoint(
                period=period_key,
                kg_co2e=kg_value,
                tonnes_co2e=kg_value / 1000,
                record_count=grouped_data[period_key]['count']
            ))
        
        # Calculate summary
        total_kg = sum(d.kg_co2e for d in trend_data)
        
        return EmissionsTrendResponse(
            organization_id=org_id,
            organization_name=await get_organization_name(supabase, org_id),
            period_type=period,
            data=trend_data,
            summary={
                "total_kg_co2e": total_kg,
                "total_tonnes_co2e": total_kg / 1000,
                "total_records": len(result.data),
                "periods": len(trend_data)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting emissions trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emissions trend: {str(e)}"
        )

@router.get("/scope-comparison", response_model=ScopeComparisonResponse)
async def get_scope_comparison(
    year: Optional[int] = Query(None, description="Reporting year (defaults to current year)"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get scope comparison data for the organization.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Determine year
        if not year:
            year = datetime.now().year
        
        # Get emissions data
        year_start = f"{year}-01-01"
        year_end = f"{year}-12-31"
        
        result = supabase.from_('emissions_logs') \
            .select('calculated_kg_co2e, metadata') \
            .eq('organization_id', org_id) \
            .gte('start_date', year_start) \
            .lte('start_date', year_end) \
            .execute()
        
        # Initialize scope data
        scope_data = {
            'scope_1': 0,
            'scope_2': 0,
            'scope_3': 0,
            'unknown': 0
        }
        
        for record in result.data:
            scope = record.get('metadata', {}).get('scope', 'unknown')
            kg_value = record.get('calculated_kg_co2e', 0)
            
            if scope == '1':
                scope_data['scope_1'] += kg_value
            elif scope == '2':
                scope_data['scope_2'] += kg_value
            elif scope == '3':
                scope_data['scope_3'] += kg_value
            else:
                scope_data['unknown'] += kg_value
        
        # Convert to tonnes
        scope_tonnes = {
            'scope_1': scope_data['scope_1'] / 1000,
            'scope_2': scope_data['scope_2'] / 1000,
            'scope_3': scope_data['scope_3'] / 1000,
            'unknown': scope_data['unknown'] / 1000
        }
        
        total_tonnes = sum(scope_tonnes.values())
        
        # Calculate percentages
        percentages = {}
        if total_tonnes > 0:
            for key, value in scope_tonnes.items():
                percentages[key] = (value / total_tonnes) * 100
        else:
            for key in scope_tonnes:
                percentages[key] = 0
        
        return ScopeComparisonResponse(
            organization_id=org_id,
            organization_name=await get_organization_name(supabase, org_id),
            scopes=scope_tonnes,
            percentages=percentages,
            total_tonnes=total_tonnes,
            year=year
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting scope comparison: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get scope comparison: {str(e)}"
        )

@router.get("/asset-performance", response_model=AssetPerformanceListResponse)
async def get_asset_performance(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    limit: int = Query(50, ge=1, le=200),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get asset performance data for the organization.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Get all assets for the organization
        assets_query = supabase.from_('assets') \
            .select('''
                id,
                name,
                type,
                capacity,
                capacity_unit,
                facility_id,
                facilities (name)
            ''') \
            .eq('organization_id', org_id) \
            .eq('is_active', True)
        
        if asset_type:
            assets_query = assets_query.eq('type', asset_type)
        
        assets_result = assets_query.execute()
        
        if not assets_result.data:
            return AssetPerformanceListResponse(
                assets=[],
                total_assets=0,
                total_emissions_tonnes=0
            )
        
        # Get emissions for each asset
        asset_performance = []
        total_emissions = 0
        
        for asset in assets_result.data:
            facility_data = asset.get('facilities', {})
            
            # Build emissions query for this asset
            emissions_query = supabase.from_('emissions_logs') \
                .select('calculated_kg_co2e, start_date') \
                .eq('organization_id', org_id) \
                .eq('asset_id', asset['id'])
            
            if start_date:
                emissions_query = emissions_query.gte('start_date', start_date)
            if end_date:
                emissions_query = emissions_query.lte('start_date', end_date)
            
            emissions_result = emissions_query.execute()
            
            if emissions_result.data:
                total_kg = sum(r.get('calculated_kg_co2e', 0) for r in emissions_result.data)
                total_tonnes = total_kg / 1000
                total_emissions += total_tonnes
                
                # Calculate emissions per unit of capacity
                emissions_per_unit = None
                if asset.get('capacity') and asset.get('capacity') > 0:
                    emissions_per_unit = total_tonnes / asset['capacity']
                
                # Get last record date
                last_record = emissions_result.data[-1] if emissions_result.data else None
                last_date = last_record.get('start_date') if last_record else None
                
                asset_performance.append(AssetPerformanceResponse(
                    asset_id=asset['id'],
                    asset_name=asset['name'],
                    asset_type=asset.get('type'),
                    facility_name=facility_data.get('name') if facility_data else None,
                    total_emissions_tonnes=total_tonnes,
                    emissions_per_unit=emissions_per_unit,
                    record_count=len(emissions_result.data),
                    last_record_date=last_date
                ))
        
        # Sort by emissions (highest first)
        asset_performance.sort(key=lambda x: x.total_emissions_tonnes, reverse=True)
        
        # Apply limit
        if limit:
            asset_performance = asset_performance[:limit]
        
        return AssetPerformanceListResponse(
            assets=asset_performance,
            total_assets=len(asset_performance),
            total_emissions_tonnes=total_emissions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting asset performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get asset performance: {str(e)}"
        )

@router.get("/summary")
async def get_analytics_summary(
    year: Optional[int] = Query(None, description="Reporting year (defaults to current year)"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get comprehensive analytics summary for the organization.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        if not year:
            year = datetime.now().year
        
        # Get organization name
        org_name = await get_organization_name(supabase, org_id)
        
        # Get scope comparison
        scope_response = await get_scope_comparison(year, current_user)
        
        # Get emissions trend (monthly)
        trend_response = await get_emissions_trend(
            start_date=f"{year}-01-01",
            end_date=f"{year}-12-31",
            period="monthly",
            current_user=current_user
        )
        
        # Get asset performance (top 10)
        asset_response = await get_asset_performance(
            start_date=f"{year}-01-01",
            end_date=f"{year}-12-31",
            limit=10,
            current_user=current_user
        )
        
        # Get asset and facility counts
        assets_result = supabase.from_('assets') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .execute()
        
        facilities_result = supabase.from_('facilities') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .execute()
        
        return {
            "organization_id": org_id,
            "organization_name": org_name,
            "year": year,
            "scope_breakdown": scope_response.scopes,
            "scope_percentages": scope_response.percentages,
            "total_emissions_tonnes": scope_response.total_tonnes,
            "trend_data": trend_response.data,
            "top_assets": asset_response.assets,
            "summary": {
                "total_assets": assets_result.count or 0,
                "total_facilities": facilities_result.count or 0,
                "total_records": sum(d.record_count for d in trend_response.data),
                "months_with_data": len(trend_response.data)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting analytics summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics summary: {str(e)}"
        )