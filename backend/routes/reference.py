# backend/routes/reference.py
"""
Reference data endpoints for units, fuel types, and categories.
These return REFERENCE DATA (types, categories, lists), not actual records.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from auth import AuthUser, require_auth
from database import get_supabase_client

router = APIRouter(prefix="/api/reference", tags=["Reference Data"])

# ==========================================
# REFERENCE DATA - Available to all authenticated users
# ==========================================

@router.get("/units")
async def get_units(
    category: Optional[str] = Query(None, description="Filter by category"),
    current_user: AuthUser = Depends(require_auth())
):
    """
    Get all available units (reference data).
    Available to all authenticated users.
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('units').select('*')
        
        if category:
            query = query.eq('category', category)
        
        result = query.order('name').execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get units: {str(e)}"
        )

@router.get("/fuel-types")
async def get_fuel_types(
    current_user: AuthUser = Depends(require_auth())
):
    """
    Get all available fuel types (reference data).
    Available to all authenticated users.
    """
    try:
        supabase = get_supabase_client()
        
        # Get distinct fuel types from defra_conversion_factors
        result = supabase.from_('defra_conversion_factors') \
            .select('activity_type') \
            .execute()
        
        fuel_types = []
        if result.data:
            all_types = list(set([r['activity_type'] for r in result.data]))
            fuel_keywords = ['Diesel', 'Petrol', 'LPG', 'CNG', 'AdBlue', 'Fuel', 'Gasoline']
            fuel_types = [t for t in all_types if any(kw.lower() in t.lower() for kw in fuel_keywords)]
            fuel_types.sort()
        
        return {
            "success": True,
            "data": fuel_types,
            "total": len(fuel_types)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get fuel types: {str(e)}"
        )

@router.get("/categories")
async def get_reference_categories(
    current_user: AuthUser = Depends(require_auth())
):
    """
    Get all reference categories.
    Available to all authenticated users.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('activity_categories') \
            .select('*') \
            .order('activity_type') \
            .execute()
        
        categories = []
        if result.data:
            categories = list(set([r.get('esrs_e1_category', 'Other') for r in result.data if r.get('esrs_e1_category')]))
            categories.sort()
        
        return {
            "success": True,
            "data": {
                "categories": categories,
                "activity_categories": result.data,
                "total": len(result.data) if result.data else 0
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get categories: {str(e)}"
        )

@router.get("/facilities")
async def get_facilities_list(
    current_user: AuthUser = Depends(require_auth())
):
    """
    Get list of facility TYPES (reference data).
    Available to all authenticated users.
    """
    try:
        facility_types = [
            {"value": "office", "label": "Office"},
            {"value": "warehouse", "label": "Warehouse"},
            {"value": "manufacturing", "label": "Manufacturing"},
            {"value": "retail", "label": "Retail"},
            {"value": "data_center", "label": "Data Center"},
            {"value": "laboratory", "label": "Laboratory"},
            {"value": "hospitality", "label": "Hospitality"},
            {"value": "other", "label": "Other"}
        ]
        
        return {
            "success": True,
            "data": facility_types,
            "total": len(facility_types)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get facilities list: {str(e)}"
        )

@router.get("/assets")
async def get_assets_list(
    current_user: AuthUser = Depends(require_auth())
):
    """
    Get list of asset TYPES (reference data).
    Available to all authenticated users.
    Note: Actual assets are accessed via /api/organizations/{org_id}/assets
    """
    try:
        # Return a list of common asset TYPES (reference data)
        asset_types = [
            {"value": "equipment", "label": "Equipment"},
            {"value": "vehicle", "label": "Vehicle"},
            {"value": "building", "label": "Building"},
            {"value": "machinery", "label": "Machinery"},
            {"value": "it_equipment", "label": "IT Equipment"},
            {"value": "furniture", "label": "Furniture"},
            {"value": "other", "label": "Other"}
        ]
        
        return {
            "success": True,
            "data": asset_types,
            "total": len(asset_types)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assets list: {str(e)}"
        )

@router.get("/facility-types")
async def get_facility_types(
    current_user: AuthUser = Depends(require_auth())
):
    """
    Alias for /facilities - Get facility TYPES (reference data).
    """
    return await get_facilities_list(current_user)

@router.get("/asset-types")
async def get_asset_types(
    current_user: AuthUser = Depends(require_auth())
):
    """
    Alias for /assets - Get asset TYPES (reference data).
    """
    return await get_assets_list(current_user)