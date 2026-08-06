Assets and Facilities - Organization Access Control
The assets and facilities endpoints already have proper organization access control. Let me verify:

python
# backend/routes/organizations/assets.py

# ✅ GET facilities - Organization members only
@router.get("/{org_id}/facilities")
async def get_facilities(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())  # ✅ Organization member
):
    # Check organization access
    if not current_user.is_admin:
        member = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', current_user.user_id) \
            .maybe_single() \
            .execute()
        
        if not member.data:
            raise HTTPException(403, "Not authorized")
    # ... rest of code

# ✅ POST facilities - Organization admin only
@router.post("/{org_id}/facilities")
async def create_facility(
    org_id: str,
    facility_data: FacilityCreate,
    current_user: AuthUser = Depends(require_org_admin())  # ✅ Organization admin
):
    # ... rest of code

# ✅ GET assets - Organization members only
@router.get("/{org_id}/assets")
async def get_assets(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())  # ✅ Organization member
):
    # ... rest of code

# ✅ POST assets - Organization admin only
@router.post("/{org_id}/assets")
async def create_asset(
    org_id: str,
    asset_data: AssetCreate,
    current_user: AuthUser = Depends(require_org_admin())  # ✅ Organization admin
):
    # ... rest of code
Access Control Summary
Role	Reference Data	Org Assets/Facilities
Public	❌	❌
Authenticated User	✅ (all)	❌ (no org)
Org Member	✅ (all)	✅ (own org)
Org Admin	✅ (all)	✅ (own org, edit)
Staff	✅ (all)	✅ (all orgs)
Admin	✅ (all)	✅ (all orgs, edit)