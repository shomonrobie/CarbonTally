# backend/routes/admin/audit_logs.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from supabase import Client
import json

from auth import AuthUser, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/audit-logs", tags=["Admin Audit Logs"])


# ================================
# PYDANTIC MODELS
# ================================

class AuditLogResponse(BaseModel):
    """Response model for audit log entry."""
    id: str
    user_id: Optional[str]
    staff_id: Optional[str]
    organization_member_id: Optional[str]
    organization_id: Optional[str]
    action_type: str
    resource_type: Optional[str]
    resource_id: Optional[str]
    action: str
    description: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    old_data: Optional[Dict[str, Any]]
    new_data: Optional[Dict[str, Any]]
    changes: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    user_email: Optional[str]
    user_name: Optional[str]
    organization_name: Optional[str]


class AuditLogsListResponse(BaseModel):
    """Response model for audit logs list."""
    logs: List[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AuditStatsResponse(BaseModel):
    """Response model for audit statistics."""
    total_logs: int
    by_action_type: Dict[str, int]
    by_resource_type: Dict[str, int]
    by_organization: List[Dict[str, Any]]
    by_user: List[Dict[str, Any]]
    logs_today: int
    logs_this_week: int
    logs_this_month: int
    top_actions: List[Dict[str, Any]]
    activity_timeline: List[Dict[str, Any]]


class ExportLogsResponse(BaseModel):
    """Response model for logs export."""
    export_id: str
    format: str
    file_url: str
    expires_at: datetime
    record_count: int
    data_preview: Optional[List[Dict[str, Any]]]


class MessageLogResponse(BaseModel):
    """Response model for message log entry."""
    id: str
    message_id: str
    conversation_id: Optional[str]
    user_id: Optional[str]
    action_type: Optional[str]
    action_details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    user_email: Optional[str]
    user_name: Optional[str]
    message_content: Optional[str]
    conversation_subject: Optional[str]


class NotificationLogResponse(BaseModel):
    """Response model for notification log entry."""
    id: str
    notification_id: Optional[str]
    user_id: Optional[str]
    channel: Optional[str]
    status: Optional[str]
    error_message: Optional[str]
    sent_at: Optional[datetime]
    delivered_at: Optional[datetime]
    opened_at: Optional[datetime]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime
    user_email: Optional[str]
    user_name: Optional[str]
    notification_title: Optional[str]
    notification_type: Optional[str]


class VerificationLogResponse(BaseModel):
    """Response model for verification log entry."""
    id: str
    verification_id: Optional[str]
    user_id: Optional[str]
    action_type: Optional[str]
    action_details: Optional[Dict[str, Any]]
    ip_address: Optional[str]
    user_agent: Optional[str]
    created_at: datetime
    user_email: Optional[str]
    user_name: Optional[str]
    document_id: Optional[str]
    document_name: Optional[str]
    verification_status: Optional[str]


# ================================
# ENDPOINTS
# ================================

@router.get("/", response_model=AuditLogsListResponse)
async def search_audit_logs(
    current_user: AuthUser = Depends(require_admin()),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    resource_id: Optional[str] = Query(None, description="Filter by resource ID"),
    action: Optional[str] = Query(None, description="Filter by action"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    search: Optional[str] = Query(None, description="Search in description"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    supabase: Client = Depends(get_supabase_client)
):
    """Search and filter audit logs with pagination."""
    try:
        # Build query
        query = supabase.from_('audit_logs') \
            .select('''
                id, user_id, staff_id, organization_member_id, organization_id,
                action_type, resource_type, resource_id, action, description,
                ip_address, user_agent, old_data, new_data, changes, metadata,
                created_at
            ''')
        
        # Apply filters
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        if action_type:
            query = query.eq('action_type', action_type)
        
        if resource_type:
            query = query.eq('resource_type', resource_type)
        
        if resource_id:
            query = query.eq('resource_id', resource_id)
        
        if action:
            query = query.eq('action', action)
        
        if start_date:
            query = query.gte('created_at', start_date.isoformat())
        
        if end_date:
            query = query.lte('created_at', end_date.isoformat())
        
        if search:
            query = query.ilike('description', f'%{search}%')
        
        # Get total count
        count_query = supabase.from_('audit_logs') \
            .select('id', count='exact')
        
        # Apply same filters to count query
        if organization_id:
            count_query = count_query.eq('organization_id', organization_id)
        if user_id:
            count_query = count_query.eq('user_id', user_id)
        if action_type:
            count_query = count_query.eq('action_type', action_type)
        if resource_type:
            count_query = count_query.eq('resource_type', resource_type)
        if resource_id:
            count_query = count_query.eq('resource_id', resource_id)
        if action:
            count_query = count_query.eq('action', action)
        if start_date:
            count_query = count_query.gte('created_at', start_date.isoformat())
        if end_date:
            count_query = count_query.lte('created_at', end_date.isoformat())
        if search:
            count_query = count_query.ilike('description', f'%{search}%')
        
        count_result = count_query.execute()
        total = count_result.count if hasattr(count_result, 'count') else 0
        
        # Get paginated results
        offset = (page - 1) * page_size
        result = query.order(sort_by, desc=(sort_order == 'desc')) \
            .range(offset, offset + page_size - 1) \
            .execute()
        
        logs = result.data or []
        
        # Enrich logs with user and organization details
        enriched_logs = []
        for log in logs:
            # Get user details
            user_email = None
            user_name = None
            if log.get('user_id'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', log['user_id']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    user_email = user_result.data.get('email')
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
            
            # Get organization name
            organization_name = None
            if log.get('organization_id'):
                org_result = supabase.from_('organizations') \
                    .select('name') \
                    .eq('id', log['organization_id']) \
                    .maybe_single() \
                    .execute()
                
                if org_result.data:
                    organization_name = org_result.data.get('name')
            
            enriched_logs.append(AuditLogResponse(
                id=log['id'],
                user_id=log.get('user_id'),
                staff_id=log.get('staff_id'),
                organization_member_id=log.get('organization_member_id'),
                organization_id=log.get('organization_id'),
                action_type=log['action_type'],
                resource_type=log.get('resource_type'),
                resource_id=log.get('resource_id'),
                action=log['action'],
                description=log.get('description'),
                ip_address=log.get('ip_address'),
                user_agent=log.get('user_agent'),
                old_data=log.get('old_data'),
                new_data=log.get('new_data'),
                changes=log.get('changes'),
                metadata=log.get('metadata'),
                created_at=log['created_at'],
                user_email=user_email,
                user_name=user_name,
                organization_name=organization_name
            ))
        
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0
        
        return AuditLogsListResponse(
            logs=enriched_logs,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except Exception as e:
        print(f"❌ Error searching audit logs: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search audit logs: {str(e)}"
        )


@router.get("/messages", response_model=List[MessageLogResponse])
async def get_message_logs(
    current_user: AuthUser = Depends(require_admin()),
    conversation_id: Optional[str] = Query(None, description="Filter by conversation"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=500, description="Number of logs to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get message activity logs."""
    try:
        query = supabase.from_('message_activity_log') \
            .select('''
                id, message_id, conversation_id, user_id, action_type,
                action_details, ip_address, user_agent, created_at
            ''')
        
        if conversation_id:
            query = query.eq('conversation_id', conversation_id)
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        if start_date:
            query = query.gte('created_at', start_date.isoformat())
        
        if end_date:
            query = query.lte('created_at', end_date.isoformat())
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        
        logs = result.data or []
        
        enriched_logs = []
        for log in logs:
            # Get user details
            user_email = None
            user_name = None
            if log.get('user_id'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', log['user_id']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    user_email = user_result.data.get('email')
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
            
            # Get message content
            message_content = None
            conversation_subject = None
            if log.get('message_id'):
                msg_result = supabase.from_('messages') \
                    .select('content, subject, conversations(subject)') \
                    .eq('id', log['message_id']) \
                    .maybe_single() \
                    .execute()
                
                if msg_result.data:
                    message_content = msg_result.data.get('content')
                    if msg_result.data.get('conversations'):
                        conversation_subject = msg_result.data['conversations'].get('subject')
            
            enriched_logs.append(MessageLogResponse(
                id=log['id'],
                message_id=log.get('message_id'),
                conversation_id=log.get('conversation_id'),
                user_id=log.get('user_id'),
                action_type=log.get('action_type'),
                action_details=log.get('action_details'),
                ip_address=log.get('ip_address'),
                user_agent=log.get('user_agent'),
                created_at=log['created_at'],
                user_email=user_email,
                user_name=user_name,
                message_content=message_content,
                conversation_subject=conversation_subject
            ))
        
        return enriched_logs
        
    except Exception as e:
        print(f"❌ Error getting message logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message logs: {str(e)}"
        )


@router.get("/notifications", response_model=List[NotificationLogResponse])
async def get_notification_logs(
    current_user: AuthUser = Depends(require_admin()),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=500, description="Number of logs to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get notification delivery logs."""
    try:
        query = supabase.from_('notification_delivery_log') \
            .select('''
                id, notification_id, user_id, channel, status,
                error_message, sent_at, delivered_at, opened_at,
                metadata, created_at
            ''')
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        if channel:
            query = query.eq('channel', channel)
        
        if status:
            query = query.eq('status', status)
        
        if start_date:
            query = query.gte('created_at', start_date.isoformat())
        
        if end_date:
            query = query.lte('created_at', end_date.isoformat())
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        
        logs = result.data or []
        
        enriched_logs = []
        for log in logs:
            # Get user details
            user_email = None
            user_name = None
            if log.get('user_id'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', log['user_id']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    user_email = user_result.data.get('email')
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
            
            # Get notification details
            notification_title = None
            notification_type = None
            if log.get('notification_id'):
                notif_result = supabase.from_('notifications') \
                    .select('title, type') \
                    .eq('id', log['notification_id']) \
                    .maybe_single() \
                    .execute()
                
                if notif_result.data:
                    notification_title = notif_result.data.get('title')
                    notification_type = notif_result.data.get('type')
            
            enriched_logs.append(NotificationLogResponse(
                id=log['id'],
                notification_id=log.get('notification_id'),
                user_id=log.get('user_id'),
                channel=log.get('channel'),
                status=log.get('status'),
                error_message=log.get('error_message'),
                sent_at=log.get('sent_at'),
                delivered_at=log.get('delivered_at'),
                opened_at=log.get('opened_at'),
                metadata=log.get('metadata'),
                created_at=log['created_at'],
                user_email=user_email,
                user_name=user_name,
                notification_title=notification_title,
                notification_type=notification_type
            ))
        
        return enriched_logs
        
    except Exception as e:
        print(f"❌ Error getting notification logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get notification logs: {str(e)}"
        )


@router.get("/verifications", response_model=List[VerificationLogResponse])
async def get_verification_logs(
    current_user: AuthUser = Depends(require_admin()),
    verification_id: Optional[str] = Query(None, description="Filter by verification"),
    user_id: Optional[str] = Query(None, description="Filter by user"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(100, ge=1, le=500, description="Number of logs to return"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get verification activity logs."""
    try:
        query = supabase.from_('verification_activity_log') \
            .select('''
                id, verification_id, user_id, action_type,
                action_details, ip_address, user_agent, created_at
            ''')
        
        if verification_id:
            query = query.eq('verification_id', verification_id)
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        if action_type:
            query = query.eq('action_type', action_type)
        
        if start_date:
            query = query.gte('created_at', start_date.isoformat())
        
        if end_date:
            query = query.lte('created_at', end_date.isoformat())
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        
        logs = result.data or []
        
        enriched_logs = []
        for log in logs:
            # Get user details
            user_email = None
            user_name = None
            if log.get('user_id'):
                user_result = supabase.from_('auth.users') \
                    .select('email, raw_user_meta_data') \
                    .eq('id', log['user_id']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    user_email = user_result.data.get('email')
                    raw_meta = user_result.data.get('raw_user_meta_data', {})
                    user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
            
            # Get verification and document details
            document_id = None
            document_name = None
            verification_status = None
            
            if log.get('verification_id'):
                verif_result = supabase.from_('customer_verifications') \
                    .select('''
                        customer_document_id, status,
                        customer_documents(file_name)
                    ''') \
                    .eq('id', log['verification_id']) \
                    .maybe_single() \
                    .execute()
                
                if verif_result.data:
                    verification_status = verif_result.data.get('status')
                    document_id = verif_result.data.get('customer_document_id')
                    if verif_result.data.get('customer_documents'):
                        document_name = verif_result.data['customer_documents'].get('file_name')
            
            enriched_logs.append(VerificationLogResponse(
                id=log['id'],
                verification_id=log.get('verification_id'),
                user_id=log.get('user_id'),
                action_type=log.get('action_type'),
                action_details=log.get('action_details'),
                ip_address=log.get('ip_address'),
                user_agent=log.get('user_agent'),
                created_at=log['created_at'],
                user_email=user_email,
                user_name=user_name,
                document_id=document_id,
                document_name=document_name,
                verification_status=verification_status
            ))
        
        return enriched_logs
        
    except Exception as e:
        print(f"❌ Error getting verification logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get verification logs: {str(e)}"
        )


@router.get("/export", response_model=ExportLogsResponse)
async def export_logs(
    current_user: AuthUser = Depends(require_admin()),
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(1000, ge=1, le=10000, description="Maximum records to export"),
    supabase: Client = Depends(get_supabase_client)
):
    """Export audit logs in JSON or CSV format."""
    try:
        # Build query
        query = supabase.from_('audit_logs') \
            .select('''
                id, user_id, organization_id, action_type, resource_type,
                resource_id, action, description, ip_address, user_agent,
                old_data, new_data, changes, metadata, created_at
            ''')
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        if start_date:
            query = query.gte('created_at', start_date.isoformat())
        
        if end_date:
            query = query.lte('created_at', end_date.isoformat())
        
        if action_type:
            query = query.eq('action_type', action_type)
        
        result = query.order('created_at', desc=True).limit(limit).execute()
        
        logs = result.data or []
        
        # Enrich logs with user and organization details
        enriched_logs = []
        for log in logs:
            # Get user email
            user_email = None
            if log.get('user_id'):
                user_result = supabase.from_('auth.users') \
                    .select('email') \
                    .eq('id', log['user_id']) \
                    .maybe_single() \
                    .execute()
                
                if user_result.data:
                    user_email = user_result.data.get('email')
            
            # Get organization name
            org_name = None
            if log.get('organization_id'):
                org_result = supabase.from_('organizations') \
                    .select('name') \
                    .eq('id', log['organization_id']) \
                    .maybe_single() \
                    .execute()
                
                if org_result.data:
                    org_name = org_result.data.get('name')
            
            enriched_logs.append({
                **log,
                'user_email': user_email,
                'organization_name': org_name
            })
        
        # Generate export ID
        export_id = f"audit_export_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # For demo purposes, create a fake file URL
        file_url = f"/exports/audit-logs/{export_id}.{format}"
        
        # Set expiry (7 days from now)
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        return ExportLogsResponse(
            export_id=export_id,
            format=format,
            file_url=file_url,
            expires_at=expires_at,
            record_count=len(enriched_logs),
            data_preview=enriched_logs[:10]
        )
        
    except Exception as e:
        print(f"❌ Error exporting logs: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export logs: {str(e)}"
        )


@router.get("/stats", response_model=AuditStatsResponse)
async def get_audit_statistics(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    supabase: Client = Depends(get_supabase_client)
):
    """Get audit statistics and analytics."""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        now = datetime.utcnow()
        today_start = datetime(now.year, now.month, now.day)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = datetime(now.year, now.month, 1)
        
        # Get all logs in date range
        result = supabase.from_('audit_logs') \
            .select('''
                id, user_id, organization_id, action_type, resource_type,
                action, created_at
            ''') \
            .gte('created_at', cutoff.isoformat()) \
            .execute()
        
        logs = result.data or []
        total = len(logs)
        
        # By action type
        action_type_counts = {}
        for log in logs:
            action_type = log.get('action_type', 'unknown')
            action_type_counts[action_type] = action_type_counts.get(action_type, 0) + 1
        
        # By resource type
        resource_type_counts = {}
        for log in logs:
            resource_type = log.get('resource_type', 'unknown')
            resource_type_counts[resource_type] = resource_type_counts.get(resource_type, 0) + 1
        
        # By organization
        org_counts = {}
        for log in logs:
            org_id = log.get('organization_id')
            if org_id:
                if org_id not in org_counts:
                    org_counts[org_id] = {'organization_id': org_id, 'count': 0}
                org_counts[org_id]['count'] += 1
        
        # Get organization names
        by_organization = []
        for org_id, data in org_counts.items():
            org_result = supabase.from_('organizations') \
                .select('name') \
                .eq('id', org_id) \
                .maybe_single() \
                .execute()
            
            org_name = org_result.data.get('name') if org_result.data else 'Unknown'
            by_organization.append({
                'organization_id': org_id,
                'organization_name': org_name,
                'count': data['count']
            })
        
        by_organization.sort(key=lambda x: x['count'], reverse=True)
        
        # By user
        user_counts = {}
        for log in logs:
            user_id = log.get('user_id')
            if user_id:
                if user_id not in user_counts:
                    user_counts[user_id] = {'user_id': user_id, 'count': 0}
                user_counts[user_id]['count'] += 1
        
        # Get user emails
        by_user = []
        for user_id, data in user_counts.items():
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', user_id) \
                .maybe_single() \
                .execute()
            
            if user_result.data:
                email = user_result.data.get('email')
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                name = raw_meta.get('full_name') or raw_meta.get('name') or email
                by_user.append({
                    'user_id': user_id,
                    'user_email': email,
                    'user_name': name,
                    'count': data['count']
                })
        
        by_user.sort(key=lambda x: x['count'], reverse=True)
        
        # Time-based counts
        logs_today = sum(1 for log in logs if log.get('created_at') and log['created_at'] >= today_start)
        logs_this_week = sum(1 for log in logs if log.get('created_at') and log['created_at'] >= week_start)
        logs_this_month = sum(1 for log in logs if log.get('created_at') and log['created_at'] >= month_start)
        
        # Top actions
        action_counts = {}
        for log in logs:
            action = log.get('action', 'unknown')
            action_counts[action] = action_counts.get(action, 0) + 1
        
        top_actions = [
            {'action': k, 'count': v} 
            for k, v in sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
        
        # Activity timeline (daily)
        timeline = {}
        for log in logs:
            created_at = log.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                key = created_at.strftime('%Y-%m-%d')
                if key not in timeline:
                    timeline[key] = 0
                timeline[key] += 1
        
        activity_timeline = [
            {'date': k, 'count': v} 
            for k, v in sorted(timeline.items())[-30:]
        ]
        
        return AuditStatsResponse(
            total_logs=total,
            by_action_type=action_type_counts,
            by_resource_type=resource_type_counts,
            by_organization=by_organization[:10],
            by_user=by_user[:10],
            logs_today=logs_today,
            logs_this_week=logs_this_week,
            logs_this_month=logs_this_month,
            top_actions=top_actions,
            activity_timeline=activity_timeline
        )
        
    except Exception as e:
        print(f"❌ Error getting audit statistics: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit statistics: {str(e)}"
        )


# ================================
# ADDITIONAL HELPER ENDPOINTS
# ================================

@router.get("/organizations")
async def get_audit_organizations(
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get list of organizations with audit logs."""
    try:
        result = supabase.from_('audit_logs') \
            .select('organization_id, organizations(name)') \
            .not_.is_('organization_id', 'null') \
            .execute()
        
        orgs = {}
        for log in (result.data or []):
            org_id = log.get('organization_id')
            if org_id:
                org_name = log.get('organizations', {}).get('name', 'Unknown') if log.get('organizations') else 'Unknown'
                orgs[org_id] = {
                    'organization_id': org_id,
                    'organization_name': org_name
                }
        
        return list(orgs.values())
        
    except Exception as e:
        print(f"❌ Error getting audit organizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit organizations: {str(e)}"
        )


@router.get("/actions")
async def get_audit_actions(
    current_user: AuthUser = Depends(require_admin()),
    supabase: Client = Depends(get_supabase_client)
):
    """Get list of unique action types and actions."""
    try:
        # Get action types
        types_result = supabase.from_('audit_logs') \
            .select('action_type') \
            .execute()
        
        action_types = list(set(
            log.get('action_type') for log in (types_result.data or []) 
            if log.get('action_type')
        ))
        
        # Get actions
        actions_result = supabase.from_('audit_logs') \
            .select('action') \
            .execute()
        
        actions = list(set(
            log.get('action') for log in (actions_result.data or []) 
            if log.get('action')
        ))
        
        return {
            "action_types": sorted(action_types),
            "actions": sorted(actions)
        }
        
    except Exception as e:
        print(f"❌ Error getting audit actions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get audit actions: {str(e)}"
        )
# ================================
# ADDITIONAL PYDANTIC MODELS
# ================================

class UserAuditActivityResponse(BaseModel):
    """Response model for user audit activity."""
    user_id: str
    user_email: str
    user_name: Optional[str]
    organization_id: Optional[str]
    organization_name: Optional[str]
    total_actions: int
    last_action_at: Optional[datetime]
    first_action_at: Optional[datetime]
    action_types: Dict[str, int]
    resource_types: Dict[str, int]
    ip_addresses: List[str]
    activity_days: int


class UserAuditSummaryResponse(BaseModel):
    """Response model for user audit summary."""
    total_users: int
    active_users: int
    inactive_users: int
    users_by_organization: Dict[str, int]
    users_by_action: Dict[str, int]
    top_users: List[Dict[str, Any]]
    user_activity_trend: List[Dict[str, Any]]


# ================================
# NEW ENDPOINT
# ================================

@router.get("/users", response_model=List[UserAuditActivityResponse])
async def get_user_audit_activity(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    organization_id: Optional[str] = Query(None, description="Filter by organization"),
    user_id: Optional[str] = Query(None, description="Filter by specific user"),
    min_actions: int = Query(1, ge=1, description="Minimum number of actions"),
    limit: int = Query(50, ge=1, le=200, description="Number of users to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get user audit activity summary.
    
    Returns detailed activity statistics for each user including action counts,
    resource types, and activity patterns.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Build base query
        query = supabase.from_('audit_logs') \
            .select('''
                user_id, organization_id, action_type, resource_type,
                action, ip_address, created_at,
                organizations(name)
            ''') \
            .gte('created_at', cutoff.isoformat()) \
            .not_.is_('user_id', 'null')
        
        if organization_id:
            query = query.eq('organization_id', organization_id)
        
        if user_id:
            query = query.eq('user_id', user_id)
        
        result = query.order('created_at', desc=True).execute()
        logs = result.data or []
        
        if not logs:
            return []
        
        # Group by user
        user_stats = {}
        for log in logs:
            user_id_key = log.get('user_id')
            if not user_id_key:
                continue
            
            if user_id_key not in user_stats:
                org_id = log.get('organization_id')
                org_name = log.get('organizations', {}).get('name') if log.get('organizations') else None
                
                user_stats[user_id_key] = {
                    'user_id': user_id_key,
                    'organization_id': org_id,
                    'organization_name': org_name,
                    'total_actions': 0,
                    'last_action_at': None,
                    'first_action_at': None,
                    'action_types': {},
                    'resource_types': {},
                    'ip_addresses': set(),
                    'activity_dates': set(),
                    'activities': []
                }
            
            stats = user_stats[user_id_key]
            stats['total_actions'] += 1
            
            # Track action types
            action_type = log.get('action_type', 'unknown')
            stats['action_types'][action_type] = stats['action_types'].get(action_type, 0) + 1
            
            # Track resource types
            resource_type = log.get('resource_type', 'unknown')
            stats['resource_types'][resource_type] = stats['resource_types'].get(resource_type, 0) + 1
            
            # Track IP addresses
            if log.get('ip_address'):
                stats['ip_addresses'].add(log['ip_address'])
            
            # Track dates
            created_at = log.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                stats['activity_dates'].add(created_at.date())
                
                # Update last action
                if not stats['last_action_at'] or created_at > stats['last_action_at']:
                    stats['last_action_at'] = created_at
                
                # Update first action
                if not stats['first_action_at'] or created_at < stats['first_action_at']:
                    stats['first_action_at'] = created_at
        
        # Enrich with user details
        enriched_users = []
        for user_id_key, stats in user_stats.items():
            # Skip users with insufficient actions
            if stats['total_actions'] < min_actions:
                continue
            
            # Get user details
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', user_id_key) \
                .maybe_single() \
                .execute()
            
            user_email = None
            user_name = None
            if user_result.data:
                user_email = user_result.data.get('email')
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
            
            # Calculate activity days
            activity_days = len(stats['activity_dates'])
            
            enriched_users.append(UserAuditActivityResponse(
                user_id=user_id_key,
                user_email=user_email or 'Unknown',
                user_name=user_name,
                organization_id=stats.get('organization_id'),
                organization_name=stats.get('organization_name'),
                total_actions=stats['total_actions'],
                last_action_at=stats['last_action_at'],
                first_action_at=stats['first_action_at'],
                action_types=stats['action_types'],
                resource_types=stats['resource_types'],
                ip_addresses=list(stats['ip_addresses']),
                activity_days=activity_days
            ))
        
        # Sort by total actions descending
        enriched_users.sort(key=lambda x: x.total_actions, reverse=True)
        
        # Apply pagination
        total = len(enriched_users)
        paginated_users = enriched_users[offset:offset + limit]
        
        return paginated_users
        
    except Exception as e:
        print(f"❌ Error getting user audit activity: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user audit activity: {str(e)}"
        )


@router.get("/users/summary", response_model=UserAuditSummaryResponse)
async def get_user_audit_summary(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get summary of user audit activity.
    
    Returns aggregated statistics about user activity including counts,
    trends, and top users.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Get all users who have activity
        result = supabase.from_('audit_logs') \
            .select('user_id, organization_id, action_type, created_at') \
            .gte('created_at', cutoff.isoformat()) \
            .not_.is_('user_id', 'null') \
            .execute()
        
        logs = result.data or []
        
        if not logs:
            return UserAuditSummaryResponse(
                total_users=0,
                active_users=0,
                inactive_users=0,
                users_by_organization={},
                users_by_action={},
                top_users=[],
                user_activity_trend=[]
            )
        
        # Track unique users
        unique_users = set()
        user_activity = {}
        org_users = {}
        action_users = {}
        
        for log in logs:
            user_id = log.get('user_id')
            if not user_id:
                continue
            
            unique_users.add(user_id)
            
            # Track organization
            org_id = log.get('organization_id')
            if org_id:
                if org_id not in org_users:
                    org_users[org_id] = set()
                org_users[org_id].add(user_id)
            
            # Track action types
            action_type = log.get('action_type', 'unknown')
            if action_type not in action_users:
                action_users[action_type] = set()
            action_users[action_type].add(user_id)
            
            # Track user activity count
            if user_id not in user_activity:
                user_activity[user_id] = 0
            user_activity[user_id] += 1
        
        total_users = len(unique_users)
        
        # Get organization names
        users_by_organization = {}
        for org_id, users in org_users.items():
            org_result = supabase.from_('organizations') \
                .select('name') \
                .eq('id', org_id) \
                .maybe_single() \
                .execute()
            
            org_name = org_result.data.get('name') if org_result.data else 'Unknown'
            users_by_organization[org_name] = len(users)
        
        # Get action type names
        users_by_action = {}
        for action_type, users in action_users.items():
            users_by_action[action_type] = len(users)
        
        # Get top users
        top_users_data = []
        for user_id, count in sorted(user_activity.items(), key=lambda x: x[1], reverse=True)[:10]:
            user_result = supabase.from_('auth.users') \
                .select('email, raw_user_meta_data') \
                .eq('id', user_id) \
                .maybe_single() \
                .execute()
            
            user_email = None
            user_name = None
            if user_result.data:
                user_email = user_result.data.get('email')
                raw_meta = user_result.data.get('raw_user_meta_data', {})
                user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
            
            top_users_data.append({
                'user_id': user_id,
                'user_email': user_email or 'Unknown',
                'user_name': user_name,
                'action_count': count
            })
        
        # Get user activity trend (daily)
        trend_data = {}
        for log in logs:
            created_at = log.get('created_at')
            if created_at:
                if isinstance(created_at, str):
                    created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                key = created_at.strftime('%Y-%m-%d')
                if key not in trend_data:
                    trend_data[key] = 0
                trend_data[key] += 1
        
        user_activity_trend = [
            {'date': k, 'actions': v} 
            for k, v in sorted(trend_data.items())
        ]
        
        # Count inactive users (activity but more than 7 days ago)
        last_week = datetime.utcnow() - timedelta(days=7)
        active_users = 0
        inactive_users = 0
        
        # Get last activity for each user
        for user_id in unique_users:
            user_logs = [l for l in logs if l.get('user_id') == user_id]
            if user_logs:
                last_activity = max(
                    l.get('created_at') for l in user_logs if l.get('created_at')
                )
                if isinstance(last_activity, str):
                    last_activity = datetime.fromisoformat(last_activity.replace('Z', '+00:00'))
                
                if last_activity and last_activity >= last_week:
                    active_users += 1
                else:
                    inactive_users += 1
        
        return UserAuditSummaryResponse(
            total_users=total_users,
            active_users=active_users,
            inactive_users=inactive_users,
            users_by_organization=users_by_organization,
            users_by_action=users_by_action,
            top_users=top_users_data,
            user_activity_trend=user_activity_trend
        )
        
    except Exception as e:
        print(f"❌ Error getting user audit summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user audit summary: {str(e)}"
        )


@router.get("/users/{user_id}/activities")
async def get_user_activity_details(
    user_id: str,
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    action_type: Optional[str] = Query(None, description="Filter by action type"),
    limit: int = Query(100, ge=1, le=500, description="Number of activities to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get detailed activity for a specific user.
    
    Returns all audit log entries for a user with filtering options.
    """
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Verify user exists
        user_result = supabase.from_('auth.users') \
            .select('email, raw_user_meta_data') \
            .eq('id', user_id) \
            .maybe_single() \
            .execute()
        
        if not user_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_email = user_result.data.get('email')
        raw_meta = user_result.data.get('raw_user_meta_data', {})
        user_name = raw_meta.get('full_name') or raw_meta.get('name') or user_email
        
        # Get activities
        query = supabase.from_('audit_logs') \
            .select('''
                id, action_type, resource_type, resource_id, action,
                description, ip_address, user_agent, old_data,
                new_data, changes, metadata, created_at,
                organization_id,
                organizations(name)
            ''') \
            .eq('user_id', user_id) \
            .gte('created_at', cutoff.isoformat())
        
        if action_type:
            query = query.eq('action_type', action_type)
        
        total_result = query.select('id', count='exact').execute()
        total = total_result.count if hasattr(total_result, 'count') else 0
        
        result = query.order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        activities = result.data or []
        
        # Enrich activities
        enriched_activities = []
        for activity in activities:
            org_name = activity.get('organizations', {}).get('name') if activity.get('organizations') else None
            
            enriched_activities.append({
                'id': activity['id'],
                'action_type': activity.get('action_type'),
                'resource_type': activity.get('resource_type'),
                'resource_id': activity.get('resource_id'),
                'action': activity.get('action'),
                'description': activity.get('description'),
                'ip_address': activity.get('ip_address'),
                'user_agent': activity.get('user_agent'),
                'old_data': activity.get('old_data'),
                'new_data': activity.get('new_data'),
                'changes': activity.get('changes'),
                'metadata': activity.get('metadata'),
                'created_at': activity['created_at'],
                'organization_id': activity.get('organization_id'),
                'organization_name': org_name
            })
        
        return {
            'user_id': user_id,
            'user_email': user_email,
            'user_name': user_name,
            'total_activities': total,
            'limit': limit,
            'offset': offset,
            'activities': enriched_activities
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting user activity details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user activity details: {str(e)}"
        )


@router.get("/users/export")
async def export_user_audit_data(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Export user audit data.
    
    Exports user activity summary in JSON or CSV format.
    """
    try:
        # Get user audit data
        users = await get_user_audit_activity(
            current_user=current_user,
            days=days,
            min_actions=1,
            limit=1000,
            offset=0,
            supabase=supabase
        )
        
        # Convert to export format
        export_data = []
        for user in users:
            export_data.append({
                'user_id': user.user_id,
                'user_email': user.user_email,
                'user_name': user.user_name,
                'organization_name': user.organization_name,
                'total_actions': user.total_actions,
                'activity_days': user.activity_days,
                'last_action_at': user.last_action_at.isoformat() if user.last_action_at else None,
                'first_action_at': user.first_action_at.isoformat() if user.first_action_at else None,
                'action_types': json.dumps(user.action_types) if format == 'csv' else user.action_types,
                'resource_types': json.dumps(user.resource_types) if format == 'csv' else user.resource_types,
                'ip_addresses': ','.join(user.ip_addresses) if format == 'csv' else user.ip_addresses
            })
        
        # Generate export ID
        export_id = f"user_audit_export_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        file_url = f"/exports/user-audit/{export_id}.{format}"
        expires_at = datetime.utcnow() + timedelta(days=7)
        
        return {
            "success": True,
            "export_id": export_id,
            "format": format,
            "file_url": file_url,
            "expires_at": expires_at,
            "record_count": len(export_data),
            "data_preview": export_data[:10]
        }
        
    except Exception as e:
        print(f"❌ Error exporting user audit data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export user audit data: {str(e)}"
        )