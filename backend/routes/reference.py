# backend/routes/reference.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
from auth import AuthUser, require_org_member
from database import get_supabase_client

router = APIRouter(prefix="/api/reference", tags=["Reference Data"])

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/fuel-types")
async def get_fuel_types(
    category: Optional[str] = Query(None, description="Filter by category: fuel, utility, scope3"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get fuel/utility types from DEFRA conversion factors.
    """
    try:
        supabase = get_supabase_client()
        
        # Get distinct activity types from DEFRA factors
        query = supabase.from_('defra_conversion_factors') \
            .select('activity_type, reporting_year') \
            .order('activity_type')
        
        if category:
            # Filter by category - can add logic based on naming patterns
            if category == 'fuel':
                query = query.ilike('activity_type', '%Diesel%').or_(
                    query.ilike('activity_type', '%Petrol%').or_(
                        query.ilike('activity_type', '%LPG%').or_(
                            query.ilike('activity_type', '%CNG%')
                        )
                    )
                )
            elif category == 'utility':
                query = query.ilike('activity_type', '%Electricity%').or_(
                    query.ilike('activity_type', '%Natural Gas%').or_(
                        query.ilike('activity_type', '%Steam%')
                    )
                )
            elif category == 'scope3':
                query = query.ilike('activity_type', '%Flight%').or_(
                    query.ilike('activity_type', '%Rail%').or_(
                        query.ilike('activity_type', '%Waste%').or_(
                            query.ilike('activity_type', '%Hotel%')
                        )
                    )
                )
        
        result = query.execute()
        
        # Get unique activity types with latest reporting year
        activity_map = {}
        for item in result.data:
            activity = item.get('activity_type')
            year = item.get('reporting_year')
            if activity not in activity_map or year > activity_map[activity]:
                activity_map[activity] = year
        
        # Sort and format
        fuel_types = [
            {
                'value': activity,
                'label': activity,
                'reporting_year': year
            }
            for activity, year in sorted(activity_map.items())
        ]
        
        return {
            "success": True,
            "fuel_types": fuel_types,
            "total": len(fuel_types)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting fuel types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fuel types: {str(e)}"
        )

@router.get("/units")
async def get_units(
    category: Optional[str] = Query(None, description="Filter by category: energy, volume, mass"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get available units from the units table.
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('units') \
            .select('*') \
            .eq('is_active', True) \
            .order('name')
        
        if category:
            query = query.eq('category', category)
        
        result = query.execute()
        
        units = []
        for item in result.data:
            units.append({
                'id': item['id'],
                'code': item['code'],
                'name': item['name'],
                'category': item['category'],
                'symbol': item.get('symbol'),
                'conversion_factor': item.get('conversion_factor', 1)
            })
        
        return {
            "success": True,
            "units": units,
            "total": len(units)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting units: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get units: {str(e)}"
        )

@router.get("/categories")
async def get_categories(
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get activity categories from activity_categories table.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('activity_categories') \
            .select('*') \
            .order('activity_type') \
            .execute()
        
        return {
            "success": True,
            "categories": result.data or [],
            "total": len(result.data or [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )

@router.get("/facilities")
async def get_facilities_list(
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get facilities for the current organization.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        result = supabase.from_('facilities') \
            .select('id, name, address_line1, city, postcode, country') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .order('name') \
            .execute()
        
        return {
            "success": True,
            "facilities": result.data or [],
            "total": len(result.data or [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting facilities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get facilities: {str(e)}"
        )

@router.get("/assets")
async def get_assets_list(
    facility_id: Optional[str] = Query(None, description="Filter by facility"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get assets for the current organization.
    """
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Get facilities for this organization
        facilities_result = supabase.from_('facilities') \
            .select('id') \
            .eq('organization_id', org_id) \
            .execute()
        
        facility_ids = [f['id'] for f in (facilities_result.data or [])]
        
        if not facility_ids:
            return {
                "success": True,
                "assets": [],
                "total": 0
            }
        
        query = supabase.from_('assets') \
            .select('id, name, type, description, facility_id') \
            .in_('facility_id', facility_ids) \
            .eq('is_active', True) \
            .order('name')
        
        if facility_id:
            query = query.eq('facility_id', facility_id)
        
        result = query.execute()
        
        return {
            "success": True,
            "assets": result.data or [],
            "total": len(result.data or [])
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting assets: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assets: {str(e)}"
        )