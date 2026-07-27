# backend/routes/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
import secrets
from auth import AuthUser, get_current_user
from database import get_supabase_client

router = APIRouter(prefix="/api/users", tags=["User Management"])

# ==========================================
# PYDANTIC MODELS
# ==========================================

class PasswordResetRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")

class PasswordResetConfirm(BaseModel):
    token: str = Field(..., description="Reset token from email")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

class PasswordChangeRequest(BaseModel):
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password (min 8 characters)")

class ProfileUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None)
    avatar_url: Optional[str] = Field(None)

class UserProfileResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    phone: Optional[str] = None
    created_at: datetime
    is_staff: bool = False
    is_org_member: bool = False
    organization_id: Optional[str] = None
    organization_name: Optional[str] = None
    role: Optional[str] = None

# ==========================================
# ENDPOINTS
# ==========================================

@router.post("/password-reset")
async def request_password_reset(
    request: PasswordResetRequest
):
    """
    Request a password reset email.
    """
    try:
        supabase = get_supabase_client()
        
        # Check if user exists
        user_result = supabase.from_('auth.users') \
            .select('id, email') \
            .eq('email', request.email) \
            .maybe_single() \
            .execute()
        
        if not user_result.data:
            # Don't reveal if user exists or not for security
            return {
                "success": True,
                "message": "If an account exists with this email, a reset link has been sent."
            }
        
        # Generate reset token
        reset_token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)
        
        # Store reset token
        supabase.from_('password_reset_tokens') \
            .upsert({
                'user_id': user_result.data['id'],
                'token': reset_token,
                'expires_at': expires_at.isoformat(),
                'used': False
            }, on_conflict='user_id') \
            .execute()
        
        # Send reset email
        try:
            from utils.email import send_password_reset_email
            await send_password_reset_email(
                email=request.email,
                reset_token=reset_token
            )
        except Exception as e:
            print(f"⚠️ Failed to send reset email: {e}")
            # Continue - user will be notified
        
        return {
            "success": True,
            "message": "If an account exists with this email, a reset link has been sent."
        }
        
    except Exception as e:
        print(f"❌ Error requesting password reset: {e}")
        # Don't reveal error details for security
        return {
            "success": True,
            "message": "If an account exists with this email, a reset link has been sent."
        }

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    request: PasswordResetConfirm
):
    """
    Confirm password reset with token.
    """
    try:
        supabase = get_supabase_client()
        
        # Validate token
        token_result = supabase.from_('password_reset_tokens') \
            .select('user_id, expires_at, used') \
            .eq('token', request.token) \
            .eq('used', False) \
            .maybe_single() \
            .execute()
        
        if not token_result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        # Check if expired
        expires_at = datetime.fromisoformat(token_result.data['expires_at'].replace('Z', '+00:00'))
        if datetime.utcnow() > expires_at:
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Reset token has expired"
            )
        
        # Update user password using Supabase admin API
        from supabase import Client
        supabase_admin: Client = get_supabase_client()
        
        try:
            supabase_admin.auth.admin.update_user_by_id(
                token_result.data['user_id'],
                {"password": request.new_password}
            )
        except Exception as e:
            print(f"❌ Error updating password: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password. Please try again."
            )
        
        # Mark token as used
        supabase.from_('password_reset_tokens') \
            .update({'used': True, 'used_at': datetime.now().isoformat()}) \
            .eq('token', request.token) \
            .execute()
        
        return {
            "success": True,
            "message": "Password reset successfully. You can now login with your new password."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error confirming password reset: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Get current user's profile.
    """
    try:
        # Get organization details if applicable
        organization_name = None
        if current_user.organization_id:
            supabase = get_supabase_client()
            org_result = supabase.from_('organizations') \
                .select('name') \
                .eq('id', current_user.organization_id) \
                .maybe_single() \
                .execute()
            
            if org_result.data:
                organization_name = org_result.data.get('name')
        
        return UserProfileResponse(
            id=current_user.user_id,
            email=current_user.email,
            first_name=current_user.first_name,
            last_name=current_user.last_name,
            full_name=f"{current_user.first_name or ''} {current_user.last_name or ''}".strip() or current_user.email,
            avatar_url=None,  # Could be fetched from user metadata
            phone=None,  # Could be fetched from user metadata
            created_at=datetime.now(),  # Could be fetched from auth.users
            is_staff=current_user.is_staff,
            is_org_member=current_user.is_org_member,
            organization_id=current_user.organization_id,
            organization_name=organization_name,
            role=current_user.role
        )
        
    except Exception as e:
        print(f"❌ Error getting user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user profile: {str(e)}"
        )

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    update_data: ProfileUpdate,
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Update current user's profile.
    """
    try:
        supabase = get_supabase_client()
        
        # Update user metadata in auth
        from supabase import Client
        supabase_admin: Client = get_supabase_client()
        
        metadata = {}
        if update_data.first_name:
            metadata['first_name'] = update_data.first_name
        if update_data.last_name:
            metadata['last_name'] = update_data.last_name
        if update_data.phone:
            metadata['phone'] = update_data.phone
        if update_data.avatar_url:
            metadata['avatar_url'] = update_data.avatar_url
        
        if metadata:
            try:
                supabase_admin.auth.admin.update_user_by_id(
                    current_user.user_id,
                    {"user_metadata": metadata}
                )
            except Exception as e:
                print(f"❌ Error updating user metadata: {e}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to update profile"
                )
        
        # Update staff profile if staff
        if current_user.is_staff:
            staff_update = {}
            if update_data.first_name:
                staff_update['first_name'] = update_data.first_name
            if update_data.last_name:
                staff_update['last_name'] = update_data.last_name
            
            if staff_update:
                supabase.from_('staff_profiles') \
                    .update(staff_update) \
                    .eq('id', current_user.user_id) \
                    .execute()
        
        # Return updated profile
        return await get_user_profile(current_user)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error updating user profile: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: AuthUser = Depends(get_current_user)
):
    """
    Change user's password.
    """
    try:
        supabase = get_supabase_client()
        
        # Verify current password
        try:
            auth_response = supabase.auth.sign_in_with_password({
                "email": current_user.email,
                "password": request.current_password
            })
            
            if not auth_response or not auth_response.user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Current password is incorrect"
                )
        except Exception as e:
            print(f"❌ Password verification error: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Update password
        from supabase import Client
        supabase_admin: Client = get_supabase_client()
        
        try:
            supabase_admin.auth.admin.update_user_by_id(
                current_user.user_id,
                {"password": request.new_password}
            )
        except Exception as e:
            print(f"❌ Error updating password: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update password"
            )
        
        return {
            "success": True,
            "message": "Password updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error changing password: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )