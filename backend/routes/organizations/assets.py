# backend/routes/organizations/assets.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime
from auth import AuthUser, require_org_member, require_permission
from database import get_supabase_client

router = APIRouter(prefix="/api/organizations/assets", tags=["Organization Assets"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class FacilityCreate(BaseModel):
    """Request model for creating a facility with detailed address."""
    name: str = Field(..., min_length=1, max_length=255)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    county: Optional[str] = Field(None, max_length=100)
    postcode: str = Field(..., min_length=1, max_length=20)
    country: str = Field("United Kingdom", max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    type: Optional[str] = Field(None, max_length=100)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "London Office",
                "address_line1": "123 Business Street",
                "city": "London",
                "postcode": "EC1A 1BB",
                "country": "United Kingdom",
                "type": "office"
            }
        }

class FacilityUpdate(BaseModel):
    """Request model for updating a facility."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    address_line1: Optional[str] = Field(None, max_length=255)
    address_line2: Optional[str] = Field(None, max_length=255)
    city: Optional[str] = Field(None, max_length=100)
    county: Optional[str] = Field(None, max_length=100)
    postcode: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    type: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)

class FacilityResponse(BaseModel):
    """Response model for a facility."""
    id: str
    name: str
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    county: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    type: Optional[str] = None
    is_active: bool
    organization_id: str
    organization_name: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    asset_count: Optional[int] = 0
    emissions_count: Optional[int] = 0
    formatted_address: Optional[str] = None

class AssetCreate(BaseModel):
    """Request model for creating an asset."""
    name: str = Field(..., min_length=1, max_length=255)
    facility_id: str = Field(..., description="Facility ID this asset belongs to")
    type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)
    serial_number: Optional[str] = Field(None, max_length=100)
    installation_date: Optional[str] = Field(None)
    capacity: Optional[float] = Field(None)
    capacity_unit: Optional[str] = Field(None, max_length=50)
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)

class AssetUpdate(BaseModel):
    """Request model for updating an asset."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    facility_id: Optional[str] = Field(None)
    type: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(None)
    serial_number: Optional[str] = Field(None, max_length=100)
    installation_date: Optional[str] = Field(None)
    capacity: Optional[float] = Field(None)
    capacity_unit: Optional[str] = Field(None, max_length=50)
    is_active: Optional[bool] = Field(None)
    metadata: Optional[Dict[str, Any]] = Field(None)

class AssetResponse(BaseModel):
    """Response model for an asset."""
    id: str
    name: str
    facility_id: str
    facility_name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    serial_number: Optional[str] = None
    installation_date: Optional[str] = None
    capacity: Optional[float] = None
    capacity_unit: Optional[str] = None
    is_active: bool
    organization_id: str
    organization_name: Optional[str] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    emissions_count: Optional[int] = 0

class AssetListResponse(BaseModel):
    assets: List[AssetResponse]
    total: int

class FacilityListResponse(BaseModel):
    facilities: List[FacilityResponse]
    total: int

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def format_address(facility: Dict) -> Optional[str]:
    """Format a facility's address for display."""
    parts = []
    if facility.get('address_line1'):
        parts.append(facility['address_line1'])
    if facility.get('address_line2'):
        parts.append(facility['address_line2'])
    if facility.get('city'):
        parts.append(facility['city'])
    if facility.get('county'):
        parts.append(facility['county'])
    if facility.get('postcode'):
        parts.append(facility['postcode'])
    if facility.get('country'):
        parts.append(facility['country'])
    return ", ".join(parts) if parts else None

async def get_organization_name(supabase_client, org_id: str) -> Optional[str]:
    """Get organization name by ID."""
    try:
        result = supabase_client.from_('organizations') \
            .select('name') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        return result.data.get('name') if result.data else None
    except Exception:
        return None

async def get_facility_stats(supabase_client, facility_id: str) -> Dict:
    """Get statistics for a facility."""
    try:
        assets_result = supabase_client.from_('assets') \
            .select('id', count='exact') \
            .eq('facility_id', facility_id) \
            .execute()
        asset_count = assets_result.count or 0
        
        asset_ids = [a['id'] for a in (assets_result.data or [])]
        emissions_count = 0
        if asset_ids:
            emissions_result = supabase_client.from_('emissions_logs') \
                .select('id', count='exact') \
                .in_('asset_id', asset_ids) \
                .execute()
            emissions_count = emissions_result.count or 0
        
        return {'asset_count': asset_count, 'emissions_count': emissions_count}
    except Exception as e:
        print(f"⚠️ Error getting facility stats: {e}")
        return {'asset_count': 0, 'emissions_count': 0}

async def get_asset_stats(supabase_client, asset_id: str) -> Dict:
    """Get statistics for an asset."""
    try:
        emissions_result = supabase_client.from_('emissions_logs') \
            .select('id', count='exact') \
            .eq('asset_id', asset_id) \
            .execute()
        return {'emissions_count': emissions_result.count or 0}
    except Exception as e:
        print(f"⚠️ Error getting asset stats: {e}")
        return {'emissions_count': 0}

# ==========================================
# FACILITY ENDPOINTS
# ==========================================

@router.get("/facilities", response_model=FacilityListResponse)
async def get_facilities(
    search: Optional[str] = Query(None, description="Search by name or address"),
    country: Optional[str] = Query(None, description="Filter by country"),
    type: Optional[str] = Query(None, description="Filter by facility type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_org_member())
):
    """Get all facilities for the user's organization."""
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        org_name = await get_organization_name(supabase, org_id)
        
        # Build query
        query = supabase.from_('facilities') \
            .select('*') \
            .eq('organization_id', org_id)
        
        if search:
            query = query.or_(
                f"name.ilike.%{search}%,"
                f"address_line1.ilike.%{search}%,"
                f"city.ilike.%{search}%,"
                f"postcode.ilike.%{search}%"
            )
        if country:
            query = query.eq('country', country)
        if type:
            query = query.eq('type', type)
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        # Count query
        count_query = supabase.from_('facilities') \
            .select('id', count='exact') \
            .eq('organization_id', org_id)
        
        if search:
            count_query = count_query.or_(
                f"name.ilike.%{search}%,"
                f"address_line1.ilike.%{search}%,"
                f"city.ilike.%{search}%,"
                f"postcode.ilike.%{search}%"
            )
        if country:
            count_query = count_query.eq('country', country)
        if type:
            count_query = count_query.eq('type', type)
        if is_active is not None:
            count_query = count_query.eq('is_active', is_active)
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        result = query.order('name').range(offset, offset + limit - 1).execute()
        
        facilities = []
        for facility in result.data:
            stats = await get_facility_stats(supabase, facility['id'])
            
            facilities.append(FacilityResponse(
                id=facility['id'],
                name=facility['name'],
                address_line1=facility.get('address_line1'),
                address_line2=facility.get('address_line2'),
                city=facility.get('city'),
                county=facility.get('county'),
                postcode=facility.get('postcode'),
                country=facility.get('country', 'United Kingdom'),
                region=facility.get('region'),
                latitude=facility.get('latitude'),
                longitude=facility.get('longitude'),
                type=facility.get('type'),
                is_active=facility.get('is_active', True),
                organization_id=org_id,
                organization_name=org_name,
                metadata=facility.get('metadata', {}),
                created_at=facility['created_at'],
                updated_at=facility.get('updated_at', facility['created_at']),
                asset_count=stats['asset_count'],
                emissions_count=stats['emissions_count'],
                formatted_address=format_address(facility)
            ))
        
        return FacilityListResponse(facilities=facilities, total=total)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting facilities: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get facilities: {str(e)}"
        )

@router.post("/facilities", response_model=FacilityResponse)
async def create_facility(
    facility_data: FacilityCreate,
    current_user: AuthUser = Depends(require_org_member())
):
    """Create a new facility."""
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Check if facility name exists
        existing = supabase.from_('facilities') \
            .select('id') \
            .eq('organization_id', org_id) \
            .ilike('name', facility_data.name) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Facility with name '{facility_data.name}' already exists"
            )
        
        insert_data = facility_data.dict()
        insert_data['organization_id'] = org_id
        insert_data['is_active'] = True
        insert_data['created_at'] = datetime.now().isoformat()
        insert_data['updated_at'] = datetime.now().isoformat()
        
        result = supabase.from_('facilities') \
            .insert(insert_data) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create facility"
            )
        
        # Fetch the created facility
        return await get_facility_by_id(supabase, result.data[0]['id'], org_id, org_name=None)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating facility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create facility: {str(e)}"
        )

async def get_facility_by_id(supabase_client, facility_id: str, org_id: str, org_name: Optional[str] = None):
    """Helper to get a single facility by ID."""
    if not org_name:
        org_name = await get_organization_name(supabase_client, org_id)
    
    result = supabase_client.from_('facilities') \
        .select('*') \
        .eq('id', facility_id) \
        .maybe_single() \
        .execute()
    
    if not result.data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Facility not found"
        )
    
    facility = result.data
    stats = await get_facility_stats(supabase_client, facility_id)
    
    return FacilityResponse(
        id=facility['id'],
        name=facility['name'],
        address_line1=facility.get('address_line1'),
        address_line2=facility.get('address_line2'),
        city=facility.get('city'),
        county=facility.get('county'),
        postcode=facility.get('postcode'),
        country=facility.get('country', 'United Kingdom'),
        region=facility.get('region'),
        latitude=facility.get('latitude'),
        longitude=facility.get('longitude'),
        type=facility.get('type'),
        is_active=facility.get('is_active', True),
        organization_id=org_id,
        organization_name=org_name,
        metadata=facility.get('metadata', {}),
        created_at=facility['created_at'],
        updated_at=facility.get('updated_at', facility['created_at']),
        asset_count=stats['asset_count'],
        emissions_count=stats['emissions_count'],
        formatted_address=format_address(facility)
    )

# ==========================================
# ASSET ENDPOINTS
# ==========================================

@router.get("/", response_model=AssetListResponse)
async def get_assets(
    facility_id: Optional[str] = Query(None, description="Filter by facility ID"),
    type: Optional[str] = Query(None, description="Filter by type"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_org_member())
):
    """Get all assets for the user's organization."""
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
            return AssetListResponse(assets=[], total=0)
        
        # Build query
        query = supabase.from_('assets') \
            .select('*') \
            .in_('facility_id', facility_ids)
        
        if facility_id:
            query = query.eq('facility_id', facility_id)
        if type:
            query = query.eq('type', type)
        if search:
            query = query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")
        if is_active is not None:
            query = query.eq('is_active', is_active)
        
        # Count query
        count_query = supabase.from_('assets') \
            .select('id', count='exact') \
            .in_('facility_id', facility_ids)
        
        if facility_id:
            count_query = count_query.eq('facility_id', facility_id)
        if type:
            count_query = count_query.eq('type', type)
        if search:
            count_query = count_query.or_(f"name.ilike.%{search}%,description.ilike.%{search}%")
        if is_active is not None:
            count_query = count_query.eq('is_active', is_active)
        
        count_result = count_query.execute()
        total = count_result.count or 0
        
        result = query.order('name').range(offset, offset + limit - 1).execute()
        
        org_name = await get_organization_name(supabase, org_id)
        
        # Get facility names for assets
        facility_names = {}
        if facility_ids:
            fac_names = supabase.from_('facilities') \
                .select('id, name') \
                .in_('id', facility_ids) \
                .execute()
            for f in fac_names.data or []:
                facility_names[f['id']] = f['name']
        
        assets = []
        for asset in result.data:
            stats = await get_asset_stats(supabase, asset['id'])
            
            assets.append(AssetResponse(
                id=asset['id'],
                name=asset['name'],
                facility_id=asset.get('facility_id'),
                facility_name=facility_names.get(asset.get('facility_id')),
                type=asset.get('type'),
                description=asset.get('description'),
                serial_number=asset.get('serial_number'),
                installation_date=asset.get('installation_date'),
                capacity=asset.get('capacity'),
                capacity_unit=asset.get('capacity_unit'),
                is_active=asset.get('is_active', True),
                organization_id=org_id,
                organization_name=org_name,
                metadata=asset.get('metadata', {}),
                created_at=asset['created_at'],
                updated_at=asset.get('updated_at', asset['created_at']),
                emissions_count=stats['emissions_count']
            ))
        
        return AssetListResponse(assets=assets, total=total)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting assets: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get assets: {str(e)}"
        )

@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset_data: AssetCreate,
    current_user: AuthUser = Depends(require_org_member())
):
    """Create a new asset."""
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        # Validate facility belongs to org
        facility = supabase.from_('facilities') \
            .select('id') \
            .eq('id', asset_data.facility_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not facility.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Facility not found or does not belong to your organization"
            )
        
        # Check if asset name exists in this facility
        existing = supabase.from_('assets') \
            .select('id') \
            .eq('facility_id', asset_data.facility_id) \
            .ilike('name', asset_data.name) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Asset with name '{asset_data.name}' already exists in this facility"
            )
        
        insert_data = asset_data.dict()
        insert_data['is_active'] = True
        insert_data['created_at'] = datetime.now().isoformat()
        insert_data['updated_at'] = datetime.now().isoformat()
        
        result = supabase.from_('assets') \
            .insert(insert_data) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create asset"
            )
        
        # Fetch the created asset
        asset_id = result.data[0]['id']
        org_name = await get_organization_name(supabase, org_id)
        
        asset_result = supabase.from_('assets') \
            .select('*') \
            .eq('id', asset_id) \
            .maybe_single() \
            .execute()
        
        asset = asset_result.data
        stats = await get_asset_stats(supabase, asset_id)
        
        # Get facility name
        facility_name = None
        if asset.get('facility_id'):
            fac_name_result = supabase.from_('facilities') \
                .select('name') \
                .eq('id', asset.get('facility_id')) \
                .maybe_single() \
                .execute()
            if fac_name_result.data:
                facility_name = fac_name_result.data.get('name')
        
        return AssetResponse(
            id=asset['id'],
            name=asset['name'],
            facility_id=asset.get('facility_id'),
            facility_name=facility_name,
            type=asset.get('type'),
            description=asset.get('description'),
            serial_number=asset.get('serial_number'),
            installation_date=asset.get('installation_date'),
            capacity=asset.get('capacity'),
            capacity_unit=asset.get('capacity_unit'),
            is_active=asset.get('is_active', True),
            organization_id=org_id,
            organization_name=org_name,
            metadata=asset.get('metadata', {}),
            created_at=asset['created_at'],
            updated_at=asset.get('updated_at', asset['created_at']),
            emissions_count=stats['emissions_count']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create asset: {str(e)}"
        )

@router.delete("/facilities/{facility_id}")
async def delete_facility(
    facility_id: str,
    permanent: bool = Query(False, description="Permanently delete or soft delete"),
    current_user: AuthUser = Depends(require_org_member())
):
    """Delete a facility."""
    try:
        supabase = get_supabase_client()
        
        org_id = current_user.organization_id
        if not org_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is not associated with an organization"
            )
        
        existing = supabase.from_('facilities') \
            .select('id, name') \
            .eq('id', facility_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Facility not found"
            )
        
        if permanent:
            assets = supabase.from_('assets') \
                .select('id', count='exact') \
                .eq('facility_id', facility_id) \
                .execute()
            
            if assets.count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete facility with {assets.count} assets"
                )
            
            supabase.from_('facilities') \
                .delete() \
                .eq('id', facility_id) \
                .execute()
            message = f"Facility '{existing.data['name']}' permanently deleted"
        else:
            supabase.from_('facilities') \
                .update({'is_active': False, 'updated_at': datetime.now().isoformat()}) \
                .eq('id', facility_id) \
                .execute()
            message = f"Facility '{existing.data['name']}' deactivated"
        
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting facility: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete facility: {str(e)}"
        )

@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: str,
    permanent: bool = Query(False, description="Permanently delete or soft delete"),
    current_user: AuthUser = Depends(require_org_member())
):
    """Delete an asset."""
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
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        existing = supabase.from_('assets') \
            .select('id, name') \
            .eq('id', asset_id) \
            .in_('facility_id', facility_ids) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Asset not found"
            )
        
        if permanent:
            emissions = supabase.from_('emissions_logs') \
                .select('id', count='exact') \
                .eq('asset_id', asset_id) \
                .execute()
            
            if emissions.count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot delete asset with {emissions.count} emissions records"
                )
            
            supabase.from_('assets') \
                .delete() \
                .eq('id', asset_id) \
                .execute()
            message = f"Asset '{existing.data['name']}' permanently deleted"
        else:
            supabase.from_('assets') \
                .update({'is_active': False, 'updated_at': datetime.now().isoformat()}) \
                .eq('id', asset_id) \
                .execute()
            message = f"Asset '{existing.data['name']}' deactivated"
        
        return {"success": True, "message": message}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting asset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete asset: {str(e)}"
        )