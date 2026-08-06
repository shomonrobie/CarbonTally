# backend/routes/organizations/management.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime, timedelta
from auth import AuthUser, require_role, require_permission, require_org_member, get_current_user
from database import get_supabase_client
from utils.organization_utils import get_organization_stats
from supabase import Client

router = APIRouter(prefix="/api/organizations", tags=["Organization Management"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class OrganizationCreate(BaseModel):
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

class OrganizationUpdate(BaseModel):
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

class OrganizationResponse(BaseModel):
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

class OrganizationStats(BaseModel):
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

class EmployeeMetadataUpdate(BaseModel):
    total_employees: Optional[int] = None
    full_time_employees: Optional[int] = None
    part_time_employees: Optional[int] = None
    contract_employees: Optional[int] = None
    average_employees: Optional[int] = None

class FinancialMetadataUpdate(BaseModel):
    annual_revenue: Optional[float] = None
    ebitda: Optional[float] = None
    total_assets: Optional[float] = None
    fiscal_year_start: Optional[str] = None
    fiscal_year_end: Optional[str] = None

class SustainabilityMetadataUpdate(BaseModel):
    renewable_energy_percentage: Optional[float] = None
    carbon_offset_percentage: Optional[float] = None
    energy_intensity: Optional[float] = None
    reporting_standard: Optional[str] = None

class ContactMetadataUpdate(BaseModel):
    primary_contact_name: Optional[str] = None
    primary_contact_email: Optional[str] = None
    primary_contact_phone: Optional[str] = None
    sustainability_officer_name: Optional[str] = None
    sustainability_officer_email: Optional[str] = None

class IndustryMetadataUpdate(BaseModel):
    industry_sector: Optional[str] = None
    naics_code: Optional[str] = None
    sic_code: Optional[str] = None

class CustomMetricsUpdate(BaseModel):
    custom_metrics: Optional[Dict[str, Any]] = None

class OrganizationMetadataUpdate(BaseModel):
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
# ✅ HELPER FUNCTIONS
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
# ✅ MAIN ORGANIZATION ENDPOINTS
# ==========================================

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Get a specific organization by ID. Admin only."""
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
    """Create a new organization. Admin only."""
    try:
        supabase = get_supabase_client()
        
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
    """Update an organization. Admin only."""
    try:
        supabase = get_supabase_client()
        
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
    """Delete an organization. Admin only."""
    try:
        supabase = get_supabase_client()
        
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
            members = supabase.from_('organization_members') \
                .select('id', count='exact') \
                .eq('organization_id', org_id) \
                .execute()
            
            if members.count > 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot permanently delete organization with {members.count} members"
                )
            
            supabase.from_('organizations') \
                .delete() \
                .eq('id', org_id) \
                .execute()
            message = f"Organization '{existing.data['name']}' permanently deleted"
        else:
            supabase.from_('organizations') \
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
    """Get detailed statistics for an organization. Admin only."""
    try:
        supabase = get_supabase_client()
        
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
            total_members=stats['total_members'],
            active_members=stats['active_members'],
            total_assets=stats['total_assets'],
            total_facilities=stats['total_facilities'],
            total_emissions_records=stats['total_emissions_records'],
            total_emissions_kg=stats['total_emissions_kg'],
            total_emissions_tonnes=stats['total_emissions_tonnes'],
            records_by_scope=stats['records_by_scope'],
            last_activity=stats['last_activity']
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
# ✅ ORGANIZATION METADATA ENDPOINTS (ALL)
# ==========================================

@router.get("/{org_id}/metadata/all")
async def get_all_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get all metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
        # Verify access
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
        
        result = supabase.from_('organization_metadata') \
            .select('*') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting all metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metadata: {str(e)}"
        )


@router.get("/{org_id}/metadata/employees")
async def get_employee_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get employee metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        result = supabase.from_('organization_metadata') \
            .select('total_employees, full_time_employees, part_time_employees, contract_employees, average_employees') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting employee metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get employee metadata: {str(e)}"
        )


@router.put("/{org_id}/metadata/employees")
async def update_employee_metadata(
    org_id: str,
    update_data: EmployeeMetadataUpdate,
    current_user: AuthUser = Depends(require_org_member())
):
    """Update employee metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.now().isoformat()
        data['updated_by'] = current_user.user_id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.now().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Employee metadata updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating employee metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update employee metadata: {str(e)}"
        )


@router.get("/{org_id}/metadata/financials")
async def get_financial_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get financial metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        result = supabase.from_('organization_metadata') \
            .select('annual_revenue, ebitda, total_assets, fiscal_year_start, fiscal_year_end') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting financial metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial metadata: {str(e)}"
        )


@router.put("/{org_id}/metadata/financials")
async def update_financial_metadata(
    org_id: str,
    update_data: FinancialMetadataUpdate,
    current_user: AuthUser = Depends(require_org_member())
):
    """Update financial metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.now().isoformat()
        data['updated_by'] = current_user.user_id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.now().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Financial metadata updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating financial metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update financial metadata: {str(e)}"
        )


@router.get("/{org_id}/metadata/sustainability")
async def get_sustainability_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get sustainability metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        result = supabase.from_('organization_metadata') \
            .select('renewable_energy_percentage, carbon_offset_percentage, energy_intensity, reporting_standard') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting sustainability metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sustainability metadata: {str(e)}"
        )


@router.put("/{org_id}/metadata/sustainability")
async def update_sustainability_metadata(
    org_id: str,
    update_data: SustainabilityMetadataUpdate,
    current_user: AuthUser = Depends(require_org_member())
):
    """Update sustainability metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.now().isoformat()
        data['updated_by'] = current_user.user_id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.now().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Sustainability metadata updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating sustainability metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sustainability metadata: {str(e)}"
        )


@router.get("/{org_id}/metadata/contacts")
async def get_contact_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get contact metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        result = supabase.from_('organization_metadata') \
            .select('primary_contact_name, primary_contact_email, primary_contact_phone, sustainability_officer_name, sustainability_officer_email') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting contact metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contact metadata: {str(e)}"
        )


@router.put("/{org_id}/metadata/contacts")
async def update_contact_metadata(
    org_id: str,
    update_data: ContactMetadataUpdate,
    current_user: AuthUser = Depends(require_org_member())
):
    """Update contact metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.now().isoformat()
        data['updated_by'] = current_user.user_id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.now().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Contact metadata updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating contact metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact metadata: {str(e)}"
        )


@router.get("/{org_id}/metadata/industry")
async def get_industry_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get industry metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        result = supabase.from_('organization_metadata') \
            .select('industry_sector, naics_code, sic_code') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting industry metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industry metadata: {str(e)}"
        )


@router.put("/{org_id}/metadata/industry")
async def update_industry_metadata(
    org_id: str,
    update_data: IndustryMetadataUpdate,
    current_user: AuthUser = Depends(require_org_member())
):
    """Update industry metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.now().isoformat()
        data['updated_by'] = current_user.user_id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.now().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Industry metadata updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating industry metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update industry metadata: {str(e)}"
        )


@router.get("/{org_id}/metadata/custom-metrics")
async def get_custom_metrics(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get custom metrics for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        result = supabase.from_('organization_metadata') \
            .select('custom_metrics') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data.get('custom_metrics', {}) if result.data else {}}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting custom metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get custom metrics: {str(e)}"
        )


@router.put("/{org_id}/metadata/custom-metrics")
async def update_custom_metrics(
    org_id: str,
    update_data: CustomMetricsUpdate,
    current_user: AuthUser = Depends(require_org_member())
):
    """Update custom metrics for an organization."""
    try:
        supabase = get_supabase_client()
        
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
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = {'custom_metrics': update_data.custom_metrics}
        data['updated_at'] = datetime.now().isoformat()
        data['updated_by'] = current_user.user_id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.now().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Custom metrics updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating custom metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update custom metrics: {str(e)}"
        )


# ==========================================
# ✅ METADATA VALIDATION ENDPOINTS
# ==========================================

@router.post("/{org_id}/metadata/validate")
async def validate_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Validate organization metadata completeness."""
    try:
        supabase = get_supabase_client()
        
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
        
        result = supabase.from_('organization_metadata') \
            .select('*') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            return {
                "success": True,
                "data": {
                    "is_complete": False,
                    "completeness_score": 0,
                    "missing_fields": [
                        "annual_revenue",
                        "total_employees",
                        "industry_sector",
                        "fiscal_year_end",
                        "reporting_standard"
                    ]
                }
            }
        
        metadata = result.data
        
        required_fields = [
            'annual_revenue',
            'total_employees',
            'full_time_employees',
            'industry_sector',
            'fiscal_year_end',
            'reporting_standard',
            'primary_contact_name',
            'primary_contact_email'
        ]
        
        missing_fields = []
        present_fields = 0
        
        for field in required_fields:
            if metadata.get(field) is not None and metadata.get(field) != '':
                present_fields += 1
            else:
                missing_fields.append(field)
        
        completeness_score = round((present_fields / len(required_fields)) * 100, 2)
        is_complete = completeness_score == 100
        
        return {
            "success": True,
            "data": {
                "is_complete": is_complete,
                "completeness_score": completeness_score,
                "missing_fields": missing_fields,
                "present_fields_count": present_fields,
                "total_required_fields": len(required_fields)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error validating metadata: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate metadata: {str(e)}"
        )


@router.get("/{org_id}/metadata/required-fields")
async def get_required_metadata_fields(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get list of required metadata fields."""
    try:
        supabase = get_supabase_client()
        
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
        
        required_fields = [
            {'field': 'annual_revenue', 'type': 'number', 'description': 'Annual revenue in GBP'},
            {'field': 'total_employees', 'type': 'number', 'description': 'Total number of employees'},
            {'field': 'full_time_employees', 'type': 'number', 'description': 'Number of full-time employees'},
            {'field': 'industry_sector', 'type': 'string', 'description': 'Industry sector classification'},
            {'field': 'fiscal_year_end', 'type': 'date', 'description': 'End date of fiscal year'},
            {'field': 'reporting_standard', 'type': 'string', 'description': 'Reporting standard used'},
            {'field': 'primary_contact_name', 'type': 'string', 'description': 'Primary contact person'},
            {'field': 'primary_contact_email', 'type': 'email', 'description': 'Primary contact email'}
        ]
        
        return {"success": True, "data": required_fields}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting required fields: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get required fields: {str(e)}"
        )