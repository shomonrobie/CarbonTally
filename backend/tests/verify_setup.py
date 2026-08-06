# backend/tests/verify_setup.py
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

import asyncio
from database import get_supabase_client

async def verify():
    supabase = get_supabase_client()
    
    print("\n" + "="*60)
    print("📊 VERIFYING TEST SETUP")
    print("="*60)
    
    # Check users in auth (via staff profiles and org members)
    print("\n👤 Test Users:")
    print("  • admin@carbontally.co.uk - Admin")
    print("  • staff@carbontally.co.uk - Staff")
    print("  • orgadmin@test.com - Org Admin")
    print("  • orgeditor@test.com - Org Editor")
    print("  • orgviewer@test.com - Org Viewer")
    print("  • testuser@example.com - Test User")
    
    # Check staff profiles
    try:
        staff = supabase.from_('staff_profiles').select('*').execute()
        print(f"\n👤 Staff Profiles ({len(staff.data) if staff.data else 0}):")
        if staff.data:
            for s in staff.data:
                print(f"  • {s.get('email')} - {s.get('role')} - {'Active' if s.get('is_active') else 'Inactive'}")
        else:
            print("  ⚠️  No staff profiles found!")
    except Exception as e:
        print(f"  ❌ Error fetching staff profiles: {e}")
    
    # Check organizations
    try:
        orgs = supabase.from_('organizations').select('*').execute()
        print(f"\n🏢 Organizations ({len(orgs.data) if orgs.data else 0}):")
        if orgs.data:
            for o in orgs.data:
                print(f"  • {o.get('name')} ({o.get('id')})")
        else:
            print("  ⚠️  No organizations found!")
    except Exception as e:
        print(f"  ❌ Error fetching organizations: {e}")
    
    # Check organization members (without join)
    try:
        members = supabase.from_('organization_members').select('*').execute()
        print(f"\n👥 Organization Members ({len(members.data) if members.data else 0}):")
        if members.data:
            # Get user emails from auth.users manually
            user_ids = [m.get('user_id') for m in members.data if m.get('user_id')]
            user_emails = {}
            
            if user_ids:
                # Fetch users from auth.users (if you have a function for this)
                # For now, just show the user_ids
                for m in members.data:
                    print(f"  • User: {m.get('user_id')} - {m.get('role')} in org {m.get('organization_id')}")
        else:
            print("  ⚠️  No organization members found!")
    except Exception as e:
        print(f"  ❌ Error fetching organization members: {e}")
    
    # Check beta codes
    try:
        codes = supabase.from_('beta_access_codes').select('*').execute()
        print(f"\n🔑 Beta Codes ({len(codes.data) if codes.data else 0}):")
        if codes.data:
            for c in codes.data:
                print(f"  • {c.get('code')} - {c.get('email')} - {c.get('status')}")
        else:
            print("  ⚠️  No beta codes found!")
    except Exception as e:
        print(f"  ❌ Error fetching beta codes: {e}")
    
    print("\n" + "="*60)
    print("📋 Test Credentials:")
    print("="*60)
    print("  Admin:      admin@carbontally.co.uk / AdminPass123!")
    print("  Staff:      staff@carbontally.co.uk / StaffPass123!")
    print("  Org Admin:  orgadmin@test.com / OrgAdminPass123!")
    print("  Org Editor: orgeditor@test.com / OrgEditorPass123!")
    print("  Org Viewer: orgviewer@test.com / OrgViewerPass123!")
    print("  User:       testuser@example.com / UserPass123!")
    print("="*60)
    
    # Get Test Organization ID
    try:
        org = supabase.from_('organizations') \
            .select('id') \
            .eq('name', 'Test Organization') \
            .maybe_single() \
            .execute()
        
        if org.data:
            print(f"\n🏢 Test Organization ID: {org.data['id']}")
            print("  Add this to your .env.test file:")
            print(f"  TEST_ORG_ID={org.data['id']}")
    except Exception as e:
        print(f"  ❌ Error getting organization ID: {e}")
    
    print("\n✅ Test data verification complete!")

if __name__ == "__main__":
    asyncio.run(verify())