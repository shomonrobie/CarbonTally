# backend/routes/organizations/dashboard.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime, timedelta
from auth import AuthUser, require_org_member
from database import get_supabase_client

router = APIRouter(prefix="/api/organizations", tags=["Organization Dashboard"])

# ==========================================
# ✅ FIXED: Use org_id from path, not current_user.organization_id
# ==========================================

@router.get("/{org_id}/dashboard-summary")
async def get_dashboard_summary(
    org_id: str,  # ✅ Add org_id parameter
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get dashboard summary for the organization.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Verify user has access to this organization
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
        
        # Get organization details
        org_result = supabase.from_('organizations') \
            .select('name, created_at') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        
        org_name = org_result.data.get('name') if org_result.data else None
        
        # Current year
        current_year = datetime.now().year
        year_start = f"{current_year}-01-01"
        year_end = f"{current_year}-12-31"
        
        # Get emissions data
        emissions_result = supabase.from_('emissions_logs') \
            .select('calculated_kg_co2e, start_date, metadata') \
            .eq('organization_id', org_id) \
            .gte('start_date', year_start) \
            .lte('start_date', year_end) \
            .execute()
        
        records = emissions_result.data or []
        
        # Calculate totals
        total_kg = sum(r.get('calculated_kg_co2e', 0) for r in records)
        total_tonnes = total_kg / 1000
        
        # Calculate scope breakdown
        scope_breakdown = {
            'scope1': 0,
            'scope2': 0,
            'scope3': 0
        }
        
        for record in records:
            scope = record.get('metadata', {}).get('scope', 'Unknown')
            if scope == 'Scope 1' or scope == '1':
                scope_breakdown['scope1'] += record.get('calculated_kg_co2e', 0)
            elif scope == 'Scope 2' or scope == '2':
                scope_breakdown['scope2'] += record.get('calculated_kg_co2e', 0)
            elif scope == 'Scope 3' or scope == '3':
                scope_breakdown['scope3'] += record.get('calculated_kg_co2e', 0)
        
        # Convert to tonnes
        scope_breakdown = {k: v / 1000 for k, v in scope_breakdown.items()}
        
        # Get monthly breakdown
        monthly_data = {}
        for record in records:
            date_str = record.get('start_date', '')
            if date_str:
                month = date_str[:7]  # YYYY-MM
                monthly_data[month] = monthly_data.get(month, 0) + record.get('calculated_kg_co2e', 0)
        
        # Get member count
        members_result = supabase.from_('organization_members') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .execute()
        
        # Get recent activity
        recent_result = supabase.from_('emissions_logs') \
            .select('''
                id,
                start_date,
                calculated_kg_co2e,
                metadata,
                assets (name),
                emission_factors (activity_type)
            ''') \
            .eq('organization_id', org_id) \
            .order('start_date', desc=True) \
            .limit(10) \
            .execute()
        
        recent_activity = []
        for record in recent_result.data or []:
            recent_activity.append({
                'id': record['id'],
                'date': record.get('start_date'),
                'kg_co2e': record.get('calculated_kg_co2e', 0),
                'tonnes_co2e': record.get('calculated_kg_co2e', 0) / 1000,
                'asset': record.get('assets', {}).get('name'),
                'activity_type': (record.get('emission_factors') or {}).get('activity_type'),
                'metadata': record.get('metadata', {})
            })
        
        # Calculate month-over-month change
        months = sorted(monthly_data.keys())
        monthly_change = 0
        if len(months) >= 2:
            last_month = months[-1]
            prev_month = months[-2]
            if monthly_data.get(prev_month, 0) > 0:
                monthly_change = ((monthly_data.get(last_month, 0) - monthly_data.get(prev_month, 0)) / 
                                 monthly_data.get(prev_month, 0)) * 100
        
        return {
            "organization_id": org_id,
            "organization_name": org_name,
            "year": current_year,
            "summary": {
                "total_emissions_kg": total_kg,
                "total_emissions_tonnes": total_tonnes,
                "total_records": len(records),
                "total_members": members_result.count or 0,
                "month_over_month_change": monthly_change
            },
            "scope_breakdown": scope_breakdown,
            "monthly_breakdown": {k: v / 1000 for k, v in monthly_data.items()},
            "recent_activity": recent_activity
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting dashboard summary: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get dashboard summary: {str(e)}"
        )


@router.get("/{org_id}/organization-activity")
async def get_organization_activity(
    org_id: str,  # ✅ Add org_id parameter
    days: int = Query(30, description="Number of days to look back"),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get recent organization activity.
    """
    try:
        supabase = get_supabase_client()
        
        # ✅ Verify user has access to this organization
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
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get recent emissions
        emissions_result = supabase.from_('emissions_logs') \
            .select('''
                id,
                start_date,
                calculated_kg_co2e,
                created_at,
                metadata,
                assets (name),
                emission_factors (activity_type)
            ''') \
            .eq('organization_id', org_id) \
            .gte('created_at', cutoff_date.isoformat()) \
            .order('created_at', desc=True) \
            .limit(50) \
            .execute()
        
        # Get recent members joined
        #
        # F-05-R2.2: this embed selected two columns that do not exist on the
        # canonical schema — ``organization_members.joined_at`` and
        # ``users.raw_user_meta_data`` (``public.users`` carries ``first_name`` /
        # ``last_name``; the mirror has no metadata column). PostgREST answered
        # ``42703 column users_1.raw_user_meta_data does not exist`` and the
        # whole activity feed returned HTTP 500.
        members_result = supabase.from_('organization_members') \
            .select('''
                id,
                role,
                created_at,
                users!inner (email, first_name, last_name)
            ''') \
            .eq('organization_id', org_id) \
            .gte('created_at', cutoff_date.isoformat()) \
            .order('created_at', desc=True) \
            .limit(20) \
            .execute()
        
        # Format activity
        activities = []
        
        for record in emissions_result.data or []:
            activities.append({
                'type': 'emission_added',
                'timestamp': record.get('created_at'),
                'details': {
                    'kg_co2e': record.get('calculated_kg_co2e', 0),
                    'tonnes_co2e': record.get('calculated_kg_co2e', 0) / 1000,
                    # F-05-R4: a NULL embedded relation must not raise.
                    'asset': (record.get('assets') or {}).get('name'),
                    'activity_type': (record.get('emission_factors') or {}).get('activity_type'),
                    'date': record.get('start_date')
                }
            })
        
        for record in members_result.data or []:
            user_data = record.get('users') or {}
            # ``public.users`` has no ``full_name`` column — compose it.
            full_name = " ".join(
                part
                for part in (user_data.get('first_name'), user_data.get('last_name'))
                if part
            ) or None
            activities.append({
                'type': 'member_joined',
                'timestamp': record.get('created_at'),
                'details': {
                    'email': user_data.get('email'),
                    'full_name': full_name,
                    'role': record.get('role')
                }
            })
        
        # Sort by timestamp
        activities.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return {
            "organization_id": org_id,
            "period_days": days,
            "activities": activities[:50],
            "total": len(activities)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error getting organization activity: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get organization activity: {str(e)}"
        )