# backend/tests/setup_test_data.py
"""
Complete test data setup for CarbonTally
Run: python backend/tests/setup_test_data.py
"""

import os
import sys
import asyncio
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database import get_supabase_client
from supabase import create_client, Client

load_dotenv()

# ==========================================
# TEST USER CONFIGURATION
# ==========================================

TEST_USERS = [
    {
        "email": "admin@carbontally.co.uk",
        "password": "AdminPass123!",
        "first_name": "Admin",
        "last_name": "User",
        "role": "admin",
        "staff_role": "admin",
        "org_role": "admin",
        "is_staff": True
    },
    {
        "email": "staff@carbontally.co.uk",
        "password": "StaffPass123!",
        "first_name": "Staff",
        "last_name": "User",
        "role": "staff",
        "staff_role": "data_extractor",
        "org_role": None,
        "is_staff": True
    },
    {
        "email": "orgadmin@test.com",
        "password": "OrgAdminPass123!",
        "first_name": "Org",
        "last_name": "Admin",
        "role": "org_admin",
        "staff_role": None,
        "org_role": "admin",
        "is_staff": False
    },
    {
        "email": "orgeditor@test.com",
        "password": "OrgEditorPass123!",
        "first_name": "Org",
        "last_name": "Editor",
        "role": "org_editor",
        "staff_role": None,
        "org_role": "editor",
        "is_staff": False
    },
    {
        "email": "orgviewer@test.com",
        "password": "OrgViewerPass123!",
        "first_name": "Org",
        "last_name": "Viewer",
        "role": "org_viewer",
        "staff_role": None,
        "org_role": "viewer",
        "is_staff": False
    },
    {
        "email": "testuser@example.com",
        "password": "UserPass123!",
        "first_name": "Test",
        "last_name": "User",
        "role": "user",
        "staff_role": None,
        "org_role": None,
        "is_staff": False
    }
]

# ==========================================
# HELPER FUNCTIONS
# ==========================================

def get_supabase_admin() -> Client:
    """Get Supabase admin client with service role"""
    url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not url or not service_key:
        print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in .env")
        return None
    
    try:
        client = create_client(url, service_key)
        print("✅ Supabase admin client initialized")
        return client
    except Exception as e:
        print(f"❌ Failed to create Supabase admin client: {e}")
        return None

def safe_execute(result):
    """Safely extract data from Supabase response"""
    if result is None:
        return None
    
    # Check if result has data attribute
    if hasattr(result, 'data'):
        return result.data
    
    # Check if result is a dict with data key
    if isinstance(result, dict) and 'data' in result:
        return result['data']
    
    # Check if result is a list (some methods return list directly)
    if isinstance(result, list):
        return result
    
    return None

async def create_auth_user(supabase_admin: Client, email: str, password: str, user_metadata: dict):
    """Create user in Supabase Auth using admin API"""
    try:
        # Check if user exists
        try:
            # Try to list users
            response = supabase_admin.auth.admin.list_users()
            
            if hasattr(response, 'users'):
                users = response.users
            elif isinstance(response, dict) and 'users' in response:
                users = response['users']
            elif isinstance(response, list):
                users = response
            else:
                users = []
            
            for user in users:
                user_email = user.email if hasattr(user, 'email') else user.get('email') if isinstance(user, dict) else None
                user_id = user.id if hasattr(user, 'id') else user.get('id') if isinstance(user, dict) else None
                
                if user_email == email:
                    print(f"⚠️  User {email} already exists (ID: {user_id})")
                    return user_id
        except Exception as e:
            print(f"⚠️  Could not check existing users: {e}")
        
        # Create user
        try:
            response = supabase_admin.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": user_metadata
            })
            
            if response:
                if hasattr(response, 'user'):
                    user = response.user
                    user_id = user.id if hasattr(user, 'id') else user.get('id')
                    print(f"✅ Created Auth user: {email} (ID: {user_id})")
                    return user_id
                elif isinstance(response, dict) and response.get('user'):
                    user_id = response['user'].get('id')
                    print(f"✅ Created Auth user: {email} (ID: {user_id})")
                    return user_id
                elif isinstance(response, dict) and response.get('id'):
                    print(f"✅ Created Auth user: {email} (ID: {response['id']})")
                    return response['id']
        except Exception as e2:
            print(f"⚠️  Could not create user via admin API: {e2}")
            
            # Try alternative method
            try:
                # Sometimes the admin API expects different format
                response = supabase_admin.auth.admin.create_user({
                    "email": email,
                    "password": password,
                    "user_metadata": user_metadata,
                    "email_confirm": True
                })
                
                if response:
                    if hasattr(response, 'user'):
                        return response.user.id
                    elif isinstance(response, dict) and response.get('user'):
                        return response['user'].get('id')
            except Exception as e3:
                print(f"❌ Both methods failed for {email}: {e3}")
                return None
        
        print(f"❌ Failed to create user: {email}")
        return None
        
    except Exception as e:
        print(f"❌ Error creating user {email}: {e}")
        return None

async def create_staff_profile(supabase: Client, user_id: str, email: str, first_name: str, last_name: str, role: str):
    """Create staff profile"""
    try:
        # Check if staff profile exists
        response = supabase.from_('staff_profiles') \
            .select('id') \
            .eq('user_id', user_id) \
            .maybe_single() \
            .execute()
        
        data = safe_execute(response)
        
        if data:
            print(f"⚠️  Staff profile already exists for {email}")
            return
        
        # Create staff profile
        data = {
            'id': user_id,  # Same as auth.users id
            'user_id': user_id,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'role': role,
            'is_active': True,
            'extraction_count': 0,
            'accuracy_rate': 100.00,
            'created_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.from_('staff_profiles') \
            .insert(data) \
            .execute()
        
        result = safe_execute(response)
        
        if result:
            print(f"✅ Created staff profile: {email} (Role: {role})")
        else:
            print(f"❌ Failed to create staff profile for {email}")
            print(f"   Response: {response}")
            
    except Exception as e:
        print(f"❌ Error creating staff profile for {email}: {e}")

async def create_organization(supabase: Client, name: str = "Test Organization"):
    """Create test organization"""
    try:
        # Check if organization exists
        response = supabase.from_('organizations') \
            .select('id, name') \
            .eq('name', name) \
            .maybe_single() \
            .execute()
        
        data = safe_execute(response)
        
        if data:
            org_id = data.get('id') if isinstance(data, dict) else data[0].get('id') if isinstance(data, list) else None
            print(f"⚠️  Organization already exists: {org_id}")
            return org_id
        
        # Create organization
        data = {
            'name': name,
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
        
        response = supabase.from_('organizations') \
            .insert(data) \
            .execute()
        
        result = safe_execute(response)
        
        if result:
            org_id = result[0]['id'] if isinstance(result, list) else result.get('id')
            print(f"✅ Created organization: {name} (ID: {org_id})")
            return org_id
        
        print(f"❌ Failed to create organization: {name}")
        print(f"   Response: {response}")
        return None
        
    except Exception as e:
        print(f"❌ Error creating organization: {e}")
        return None

async def add_org_member(supabase: Client, org_id: str, user_id: str, role: str, email: str):
    """Add user as organization member"""
    try:
        # Check if member already exists
        response = supabase.from_('organization_members') \
            .select('id, role') \
            .eq('organization_id', org_id) \
            .eq('user_id', user_id) \
            .maybe_single() \
            .execute()
        
        data = safe_execute(response)
        
        if data:
            print(f"⚠️  {email} is already a member of organization")
            
            # Update role if different
            if isinstance(data, dict) and data.get('role') != role:
                response = supabase.from_('organization_members') \
                    .update({'role': role}) \
                    .eq('id', data['id']) \
                    .execute()
                print(f"✅ Updated {email}'s role to {role}")
            return
        
        # Add member
        data = {
            'organization_id': org_id,
            'user_id': user_id,
            'role': role,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.from_('organization_members') \
            .insert(data) \
            .execute()
        
        result = safe_execute(response)
        
        if result:
            print(f"✅ Added {email} as {role} to organization")
        else:
            print(f"❌ Failed to add {email} as member")
            print(f"   Response: {response}")
            
    except Exception as e:
        print(f"❌ Error adding member {email}: {e}")

async def create_beta_code(supabase: Client, email: str):
    """Create a beta code for testing"""
    try:
        import secrets
        import string
        
        code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
        
        # Check if code exists
        response = supabase.from_('beta_access_codes') \
            .select('id') \
            .eq('code', code) \
            .maybe_single() \
            .execute()
        
        if safe_execute(response):
            return await create_beta_code(supabase, email)
        
        data = {
            'code': code,
            'email': email,
            'status': 'active',
            'expires_at': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'created_at': datetime.utcnow().isoformat()
        }
        
        response = supabase.from_('beta_access_codes') \
            .insert(data) \
            .execute()
        
        result = safe_execute(response)
        
        if result:
            print(f"✅ Created beta code {code} for {email}")
            return code
        
        return None
        
    except Exception as e:
        print(f"❌ Error creating beta code: {e}")
        return None

# ==========================================
# MAIN SETUP FUNCTION
# ==========================================

async def setup_test_data():
    """Complete test data setup"""
    print("="*70)
    print("🚀 CARBONTALLY TEST DATA SETUP")
    print("="*70 + "\n")
    
    # Get Supabase clients
    supabase = get_supabase_client()
    
    if not supabase:
        print("❌ Failed to initialize Supabase client")
        return False
    
    supabase_admin = get_supabase_admin()
    
    if not supabase_admin:
        print("❌ Failed to initialize Supabase admin client")
        print("   Make sure SUPABASE_SERVICE_KEY is set in .env")
        return False
    
    # ==========================================
    # 1. Create Auth Users
    # ==========================================
    print("\n📌 CREATING AUTH USERS")
    print("-" * 40)
    print("⚠️  Note: If users already exist in auth.users, they will be skipped.")
    print("-" * 40)
    
    user_ids = {}
    for user in TEST_USERS:
        print(f"\nCreating: {user['email']}")
        
        user_id = await create_auth_user(
            supabase_admin,
            user['email'],
            user['password'],
            {
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'role': user['role']
            }
        )
        
        if user_id:
            user_ids[user['email']] = user_id
            user['user_id'] = user_id
        else:
            print(f"⚠️  Could not create {user['email']} automatically")
            print(f"   Please create manually in Supabase Dashboard:")
            print(f"   Email: {user['email']}")
            print(f"   Password: {user['password']}")
    
    # ==========================================
    # 2. Create Staff Profiles
    # ==========================================
    print("\n📌 CREATING STAFF PROFILES")
    print("-" * 40)
    
    staff_users = [u for u in TEST_USERS if u.get('is_staff') and u.get('user_id')]
    
    for user in staff_users:
        await create_staff_profile(
            supabase,
            user['user_id'],
            user['email'],
            user['first_name'],
            user['last_name'],
            user['staff_role']
        )
    
    # ==========================================
    # 3. Create Organization
    # ==========================================
    print("\n📌 CREATING ORGANIZATION")
    print("-" * 40)
    
    org_name = "Test Organization"
    org_id = await create_organization(supabase, org_name)
    
    if not org_id:
        print("❌ Failed to create organization.")
        print("   Please create manually in Supabase Dashboard or check permissions.")
        return False
    
    # ==========================================
    # 4. Add Organization Members
    # ==========================================
    print("\n📌 ADDING ORGANIZATION MEMBERS")
    print("-" * 40)
    
    org_users = [u for u in TEST_USERS if u.get('org_role') and u.get('user_id')]
    
    for user in org_users:
        await add_org_member(
            supabase,
            org_id,
            user['user_id'],
            user['org_role'],
            user['email']
        )
    
    # ==========================================
    # 5. Create Beta Codes
    # ==========================================
    print("\n📌 CREATING BETA CODES")
    print("-" * 40)
    
    beta_users = ['testuser@example.com', 'orgadmin@test.com']
    beta_codes = {}
    
    for email in beta_users:
        code = await create_beta_code(supabase, email)
        if code:
            beta_codes[email] = code
    
    # ==========================================
    # 6. Create .env.test File
    # ==========================================
    print("\n📌 CREATING .env.test FILE")
    print("-" * 40)
    
    admin_user = next((u for u in TEST_USERS if u['role'] == 'admin'), None)
    test_user = next((u for u in TEST_USERS if u['role'] == 'user'), None)
    org_admin = next((u for u in TEST_USERS if u['role'] == 'org_admin'), None)
    
    with open('.env.test', 'w') as f:
        f.write(f"""# ==========================================
# CarbonTally Test Environment Configuration
# Generated: {datetime.utcnow().isoformat()}
# ==========================================

# API Configuration
TEST_API_URL=http://localhost:8000

# Test Users
TEST_ADMIN_EMAIL={admin_user['email'] if admin_user else 'admin@carbontally.co.uk'}
TEST_ADMIN_PASSWORD={admin_user['password'] if admin_user else 'AdminPass123!'}
TEST_USER_EMAIL={test_user['email'] if test_user else 'testuser@example.com'}
TEST_USER_PASSWORD={test_user['password'] if test_user else 'UserPass123!'}
TEST_ORG_ADMIN_EMAIL={org_admin['email'] if org_admin else 'orgadmin@test.com'}
TEST_ORG_ADMIN_PASSWORD={org_admin['password'] if org_admin else 'OrgAdminPass123!'}

# Test Organization
TEST_ORG_ID={org_id}
TEST_ORG_NAME={org_name}

# Beta Codes
""")
        for email, code in beta_codes.items():
            f.write(f"BETA_CODE_{email.split('@')[0].upper()}={code}\n")
        
        f.write(f"""
# Supabase Configuration
SUPABASE_URL={os.getenv('SUPABASE_URL')}
SUPABASE_ANON_KEY={os.getenv('SUPABASE_ANON_KEY')}
SUPABASE_SERVICE_KEY={os.getenv('SUPABASE_SERVICE_KEY')}
""")
    
    print("✅ .env.test file created!")
    
    # ==========================================
    # 7. Print Summary
    # ==========================================
    print("\n" + "="*70)
    print("✅ TEST DATA SETUP COMPLETE!")
    print("="*70)
    
    print("\n📋 Test Users:")
    for user in TEST_USERS:
        has_user_id = '✅' if user.get('user_id') else '⚠️'
        print(f"  {has_user_id} {user['email']} / {user['password']}")
        print(f"    - Role: {user['role']}")
        if user.get('staff_role'):
            print(f"    - Staff Role: {user['staff_role']}")
        if user.get('org_role'):
            print(f"    - Org Role: {user['org_role']}")
        print()
    
    print(f"\n🏢 Test Organization:")
    print(f"  • ID: {org_id}")
    print(f"  • Name: {org_name}")
    
    if beta_codes:
        print("\n🔑 Beta Codes:")
        for email, code in beta_codes.items():
            print(f"  • {email}: {code}")
    
    print("\n🚀 Ready to run tests:")
    print("  python backend/tests/test_api.py")
    print("\n🔧 If staff profiles weren't created, check:")
    print("  1. Supabase RLS policies for staff_profiles table")
    print("  2. Supabase permissions for the service role key")
    
    return True

# ==========================================
# RUN SETUP
# ==========================================

if __name__ == "__main__":
    asyncio.run(setup_test_data())