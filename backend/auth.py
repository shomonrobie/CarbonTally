# backend/auth.py - Updated to work with or without parentheses

import os
import jwt
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
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
    "can_manage_billing": False,
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
    entity_id: Optional[str] = None
    extraction_count: Optional[int] = 0
    accuracy_rate: Optional[float] = 100.0
    is_staff: bool = False
    is_org_member: bool = False
    is_admin: bool = False
    role_name: Optional[str] = None

    # D20 (APPROVED 2026-08-20) — scope-aware authorization dimension:
    # ``staff_profiles.entity_id IS NULL`` = CarbonTally internal staff;
    # ``entity_id IS NOT NULL`` = Processing Entity staff. Role names are NOT
    # sufficient authority; scope is evaluated before any role/permission.
    @property
    def is_internal_staff(self) -> bool:
        """CarbonTally internal staff (``entity_id IS NULL``)."""
        return self.is_staff and not self.entity_id

    @property
    def is_entity_staff(self) -> bool:
        """Processing Entity staff (``entity_id IS NOT NULL``)."""
        return self.is_staff and bool(self.entity_id)

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
        user = None
        
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
        
        # ✅ FIX: Allow all authenticated users
        # Check if user is in staff_profiles
        staff_data = None
        is_staff = False
        
        try:
            staff_result = supabase_client.from_('staff_profiles') \
                .select('id, user_id, role_id, is_active, first_name, last_name, entity_id') \
                .eq('user_id', user_id) \
                .maybe_single() \
                .execute()
            
            if staff_result and staff_result.data:
                staff_data = staff_result.data
                is_staff = True
                print(f"✅ Found staff profile for user: {user_email}")

                # Resolve the authoritative staff role (staff_roles) so the
                # caller's role_name/permissions reflect the real permission
                # model (operator/reviewer/qc/admin). staff_profiles has no
                # `role` column (schema fact) — the role lives on staff_roles.
                staff_data['role_name'] = None
                staff_data['permissions'] = {}
                role_id = staff_data.get('role_id')
                if role_id:
                    try:
                        role_result = supabase_client.from_('staff_roles') \
                            .select('name, permissions') \
                            .eq('id', role_id) \
                            .maybe_single() \
                            .execute()
                        if role_result and role_result.data:
                            staff_data['role_name'] = role_result.data.get('name')
                            staff_data['permissions'] = role_result.data.get('permissions') or {}
                    except Exception as role_error:
                        print(f"⚠️ Staff role query error: {role_error}")
                
        except Exception as staff_error:
            print(f"⚠️ Staff profile query error: {staff_error}")
        
        # Check if user is in organization_members
        org_member_data = None
        is_org_member = False
        organization_id = None
        org_role = None
        
        try:
            org_result = supabase_client.from_('organization_members') \
                .select('id, organization_id, role, created_at, is_active') \
                .eq('user_id', user_id) \
                .eq('is_active', True) \
                .maybe_single() \
                .execute()
            
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
        
        # ✅ RETURN: Allow all authenticated users
        # Get user metadata from auth (GoTrue path only — the manual JWT-decode
        # fallback has no `user` object; metadata stays empty).
        user_metadata = {}
        if user is not None and hasattr(user, 'user_metadata'):
            user_metadata = user.user_metadata
        elif isinstance(user, dict) and user.get('user_metadata'):
            user_metadata = user.get('user_metadata', {})
        
        # Determine role
        role = "user"
        role_name = "user"
        permissions = {}
        
        if is_staff and staff_data:
            role = staff_data.get('role_name') or 'staff'
            role_name = role
            permissions = staff_data.get('permissions') or {}
        elif is_org_member and org_member_data:
            role = f"org_{org_role}" if org_role else "org_viewer"
            role_name = role
        
        return AuthUser(
            user_id=user_id,
            email=user_email,
            role=role,
            role_id=staff_data.get('role_id') if staff_data else None,
            role_name=role_name,
            permissions=permissions,
            is_active=True,
            first_name=staff_data.get('first_name') if staff_data else user_metadata.get('first_name'),
            last_name=staff_data.get('last_name') if staff_data else user_metadata.get('last_name'),
            organization_id=organization_id,
            entity_id=staff_data.get('entity_id') if staff_data else None,
            extraction_count=staff_data.get('extraction_count', 0) if staff_data else 0,
            accuracy_rate=staff_data.get('accuracy_rate', 100.0) if staff_data else 100.0,
            is_staff=is_staff,
            is_org_member=is_org_member,
            # D20: ``is_admin`` (global CarbonTally admin) is scoped to internal
            # staff only — a Processing Entity staff profile with an
            # ``admin``-named role must never become a global admin.
            is_admin=(
                is_staff
                and (staff_data.get('entity_id') if staff_data else None) is None
                and (role == 'admin' or role_name == 'admin')
            )
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
# AUTHENTICATION HELPERS - FIXED!
# ==========================================

def require_auth():
    """
    Dependency factory for authentication.
    Returns a callable that FastAPI can use as a dependency.
    Works with both: Depends(require_auth) and Depends(require_auth())
    """
    async def auth_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return current_user
    
    return auth_checker

def require_admin():
    """
    Dependency factory for admin privileges.
    Works with both: Depends(require_admin) and Depends(require_admin())
    """
    async def admin_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # D20 (scope-first): Processing Entity staff never hold internal
        # CarbonTally admin authority, regardless of the role name.
        if current_user.is_entity_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Processing Entity staff cannot hold internal admin authority",
            )

        if current_user.role != 'admin' and current_user.role_name != 'admin':
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        return current_user
    
    return admin_checker

def require_staff():
    """
    Dependency factory for staff membership.
    Works with both: Depends(require_staff) and Depends(require_staff())
    """
    async def staff_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not current_user.is_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Staff access required"
            )
        
        return current_user
    
    return staff_checker

def require_org_member():
    """
    Dependency factory for organization membership.
    Works with both: Depends(require_org_member) and Depends(require_org_member())
    """
    async def org_member_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not current_user.is_org_member:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Organization member access required"
            )
        
        return current_user
    
    return org_member_checker

def require_org_admin():
    """
    Dependency factory for organization admin privileges.
    Works with both: Depends(require_org_admin) and Depends(require_org_admin())

    Organisation administrators are the roles the schema's RLS treats as
    administrators of their own organisation: ``owner`` and ``admin``
    (``organization_members.role`` CHECK constraint; the RLS admin policies
    ``om_insert_admin`` / ``om_update_admin`` / ``om_select_self_or_admin`` use
    ``role IN ('owner','admin')``). Global CarbonTally admins pass too.
    """
    async def org_admin_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Global CarbonTally admin — D20 (scope-first): the global-admin path is
        # limited to CarbonTally INTERNAL staff (``entity_id IS NULL``). A
        # Processing Entity staff profile with an ``admin``-named role must
        # never pass as a global admin.
        if current_user.is_internal_staff and (current_user.role == 'admin' or current_user.role_name == 'admin'):
            return current_user

        # Org member holding the owner/admin role. ``get_current_user`` derives
        # ``role`` as ``org_<org_role>`` (e.g. ``org_owner``); the authoritative
        # fallback below re-reads the membership row.
        if current_user.is_org_member and current_user.organization_id:
            if (
                current_user.role in ('org_owner', 'org_admin')
                or current_user.role_name in ('owner', 'admin')
            ):
                return current_user
            # Authoritative fallback: resolve the membership role directly.
            # ``get_supabase_client()`` raises HTTPException(500) when Supabase
            # is not configured; that must not mask a 403 authz decision.
            try:
                supabase = get_supabase_client()
                result = supabase.from_('organization_members') \
                    .select('role') \
                    .eq('user_id', current_user.user_id) \
                    .eq('organization_id', current_user.organization_id) \
                    .maybe_single() \
                    .execute()

                if result and result.data and result.data.get('role') in ('admin', 'owner'):
                    return current_user
            except HTTPException:
                # Supabase unavailable → fail closed with 403 (never 500).
                pass
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization admin privileges required"
        )

    return org_admin_checker

def require_org_access(organization_id: str):
    """
    Dependency factory for organization access.
    Requires the organization_id parameter.
    """
    async def org_access_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        # CarbonTally INTERNAL staff may access any organization (operational
        # access). D20: Processing Entity staff never get customer-organization
        # access — they fall through to the org-membership check (denied).
        if current_user.is_internal_staff:
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

def require_entity_member(entity_id: str):
    """
    Dependency factory for Processing Entity membership (V3, ADR-V3-001).

    Mirrors ``require_org_access``: CarbonTally internal staff/admin may access
    any entity (entity administration is CarbonTally-internal); Processing
    Entity staff may only access their own entity. The positive NULL convention
    is preserved — CarbonTally internal staff carry ``entity_id=None``.
    """
    async def entity_member_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # CarbonTally internal staff/admin may act on any entity.
        if current_user.is_staff and not current_user.entity_id:
            return current_user

        # Processing Entity staff may only act on their own entity.
        if current_user.entity_id:
            if current_user.entity_id != entity_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You don't have access to this Processing Entity",
                )
            return current_user

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Processing Entity member access required",
        )

    return entity_member_checker

def require_role(required_roles: List[str]):
    """
    Dependency factory for role requirements.
    """
    async def role_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        # D20 (scope-first): Processing Entity staff never pass role-name
        # authorization guards, regardless of the role name.
        if current_user.is_entity_staff:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Processing Entity staff cannot hold role-name authority",
            )

        if current_user.role not in required_roles and current_user.role_name not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}. User has role: {current_user.role}"
            )
        return current_user
    
    return role_checker

def require_permission(permission: str):
    """
    Dependency factory for permission requirements.
    """
    async def permission_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
        if not current_user.permissions.get(permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}"
            )
        return current_user
    
    return permission_checker

def require_any_permission(permissions: List[str]):
    """Require any of the specified permissions."""
    async def permission_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
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
    async def permission_checker(
        current_user: AuthUser = Depends(get_current_user)
    ) -> AuthUser:
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

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_role_permissions(supabase_client: Client, role_id: str) -> Dict[str, bool]:
    """
    Get permissions for a role.
    This is an alias for get_role_permissions_from_db for backward compatibility.
    """
    return get_role_permissions_from_db(supabase_client, role_id)

async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[AuthUser]:
    """
    Get current user if authenticated, return None otherwise.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
    except Exception:
        return None