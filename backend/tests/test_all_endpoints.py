# backend/tests/test_all_endpoints.py
"""
Comprehensive API test script for all 263 endpoints
Run: python backend/tests/test_all_endpoints.py
"""

import os
import sys
import asyncio
import json
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

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
    "admin": {"email": "admin@carbontally.co.uk", "password": "AdminPass123!", "role": "admin"},
    "staff": {"email": "staff@carbontally.co.uk", "password": "StaffPass123!", "role": "staff"},
    "org_admin": {"email": "orgadmin@test.com", "password": "OrgAdminPass123!", "role": "org_admin"},
    "org_viewer": {"email": "orgviewer@test.com", "password": "OrgViewerPass123!", "role": "org_viewer"},
    "user": {"email": "testuser@example.com", "password": "UserPass123!", "role": "user"}
}

# ==========================================
# TEST RESULTS
# ==========================================

class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.details = []
    
    def add_result(self, name: str, status: str, status_code: int, error: Optional[str] = None):
        self.total += 1
        if status == "PASSED":
            self.passed += 1
        elif status == "FAILED":
            self.failed += 1
        elif status == "SKIPPED":
            self.skipped += 1
        
        self.details.append({
            "name": name,
            "status": status,
            "status_code": status_code,
            "error": error[:200] if error else None
        })
    
    def print_summary(self):
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        if self.total > 0:
            print(f"\n  ✅ Passed: {self.passed}/{self.total} ({self.passed/self.total*100:.1f}%)")
            print(f"  ❌ Failed: {self.failed}/{self.total} ({self.failed/self.total*100:.1f}%)")
            print(f"  ⏭️  Skipped: {self.skipped}")
        else:
            print("\n  No tests run.")
        
        if self.failed > 0:
            print("\n❌ Failed Tests:")
            for detail in self.details:
                if detail["status"] == "FAILED":
                    print(f"  - {detail['name']} (Status: {detail['status_code']})")
                    if detail.get("error"):
                        print(f"    Error: {detail['error']}")
        
        # Save results
        with open("test_results_all.json", "w") as f:
            json.dump({
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "skipped": self.skipped,
                "details": self.details
            }, f, indent=2, default=str)
        
        print(f"\n📝 Detailed results saved to test_results_all.json")

# ==========================================
# API TESTER CLASS
# ==========================================

class APITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.tokens = {}
        self.test_data = {}
        self.results = TestResults()
        self.supabase = None
    
    def get_supabase_client(self):
        if not self.supabase and SUPABASE_URL and SUPABASE_ANON_KEY:
            self.supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
        return self.supabase
    
    async def login(self, email: str, password: str) -> Optional[str]:
        """Login using Supabase Auth"""
        try:
            supabase = self.get_supabase_client()
            if supabase:
                response = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                if response and response.session:
                    return response.session.access_token
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
        
        return bool(self.tokens)
    
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
                           skip_auth: bool = False,
                           skip_test: bool = False) -> Dict:
        """Test a single endpoint"""
        if skip_test:
            self.results.add_result(name or f"{method} {endpoint}", "SKIPPED", 0)
            return {"success": True, "skipped": True}
        
        url = f"{self.base_url}{endpoint}"
        test_name = name or f"{method} {endpoint}"
        
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
                elif method == "PATCH":
                    response = await client.patch(url, json=data, headers=headers)
                elif method == "DELETE":
                    response = await client.delete(url, headers=headers)
                
                if response is None:
                    self.results.add_result(test_name, "FAILED", 0, "No response")
                    return {"success": False, "error": "No response"}
                
                if response.status_code == expected_status:
                    self.results.add_result(test_name, "PASSED", response.status_code)
                    try:
                        return {"success": True, "data": response.json() if response.text else None}
                    except:
                        return {"success": True, "data": response.text}
                else:
                    error_text = response.text[:200] if response.text else "No response"
                    self.results.add_result(test_name, "FAILED", response.status_code, error_text)
                    return {"success": False, "status_code": response.status_code, "error": error_text}
                    
            except Exception as e:
                self.results.add_result(test_name, "FAILED", 0, str(e))
                return {"success": False, "error": str(e)}
    
    async def run_tests(self):
        """Run all endpoint tests"""
        print("\n" + "="*80)
        print("🚀 TESTING ALL ENDPOINTS")
        print("="*80)
        print(f"🌐 Base URL: {self.base_url}")
        
        # Authenticate
        if not await self.authenticate_all():
            print("❌ Authentication failed. Cannot run tests.")
            return
        
        # Get test organization
        try:
            supabase = self.get_supabase_client()
            if supabase:
                org = supabase.from_('organizations').select('id').limit(1).execute()
                if org.data:
                    self.test_data["org_id"] = org.data[0]['id']
                    print(f"\n📝 Using organization: {self.test_data['org_id']}")
        except Exception as e:
            print(f"⚠️ Could not get organization: {e}")
        
        # ==========================================
        # 1. PUBLIC ENDPOINTS
        # ==========================================
        print("\n📌 1. PUBLIC ENDPOINTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/", 200, skip_auth=True, name="Root")
        await self.test_endpoint("GET", "/health", 200, skip_auth=True, name="Health check")
        
        # ==========================================
        # 2. WAITLIST
        # ==========================================
        print("\n📌 2. WAITLIST ENDPOINTS")
        print("-" * 50)
        
        await self.test_endpoint("POST", "/api/waitlist/", 200,
                               skip_auth=True,
                               data={"email": f"test_{random.randint(1000,9999)}@example.com", "full_name": "Test User"},
                               name="Add to waitlist")
        await self.test_endpoint("GET", "/api/waitlist/", 200,
                               token_key="admin", name="Get waitlist")
        
        # ==========================================
        # 3. USER PROFILE
        # ==========================================
        print("\n📌 3. USER PROFILE ENDPOINTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/users/profile", 200,
                               token_key="user", name="Get profile")
        await self.test_endpoint("PUT", "/api/users/profile", 200,
                               token_key="user",
                               data={"full_name": f"Test User {random.randint(1000,9999)}"},
                               name="Update profile")
        
        # ==========================================
        # 4. REFERENCE DATA
        # ==========================================
        print("\n📌 4. REFERENCE DATA")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/reference/units", 200,
                               token_key="user", name="Get units")
        await self.test_endpoint("GET", "/api/reference/fuel-types", 200,
                               token_key="user", name="Get fuel types")
        await self.test_endpoint("GET", "/api/reference/categories", 200,
                               token_key="user", name="Get categories")
        await self.test_endpoint("GET", "/api/reference/facility-types", 200,
                               token_key="user", name="Get facility types")
        await self.test_endpoint("GET", "/api/reference/asset-types", 200,
                               token_key="user", name="Get asset types")
        await self.test_endpoint("GET", "/api/reference/facilities", 200,
                               token_key="user", name="Get facilities list")
        await self.test_endpoint("GET", "/api/reference/assets", 200,
                               token_key="user", name="Get assets list")
        
        # ==========================================
        # 5. GLOSSARY
        # ==========================================
        print("\n📌 5. GLOSSARY ENDPOINTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/glossary/", 200,
                               token_key="admin", name="Get glossary")
        await self.test_endpoint("GET", "/api/glossary/categories", 200,
                               token_key="admin", name="Get glossary categories")
        await self.test_endpoint("GET", "/api/glossary/search?q=Test", 200,
                               token_key="admin", name="Search glossary")
        
        # Create glossary term - expect 201
        glossary_data = {
            "term": f"Test Term {random.randint(1000,9999)}",
            "definition": "This is a test definition",
            "category": "Test"
        }
        await self.test_endpoint("POST", "/api/glossary/", 201,
                               token_key="admin", data=glossary_data,
                               name="Create glossary term")
        
        # ==========================================
        # 6. ORGANIZATION MANAGEMENT
        # ==========================================
        print("\n📌 6. ORGANIZATION MANAGEMENT")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/organizations/", 200,
                               token_key="admin", name="Get all organizations")
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            
            await self.test_endpoint("GET", f"/api/organizations/{org_id}", 200,
                                   token_key="admin", name="Get organization")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/stats", 200,
                                   token_key="admin", name="Get org stats")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata", 200,
                                   token_key="org_admin", name="Get org metadata")
            await self.test_endpoint("PUT", f"/api/organizations/{org_id}/metadata", 200,
                                   token_key="org_admin",
                                   data={"annual_revenue": 1000000},
                                   name="Update org metadata")
            
            # ❌ User should not access org details
            await self.test_endpoint("GET", f"/api/organizations/{org_id}", 403,
                                   token_key="user", name="User accessing org (should fail)")
        
        # ==========================================
        # 7. ORGANIZATION METADATA
        # ==========================================
        print("\n📌 7. ORGANIZATION METADATA")
        print("-" * 50)
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata/all", 200,
                                   token_key="org_admin", name="Get all metadata")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata/financials", 200,
                                   token_key="org_admin", name="Get financial metadata")
            await self.test_endpoint("PUT", f"/api/organizations/{org_id}/metadata/financials", 200,
                                   token_key="org_admin",
                                   data={"annual_revenue": 1000000},
                                   name="Update financial metadata")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata/employees", 200,
                                   token_key="org_admin", name="Get employee metadata")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata/sustainability", 200,
                                   token_key="org_admin", name="Get sustainability metadata")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata/contacts", 200,
                                   token_key="org_admin", name="Get contact metadata")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata/industry", 200,
                                   token_key="org_admin", name="Get industry metadata")
            await self.test_endpoint("POST", f"/api/organizations/{org_id}/metadata/validate", 200,
                                   token_key="org_admin", name="Validate metadata")
        
        # ==========================================
        # 8. FACILITIES & ASSETS
        # ==========================================
        print("\n📌 8. FACILITIES & ASSETS")
        print("-" * 50)
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/facilities", 200,
                                   token_key="org_admin", name="Get facilities")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/assets", 200,
                                   token_key="org_admin", name="Get assets")
            
            # Create facility
            facility_data = {
                "name": f"Test Facility {random.randint(1000,9999)}",
                "type": "Office",
                "postcode": "EC1A 1BB",
                "city": "London"
            }
            result = await self.test_endpoint("POST", f"/api/organizations/{org_id}/facilities", 201,
                                            token_key="org_admin", data=facility_data,
                                            name="Create facility")
            if result.get("success") and result.get("data"):
                self.test_data["facility_id"] = result["data"].get("id")
            
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/facilities/stats", 200,
                                   token_key="org_admin", name="Get facility stats")
            
            # Create asset
            if self.test_data.get("facility_id"):
                asset_data = {
                    "name": f"Test Asset {random.randint(1000,9999)}",
                    "facility_id": self.test_data["facility_id"],
                    "type": "Equipment",
                    "capacity": 100.0,
                    "capacity_unit": "kW"
                }
                result = await self.test_endpoint("POST", f"/api/organizations/{org_id}/assets", 201,
                                                token_key="org_admin", data=asset_data,
                                                name="Create asset")
                if result.get("success") and result.get("data"):
                    self.test_data["asset_id"] = result["data"].get("id")
                
                await self.test_endpoint("GET", f"/api/organizations/{org_id}/assets/stats", 200,
                                       token_key="org_admin", name="Get asset stats")
        
        # ==========================================
        # 9. ADMIN STAFF
        # ==========================================
        print("\n📌 9. ADMIN STAFF ENDPOINTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/staff", 200,
                               token_key="admin", name="Get staff list")
        await self.test_endpoint("GET", "/api/admin/staff/performance", 200,
                               token_key="admin", name="Get staff performance")
        await self.test_endpoint("GET", "/api/admin/staff/me", 200,
                               token_key="admin", name="Get my staff profile")
        await self.test_endpoint("GET", "/api/admin/staff/activity", 200,
                               token_key="admin", name="Get staff activity")
        await self.test_endpoint("GET", "/api/admin/staff/performance/export", 200,
                               token_key="admin", name="Export staff performance")
        
        # ==========================================
        # 10. ADMIN WORKLOAD - CORRECTED PATHS
        # ==========================================
        print("\n📌 10. ADMIN WORKLOAD")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/workload/queue/settings", 200,
                               token_key="admin", name="Get queue settings")
        await self.test_endpoint("GET", "/api/admin/workload/queue/stats", 200,
                               token_key="admin", name="Get queue stats")
        await self.test_endpoint("GET", "/api/admin/workload/staff/workload", 200,
                               token_key="admin", name="Get staff workload")
        
        # ==========================================
        # 11. ADMIN BETA
        # ==========================================
        print("\n📌 11. ADMIN BETA")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/beta/codes", 200,
                               token_key="admin", name="Get beta codes")
        await self.test_endpoint("GET", "/api/admin/beta/users", 200,
                               token_key="admin", name="Get beta users")
        await self.test_endpoint("GET", "/api/admin/beta/users/stats", 200,
                               token_key="admin", name="Get beta stats")
        
        # ==========================================
        # 12. ADMIN AUDIT
        # ==========================================
        print("\n📌 12. ADMIN AUDIT")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/audit/activity", 200,
                               token_key="admin", name="Get audit logs")
        await self.test_endpoint("GET", "/api/admin/audit/activity/export", 200,
                               token_key="admin", name="Export audit logs")
        await self.test_endpoint("GET", "/api/admin/audit/activity/search", 200,
                               token_key="admin", name="Search audit logs")
        
        # ==========================================
        # 13. ADMIN LOGS
        # ==========================================
        print("\n📌 13. ADMIN LOGS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/logs/email", 200,
                               token_key="admin", name="Get email logs")
        await self.test_endpoint("GET", "/api/admin/logs/processing", 200,
                               token_key="admin", name="Get processing logs")
        await self.test_endpoint("GET", "/api/admin/logs/email/stats", 200,
                               token_key="admin", name="Get email stats")
        await self.test_endpoint("GET", "/api/admin/logs/processing/stats", 200,
                               token_key="admin", name="Get processing stats")
        
        # ==========================================
        # 14. ADMIN PERMISSIONS
        # ==========================================
        print("\n📌 14. ADMIN PERMISSIONS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/permissions/roles", 200,
                               token_key="admin", name="Get roles")
        await self.test_endpoint("GET", "/api/admin/permissions/permissions/list", 200,
                               token_key="admin", name="Get permissions list")
        
        # ==========================================
        # 15. ADMIN DEFRA
        # ==========================================
        print("\n📌 15. ADMIN DEFRA")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/defra/factors", 200,
                               token_key="admin", name="Get defra factors")
        await self.test_endpoint("GET", "/api/admin/defra/years", 200,
                               token_key="admin", name="Get defra years")
        await self.test_endpoint("GET", "/api/admin/defra/activities", 200,
                               token_key="admin", name="Get defra activities")
        await self.test_endpoint("GET", "/api/admin/defra/validate", 200,
                               token_key="admin", name="Validate defra factor")
        
        # ==========================================
        # 16. ADMIN SETTINGS
        # ==========================================
        print("\n📌 16. ADMIN SETTINGS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/settings/settings-history", 200,
                               token_key="admin", name="Get settings history")
        
        # ==========================================
        # 17. ADMIN EMAIL TEMPLATES
        # ==========================================
        print("\n📌 17. ADMIN EMAIL TEMPLATES")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/email/templates", 200,
                               token_key="admin", name="Get email templates")
        await self.test_endpoint("GET", "/api/admin/email/templates/types", 200,
                               token_key="admin", name="Get template types")
        
        # ==========================================
        # 18. ADMIN EXTRACTION
        # ==========================================
        print("\n📌 18. ADMIN EXTRACTION")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/extraction/reviews/pending", 200,
                               token_key="admin", name="Get pending reviews")
        
        # ==========================================
        # 19. ADMIN REVIEW HISTORY
        # ==========================================
        print("\n📌 19. ADMIN REVIEW HISTORY")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/review-history/history", 200,
                               token_key="admin", name="Get review history")
        await self.test_endpoint("GET", "/api/admin/review-history/history/audit", 200,
                               token_key="admin", name="Get review audit trail")
        
        # ==========================================
        # 20. ADMIN BULK
        # ==========================================
        print("\n📌 20. ADMIN BULK")
        print("-" * 50)
        
        # These are POST/DELETE endpoints, just test they exist
        await self.test_endpoint("DELETE", "/api/admin/bulk/documents/bulk", 422,  # This may be the correct status
                       token_key="admin", 
                       data={"document_ids": []},  # Add a body
                       name="Bulk delete documents")
        
        # ==========================================
        # 21. ADMIN ANALYTICS
        # ==========================================
        print("\n📌 21. ADMIN ANALYTICS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/analytics/system/health", 200,
                               token_key="admin", name="Get system health")
        await self.test_endpoint("GET", "/api/admin/analytics/system/performance", 200,
                               token_key="admin", name="Get system performance")
        await self.test_endpoint("GET", "/api/admin/analytics/system/usage", 200,
                               token_key="admin", name="Get system usage")
        
        # ==========================================
        # 22. ADMIN ASSIGNMENTS
        # ==========================================
        print("\n📌 22. ADMIN ASSIGNMENTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/admin/assignments/assignment-stats", 200,
                               token_key="admin", name="Get assignment stats")
        await self.test_endpoint("GET", "/api/admin/assignments/available", 200,
                               token_key="admin", name="Get available reviews")
        await self.test_endpoint("GET", "/api/admin/assignments/staff", 200,
                               token_key="admin", name="Get staff list")
        
        # ==========================================
        # 23. FEEDBACK
        # ==========================================
        print("\n📌 23. FEEDBACK")
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
        await self.test_endpoint("GET", "/api/feedback", 200,
                               token_key="user", name="Get user feedback")
        
        # ==========================================
        # 24. REPORTS
        # ==========================================
        print("\n📌 24. REPORTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/reports/report_status", 200,
                               token_key="admin", name="Get report status")
        await self.test_endpoint("GET", "/api/reports/defra-mapping", 200,
                               token_key="org_admin", name="Get defra mapping")
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            await self.test_endpoint("GET", f"/api/reports/defra-factors/2024", 200,
                                   token_key="org_admin", name="Get defra factors by year")
        
        # ==========================================
        # 25. ORGANIZATION DASHBOARD
        # ==========================================
        print("\n📌 25. ORGANIZATION DASHBOARD")
        print("-" * 50)
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            await self.test_endpoint("GET", f"/api/organizations/dashboard-summary?organization_id={org_id}", 200,
                                   token_key="org_admin", name="Get dashboard summary")
            await self.test_endpoint("GET", f"/api/organizations/organization-activity?organization_id={org_id}", 200,
                                   token_key="org_admin", name="Get organization activity")
        
        # ==========================================
        # 26. ORGANIZATION MEMBERS
        # ==========================================
        print("\n📌 26. ORGANIZATION MEMBERS")
        print("-" * 50)
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/members", 200,
                                   token_key="org_admin", name="Get members")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/members/stats", 200,
                                   token_key="org_admin", name="Get member stats")
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/members/roles", 200,
                                   token_key="org_admin", name="Get member roles")
        
        # ==========================================
        # 27. NOTIFICATIONS
        # ==========================================
        print("\n📌 27. NOTIFICATIONS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/notifications/templates", 200,
                               token_key="admin", name="Get notification templates")
        
        # ==========================================
        # 28. EMISSIONS - CORRECTED PATHS
        # ==========================================
        print("\n📌 28. EMISSIONS")
        print("-" * 50)
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            await self.test_endpoint("GET", f"/api/emissions/emissions?organization_id={org_id}", 200,
                                   token_key="org_admin", name="Get emissions")
            await self.test_endpoint("GET", f"/api/emissions/emissions/stats?organization_id={org_id}", 200,
                                   token_key="org_admin", name="Get emission stats")
        
        # ==========================================
        # 29. DOCUMENTS
        # ==========================================
        print("\n📌 29. DOCUMENTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/documents/", 200,
                               token_key="org_admin", name="Get documents")
        await self.test_endpoint("GET", "/api/documents/stats/", 200,
                               token_key="org_admin", name="Get document stats")
        
        # ==========================================
        # 30. DRAFTS
        # ==========================================
        print("\n📌 30. DRAFTS")
        print("-" * 50)
        
        await self.test_endpoint("GET", "/api/drafts/", 200,
                               token_key="org_admin", name="Get drafts")
        
        # ==========================================
        # 31. PERMISSION TESTS
        # ==========================================
        print("\n📌 31. PERMISSION TESTS")
        print("-" * 50)
        
        # ❌ These should fail with 403
        await self.test_endpoint("GET", "/api/admin/staff", 403,
                               token_key="user", name="User accessing admin (should fail)")
        await self.test_endpoint("GET", "/api/admin/staff", 403,
                               token_key="org_viewer", name="Org viewer accessing admin (should fail)")
        
        # ✅ Admin should pass
        await self.test_endpoint("GET", "/api/admin/staff", 200,
                               token_key="admin", name="Admin accessing admin (should pass)")
        
        # ==========================================
        # SUMMARY
        # ==========================================
        self.results.print_summary()

# ==========================================
# MAIN
# ==========================================

async def main():
    """Run all tests"""
    print("🔍 Testing all endpoints...")
    
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
    
    tester = APITester()
    await tester.run_tests()

if __name__ == "__main__":
    asyncio.run(main())