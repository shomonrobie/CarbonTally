# backend/routes/customer_dashboard.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from supabase import Client

from auth import AuthUser, require_org_member
from database import get_supabase_client

router = APIRouter(prefix="/api/customer/dashboard", tags=["Customer Dashboard"])


# ================================
# PYDANTIC MODELS
# ================================

class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics."""
    total_documents: int = Field(..., description="Total documents")
    pending_review: int = Field(..., description="Documents pending review")
    approved_documents: int = Field(..., description="Approved documents")
    rejected_documents: int = Field(..., description="Rejected documents")
    total_assets: int = Field(..., description="Total assets")
    active_assets: int = Field(..., description="Active assets")
    total_emissions: Optional[float] = Field(None, description="Total emissions in kg CO2e")
    recent_activity_count: int = Field(..., description="Recent activities in last 7 days")


class DocumentStatusOverviewResponse(BaseModel):
    """Response model for document status overview."""
    status: str
    count: int
    percentage: float
    documents: List[Dict[str, Any]]


class AssetPerformanceResponse(BaseModel):
    """Response model for asset performance."""
    asset_id: str
    asset_name: str
    total_documents: int
    approved_documents: int
    rejected_documents: int
    pending_documents: int
    approval_rate: float
    last_upload_date: Optional[datetime]


class EmissionsOverviewResponse(BaseModel):
    """Response model for emissions overview."""
    total_emissions: float
    emissions_by_asset: List[Dict[str, Any]]
    emissions_by_period: List[Dict[str, Any]]
    total_documents_with_emissions: int
    average_emissions_per_document: float


class PendingActionResponse(BaseModel):
    """Response model for pending actions."""
    action_type: str
    count: int
    items: List[Dict[str, Any]]


class ActivityResponse(BaseModel):
    """Response model for recent activity."""
    id: str
    action_type: str
    description: str
    resource_type: str
    resource_id: Optional[str]
    created_at: datetime
    user_id: Optional[str]
    user_name: Optional[str]


class NotificationResponse(BaseModel):
    """Response model for notifications."""
    id: str
    title: str
    message: str
    type: str
    is_read: bool
    created_at: datetime
    link: Optional[str]


# ================================
# ENDPOINTS
# ================================

@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get main dashboard statistics."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return DashboardStatsResponse(
                total_documents=0,
                pending_review=0,
                approved_documents=0,
                rejected_documents=0,
                total_assets=0,
                active_assets=0,
                total_emissions=None,
                recent_activity_count=0
            )
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        # Get documents stats
        docs_result = supabase.from_('customer_documents') \
            .select('id, status, asset_id') \
            .in_('organization_id', org_ids) \
            .execute()
        
        documents = docs_result.data or []
        total_docs = len(documents)
        
        pending = sum(1 for d in documents if d.get('status') in ['uploaded', 'processing', 'ready_for_review'])
        approved = sum(1 for d in documents if d.get('status') == 'approved')
        rejected = sum(1 for d in documents if d.get('status') == 'rejected')
        
        # Get assets stats
        assets_result = supabase.from_('assets') \
            .select('id, is_active') \
            .in_('organization_id', org_ids) \
            .execute()
        
        assets = assets_result.data or []
        total_assets = len(assets)
        active_assets = sum(1 for a in assets if a.get('is_active', True))
        
        # Get emissions stats (from emissions_logs)
        emissions_result = supabase.from_('emissions_logs') \
            .select('calculated_kg_co2e') \
            .in_('organization_id', org_ids) \
            .execute()
        
        emissions = emissions_result.data or []
        total_emissions = sum(e.get('calculated_kg_co2e', 0) for e in emissions) if emissions else None
        
        # Get recent activity count (last 7 days)
        cutoff = datetime.utcnow() - timedelta(days=7)
        activity_result = supabase.from_('audit_logs') \
            .select('id', count='exact') \
            .in_('organization_id', org_ids) \
            .gte('created_at', cutoff.isoformat()) \
            .execute()
        
        recent_activity_count = activity_result.count if hasattr(activity_result, 'count') else 0
        
        return DashboardStatsResponse(
            total_documents=total_docs,
            pending_review=pending,
            approved_documents=approved,
            rejected_documents=rejected,
            total_assets=total_assets,
            active_assets=active_assets,
            total_emissions=total_emissions,
            recent_activity_count=recent_activity_count
        )
        
    except Exception as e:
        print(f"❌ Error getting dashboard stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard stats: {str(e)}"
        )


@router.get("/documents", response_model=List[DocumentStatusOverviewResponse])
async def get_document_status_overview(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get document status overview."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return []
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        # Get all documents
        docs_result = supabase.from_('customer_documents') \
            .select('''
                id, status, file_name, file_url, upload_date, created_at,
                asset_id, assets(name)
            ''') \
            .in_('organization_id', org_ids) \
            .order('created_at', desc=True) \
            .execute()
        
        documents = docs_result.data or []
        total_docs = len(documents)
        
        if total_docs == 0:
            return []
        
        # Group by status
        status_groups = {}
        for doc in documents:
            status = doc.get('status', 'unknown')
            if status not in status_groups:
                status_groups[status] = []
            status_groups[status].append({
                'id': doc['id'],
                'file_name': doc['file_name'],
                'file_url': doc['file_url'],
                'upload_date': doc.get('upload_date'),
                'created_at': doc['created_at'],
                'asset_id': doc['asset_id'],
                'asset_name': doc.get('assets', {}).get('name', 'Unknown Asset') if doc.get('assets') else 'Unknown Asset'
            })
        
        # Build response
        response = []
        for status, docs in status_groups.items():
            count = len(docs)
            percentage = (count / total_docs) * 100
            response.append(DocumentStatusOverviewResponse(
                status=status,
                count=count,
                percentage=round(percentage, 2),
                documents=docs[:10]  # Limit to 10 most recent
            ))
        
        return response
        
    except Exception as e:
        print(f"❌ Error getting document status overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get document status overview: {str(e)}"
        )


@router.get("/assets", response_model=List[AssetPerformanceResponse])
async def get_asset_performance(
    current_user: AuthUser = Depends(require_org_member()),
    limit: int = Query(10, ge=1, le=50, description="Number of assets to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get asset performance metrics."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return []
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        # Get assets
        assets_result = supabase.from_('assets') \
            .select('id, name') \
            .in_('organization_id', org_ids) \
            .eq('is_active', True) \
            .order('name') \
            .limit(limit) \
            .execute()
        
        assets = assets_result.data or []
        if not assets:
            return []
        
        asset_ids = [asset['id'] for asset in assets]
        
        # Get documents for these assets
        docs_result = supabase.from_('customer_documents') \
            .select('id, status, asset_id, upload_date') \
            .in_('asset_id', asset_ids) \
            .execute()
        
        documents = docs_result.data or []
        
        # Calculate performance per asset
        performance = []
        for asset in assets:
            asset_id = asset['id']
            asset_docs = [d for d in documents if d['asset_id'] == asset_id]
            
            total = len(asset_docs)
            approved = sum(1 for d in asset_docs if d.get('status') == 'approved')
            rejected = sum(1 for d in asset_docs if d.get('status') == 'rejected')
            pending = sum(1 for d in asset_docs if d.get('status') in ['uploaded', 'processing', 'ready_for_review'])
            
            approval_rate = (approved / total * 100) if total > 0 else 0
            
            last_upload = None
            if asset_docs:
                dates = [d.get('upload_date') for d in asset_docs if d.get('upload_date')]
                if dates:
                    last_upload = max(dates)
            
            performance.append(AssetPerformanceResponse(
                asset_id=asset_id,
                asset_name=asset['name'],
                total_documents=total,
                approved_documents=approved,
                rejected_documents=rejected,
                pending_documents=pending,
                approval_rate=round(approval_rate, 2),
                last_upload_date=last_upload
            ))
        
        # Sort by total documents descending
        performance.sort(key=lambda x: x.total_documents, reverse=True)
        
        return performance
        
    except Exception as e:
        print(f"❌ Error getting asset performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get asset performance: {str(e)}"
        )


@router.get("/emissions", response_model=EmissionsOverviewResponse)
async def get_emissions_overview(
    current_user: AuthUser = Depends(require_org_member()),
    period: str = Query("month", regex="^(week|month|quarter|year)$", description="Time period for aggregation"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get emissions overview."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return EmissionsOverviewResponse(
                total_emissions=0,
                emissions_by_asset=[],
                emissions_by_period=[],
                total_documents_with_emissions=0,
                average_emissions_per_document=0
            )
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        # Get emissions with asset info
        emissions_result = supabase.from_('emissions_logs') \
            .select('''
                id, calculated_kg_co2e, asset_id, created_at, 
                customer_document_id,
                assets(name)
            ''') \
            .in_('organization_id', org_ids) \
            .execute()
        
        emissions = emissions_result.data or []
        
        if not emissions:
            return EmissionsOverviewResponse(
                total_emissions=0,
                emissions_by_asset=[],
                emissions_by_period=[],
                total_documents_with_emissions=0,
                average_emissions_per_document=0
            )
        
        # Total emissions
        total_emissions = sum(e.get('calculated_kg_co2e', 0) for e in emissions)
        
        # Emissions by asset
        asset_emissions = {}
        for e in emissions:
            asset_id = e.get('asset_id')
            if asset_id:
                asset_name = e.get('assets', {}).get('name', 'Unknown Asset') if e.get('assets') else 'Unknown Asset'
                if asset_id not in asset_emissions:
                    asset_emissions[asset_id] = {
                        'asset_id': asset_id,
                        'asset_name': asset_name,
                        'total_emissions': 0,
                        'document_count': 0
                    }
                asset_emissions[asset_id]['total_emissions'] += e.get('calculated_kg_co2e', 0)
                if e.get('customer_document_id'):
                    asset_emissions[asset_id]['document_count'] += 1
        
        emissions_by_asset = list(asset_emissions.values())
        emissions_by_asset.sort(key=lambda x: x['total_emissions'], reverse=True)
        
        # Emissions by period
        period_groups = {}
        for e in emissions:
            created_at = e.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                
                if period == 'week':
                    key = created_at.strftime('%Y-W%W')
                elif period == 'month':
                    key = created_at.strftime('%Y-%m')
                elif period == 'quarter':
                    quarter = (created_at.month - 1) // 3 + 1
                    key = f"{created_at.year}-Q{quarter}"
                else:  # year
                    key = created_at.strftime('%Y')
                
                if key not in period_groups:
                    period_groups[key] = 0
                period_groups[key] += e.get('calculated_kg_co2e', 0)
        
        emissions_by_period = [
            {'period': k, 'emissions': v} 
            for k, v in sorted(period_groups.items())
        ]
        
        # Count documents with emissions
        doc_ids = set(e.get('customer_document_id') for e in emissions if e.get('customer_document_id'))
        total_docs_with_emissions = len(doc_ids)
        
        avg_emissions = (total_emissions / len(emissions)) if emissions else 0
        
        return EmissionsOverviewResponse(
            total_emissions=round(total_emissions, 2),
            emissions_by_asset=emissions_by_asset[:10],  # Top 10 assets
            emissions_by_period=emissions_by_period,
            total_documents_with_emissions=total_docs_with_emissions,
            average_emissions_per_document=round(avg_emissions, 2)
        )
        
    except Exception as e:
        print(f"❌ Error getting emissions overview: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get emissions overview: {str(e)}"
        )


@router.get("/pending", response_model=List[PendingActionResponse])
async def get_pending_actions(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get pending actions requiring user attention."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return []
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        pending_actions = []
        
        # 1. Pending document reviews
        pending_docs = supabase.from_('customer_documents') \
            .select('''
                id, file_name, status, upload_date, asset_id,
                assets(name)
            ''') \
            .in_('organization_id', org_ids) \
            .in_('status', ['uploaded', 'processing', 'ready_for_review']) \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        if pending_docs.data:
            docs = []
            for doc in pending_docs.data:
                docs.append({
                    'id': doc['id'],
                    'file_name': doc['file_name'],
                    'status': doc['status'],
                    'upload_date': doc.get('upload_date'),
                    'asset_name': doc.get('assets', {}).get('name', 'Unknown Asset') if doc.get('assets') else 'Unknown Asset'
                })
            
            pending_actions.append(PendingActionResponse(
                action_type='documents_pending_review',
                count=len(docs),
                items=docs
            ))
        
        # 2. Staff review requests (manual_review_queue)
        review_requests = supabase.from_('manual_review_queue') \
            .select('''
                id, priority, status, customer_notes, created_at,
                customer_document_id,
                customer_documents(file_name)
            ''') \
            .in_('organization_id', org_ids) \
            .in_('status', ['pending', 'assigned']) \
            .order('priority', desc=True) \
            .limit(10) \
            .execute()
        
        if review_requests.data:
            requests = []
            for req in review_requests.data:
                doc = req.get('customer_documents', {})
                requests.append({
                    'id': req['id'],
                    'priority': req.get('priority', 1),
                    'status': req['status'],
                    'notes': req.get('customer_notes'),
                    'created_at': req['created_at'],
                    'document_name': doc.get('file_name', 'Unknown Document') if doc else 'Unknown Document'
                })
            
            pending_actions.append(PendingActionResponse(
                action_type='staff_review_requests',
                count=len(requests),
                items=requests
            ))
        
        # 3. Unread notifications
        notifications = supabase.from_('notifications') \
            .select('id, title, message, type, created_at, link') \
            .eq('user_id', current_user.user_id) \
            .eq('is_read', False) \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        if notifications.data:
            notifs = []
            for notif in notifications.data:
                notifs.append({
                    'id': notif['id'],
                    'title': notif['title'],
                    'message': notif['message'],
                    'type': notif['type'],
                    'created_at': notif['created_at'],
                    'link': notif.get('link')
                })
            
            pending_actions.append(PendingActionResponse(
                action_type='unread_notifications',
                count=len(notifs),
                items=notifs
            ))
        
        return pending_actions
        
    except Exception as e:
        print(f"❌ Error getting pending actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get pending actions: {str(e)}"
        )


@router.get("/activity", response_model=List[ActivityResponse])
async def get_recent_activity(
    current_user: AuthUser = Depends(require_org_member()),
    limit: int = Query(20, ge=1, le=100, description="Number of activities to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get recent activity log."""
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return []
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        # Get audit logs
        activity_result = supabase.from_('audit_logs') \
            .select('''
                id, action_type, description, resource_type, 
                resource_id, created_at, user_id,
                auth_users!user_id(email, raw_user_meta_data)
            ''') \
            .in_('organization_id', org_ids) \
            .order('created_at', desc=True) \
            .limit(limit) \
            .execute()
        
        activities = activity_result.data or []
        
        response = []
        for act in activities:
            user = act.get('auth_users', {}) if act.get('auth_users') else {}
            user_name = None
            if user:
                raw_meta = user.get('raw_user_meta_data', {})
                user_name = raw_meta.get('full_name') or raw_meta.get('name') or user.get('email')
            
            response.append(ActivityResponse(
                id=act['id'],
                action_type=act.get('action_type', 'unknown'),
                description=act.get('description', ''),
                resource_type=act.get('resource_type', ''),
                resource_id=act.get('resource_id'),
                created_at=act['created_at'],
                user_id=act.get('user_id'),
                user_name=user_name
            ))
        
        return response
        
    except Exception as e:
        print(f"❌ Error getting recent activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent activity: {str(e)}"
        )


@router.get("/notifications", response_model=List[NotificationResponse])
async def get_notifications(
    current_user: AuthUser = Depends(require_org_member()),
    include_read: bool = Query(False, description="Include read notifications"),
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get unread notifications for the current user."""
    try:
        # Build query
        query = supabase.from_('notifications') \
            .select('id, title, message, type, is_read, created_at, link') \
            .eq('user_id', current_user.user_id)
        
        if not include_read:
            query = query.eq('is_read', False)
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        
        notifications = result.data or []
        
        return [
            NotificationResponse(
                id=n['id'],
                title=n['title'],
                message=n['message'],
                type=n.get('type', 'info'),
                is_read=n.get('is_read', False),
                created_at=n['created_at'],
                link=n.get('link')
            )
            for n in notifications
        ]
        
    except Exception as e:
        print(f"❌ Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notifications: {str(e)}"
        )
class DashboardTrendsResponse(BaseModel):
    """Response model for dashboard trends."""
    document_trend: List[Dict[str, Any]]
    emissions_trend: List[Dict[str, Any]]
    verification_trend: List[Dict[str, Any]]
    activity_trend: List[Dict[str, Any]]
    period: str
    summary: Dict[str, Any]


class DashboardAlertResponse(BaseModel):
    """Response model for dashboard alerts."""
    id: str
    type: str
    severity: str
    title: str
    message: str
    link: Optional[str]
    is_read: bool
    created_at: datetime
    action_required: bool
    expires_at: Optional[datetime]


# ================================
# NEW ENDPOINTS
# ================================

@router.get("/trends", response_model=DashboardTrendsResponse)
async def get_dashboard_trends(
    current_user: AuthUser = Depends(require_org_member()),
    period: str = Query("30d", regex="^(7d|30d|90d|1y)$", description="Time period: 7d, 30d, 90d, 1y"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get dashboard trends for documents, emissions, verifications, and activity.
    
    Returns trend data for the specified time period with summary statistics.
    """
    try:
        # Get user's organizations
        orgs_result = supabase.from_('organization_members') \
            .select('organization_id') \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not orgs_result.data:
            return DashboardTrendsResponse(
                document_trend=[],
                emissions_trend=[],
                verification_trend=[],
                activity_trend=[],
                period=period,
                summary={}
            )
        
        org_ids = [org['organization_id'] for org in orgs_result.data]
        
        if organization_id:
            if organization_id not in org_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this organization"
                )
            org_ids = [organization_id]
        
        # Determine date range based on period
        now = datetime.utcnow()
        if period == "7d":
            start_date = now - timedelta(days=7)
            interval = "day"
            num_points = 7
        elif period == "30d":
            start_date = now - timedelta(days=30)
            interval = "day"
            num_points = 30
        elif period == "90d":
            start_date = now - timedelta(days=90)
            interval = "week"
            num_points = 13
        else:  # 1y
            start_date = now - timedelta(days=365)
            interval = "month"
            num_points = 12
        
        start_date_str = start_date.isoformat()
        
        # 1. Document trend
        docs_result = supabase.from_('customer_documents') \
            .select('id, status, created_at') \
            .in_('organization_id', org_ids) \
            .gte('created_at', start_date_str) \
            .execute()
        
        documents = docs_result.data or []
        
        # Aggregate documents by interval
        doc_trend = aggregate_by_interval(documents, start_date, now, interval, 'created_at')
        
        # Add status breakdown for each interval
        for point in doc_trend:
            point_date = datetime.fromisoformat(point['date'])
            next_date = point_date + get_interval_delta(interval)
            
            point_docs = [d for d in documents if d.get('created_at') and 
                         point_date <= datetime.fromisoformat(d['created_at'].replace('Z', '+00:00')) < next_date]
            
            point['uploaded'] = sum(1 for d in point_docs if d.get('status') == 'uploaded')
            point['processing'] = sum(1 for d in point_docs if d.get('status') == 'processing')
            point['approved'] = sum(1 for d in point_docs if d.get('status') == 'approved')
            point['rejected'] = sum(1 for d in point_docs if d.get('status') == 'rejected')
            point['pending'] = sum(1 for d in point_docs if d.get('status') in ['uploaded', 'processing', 'ready_for_review'])
        
        # 2. Emissions trend
        emissions_result = supabase.from_('emissions_logs') \
            .select('calculated_kg_co2e, created_at') \
            .in_('organization_id', org_ids) \
            .gte('created_at', start_date_str) \
            .execute()
        
        emissions = emissions_result.data or []
        
        # Aggregate emissions by interval
        emissions_trend = aggregate_by_interval(emissions, start_date, now, interval, 'created_at', 'calculated_kg_co2e')
        
        # 3. Verification trend
        verifications_result = supabase.from_('customer_verifications') \
            .select('id, status, submitted_at, verified_at, rejected_at') \
            .in_('organization_id', org_ids) \
            .gte('created_at', start_date_str) \
            .execute()
        
        verifications = verifications_result.data or []
        
        # Aggregate verifications by interval
        verification_trend = aggregate_by_interval(verifications, start_date, now, interval, 'submitted_at')
        for point in verification_trend:
            point_date = datetime.fromisoformat(point['date'])
            next_date = point_date + get_interval_delta(interval)
            
            point_verifs = [v for v in verifications if v.get('submitted_at') and 
                           point_date <= datetime.fromisoformat(v['submitted_at'].replace('Z', '+00:00')) < next_date]
            
            point['submitted'] = len(point_verifs)
            point['verified'] = sum(1 for v in point_verifs if v.get('status') == 'verified')
            point['rejected'] = sum(1 for v in point_verifs if v.get('status') == 'rejected')
            point['revision_requested'] = sum(1 for v in point_verifs if v.get('status') == 'revision_requested')
        
        # 4. Activity trend
        activity_result = supabase.from_('audit_logs') \
            .select('id, action_type, created_at') \
            .in_('organization_id', org_ids) \
            .gte('created_at', start_date_str) \
            .execute()
        
        activities = activity_result.data or []
        
        # Aggregate activities by interval
        activity_trend = aggregate_by_interval(activities, start_date, now, interval, 'created_at')
        for point in activity_trend:
            point_date = datetime.fromisoformat(point['date'])
            next_date = point_date + get_interval_delta(interval)
            
            point_activities = [a for a in activities if a.get('created_at') and 
                               point_date <= datetime.fromisoformat(a['created_at'].replace('Z', '+00:00')) < next_date]
            
            point['total'] = len(point_activities)
            point['document_actions'] = sum(1 for a in point_activities if a.get('action_type') in ['upload', 'verify', 'approve', 'reject'])
            point['user_actions'] = sum(1 for a in point_activities if a.get('action_type') in ['login', 'logout', 'profile_update'])
            point['system_actions'] = sum(1 for a in point_activities if a.get('action_type') in ['system', 'automated'])
        
        # Calculate summary statistics
        total_documents = len(documents)
        total_emissions = sum(e.get('calculated_kg_co2e', 0) for e in emissions) if emissions else 0
        total_verifications = len(verifications)
        total_activities = len(activities)
        
        # Calculate growth rates
        doc_growth = calculate_growth_rate(doc_trend, 'count')
        emissions_growth = calculate_growth_rate(emissions_trend, 'value')
        
        summary = {
            'total_documents': total_documents,
            'total_emissions': round(total_emissions, 2),
            'total_verifications': total_verifications,
            'total_activities': total_activities,
            'document_growth_rate': round(doc_growth, 2) if doc_growth is not None else 0,
            'emissions_growth_rate': round(emissions_growth, 2) if emissions_growth is not None else 0,
            'period': period,
            'start_date': start_date.isoformat(),
            'end_date': now.isoformat()
        }
        
        return DashboardTrendsResponse(
            document_trend=doc_trend,
            emissions_trend=emissions_trend,
            verification_trend=verification_trend,
            activity_trend=activity_trend,
            period=period,
            summary=summary
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting dashboard trends: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard trends: {str(e)}"
        )


@router.get("/alerts", response_model=List[DashboardAlertResponse])
async def get_dashboard_alerts(
    current_user: AuthUser = Depends(require_org_member()),
    include_read: bool = Query(False, description="Include read alerts"),
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, error, critical"),
    limit: int = Query(20, ge=1, le=100, description="Number of alerts to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get dashboard alerts for the current user.
    
    Returns alerts including notifications and system warnings.
    """
    try:
        now = datetime.utcnow()
        alerts = []
        
        # 1. Get notifications as alerts
        query = supabase.from_('notifications') \
            .select('''
                id, title, message, type, is_read, created_at, 
                link, priority, metadata, read_at
            ''') \
            .eq('user_id', current_user.user_id)
        
        if not include_read:
            query = query.eq('is_read', False)
        
        if severity:
            # Map severity to notification priority or type
            if severity == 'critical':
                query = query.eq('priority', 'critical')
            elif severity == 'error':
                query = query.eq('priority', 'high')
            elif severity == 'warning':
                query = query.eq('priority', 'medium')
            else:  # info
                query = query.eq('priority', 'low')
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        
        notifications = result.data or []
        for notif in notifications:
            # Determine severity from priority
            priority = notif.get('priority', 'low')
            if priority == 'critical':
                severity_level = 'critical'
            elif priority == 'high':
                severity_level = 'error'
            elif priority == 'medium':
                severity_level = 'warning'
            else:
                severity_level = 'info'
            
            # Determine if action is required
            action_required = False
            if notif.get('type') in ['review_request', 'verification_pending', 'sla_breach']:
                action_required = True
            
            alerts.append(DashboardAlertResponse(
                id=notif['id'],
                type=notif.get('type', 'notification'),
                severity=severity_level,
                title=notif['title'],
                message=notif['message'],
                link=notif.get('link'),
                is_read=notif.get('is_read', False),
                created_at=notif['created_at'],
                action_required=action_required,
                expires_at=notif.get('metadata', {}).get('expires_at') if notif.get('metadata') else None
            ))
        
        # 2. Add system alerts from audit logs (e.g., SLA breaches, errors)
        if len(alerts) < limit:
            system_alerts = supabase.from_('audit_logs') \
                .select('id, action_type, description, created_at') \
                .eq('action_type', 'error') \
                .eq('organization_id', current_user.user_id) \
                .order('created_at', desc=True) \
                .limit(limit - len(alerts)) \
                .execute()
            
            for alert in (system_alerts.data or []):
                alerts.append(DashboardAlertResponse(
                    id=f"sys_{alert['id']}",
                    type='system_alert',
                    severity='error',
                    title='System Error',
                    message=alert.get('description', 'A system error occurred'),
                    link=None,
                    is_read=False,
                    created_at=alert['created_at'],
                    action_required=False,
                    expires_at=None
                ))
        
        # Sort by created_at descending
        alerts.sort(key=lambda x: x.created_at, reverse=True)
        
        # Return only up to limit
        return alerts[:limit]
        
    except Exception as e:
        print(f"❌ Error getting dashboard alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard alerts: {str(e)}"
        )


# ================================
# HELPER FUNCTIONS
# ================================

def aggregate_by_interval(data: List[Dict], start_date: datetime, end_date: datetime, 
                         interval: str, date_field: str, value_field: str = None) -> List[Dict[str, Any]]:
    """
    Aggregate data by time interval.
    
    Args:
        data: List of records with date field
        start_date: Start of period
        end_date: End of period
        interval: 'day', 'week', or 'month'
        date_field: Name of the date field in records
        value_field: Name of the numeric value field (optional)
    
    Returns:
        List of aggregated data points
    """
    result = []
    current = start_date
    
    while current <= end_date:
        next_date = current + get_interval_delta(interval)
        
        # Filter records in this interval
        interval_data = []
        for record in data:
            record_date = record.get(date_field)
            if not record_date:
                continue
            
            if isinstance(record_date, str):
                record_date = datetime.fromisoformat(record_date.replace('Z', '+00:00'))
            
            if current <= record_date < next_date:
                interval_data.append(record)
        
        # Calculate aggregate values
        point = {
            'date': current.isoformat(),
            'count': len(interval_data)
        }
        
        if value_field:
            total = sum(r.get(value_field, 0) for r in interval_data)
            point['value'] = round(total, 2)
            
            if len(interval_data) > 0:
                point['average'] = round(total / len(interval_data), 2)
            else:
                point['average'] = 0
        
        result.append(point)
        current = next_date
    
    return result


def get_interval_delta(interval: str) -> timedelta:
    """Get timedelta for interval."""
    if interval == 'day':
        return timedelta(days=1)
    elif interval == 'week':
        return timedelta(days=7)
    elif interval == 'month':
        return timedelta(days=30)  # Approximate
    else:
        return timedelta(days=1)


def calculate_growth_rate(trend_data: List[Dict], value_key: str) -> Optional[float]:
    """
    Calculate growth rate between first and last data points.
    
    Args:
        trend_data: List of trend data points
        value_key: Key for the value to calculate growth on
    
    Returns:
        Growth rate as percentage, or None if insufficient data
    """
    if len(trend_data) < 2:
        return None
    
    first_value = trend_data[0].get(value_key, 0)
    last_value = trend_data[-1].get(value_key, 0)
    
    if first_value == 0:
        return None
    
    growth_rate = ((last_value - first_value) / first_value) * 100
    return growth_rate


# ================================
# ADDITIONAL HELPER ENDPOINTS
# ================================

@router.get("/alerts/summary")
async def get_alert_summary(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get summary of alerts by severity.
    
    Returns count of alerts grouped by severity level.
    """
    try:
        # Get notifications by priority
        result = supabase.from_('notifications') \
            .select('priority, id', count='exact') \
            .eq('user_id', current_user.user_id) \
            .eq('is_read', False) \
            .execute()
        
        notifications = result.data or []
        
        summary = {
            'total': len(notifications),
            'critical': 0,
            'error': 0,
            'warning': 0,
            'info': 0
        }
        
        for notif in notifications:
            priority = notif.get('priority', 'low')
            if priority == 'critical':
                summary['critical'] += 1
            elif priority == 'high':
                summary['error'] += 1
            elif priority == 'medium':
                summary['warning'] += 1
            else:
                summary['info'] += 1
        
        return summary
        
    except Exception as e:
        print(f"❌ Error getting alert summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert summary: {str(e)}"
        )


@router.put("/alerts/{alert_id}/dismiss")
async def dismiss_alert(
    alert_id: str,
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Dismiss a specific alert.
    
    Marks the alert as read/dismissed.
    """
    try:
        now = datetime.utcnow().isoformat()
        
        result = supabase.from_('notifications') \
            .update({
                'is_read': True,
                'read_at': now,
                'is_dismissed': True,
                'dismissed_at': now,
                'updated_at': now
            }) \
            .eq('id', alert_id) \
            .eq('user_id', current_user.user_id) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        return {
            "success": True,
            "message": "Alert dismissed successfully",
            "alert_id": alert_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error dismissing alert: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dismiss alert: {str(e)}"
        )


@router.delete("/alerts/clear-all")
async def clear_all_alerts(
    current_user: AuthUser = Depends(require_org_member()),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Clear all alerts for the current user.
    
    Marks all notifications as read/dismissed.
    """
    try:
        now = datetime.utcnow().isoformat()
        
        result = supabase.from_('notifications') \
            .update({
                'is_read': True,
                'read_at': now,
                'is_dismissed': True,
                'dismissed_at': now,
                'updated_at': now
            }) \
            .eq('user_id', current_user.user_id) \
            .eq('is_read', False) \
            .execute()
        
        updated_count = len(result.data) if result.data else 0
        
        return {
            "success": True,
            "message": f"Cleared {updated_count} alerts",
            "cleared_count": updated_count
        }
        
    except Exception as e:
        print(f"❌ Error clearing alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear alerts: {str(e)}"
        )