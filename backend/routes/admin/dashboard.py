# backend/routes/admin/dashboard.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta, date
from supabase import Client
import json

from auth import AuthUser, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/dashboard", tags=["Admin Dashboard"])


# ================================
# PYDANTIC MODELS
# ================================

class OverallStatsResponse(BaseModel):
    """Response model for overall admin statistics."""
    total_organizations: int
    total_users: int
    total_documents: int
    total_emissions: float
    total_reviews_completed: int
    pending_reviews: int
    staff_count: int
    active_staff: int
    approval_rate: float
    avg_review_time_minutes: float
    organizations_with_activity: int
    documents_this_month: int
    revenue_metrics: Optional[Dict[str, Any]]


class DocumentOverviewResponse(BaseModel):
    """Response model for document overview."""
    total_documents: int
    by_status: Dict[str, int]
    by_organization: List[Dict[str, Any]]
    by_type: Dict[str, int]
    by_month: List[Dict[str, Any]]
    documents_today: int
    documents_this_week: int
    documents_this_month: int
    growth_rate: float


class StaffPerformanceResponse(BaseModel):
    """Response model for staff performance."""
    staff_id: str
    staff_name: str
    email: str
    role: str
    reviews_assigned: int
    reviews_completed: int
    avg_review_time_seconds: Optional[int]
    accuracy_rate: float
    current_load: int
    total_review_time_seconds: Optional[int]
    extraction_count: int
    is_active: bool


class OrganizationHealthResponse(BaseModel):
    """Response model for organization health."""
    organization_id: str
    organization_name: str
    member_count: int
    document_count: int
    emissions_total: float
    last_activity: Optional[datetime]
    health_score: float
    status: str
    subscription_tier: Optional[str]
    created_at: datetime


class SLAComplianceResponse(BaseModel):
    """Response model for SLA compliance."""
    sla_breached_count: int
    sla_met_count: int
    compliance_rate: float
    avg_response_time_hours: float
    avg_resolution_time_hours: float
    breaches_by_priority: Dict[str, int]
    breaches_by_organization: List[Dict[str, Any]]
    sla_trend: List[Dict[str, Any]]


class SystemHealthResponse(BaseModel):
    """Response model for system health."""
    total_users: int
    active_users_today: int
    active_users_this_week: int
    storage_used_bytes: int
    storage_limit_bytes: int
    storage_usage_percentage: float
    api_requests_today: int
    api_requests_this_week: int
    error_rate: float
    avg_response_time_ms: float
    queue_size: int
    processing_backlog: int
    uptime_percentage: float


class QueueOverviewResponse(BaseModel):
    """Response model for queue overview."""
    total_in_queue: int
    pending_count: int
    assigned_count: int
    in_progress_count: int
    completed_today: int
    avg_wait_time_hours: float
    by_priority: Dict[str, int]
    by_organization: List[Dict[str, Any]]
    oldest_item_age_hours: Optional[float]
    staff_workload: List[Dict[str, Any]]


class ExportDashboardDataResponse(BaseModel):
    """Response model for dashboard data export."""
    export_id: str
    format: str
    file_url: str
    expires_at: datetime
    record_count: int
    data_preview: Optional[List[Dict[str, Any]]]


# ================================
# ENDPOINTS
# ================================

@router.get("/stats", response_model=OverallStatsResponse)
async def get_overall_stats(
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get overall admin dashboard statistics."""
    try:
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        # Get organizations count
        orgs_result = supabase.from_('organizations') \
            .select('id', count='exact') \
            .execute()
        total_organizations = orgs_result.count if hasattr(orgs_result, 'count') else 0
        
        # Get users count (from organization_members distinct)
        users_result = supabase.from_('organization_members') \
            .select('user_id', count='exact') \
            .execute()
        total_users = users_result.count if hasattr(users_result, 'count') else 0
        
        # Get documents count
        docs_result = supabase.from_('customer_documents') \
            .select('id', count='exact') \
            .execute()
        total_documents = docs_result.count if hasattr(docs_result, 'count') else 0
        
        # Get documents this month
        docs_month_result = supabase.from_('customer_documents') \
            .select('id', count='exact') \
            .gte('created_at', month_start.isoformat()) \
            .execute()
        documents_this_month = docs_month_result.count if hasattr(docs_month_result, 'count') else 0
        
        # Get emissions
        emissions_result = supabase.from_('emissions_logs') \
            .select('calculated_kg_co2e') \
            .execute()
        emissions = emissions_result.data or []
        total_emissions = sum(e.get('calculated_kg_co2e', 0) for e in emissions)
        
        # Get review stats from manual_review_queue
        reviews_result = supabase.from_('manual_review_queue') \
            .select('status', count='exact') \
            .execute()
        reviews = reviews_result.data or []
        total_reviews = len(reviews)
        pending_reviews = sum(1 for r in reviews if r.get('status') in ['pending', 'assigned'])
        
        # Get completed reviews
        completed_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('status', 'completed') \
            .execute()
        total_reviews_completed = completed_result.count if hasattr(completed_result, 'count') else 0
        
        # Get staff count from staff_profiles
        staff_result = supabase.from_('staff_profiles') \
            .select('id, is_active', count='exact') \
            .execute()
        staff = staff_result.data or []
        staff_count = len(staff)
        active_staff = sum(1 for s in staff if s.get('is_active', True))
        
        # Calculate approval rate from customer_documents
        approved_result = supabase.from_('customer_documents') \
            .select('id', count='exact') \
            .eq('status', 'approved') \
            .execute()
        rejected_result = supabase.from_('customer_documents') \
            .select('id', count='exact') \
            .eq('status', 'rejected') \
            .execute()
        
        approved = approved_result.count if hasattr(approved_result, 'count') else 0
        rejected = rejected_result.count if hasattr(rejected_result, 'count') else 0
        total_verified = approved + rejected
        approval_rate = (approved / total_verified * 100) if total_verified > 0 else 0
        
        # Get avg review time from manual_review_queue
        avg_time_result = supabase.from_('manual_review_queue') \
            .select('review_time_seconds') \
            .eq('status', 'completed') \
            .not_.is_('review_time_seconds', 'null') \
            .execute()
        
        avg_time_seconds = 0
        if avg_time_result.data:
            times = [t.get('review_time_seconds', 0) for t in avg_time_result.data if t.get('review_time_seconds')]
            if times:
                avg_time_seconds = sum(times) / len(times)
        
        avg_review_time_minutes = avg_time_seconds / 60 if avg_time_seconds else 0
        
        # Organizations with recent activity (last 30 days)
        cutoff = datetime.utcnow() - timedelta(days=30)
        active_orgs_result = supabase.from_('audit_logs') \
            .select('organization_id') \
            .gte('created_at', cutoff.isoformat()) \
            .execute()
        
        active_orgs = set()
        for log in (active_orgs_result.data or []):
            if log.get('organization_id'):
                active_orgs.add(log['organization_id'])
        organizations_with_activity = len(active_orgs)
        
        return OverallStatsResponse(
            total_organizations=total_organizations,
            total_users=total_users,
            total_documents=total_documents,
            total_emissions=round(total_emissions, 2),
            total_reviews_completed=total_reviews_completed,
            pending_reviews=pending_reviews,
            staff_count=staff_count,
            active_staff=active_staff,
            approval_rate=round(approval_rate, 2),
            avg_review_time_minutes=round(avg_review_time_minutes, 2),
            organizations_with_activity=organizations_with_activity,
            documents_this_month=documents_this_month,
            revenue_metrics=None  # Placeholder for future integration
        )
        
    except Exception as e:
        print(f"❌ Error getting overall stats: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get overall stats: {str(e)}"
        )


@router.get("/documents", response_model=DocumentOverviewResponse)
async def get_document_overview(
    current_user: AuthUser = Depends(require_admin()),
    limit: int = Query(10, ge=1, le=50, description="Number of organizations to show"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get document overview for admin dashboard."""
    try:
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = datetime(now.year, now.month, 1)
        
        # Get all documents
        docs_result = supabase.from_('customer_documents') \
            .select('id, status, file_type, created_at, organization_id, organizations(name)') \
            .execute()
        
        documents = docs_result.data or []
        total = len(documents)
        
        # Status breakdown
        status_counts = {}
        for doc in documents:
            status = doc.get('status', 'unknown')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        # By organization
        org_counts = {}
        for doc in documents:
            org_id = doc.get('organization_id')
            if org_id:
                org_name = doc.get('organizations', {}).get('name', 'Unknown') if doc.get('organizations') else 'Unknown'
                key = f"{org_id}::{org_name}"
                if key not in org_counts:
                    org_counts[key] = {'organization_id': org_id, 'organization_name': org_name, 'count': 0}
                org_counts[key]['count'] += 1
        
        by_organization = sorted(org_counts.values(), key=lambda x: x['count'], reverse=True)[:limit]
        
        # By type
        type_counts = {}
        for doc in documents:
            file_type = doc.get('file_type', 'unknown')
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        # By month (last 12 months)
        month_counts = {}
        for doc in documents:
            created_at = doc.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                key = created_at.strftime('%Y-%m')
                month_counts[key] = month_counts.get(key, 0) + 1
        
        by_month = [{'month': k, 'count': v} for k, v in sorted(month_counts.items())[-12:]]
        
        # Today, this week, this month
        docs_today = sum(1 for d in documents 
                        if d.get('created_at') and d['created_at'] >= today_start)
        docs_week = sum(1 for d in documents 
                       if d.get('created_at') and d['created_at'] >= week_start)
        docs_month = sum(1 for d in documents 
                        if d.get('created_at') and d['created_at'] >= month_start)
        
        # Growth rate (compared to previous month)
        prev_month_start = month_start - timedelta(days=month_start.day)
        docs_prev_month = sum(1 for d in documents 
                             if d.get('created_at') and 
                             prev_month_start <= d['created_at'] < month_start)
        
        growth_rate = ((docs_month - docs_prev_month) / docs_prev_month * 100) if docs_prev_month > 0 else 0
        
        return DocumentOverviewResponse(
            total_documents=total,
            by_status=status_counts,
            by_organization=by_organization,
            by_type=type_counts,
            by_month=by_month,
            documents_today=docs_today,
            documents_this_week=docs_week,
            documents_this_month=docs_month,
            growth_rate=round(growth_rate, 2)
        )
        
    except Exception as e:
        print(f"❌ Error getting document overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document overview: {str(e)}"
        )


@router.get("/staff", response_model=List[StaffPerformanceResponse])
async def get_staff_performance(
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get staff performance metrics."""
    try:
        # Get all staff profiles
        staff_result = supabase.from_('staff_profiles') \
            .select('''
                id, user_id, role, first_name, last_name, email, is_active,
                extraction_count, accuracy_rate, total_reviews_completed,
                avg_review_time_seconds, total_review_time_seconds,
                current_load, reviews_assigned, reviews_completed
            ''') \
            .execute()
        
        staff = staff_result.data or []
        
        performance = []
        for s in staff:
            # Get reviews assigned from manual_review_queue
            reviews_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', s['user_id']) \
                .execute()
            
            reviews_assigned = reviews_result.count if hasattr(reviews_result, 'count') else 0
            
            # Get completed reviews
            completed_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', s['user_id']) \
                .eq('status', 'completed') \
                .execute()
            
            reviews_completed = completed_result.count if hasattr(completed_result, 'count') else 0
            
            # Get current load (pending + in_progress)
            load_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', s['user_id']) \
                .in_('status', ['pending', 'in_progress', 'assigned']) \
                .execute()
            
            current_load = load_result.count if hasattr(load_result, 'count') else 0
            
            performance.append(StaffPerformanceResponse(
                staff_id=s['id'],
                staff_name=f"{s.get('first_name', '')} {s.get('last_name', '')}".strip() or 'Unknown',
                email=s.get('email', ''),
                role=s.get('role', 'staff'),
                reviews_assigned=reviews_assigned,
                reviews_completed=reviews_completed,
                avg_review_time_seconds=s.get('avg_review_time_seconds'),
                accuracy_rate=float(s.get('accuracy_rate', 0)) if s.get('accuracy_rate') else 0,
                current_load=current_load,
                total_review_time_seconds=s.get('total_review_time_seconds'),
                extraction_count=s.get('extraction_count', 0),
                is_active=s.get('is_active', True)
            ))
        
        # Sort by current load descending
        performance.sort(key=lambda x: x.current_load, reverse=True)
        
        return performance
        
    except Exception as e:
        print(f"❌ Error getting staff performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get staff performance: {str(e)}"
        )


@router.get("/organizations", response_model=List[OrganizationHealthResponse])
async def get_organization_health(
    current_user: AuthUser = Depends(require_admin()),
    limit: int = Query(20, ge=1, le=100, description="Number of organizations to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get organization health metrics."""
    try:
        # Get all organizations
        orgs_result = supabase.from_('organizations') \
            .select('id, name, created_at, subscription_tier') \
            .limit(limit) \
            .execute()
        
        organizations = orgs_result.data or []
        
        health_metrics = []
        for org in organizations:
            org_id = org['id']
            
            # Get member count
            members_result = supabase.from_('organization_members') \
                .select('id', count='exact') \
                .eq('organization_id', org_id) \
                .execute()
            member_count = members_result.count if hasattr(members_result, 'count') else 0
            
            # Get document count
            docs_result = supabase.from_('customer_documents') \
                .select('id', count='exact') \
                .eq('organization_id', org_id) \
                .execute()
            document_count = docs_result.count if hasattr(docs_result, 'count') else 0
            
            # Get emissions
            emissions_result = supabase.from_('emissions_logs') \
                .select('calculated_kg_co2e') \
                .eq('organization_id', org_id) \
                .execute()
            emissions = emissions_result.data or []
            total_emissions = sum(e.get('calculated_kg_co2e', 0) for e in emissions)
            
            # Get last activity
            activity_result = supabase.from_('audit_logs') \
                .select('created_at') \
                .eq('organization_id', org_id) \
                .order('created_at', desc=True) \
                .limit(1) \
                .execute()
            
            last_activity = activity_result.data[0]['created_at'] if activity_result.data else None
            
            # Calculate health score
            # Simple scoring: active members (30%), documents (30%), recent activity (40%)
            member_score = min(member_count / 10 * 30, 30)  # 10+ members = 30 points
            doc_score = min(document_count / 50 * 30, 30)   # 50+ docs = 30 points
            activity_score = 40 if last_activity else 0
            
            if last_activity:
                if isinstance(last_activity, str):
                    last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                days_since = (datetime.utcnow() - last_activity).days
                if days_since < 7:
                    activity_score = 40
                elif days_since < 30:
                    activity_score = 20
                else:
                    activity_score = 10
            
            health_score = member_score + doc_score + activity_score
            health_score = min(health_score, 100)
            
            # Determine status
            if health_score >= 80:
                status = 'healthy'
            elif health_score >= 50:
                status = 'warning'
            else:
                status = 'critical'
            
            health_metrics.append(OrganizationHealthResponse(
                organization_id=org_id,
                organization_name=org['name'],
                member_count=member_count,
                document_count=document_count,
                emissions_total=round(total_emissions, 2),
                last_activity=last_activity,
                health_score=round(health_score, 2),
                status=status,
                subscription_tier=org.get('subscription_tier'),
                created_at=org['created_at']
            ))
        
        # Sort by health score descending
        health_metrics.sort(key=lambda x: x.health_score, reverse=True)
        
        return health_metrics
        
    except Exception as e:
        print(f"❌ Error getting organization health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization health: {str(e)}"
        )


@router.get("/sla", response_model=SLAComplianceResponse)
async def get_sla_compliance(
    current_user: AuthUser = Depends(require_admin()),
    period_days: int = Query(30, ge=7, le=365, description="Analysis period in days"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get SLA compliance metrics."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=period_days)
        
        # Get reviews from manual_review_queue with SLA data
        reviews_result = supabase.from_('manual_review_queue') \
            .select('''
                id, status, priority, sla_deadline, sla_breached,
                created_at, completed_at, review_time_seconds,
                organization_id,
                organizations(name)
            ''') \
            .gte('created_at', cutoff.isoformat()) \
            .execute()
        
        reviews = reviews_result.data or []
        
        # Calculate SLA metrics
        breached = sum(1 for r in reviews if r.get('sla_breached', False))
        total = len(reviews) if reviews else 1
        compliance_rate = ((total - breached) / total * 100) if total > 0 else 100
        
        # Response times for completed reviews
        completed = [r for r in reviews if r.get('status') == 'completed']
        response_times = []
        resolution_times = []
        
        for r in completed:
            created_at = r.get('created_at')
            completed_at = r.get('completed_at')
            if created_at and completed_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                if isinstance(completed_at, str):
                    completed_at = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                
                response_time = (completed_at - created_at).total_seconds() / 3600
                response_times.append(response_time)
                
                if r.get('review_time_seconds'):
                    resolution_times.append(r['review_time_seconds'] / 3600)
        
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else 0
        
        # Breaches by priority
        priority_breaches = {}
        for r in reviews:
            if r.get('sla_breached', False):
                priority = r.get('priority', 1)
                key = f'priority_{priority}'
                priority_breaches[key] = priority_breaches.get(key, 0) + 1
        
        # Breaches by organization
        org_breaches = {}
        for r in reviews:
            if r.get('sla_breached', False):
                org_id = r.get('organization_id')
                if org_id:
                    org_name = r.get('organizations', {}).get('name', 'Unknown') if r.get('organizations') else 'Unknown'
                    key = f"{org_id}::{org_name}"
                    if key not in org_breaches:
                        org_breaches[key] = {'organization_id': org_id, 'organization_name': org_name, 'breaches': 0}
                    org_breaches[key]['breaches'] += 1
        
        breaches_by_organization = sorted(org_breaches.values(), key=lambda x: x['breaches'], reverse=True)[:10]
        
        # SLA trend (daily)
        trend_data = {}
        for r in reviews:
            created_at = r.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                key = created_at.strftime('%Y-%m-%d')
                if key not in trend_data:
                    trend_data[key] = {'total': 0, 'breached': 0}
                trend_data[key]['total'] += 1
                if r.get('sla_breached', False):
                    trend_data[key]['breached'] += 1
        
        sla_trend = [
            {
                'date': k,
                'total': v['total'],
                'breached': v['breached'],
                'compliance': round(((v['total'] - v['breached']) / v['total'] * 100) if v['total'] > 0 else 100, 2)
            }
            for k, v in sorted(trend_data.items())[-30:]
        ]
        
        return SLAComplianceResponse(
            sla_breached_count=breached,
            sla_met_count=total - breached,
            compliance_rate=round(compliance_rate, 2),
            avg_response_time_hours=round(avg_response_time, 2),
            avg_resolution_time_hours=round(avg_resolution_time, 2),
            breaches_by_priority=priority_breaches,
            breaches_by_organization=breaches_by_organization,
            sla_trend=sla_trend
        )
        
    except Exception as e:
        print(f"❌ Error getting SLA compliance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SLA compliance: {str(e)}"
        )


@router.get("/system", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get system health metrics."""
    try:
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_start = today_start - timedelta(days=now.weekday())
        
        # Total users
        users_result = supabase.from_('organization_members') \
            .select('user_id', count='exact') \
            .execute()
        total_users = users_result.count if hasattr(users_result, 'count') else 0
        
        # Active users today
        active_today = supabase.from_('audit_logs') \
            .select('user_id', count='exact') \
            .gte('created_at', today_start.isoformat()) \
            .execute()
        active_users_today = active_today.count if hasattr(active_today, 'count') else 0
        
        # Active users this week
        active_week = supabase.from_('audit_logs') \
            .select('user_id', count='exact') \
            .gte('created_at', week_start.isoformat()) \
            .execute()
        active_users_week = active_week.count if hasattr(active_week, 'count') else 0
        
        # Get storage usage from organization_files
        storage_result = supabase.from_('organization_files') \
            .select('size_bytes') \
            .execute()
        storage = storage_result.data or []
        storage_used = sum(s.get('size_bytes', 0) for s in storage)
        storage_limit = 50 * 1024**3  # 50 GB limit (example)
        storage_usage_percentage = (storage_used / storage_limit * 100) if storage_limit > 0 else 0
        
        # API requests (from audit_logs)
        api_today = supabase.from_('audit_logs') \
            .select('id', count='exact') \
            .gte('created_at', today_start.isoformat()) \
            .execute()
        api_requests_today = api_today.count if hasattr(api_today, 'count') else 0
        
        api_week = supabase.from_('audit_logs') \
            .select('id', count='exact') \
            .gte('created_at', week_start.isoformat()) \
            .execute()
        api_requests_week = api_week.count if hasattr(api_week, 'count') else 0
        
        # Error rate (from audit_logs with error action)
        error_result = supabase.from_('audit_logs') \
            .select('id', count='exact') \
            .eq('action_type', 'error') \
            .gte('created_at', week_start.isoformat()) \
            .execute()
        errors = error_result.count if hasattr(error_result, 'count') else 0
        error_rate = (errors / api_requests_week * 100) if api_requests_week > 0 else 0
        
        # Queue size
        queue_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .in_('status', ['pending', 'assigned', 'in_progress']) \
            .execute()
        queue_size = queue_result.count if hasattr(queue_result, 'count') else 0
        
        # Processing backlog (items in queue > 24 hours)
        backlog_cutoff = now - timedelta(hours=24)
        backlog_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .in_('status', ['pending', 'assigned', 'in_progress']) \
            .lt('created_at', backlog_cutoff.isoformat()) \
            .execute()
        processing_backlog = backlog_result.count if hasattr(backlog_result, 'count') else 0
        
        # Calculate uptime (simplified - assumes 99.9% if no errors)
        # In production, this would come from a monitoring system
        uptime_percentage = 99.9
        
        return SystemHealthResponse(
            total_users=total_users,
            active_users_today=active_users_today,
            active_users_this_week=active_users_week,
            storage_used_bytes=storage_used,
            storage_limit_bytes=storage_limit,
            storage_usage_percentage=round(storage_usage_percentage, 2),
            api_requests_today=api_requests_today,
            api_requests_this_week=api_requests_week,
            error_rate=round(error_rate, 2),
            avg_response_time_ms=0,  # Placeholder - would need APM integration
            queue_size=queue_size,
            processing_backlog=processing_backlog,
            uptime_percentage=uptime_percentage
        )
        
    except Exception as e:
        print(f"❌ Error getting system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )


@router.get("/queue", response_model=QueueOverviewResponse)
async def get_queue_overview(
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get queue overview and staff workload."""
    try:
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        
        # Get all queue items
        queue_result = supabase.from_('manual_review_queue') \
            .select('''
                id, status, priority, assigned_to, created_at, completed_at,
                organization_id, organizations(name)
            ''') \
            .execute()
        
        queue_items = queue_result.data or []
        total = len(queue_items)
        
        # Counts by status
        pending = sum(1 for q in queue_items if q.get('status') == 'pending')
        assigned = sum(1 for q in queue_items if q.get('status') == 'assigned')
        in_progress = sum(1 for q in queue_items if q.get('status') == 'in_progress')
        
        # Completed today
        completed_today = sum(1 for q in queue_items 
                             if q.get('status') == 'completed' 
                             and q.get('completed_at') 
                             and q['completed_at'] >= today_start)
        
        # By priority
        priority_counts = {}
        for q in queue_items:
            priority = q.get('priority', 1)
            key = f'priority_{priority}'
            priority_counts[key] = priority_counts.get(key, 0) + 1
        
        # By organization
        org_counts = {}
        for q in queue_items:
            org_id = q.get('organization_id')
            if org_id:
                org_name = q.get('organizations', {}).get('name', 'Unknown') if q.get('organizations') else 'Unknown'
                key = f"{org_id}::{org_name}"
                if key not in org_counts:
                    org_counts[key] = {'organization_id': org_id, 'organization_name': org_name, 'count': 0}
                org_counts[key]['count'] += 1
        
        by_organization = sorted(org_counts.values(), key=lambda x: x['count'], reverse=True)[:10]
        
        # Average wait time
        wait_times = []
        for q in queue_items:
            created_at = q.get('created_at')
            if created_at and q.get('status') in ['assigned', 'in_progress', 'completed']:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                wait_time = (now - created_at).total_seconds() / 3600
                wait_times.append(wait_time)
        
        avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
        
        # Oldest item age
        oldest_age = None
        if queue_items:
            oldest = min(q for q in queue_items if q.get('created_at'))
            if oldest.get('created_at'):
                created_at = oldest['created_at']
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                oldest_age = (now - created_at).total_seconds() / 3600
        
        # Staff workload
        staff_load = []
        staff_result = supabase.from_('staff_profiles') \
            .select('id, user_id, first_name, last_name, email') \
            .eq('is_active', True) \
            .execute()
        
        for staff in (staff_result.data or []):
            load_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', staff['user_id']) \
                .in_('status', ['pending', 'assigned', 'in_progress']) \
                .execute()
            
            load_count = load_result.count if hasattr(load_result, 'count') else 0
            
            # Get completed count
            completed_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('assigned_to', staff['user_id']) \
                .eq('status', 'completed') \
                .execute()
            
            completed_count = completed_result.count if hasattr(completed_result, 'count') else 0
            
            staff_load.append({
                'staff_id': staff['id'],
                'staff_name': f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or 'Unknown',
                'current_load': load_count,
                'completed_today': 0,  # Would need more specific query
                'capacity': 10  # Example max capacity
            })
        
        staff_load.sort(key=lambda x: x['current_load'], reverse=True)
        
        return QueueOverviewResponse(
            total_in_queue=total,
            pending_count=pending,
            assigned_count=assigned,
            in_progress_count=in_progress,
            completed_today=completed_today,
            avg_wait_time_hours=round(avg_wait_time, 2),
            by_priority=priority_counts,
            by_organization=by_organization,
            oldest_item_age_hours=round(oldest_age, 2) if oldest_age else None,
            staff_workload=staff_load
        )
        
    except Exception as e:
        print(f"❌ Error getting queue overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get queue overview: {str(e)}"
        )


@router.get("/export", response_model=ExportDashboardDataResponse)
async def export_dashboard_data(
    current_user: AuthUser = Depends(require_admin()),
    data_type: str = Query(..., regex="^(stats|documents|staff|organizations|sla|system|queue)$"),
    format: str = Query("json", regex="^(json|csv)$"),
    period_days: int = Query(30, ge=7, le=365),
    supabase: Client = Depends(get_supabase_client)
):
    """Export dashboard data in JSON or CSV format."""
    try:
        # Fetch data based on type
        data = []
        record_count = 0
        
        if data_type == 'stats':
            # Get overall stats
            stats = await get_overall_stats(current_user, supabase)
            data = [stats.dict()]
            record_count = 1
            
        elif data_type == 'documents':
            # Get document overview
            docs = await get_document_overview(current_user, supabase)
            data = docs.dict()
            record_count = len(data.get('by_organization', []))
            
        elif data_type == 'staff':
            # Get staff performance
            staff = await get_staff_performance(current_user, supabase)
            data = [s.dict() for s in staff]
            record_count = len(data)
            
        elif data_type == 'organizations':
            # Get organization health
            orgs = await get_organization_health(current_user, supabase)
            data = [o.dict() for o in orgs]
            record_count = len(data)
            
        elif data_type == 'sla':
            # Get SLA compliance
            sla = await get_sla_compliance(current_user, period_days, supabase)
            data = sla.dict()
            record_count = len(data.get('sla_trend', []))
            
        elif data_type == 'system':
            # Get system health
            system = await get_system_health(current_user, supabase)
            data = system.dict()
            record_count = 1
            
        elif data_type == 'queue':
            # Get queue overview
            queue = await get_queue_overview(current_user, supabase)
            data = queue.dict()
            record_count = len(data.get('staff_workload', []))
        
        # Generate export ID
        export_id = f"export_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{data_type}"
        
        # For demo purposes, create a fake file URL
        # In production, this would save to a storage bucket
        file_url = f"/exports/{export_id}.{format}"
        
        # Set expiry (7 days from now)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        return ExportDashboardDataResponse(
            export_id=export_id,
            format=format,
            file_url=file_url,
            expires_at=expires_at,
            record_count=record_count,
            data_preview=data[:10] if isinstance(data, list) else [data]
        )
        
    except Exception as e:
        print(f"❌ Error exporting dashboard data: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export dashboard data: {str(e)}"
        )
@router.get("/document-types")
async def get_document_type_dashboard(
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Admin dashboard for document types overview.
    """
    try:
        supabase = get_supabase_client()
        
        # Get document types with counts
        result = supabase.from_('customer_documents') \
            .select('document_type_code, status, organization_id') \
            .execute()
        
        types_result = supabase.from_('document_types') \
            .select('code, name, category, is_active') \
            .execute()
        
        type_map = {t['code']: t for t in types_result.data or []}
        
        # Build summary
        by_type = {}
        by_organization = {}
        
        for item in result.data or []:
            doc_type = item.get('document_type_code', 'unknown')
            status = item.get('status', 'pending')
            org_id = item.get('organization_id')
            
            if doc_type not in by_type:
                by_type[doc_type] = {
                    'code': doc_type,
                    'name': type_map.get(doc_type, {}).get('name', doc_type),
                    'category': type_map.get(doc_type, {}).get('category', 'unknown'),
                    'total': 0,
                    'pending': 0,
                    'extracted': 0,
                    'approved': 0,
                    'rejected': 0,
                    'unique_organizations': set()
                }
            
            by_type[doc_type]['total'] += 1
            if status in by_type[doc_type]:
                by_type[doc_type][status] += 1
            if org_id:
                by_type[doc_type]['unique_organizations'].add(org_id)
        
        # Convert sets to counts
        for doc_type in by_type.values():
            doc_type['unique_organizations'] = len(doc_type['unique_organizations'])
        
        return {
            "success": True,
            "document_types": sorted(by_type.values(), key=lambda x: x['total'], reverse=True),
            "summary": {
                "total_documents": len(result.data or []),
                "total_types": len(by_type),
                "active_types": len([t for t in types_result.data or [] if t.get('is_active')])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
# ================================
# ADDITIONAL PYDANTIC MODELS
# ================================

class AdminAlertResponse(BaseModel):
    """Response model for admin dashboard alerts."""
    id: str
    type: str
    severity: str
    title: str
    message: str
    link: Optional[str]
    created_at: datetime
    expires_at: Optional[datetime]
    is_resolved: bool
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    resolved_by_name: Optional[str]
    metadata: Optional[Dict[str, Any]]
    category: str  # system, security, sla, performance, user, document


class AdminAlertSummaryResponse(BaseModel):
    """Response model for admin alert summary."""
    total: int
    critical: int
    high: int
    medium: int
    low: int
    by_category: Dict[str, int]
    unresolved_count: int
    resolved_today: int


# ================================
# NEW ENDPOINT
# ================================

@router.get("/alerts", response_model=List[AdminAlertResponse])
async def get_admin_alerts(
    current_user: AuthUser = Depends(require_admin()),
    severity: Optional[str] = Query(None, description="Filter by severity: critical, high, medium, low"),
    category: Optional[str] = Query(None, description="Filter by category: system, security, sla, performance, user, document"),
    include_resolved: bool = Query(False, description="Include resolved alerts"),
    limit: int = Query(50, ge=1, le=200, description="Number of alerts to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get admin dashboard alerts.
    
    Returns system-wide alerts including SLA breaches, security events, 
    system health issues, and critical notifications.
    """
    try:
        alerts = []
        now = datetime.utcnow()
        
        # 1. SLA Breach Alerts
        sla_result = supabase.from_('manual_review_queue') \
            .select('''
                id, sla_breached, sla_deadline, priority, 
                created_at, assigned_to, organization_id,
                organizations(name),
                staff_profiles!assigned_to(first_name, last_name, email)
            ''') \
            .eq('sla_breached', True) \
            .order('sla_deadline', desc=True) \
            .limit(limit) \
            .execute()
        
        for item in (sla_result.data or []):
            org_name = item.get('organizations', {}).get('name', 'Unknown') if item.get('organizations') else 'Unknown'
            staff = item.get('staff_profiles', {}) if item.get('staff_profiles') else {}
            staff_name = f"{staff.get('first_name', '')} {staff.get('last_name', '')}".strip() or 'Unassigned'
            
            # Determine severity based on priority and time overdue
            priority = item.get('priority', 1)
            if priority >= 4:
                severity_level = 'critical'
            elif priority >= 3:
                severity_level = 'high'
            elif priority >= 2:
                severity_level = 'medium'
            else:
                severity_level = 'low'
            
            # Check if already resolved (if there's a resolution)
            is_resolved = False
            resolved_at = None
            resolved_by = None
            
            # Check if there's a resolution note
            if item.get('metadata') and isinstance(item.get('metadata'), dict):
                metadata = item['metadata']
                is_resolved = metadata.get('resolved', False)
                resolved_at = metadata.get('resolved_at')
                resolved_by = metadata.get('resolved_by')
            
            alerts.append(AdminAlertResponse(
                id=f"sla_{item['id']}",
                type='sla_breach',
                severity=severity_level,
                title=f"SLA Breach - Priority {priority}",
                message=f"SLA deadline breached for review #{item['id'][:8]} in {org_name}. Assigned to {staff_name}.",
                link=f"/admin/reviews/{item['id']}",
                created_at=item.get('created_at', now),
                expires_at=item.get('sla_deadline'),
                is_resolved=is_resolved,
                resolved_at=resolved_at,
                resolved_by=resolved_by,
                resolved_by_name=None,
                metadata={
                    'review_id': item['id'],
                    'priority': priority,
                    'organization_id': item.get('organization_id'),
                    'organization_name': org_name,
                    'assigned_to': item.get('assigned_to'),
                    'assigned_to_name': staff_name,
                    'sla_deadline': item.get('sla_deadline')
                },
                category='sla'
            ))
        
        # 2. System Health Alerts
        # Check for system issues (from audit logs with errors)
        error_result = supabase.from_('audit_logs') \
            .select('id, action_type, description, created_at, metadata') \
            .eq('action_type', 'error') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        for error in (error_result.data or []):
            # Check if this error is still relevant (within last hour)
            error_time = error.get('created_at')
            if isinstance(error_time, str):
                error_time = datetime.fromisoformat(error_time.replace('Z', '+00:00'))
            
            if error_time and (now - error_time) > timedelta(hours=1):
                continue
            
            metadata = error.get('metadata', {})
            is_resolved = metadata.get('resolved', False)
            
            alerts.append(AdminAlertResponse(
                id=f"sys_{error['id']}",
                type='system_error',
                severity='high',
                title=f"System Error: {error.get('action_type', 'unknown')}",
                message=error.get('description', 'An unexpected system error occurred'),
                link=None,
                created_at=error.get('created_at', now),
                expires_at=error_time + timedelta(hours=1) if error_time else None,
                is_resolved=is_resolved,
                resolved_at=metadata.get('resolved_at'),
                resolved_by=metadata.get('resolved_by'),
                resolved_by_name=None,
                metadata=error.get('metadata'),
                category='system'
            ))
        
        # 3. Security Alerts
        # Check for suspicious activity
        security_result = supabase.from_('audit_logs') \
            .select('id, action, description, created_at, user_id, ip_address, metadata') \
            .eq('action_type', 'security') \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        for event in (security_result.data or []):
            metadata = event.get('metadata', {})
            is_resolved = metadata.get('resolved', False)
            
            # Get user details if available
            user_name = None
            if event.get('user_id'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', event['user_id']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_result.data.get('email')
            
            alerts.append(AdminAlertResponse(
                id=f"sec_{event['id']}",
                type='security_event',
                severity='critical' if event.get('action') in ['unauthorized_access', 'suspicious_login'] else 'high',
                title=f"Security Event: {event.get('action', 'unknown')}",
                message=event.get('description', 'Security event detected') + (f" by {user_name}" if user_name else ''),
                link=None,
                created_at=event.get('created_at', now),
                expires_at=now + timedelta(days=7),
                is_resolved=is_resolved,
                resolved_at=metadata.get('resolved_at'),
                resolved_by=metadata.get('resolved_by'),
                resolved_by_name=None,
                metadata={
                    'user_id': event.get('user_id'),
                    'user_name': user_name,
                    'ip_address': event.get('ip_address'),
                    **metadata
                },
                category='security'
            ))
        
        # 4. User Activity Alerts
        # Check for inactive users or unusual activity
        inactive_users = supabase.from_('organization_members') \
            .select('''
                user_id,
                organizations(name),
                auth_users!inner(email, raw_user_meta_data, last_sign_in_at)
            ''') \
            .execute()
        
        for member in (inactive_users.data or []):
            user = member.get('auth_users', {}) if member.get('auth_users') else {}
            last_sign_in = user.get('last_sign_in_at')
            
            if last_sign_in:
                if isinstance(last_sign_in, str):
                    last_sign_in = datetime.fromisoformat(last_sign_in.replace('Z', '+00:00'))
                
                # Alert if user hasn't signed in for 30+ days
                if last_sign_in and (now - last_sign_in) > timedelta(days=30):
                    org_name = member.get('organizations', {}).get('name', 'Unknown') if member.get('organizations') else 'Unknown'
                    user_name = None
                    raw_meta = user.get('raw_user_meta_data', {})
                    user_name = raw_meta.get('full_name') or raw_meta.get('name') or user.get('email')
                    
                    days_inactive = (now - last_sign_in).days
                    
                    alerts.append(AdminAlertResponse(
                        id=f"inactive_{member['user_id']}",
                        type='inactive_user',
                        severity='low' if days_inactive < 60 else 'medium',
                        title=f"Inactive User: {user_name}",
                        message=f"User has been inactive for {days_inactive} days in {org_name}",
                        link=None,
                        created_at=now,
                        expires_at=now + timedelta(days=7),
                        is_resolved=False,
                        resolved_at=None,
                        resolved_by=None,
                        resolved_by_name=None,
                        metadata={
                            'user_id': member['user_id'],
                            'user_name': user_name,
                            'organization_id': member.get('organization_id'),
                            'organization_name': org_name,
                            'days_inactive': days_inactive,
                            'last_sign_in': last_sign_in.isoformat()
                        },
                        category='user'
                    ))
        
        # 5. Document Processing Alerts
        # Check for stuck documents
        stuck_docs = supabase.from_('customer_documents') \
            .select('''
                id, file_name, status, created_at, organization_id,
                organizations(name)
            ''') \
            .in_('status', ['processing', 'uploaded']) \
            .lt('created_at', (now - timedelta(hours=2)).isoformat()) \
            .limit(limit) \
            .execute()
        
        for doc in (stuck_docs.data or []):
            org_name = doc.get('organizations', {}).get('name', 'Unknown') if doc.get('organizations') else 'Unknown'
            time_stuck = (now - datetime.fromisoformat(doc['created_at'].replace('Z', '+00:00'))).total_seconds() / 3600
            
            alerts.append(AdminAlertResponse(
                id=f"doc_{doc['id']}",
                type='stuck_document',
                severity='high' if time_stuck > 12 else 'medium',
                title=f"Stuck Document: {doc.get('file_name', 'Unknown')}",
                message=f"Document has been {doc.get('status', 'processing')} for {time_stuck:.1f} hours in {org_name}",
                link=f"/admin/documents/{doc['id']}",
                created_at=doc.get('created_at', now),
                expires_at=now + timedelta(hours=12),
                is_resolved=False,
                resolved_at=None,
                resolved_by=None,
                resolved_by_name=None,
                metadata={
                    'document_id': doc['id'],
                    'file_name': doc.get('file_name'),
                    'status': doc.get('status'),
                    'organization_id': doc.get('organization_id'),
                    'organization_name': org_name,
                    'hours_stuck': round(time_stuck, 1)
                },
                category='document'
            ))
        
        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        if category:
            alerts = [a for a in alerts if a.category == category]
        
        if not include_resolved:
            alerts = [a for a in alerts if not a.is_resolved]
        
        # Sort by severity and created_at
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        alerts.sort(key=lambda x: (severity_order.get(x.severity, 4), x.created_at), reverse=False)
        
        # Apply pagination
        total = len(alerts)
        alerts = alerts[offset:offset + limit]
        
        return alerts
        
    except Exception as e:
        print(f"❌ Error getting admin alerts: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin alerts: {str(e)}"
        )


# ================================
# ADDITIONAL HELPER ENDPOINTS
# ================================

@router.get("/alerts/summary", response_model=AdminAlertSummaryResponse)
async def get_admin_alert_summary(
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get summary of admin alerts by severity and category.
    """
    try:
        # Get all alerts (simplified - reuse the logic from get_admin_alerts)
        alerts = await get_admin_alerts(
            current_user=current_user,
            include_resolved=False,
            limit=1000,
            offset=0,
            supabase=supabase
        )
        
        # Count by severity
        critical = sum(1 for a in alerts if a.severity == 'critical')
        high = sum(1 for a in alerts if a.severity == 'high')
        medium = sum(1 for a in alerts if a.severity == 'medium')
        low = sum(1 for a in alerts if a.severity == 'low')
        
        # Count by category
        by_category = {}
        for alert in alerts:
            by_category[alert.category] = by_category.get(alert.category, 0) + 1
        
        # Get resolved today count
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        resolved_today_result = supabase.from_('audit_logs') \
            .select('id', count='exact') \
            .eq('action_type', 'alert_resolved') \
            .gte('created_at', today_start.isoformat()) \
            .execute()
        
        resolved_today = resolved_today_result.count if hasattr(resolved_today_result, 'count') else 0
        
        return AdminAlertSummaryResponse(
            total=len(alerts),
            critical=critical,
            high=high,
            medium=medium,
            low=low,
            by_category=by_category,
            unresolved_count=len(alerts),
            resolved_today=resolved_today
        )
        
    except Exception as e:
        print(f"❌ Error getting admin alert summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin alert summary: {str(e)}"
        )


@router.put("/alerts/{alert_id}/resolve")
async def resolve_admin_alert(
    alert_id: str,
    notes: Optional[str] = Query(None, description="Resolution notes"),
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Resolve an admin alert.
    
    Marks the alert as resolved and logs the resolution.
    """
    try:
        now = datetime.utcnow().isoformat()
        
        # Determine alert type from ID prefix
        alert_type = alert_id.split('_')[0] if '_' in alert_id else 'unknown'
        actual_id = alert_id.split('_')[1] if '_' in alert_id else alert_id
        
        # Update the appropriate table based on alert type
        if alert_type == 'sla':
            # Update manual_review_queue metadata
            result = supabase.from_('manual_review_queue') \
                .select('metadata') \
                .eq('id', actual_id) \
                .maybe_single() \
                .execute()
            
            if result.data:
                metadata = result.data.get('metadata', {})
                metadata['resolved'] = True
                metadata['resolved_at'] = now
                metadata['resolved_by'] = current_user.id
                metadata['resolution_notes'] = notes
                
                update_result = supabase.from_('manual_review_queue') \
                    .update({'metadata': metadata}) \
                    .eq('id', actual_id) \
                    .execute()
                
                if not update_result.data:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to resolve SLA alert"
                    )
        
        elif alert_type == 'sys' or alert_type == 'sec':
            # Update audit_logs metadata
            result = supabase.from_('audit_logs') \
                .select('metadata') \
                .eq('id', actual_id) \
                .maybe_single() \
                .execute()
            
            if result.data:
                metadata = result.data.get('metadata', {})
                metadata['resolved'] = True
                metadata['resolved_at'] = now
                metadata['resolved_by'] = current_user.id
                metadata['resolution_notes'] = notes
                
                update_result = supabase.from_('audit_logs') \
                    .update({'metadata': metadata}) \
                    .eq('id', actual_id) \
                    .execute()
                
                if not update_result.data:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to resolve security/system alert"
                    )
        
        elif alert_type == 'doc':
            # Update customer_documents
            result = supabase.from_('customer_documents') \
                .select('metadata') \
                .eq('id', actual_id) \
                .maybe_single() \
                .execute()
            
            if result.data:
                metadata = result.data.get('metadata', {})
                metadata['alert_resolved'] = True
                metadata['alert_resolved_at'] = now
                metadata['alert_resolved_by'] = current_user.id
                metadata['resolution_notes'] = notes
                
                update_result = supabase.from_('customer_documents') \
                    .update({'metadata': metadata}) \
                    .eq('id', actual_id) \
                    .execute()
                
                if not update_result.data:
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Failed to resolve document alert"
                    )
        
        elif alert_type == 'inactive':
            # For inactive user alerts, send a notification or email
            # No database update needed, just mark as resolved in response
            pass
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown alert type: {alert_type}"
            )
        
        # Create audit log for resolution
        try:
            audit_data = {
                'user_id': current_user.id,
                'action_type': 'alert_resolved',
                'resource_type': 'admin_alert',
                'resource_id': alert_id,
                'action': 'resolve',
                'description': f"Resolved admin alert: {alert_id} - {notes if notes else 'No notes provided'}",
                'new_data': {'resolved_at': now, 'resolved_by': current_user.id},
                'created_at': now
            }
            supabase.from_('audit_logs').insert(audit_data).execute()
        except Exception as audit_error:
            print(f"⚠️ Error creating audit log: {audit_error}")
        
        return {
            "success": True,
            "message": "Alert resolved successfully",
            "alert_id": alert_id,
            "resolved_at": now,
            "resolved_by": current_user.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error resolving admin alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve admin alert: {str(e)}"
        )