# backend/routes/admin/analytics.py
"""
System health and analytics endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from auth import AuthUser, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/analytics", tags=["Admin - Analytics"])

# ==========================================
# System Health Endpoints
# ==========================================

@router.get("/system/health")
async def get_system_health(
    current_user: AuthUser = Depends(require_admin())
):
    """
    Get system health metrics.
    Returns overall system status, performance, and health indicators.
    """
    try:
        supabase = get_supabase_client()
        
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'components': {
                'database': {'status': 'healthy', 'latency_ms': 0},
                'storage': {'status': 'healthy', 'usage_percent': 0},
                'api': {'status': 'healthy', 'uptime': '100%'}
            },
            'metrics': {
                'total_users': 0,
                'active_users_today': 0,
                'total_organizations': 0,
                'total_documents': 0,
                'pending_reviews': 0,
                'processing_queue': 0
            }
        }
        
        # Check database health
        try:
            start_time = datetime.utcnow()
            db_check = supabase.from_('organizations') \
                .select('id') \
                .limit(1) \
                .execute()
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            health_data['components']['database']['latency_ms'] = round(latency, 2)
            health_data['components']['database']['status'] = 'healthy'
        except Exception as e:
            health_data['components']['database']['status'] = 'unhealthy'
            health_data['components']['database']['error'] = str(e)
            health_data['status'] = 'degraded'
        
        # Get metrics
        try:
            # Total organizations
            org_result = supabase.from_('organizations') \
                .select('id', count='exact') \
                .execute()
            health_data['metrics']['total_organizations'] = len(org_result.data) if org_result.data else 0
            
            # Total documents
            doc_result = supabase.from_('organization_files') \
                .select('id', count='exact') \
                .execute()
            health_data['metrics']['total_documents'] = len(doc_result.data) if doc_result.data else 0
            
            # Pending reviews
            review_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('status', 'pending') \
                .execute()
            health_data['metrics']['pending_reviews'] = len(review_result.data) if review_result.data else 0
            
            # Processing queue
            processing_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('status', 'processing') \
                .execute()
            health_data['metrics']['processing_queue'] = len(processing_result.data) if processing_result.data else 0
            
        except Exception as e:
            health_data['status'] = 'degraded'
            health_data['metrics_error'] = str(e)
        
        # Check for critical errors
        try:
            # Check for failed reviews in last hour
            hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
            error_result = supabase.from_('manual_review_queue') \
                .select('id', count='exact') \
                .eq('status', 'failed') \
                .gte('created_at', hour_ago) \
                .execute()
            
            error_count = len(error_result.data) if error_result.data else 0
            if error_count > 5:
                health_data['status'] = 'degraded'
                health_data['warnings'] = [f"{error_count} failed reviews in the last hour"]
        except Exception:
            pass
        
        return {
            "success": True,
            "data": health_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )

# ==========================================
# System Performance Endpoints
# ==========================================

@router.get("/system/performance")
async def get_system_performance(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(7, ge=1, le=90)
):
    """
    Get system performance metrics over time.
    """
    try:
        supabase = get_supabase_client()
        
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        performance_data = {
            'timeframe': {
                'days': days,
                'start_date': start_date,
                'end_date': datetime.utcnow().isoformat()
            },
            'metrics': {
                'total_requests': 0,
                'avg_response_time': 0,
                'error_rate': 0,
                'daily_trends': []
            }
        }
        
        # Get processing logs for performance metrics
        logs_result = supabase.from_('processing_logs') \
            .select('*') \
            .gte('started_at', start_date) \
            .execute()
        
        if logs_result.data:
            total_requests = len(logs_result.data)
            performance_data['metrics']['total_requests'] = total_requests
            
            # Calculate average duration
            durations = [l.get('duration_ms', 0) for l in logs_result.data if l.get('duration_ms')]
            if durations:
                performance_data['metrics']['avg_response_time'] = sum(durations) / len(durations)
            
            # Calculate error rate
            errors = [l for l in logs_result.data if l.get('status') == 'failed']
            if errors:
                performance_data['metrics']['error_rate'] = (len(errors) / total_requests) * 100
            
            # Calculate daily trends
            daily_data = {}
            for log in logs_result.data:
                date = log.get('started_at', '').split('T')[0] if log.get('started_at') else None
                if date:
                    if date not in daily_data:
                        daily_data[date] = {'count': 0, 'total_duration': 0}
                    daily_data[date]['count'] += 1
                    daily_data[date]['total_duration'] += log.get('duration_ms', 0)
            
            for date, data in daily_data.items():
                performance_data['metrics']['daily_trends'].append({
                    'date': date,
                    'requests': data['count'],
                    'avg_duration_ms': data['total_duration'] / data['count'] if data['count'] > 0 else 0
                })
        
        return {
            "success": True,
            "data": performance_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system performance: {str(e)}"
        )

# ==========================================
# System Usage Endpoints
# ==========================================

@router.get("/system/usage")
async def get_system_usage(
    current_user: AuthUser = Depends(require_admin()),
    days: int = Query(30, ge=1, le=365)
):
    """
    Get system usage statistics.
    """
    try:
        supabase = get_supabase_client()
        
        start_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        
        usage_data = {
            'timeframe': {
                'days': days,
                'start_date': start_date,
                'end_date': datetime.utcnow().isoformat()
            },
            'storage': {
                'total_bytes': 0,
                'file_count': 0,
                'avg_file_size': 0
            },
            'activity': {
                'total_users': 0,
                'active_users': 0,
                'documents_uploaded': 0,
                'reviews_completed': 0
            },
            'trends': {
                'daily_uploads': [],
                'daily_reviews': []
            }
        }
        
        # Get file storage metrics
        files_result = supabase.from_('organization_files') \
            .select('size_bytes') \
            .execute()
        
        if files_result.data:
            sizes = [f.get('size_bytes', 0) for f in files_result.data if f.get('size_bytes')]
            usage_data['storage']['file_count'] = len(sizes)
            usage_data['storage']['total_bytes'] = sum(sizes)
            usage_data['storage']['avg_file_size'] = usage_data['storage']['total_bytes'] / len(sizes) if sizes else 0
        
        # Get activity metrics
        # Documents uploaded
        uploaded_result = supabase.from_('organization_files') \
            .select('id', count='exact') \
            .gte('uploaded_at', start_date) \
            .execute()
        usage_data['activity']['documents_uploaded'] = len(uploaded_result.data) if uploaded_result.data else 0
        
        # Reviews completed
        reviews_result = supabase.from_('manual_review_queue') \
            .select('id', count='exact') \
            .eq('status', 'completed') \
            .gte('completed_at', start_date) \
            .execute()
        usage_data['activity']['reviews_completed'] = len(reviews_result.data) if reviews_result.data else 0
        
        return {
            "success": True,
            "data": usage_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system usage: {str(e)}"
        )