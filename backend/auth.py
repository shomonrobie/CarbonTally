# backend/auth.py - COMPLETE FIXED VERSION

import os
import jwt
from datetime import datetime
from typing import Optional, Dict, List, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# ==========================================
# DEFAULT PERMISSIONS (Fallback only)
# ==========================================

DEFAULT_STAFF_PERMISSIONS = {
    "can_view_all": False,
    "can_manage_staff": False,
    "can_manage_roles": False,
    "can_view_organizations": False,
    "can_manage_organizations": False,
    "can_extract": False,
    "can_process": False,
    "can_review": False,
    "can_approve": False,
    "can_export": False,
    "can_delete": False,
}

DEFAULT_ORG_PERMISSIONS = {
    "can_view_org_data": False,
    "can_edit_org_data": False,
    "can_delete_org_data": False,
    "can_manage_org_members": False,
    "can_generate_reports": False,
    "can_export_org_data": False,
}

# ==========================================
# PYDANTIC MODELS
# ==========================================

class AuthUser(BaseModel):
    """Authenticated user model."""
    user_id: str
    email: str
    role: str
    role_id: Optional[str] = None
    permissions: Dict[str, bool] = {}
    is_active: bool = True
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_id: Optional[str] = None
    extraction_count: Optional[int] = 0
    accuracy_rate: Optional[float] = 100.0
    is_staff: bool = False
    is_org_member: bool = False
    role_name: Optional[str] = None

# ==========================================
# SUPABASE CLIENT
# ==========================================

def get_supabase_client() -> Client:
    """Get Supabase client instance."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration missing"
        )
    
    try:
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        return client
    except Exception as e:
        print(f"❌ Supabase client creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Supabase client: {str(e)}"
        )

# ==========================================
# SECURITY
# ==========================================

security = HTTPBearer()

# ==========================================
# PERMISSION HELPERS
# ==========================================

def get_role_permissions_from_db(supabase_client: Client, role_id: str) -> Dict[str, bool]:
    """Get permissions from database for a specific role."""
    try:
        result = supabase_client.from_('roles') \
            .select('permissions') \
            .eq('id', role_id) \
            .maybe_single() \
            .execute()
        
        if result and result.data:
            permissions = result.data.get('permissions', {})
            if isinstance(permissions, dict):
                return permissions
        
        return {}
        
    except Exception as e:
        print(f"⚠️ Error fetching permissions from database: {e}")
        return {}

# ==========================================
# MAIN AUTHENTICATION FUNCTION
# ==========================================
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> AuthUser:
    """Get current authenticated user."""
    try:
        token = credentials.credentials
        supabase_client = get_supabase_client()
        
        print(f"🔍 Authenticating user...")
        
        # Verify token with Supabase
        try:
            user_response = supabase_client.auth.get_user(token)
            
            if not user_response or not user_response.user:
                print("❌ No user found in token response")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication credentials"
                )
            
            user = user_response.user
            user_id = user.id
            user_email = user.email
            
            print(f"✅ User authenticated: {user_email} (ID: {user_id})")
            
        except Exception as auth_error:
            print(f"❌ Auth error: {auth_error}")
            try:
                if SUPABASE_JWT_SECRET:
                    decoded = jwt.decode(
                        token, 
                        SUPABASE_JWT_SECRET, 
                        algorithms=["HS256"],
                        options={"verify_signature": True}
                    )
                    user_id = decoded.get('sub')
                    user_email = decoded.get('email')
                    print(f"✅ Token decoded manually: {user_email}")
                else:
                    raise
            except Exception as decode_error:
                print(f"❌ Token decode failed: {decode_error}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid authentication token"
                )
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No user ID found in token"
            )
        
        # Check if user is in staff_profiles
        staff_data = None
        is_staff = False
        
        try:
            staff_result = supabase_client.from_('staff_profiles') \
                .select('''
                    id,
                    role,
                    role_id,
                    is_active,
                    first_name,
                    last_name,
                    permissions,
                    extraction_count,
                    accuracy_rate,
                    last_login,
                    roles (
                        id,
                        name,
                        description,
                        permissions
                    )
                ''') \
                .eq('id', user_id) \
                .maybe_single() \
                .execute()
            
            if staff_result and staff_result.data:
                staff_data = staff_result.data
                is_staff = True
                print(f"✅ Found staff profile for user: {user_email}")
                
        except Exception as staff_error:
            print(f"⚠️ Staff profile query error: {staff_error}")
        
        # Check if user is in organization_members
        org_member_data = None
        is_org_member = False
        organization_id = None
        org_role = None
        
        try:
            # ✅ Now with is_active column
            org_result = supabase_client.from_('organization_members').select(
                'id, organization_id, role, created_at, is_active'
            ).eq('user_id', user_id).eq('is_active', True).maybe_single().execute()
            
            if org_result and org_result.data:
                org_member_data = org_result.data
                is_org_member = True
                organization_id = org_member_data.get('organization_id')
                org_role = org_member_data.get('role')
                print(f"✅ Found active organization member: {user_email} (Org: {organization_id}, Role: {org_role})")
            else:
                print(f"ℹ️ User {user_email} is not an active organization member")
                
        except Exception as org_error:
            print(f"⚠️ Organization member query error: {org_error}")
                
        except Exception as org_error:
            print(f"⚠️ Organization member query error: {org_error}")
        
        # Determine user's role and permissions
        if is_staff and staff_data:
            # Staff user
            role_id = staff_data.get('role_id')
            role_name = staff_data.get('role', 'viewer')
            
            # Get permissions from database
            permissions = {}
            if role_id:
                db_permissions = get_role_permissions_from_db(supabase_client, role_id)
                if db_permissions:
                    permissions = db_permissions
                    print(f"✅ Loaded permissions from database for role: {role_name}")
                else:
                    permissions = DEFAULT_STAFF_PERMISSIONS.copy()
                    print(f"⚠️ Using default permissions for role: {role_name}")
            else:
                permissions = DEFAULT_STAFF_PERMISSIONS.copy()
            
            # Merge custom permissions
            if staff_data.get('permissions'):
                if isinstance(staff_data['permissions'], dict):
                    permissions.update(staff_data['permissions'])
                    print(f"✅ Merged custom permissions for staff member")
            
            # Check if staff account is active
            if not staff_data.get('is_active', False):
                print(f"❌ Staff account inactive: {user_email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Staff account is inactive"
                )
            
            return AuthUser(
                user_id=user_id,
                email=user_email,
                role=role_name,
                role_id=role_id,
                role_name=role_name,
                permissions=permissions,
                is_active=staff_data.get('is_active', True),
                first_name=staff_data.get('first_name'),
                last_name=staff_data.get('last_name'),
                organization_id=organization_id,
                extraction_count=staff_data.get('extraction_count', 0),
                accuracy_rate=staff_data.get('accuracy_rate', 100.0),
                is_staff=True,
                is_org_member=is_org_member
            )
        
        elif is_org_member and org_member_data:
            # Organization member (not staff)
            org_role_name = f"org_{org_role}" if org_role else "org_viewer"
            permissions = DEFAULT_ORG_PERMISSIONS.copy()
            
            print(f"✅ User {user_email} is an organization member with role: {org_role}")
            
            return AuthUser(
                user_id=user_id,
                email=user_email,
                role=org_role_name,
                role_id=None,
                role_name=org_role_name,
                permissions=permissions,
                is_active=True,
                first_name=None,
                last_name=None,
                organization_id=organization_id,
                extraction_count=0,
                accuracy_rate=100.0,
                is_staff=False,
                is_org_member=True
            )
        
        else:
            # No access
            print(f"❌ User {user_email} has no access (not staff and not org member)")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User does not have access to this system"
            )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication failed: {str(e)}"
        )
# ==========================================
# AUTHORIZATION HELPERS - FIXED
# ==========================================

def require_role(required_roles: List[str]):
    """
    Dependency factory to require specific roles.
    Returns a callable that FastAPI can use as a dependency.
    """
    async def role_checker(current_user: AuthUser = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}. User has role: {current_user.role}"
            )
        return current_user
    return role_checker  # ✅ Returns the callable

def require_permission(permission: str):
    """
    Dependency factory to require specific permission.
    Returns a callable that FastAPI can use as a dependency.
    """
    async def permission_checker(current_user: AuthUser = Depends(get_current_user)):
        if not current_user.permissions.get(permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )
        return current_user
    return permission_checker  # ✅ Returns the callable

def require_any_permission(permissions: List[str]):
    """Require any of the specified permissions."""
    async def permission_checker(current_user: AuthUser = Depends(get_current_user)):
        has_permission = any(
            current_user.permissions.get(perm, False) 
            for perm in permissions
        )
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required any permission from: {', '.join(permissions)}"
            )
        return current_user
    return permission_checker

def require_all_permissions(permissions: List[str]):
    """Require all specified permissions."""
    async def permission_checker(current_user: AuthUser = Depends(get_current_user)):
        missing = [
            perm for perm in permissions 
            if not current_user.permissions.get(perm, False)
        ]
        if missing:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing permissions: {', '.join(missing)}"
            )
        return current_user
    return permission_checker

def require_staff():
    """Require user to be a staff member."""
    async def staff_checker(current_user: AuthUser = Depends(get_current_user)):
        if not current_user.is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff access required"
            )
        return current_user
    return staff_checker

def require_org_member():
    """
    Require user to be an active organization member.
    """
    async def org_checker(current_user: AuthUser = Depends(get_current_user)):
        if not current_user.is_org_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization member access required"
            )
        # Check if the organization member is active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization member account is inactive"
            )
        return current_user
    return org_checker


def require_org_access(organization_id: str):
    """
    Require access to a specific organization.
    Staff can access any organization, members can only access their own.
    """
    async def org_access_checker(current_user: AuthUser = Depends(get_current_user)):
        # Staff can access any organization
        if current_user.is_staff:
            return current_user
        
        # Organization members can only access their own
        if current_user.is_org_member:
            if current_user.organization_id != organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this organization's data"
                )
            return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    return org_access_checker
def get_role_permissions(supabase_client, role_id: str) -> Dict[str, bool]:
    """
    Get permissions for a role.
    This is an alias for get_role_permissions_from_db for backward compatibility.
    """
    return get_role_permissions_from_db(supabase_client, role_id)
