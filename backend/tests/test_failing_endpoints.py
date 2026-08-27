# backend/tests/test_failing_endpoints.py
"""
Test only the failing endpoints to debug issues.
Run: python backend/tests/test_failing_endpoints.py
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add backend to path
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

import httpx
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================

BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Test users
TEST_USERS = {
    "admin": {"email": "admin@carbontally.co.uk", "password": "AdminPass123!"},
    "user": {"email": "testuser@example.com", "password": "UserPass123!"},
    "org_admin": {"email": "orgadmin@test.com", "password": "OrgAdminPass123!"},
    "org_viewer": {"email": "orgviewer@test.com", "password": "OrgViewerPass123!"},
}

# ==========================================
# TEST RESULTS
# ==========================================

class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.details = []
    
    def add_result(self, name: str, status: str, status_code: int, error: Optional[str] = None):
        self.total += 1
        if status == "PASSED":
            self.passed += 1
        elif status == "FAILED":
            self.failed += 1
        
        self.details.append({
            "name": name,
            "status": status,
            "status_code": status_code,
            "error": error
        })
    
    def print_summary(self):
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        print(f"\n  ✅ Passed: {self.passed}/{self.total} ({self.passed/self.total*100:.1f}%)" if self.total > 0 else "  ✅ Passed: 0")
        print(f"  ❌ Failed: {self.failed}/{self.total} ({self.failed/self.total*100:.1f}%)" if self.total > 0 else "  ❌ Failed: 0")
        
        if self.failed > 0:
            print("\n❌ Failed Tests:")
            for detail in self.details:
                if detail["status"] == "FAILED":
                    print(f"  - {detail['name']} (Status: {detail['status_code']})")
                    if detail.get("error"):
                        print(f"    Error: {detail['error'][:200]}")

# ==========================================
# TESTER CLASS
# ==========================================

class FailingEndpointTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.tokens = {}
        self.results = TestResults()
        self.test_data = {}
    
    async def login(self, email: str, password: str) -> Optional[str]:
        """Login using Supabase Auth"""
        try:
            # Try Supabase auth first
            if SUPABASE_URL and SUPABASE_ANON_KEY:
                supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                if response and response.session:
                    return response.session.access_token
            
            # Fallback to API login
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/auth/login",
                    json={"email": email, "password": password}
                )
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")
            return None
        except Exception as e:
            print(f"  ❌ Login error for {email}: {e}")
            return None
    
    async def authenticate_all(self):
        """Authenticate all test users"""
        print("\n🔑 Authenticating users...")
        print("-" * 50)
        
        for user_type, user_data in TEST_USERS.items():
            token = await self.login(user_data["email"], user_data["password"])
            if token:
                self.tokens[user_type] = token
                print(f"  ✅ {user_type}: {user_data['email']}")
            else:
                print(f"  ❌ {user_type}: {user_data['email']}")
        
        if not self.tokens:
            print("\n❌ No users authenticated!")
            return False
        return True
    
    def get_headers(self, token_key: str = "admin") -> Dict[str, str]:
        token = self.tokens.get(token_key)
        if not token:
            return {}
        return {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def test_endpoint(self, method: str, endpoint: str, 
                           expected_status: int = 200,
                           token_key: str = "admin",
                           data: Optional[Dict] = None,
                           name: Optional[str] = None,
                           skip_auth: bool = False) -> bool:
        """Test a single endpoint"""
        url = f"{self.base_url}{endpoint}"
        test_name = name or f"{method} {endpoint}"
        
        print(f"\n🔍 Testing: {method} {endpoint}")
        print(f"   Expected: {expected_status}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            headers = {} if skip_auth else self.get_headers(token_key)
            
            try:
                response = None
                if method == "GET":
                    response = await client.get(url, headers=headers)
                elif method == "POST":
                    response = await client.post(url, json=data, headers=headers)
                elif method == "PUT":
                    response = await client.put(url, json=data, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                
                if response:
                    print(f"   Status: {response.status_code}")
                    if response.status_code != expected_status:
                        print(f"   Response: {response.text[:300]}")
                    
                    if response.status_code == expected_status:
                        self.results.add_result(test_name, "PASSED", response.status_code)
                        if response.text:
                            try:
                                data = response.json()
                                print(f"   Data: {json.dumps(data, indent=2)[:200]}")
                            except:
                                pass
                        return True
                    else:
                        self.results.add_result(test_name, "FAILED", response.status_code, response.text[:200])
                        return False
                else:
                    self.results.add_result(test_name, "FAILED", 0, "No response")
                    return False
                    
            except Exception as e:
                print(f"   Error: {e}")
                self.results.add_result(test_name, "FAILED", 0, str(e))
                return False
    
    async def run_tests(self):
        """Run tests for all failing endpoints"""
        print("\n" + "="*80)
        print("🔍 TESTING FAILING ENDPOINTS ONLY")
        print("="*80)
        print(f"🌐 Base URL: {self.base_url}")
        
        # Authenticate
        if not await self.authenticate_all():
            return
        
        # ==========================================
        # 1. GLOSSARY ENDPOINTS
        # ==========================================
        print("\n📌 1. GLOSSARY ENDPOINTS")
        print("-" * 50)
        
        # Test GET glossary
        await self.test_endpoint("GET", "/api/glossary/", 200, 
                               token_key="admin", name="Get glossary")
        
        # Test POST glossary
        glossary_data = {
            "term": f"Test Term {__import__('random').randint(1000,9999)}",
            "definition": "This is a test definition",
            "category": "Test"
        }
        await self.test_endpoint("POST", "/api/glossary/", 200,
                               token_key="admin", data=glossary_data, 
                               name="Create glossary term")
        
        # ==========================================
        # 2. ADMIN STAFF ENDPOINTS
        # ==========================================
        print("\n📌 2. ADMIN STAFF ENDPOINTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/staff", 200,
                               token_key="admin", name="Get staff list")
        
        await self.test_endpoint("GET", "/api/admin/staff/performance", 200,
                               token_key="admin", name="Get staff performance")
        
        # ==========================================
        # 3. PERMISSIONS ROLES
        # ==========================================
        print("\n📌 3. PERMISSIONS ROLES")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/permissions/roles", 200,
                               token_key="admin", name="Get roles")
        
        # ==========================================
        # 4. FEEDBACK
        # ==========================================
        print("\n📌 4. FEEDBACK")
        print("-" * 50)
        
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
        
        # ==========================================
        # 5. REPORTS
        # ==========================================
        print("\n📌 5. REPORTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/reports/report_status", 200,
                               token_key="admin", name="Get report status")
        
        # ==========================================
        # 6. PERMISSION TESTS
        # ==========================================
        print("\n📌 6. PERMISSION TESTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/staff", 403,
                               token_key="user", name="User accessing admin (should fail)")
        
        await self.test_endpoint("GET", "/api/admin/staff", 403,
                               token_key="org_viewer", name="Org viewer accessing admin (should fail)")
        
        # ==========================================
        # 7. ORGANIZATION ENDPOINTS (Check if they work)
        # ==========================================
        print("\n📌 7. ORGANIZATION ENDPOINTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/organizations/", 200,
                               token_key="admin", name="Get all organizations")
        
        # ==========================================
        # SUMMARY
        # ==========================================
        self.results.print_summary()

# ==========================================
# MAIN
# ==========================================

async def main():
    """Run the tests"""
    print("🔍 Testing failing endpoints...")
    
    # Check if server is running
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                print("✅ Server is running!")
            else:
                print(f"⚠️ Server responded with status: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to server at {BASE_URL}")
        print(f"   Error: {e}")
        print("   Make sure the server is running: uvicorn main:app --reload")
        return
    
    tester = FailingEndpointTester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())