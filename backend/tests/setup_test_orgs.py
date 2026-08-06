# backend/tests/setup_test_orgs.py
"""
Setup test organizations and users for testing
Run: python backend/tests/setup_test_orgs.py
"""

import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime
import random
import string

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from database import get_supabase_client
from supabase import create_client

# Test users configuration
TEST_USERS = {
    "admin": {
        "email": "admin@carbontally.co.uk",
        "password": "AdminPass123!",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
        "is_staff": True,
        "staff_role": "admin"
    },
    "staff": {
        "email": "staff@carbontally.co.uk",
        "password": "StaffPass123!",
        "first_name": "Staff",
        "last_name": "User",
        "role": "staff",
        "is_staff": True,
        "staff_role": "data_extractor"
    },
    "org_admin": {
        "email": "orgadmin@test.com",
        "password": "OrgAdminPass123!",
        "first_name": "Org",
        "last_name": "Admin",
        "role": "org_admin",
        "is_staff": False,
        "org_role": "admin",
        "org_name": "Test Organization"
    },
    "org_editor": {
        "email": "orgeditor@test.com",
        "password": "OrgEditorPass123!",
        "first_name": "Org",
        "last_name": "Editor",
        "role": "org_editor",
        "is_staff": False,
        "org_role": "editor",
        "org_name": "Test Organization"
    },
    "org_viewer": {
        "email": "orgviewer@test.com",
        "password": "OrgViewerPass123!",
        "first_name": "Org",
        "last_name": "Viewer",
        "role": "org_viewer",
        "is_staff": False,
        "org_role": "viewer",
        "org_name": "Test Organization"
    },
    "user": {
        "email": "testuser@example.com",
        "password": "UserPass123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
        "is_staff": False,
        "org_name": None,  # Will be created from email
        "auto_create_org": True
    }
}

async def create_auth_user(supabase_admin, email: str, password: str, user_data: dict):
    """Create user in Supabase Auth"""
    try:
        # Check if user exists
        users = supabase_admin.auth.admin.list_users()
        for user in users.users:
            if user.email == email:
                print(f"⚠️  User {email} already exists in Auth")
                return user.id
        
        # Create user
        response = supabase_admin.auth.admin.create_user({
            "email": email,
            "password": password,
            "email_confirm": True,
            "user_metadata": {
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
                "role": user_data.get("role", "user")
            }
        })
        
        if response and response.user:
            print(f"✅ Created Auth user: {email}")
            return response.user.id
        
        print(f"❌ Failed to create Auth user: {email}")
        return None
        
    except Exception as e:
        print(f"❌ Error creating Auth user {email}: {e}")
        return None

async def create_staff_profile(supabase, user_id: str, email: str, user_data: dict):
    """Create staff profile for staff users"""
    if not user_data.get("is_staff"):
        return
    
    try:
        # Check if staff profile exists
        existing = supabase.from_('staff_profiles') \
            .select('id') \
            .eq('user_id', user_id) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            print(f"⚠️  Staff profile already exists for {email}")
            return
        
        # Create staff profile
        data = {
            'id': user_id,
            'user_id': user_id,
            'email': email,
            'first_name': user_data.get("first_name", ""),
            'last_name': user_data.get("last_name", ""),
            'role': user_data.get("staff_role", "data_extractor"),
            'is_active': True,
            'extraction_count': 0,
            'accuracy_rate': 100.00,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('staff_profiles') \
            .insert(data) \
            .execute()
        
        if result.data:
            print(f"✅ Created staff profile: {email}")
        else:
            print(f"❌ Failed to create staff profile for {email}")
            
    except Exception as e:
        print(f"❌ Error creating staff profile for {email}: {e}")

async def create_organization(supabase, org_name: str, user_id: str, user_email: str) -> str:
    """Create or get organization"""
    try:
        # Clean org name
        if not org_name:
            # Generate from email
            org_name = user_email.split('@')[0].replace('.', ' ').title()
            if len(org_name) < 2:
                org_name = f"User {user_id[:8]}"
        
        # Check if organization exists
        existing = supabase.from_('organizations') \
            .select('id') \
            .eq('name', org_name) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            print(f"⚠️  Organization '{org_name}' already exists")
            return existing.data['id']
        
        # Create organization
        data = {
            'name': org_name,
            'industry': 'Technology',
            'sector': 'Software',
            'country': 'United Kingdom',
            'timezone': 'Europe/London',
            'currency': 'GBP',
            'reporting_standard': 'SECR',
            'subscription_status': 'trial',
            'subscription_tier': 'starter',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('organizations') \
            .insert(data) \
            .execute()
        
        if result.data:
            org_id = result.data[0]['id']
            print(f"✅ Created organization '{org_name}' (ID: {org_id})")
            return org_id
        
        print(f"❌ Failed to create organization '{org_name}'")
        return None
        
    except Exception as e:
        print(f"❌ Error creating organization: {e}")
        return None

async def add_org_member(supabase, org_id: str, user_id: str, role: str, email: str):
    """Add user as organization member"""
    try:
        # Check if member exists
        existing = supabase.from_('organization_members') \
            .select('id') \
            .eq('organization_id', org_id) \
            .eq('user_id', user_id) \
            .maybe_single() \
            .execute()
        
        if existing.data:
            print(f"⚠️  {email} is already a member of organization")
            return
        
        # Add member
        data = {
            'organization_id': org_id,
            'user_id': user_id,
            'role': role,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        result = supabase.from_('organization_members') \
            .insert(data) \
            .execute()
        
        if result.data:
            print(f"✅ Added {email} as {role} to organization")
        else:
            print(f"❌ Failed to add {email} as member")
            
    except Exception as e:
        print(f"❌ Error adding member {email}: {e}")

async def setup_test_data():
    """Complete test data setup"""
    print("="*70)
    print("🚀 SETTING UP TEST DATA")
    print("="*70)
    
    supabase = get_supabase_client()
    
    # Get admin client for auth
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_service_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY")
        return
    
    supabase_admin = create_client(supabase_url, supabase_service_key)
    
    # Store created user IDs
    user_ids = {}
    org_id = None
    
    # First pass: Create auth users
    print("\n📌 CREATING AUTH USERS")
    print("-" * 50)
    
    for user_type, user_data in TEST_USERS.items():
        user_id = await create_auth_user(
            supabase_admin,
            user_data["email"],
            user_data["password"],
            user_data
        )
        if user_id:
            user_ids[user_data["email"]] = user_id
            user_data["user_id"] = user_id
    
    # Second pass: Create organizations
    print("\n📌 CREATING ORGANIZATIONS")
    print("-" * 50)
    
    for user_type, user_data in TEST_USERS.items():
        if user_data.get("is_staff"):
            continue  # Staff don't need organizations
        
        user_id = user_data.get("user_id")
        if not user_id:
            continue
        
        # Determine organization name
        if user_data.get("org_name"):
            org_name = user_data["org_name"]
        elif user_data.get("auto_create_org"):
            # Create from email
            org_name = user_data["email"].split('@')[0].replace('.', ' ').title()
            if len(org_name) < 2:
                org_name = f"User {user_id[:8]}"
        else:
            continue
        
        # Get or create organization
        current_org_id = await create_organization(supabase, org_name, user_id, user_data["email"])
        
        if current_org_id:
            # Store first org_id as the main test org
            if not org_id:
                org_id = current_org_id
            
            # Add user as member
            if user_data.get("org_role"):
                await add_org_member(
                    supabase,
                    current_org_id,
                    user_id,
                    user_data["org_role"],
                    user_data["email"]
                )
    
    # Third pass: Create staff profiles
    print("\n📌 CREATING STAFF PROFILES")
    print("-" * 50)
    
    for user_type, user_data in TEST_USERS.items():
        if user_data.get("is_staff") and user_data.get("user_id"):
            await create_staff_profile(
                supabase,
                user_data["user_id"],
                user_data["email"],
                user_data
            )
    
    # Create .env.test file
    print("\n📌 CREATING .env.test FILE")
    print("-" * 50)
    
    admin_user = TEST_USERS.get("admin")
    user_user = TEST_USERS.get("user")
    org_admin = TEST_USERS.get("org_admin")
    
    with open('.env.test', 'w') as f:
        f.write(f"""# ==========================================
# CarbonTally Test Environment
# Generated: {datetime.utcnow().isoformat()}
# ==========================================

# API Configuration
TEST_API_URL=http://localhost:8000

# Test Users
TEST_ADMIN_EMAIL={admin_user['email'] if admin_user else 'admin@carbontally.co.uk'}
TEST_ADMIN_PASSWORD={admin_user['password'] if admin_user else 'AdminPass123!'}
TEST_USER_EMAIL={user_user['email'] if user_user else 'testuser@example.com'}
TEST_USER_PASSWORD={user_user['password'] if user_user else 'UserPass123!'}
TEST_ORG_ADMIN_EMAIL={org_admin['email'] if org_admin else 'orgadmin@test.com'}
TEST_ORG_ADMIN_PASSWORD={org_admin['password'] if org_admin else 'OrgAdminPass123!'}

# Test Organization
TEST_ORG_ID={org_id or 'test-org-id'}
""")
    
    print("✅ .env.test file created!")
    
    # Final summary
    print("\n" + "="*70)
    print("✅ TEST DATA SETUP COMPLETE!")
    print("="*70)
    
    print("\n📋 Test Users:")
    for user_type, user_data in TEST_USERS.items():
        has_id = "✅" if user_data.get("user_id") else "❌"
        print(f"  {has_id} {user_type}: {user_data['email']} / {user_data['password']}")
        if user_data.get("is_staff"):
            print(f"     - Staff Role: {user_data.get('staff_role', 'staff')}")
        if user_data.get("org_role"):
            print(f"     - Org Role: {user_data.get('org_role')}")
        if user_data.get("user_id"):
            print(f"     - User ID: {user_data['user_id']}")
    
    if org_id:
        print(f"\n🏢 Test Organization ID: {org_id}")
    
    print("\n🚀 Ready to run tests:")
    print("  python backend/tests/test_all_endpoints.py")

if __name__ == "__main__":
    asyncio.run(setup_test_data())