# backend/utils/organization_utils.py
"""
Organization-related utility functions.
Shared across multiple modules.
"""

from typing import Optional, Dict, List, Any
from supabase import Client

async def get_organization_name(supabase_client: Client, org_id: str) -> Optional[str]:
    """
    Get organization name by ID.
    
    Args:
        supabase_client: Supabase client instance
        org_id: Organization ID
    
    Returns:
        Organization name or None if not found
    """
    try:
        result = supabase_client.from_('organizations') \
            .select('name') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        return result.data.get('name') if result.data else None
    except Exception:
        return None

async def get_organization_by_id(supabase_client: Client, org_id: str) -> Optional[Dict]:
    """
    Get full organization details by ID.
    
    Args:
        supabase_client: Supabase client instance
        org_id: Organization ID
    
    Returns:
        Organization data or None if not found
    """
    try:
        result = supabase_client.from_('organizations') \
            .select('*') \
            .eq('id', org_id) \
            .maybe_single() \
            .execute()
        return result.data if result.data else None
    except Exception:
        return None
async def get_organization_stats(supabase_client: Client, org_id: str) -> Dict:
    """
    Get statistics for an organization.
    
    Args:
        supabase_client: Supabase client instance
        org_id: Organization ID
    
    Returns:
        Dictionary with organization statistics
    """
    try:
        stats = {
            'total_members': 0,
            'total_assets': 0,
            'total_facilities': 0,
            'total_emissions': 0,
            'total_documents': 0
        }
        
        # Get members count
        members_result = supabase_client.from_('organization_members') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .execute()
        stats['total_members'] = members_result.count or 0
        
        # Get facilities count
        facilities_result = supabase_client.from_('facilities') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .execute()
        stats['total_facilities'] = facilities_result.count or 0
        
        # ✅ Get assets count through facilities
        # First get facility IDs
        facilities = supabase_client.from_('facilities') \
            .select('id') \
            .eq('organization_id', org_id) \
            .execute()
        
        if facilities.data:
            facility_ids = [f['id'] for f in facilities.data]
            assets_result = supabase_client.from_('assets') \
                .select('id', count='exact') \
                .in_('facility_id', facility_ids) \
                .execute()
            stats['total_assets'] = assets_result.count or 0
        else:
            stats['total_assets'] = 0
        
        # Get emissions count
        emissions_result = supabase_client.from_('emissions_logs') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .execute()
        stats['total_emissions'] = emissions_result.count or 0
        
        # Get documents count
        documents_result = supabase_client.from_('organization_files') \
            .select('id', count='exact') \
            .eq('organization_id', org_id) \
            .execute()
        stats['total_documents'] = documents_result.count or 0
        
        return stats
        
    except Exception as e:
        print(f"⚠️ Error getting organization stats: {e}")
        import traceback
        traceback.print_exc()
        return {
            'total_members': 0,
            'total_assets': 0,
            'total_facilities': 0,
            'total_emissions': 0,
            'total_documents': 0
        }

async def get_facility_stats(supabase_client: Client, facility_id: str) -> Dict:
    """
    Get statistics for a facility.
    
    Args:
        supabase_client: Supabase client instance
        facility_id: Facility ID
    
    Returns:
        Dictionary with facility statistics
    """
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
        
        return {
            'asset_count': asset_count,
            'emissions_count': emissions_count
        }
        
    except Exception as e:
        print(f"⚠️ Error getting facility stats: {e}")
        return {'asset_count': 0, 'emissions_count': 0}

async def get_organization_members(supabase_client: Client, org_id: str, limit: int = 100) -> List[Dict]:
    """
    Get members of an organization.
    
    Args:
        supabase_client: Supabase client instance
        org_id: Organization ID
        limit: Maximum number of members to return
    
    Returns:
        List of organization members
    """
    try:
        result = supabase_client.from_('organization_members') \
            .select('*, users!inner(email, user_metadata)') \
            .eq('organization_id', org_id) \
            .eq('is_active', True) \
            .limit(limit) \
            .execute()
        return result.data if result.data else []
    except Exception:
        return []

async def get_organization_assets(supabase_client: Client, org_id: str) -> List[Dict]:
    """
    Get all assets for an organization.
    
    Args:
        supabase_client: Supabase client instance
        org_id: Organization ID
    
    Returns:
        List of assets
    """
    try:
        # Get facilities first
        facilities_result = supabase_client.from_('facilities') \
            .select('id') \
            .eq('organization_id', org_id) \
            .execute()
        
        if not facilities_result.data:
            return []
        
        facility_ids = [f['id'] for f in facilities_result.data]
        
        # Get assets for all facilities
        result = supabase_client.from_('assets') \
            .select('*, facilities!inner(name)') \
            .in_('facility_id', facility_ids) \
            .execute()
        
        return result.data if result.data else []
        
    except Exception as e:
        print(f"⚠️ Error getting organization assets: {e}")
        return []
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
