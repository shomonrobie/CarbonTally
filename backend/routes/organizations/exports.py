# backend/routes/organizations/exports.py
"""
Export management endpoints for emissions data and reports.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from auth import AuthUser, require_org_member, require_org_admin
from database import get_supabase_client
import csv
import io
import json
from uuid import UUID

router = APIRouter(prefix="/api/organizations/{org_id}/exports", tags=["Exports"])

# ==========================================
# Pydantic Models
# ==========================================

class ExportRequest(BaseModel):
    format: str = "csv"  # csv, json, pdf
    filters: Optional[Dict[str, Any]] = None
    date_range_start: Optional[str] = None
    date_range_end: Optional[str] = None
    include_metadata: bool = True

class ExportResponse(BaseModel):
    id: str
    file_name: str
    format: str
    status: str
    record_count: Optional[int] = None
    created_at: str
    expires_at: Optional[str] = None
    download_url: Optional[str] = None

# ==========================================
# Export Endpoints
# ==========================================

@router.post("/exports/emissions")
async def export_emissions_data(
    org_id: str,
    request: ExportRequest,
    current_user: AuthUser = Depends(require_org_member())
):
    """Generate an export of emissions data."""
    try:
        supabase = get_supabase_client()
        
        # Build query
        query = supabase.from_('emissions_logs') \
            .select('*, assets!left(name, type), defra_conversion_factors!left(activity_type, co2e_multiplier)') \
            .eq('organization_id', org_id)
        
        # Apply date filters
        if request.date_range_start:
            query = query.gte('start_date', request.date_range_start)
        if request.date_range_end:
            query = query.lte('end_date', request.date_range_end)
        
        # Apply custom filters
        if request.filters:
            for key, value in request.filters.items():
                if key in ['asset_id', 'created_by_user_id']:
                    query = query.eq(key, value)
        
        result = query.execute()
        
        if not result.data:
            return {
                "success": True,
                "message": "No data to export",
                "record_count": 0
            }
        
        # Generate file
        file_name = f"emissions_export_{org_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        if request.format == "csv":
            content = generate_csv_export(result.data)
            file_name += ".csv"
            mime_type = "text/csv"
        elif request.format == "json":
            content = json.dumps(result.data, indent=2, default=str)
            file_name += ".json"
            mime_type = "application/json"
        else:
            # PDF - you'd need to implement PDF generation
            content = json.dumps(result.data, indent=2, default=str)
            file_name += ".json"
            mime_type = "application/json"
        
        # Store export record
        export_data = {
            'organization_id': org_id,
            'user_id': current_user.user_id,
            'file_name': file_name,
            'format': request.format,
            'filters': request.filters,
            'record_count': len(result.data),
            'status': 'completed',
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + timedelta(days=7)).isoformat()
        }
        
        # In a real implementation, you'd save the file to S3/Storage
        # and store the URL. For now, we'll return the content directly.
        
        return Response(
            content=content,
            media_type=mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={file_name}",
                "X-Record-Count": str(len(result.data))
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate export: {str(e)}"
        )

@router.get("")
async def get_exports(
    org_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: AuthUser = Depends(require_org_member())
):
    """Get list of exports for an organization."""
    try:
        supabase = get_supabase_client()
        result = supabase.from_('export_history') \
            .select('*') \
            .eq('organization_id', org_id) \
            .order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(result.data)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get exports: {str(e)}"
        )

@router.get("/{export_id}/download")
async def download_export(
    org_id: str,
    export_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    """Download an exported file."""
    try:
        supabase = get_supabase_client()
        
        # Get export record
        result = supabase.from_('export_history') \
            .select('*') \
            .eq('id', export_id) \
            .eq('organization_id', org_id) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Export not found"
            )
        
        # Check if expired
        if result.data.get('expires_at'):
            expires_at = datetime.fromisoformat(result.data['expires_at'].replace('Z', '+00:00'))
            if expires_at < datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
                raise HTTPException(
                    status_code=status.HTTP_410_GONE,
                    detail="Export has expired"
                )
        
        # In a real implementation, you'd retrieve the file from storage
        # and stream it back. For now, we'll return the metadata.
        
        return {
            "success": True,
            "data": result.data,
            "message": "Download URL would be returned here"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download export: {str(e)}"
        )

@router.delete("/{export_id}")
async def delete_export(
    org_id: str,
    export_id: str,
    current_user: AuthUser = Depends(require_org_admin())
):
    """Delete an export record."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('export_history') \
            .delete() \
            .eq('id', export_id) \
            .eq('organization_id', org_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Export deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete export: {str(e)}"
        )

# ==========================================
# Helper Functions
# ==========================================

def generate_csv_export(data: List[Dict]) -> str:
    """Generate CSV from data."""
    if not data:
        return ""
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Get headers from first record
    headers = list(data[0].keys())
    writer.writerow(headers)
    
    # Write data
    for record in data:
        row = []
        for header in headers:
            value = record.get(header)
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            elif value is None:
                value = ""
            row.append(value)
        writer.writerow(row)
    
    return output.getvalue()