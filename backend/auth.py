# backend/auth.py - Updated to work with or without parentheses

import os
import jwt
from datetime import datetime
from typing import Optional, Dict, List, Any, Callable
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from supabase import Client
from dotenv import load_dotenv

# Phase 3 / P1-A — the service-role Supabase client is owned by
# ``infra.supabase`` (the architecture's single place that constructs Supabase
# clients). Reusing it here stops the per-request client creation that leaked
# file descriptors until the process exhausted its FD limit.
from infra.supabase import get_service_client


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
    """Return the process-wide service-role Supabase client.

    Phase 3 / P1-A — the previous implementation created a NEW service-role
    client on every call, leaking file descriptors under sustained load until
    the process hit its FD limit and every authenticated request returned
    ``500 ... Too many open files``. The process-wide singleton owned by
    ``infra.supabase`` is now reused. Service-role authority, the repository
    layer's RLS-bypass behaviour and the explicit ``SUPABASE_SERVICE_KEY``
    requirement are all preserved.
    """
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration missing"
        )
    
    try:
        return get_service_client()
    except Exception as e:
        print(f"❌ Supabase client creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize Supabase client: {str(e)}"
        )

# ==========================================
# SECURITY
# ==========================================

# WS3 / API-0001 — HTTPBearer(auto_error=False): a *missing* Authorization
# header now flows into get_current_user (as None) instead of being rejected
# by the scheme with an HTTP 403 "Not authenticated". This lets the API return
# the correct 401 + WWW-Authenticate for unauthenticated requests while
# keeping invalid-token → 401 and insufficient-permission → 403 semantics.
security = HTTPBearer(auto_error=False)

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
        # WS3 / API-0001 — missing credentials (HTTPBearer(auto_error=False)
        # yields None) must be reported as 401 Unauthorized with a standard
        # auth challenge, not 403 Forbidden.
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
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

# ==========================================
# ORGANISATION SCOPE ENFORCEMENT (F-05-R1)
# ==========================================
#
# F-05-R1 (release-blocking, CT-FINAL-01): the organisation guards below only
# proved that the caller was a member of *some* organisation, while the handler
# then used the service-role Supabase client scoped ONLY by the organisation id
# taken from the request path. Any authenticated organisation member could
# therefore read and write ANOTHER organisation's data by changing that path
# parameter. Reproduced on
# ``POST /api/organizations/{org_id}/exports/exports/emissions``.
#
# The remediation is central rather than per-route: before any guarded handler
# runs, every organisation named by the request PATH must be one the caller is
# actually authorised for. 102 path-scoped routes share these two guards.

#: Route path parameters that name the organisation a request operates on.
ORG_SCOPE_PATH_PARAMS: tuple = (
    "organization_id",
    "org_id",
    "organisation_id",
)


def get_request_org_scope(request: Optional[Request]) -> tuple:
    """Organisation ids declared in the request's PATH (F-05-R1).

    Returns ``()`` when the route declares no organisation path parameter, in
    which case the guards keep their historical membership-only behaviour.
    ``request`` is ``None`` only for direct (unit-test) invocations of a guard
    checker; FastAPI always injects the real ``Request`` for routed requests.
    """
    path_params = getattr(request, "path_params", None) or {}
    found: List[str] = []
    for name in ORG_SCOPE_PATH_PARAMS:
        value = path_params.get(name)
        if value in (None, ""):
            continue
        value = str(value)
        if value not in found:
            found.append(value)
    return tuple(found)


def get_active_org_role(user_id: str, organization_id: str) -> Optional[str]:
    """Authoritative role of an ACTIVE membership, or ``None`` (fail closed).

    ``None`` means "not authorised": an unusable membership store must never
    become an implicit allow, and it must never surface as HTTP 500 either
    (F-05-R3 — the previous ``maybe_single()`` lookup raised ``AttributeError``
    on ``None`` for a member of several organisations or for no row at all).
    """
    if not user_id or not organization_id:
        return None
    try:
        supabase = get_supabase_client()
        result = (
            supabase.from_('organization_members')
            .select('role, is_active')
            .eq('user_id', user_id)
            .eq('organization_id', organization_id)
            .eq('is_active', True)
            .limit(1)
            .execute()
        )
    except HTTPException:
        # Supabase not configured / unavailable → deny, never 500.
        return None
    except Exception as e:
        print(f"⚠️ Organisation membership lookup failed: {e}")
        return None

    rows = getattr(result, "data", None) or []
    if not rows:
        return None
    return rows[0].get('role')


def _org_admin_authority(current_user: AuthUser, org_id: str) -> bool:
    """True when ``current_user`` may administer ``org_id`` (owner/admin)."""
    if (
        current_user.organization_id
        and current_user.organization_id == org_id
        and (
            current_user.role in ('org_owner', 'org_admin')
            or current_user.role_name in ('owner', 'admin')
        )
    ):
        # Token-derived fast path — no database round trip for the common case.
        return True
    return get_active_org_role(current_user.user_id, org_id) in ('owner', 'admin')


async def enforce_org_path_scope(
    request: Optional[Request], current_user: AuthUser
) -> None:
    """Require exact-tenant authority for every organisation named by the path.

    * No organisation in the path → nothing to enforce (historical behaviour).
    * CarbonTally INTERNAL staff → unchanged operational cross-organisation
      access. They are not organisation members, so the guard's own membership
      test still decides; this branch only avoids *denying* an internal staff
      member that also holds an organisation membership.
    * Everyone else → the path organisation must be the caller's own
      organisation, or one where they hold an ACTIVE membership.
    """
    path_orgs = get_request_org_scope(request)
    if not path_orgs or not current_user:
        return
    if current_user.is_internal_staff:
        return

    for org_id in path_orgs:
        if current_user.organization_id and current_user.organization_id == org_id:
            continue
        if get_active_org_role(current_user.user_id, org_id) is not None:
            continue
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization",
        )


def enforce_org_body_scope(organization_id: Any, current_user: AuthUser) -> None:
    """POD-5 — authorise the organisation a request names in its **body**.

    ``enforce_org_path_scope`` reads organisations from the route *path*, so it
    is a deliberate no-op for the routes that take ``organization_id`` in the
    JSON body — and those routes go on to read with the service-role client,
    which bypasses RLS. Without this check any authenticated organisation member
    could ask for another organisation's report. (Verified on
    ``POST /api/reports/generate-enhanced-report``: with only
    ``require_org_member()`` attached, a member of org B received org A's
    generated PDF.)

    The rule applied is the ratified POD-5 one (``routes/legacy_reports``): the
    body organisation must be the caller's own. It is deliberately stricter than
    the path rule above, which also accepts an *active* membership — whether
    consultants or internal CarbonTally staff should generate a client's report
    through these body-organisation paths is a Product Owner decision, so the
    canonical route and its POD-5 compatibility alias keep identical behaviour
    until that decision is made.
    """
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    caller_org = getattr(current_user, "organization_id", None)
    if not caller_org:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No organisation context for this account.",
        )
    if str(organization_id) != str(caller_org):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this organization",
        )


def require_auth():
    """
    Dependency factory for authentication.
    Must be used as ``Depends(require_auth())``: the parenthesised form calls the
    factory so the returned checker runs. ``Depends(require_auth)`` (no
    parentheses) would hand FastAPI the factory itself, skip the check entirely
    and inject the checker *function* as the handler's user argument (verified
    against FastAPI 0.141.1 — HTTP 200 with no authentication).
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

#: Role names that carry CarbonTally-internal admin authority (ISC-10 /
#: PO Decision 2). The seeded ``system_admin`` role is a full
#: system-administration role and must pass the legacy ``/api/v2/admin/*``
#: authorizer that historically only recognised the literal role name ``admin``.
ADMIN_ROLE_NAMES: tuple[str, ...] = ("admin", "system_admin")


def require_admin():
    """
    Dependency factory for admin privileges.
    Must be used as ``Depends(require_admin())`` — see ``require_auth`` for why
    the no-parentheses form is a silent bypass.
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

        if (
            current_user.role not in ADMIN_ROLE_NAMES
            and current_user.role_name not in ADMIN_ROLE_NAMES
            and not current_user.permissions.get("is_superuser", False)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required",
            )
        
        return current_user
    
    return admin_checker

def require_staff():
    """
    Dependency factory for staff membership.
    Must be used as ``Depends(require_staff())`` — see ``require_auth`` for why
    the no-parentheses form is a silent bypass. (``api.operations_auth`` exposes
    an unrelated *dependency function* also named ``require_staff``; that one is
    used bare and is correct.)
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

    F-05-R1: when the route PATH names an organisation (``{organization_id}`` /
    ``{org_id}``), membership in *any* organisation is NOT sufficient — the
    caller must be authorised for the organisation the path names, because the
    handler goes on to use the service-role client scoped only by that path
    parameter. Internal CarbonTally staff keep their approved operational
    cross-organisation access; Processing Entity staff remain denied (D20
    scope-first).

    Must be used as ``Depends(require_org_member())`` — the parenthesised form.
    ``Depends(require_org_member)`` (no parentheses) would pass the factory
    itself as the dependency, never run the check, and inject the checker
    function into the handler (verified against FastAPI 0.141.1).
    """
    async def org_member_checker(
        current_user: AuthUser = Depends(get_current_user),
        request: Request = None,  # type: ignore[assignment]
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

        # F-05-R1 — exact-tenant enforcement (no-op without a path org).
        await enforce_org_path_scope(request, current_user)

        return current_user
    
    return org_member_checker

def require_org_admin():
    """
    Dependency factory for organization admin privileges.
    Must be used as ``Depends(require_org_admin())`` (see ``require_org_member``
    for the no-parentheses hazard).

    Organisation administrators are the roles the schema's RLS treats as
    administrators of their own organisation: ``owner`` and ``admin``
    (``organization_members.role`` CHECK constraint; the RLS admin policies
    ``om_insert_admin`` / ``om_update_admin`` / ``om_select_self_or_admin`` use
    ``role IN ('owner','admin')``). Global CarbonTally admins pass too.

    F-05-R1: when the path names an organisation, admin authority must hold for
    *that* organisation. F-05-R3: the authoritative lookup is a list query, so a
    member of several organisations (or a caller with no row) yields 403 rather
    than the previous ``maybe_single()`` ``AttributeError`` → 500.
    """
    async def org_admin_checker(
        current_user: AuthUser = Depends(get_current_user),
        request: Request = None,  # type: ignore[assignment]
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
        # never pass as a global admin. PO Decision 2: ``system_admin`` is a
        # full system-administration role and passes here too.
        if current_user.is_internal_staff and (
            current_user.role in ADMIN_ROLE_NAMES
            or current_user.role_name in ADMIN_ROLE_NAMES
            or current_user.permissions.get("is_superuser", False)
        ):
            return current_user

        if current_user.is_org_member and current_user.user_id:
            # The organisation(s) the caller must administer: the path
            # organisation when the route names one, otherwise the caller's own
            # organisation (historical behaviour).
            path_orgs = get_request_org_scope(request)
            target_orgs = path_orgs or (
                (current_user.organization_id,)
                if current_user.organization_id
                else ()
            )
            for org_id in target_orgs:
                if _org_admin_authority(current_user, org_id):
                    return current_user

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
    # PO Decision 2 — ``system_admin`` is a full system-administration role: it
    # satisfies every legacy gate that requires the ``admin`` role (superset
    # semantics) without granting the less-privileged role names.
    accepted = set(required_roles)
    if "admin" in accepted:
        accepted.update(ADMIN_ROLE_NAMES)

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

        if current_user.role not in accepted and current_user.role_name not in accepted:
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