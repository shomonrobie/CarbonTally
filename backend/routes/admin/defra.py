# backend/routes/admin/defra.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from auth import AuthUser, require_role, require_permission
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/defra", tags=["Admin - DEFRA Factor Management"])

# ==========================================
# PYDANTIC MODELS
# ==========================================
class DEFRAFactorBase(BaseModel):
    """Base DEFRA factor model with common fields and validations."""
    reporting_year: int = Field(..., ge=2000, le=2100, description="Reporting year")
    activity_type: str = Field(..., min_length=1, max_length=150, description="Activity type (e.g., Diesel (DERV))")
    co2e_multiplier: float = Field(..., gt=0, description="CO2e multiplier (kg CO2e per unit)")
    
    @validator('activity_type')
    def validate_activity_type(cls, v):
        """Ensure activity type is properly formatted."""
        return v.strip()
    
    class Config:
        json_schema_extra = {
            "example": {
                "reporting_year": 2024,
                "activity_type": "Diesel (DERV)",
                "co2e_multiplier": 2.68
            }
        }

class DEFRAFactorCreate(DEFRAFactorBase):
    """Request model for creating a DEFRA factor."""
    pass  # All fields are required (inherited)

class DEFRAFactorUpdate(BaseModel):
    """Request model for updating a DEFRA factor."""
    reporting_year: Optional[int] = Field(None, ge=2000, le=2100)
    activity_type: Optional[str] = Field(None, min_length=1, max_length=150)
    co2e_multiplier: Optional[float] = Field(None, gt=0)
    
    @validator('activity_type')
    def validate_activity_type(cls, v):
        """Ensure activity type is properly formatted."""
        if v:
            return v.strip()
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "activity_type": "Diesel (DERV) - Updated",
                "co2e_multiplier": 2.75
            }
        }


class DEFRAFactorBulkCreate(BaseModel):
    """Request model for bulk creating DEFRA factors."""
    factors: List[DEFRAFactorCreate] = Field(..., min_items=1, description="List of factors to create")
    
    class Config:
        json_schema_extra = {
            "example": {
                "factors": [
                    {
                        "reporting_year": 2024,
                        "activity_type": "Diesel (DERV)",
                        "co2e_multiplier": 2.68
                    },
                    {
                        "reporting_year": 2024,
                        "activity_type": "Petrol (Unleaded)",
                        "co2e_multiplier": 2.45
                    }
                ]
            }
        }

class DEFRAFactorResponse(BaseModel):
    """Response model for a DEFRA factor."""
    id: str
    reporting_year: int
    activity_type: str
    co2e_multiplier: float
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "reporting_year": 2024,
                "activity_type": "Diesel (DERV)",
                "co2e_multiplier": 2.68,
                "created_at": "2024-01-01T00:00:00Z"
            }
        }

class DEFRAFactorListResponse(BaseModel):
    """Response model for DEFRA factor list."""
    factors: List[DEFRAFactorResponse]
    total: int
    years_available: List[int]
    activities_available: List[str]

# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def get_available_years(supabase_client) -> List[int]:
    """Get all available reporting years."""
    try:
        result = supabase_client.from_('defra_conversion_factors') \
            .select('reporting_year') \
            .order('reporting_year', desc=True) \
            .execute()
        
        years = list(set([f['reporting_year'] for f in result.data])) if result.data else []
        return sorted(years, reverse=True)
    except Exception as e:
        print(f"⚠️ Error getting available years: {e}")
        return []

async def get_available_activities(supabase_client) -> List[str]:
    """Get all available activity types."""
    try:
        result = supabase_client.from_('defra_conversion_factors') \
            .select('activity_type') \
            .order('activity_type') \
            .execute()
        
        activities = list(set([f['activity_type'] for f in result.data])) if result.data else []
        return sorted(activities)
    except Exception as e:
        print(f"⚠️ Error getting available activities: {e}")
        return []

# ==========================================
# ENDPOINTS
# ==========================================
@router.get("/factors")
async def get_admin_defra_factors(
    year: Optional[int] = Query(None, description="Filter by reporting year"),
    activity: Optional[str] = Query(None, description="Filter by activity type"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Get all DEFRA factors with filters."""
    try:
        supabase = get_supabase_client()
        
        # ✅ Build the query
        query = supabase.from_('defra_conversion_factors') \
            .select('*')
        
        if year:
            query = query.eq('reporting_year', year)
        if activity:
            query = query.ilike('activity_type', f'%{activity}%')
        
        # ✅ Get count separately (no .clone())
        count_query = supabase.from_('defra_conversion_factors') \
            .select('id', count='exact')
        
        if year:
            count_query = count_query.eq('reporting_year', year)
        if activity:
            count_query = count_query.ilike('activity_type', f'%{activity}%')
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        # Get paginated results
        result = query.order('reporting_year', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {
            "success": True,
            "data": result.data or [],
            "total": total,
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        print(f"❌ Error getting DEFRA factors: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DEFRA factors: {str(e)}"
        )


@router.get("/factors/{factor_id}", response_model=DEFRAFactorResponse)
async def get_defra_factor(
    factor_id: str,
    current_user: AuthUser = Depends(require_role(["admin", "data_approver"]))
):
    """
    Get a specific DEFRA factor by ID.
    Available to admins and data approvers.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('defra_conversion_factors') \
            .select('id, reporting_year, activity_type, co2e_multiplier, created_at') \
            .eq('id', factor_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DEFRA factor not found"
            )
        
        factor = result.data
        return DEFRAFactorResponse(
            id=factor['id'],
            reporting_year=factor['reporting_year'],
            activity_type=factor['activity_type'],
            co2e_multiplier=float(factor['co2e_multiplier']),
            created_at=factor['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting DEFRA factor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DEFRA factor: {str(e)}"
        )

@router.post("/factors", response_model=DEFRAFactorResponse)
async def create_defra_factor(
    factor_data: DEFRAFactorCreate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Create a new DEFRA factor.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if factor already exists for this year and activity
        existing = supabase.from_('defra_conversion_factors') \
            .select('id') \
            .eq('reporting_year', factor_data.reporting_year) \
            .eq('activity_type', factor_data.activity_type) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Factor already exists for {factor_data.activity_type} in {factor_data.reporting_year}"
            )
        
        # Create factor
        result = supabase.from_('defra_conversion_factors') \
            .insert({
                'reporting_year': factor_data.reporting_year,
                'activity_type': factor_data.activity_type,
                'co2e_multiplier': factor_data.co2e_multiplier
            }) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create DEFRA factor"
            )
        
        factor = result.data[0]
        return DEFRAFactorResponse(
            id=factor['id'],
            reporting_year=factor['reporting_year'],
            activity_type=factor['activity_type'],
            co2e_multiplier=float(factor['co2e_multiplier']),
            created_at=factor['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating DEFRA factor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create DEFRA factor: {str(e)}"
        )

@router.post("/factors/bulk")
async def create_defra_factors_bulk(
    bulk_data: DEFRAFactorBulkCreate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Bulk create DEFRA factors.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        created = 0
        skipped = 0
        errors = []
        
        for factor in bulk_data.factors:
            try:
                # Check if exists
                existing = supabase.from_('defra_conversion_factors') \
                    .select('id') \
                    .eq('reporting_year', factor.reporting_year) \
                    .eq('activity_type', factor.activity_type) \
                    .maybe_single() \
                    .execute()
                
                if existing.data:
                    skipped += 1
                    continue
                
                # Create factor
                result = supabase.from_('defra_conversion_factors') \
                    .insert({
                        'reporting_year': factor.reporting_year,
                        'activity_type': factor.activity_type,
                        'co2e_multiplier': factor.co2e_multiplier
                    }) \
                    .execute()
                
                if result.data:
                    created += 1
                else:
                    errors.append(f"Failed to create {factor.activity_type} ({factor.reporting_year})")
                    
            except Exception as e:
                errors.append(f"Error creating {factor.activity_type} ({factor.reporting_year}): {str(e)}")
        
        return {
            "success": True,
            "message": f"Created {created} factors, skipped {skipped} existing",
            "created": created,
            "skipped": skipped,
            "errors": errors if errors else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error bulk creating DEFRA factors: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bulk create DEFRA factors: {str(e)}"
        )

@router.put("/factors/{factor_id}", response_model=DEFRAFactorResponse)
async def update_defra_factor(
    factor_id: str,
    update_data: DEFRAFactorUpdate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Update a DEFRA factor.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if factor exists
        existing = supabase.from_('defra_conversion_factors') \
            .select('id, reporting_year, activity_type') \
            .eq('id', factor_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DEFRA factor not found"
            )
        
        # Build update dict
        update_dict = {}
        if update_data.activity_type is not None:
            update_dict['activity_type'] = update_data.activity_type
        if update_data.co2e_multiplier is not None:
            update_dict['co2e_multiplier'] = update_data.co2e_multiplier
        if update_data.reporting_year is not None:
            update_dict['reporting_year'] = update_data.reporting_year
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Check for duplicate if changing year or activity
        if update_data.activity_type or update_data.reporting_year:
            new_year = update_data.reporting_year or existing.data['reporting_year']
            new_activity = update_data.activity_type or existing.data['activity_type']
            
            duplicate = supabase.from_('defra_conversion_factors') \
                .select('id') \
                .eq('reporting_year', new_year) \
                .eq('activity_type', new_activity) \
                .neq('id', factor_id) \
                .maybe_single() \
                .execute()
            
            if duplicate.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Factor already exists for {new_activity} in {new_year}"
                )
        
        # Update factor
        result = supabase.from_('defra_conversion_factors') \
            .update(update_dict) \
            .eq('id', factor_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update DEFRA factor"
            )
        
        factor = result.data[0]
        return DEFRAFactorResponse(
            id=factor['id'],
            reporting_year=factor['reporting_year'],
            activity_type=factor['activity_type'],
            co2e_multiplier=float(factor['co2e_multiplier']),
            created_at=factor['created_at']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating DEFRA factor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update DEFRA factor: {str(e)}"
        )

@router.delete("/factors/{factor_id}")
async def delete_defra_factor(
    factor_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Delete a DEFRA factor.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if factor exists
        existing = supabase.from_('defra_conversion_factors') \
            .select('id, activity_type, reporting_year') \
            .eq('id', factor_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="DEFRA factor not found"
            )
        
        # Check if factor is being used in emissions_logs
        emissions_usage = supabase.from_('emissions_logs') \
            .select('id', count='exact') \
            .eq('defra_factor_id', factor_id) \
            .execute()
        
        if emissions_usage.count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete factor that is used in {emissions_usage.count} emissions records"
            )
        
        # Delete factor
        result = supabase.from_('defra_conversion_factors') \
            .delete() \
            .eq('id', factor_id) \
            .execute()
        
        return {
            "success": True,
            "message": f"DEFRA factor '{existing.data['activity_type']}' ({existing.data['reporting_year']}) deleted successfully",
            "factor_id": factor_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting DEFRA factor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete DEFRA factor: {str(e)}"
        )

@router.get("/years")
async def get_defra_years(
    current_user: AuthUser = Depends(require_role(["admin", "data_approver", "staff"]))
):
    """
    Get all available DEFRA reporting years.
    Available to admins, data approvers, and staff.
    """
    try:
        supabase = get_supabase_client()
        
        years = await get_available_years(supabase)
        
        return {
            "years": years,
            "total": len(years)
        }
        
    except Exception as e:
        print(f"❌ Error getting DEFRA years: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DEFRA years: {str(e)}"
        )

@router.get("/activities")
async def get_defra_activities(
    reporting_year: Optional[int] = Query(None, description="Filter by reporting year"),
    current_user: AuthUser = Depends(require_role(["admin", "data_approver", "staff"]))
):
    """
    Get all available DEFRA activity types.
    Optionally filter by reporting year.
    Available to admins, data approvers, and staff.
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('defra_conversion_factors') \
            .select('activity_type')
        
        if reporting_year:
            query = query.eq('reporting_year', reporting_year)
        
        result = query.order('activity_type').execute()
        
        activities = list(set([f['activity_type'] for f in result.data])) if result.data else []
        
        return {
            "activities": sorted(activities),
            "total": len(activities)
        }
        
    except Exception as e:
        print(f"❌ Error getting DEFRA activities: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get DEFRA activities: {str(e)}"
        )

@router.get("/validate")
async def validate_defra_factor(
    reporting_year: int = Query(..., description="Reporting year to validate"),
    activity_type: str = Query(..., description="Activity type to validate"),
    current_user: AuthUser = Depends(require_role(["admin", "data_approver"]))
):
    """
    Validate if a DEFRA factor exists for a given year and activity.
    Available to admins and data approvers.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('defra_conversion_factors') \
            .select('id, co2e_multiplier') \
            .eq('reporting_year', reporting_year) \
            .eq('activity_type', activity_type) \
            .maybe_single() \
            .execute()
        
        if result.data:
            return {
                "exists": True,
                "factor_id": result.data['id'],
                "co2e_multiplier": float(result.data['co2e_multiplier']),
                "reporting_year": reporting_year,
                "activity_type": activity_type
            }
        else:
            return {
                "exists": False,
                "reporting_year": reporting_year,
                "activity_type": activity_type,
                "message": f"No factor found for {activity_type} in {reporting_year}"
            }
        
    except Exception as e:
        print(f"❌ Error validating DEFRA factor: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate DEFRA factor: {str(e)}"
        )