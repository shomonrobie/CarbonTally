# backend/routes/admin/beta.py
"""
Beta access management endpoints for managing beta codes and users.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from auth import AuthUser, get_current_user, get_current_user_optional, require_admin, require_auth
from database import get_supabase_client
import secrets
import string

router = APIRouter(prefix="/api/admin/beta", tags=["Admin - Beta Management"])

# ==========================================
# Pydantic Models
# ==========================================

class BetaCodeCreate(BaseModel):
    email: Optional[str] = None
    expires_in_days: int = 30
    status: str = "active"

class BetaCodeUpdate(BaseModel):
    status: str  # active, used, expired, revoked

class BetaCodeValidate(BaseModel):
    code: str

class BetaUserCreate(BaseModel):
    email: str
    beta_code: str
    access_level: str = "standard"  # standard, premium, admin

class BetaUserUpdate(BaseModel):
    access_level: Optional[str] = None
    beta_code: Optional[str] = None

# ==========================================
# Helper Functions
# ==========================================

def generate_beta_code() -> str:
    """Generate a random beta access code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(8))

# ==========================================
# Beta Code Endpoints
# ==========================================

@router.get("/codes")
async def get_beta_codes(
    current_user: AuthUser = Depends(require_admin()),
    status: Optional[str] = None,
    email: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get all beta access codes."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('beta_access_codes').select('*')
        
        if status:
            query = query.eq('status', status)
        if email:
            query = query.eq('email', email)
        
        result = query.order('created_at', desc=True) \
            .range(offset, offset + limit - 1) \
            .execute()
        
        # Get count
        count_query = supabase.from_('beta_access_codes').select('id', count='exact')
        if status:
            count_query = count_query.eq('status', status)
        if email:
            count_query = count_query.eq('email', email)
        count_result = count_query.execute()
        
        return {
            "success": True,
            "data": result.data,
            "total": len(count_result.data) if count_result.data else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get beta codes: {str(e)}"
        )

@router.post("/codes")
async def create_beta_code(
    code_data: BetaCodeCreate,
    current_user: AuthUser = Depends(require_admin())
):
    """Create a new beta access code."""
    try:
        supabase = get_supabase_client()
        
        # Generate unique code
        code = generate_beta_code()
        while True:
            # Check if code exists
            existing = supabase.from_('beta_access_codes') \
                .select('id') \
                .eq('code', code) \
                .maybe_single() \
                .execute()
            
            if not existing.data:
                break
            code = generate_beta_code()
        
        data = {
            'code': code,
            'email': code_data.email,
            'status': code_data.status,
            'expires_at': (datetime.utcnow() + timedelta(days=code_data.expires_in_days)).isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('beta_access_codes') \
            .insert(data) \
            .execute()
        
        return {
            "success": True,
            "message": "Beta code created successfully",
            "data": result.data[0] if result.data else None
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create beta code: {str(e)}"
        )

@router.put("/codes/{code_id}/status")
async def update_beta_code_status(
    code_id: str,
    update_data: BetaCodeUpdate,
    current_user: AuthUser = Depends(require_admin())
):
    """Update beta code status."""
    try:
        supabase = get_supabase_client()
        
        # Check if code exists
        existing = supabase.from_('beta_access_codes') \
            .select('id') \
            .eq('id', code_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beta code not found"
            )
        
        data = {
            'status': update_data.status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if update_data.status == 'used':
            data['used_at'] = datetime.utcnow().isoformat()
        
        result = supabase.from_('beta_access_codes') \
            .update(data) \
            .eq('id', code_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Beta code status updated",
            "data": result.data[0] if result.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update beta code: {str(e)}"
        )

@router.delete("/codes/{code_id}")
async def delete_beta_code(
    code_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """Delete a beta access code."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('beta_access_codes') \
            .delete() \
            .eq('id', code_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Beta code deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete beta code: {str(e)}"
        )

@router.get("/codes/validate/{code}")
async def validate_beta_code(
    code: str,
    current_user: Optional[AuthUser] = Depends(get_current_user_optional)

):
    """Validate a beta access code."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('beta_access_codes') \
            .select('*') \
            .eq('code', code) \
            .maybe_single() \
            .execute()
        
        if not result.data:
            return {
                "success": False,
                "valid": False,
                "message": "Invalid beta code"
            }
        
        beta_code = result.data
        
        # Check if expired
        if beta_code['expires_at']:
            expires_at = datetime.fromisoformat(beta_code['expires_at'].replace('Z', '+00:00'))
            if expires_at < datetime.utcnow().replace(tzinfo=expires_at.tzinfo):
                return {
                    "success": False,
                    "valid": False,
                    "message": "Beta code has expired"
                }
        
        # Check if used
        if beta_code['status'] == 'used':
            return {
                "success": False,
                "valid": False,
                "message": "Beta code has already been used"
            }
        
        if beta_code['status'] == 'revoked':
            return {
                "success": False,
                "valid": False,
                "message": "Beta code has been revoked"
            }
        
        return {
            "success": True,
            "valid": True,
            "data": {
                "code": beta_code['code'],
                "email": beta_code.get('email'),
                "status": beta_code['status'],
                "expires_at": beta_code['expires_at']
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate beta code: {str(e)}"
        )

# ==========================================
# Beta User Endpoints
# ==========================================

@router.get("/users")
async def get_beta_users(
    current_user: AuthUser = Depends(require_admin()),
    access_level: Optional[str] = None,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """Get all beta users."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('beta_users').select('*')
        
        if access_level:
            query = query.eq('access_level', access_level)
        
        result = query.order('created_at', desc=True) \
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
            detail=f"Failed to get beta users: {str(e)}"
        )

@router.post("/users")
async def create_beta_user(
    user_data: BetaUserCreate,
    current_user: AuthUser = Depends(require_admin())
):
    """Create a new beta user."""
    try:
        supabase = get_supabase_client()
        
        # Validate beta code
        code_result = supabase.from_('beta_access_codes') \
            .select('*') \
            .eq('code', user_data.beta_code) \
            .maybe_single() \
            .execute()
        
        if not code_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid beta code"
            )
        
        # Check if user already exists
        existing = supabase.from_('beta_users') \
            .select('id') \
            .eq('email', user_data.email) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User already has beta access"
            )
        
        data = {
            'email': user_data.email,
            'beta_code': user_data.beta_code,
            'access_level': user_data.access_level,
            'invited_by': current_user.id,
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('beta_users') \
            .insert(data) \
            .execute()
        
        # Mark beta code as used
        supabase.from_('beta_access_codes') \
            .update({'status': 'used', 'used_at': datetime.utcnow().isoformat()}) \
            .eq('code', user_data.beta_code) \
            .execute()
        
        return {
            "success": True,
            "message": "Beta user created successfully",
            "data": result.data[0] if result.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create beta user: {str(e)}"
        )

@router.put("/users/{user_id}/access")
async def update_beta_user_access(
    user_id: str,
    update_data: BetaUserUpdate,
    current_user: AuthUser = Depends(require_admin())
):
    """Update beta user access level."""
    try:
        supabase = get_supabase_client()
        
        # Check if user exists
        existing = supabase.from_('beta_users') \
            .select('id') \
            .eq('id', user_id) \
            .maybe_single() \
            .execute()
        
        if not existing.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Beta user not found"
            )
        
        data = update_data.dict(exclude_none=True)
        data['updated_at'] = datetime.utcnow().isoformat()
        
        result = supabase.from_('beta_users') \
            .update(data) \
            .eq('id', user_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Beta user access updated",
            "data": result.data[0] if result.data else None
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update beta user: {str(e)}"
        )

@router.delete("/users/{user_id}")
async def delete_beta_user(
    user_id: str,
    current_user: AuthUser = Depends(require_admin())
):
    """Delete a beta user."""
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('beta_users') \
            .delete() \
            .eq('id', user_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Beta user deleted successfully"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete beta user: {str(e)}"
        )

@router.get("/users/stats")
async def get_beta_stats(
    current_user: AuthUser = Depends(require_admin())
):
    """Get beta user statistics."""
    try:
        supabase = get_supabase_client()
        
        # Total beta users
        total_result = supabase.from_('beta_users') \
            .select('id', count='exact') \
            .execute()
        
        # By access level
        level_result = supabase.from_('beta_users') \
            .select('access_level', count='exact') \
            .execute()
        
        # Active vs inactive (last 30 days)
        active_result = supabase.from_('beta_users') \
            .select('id', count='exact') \
            .gte('last_active_at', (datetime.utcnow() - timedelta(days=30)).isoformat()) \
            .execute()
        
        # Beta codes stats
        codes_result = supabase.from_('beta_access_codes') \
            .select('status', count='exact') \
            .execute()
        
        stats = {
            'total_beta_users': len(total_result.data) if total_result.data else 0,
            'active_last_30_days': len(active_result.data) if active_result.data else 0,
            'by_access_level': {},
            'beta_codes': {}
        }
        
        if level_result.data:
            for item in level_result.data:
                stats['by_access_level'][item['access_level']] = stats['by_access_level'].get(item['access_level'], 0) + 1
        
        if codes_result.data:
            for item in codes_result.data:
                stats['beta_codes'][item['status']] = stats['beta_codes'].get(item['status'], 0) + 1
        
        return {"success": True, "data": stats}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get beta stats: {str(e)}"
        )