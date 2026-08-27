# backend/tests/test_api_simple.py
"""
Simple API test script for CarbonTally
Uses Supabase Auth directly (same as frontend)
Run: python backend/tests/test_api_simple.py
"""

import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

import asyncio
import httpx
import json
from typing import Dict, Any, Optional
import random
from supabase import create_client, Client

# Load environment
from dotenv import load_dotenv
load_dotenv()

# Test configuration
BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Test users - make sure these match your database
TEST_USERS = {
    "admin": {
        "email": "admin@carbontally.co.uk",
        "password": "AdminPass123!",
        "role": "admin"
    },
    "staff": {
        "email": "staff@carbontally.co.uk",
        "password": "StaffPass123!",
        "role": "staff"
    },
    "org_admin": {
        "email": "orgadmin@test.com",
        "password": "OrgAdminPass123!",
        "role": "org_admin"
    },
    "org_editor": {
        "email": "orgeditor@test.com",
        "password": "OrgEditorPass123!",
        "role": "org_editor"
    },
    "org_viewer": {
        "email": "orgviewer@test.com",
        "password": "OrgViewerPass123!",
        "role": "org_viewer"
    },
    "user": {
        "email": "testuser@example.com",
        "password": "UserPass123!",
        "role": "user"
    }
}

class APITester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.tokens = {}
        self.results = {"passed": 0, "failed": 0, "total": 0, "details": []}
        self.test_data = {}
        self.supabase_client = None
    
    def get_supabase_client(self) -> Client:
        """Get Supabase client"""
        if not SUPABASE_URL or not SUPABASE_ANON_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set in .env")
        
        if not self.supabase_client:
            self.supabase_client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        
        return self.supabase_client
    
    async def login(self, email: str, password: str) -> Optional[str]:
        """Login using Supabase Auth (same as frontend)"""
        try:
            supabase = self.get_supabase_client()
            
            # Sign in with password
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Check if we got a session
            if response and response.session:
                access_token = response.session.access_token
                print(f"  ✅ Login successful: {email}")
                return access_token
            else:
                print(f"  ❌ Login failed: {email} - No session returned")
                return None
                
        except Exception as e:
            error_msg = str(e)
            if "Invalid login credentials" in error_msg:
                print(f"  ❌ Login failed: {email} - Invalid credentials")
            elif "Email not confirmed" in error_msg:
                print(f"  ❌ Login failed: {email} - Email not confirmed")
            else:
                print(f"  ❌ Login failed: {email} - {error_msg}")
            return None
    
    async def authenticate_all(self):
        """Authenticate all users using Supabase"""
        print("\n🔑 Authenticating users with Supabase...")
        print("-" * 40)
        
        for user_type, user_data in TEST_USERS.items():
            token = await self.login(user_data["email"], user_data["password"])
            if token:
                self.tokens[user_type] = token
                print(f"  ✅ {user_type}: {user_data['email']}")
            else:
                print(f"  ❌ {user_type}: {user_data['email']}")
                print(f"     Please check user exists and is confirmed in Supabase")
        
        if not self.tokens:
            print("\n❌ No users authenticated!")
            print("   Make sure:")
            print("   1. Server is running on port 8000")
            print("   2. Users exist in Supabase Auth")
            print("   3. Users have confirmed their emails")
            print("   4. Staff profiles/org members are set up")
        
        return self.tokens
    
    async def test_endpoint(self, method: str, endpoint: str, 
                           expected_status: int = 200,
                           token_key: Optional[str] = "admin",
                           data: Dict = None,
                           name: str = None) -> bool:
        """Test an endpoint with authentication"""
        self.results["total"] += 1
        
        url = f"{self.base_url}{endpoint}"
        test_name = name or f"{method} {endpoint}"
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Prepare headers
            headers = {"Content-Type": "application/json"}
            
            if token_key and token_key in self.tokens:
                headers["Authorization"] = f"Bearer {self.tokens[token_key]}"
            elif token_key and token_key not in self.tokens:
                print(f"  ⚠️  No token for {token_key}, skipping test")
                self.results["skipped"] = self.results.get("skipped", 0) + 1
                return False
            
            try:
                # Make request
                response = None
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=data, headers=headers)
                elif method == "PATCH":
                    response = await client.patch(url, json=data, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                
                # Check result
                if response.status_code == expected_status:
                    print(f"  ✅ {test_name}")
                    self.results["passed"] += 1
                    self.results["details"].append({
                        "name": test_name,
                        "status": "PASSED",
                        "code": response.status_code
                    })
                    return True
                else:
                    print(f"  ❌ {test_name} - Expected {expected_status}, got {response.status_code}")
                    if response.text:
                        try:
                            error_data = response.json()
                            print(f"     Error: {error_data.get('detail', error_data)}")
                        except:
                            print(f"     Response: {response.text[:200]}")
                    self.results["failed"] += 1
                    self.results["details"].append({
                        "name": test_name,
                        "status": "FAILED",
                        "code": response.status_code,
                        "response": response.text[:200]
                    })
                    return False
                    
            except Exception as e:
                print(f"  ❌ {test_name} - Error: {e}")
                self.results["failed"] += 1
                self.results["details"].append({
                    "name": test_name,
                    "status": "ERROR",
                    "error": str(e)
                })
                return False
    
    async def run_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("🚀 CARBONTALLY API TESTS")
        print("="*70)
        print(f"🌐 Base URL: {self.base_url}")
        print(f"🔐 Using Supabase Auth")
        
        # Authenticate users
        await self.authenticate_all()
        
        if not self.tokens:
            print("\n❌ No users authenticated. Cannot run tests.")
            return
        
        # ==========================================
        # 1. PUBLIC ENDPOINTS
        # ==========================================
        print("\n📌 1. PUBLIC ENDPOINTS")
        print("-" * 40)
        
        await self.test_endpoint("GET", "/", 200, token_key=None, name="Root endpoint")
        await self.test_endpoint("GET", "/health", 200, token_key=None, name="Health check")
        
        # ==========================================
        # 2. WAITLIST (Public)
        # ==========================================
        print("\n📌 2. WAITLIST ENDPOINTS")
        print("-" * 40)
        
        waitlist_data = {
            "email": f"test_{random.randint(1000, 9999)}@example.com",
            "full_name": "Test User",
            "company_name": "Test Company"
        }
        await self.test_endpoint("POST", "/api/waitlist/", 200, 
                               token_key=None, data=waitlist_data, 
                               name="Create waitlist entry")
        
        await self.test_endpoint("GET", "/api/waitlist/", 200,
                               token_key="admin", name="Get waitlist entries")
        
        # ==========================================
        # 3. USER PROFILE
        # ==========================================
        print("\n📌 3. USER PROFILE")
        print("-" * 40)
        
        if self.tokens.get("user"):
            await self.test_endpoint("GET", "/api/users/profile", 200, 
                                   token_key="user", name="Get user profile")
            
            await self.test_endpoint("PUT", "/api/users/profile", 200,
                                   token_key="user", 
                                   data={"full_name": "Updated Test User"},
                                   name="Update user profile")
        
        # ==========================================
        # 4. ORGANIZATION ENDPOINTS
        # ==========================================
        print("\n📌 4. ORGANIZATION ENDPOINTS")
        print("-" * 40)
        
        if self.tokens.get("admin"):
            # Get organizations
            result = await self.test_endpoint("GET", "/api/organizations/", 200,
                                            token_key="admin", name="Get all organizations")
        
        # ==========================================
        # 5. ADMIN ENDPOINTS
        # ==========================================
        print("\n📌 5. ADMIN ENDPOINTS")
        print("-" * 40)
        
        if self.tokens.get("admin"):
            # Staff endpoints
            await self.test_endpoint("GET", "/api/admin/staff", 200,
                                   token_key="admin", name="Get staff list")
            
            await self.test_endpoint("GET", "/api/admin/staff/performance", 200,
                                   token_key="admin", name="Get staff performance")
            
            # Workload endpoints
            await self.test_endpoint("GET", "/api/admin/staff/workload", 200,
                                   token_key="admin", name="Get staff workload")
            
            # Queue settings
            await self.test_endpoint("GET", "/api/admin/queue/settings", 200,
                                   token_key="admin", name="Get queue settings")
            
            # Queue stats
            await self.test_endpoint("GET", "/api/admin/queue/stats", 200,
                                   token_key="admin", name="Get queue stats")
            
            # Beta endpoints
            await self.test_endpoint("GET", "/api/admin/beta/codes", 200,
                                   token_key="admin", name="Get beta codes")
            
            await self.test_endpoint("GET", "/api/admin/beta/users", 200,
                                   token_key="admin", name="Get beta users")
            
            # Audit logs
            await self.test_endpoint("GET", "/api/admin/audit/activity", 200,
                                   token_key="admin", name="Get audit logs")
            
            # Email logs
            await self.test_endpoint("GET", "/api/admin/logs/email", 200,
                                   token_key="admin", name="Get email logs")
            
            # Processing logs
            await self.test_endpoint("GET", "/api/admin/logs/processing", 200,
                                   token_key="admin", name="Get processing logs")
            
            # System health
            await self.test_endpoint("GET", "/api/admin/analytics/system/health", 200,
                                   token_key="admin", name="Get system health")
            
            # Email templates
            await self.test_endpoint("GET", "/api/admin/email/templates", 200,
                                   token_key="admin", name="Get email templates")
            
            # Settings
            await self.test_endpoint("GET", "/api/admin/settings/history", 200,
                                   token_key="admin", name="Get settings history")
        
        # ==========================================
        # 6. PERMISSION TESTS
        # ==========================================
        print("\n📌 6. PERMISSION TESTS")
        print("-" * 40)
        
        if self.tokens.get("user") and self.tokens.get("admin"):
            # Regular user accessing admin - should fail
            await self.test_endpoint("GET", "/api/admin/staff", 403,
                                   token_key="user", name="User accessing admin (should fail)")
            
            # Org viewer accessing admin - should fail
            await self.test_endpoint("GET", "/api/admin/staff", 403,
                                   token_key="org_viewer", name="Org viewer accessing admin (should fail)")
        
        # ==========================================
        # 7. GLOSSARY ENDPOINTS
        # ==========================================
        print("\n📌 7. GLOSSARY ENDPOINTS")
        print("-" * 40)
        
        if self.tokens.get("admin"):
            glossary_data = {
                "term": f"Test Term {random.randint(1000, 9999)}",
                "definition": "This is a test definition",
                "category": "Test"
            }
            
            await self.test_endpoint("POST", "/api/glossary", 201,
                                   token_key="admin", data=glossary_data,
                                   name="Create glossary term")
            
            await self.test_endpoint("GET", "/api/glossary", 200,
                                   token_key="admin", name="Get glossary")
            
            await self.test_endpoint("GET", "/api/glossary/categories", 200,
                                   token_key="admin", name="Get glossary categories")
            
            await self.test_endpoint("GET", "/api/glossary/search?q=Test", 200,
                                   token_key="admin", name="Search glossary")
        
        # ==========================================
        # 8. FEEDBACK ENDPOINTS
        # ==========================================
        print("\n📌 8. FEEDBACK ENDPOINTS")
        print("-" * 40)
        
        if self.tokens.get("user"):
            feedback_data = {
                "type": "suggestion",
                "title": "Test Feedback",
                "description": "This is a test feedback",
                "severity": "medium",
                "rating": 4
            }
            
            await self.test_endpoint("POST", "/api/feedback", 201,
                                   token_key="user", data=feedback_data,
                                   name="Submit feedback")
            
            await self.test_endpoint("GET", "/api/feedback", 200,
                                   token_key="user", name="Get user feedback")
        
        print("\n" + "="*70)
    
    def print_summary(self):
        """Print summary"""
        print("\n" + "="*70)
        print("📊 TEST SUMMARY")
        print("="*70)
        
        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        skipped = self.results.get("skipped", 0)
        
        if total > 0:
            print(f"\n  ✅ Passed: {passed}/{total} ({passed/total*100:.1f}%)")
            print(f"  ❌ Failed: {failed}/{total} ({failed/total*100:.1f}%)")
            if skipped > 0:
                print(f"  ⏭️  Skipped: {skipped}")
        else:
            print("\n  No tests were run.")
        
        if failed == 0 and total > 0:
            print("\n🎉 All tests passed!")
        elif failed > 0:
            print(f"\n⚠️  {failed} test(s) failed. Check the output above for details.")
            
            # Show failed tests
            print("\n❌ Failed Tests:")
            for detail in self.results["details"]:
                if detail.get("status") == "FAILED":
                    print(f"  - {detail.get('name', 'Unknown')}")
                    if detail.get("response"):
                        print(f"    Response: {detail['response']}")
        
        # Export results
        try:
            with open("test_results.json", "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"\n📝 Detailed results saved to test_results.json")
        except:
            pass
        
        print("="*70)

async def main():
    """Run tests"""
    print(f"🔍 Testing API at: {BASE_URL}")
    print(f"🔐 Using Supabase Auth with URL: {SUPABASE_URL}")
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Server is running!")
            else:
                print(f"⚠️  Server responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("   Make sure the server is running: uvicorn main:app --reload")
        return
    
    # Check if Supabase is configured
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        print("❌ Supabase not configured!")
        print("   Make sure SUPABASE_URL and SUPABASE_ANON_KEY are set in .env")
        return
    
    tester = APITester()
    await tester.run_tests()
    tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())