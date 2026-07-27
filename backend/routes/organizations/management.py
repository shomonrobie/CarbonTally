# backend/routes/organizations/management.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from auth import AuthUser, require_role, require_permission, require_org_member, get_current_user
from database import get_supabase_client


router = APIRouter(prefix="/organizations", tags=["Organization Management"])  # ✅ This should be the prefix

# ==========================================
# PYDANTIC MODELS
# ==========================================

class OrganizationCreate(BaseModel):
    """Request model for creating an organization."""
    name: str = Field(..., min_length=1, max_length=255)
    company_number: Optional[str] = Field(None, max_length=50)
    registered_address: Optional[str] = Field(None)
    country: Optional[str] = Field("UK")
    timezone: Optional[str] = Field("Europe/London")
    currency: Optional[str] = Field("GBP")
    website: Optional[str] = Field(None)
    industry: Optional[str] = Field(None)
    sector: Optional[str] = Field(None)
    company_size: Optional[str] = Field(None)
    vat_number: Optional[str] = Field(None)
    registration_number: Optional[str] = Field(None)
    financial_year_end: Optional[str] = Field(None)
    reporting_standard: Optional[str] = Field("SECR")
    secr_enabled: bool = True
    esrs_enabled: bool = False
    issb_enabled: bool = False
    default_defra_version: int = Field(2024)
    preferred_units: str = Field("metric")
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "ACME Corporation",
                "company_number": "12345678",
                "registered_address": "123 Business St, London, UK",
                "country": "UK",
                "timezone": "Europe/London",
                "currency": "GBP",
                "website": "https://acme.com",
                "industry": "Technology",
                "sector": "Software",
                "company_size": "50-100",
                "reporting_standard": "SECR",
                "secr_enabled": True,
                "default_defra_version": 2024
            }
        }

class OrganizationUpdate(BaseModel):
    """Request model for updating an organization."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    company_number: Optional[str] = Field(None, max_length=50)
    registered_address: Optional[str] = Field(None)
    country: Optional[str] = Field(None)
    timezone: Optional[str] = Field(None)
    currency: Optional[str] = Field(None)
    website: Optional[str] = Field(None)
    industry: Optional[str] = Field(None)
    sector: Optional[str] = Field(None)
    company_size: Optional[str] = Field(None)
    vat_number: Optional[str] = Field(None)
    registration_number: Optional[str] = Field(None)
    financial_year_end: Optional[str] = Field(None)
    reporting_standard: Optional[str] = Field(None)
    secr_enabled: Optional[bool] = Field(None)
    esrs_enabled: Optional[bool] = Field(None)
    issb_enabled: Optional[bool] = Field(None)
    default_defra_version: Optional[int] = Field(None)
    preferred_units: Optional[str] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "ACME Corporation Ltd",
                "industry": "Technology - Software",
                "secr_enabled": True
            }
        }

class OrganizationResponse(BaseModel):
    """Response model for an organization."""
    id: str
    name: str
    company_number: Optional[str] = None
    registered_address: Optional[str] = None
    country: str
    timezone: str
    currency: str
    website: Optional[str] = None
    industry: Optional[str] = None
    sector: Optional[str] = None
    company_size: Optional[str] = None
    vat_number: Optional[str] = None
    registration_number: Optional[str] = None
    financial_year_end: Optional[str] = None
    reporting_standard: str
    secr_enabled: bool
    esrs_enabled: bool
    issb_enabled: bool
    default_defra_version: int
    preferred_units: str
    logo_url: Optional[str] = None
    subscription_status: str
    subscription_tier: str
    trial_start_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = 0
    emissions_record_count: Optional[int] = 0
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "2b7a2e09-2cc3-461e-84e6-81137eb63ab3",
                "name": "ACME Corporation",
                "country": "UK",
                "timezone": "Europe/London",
                "currency": "GBP",
                "reporting_standard": "SECR",
                "secr_enabled": True,
                "default_defra_version": 2024,
                "subscription_status": "active",
                "subscription_tier": "starter",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z",
                "member_count": 5,
                "emissions_record_count": 150
            }
        }

class OrganizationStats(BaseModel):
    """Response model for organization stats."""
    organization_id: str
    organization_name: str
    total_members: int
    active_members: int
    total_assets: int
    total_facilities: int
    total_emissions_records: int
    total_emissions_kg: float
    total_emissions_tonnes: float
    records_by_scope: Dict[str, int]
    last_activity: Optional[datetime] = None

# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def get_organization_stats(supabase_client, org_id: str) -> Dict:
    """Get statistics for an organization."""
    try:
        # Get member count
        members_result = supabase_client.from_('organization_members') \
            .select('id, is_active', count='exact') \
            .eq('organization_id', org_id) \
            .execute()
        
        members = members_result.data or []
        total_members = len(members)
        active_members = sum(1 for m in members if m.get('is_active', True))
        
        # Get asset count
        assets_result = supabase_client.from_('assets') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .execute()
        total_assets = assets_result.count or 0
        
        # Get facility count
        facilities_result = supabase_client.from_('facilities') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .execute()
        total_facilities = facilities_result.count or 0
        
        # Get emissions records
        emissions_result = supabase_client.from_('emissions_logs') \
            .select('calculated_kg_co2e, metadata') \
            .eq('organization_id', org_id) \
            .execute()
        
        records = emissions_result.data or []
        total_records = len(records)
        total_kg = sum(r.get('calculated_kg_co2e', 0) for r in records)
        
        # Get scope breakdown
        records_by_scope = {'1': 0, '2': 0, '3': 0}
        for record in records:
            scope = record.get('metadata', {}).get('scope', 'Unknown')
            if scope in records_by_scope:
                records_by_scope[scope] += 1
        
        # Get last activity
        last_activity_result = supabase_client.from_('emissions_logs') \
            .select('created_at') \
            .eq('organization_id', org_id) \
            .order('created_at', desc=True) \
            .limit(1) \
            .execute()
        
        last_activity = last_activity_result.data[0]['created_at'] if last_activity_result.data else None
        
        return {
            'total_members': total_members,
            'active_members': active_members,
            'total_assets': total_assets,
            'total_facilities': total_facilities,
            'total_emissions_records': total_records,
            'total_emissions_kg': total_kg,
            'total_emissions_tonnes': total_kg / 1000,
            'records_by_scope': records_by_scope,
            'last_activity': last_activity
        }
        
    except Exception as e:
        print(f"⚠️ Error getting organization stats: {e}")
        return {
            'total_members': 0,
            'active_members': 0,
            'total_assets': 0,
            'total_facilities': 0,
            'total_emissions_records': 0,
            'total_emissions_kg': 0,
            'total_emissions_tonnes': 0,
            'records_by_scope': {'1': 0, '2': 0, '3': 0},
            'last_activity': None
        }

# ==========================================
# ENDPOINTS
# ==========================================

@router.get("/", response_model=List[OrganizationResponse])
async def get_all_organizations(
    search: Optional[str] = Query(None, description="Search by name"),
    industry: Optional[str] = Query(None, description="Filter by industry"),
    subscription_status: Optional[str] = Query(None, description="Filter by subscription status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get all organizations.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('organizations').select('*')
        
        if search:
            query = query.ilike('name', f'%{search}%')
        if industry:
            query = query.eq('industry', industry)
        if subscription_status:
            query = query.eq('subscription_status', subscription_status)
        
        result = query.order('name').range(offset, offset + limit - 1).execute()
        
        organizations = []
        for org in result.data:
            stats = await get_organization_stats(supabase, org['id'])
            
            organizations.append(OrganizationResponse(
                id=org['id'],
                name=org['name'],
                company_number=org.get('company_number'),
                registered_address=org.get('registered_address'),
                country=org.get('country', 'UK'),
                timezone=org.get('timezone', 'Europe/London'),
                currency=org.get('currency', 'GBP'),
                website=org.get('website'),
                industry=org.get('industry'),
                sector=org.get('sector'),
                company_size=org.get('company_size'),
                vat_number=org.get('vat_number'),
                registration_number=org.get('registration_number'),
                financial_year_end=org.get('financial_year_end'),
                reporting_standard=org.get('reporting_standard', 'SECR'),
                secr_enabled=org.get('secr_enabled', True),
                esrs_enabled=org.get('esrs_enabled', False),
                issb_enabled=org.get('issb_enabled', False),
                default_defra_version=org.get('default_defra_version', 2024),
                preferred_units=org.get('preferred_units', 'metric'),
                logo_url=org.get('logo_url'),
                subscription_status=org.get('subscription_status', 'trial'),
                subscription_tier=org.get('subscription_tier', 'starter'),
                trial_start_date=org.get('trial_start_date'),
                trial_end_date=org.get('trial_end_date'),
                created_at=org['created_at'],
                updated_at=org.get('updated_at', org['created_at']),
                member_count=stats['total_members'],
                emissions_record_count=stats['total_emissions_records']
            ))
        
        return organizations
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting organizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organizations: {str(e)}"
        )

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get a specific organization by ID.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('organizations') \
            .select('*') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        org = result.data
        stats = await get_organization_stats(supabase, org_id)
        
        return OrganizationResponse(
            id=org['id'],
            name=org['name'],
            company_number=org.get('company_number'),
            registered_address=org.get('registered_address'),
            country=org.get('country', 'UK'),
            timezone=org.get('timezone', 'Europe/London'),
            currency=org.get('currency', 'GBP'),
            website=org.get('website'),
            industry=org.get('industry'),
            sector=org.get('sector'),
            company_size=org.get('company_size'),
            vat_number=org.get('vat_number'),
            registration_number=org.get('registration_number'),
            financial_year_end=org.get('financial_year_end'),
            reporting_standard=org.get('reporting_standard', 'SECR'),
            secr_enabled=org.get('secr_enabled', True),
            esrs_enabled=org.get('esrs_enabled', False),
            issb_enabled=org.get('issb_enabled', False),
            default_defra_version=org.get('default_defra_version', 2024),
            preferred_units=org.get('preferred_units', 'metric'),
            logo_url=org.get('logo_url'),
            subscription_status=org.get('subscription_status', 'trial'),
            subscription_tier=org.get('subscription_tier', 'starter'),
            trial_start_date=org.get('trial_start_date'),
            trial_end_date=org.get('trial_end_date'),
            created_at=org['created_at'],
            updated_at=org.get('updated_at', org['created_at']),
            member_count=stats['total_members'],
            emissions_record_count=stats['total_emissions_records']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization: {str(e)}"
        )

@router.post("/", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Create a new organization.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if organization name already exists
        existing = supabase.from_('organizations') \
            .select('id') \
            .ilike('name', org_data.name) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Organization with name '{org_data.name}' already exists"
            )
        
        # Create organization
        now = datetime.now().isoformat()
        result = supabase.from_('organizations') \
            .insert({
                **org_data.dict(exclude_unset=True),
                'created_at': now,
                'updated_at': now,
                'subscription_status': 'trial',
                'subscription_tier': 'starter',
                'trial_start_date': now,
                'trial_end_date': (datetime.now() + timedelta(days=30)).isoformat()
            }) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create organization"
            )
        
        # Get the created organization
        return await get_organization(result.data[0]['id'], current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create organization: {str(e)}"
        )

@router.put("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    update_data: OrganizationUpdate,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Update an organization.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if organization exists
        existing = supabase.from_('organizations') \
            .select('id') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Check name uniqueness if updating
        if update_data.name:
            name_check = supabase.from_('organizations') \
                .select('id') \
                .ilike('name', update_data.name) \
                .neq('id', org_id) \
                .maybe_single() \
                .execute()
            
            if name_check.data:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Organization with name '{update_data.name}' already exists"
                )
        
        # Update organization
        update_dict = update_data.dict(exclude_unset=True)
        update_dict['updated_at'] = datetime.now().isoformat()
        
        result = supabase.from_('organizations') \
            .update(update_dict) \
            .eq('id', org_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update organization"
            )
        
        return await get_organization(org_id, current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization: {str(e)}"
        )

@router.delete("/{org_id}")
async def delete_organization(
    org_id: str,
    permanent: bool = Query(False, description="Permanently delete or soft delete"),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Delete an organization.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if organization exists
        existing = supabase.from_('organizations') \
            .select('id, name') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        if permanent:
            # Check if there are any members before permanent delete
            members = supabase.from_('organization_members') \
                .select('id', count='exact') \
                .eq('organization_id', org_id) \
                .execute()
            
            if members.count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot permanently delete organization with {members.count} members. Remove members first."
                )
            
            # Hard delete
            result = supabase.from_('organizations') \
                .delete() \
                .eq('id', org_id) \
                .execute()
            
            message = f"Organization '{existing.data['name']}' permanently deleted"
        else:
            # Soft delete - deactivate
            result = supabase.from_('organizations') \
                .update({
                    'is_active': False,
                    'deleted_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }) \
                .eq('id', org_id) \
                .execute()
            
            message = f"Organization '{existing.data['name']}' deactivated"
        
        return {
            "success": True,
            "message": message,
            "organization_id": org_id,
            "permanent": permanent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete organization: {str(e)}"
        )

@router.get("/{org_id}/stats", response_model=OrganizationStats)
async def get_organization_stats_endpoint(
    org_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Get detailed statistics for an organization.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()
        
        # Get organization name
        org_result = supabase.from_('organizations') \
            .select('name') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        if not org_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        stats = await get_organization_stats(supabase, org_id)
        
        return OrganizationStats(
            organization_id=org_id,
            organization_name=org_result.data['name'],
            **stats
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting organization stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization stats: {str(e)}"
        )
# ==========================================
# ORGANIZATION METADATA ENDPOINTS
# ==========================================
# backend/routes/organizations/management.py - Add after the existing endpoints

# ==========================================
# ORGANIZATION METADATA MODELS
# ==========================================
class OrganizationMetadataUpdate(BaseModel):
    """Request model for updating organization metadata."""
    total_employees: Optional[int] = None
    full_time_employees: Optional[int] = None
    part_time_employees: Optional[int] = None
    contract_employees: Optional[int] = None
    average_employees: Optional[int] = None
    annual_revenue: Optional[float] = None
    ebitda: Optional[float] = None
    total_assets: Optional[float] = None
    total_facilities: Optional[int] = None
    total_floor_area_sqft: Optional[float] = None
    occupied_floor_area_sqft: Optional[float] = None
    renewable_energy_percentage: Optional[float] = None
    carbon_offset_percentage: Optional[float] = None
    energy_intensity: Optional[float] = None
    reporting_standard: Optional[str] = None
    fiscal_year_start: Optional[str] = None
    fiscal_year_end: Optional[str] = None
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    sustainability_officer_name: Optional[str] = None
    sustainability_officer_email: Optional[str] = None
    industry_sector: Optional[str] = None
    naics_code: Optional[str] = None
    sic_code: Optional[str] = None
    custom_metrics: Optional[Dict[str, Any]] = None

# ==========================================
# HELPER FUNCTIONS
# ==========================================

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

# ==========================================
# ORGANIZATION METADATA ENDPOINTS
# ==========================================

@router.get("/{org_id}/metadata")
async def get_organization_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get organization metadata for reporting.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if user has access to this organization
        if current_user.organization_id != org_id and not current_user.is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this organization's data"
            )
        
        # Check if organization exists
        org_check = supabase.from_('organizations') \
            .select('id') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        if not org_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # ✅ Try to get metadata - handle if table doesn't exist
        try:
            result = supabase.from_('organization_metadata') \
                .select('*') \
                .eq('organization_id', org_id) \
                .maybe_single() \
                .execute()
            
            # ✅ Check if result exists and has data
            if result and result.data:
                return {
                    "success": True,
                    "data": result.data
                }
                
        except Exception as table_error:
            print(f"⚠️ Table error (likely table doesn't exist): {table_error}")
            # Fall through to return empty metadata
        
        # ✅ Return empty metadata if no data found or table doesn't exist
        return {
            "success": True,
            "data": {
                "organization_id": org_id,
                "total_employees": 0,
                "full_time_employees": 0,
                "part_time_employees": 0,
                "contract_employees": 0,
                "average_employees": 0,
                "annual_revenue": 0,
                "ebitda": 0,
                "total_assets": 0,
                "total_facilities": 0,
                "total_floor_area_sqft": 0,
                "occupied_floor_area_sqft": 0,
                "renewable_energy_percentage": 0,
                "carbon_offset_percentage": 0,
                "energy_intensity": 0,
                "reporting_standard": "SECR",
                "fiscal_year_start": f"{datetime.now().year}-04-01",
                "fiscal_year_end": f"{datetime.now().year + 1}-03-31",
                "primary_contact_name": "",
                "primary_contact_email": "",
                "primary_contact_phone": "",
                "sustainability_officer_name": "",
                "sustainability_officer_email": "",
                "industry_sector": "",
                "naics_code": "",
                "sic_code": "",
                "custom_metrics": {}
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error in get_organization_metadata: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization metadata: {str(e)}"
        )

@router.put("/{org_id}/metadata")
async def update_organization_metadata(
    org_id: str,
    metadata_data: OrganizationMetadataUpdate,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Update organization metadata for reporting.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if user has access to this organization
        if current_user.organization_id != org_id and not current_user.is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this organization's data"
            )
        
        # Check if organization exists
        org_check = supabase.from_('organizations') \
            .select('id') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        if not org_check.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization not found"
            )
        
        # Build update dict (remove None values)
        update_dict = {k: v for k, v in metadata_data.dict().items() if v is not None}
        update_dict['updated_at'] = datetime.now().isoformat()
        update_dict['updated_by'] = current_user.user_id
        
        if not update_dict:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        try:
            # Check if metadata exists
            existing = supabase.from_('organization_metadata') \
                .select('id') \
                .eq('organization_id', org_id) \
                .maybe_single() \
                .execute()
            
            if existing and existing.data:
                # Update existing
                result = supabase.from_('organization_metadata') \
                    .update(update_dict) \
                    .eq('organization_id', org_id) \
                    .execute()
            else:
                # Create new
                update_dict['organization_id'] = org_id
                update_dict['created_at'] = datetime.now().isoformat()
                result = supabase.from_('organization_metadata') \
                    .insert(update_dict) \
                    .execute()
                    
        except Exception as table_error:
            # Table might not exist - create it and retry
            print(f"⚠️ Table error, creating metadata: {table_error}")
            
            # Insert directly - table should exist now
            update_dict['organization_id'] = org_id
            update_dict['created_at'] = datetime.now().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(update_dict) \
                .execute()
        
        # Fetch the updated/created record
        final_result = supabase.from_('organization_metadata') \
            .select('*') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {
            "success": True,
            "message": "Organization metadata updated successfully",
            "data": final_result.data if final_result and final_result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating organization metadata: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update organization metadata: {str(e)}"
        )
