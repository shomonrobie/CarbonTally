# Create new file: backend/routes/admin/settings.py

"""
System settings management endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from auth import AuthUser, require_admin
from database import get_supabase_client

router = APIRouter(prefix="/api/admin/settings", tags=["Admin - Settings"])

# ==========================================
# Pydantic Models
# ==========================================

class SettingsUpdate(BaseModel):
    max_file_size_mb: Optional[int] = None
    allowed_file_types: Optional[List[str]] = None
    enable_auto_repair: Optional[bool] = None
    max_batch_files: Optional[int] = None
    max_total_batch_size_mb: Optional[int] = None
    data_retention_days: Optional[int] = None
    require_2fa: Optional[bool] = None
    session_timeout_minutes: Optional[int] = None
    max_login_attempts: Optional[int] = None

class SettingsReset(BaseModel):
    confirm: bool = True

# ==========================================
# Settings Endpoints
# ==========================================

@router.get("/settings-history")
async def get_settings_history(
    current_user: AuthUser = Depends(require_admin()),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get settings change history."""
    try:
        supabase = get_supabase_client()
        
        # Since we don't have a settings_history table, we'll simulate it
        # In production, you'd have an audit log table
        
        result = supabase.from_('system_settings') \
            .select('*') \
            .order('updated_at', desc=True) \
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
            detail=f"Failed to get settings history: {str(e)}"
        )

@router.post("/validate")
async def validate_settings(
    settings: SettingsUpdate,
    current_user: AuthUser = Depends(require_admin())
):
    """Validate settings before applying."""
    try:
        validation_results = {
            'valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Validate max_file_size_mb
        if settings.max_file_size_mb is not None:
            if settings.max_file_size_mb < 1:
                validation_results['valid'] = False
                validation_results['errors'].append('max_file_size_mb must be at least 1')
            elif settings.max_file_size_mb > 500:
                validation_results['warnings'].append('max_file_size_mb is very large (> 500MB)')
        
        # Validate max_batch_files
        if settings.max_batch_files is not None:
            if settings.max_batch_files < 1:
                validation_results['valid'] = False
                validation_results['errors'].append('max_batch_files must be at least 1')
        
        # Validate data_retention_days
        if settings.data_retention_days is not None:
            if settings.data_retention_days < 1:
                validation_results['valid'] = False
                validation_results['errors'].append('data_retention_days must be at least 1')
        
        # Validate session_timeout_minutes
        if settings.session_timeout_minutes is not None:
            if settings.session_timeout_minutes < 5:
                validation_results['valid'] = False
                validation_results['errors'].append('session_timeout_minutes must be at least 5')
        
        return {
            "success": True,
            "data": validation_results
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate settings: {str(e)}"
        )

@router.post("/reset")
async def reset_settings(
    reset_data: SettingsReset,
    current_user: AuthUser = Depends(require_admin())
):
    """Reset settings to default values."""
    try:
        if not reset_data.confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation required"
            )
        
        supabase = get_supabase_client()
        
        # Default settings
        default_settings = {
            'max_file_size_mb': 50,
            'allowed_file_types': ['csv', 'pdf', 'xlsx', 'xls'],
            'enable_auto_repair': True,
            'max_batch_files': 20,
            'max_total_batch_size_mb': 200,
            'data_retention_days': 365,
            'require_2fa': False,
            'session_timeout_minutes': 60,
            'max_login_attempts': 5,
            'updated_at': datetime.utcnow().isoformat(),
            'updated_by': current_user.id
        }
        
        # Update settings
        result = supabase.from_('system_settings') \
            .update(default_settings) \
            .eq('id', '1') \
            .execute()
        
        return {
            "success": True,
            "message": "Settings reset to default values",
            "data": default_settings
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset settings: {str(e)}"
        )