# backend/routes/organizations/metadata.py
"""
Organization metadata management endpoints.
Handles financial, employee, and sustainability metadata.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import date, datetime
from auth import AuthUser, require_org_admin, require_org_member
from database import get_supabase_client

router = APIRouter(prefix="/api/organizations", tags=["Organization Metadata"])

# ==========================================
# Pydantic Models
# ==========================================

class FinancialMetadataUpdate(BaseModel):
    annual_revenue: Optional[float] = None
    ebitda: Optional[float] = None
    total_assets: Optional[float] = None
    fiscal_year_start: Optional[date] = None
    fiscal_year_end: Optional[date] = None

class EmployeeMetadataUpdate(BaseModel):
    total_employees: Optional[int] = None
    full_time_employees: Optional[int] = None
    part_time_employees: Optional[int] = None
    contract_employees: Optional[int] = None
    average_employees: Optional[int] = None

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

# ==========================================
# Financial Metadata Endpoints
# ==========================================

@router.get("/{org_id}/metadata/financials")
async def get_financial_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get financial metadata for an organization."""
    try:
        supabase = get_supabase_client()
        result = supabase.from_('organization_metadata') \
            .select('annual_revenue, ebitda, total_assets, fiscal_year_start, fiscal_year_end') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get financial metadata: {str(e)}"
        )

@router.put("/{org_id}/metadata/financials")
async def update_financial_metadata(
    org_id: str,
    update_data: FinancialMetadataUpdate,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Update financial metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
        # Check if metadata exists
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.utcnow().isoformat()
        data['updated_by'] = current_user.id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.utcnow().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Financial metadata updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update financial metadata: {str(e)}"
        )

# ==========================================
# Employee Metadata Endpoints
# ==========================================

@router.get("/{org_id}/metadata/employees")
async def get_employee_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get employee metadata for an organization."""
    try:
        supabase = get_supabase_client()
        result = supabase.from_('organization_metadata') \
            .select('total_employees, full_time_employees, part_time_employees, contract_employees, average_employees') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get employee metadata: {str(e)}"
        )

@router.put("/{org_id}/metadata/employees")
async def update_employee_metadata(
    org_id: str,
    update_data: EmployeeMetadataUpdate,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Update employee metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.utcnow().isoformat()
        data['updated_by'] = current_user.id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.utcnow().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Employee metadata updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update employee metadata: {str(e)}"
        )

# ==========================================
# Sustainability Metadata Endpoints
# ==========================================

@router.get("/{org_id}/metadata/sustainability")
async def get_sustainability_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get sustainability metadata for an organization."""
    try:
        supabase = get_supabase_client()
        result = supabase.from_('organization_metadata') \
            .select('renewable_energy_percentage, carbon_offset_percentage, energy_intensity, reporting_standard') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get sustainability metadata: {str(e)}"
        )

@router.put("/{org_id}/metadata/sustainability")
async def update_sustainability_metadata(
    org_id: str,
    update_data: SustainabilityMetadataUpdate,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Update sustainability metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.utcnow().isoformat()
        data['updated_by'] = current_user.id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.utcnow().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Sustainability metadata updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update sustainability metadata: {str(e)}"
        )

# ==========================================
# Contact Metadata Endpoints
# ==========================================

@router.get("/{org_id}/metadata/contacts")
async def get_contact_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get contact metadata for an organization."""
    try:
        supabase = get_supabase_client()
        result = supabase.from_('organization_metadata') \
            .select('primary_contact_name, primary_contact_email, primary_contact_phone, sustainability_officer_name, sustainability_officer_email') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contact metadata: {str(e)}"
        )

@router.put("/{org_id}/metadata/contacts")
async def update_contact_metadata(
    org_id: str,
    update_data: ContactMetadataUpdate,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Update contact metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.utcnow().isoformat()
        data['updated_by'] = current_user.id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.utcnow().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Contact metadata updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update contact metadata: {str(e)}"
        )

# ==========================================
# Industry Metadata Endpoints
# ==========================================

@router.get("/{org_id}/metadata/industry")
async def get_industry_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get industry metadata for an organization."""
    try:
        supabase = get_supabase_client()
        result = supabase.from_('organization_metadata') \
            .select('industry_sector, naics_code, sic_code') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get industry metadata: {str(e)}"
        )

@router.put("/{org_id}/metadata/industry")
async def update_industry_metadata(
    org_id: str,
    update_data: IndustryMetadataUpdate,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Update industry metadata for an organization."""
    try:
        supabase = get_supabase_client()
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.utcnow().isoformat()
        data['updated_by'] = current_user.id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.utcnow().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Industry metadata updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update industry metadata: {str(e)}"
        )

# ==========================================
# Custom Metrics Endpoints
# ==========================================

@router.get("/{org_id}/metadata/custom-metrics")
async def get_custom_metrics(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get custom metrics for an organization."""
    try:
        supabase = get_supabase_client()
        result = supabase.from_('organization_metadata') \
            .select('custom_metrics') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data.get('custom_metrics', {}) if result.data else {}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get custom metrics: {str(e)}"
        )

@router.put("/{org_id}/metadata/custom-metrics")
async def update_custom_metrics(
    org_id: str,
    update_data: CustomMetricsUpdate,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Update custom metrics for an organization."""
    try:
        supabase = get_supabase_client()
        
        existing = supabase.from_('organization_metadata') \
            .select('id') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        data = {'custom_metrics': update_data.custom_metrics}
        data['updated_at'] = datetime.utcnow().isoformat()
        data['updated_by'] = current_user.id
        
        if existing.data:
            result = supabase.from_('organization_metadata') \
                .update(data) \
                .eq('organization_id', org_id) \
                .execute()
        else:
            data['organization_id'] = org_id
            data['created_at'] = datetime.utcnow().isoformat()
            result = supabase.from_('organization_metadata') \
                .insert(data) \
                .execute()
        
        return {"success": True, "message": "Custom metrics updated successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update custom metrics: {str(e)}"
        )

# ==========================================
# Complete Metadata Endpoints
# ==========================================

@router.get("/{org_id}/metadata/all")
async def get_all_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get all metadata for an organization."""
    try:
        supabase = get_supabase_client()
        result = supabase.from_('organization_metadata') \
            .select('*') \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        return {"success": True, "data": result.data or {}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metadata: {str(e)}"
        )
# Add to backend/routes/organizations/metadata.py

# ==========================================
# Metadata Validation
# ==========================================

@router.post("/{org_id}/metadata/validate")
async def validate_metadata(
    org_id: str,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Validate organization metadata completeness."""
    try:
        supabase = get_supabase_client()
        
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
        
        # Define required fields
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
        
        # Check which fields are present
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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate metadata: {str(e)}"
        )

@router.get("/{org_id}/metadata/required-fields")
async def get_required_metadata_fields(
    org_id: str,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Get list of required metadata fields."""
    try:
        required_fields = [
            {'field': 'annual_revenue', 'type': 'number', 'description': 'Annual revenue in USD'},
            {'field': 'total_employees', 'type': 'number', 'description': 'Total number of employees'},
            {'field': 'full_time_employees', 'type': 'number', 'description': 'Number of full-time employees'},
            {'field': 'industry_sector', 'type': 'string', 'description': 'Industry sector classification'},
            {'field': 'fiscal_year_end', 'type': 'date', 'description': 'End date of fiscal year'},
            {'field': 'reporting_standard', 'type': 'string', 'description': 'Reporting standard used'},
            {'field': 'primary_contact_name', 'type': 'string', 'description': 'Primary contact person'},
            {'field': 'primary_contact_email', 'type': 'email', 'description': 'Primary contact email'}
        ]
        
        return {"success": True, "data": required_fields}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get required fields: {str(e)}"
        )