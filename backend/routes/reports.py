# backend/routes/reports.py - Fixed version

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
import io
import pandas as pd
import traceback
import uuid  # ✅ Added missing import
from supabase import Client

from auth import AuthUser, require_auth, require_org_member, require_org_admin, require_permission, require_role, require_admin
from database import get_supabase_client

# Import from report_generator
from report_generator import (
    EnhancedSustainabilityReportGenerator,
    EnhancedReportRequest,
)
from report_generator import router as report_generator_router

# ==========================================
# ROUTER SETUP
# ==========================================
router = APIRouter(prefix="/api/reports", tags=["Reports"])

# Use the router from report_generator
router.include_router(report_generator_router)

# ==========================================
# PYDANTIC MODELS (All models remain the same)
# ==========================================

class CustomerSummaryReportResponse(BaseModel):
    organization_id: str
    organization_name: str
    report_period: Dict[str, str]
    total_documents: int
    documents_by_status: Dict[str, int]
    documents_by_type: Dict[str, int]
    verification_rate: float
    approval_rate: float
    average_verification_time_hours: float
    total_emissions: float
    emissions_by_asset: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    pending_actions: int
    staff_interactions: int

class StaffPerformanceReportResponse(BaseModel):
    staff_id: str
    staff_name: str
    email: str
    role: str
    period: Dict[str, str]
    reviews_assigned: int
    reviews_completed: int
    completion_rate: float
    average_review_time_minutes: float
    accuracy_rate: float
    total_review_time_hours: float
    workload_trend: List[Dict[str, Any]]
    quality_score: float
    efficiency_score: float
    top_performing_areas: List[str]
    areas_for_improvement: List[str]

class OrganizationComparisonReportResponse(BaseModel):
    report_period: Dict[str, str]
    organizations: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    rankings: Dict[str, List[Dict[str, Any]]]
    summary: Dict[str, Any]

class EmissionsTrendReportResponse(BaseModel):
    organization_id: str
    organization_name: str
    report_period: Dict[str, str]
    total_emissions: float
    emissions_by_period: List[Dict[str, Any]]
    emissions_by_asset: List[Dict[str, Any]]
    emissions_by_scope: Dict[str, float]
    growth_rate: float
    projections: Optional[List[Dict[str, Any]]]
    insights: List[str]
    recommendations: List[str]

class GenerateReportRequest(BaseModel):
    report_type: str
    organization_id: Optional[str] = None
    start_date: datetime
    end_date: datetime
    format: str = "json"
    include_charts: bool = False
    metrics: Optional[List[str]] = None
    filters: Optional[Dict[str, Any]] = None

class GenerateReportResponse(BaseModel):
    report_id: str
    report_type: str
    generated_at: datetime
    format: str
    file_url: Optional[str]
    data: Dict[str, Any]
    summary: Dict[str, Any]
    expires_at: datetime

class ReportScheduleCreate(BaseModel):
    report_type: str
    name: str
    frequency: str
    day_of_week: Optional[int] = None
    day_of_month: Optional[int] = None
    time: str
    organization_id: Optional[str] = None
    recipients: List[str]
    format: str = "json"
    filters: Optional[Dict[str, Any]] = None
    is_active: bool = True

class ReportScheduleResponse(BaseModel):
    id: str
    report_type: str
    name: str
    frequency: str
    day_of_week: Optional[int]
    day_of_month: Optional[int]
    time: str
    organization_id: Optional[str]
    recipients: List[str]
    format: str
    filters: Optional[Dict[str, Any]]
    is_active: bool
    next_run_at: Optional[datetime]
    last_run_at: Optional[datetime]
    last_run_status: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    created_by_name: Optional[str]

class ReportTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    report_type: str
    config: Dict[str, Any]
    filters: Optional[Dict[str, Any]] = None
    is_public: bool = False
    is_active: bool = True

class ReportTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None

class ReportTemplateResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    report_type: str
    config: Dict[str, Any]
    filters: Optional[Dict[str, Any]]
    is_public: bool
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]
    created_by: Optional[str]
    created_by_name: Optional[str]
    usage_count: int

class ReportShareCreate(BaseModel):
    report_id: str
    shared_with: List[str]
    permission: str = "view"
    expires_at: Optional[datetime] = None

class ReportShareResponse(BaseModel):
    id: str
    report_id: str
    report_name: Optional[str]
    report_type: Optional[str]
    shared_by: Optional[str]
    shared_by_name: Optional[str]
    shared_with: str
    shared_with_name: Optional[str]
    permission: str
    expires_at: Optional[datetime]
    created_at: datetime
    is_active: bool

# ==========================================
# ✅ FIXED: Helper function for organization access
# ==========================================

async def verify_org_access(supabase, org_id: str, user_id: str) -> bool:
    """Verify user has access to an organization."""
    member_check = supabase.from_('organization_members') \
        .select('id') \
        .eq('organization_id', org_id) \
        .eq('user_id', user_id) \
        .maybe_single() \
        .execute()
    
    if member_check.data:
        return True
    
    # Check if user is staff/admin
    staff_check = supabase.from_('staff_profiles') \
        .select('id') \
        .eq('user_id', user_id) \
        .in_('role', ['admin', 'staff']) \
        .maybe_single() \
        .execute()
    
    return bool(staff_check.data)

# ==========================================
# ✅ FIXED: ENDPOINTS WITH PROPER AUTH
# ==========================================

@router.get("/report_status")
async def report_service_status():
    """Check if report generation service is available."""
    return {
        "status": "operational",
        "service": "CarbonTally Report Generator",
        "version": "2.0",
        "available_reports": ["SECR", "CSRD", "ISSB", "AUDITOR_EXCEL"],
        "available_enhanced_reports": ["SECR"],
        "supported_formats": ["PDF", "Excel"],
        "timestamp": datetime.now().isoformat()
    }

# ==========================================
# DEFRA MAPPING ENDPOINTS
# ==========================================

@router.get("/defra-mapping")
async def get_defra_mapping(
    current_user: AuthUser = Depends(require_org_member())
):
    """Get the current activity type mapping for DEFRA factors."""
    mapping = {
        'Diesel': 'Diesel (DERV)',
        'Petrol': 'Petrol (Unleaded)',
        'AdBlue': 'AdBlue',
        'LPG': 'LPG',
        'CNG': 'CNG',
        'Electricity': 'UK Electricity Grid',
        'Natural Gas': 'Natural Gas',
        'Steam': 'Steam',
        'Chilled Water': 'Chilled Water',
        'Flight (Short Haul)': 'Flight (Short Haul)',
        'Flight (Long Haul)': 'Flight (Long Haul)',
        'Rail (National)': 'Rail (National)',
        'Hotel Stay': 'Hotel Stay',
        'Mixed Waste': 'Mixed Waste',
        'Recycled Waste': 'Recycled Waste',
        'Taxi': 'Taxi',
        'Bus': 'Bus',
        'Freight': 'Freight',
    }
    
    return {"status": "success", "mapping": mapping}

@router.get("/defra-factors/{reporting_year}")
async def get_defra_factors_by_year(
    reporting_year: int,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get all DEFRA factors for a specific reporting year."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('defra_conversion_factors') \
            .select('*') \
            .eq('reporting_year', reporting_year) \
            .order('activity_type') \
            .execute()
        
        return {
            "status": "success",
            "reporting_year": reporting_year,
            "factors": result.data,
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        print(f"❌ Error fetching DEFRA factors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ✅ FIXED: CUSTOMER SUMMARY REPORT
# ==========================================

@router.get("/customer/summary", response_model=CustomerSummaryReportResponse)
async def get_customer_summary_report(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    days: int = Query(90, ge=7, le=365, description="Number of days to include"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get customer summary report for an organization."""
    try:
        user_id = current_user.user_id
        
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', user_id) \
            .execute()
        
        if not orgs_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No organizations found"
            )
        
        # Determine target organization
        if organization_id:
            if organization_id not in [org['organization_id'] for org in orgs_result.data]:
                # Check if user is staff/admin
                staff_check = supabase.from_('staff_profiles') \
                    .select('id') \
                    .eq('user_id', user_id) \
                    .in_('role', ['admin', 'staff']) \
                    .maybe_single() \
                    .execute()
                
                if not staff_check.data:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have access to this organization"
                    )
            target_org_id = organization_id
        else:
            target_org_id = orgs_result.data[0]['organization_id']
        
        # ✅ Rest of the function remains the same...
        # Get organization name
        org_result = supabase.from_('organizations') \
            .select('name') \
            .eq('id', target_org_id) \
            .maybe_single() \
            .execute()
        
        org_name = org_result.data.get('name', 'Unknown') if org_result.data else 'Unknown'
        
        # Set date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get documents
        docs_result = supabase.from_('customer_documents') \
            .select('id, status, file_type, created_at, verified_at') \
            .eq('organization_id', target_org_id) \
            .gte('created_at', start_date.isoformat()) \
            .execute()
        
        documents = docs_result.data or []
        total_docs = len(documents)
        
        # Documents by status
        status_counts = {}
        for doc in documents:
            status = doc.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # Documents by type
        type_counts = {}
        for doc in documents:
            file_type = doc.get('file_type', 'unknown')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        # Verification rate
        verified = sum(1 for d in documents if d.get('status') in ['approved', 'rejected'])
        verification_rate = (verified / total_docs * 100) if total_docs > 0 else 0
        
        # Approval rate
        approved = sum(1 for d in documents if d.get('status') == 'approved')
        approval_rate = (approved / verified * 100) if verified > 0 else 0
        
        # Average verification time
        verification_times = []
        for doc in documents:
            if doc.get('verified_at') and doc.get('created_at'):
                created_at = doc['created_at']
                verified_at = doc['verified_at']
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if isinstance(verified_at, str):
                    verified_at = datetime.fromisoformat(verified_at.replace('Z', '+00:00'))
                hours = (verified_at - created_at).total_seconds() / 3600
                verification_times.append(hours)
        
        avg_verification_time = sum(verification_times) / len(verification_times) if verification_times else 0
        
        # Get emissions
        emissions_result = supabase.from_('emissions_logs') \
            .select('calculated_kg_co2e, asset_id, assets(name)') \
            .eq('organization_id', target_org_id) \
            .gte('created_at', start_date.isoformat()) \
            .execute()
        
        emissions = emissions_result.data or []
        total_emissions = sum(e.get('calculated_kg_co2e', 0) for e in emissions)
        
        # Emissions by asset
        emissions_by_asset = {}
        for e in emissions:
            asset_id = e.get('asset_id')
            if asset_id:
                asset_name = e.get('assets', {}).get('name', 'Unknown') if e.get('assets') else 'Unknown'
                if asset_id not in emissions_by_asset:
                    emissions_by_asset[asset_id] = {
                        'asset_id': asset_id,
                        'asset_name': asset_name,
                        'total_emissions': 0
                    }
                emissions_by_asset[asset_id]['total_emissions'] += e.get('calculated_kg_co2e', 0)
        
        # Recent activity
        activity_result = supabase.from_('audit_logs') \
            .select('action, description, created_at, user_id, auth_users(email, raw_user_meta_data)') \
            .eq('organization_id', target_org_id) \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        recent_activity = []
        for act in (activity_result.data or []):
            user = act.get('auth_users', {}) if act.get('auth_users') else {}
            user_name = None
            if user:
                raw_meta = user.get('raw_user_meta_data', {})
                user_name = raw_meta.get('full_name') or raw_meta.get('name') or user.get('email')
            
            recent_activity.append({
                'action': act.get('action', 'unknown'),
                'description': act.get('description', ''),
                'created_at': act['created_at'],
                'user_name': user_name
            })
        
        # Pending actions
        pending_result = supabase.from_('customer_documents') \
            .select('id', count='exact') \
            .eq('organization_id', target_org_id) \
            .in_('status', ['uploaded', 'processing', 'ready_for_review']) \
            .execute()
        pending_actions = pending_result.count if hasattr(pending_result, 'count') else 0
        
        # Staff interactions
        staff_result = supabase.from_('audit_logs') \
            .select('id', count='exact') \
            .eq('organization_id', target_org_id) \
            .eq('action_type', 'staff_interaction') \
            .gte('created_at', start_date.isoformat()) \
            .execute()
        staff_interactions = staff_result.count if hasattr(staff_result, 'count') else 0
        
        return CustomerSummaryReportResponse(
            organization_id=target_org_id,
            organization_name=org_name,
            report_period={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': str(days)
            },
            total_documents=total_docs,
            documents_by_status=status_counts,
            documents_by_type=type_counts,
            verification_rate=round(verification_rate, 2),
            approval_rate=round(approval_rate, 2),
            average_verification_time_hours=round(avg_verification_time, 2),
            total_emissions=round(total_emissions, 2),
            emissions_by_asset=list(emissions_by_asset.values()),
            recent_activity=recent_activity,
            pending_actions=pending_actions,
            staff_interactions=staff_interactions
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating customer summary report: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate customer summary report: {str(e)}"
        )

# ==========================================
# ✅ FIXED: STAFF PERFORMANCE REPORT
# ==========================================

@router.get("/admin/staff-performance", response_model=List[StaffPerformanceReportResponse])
async def get_staff_performance_report(
    current_user: AuthUser = Depends(require_admin()),
    staff_id: Optional[str] = Query(None, description="Specific staff member ID"),
    days: int = Query(30, ge=7, le=365, description="Number of days to include"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get staff performance report."""
    try:
        # ✅ Use current_user.user_id instead of current_user.id
        user_id = current_user.user_id
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get staff profiles
        query = supabase.from_('staff_profiles') \
            .select('''
                id, user_id, role, first_name, last_name, email,
                accuracy_rate, extraction_count, total_reviews_completed,
                avg_review_time_seconds, total_review_time_seconds
            ''')
        
        if staff_id:
            query = query.eq('user_id', staff_id)
        
        # ✅ For admin, get all staff; for staff, only get their own
        if not staff_id:
            is_admin = supabase.from_('staff_profiles') \
                .select('id') \
                .eq('user_id', user_id) \
                .eq('role', 'admin') \
                .maybe_single() \
                .execute()
            
            if not is_admin.data:
                query = query.eq('user_id', user_id)
        
        result = query.execute()
        staff_list = result.data or []
        
        reports = []
        for staff in staff_list:
            staff_user_id = staff.get('user_id')
            
            # Get reviews in period
            reviews_result = supabase.from_('manual_review_queue') \
                .select('''
                    id, status, created_at, completed_at, review_time_seconds,
                    priority, customer_document_id
                ''') \
                .eq('assigned_to', staff_user_id) \
                .gte('created_at', start_date.isoformat()) \
                .execute()
            
            reviews = reviews_result.data or []
            
            # Calculate metrics
            assigned = len(reviews)
            completed = sum(1 for r in reviews if r.get('status') == 'completed')
            completion_rate = (completed / assigned * 100) if assigned > 0 else 0
            
            # Average review time
            review_times = [r.get('review_time_seconds', 0) for r in reviews if r.get('review_time_seconds')]
            avg_time = sum(review_times) / len(review_times) if review_times else 0
            
            # Total review time
            total_time = sum(review_times) / 3600 if review_times else 0
            
            # Quality score (based on accuracy and completion)
            accuracy = float(staff.get('accuracy_rate', 0)) if staff.get('accuracy_rate') else 0
            quality_score = (accuracy * 0.6) + (completion_rate * 0.4)
            
            # Efficiency score
            efficiency_score = 100
            if avg_time > 0:
                efficiency_score = min(100, max(0, 100 - (avg_time / 60)))
            
            # Workload trend (last 30 days)
            workload_trend = []
            for i in range(30, 0, -1):
                day = end_date - timedelta(days=i)
                day_start = datetime(day.year, day.month, day.day)
                
                day_reviews = sum(1 for r in reviews 
                                 if r.get('created_at') and 
                                 isinstance(r['created_at'], str) and 
                                 day_start <= datetime.fromisoformat(r['created_at'].replace('Z', '+00:00')) < day_start + timedelta(days=1))
                
                workload_trend.append({
                    'date': day_start.isoformat(),
                    'reviews': day_reviews
                })
            
            # Top performing areas
            top_areas = ['Document Verification', 'Data Extraction', 'Quality Review']
            areas_for_improvement = ['Processing Speed', 'Accuracy in Complex Cases']
            
            name = f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or 'Unknown'
            
            reports.append(StaffPerformanceReportResponse(
                staff_id=staff['id'],
                staff_name=name,
                email=staff.get('email', ''),
                role=staff.get('role', 'staff'),
                period={
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': str(days)
                },
                reviews_assigned=assigned,
                reviews_completed=completed,
                completion_rate=round(completion_rate, 2),
                average_review_time_minutes=round(avg_time / 60, 2) if avg_time else 0,
                accuracy_rate=round(accuracy, 2),
                total_review_time_hours=round(total_time, 2),
                workload_trend=workload_trend,
                quality_score=round(quality_score, 2),
                efficiency_score=round(efficiency_score, 2),
                top_performing_areas=top_areas,
                areas_for_improvement=areas_for_improvement
            ))
        
        reports.sort(key=lambda x: x.completion_rate, reverse=True)
        
        return reports
        
    except Exception as e:
        print(f"❌ Error generating staff performance report: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate staff performance report: {str(e)}"
        )

# ==========================================
# ✅ FIXED: ORGANIZATION COMPARISON REPORT
# ==========================================

@router.get("/admin/organization-comparison", response_model=OrganizationComparisonReportResponse)
async def get_organization_comparison_report(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(90, ge=7, le=365, description="Number of days to include"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get organization comparison report. Admin only."""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get all organizations
        orgs_result = supabase.from_('organizations') \
            .select('id, name, subscription_tier, created_at') \
            .execute()
        
        organizations = orgs_result.data or []
        
        # Get metrics for each organization
        org_metrics = []
        for org in organizations:
            org_id = org['id']
            
            # Document metrics
            docs_result = supabase.from_('customer_documents') \
                .select('id, status, created_at') \
                .eq('organization_id', org_id) \
                .gte('created_at', start_date.isoformat()) \
                .execute()
            
            docs = docs_result.data or []
            total_docs = len(docs)
            
            approved = sum(1 for d in docs if d.get('status') == 'approved')
            rejected = sum(1 for d in docs if d.get('status') == 'rejected')
            pending = sum(1 for d in docs if d.get('status') in ['uploaded', 'processing', 'ready_for_review'])
            
            # Emissions
            emissions_result = supabase.from_('emissions_logs') \
                .select('calculated_kg_co2e') \
                .eq('organization_id', org_id) \
                .gte('created_at', start_date.isoformat()) \
                .execute()
            
            emissions = emissions_result.data or []
            total_emissions = sum(e.get('calculated_kg_co2e', 0) for e in emissions)
            
            # Staff interactions
            staff_result = supabase.from_('audit_logs') \
                .select('id', count='exact') \
                .eq('organization_id', org_id) \
                .eq('action_type', 'staff_interaction') \
                .gte('created_at', start_date.isoformat()) \
                .execute()
            staff_interactions = staff_result.count if hasattr(staff_result, 'count') else 0
            
            # Member count
            members_result = supabase.from_('organization_members') \
                .select('id', count='exact') \
                .eq('organization_id', org_id) \
                .execute()
            member_count = members_result.count if hasattr(members_result, 'count') else 0
            
            # Calculate scores
            engagement_score = min(100, (staff_interactions / max(1, total_docs)) * 50)
            efficiency_score = (approved / max(1, total_docs)) * 100 if total_docs > 0 else 0
            
            org_metrics.append({
                'organization_id': org_id,
                'organization_name': org['name'],
                'subscription_tier': org.get('subscription_tier', 'free'),
                'total_documents': total_docs,
                'approved_documents': approved,
                'rejected_documents': rejected,
                'pending_documents': pending,
                'approval_rate': round((approved / max(1, total_docs)) * 100, 2),
                'total_emissions': round(total_emissions, 2),
                'staff_interactions': staff_interactions,
                'member_count': member_count,
                'engagement_score': round(engagement_score, 2),
                'efficiency_score': round(efficiency_score, 2)
            })
        
        # Rankings
        rankings = {
            'documents': sorted(org_metrics, key=lambda x: x['total_documents'], reverse=True)[:5],
            'approval_rate': sorted(org_metrics, key=lambda x: x['approval_rate'], reverse=True)[:5],
            'engagement': sorted(org_metrics, key=lambda x: x['engagement_score'], reverse=True)[:5],
            'efficiency': sorted(org_metrics, key=lambda x: x['efficiency_score'], reverse=True)[:5]
        }
        
        # Summary metrics
        summary = {
            'total_organizations': len(organizations),
            'total_documents': sum(o['total_documents'] for o in org_metrics),
            'avg_approval_rate': round(sum(o['approval_rate'] for o in org_metrics) / len(org_metrics), 2) if org_metrics else 0,
            'total_emissions': sum(o['total_emissions'] for o in org_metrics),
            'avg_engagement_score': round(sum(o['engagement_score'] for o in org_metrics) / len(org_metrics), 2) if org_metrics else 0,
            'top_performer': org_metrics[0]['organization_name'] if org_metrics else 'N/A'
        }
        
        return OrganizationComparisonReportResponse(
            report_period={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': str(days)
            },
            organizations=org_metrics,
            metrics={
                'total_organizations': len(organizations),
                'total_documents': summary['total_documents'],
                'avg_approval_rate': summary['avg_approval_rate'],
                'total_emissions': summary['total_emissions']
            },
            rankings=rankings,
            summary=summary
        )
        
    except Exception as e:
        print(f"❌ Error generating organization comparison report: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate organization comparison report: {str(e)}"
        )

# ==========================================
# ✅ FIXED: EMISSIONS TREND REPORT
# ==========================================

@router.get("/emissions/trend", response_model=EmissionsTrendReportResponse)
async def get_emissions_trend_report(
    current_user: AuthUser = Depends(require_org_member()),
    organization_id: Optional[str] = Query(None, description="Organization ID"),
    months: int = Query(12, ge=3, le=36, description="Number of months to include"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get emissions trend report."""
    try:
        user_id = current_user.user_id
        
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', user_id) \
            .execute()
        
        if not orgs_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No organizations found"
            )
        
        # Determine target organization
        if organization_id:
            if organization_id not in [org['organization_id'] for org in orgs_result.data]:
                # Check if user is staff/admin
                staff_check = supabase.from_('staff_profiles') \
                    .select('id') \
                    .eq('user_id', user_id) \
                    .in_('role', ['admin', 'staff']) \
                    .maybe_single() \
                    .execute()
                
                if not staff_check.data:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="You don't have access to this organization"
                    )
            target_org_id = organization_id
        else:
            target_org_id = orgs_result.data[0]['organization_id']
        
        # Get organization name
        org_result = supabase.from_('organizations') \
            .select('name') \
            .eq('id', target_org_id) \
            .maybe_single() \
            .execute()
        
        org_name = org_result.data.get('name', 'Unknown') if org_result.data else 'Unknown'
        
        # ✅ Rest of the function remains the same...
        # Set date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=months * 30)
        
        # Get emissions
        emissions_result = supabase.from_('emissions_logs') \
            .select('''
                calculated_kg_co2e, created_at, asset_id,
                assets(name, type)
            ''') \
            .eq('organization_id', target_org_id) \
            .gte('created_at', start_date.isoformat()) \
            .order('created_at') \
            .execute()
        
        emissions = emissions_result.data or []
        
        if not emissions:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No emissions data found for this period"
            )
        
        # Total emissions
        total_emissions = sum(e.get('calculated_kg_co2e', 0) for e in emissions)
        
        # Emissions by period (monthly)
        monthly_data = {}
        for e in emissions:
            created_at = e.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                key = created_at.strftime('%Y-%m')
                if key not in monthly_data:
                    monthly_data[key] = 0
                monthly_data[key] += e.get('calculated_kg_co2e', 0)
        
        emissions_by_period = [
            {'period': k, 'emissions': v} 
            for k, v in sorted(monthly_data.items())
        ]
        
        # Emissions by asset
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
                        'total_emissions': 0
                    }
                asset_emissions[asset_id]['total_emissions'] += e.get('calculated_kg_co2e', 0)
        
        # Emissions by scope
        scope_emissions = {
            'scope_1': 0,
            'scope_2': 0,
            'scope_3': 0
        }
        
        for e in emissions:
            asset_type = e.get('assets', {}).get('type', 'unknown') if e.get('assets') else 'unknown'
            value = e.get('calculated_kg_co2e', 0)
            if asset_type in ['generator', 'vehicle', 'boiler']:
                scope_emissions['scope_1'] += value
            elif asset_type in ['electricity', 'heating']:
                scope_emissions['scope_2'] += value
            else:
                scope_emissions['scope_3'] += value
        
        # Growth rate
        emissions_by_period_sorted = sorted(monthly_data.items())
        if len(emissions_by_period_sorted) >= 6:
            recent = sum(v for _, v in emissions_by_period_sorted[-3:])
            previous = sum(v for _, v in emissions_by_period_sorted[-6:-3])
            growth_rate = ((recent - previous) / previous * 100) if previous > 0 else 0
        else:
            growth_rate = 0
        
        # Simple projections
        projections = []
        if len(emissions_by_period_sorted) >= 3:
            x = list(range(len(emissions_by_period_sorted)))
            y = [v for _, v in emissions_by_period_sorted]
            
            n = len(x)
            sum_x = sum(x)
            sum_y = sum(y)
            sum_xy = sum(x[i] * y[i] for i in range(n))
            sum_xx = sum(x[i] * x[i] for i in range(n))
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x) if n * sum_xx - sum_x * sum_x != 0 else 0
            intercept = (sum_y - slope * sum_x) / n
            
            for i in range(1, 4):
                projected = slope * (n + i) + intercept
                projections.append({
                    'period': f"Projected Month {i}",
                    'projected_emissions': max(0, round(projected, 2))
                })
        
        # Insights
        insights = []
        if growth_rate > 10:
            insights.append("Significant increase in emissions detected. Review operations for optimization opportunities.")
        elif growth_rate < -10:
            insights.append("Emissions decreasing. Continue current initiatives.")
        else:
            insights.append("Emissions relatively stable. Consider implementing new reduction strategies.")
        
        if total_emissions > 1000:
            insights.append("High total emissions. Consider carbon offset programs.")
        
        # Recommendations
        recommendations = []
        if scope_emissions['scope_1'] > scope_emissions['scope_2']:
            recommendations.append("Focus on reducing direct emissions (Scope 1) through equipment upgrades.")
        if scope_emissions['scope_2'] > 0:
            recommendations.append("Consider switching to renewable energy sources to reduce Scope 2 emissions.")
        if len(asset_emissions) > 0:
            top_asset = max(asset_emissions.values(), key=lambda x: x['total_emissions'])
            recommendations.append(f"Focus on optimizing {top_asset['asset_name']} to reduce emissions.")
        
        return EmissionsTrendReportResponse(
            organization_id=target_org_id,
            organization_name=org_name,
            report_period={
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'months': str(months)
            },
            total_emissions=round(total_emissions, 2),
            emissions_by_period=emissions_by_period,
            emissions_by_asset=list(asset_emissions.values()),
            emissions_by_scope={k: round(v, 2) for k, v in scope_emissions.items()},
            growth_rate=round(growth_rate, 2),
            projections=projections if projections else None,
            insights=insights,
            recommendations=recommendations
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating emissions trend report: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate emissions trend report: {str(e)}"
        )

# ==========================================
# GENERATE CUSTOM REPORT
# ==========================================

@router.post("/generate", response_model=GenerateReportResponse)
async def generate_custom_report(
    report_request: GenerateReportRequest,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Generate a custom report based on specified parameters."""
    try:
        user_id = current_user.user_id
        
        # Validate report type
        valid_report_types = ['summary', 'documents', 'emissions', 'staff', 'organization', 'custom']
        if report_request.report_type not in valid_report_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid report type. Must be one of: {', '.join(valid_report_types)}"
            )
        
        # Verify organization access if specified
        if report_request.organization_id:
            has_access = await verify_org_access(supabase, report_request.organization_id, user_id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this organization's data"
                )
        
        # ✅ Rest of the function remains the same...
        # Collect data based on report type
        report_data = {}
        summary = {}
        
        if report_request.report_type == 'summary':
            # Get summary data
            docs_result = supabase.from_('customer_documents') \
                .select('id, status, file_type, created_at') \
                .gte('created_at', report_request.start_date.isoformat()) \
                .lte('created_at', report_request.end_date.isoformat())
            
            if report_request.organization_id:
                docs_result = docs_result.eq('organization_id', report_request.organization_id)
            
            docs = docs_result.execute().data or []
            
            report_data = {
                'total_documents': len(docs),
                'documents_by_status': {},
                'documents_by_type': {},
                'date_range': {
                    'start': report_request.start_date.isoformat(),
                    'end': report_request.end_date.isoformat()
                }
            }
            
            for doc in docs:
                status = doc.get('status', 'unknown')
                report_data['documents_by_status'][status] = report_data['documents_by_status'].get(status, 0) + 1
                
                file_type = doc.get('file_type', 'unknown')
                report_data['documents_by_type'][file_type] = report_data['documents_by_type'].get(file_type, 0) + 1
            
            summary = {
                'total': len(docs),
                'statuses': len(report_data['documents_by_status']),
                'types': len(report_data['documents_by_type'])
            }
            
        elif report_request.report_type == 'emissions':
            # Get emissions data
            emissions_result = supabase.from_('emissions_logs') \
                .select('calculated_kg_co2e, created_at, asset_id, assets(name)') \
                .gte('created_at', report_request.start_date.isoformat()) \
                .lte('created_at', report_request.end_date.isoformat())
            
            if report_request.organization_id:
                emissions_result = emissions_result.eq('organization_id', report_request.organization_id)
            
            emissions = emissions_result.execute().data or []
            
            total_emissions = sum(e.get('calculated_kg_co2e', 0) for e in emissions)
            
            report_data = {
                'total_emissions': total_emissions,
                'emissions_count': len(emissions),
                'date_range': {
                    'start': report_request.start_date.isoformat(),
                    'end': report_request.end_date.isoformat()
                },
                'emissions_by_asset': {}
            }
            
            for e in emissions:
                asset_id = e.get('asset_id')
                if asset_id:
                    asset_name = e.get('assets', {}).get('name', 'Unknown') if e.get('assets') else 'Unknown'
                    if asset_id not in report_data['emissions_by_asset']:
                        report_data['emissions_by_asset'][asset_id] = {
                            'asset_id': asset_id,
                            'asset_name': asset_name,
                            'total_emissions': 0
                        }
                    report_data['emissions_by_asset'][asset_id]['total_emissions'] += e.get('calculated_kg_co2e', 0)
            
            summary = {
                'total_emissions': round(total_emissions, 2),
                'records': len(emissions),
                'assets': len(report_data['emissions_by_asset'])
            }
            
        else:  # custom
            # Generic data collection
            tables = ['customer_documents', 'emissions_logs', 'audit_logs']
            report_data = {}
            
            for table in tables:
                query = supabase.from_(table) \
                    .select('*') \
                    .gte('created_at', report_request.start_date.isoformat()) \
                    .lte('created_at', report_request.end_date.isoformat())
                
                if report_request.organization_id and table != 'audit_logs':
                    query = query.eq('organization_id', report_request.organization_id)
                elif report_request.organization_id and table == 'audit_logs':
                    query = query.eq('organization_id', report_request.organization_id)
                
                result = query.limit(1000).execute()
                report_data[table] = result.data or []
            
            summary = {
                'tables_included': len(report_data),
                'total_records': sum(len(v) for v in report_data.values())
            }
        
        # Generate report ID
        report_id = f"report_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Set expiry (7 days from now)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        # File URL (placeholder - would save to storage in production)
        file_url = f"/reports/{report_id}.{report_request.format}"
        
        return GenerateReportResponse(
            report_id=report_id,
            report_type=report_request.report_type,
            generated_at=datetime.utcnow(),
            format=report_request.format,
            file_url=file_url,
            data=report_data,
            summary=summary,
            expires_at=expires_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error generating custom report: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate custom report: {str(e)}"
        )

# ==========================================
# HELPER ENDPOINTS
# ==========================================

@router.get("/types")
async def get_report_types(
    current_user: AuthUser = Depends(require_org_member())
):
    """Get list of available report types."""
    return {
        "report_types": [
            {"id": "summary", "name": "Summary Report", "description": "High-level overview of documents and activity"},
            {"id": "documents", "name": "Document Report", "description": "Detailed document statistics and trends"},
            {"id": "emissions", "name": "Emissions Report", "description": "Emissions data and analysis"},
            {"id": "staff", "name": "Staff Performance", "description": "Staff productivity and efficiency metrics"},
            {"id": "organization", "name": "Organization Report", "description": "Organization-wide metrics and comparisons"},
            {"id": "custom", "name": "Custom Report", "description": "Build your own report with custom filters"}
        ]
    }


@router.get("/metrics")
async def get_available_metrics(
    current_user: AuthUser = Depends(require_org_member())
):
    """Get list of available metrics for reports."""
    return {
        "metrics": [
            {"id": "document_count", "name": "Document Count", "category": "Documents"},
            {"id": "verification_rate", "name": "Verification Rate", "category": "Documents"},
            {"id": "approval_rate", "name": "Approval Rate", "category": "Documents"},
            {"id": "total_emissions", "name": "Total Emissions", "category": "Emissions"},
            {"id": "emissions_by_asset", "name": "Emissions by Asset", "category": "Emissions"},
            {"id": "staff_completion_rate", "name": "Staff Completion Rate", "category": "Staff"},
            {"id": "avg_review_time", "name": "Average Review Time", "category": "Staff"},
            {"id": "organization_engagement", "name": "Organization Engagement", "category": "Organizations"},
            {"id": "activity_trend", "name": "Activity Trend", "category": "General"},
            {"id": "sla_compliance", "name": "SLA Compliance", "category": "General"}
        ]
    }

@router.get("/schedule/frequencies")
async def get_schedule_frequencies(
    current_user: AuthUser = Depends(require_admin())
):
    """Get available schedule frequencies."""
    return {
        "frequencies": [
            {"value": "daily", "label": "Daily"},
            {"value": "weekly", "label": "Weekly"},
            {"value": "monthly", "label": "Monthly"},
            {"value": "quarterly", "label": "Quarterly"}
        ]
    }


@router.get("/templates/categories")
async def get_template_categories(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get template categories based on report types."""
    try:
        result = supabase.from_('report_templates') \
            .select('report_type') \
            .execute()
        
        categories = list(set(
            t.get('report_type') for t in (result.data or []) 
            if t.get('report_type')
        ))
        
        return {"categories": sorted(categories)}
        
    except Exception as e:
        print(f"❌ Error getting template categories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get template categories: {str(e)}"
        )

# ==========================================
# ADMIN DEFRA IMPORT ENDPOINT
# ==========================================

@router.post("/admin/import-defra-factors")
async def import_defra_factors(
    file: UploadFile = File(...),
    reporting_year: int = Form(...),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """Admin endpoint to upload a cleaned DEFRA CSV."""
    try:
        supabase = get_supabase_client()

        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        required_cols = ['activity_type', 'co2e_multiplier']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=400, 
                detail=f"CSV must contain columns: {required_cols}"
            )
            
        df = df.dropna(subset=required_cols)
        df['reporting_year'] = reporting_year
        df['co2e_multiplier'] = df['co2e_multiplier'].astype(float)
        df['activity_type'] = df['activity_type'].str.strip()
        
        records = df[['reporting_year', 'activity_type', 'co2e_multiplier']].to_dict('records')
        
        result = supabase.from_('defra_conversion_factors').upsert(
            records, 
            on_conflict='reporting_year,activity_type'
        ).execute()
        
        return {
            "status": "success", 
            "message": f"Successfully imported/updated {len(records)} DEFRA factors for {reporting_year}",
            "records_imported": len(records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"--- DEFRA IMPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# ==========================================
# REPORT GENERATION ENDPOINT
# ==========================================

@router.post("/generate-enhanced-report")
async def generate_enhanced_sustainability_report(
    request: EnhancedReportRequest,
    current_user: AuthUser = Depends(require_org_member())
):
    """Generate an enhanced sustainability report."""
    try:
        supabase = get_supabase_client()
        
        generator = EnhancedSustainabilityReportGenerator(
            supabase, 
            request.organization_id, 
            request.reporting_year,
            request.report_type,
            request.include_narratives
        )
        
        if request.report_type == 'SECR':
            result = generator.generate_enhanced_secr_report()
        elif request.report_type == 'CSRD':
            result = generator.generate_enhanced_secr_report()
        elif request.report_type == 'ISSB':
            result = generator.generate_enhanced_secr_report()
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported report type: {request.report_type}. Supported: SECR, CSRD, ISSB"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- ENHANCED REPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Enhanced report generation failed: {str(e)}")
    # ==========================================
# REPORT SCHEDULES ENDPOINTS (Add these)
# ==========================================

@router.post("/schedule", response_model=ReportScheduleResponse)
async def create_report_schedule(
    schedule_data: ReportScheduleCreate,
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a scheduled report."""
    try:
        # Verify organization access if specified
        if schedule_data.organization_id:
            has_access = await verify_org_access(supabase, schedule_data.organization_id, current_user.user_id)
            if not has_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this organization"
                )
        
        now = datetime.utcnow().isoformat()
        
        # Calculate next run time
        next_run = calculate_next_run(
            schedule_data.frequency, 
            schedule_data.time, 
            schedule_data.day_of_week, 
            schedule_data.day_of_month
        )
        
        schedule = {
            'report_type': schedule_data.report_type,
            'name': schedule_data.name,
            'frequency': schedule_data.frequency,
            'day_of_week': schedule_data.day_of_week,
            'day_of_month': schedule_data.day_of_month,
            'time': schedule_data.time,
            'organization_id': schedule_data.organization_id,
            'recipients': schedule_data.recipients,
            'format': schedule_data.format,
            'filters': schedule_data.filters,
            'is_active': schedule_data.is_active,
            'next_run_at': next_run.isoformat() if next_run else None,
            'created_by': current_user.user_id,
            'created_at': now,
            'updated_at': now
        }
        
        result = supabase.from_('report_schedules') \
            .insert(schedule) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create report schedule"
            )
        
        # Get user name
        created_by_name = None
        user_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if user_result.data:
            raw_meta = user_result.data.get('raw_user_meta_data', {})
            created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
        
        schedule_data = result.data[0]
        
        return ReportScheduleResponse(
            id=schedule_data['id'],
            report_type=schedule_data['report_type'],
            name=schedule_data['name'],
            frequency=schedule_data['frequency'],
            day_of_week=schedule_data.get('day_of_week'),
            day_of_month=schedule_data.get('day_of_month'),
            time=schedule_data['time'],
            organization_id=schedule_data.get('organization_id'),
            recipients=schedule_data.get('recipients', []),
            format=schedule_data.get('format', 'json'),
            filters=schedule_data.get('filters'),
            is_active=schedule_data.get('is_active', True),
            next_run_at=schedule_data.get('next_run_at'),
            last_run_at=schedule_data.get('last_run_at'),
            last_run_status=schedule_data.get('last_run_status'),
            created_at=schedule_data['created_at'],
            updated_at=schedule_data.get('updated_at'),
            created_by=schedule_data.get('created_by'),
            created_by_name=created_by_name
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating report schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report schedule: {str(e)}"
        )


@router.get("/schedule", response_model=List[ReportScheduleResponse])
async def get_report_schedules(
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get all report schedules."""
    try:
        result = supabase.from_('report_schedules') \
            .select('*') \
            .order('created_at', desc=True) \
            .execute()
        
        schedules = result.data or []
        
        # Enrich with user details
        enriched_schedules = []
        for schedule in schedules:
            created_by_name = None
            if schedule.get('created_by'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', schedule['created_by']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
            
            enriched_schedules.append(ReportScheduleResponse(
                id=schedule['id'],
                report_type=schedule['report_type'],
                name=schedule['name'],
                frequency=schedule['frequency'],
                day_of_week=schedule.get('day_of_week'),
                day_of_month=schedule.get('day_of_month'),
                time=schedule['time'],
                organization_id=schedule.get('organization_id'),
                recipients=schedule.get('recipients', []),
                format=schedule.get('format', 'json'),
                filters=schedule.get('filters'),
                is_active=schedule.get('is_active', True),
                next_run_at=schedule.get('next_run_at'),
                last_run_at=schedule.get('last_run_at'),
                last_run_status=schedule.get('last_run_status'),
                created_at=schedule['created_at'],
                updated_at=schedule.get('updated_at'),
                created_by=schedule.get('created_by'),
                created_by_name=created_by_name
            ))
        
        return enriched_schedules
        
    except Exception as e:
        print(f"❌ Error getting report schedules: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report schedules: {str(e)}"
        )


@router.delete("/schedule/{schedule_id}")
async def delete_report_schedule(
    schedule_id: str,
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a report schedule."""
    try:
        # Check if schedule exists
        existing = supabase.from_('report_schedules') \
            .select('id') \
            .eq('id', schedule_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report schedule not found"
            )
        
        result = supabase.from_('report_schedules') \
            .delete() \
            .eq('id', schedule_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Report schedule deleted successfully",
            "schedule_id": schedule_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting report schedule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report schedule: {str(e)}"
        )


# ==========================================
# REPORT TEMPLATES ENDPOINTS (Add these)
# ==========================================

@router.get("/templates", response_model=List[ReportTemplateResponse])
async def get_report_templates(
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    include_public: bool = Query(True, description="Include public templates"),
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get report templates."""
    try:
        query = supabase.from_('report_templates') \
            .select('*')
        
        if report_type:
            query = query.eq('report_type', report_type)
        
        if include_public:
            query = query.or_(f'is_public.eq.true,created_by.eq.{current_user.user_id}')
        else:
            query = query.eq('created_by', current_user.user_id)
        
        result = query.order('created_at', desc=True).execute()
        
        templates = result.data or []
        
        # Enrich with user details and usage count
        enriched_templates = []
        for template in templates:
            created_by_name = None
            if template.get('created_by'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', template['created_by']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
            
            # Get usage count from metadata
            metadata = template.get('metadata', {})
            usage_count = metadata.get('usage_count', 0)
            
            enriched_templates.append(ReportTemplateResponse(
                id=template['id'],
                name=template['name'],
                description=template.get('description'),
                report_type=template['report_type'],
                config=template.get('config', {}),
                filters=template.get('filters'),
                is_public=template.get('is_public', False),
                is_active=template.get('is_active', True),
                created_at=template['created_at'],
                updated_at=template.get('updated_at'),
                created_by=template.get('created_by'),
                created_by_name=created_by_name,
                usage_count=usage_count
            ))
        
        return enriched_templates
        
    except Exception as e:
        print(f"❌ Error getting report templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get report templates: {str(e)}"
        )


@router.post("/templates", response_model=ReportTemplateResponse)
async def create_report_template(
    template_data: ReportTemplateCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Create a report template."""
    try:
        now = datetime.utcnow().isoformat()
        
        template = {
            'name': template_data.name,
            'description': template_data.description,
            'report_type': template_data.report_type,
            'config': template_data.config,
            'filters': template_data.filters,
            'is_public': template_data.is_public,
            'is_active': template_data.is_active,
            'created_by': current_user.user_id,
            'created_at': now,
            'updated_at': now,
            'metadata': {'usage_count': 0}
        }
        
        result = supabase.from_('report_templates') \
            .insert(template) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create report template"
            )
        
        # Get user name
        created_by_name = None
        user_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if user_result.data:
            raw_meta = user_result.data.get('raw_user_meta_data', {})
            created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
        
        template_data = result.data[0]
        
        return ReportTemplateResponse(
            id=template_data['id'],
            name=template_data['name'],
            description=template_data.get('description'),
            report_type=template_data['report_type'],
            config=template_data.get('config', {}),
            filters=template_data.get('filters'),
            is_public=template_data.get('is_public', False),
            is_active=template_data.get('is_active', True),
            created_at=template_data['created_at'],
            updated_at=template_data.get('updated_at'),
            created_by=template_data.get('created_by'),
            created_by_name=created_by_name,
            usage_count=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error creating report template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create report template: {str(e)}"
        )


@router.put("/templates/{template_id}", response_model=ReportTemplateResponse)
async def update_report_template(
    template_id: str,
    template_data: ReportTemplateUpdate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Update a report template."""
    try:
        # Check if template exists and user has permission
        existing = supabase.from_('report_templates') \
            .select('id, created_by, is_public') \
            .eq('id', template_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report template not found"
            )
        
        template = existing.data
        
        # Check permissions
        if template['created_by'] != current_user.user_id and not template.get('is_public', False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to update this template"
            )
        
        now = datetime.utcnow().isoformat()
        
        update_data = {'updated_at': now}
        if template_data.name is not None:
            update_data['name'] = template_data.name
        if template_data.description is not None:
            update_data['description'] = template_data.description
        if template_data.config is not None:
            update_data['config'] = template_data.config
        if template_data.filters is not None:
            update_data['filters'] = template_data.filters
        if template_data.is_public is not None:
            update_data['is_public'] = template_data.is_public
        if template_data.is_active is not None:
            update_data['is_active'] = template_data.is_active
        
        result = supabase.from_('report_templates') \
            .update(update_data) \
            .eq('id', template_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update report template"
            )
        
        # Get updated template
        updated = supabase.from_('report_templates') \
            .select('*') \
            .eq('id', template_id) \
            .maybe_single() \
            .execute()
        
        template_data = updated.data
        
        # Get user name
        created_by_name = None
        if template_data.get('created_by'):
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', template_data['created_by']) \
                .maybe_single() \
                .execute()
            
            if user_result.data:
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                created_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
        
        metadata = template_data.get('metadata', {})
        usage_count = metadata.get('usage_count', 0)
        
        return ReportTemplateResponse(
            id=template_data['id'],
            name=template_data['name'],
            description=template_data.get('description'),
            report_type=template_data['report_type'],
            config=template_data.get('config', {}),
            filters=template_data.get('filters'),
            is_public=template_data.get('is_public', False),
            is_active=template_data.get('is_active', True),
            created_at=template_data['created_at'],
            updated_at=template_data.get('updated_at'),
            created_by=template_data.get('created_by'),
            created_by_name=created_by_name,
            usage_count=usage_count
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating report template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update report template: {str(e)}"
        )


@router.delete("/templates/{template_id}")
async def delete_report_template(
    template_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Delete a report template."""
    try:
        # Check if template exists and user has permission
        existing = supabase.from_('report_templates') \
            .select('id, created_by, is_public') \
            .eq('id', template_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report template not found"
            )
        
        template = existing.data
        
        # Check permissions (only creator can delete)
        if template['created_by'] != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only the creator can delete this template"
            )
        
        result = supabase.from_('report_templates') \
            .delete() \
            .eq('id', template_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Report template deleted successfully",
            "template_id": template_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error deleting report template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete report template: {str(e)}"
        )


# ==========================================
# REPORT SHARING ENDPOINTS (Add these)
# ==========================================

@router.post("/{report_id}/share")
async def share_report(
    report_id: str,
    share_data: ReportShareCreate,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Share a report with other users."""
    try:
        # Verify report exists and user has access
        report_result = supabase.from_('report_history') \
            .select('id, organization_id, user_id, metadata') \
            .eq('id', report_id) \
            .maybe_single() \
            .execute()
        
        if not report_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        report = report_result.data
        
        # Verify user is the owner or admin
        if report.get('user_id') != current_user.user_id:
            # Check if user is staff/admin
            staff_check = supabase.from_('staff_profiles') \
                .select('id') \
                .eq('user_id', current_user.user_id) \
                .in_('role', ['admin', 'staff']) \
                .maybe_single() \
                .execute()
            
            if not staff_check.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have permission to share this report"
                )
        
        now = datetime.utcnow().isoformat()
        
        # Get existing shares or initialize
        metadata = report.get('metadata', {})
        if 'shares' not in metadata:
            metadata['shares'] = []
        
        # Add shares
        added_shares = []
        for share_with in share_data.shared_with:
            # Check if user exists
            user_result = supabase.from_('auth.users') \
                .select('id, email') \
                .eq('email', share_with) \
                .maybe_single() \
                .execute()
            
            if not user_result.data:
                # Try by ID
                user_result = supabase.from_('auth.users') \
                    .select('id, email') \
                    .eq('id', share_with) \
                    .maybe_single() \
                    .execute()
                
                if not user_result.data:
                    continue
            
            share_entry = {
                'id': str(uuid.uuid4()),
                'shared_with': user_result.data['id'],
                'permission': share_data.permission,
                'shared_by': current_user.user_id,
                'created_at': now,
                'expires_at': share_data.expires_at.isoformat() if share_data.expires_at else None
            }
            
            # Check if already shared
            existing_share = next((s for s in metadata['shares'] if s.get('shared_with') == share_entry['shared_with']), None)
            if existing_share:
                existing_share.update(share_entry)
            else:
                metadata['shares'].append(share_entry)
            
            added_shares.append(user_result.data['id'])
        
        # Update report metadata
        update_result = supabase.from_('report_history') \
            .update({
                'metadata': metadata,
                'updated_at': now
            }) \
            .eq('id', report_id) \
            .execute()
        
        if not update_result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to share report"
            )
        
        return {
            "success": True,
            "message": f"Report shared with {len(added_shares)} users",
            "report_id": report_id,
            "shared_with": added_shares,
            "permission": share_data.permission
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sharing report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to share report: {str(e)}"
        )


@router.get("/shared", response_model=List[ReportShareResponse])
async def get_shared_reports(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get reports shared with the current user."""
    try:
        # Get all report history entries
        result = supabase.from_('report_history') \
            .select('id, report_type, user_id, metadata, created_at, organization_id') \
            .execute()
        
        reports = result.data or []
        
        shared_reports = []
        for report in reports:
            metadata = report.get('metadata', {})
            shares = metadata.get('shares', [])
            
            for share in shares:
                if share.get('shared_with') == current_user.user_id:
                    # Check if expired
                    if share.get('expires_at'):
                        expires_at = datetime.fromisoformat(share['expires_at'].replace('Z', '+00:00'))
                        if expires_at < datetime.utcnow():
                            continue
                    
                    # Get shared by name
                    shared_by_name = None
                    if share.get('shared_by'):
                        user_result = supabase.from_('auth.users') \
                            .select('email, raw_user_meta_data') \
                            .eq('id', share['shared_by']) \
                            .maybe_single() \
                            .execute()
                        
                        if user_result.data:
                            raw_meta = user_result.data.get('raw_user_meta_data', {})
                            shared_by_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
                    
                    # Get report name from metadata
                    report_name = metadata.get('report_name', f"Report {report['id'][:8]}")
                    report_type = report.get('report_type', 'unknown')
                    
                    shared_reports.append(ReportShareResponse(
                        id=share.get('id', str(uuid.uuid4())),
                        report_id=report['id'],
                        report_name=report_name,
                        report_type=report_type,
                        shared_by=share.get('shared_by'),
                        shared_by_name=shared_by_name,
                        shared_with=current_user.user_id,
                        shared_with_name=None,
                        permission=share.get('permission', 'view'),
                        expires_at=share.get('expires_at'),
                        created_at=datetime.fromisoformat(share['created_at']) if share.get('created_at') else datetime.utcnow(),
                        is_active=True
                    ))
        
        return shared_reports
        
    except Exception as e:
        print(f"❌ Error getting shared reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get shared reports: {str(e)}"
        )


# ==========================================
# HELPER FUNCTION
# ==========================================

def calculate_next_run(frequency: str, time_str: str, day_of_week: Optional[int] = None, 
                       day_of_month: Optional[int] = None) -> Optional[datetime]:
    """
    Calculate the next run time for a scheduled report.
    """
    now = datetime.utcnow()
    hour, minute = map(int, time_str.split(':'))
    
    if frequency == 'daily':
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_run += timedelta(days=1)
        return next_run
    
    elif frequency == 'weekly':
        if day_of_week is None:
            return None
        days_ahead = day_of_week - now.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        next_run = now + timedelta(days=days_ahead)
        next_run = next_run.replace(hour=hour, minute=minute, second=0, microsecond=0)
        return next_run
    
    elif frequency == 'monthly':
        if day_of_month is None:
            return None
        if day_of_month > 28:
            # Handle month end
            next_month = now.replace(day=1) + timedelta(days=32)
            last_day = (next_month.replace(day=1) - timedelta(days=1)).day
            day = min(day_of_month, last_day)
        else:
            day = day_of_month
        
        next_run = now.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
        if next_run <= now:
            next_month = now.replace(day=1) + timedelta(days=32)
            next_run = next_month.replace(day=day, hour=hour, minute=minute, second=0, microsecond=0)
        return next_run
    
    elif frequency == 'quarterly':
        if day_of_month is None:
            return None
        current_quarter = (now.month - 1) // 3
        next_quarter_month = (current_quarter * 3) + 4
        if next_quarter_month > 12:
            next_quarter_month = 1
            year = now.year + 1
        else:
            year = now.year
        
        if day_of_month > 28:
            next_month = datetime(year, next_quarter_month, 1) + timedelta(days=32)
            last_day = (next_month.replace(day=1) - timedelta(days=1)).day
            day = min(day_of_month, last_day)
        else:
            day = day_of_month
        
        next_run = datetime(year, next_quarter_month, day, hour, minute, 0)
        if next_run <= now:
            next_run = datetime(year + 1, next_quarter_month, day, hour, minute, 0)
        return next_run
    
    return None