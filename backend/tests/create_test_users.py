# backend/tests/create_test_users.py
"""
Create test users in Supabase Auth and database
Run: python backend/tests/create_test_users.py
"""

import os
import sys
from pathlib import Path
import asyncio
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from database import get_supabase_client
from auth import hash_password

load_dotenv()

# Test user credentials
TEST_USERS = [
    {
        "email": "admin@carbontally.co.uk",
        "password": "AdminPass123!",
        "role": "admin",
        "first_name": "Admin",
        "last_name": "User",
        "is_admin": True
    },
    {
        "email": "testuser@example.com",
        "password": "UserPass123!",
        "role": "user",
        "first_name": "Test",
        "last_name": "User",
        "is_admin": False
    },
    {
        "email": "orgadmin@test.com",
        "password": "OrgAdminPass123!",
        "role": "org_admin",
        "first_name": "Org",
        "last_name": "Admin",
        "is_admin": False
    }
]

async def create_test_users():
    """Create test users in Supabase"""
    try:
        supabase = get_supabase_client()
        
        for user_data in TEST_USERS:
            print(f"\n📝 Creating user: {user_data['email']}")
            
            # Check if user already exists
            existing = supabase.from_('auth.users') \
                .select('id') \
                .eq('email', user_data['email']) \
                .maybe_single() \
                .execute()
            
            if existing.data:
                print(f"⚠️  User {user_data['email']} already exists, skipping...")
                continue
            
            # Create user in Supabase Auth
            # Note: This uses the Supabase Admin API
            # You'll need to use the service role key
            
            # Create user
            user_result = supabase.auth.admin.create_user({
                'email': user_data['email'],
                'password': user_data['password'],
                'email_confirm': True,
                'user_metadata': {
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'role': user_data['role']
                }
            })
            
            if user_result.user:
                user_id = user_result.user.id
                print(f"✅ Created user: {user_data['email']} (ID: {user_id})")
                
                # Add user to staff_profiles if admin
                if user_data['is_admin'] or user_data['role'] == 'admin':
                    staff_result = supabase.from_('staff_profiles') \
                        .insert({
                            'user_id': user_id,
                            'email': user_data['email'],
                            'first_name': user_data['first_name'],
                            'last_name': user_data['last_name'],
                            'role': 'admin',
                            'is_active': True,
                            'created_at': 'now()'
                        }) \
                        .execute()
                    
                    if staff_result.data:
                        print(f"✅ Added to staff_profiles: {user_data['email']}")
                
            else:
                print(f"❌ Failed to create user: {user_data['email']}")
                print(f"Error: {user_result}")
        
        print("\n✅ Test users created successfully!")
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        import traceback
        traceback.print_exc()

async def create_test_organization():
    """Create a test organization"""
    try:
        supabase = get_supabase_client()
        
        # Check if test org exists
        existing = supabase.from_('organizations') \
            .select('id') \
            .eq('name', 'Test Organization') \
            .maybe_single() \
            .execute()
        
        if existing.data:
            print(f"⚠️  Test Organization already exists: {existing.data['id']}")
            return existing.data['id']
        
        # Create organization
        org_result = supabase.from_('organizations') \
            .insert({
                'name': 'Test Organization',
                'industry': 'Technology',
                'sector': 'Software',
                'country': 'United Kingdom',
                'created_at': 'now()'
            }) \
            .execute()
        
        if org_result.data:
            org_id = org_result.data[0]['id']
            print(f"✅ Created test organization: {org_id}")
            
            # Add org admin as member
            admin_user = supabase.from_('auth.users') \
                .select('id') \
                .eq('email', 'orgadmin@test.com') \
                .maybe_single() \
                .execute()
            
            if admin_user.data:
                member_result = supabase.from_('organization_members') \
                    .insert({
                        'organization_id': org_id,
                        'user_id': admin_user.data['id'],
                        'role': 'admin',
                        'is_active': True,
                        'created_at': 'now()'
                    }) \
                    .execute()
                
                if member_result.data:
                    print(f"✅ Added org_admin as member of test organization")
            
            return org_id
        
    except Exception as e:
        print(f"❌ Error creating test organization: {e}")
        return None

async def main():
    """Main function"""
    print("="*60)
    print("🔄 CREATING TEST USERS AND ORGANIZATION")
    print("="*60)
    
    # Create test users
    await create_test_users()
    
    # Create test organization
    org_id = await create_test_organization()
    
    if org_id:
        print(f"\n✅ Test setup complete!")
        print(f"📝 Test Organization ID: {org_id}")
        print("\n📋 Test Credentials:")
        print("  Admin:      admin@carbontally.co.uk / AdminPass123!")
        print("  User:       testuser@example.com / UserPass123!")
        print("  Org Admin:  orgadmin@test.com / OrgAdminPass123!")
        print("\n🔧 Add to your .env.test file:")
        print(f"TEST_ORG_ID={org_id}")

if __name__ == "__main__":
    asyncio.run(main())