# backend/tests/test_api.py
"""
Comprehensive API test script
Run: python -m pytest tests/test_api.py -v
Or: python backend/tests/test_api.py
"""

import asyncio
import httpx
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random
import string

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tests.config import TestConfig
from tests.auth_helper import AuthHelper, TestUser, create_test_users

class APITester:
    def __init__(self, base_url: str = TestConfig.API_BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "details": []
        }
        self.auth_headers = {}
        self.admin_headers = {}
        self.test_data = {}
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def authenticate(self, email: str, password: str) -> bool:
        """Authenticate and get token"""
        try:
            response = await self.client.post(
                f"{self.base_url}/api/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    return True
            return False
        except Exception as e:
            print(f"❌ Authentication error: {e}")
            return False
    
    def set_auth_headers(self, token: str):
        """Set authentication headers"""
        self.auth_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    def set_admin_headers(self, token: str):
        """Set admin authentication headers"""
        self.admin_headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def test_endpoint(self, method: str, endpoint: str, 
                           expected_status: int = 200, 
                           data: Optional[Dict] = None,
                           headers: Optional[Dict] = None,
                           name: Optional[str] = None,
                           skip_auth: bool = False) -> Dict:
        """Test a single endpoint"""
        self.results["total"] += 1
        
        url = f"{self.base_url}{endpoint}"
        test_name = name or f"{method} {endpoint}"
        
        try:
            # Prepare headers
            request_headers = headers or (self.auth_headers if not skip_auth else {})
            
            # Make request
            response = None
            if method.upper() == "GET":
                response = await self.client.get(url, headers=request_headers)
            elif method.upper() == "POST":
                response = await self.client.post(url, json=data, headers=request_headers)
            elif method.upper() == "PUT":
                response = await self.client.put(url, json=data, headers=request_headers)
            elif method.upper() == "PATCH":
                response = await self.client.patch(url, json=data, headers=request_headers)
            elif method.upper() == "DELETE":
                response = await self.client.delete(url, headers=request_headers)
            
            # Check result
            if response.status_code == expected_status:
                self.results["passed"] += 1
                status = "✅ PASSED"
            else:
                self.results["failed"] += 1
                status = f"❌ FAILED (expected {expected_status}, got {response.status_code})"
            
            result = {
                "name": test_name,
                "method": method,
                "endpoint": endpoint,
                "status": status,
                "response_code": response.status_code,
                "response": response.text[:500] if response.text else None
            }
            
            if response.status_code == 200:
                try:
                    result["data"] = response.json()
                except:
                    pass
            
            self.results["details"].append(result)
            
            # Print result
            print(f"{status} - {test_name}")
            if response.status_code != expected_status:
                print(f"  Response: {response.text[:200]}")
            
            return {
                "success": response.status_code == expected_status,
                "status_code": response.status_code,
                "data": response.json() if response.text and response.text.startswith('{') else None,
                "text": response.text
            }
            
        except Exception as e:
            self.results["failed"] += 1
            print(f"❌ ERROR - {test_name}: {e}")
            self.results["details"].append({
                "name": test_name,
                "method": method,
                "endpoint": endpoint,
                "status": f"❌ ERROR: {e}",
                "error": str(e)
            })
            return {"success": False, "error": str(e)}
    
    async def test_all_endpoints(self, admin_token: str, user_token: str):
        """Test all API endpoints"""
        
        # Set authentication headers
        self.set_auth_headers(user_token)
        self.set_admin_headers(admin_token)
        
        print("\n" + "="*80)
        print("🚀 STARTING API TESTS")
        print("="*80 + "\n")
        
        # ==========================================
        # 1. PUBLIC ENDPOINTS (No Auth Required)
        # ==========================================
        print("\n📌 PUBLIC ENDPOINTS")
        print("-" * 40)
        
        await self.test_endpoint("GET", "/", 200, name="Root endpoint", skip_auth=True)
        await self.test_endpoint("GET", "/health", 200, name="Health check", skip_auth=True)
        await self.test_endpoint("GET", "/test-upload", 200, name="Test upload", skip_auth=True)
        
        # ==========================================
        # 2. WAITLIST ENDPOINTS (Public)
        # ==========================================
        print("\n📌 WAITLIST ENDPOINTS")
        print("-" * 40)
        
        # Test waitlist creation
        waitlist_data = {
            "email": f"test_{random.randint(1000, 9999)}@example.com",
            "full_name": "Test User",
            "company_name": "Test Company"
        }
        await self.test_endpoint("POST", "/api/waitlist/", 200, 
                               data=waitlist_data, name="Create waitlist entry", skip_auth=True)
        
        # Test get waitlist (authenticated)
        await self.test_endpoint("GET", "/api/waitlist/", 200, 
                               name="Get waitlist entries")
        
        # ==========================================
        # 3. USER AUTHENTICATION ENDPOINTS
        # ==========================================
        print("\n📌 USER AUTHENTICATION ENDPOINTS")
        print("-" * 40)
        
        # Test user profile
        await self.test_endpoint("GET", "/api/users/profile", 200, 
                               name="Get user profile")
        
        # Test update profile
        await self.test_endpoint("PUT", "/api/users/profile", 200,
                               data={"full_name": "Updated Test User"},
                               name="Update user profile")
        
        # Test password change (will fail if password doesn't match)
        await self.test_endpoint("POST", "/api/users/change-password", 400,
                               data={
                                   "old_password": "wrongpassword",
                                   "new_password": "NewTestPass123!"
                               },
                               name="Change password (wrong old password)")
        
        # ==========================================
        # 4. ORGANIZATION ENDPOINTS (Admin Only)
        # ==========================================
        print("\n📌 ORGANIZATION ENDPOINTS")
        print("-" * 40)
        
        # Get organizations
        org_result = await self.test_endpoint("GET", "/api/organizations/", 200,
                                            name="Get all organizations (admin)")
        
        # Create organization (admin)
        org_data = {
            "name": f"Test Org {random.randint(1000, 9999)}",
            "industry": "Technology",
            "sector": "Software"
        }
        org_result = await self.test_endpoint("POST", "/api/organizations/", 201,
                                            data=org_data,
                                            headers=self.admin_headers,
                                            name="Create organization")
        
        # Store organization ID for later tests
        if org_result.get("success") and org_result.get("data"):
            self.test_data["org_id"] = org_result["data"].get("id")
            print(f"  📝 Created org ID: {self.test_data['org_id']}")
        
        # Get organization details
        if self.test_data.get("org_id"):
            await self.test_endpoint("GET", f"/api/organizations/{self.test_data['org_id']}", 200,
                                   name="Get organization details")
            
            # Update organization
            await self.test_endpoint("PUT", f"/api/organizations/{self.test_data['org_id']}", 200,
                                   data={"name": "Updated Test Org", "industry": "Finance"},
                                   headers=self.admin_headers,
                                   name="Update organization")
            
            # Get organization stats
            await self.test_endpoint("GET", f"/api/organizations/{self.test_data['org_id']}/stats", 200,
                                   name="Get organization stats")
        
        # ==========================================
        # 5. ORGANIZATION METADATA ENDPOINTS
        # ==========================================
        print("\n📌 ORGANIZATION METADATA ENDPOINTS")
        print("-" * 40)
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            
            # Financial metadata
            financial_data = {
                "annual_revenue": 1000000,
                "ebitda": 200000,
                "total_assets": 5000000
            }
            await self.test_endpoint("PUT", f"/api/organizations/{org_id}/metadata/financials", 200,
                                   data=financial_data,
                                   name="Update financial metadata")
            
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata/financials", 200,
                                   name="Get financial metadata")
            
            # Employee metadata
            employee_data = {
                "total_employees": 50,
                "full_time_employees": 40,
                "part_time_employees": 10
            }
            await self.test_endpoint("PUT", f"/api/organizations/{org_id}/metadata/employees", 200,
                                   data=employee_data,
                                   name="Update employee metadata")
            
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata/employees", 200,
                                   name="Get employee metadata")
            
            # Sustainability metadata
            sustain_data = {
                "renewable_energy_percentage": 75.5,
                "carbon_offset_percentage": 50.0,
                "energy_intensity": 0.5
            }
            await self.test_endpoint("PUT", f"/api/organizations/{org_id}/metadata/sustainability", 200,
                                   data=sustain_data,
                                   name="Update sustainability metadata")
            
            # Contact metadata
            contact_data = {
                "primary_contact_name": "John Doe",
                "primary_contact_email": "john@test.com",
                "primary_contact_phone": "+1234567890"
            }
            await self.test_endpoint("PUT", f"/api/organizations/{org_id}/metadata/contacts", 200,
                                   data=contact_data,
                                   name="Update contact metadata")
            
            # Industry metadata
            industry_data = {
                "industry_sector": "Technology",
                "naics_code": "541511",
                "sic_code": "7371"
            }
            await self.test_endpoint("PUT", f"/api/organizations/{org_id}/metadata/industry", 200,
                                   data=industry_data,
                                   name="Update industry metadata")
            
            # Get all metadata
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/metadata/all", 200,
                                   name="Get all metadata")
            
            # Validate metadata
            await self.test_endpoint("POST", f"/api/organizations/{org_id}/metadata/validate", 200,
                                   name="Validate metadata")
        
        # ==========================================
        # 6. ORGANIZATION MEMBERS ENDPOINTS
        # ==========================================
        print("\n📌 ORGANIZATION MEMBERS ENDPOINTS")
        print("-" * 40)
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            
            # Get members
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/members", 200,
                                   name="Get members")
            
            # Get member stats
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/members/stats", 200,
                                   name="Get member stats")
            
            # Get roles
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/members/roles", 200,
                                   name="Get member roles")
        
        # ==========================================
        # 7. ASSETS AND FACILITIES ENDPOINTS
        # ==========================================
        print("\n📌 ASSETS AND FACILITIES ENDPOINTS")
        print("-" * 40)
        
        if self.test_data.get("org_id"):
            org_id = self.test_data["org_id"]
            
            # Create facility
            facility_data = {
                "name": f"Test Facility {random.randint(1000, 9999)}",
                "type": "Office",
                "postcode": "12345",
                "city": "Test City"
            }
            facility_result = await self.test_endpoint("POST", f"/api/organizations/{org_id}/facilities", 201,
                                                     data=facility_data,
                                                     name="Create facility")
            
            if facility_result.get("success") and facility_result.get("data"):
                self.test_data["facility_id"] = facility_result["data"].get("id")
                print(f"  📝 Created facility ID: {self.test_data['facility_id']}")
            
            # Get facilities
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/facilities", 200,
                                   name="Get facilities")
            
            # Get facility stats
            await self.test_endpoint("GET", f"/api/organizations/{org_id}/facilities/stats", 200,
                                   name="Get facility stats")
            
            if self.test_data.get("facility_id"):
                facility_id = self.test_data["facility_id"]
                
                # Update facility
                await self.test_endpoint("PUT", f"/api/organizations/{org_id}/facilities/{facility_id}", 200,
                                       data={"name": "Updated Facility", "city": "Updated City"},
                                       name="Update facility")
                
                # Update facility status
                await self.test_endpoint("POST", f"/api/organizations/{org_id}/facilities/{facility_id}/status", 200,
                                       data={"is_active": False},
                                       name="Deactivate facility")
                
                # Create asset
                asset_data = {
                    "name": f"Test Asset {random.randint(1000, 9999)}",
                    "facility_id": facility_id,
                    "type": "Equipment",
                    "capacity": 100.0,
                    "capacity_unit": "kW"
                }
                asset_result = await self.test_endpoint("POST", f"/api/organizations/{org_id}/assets", 201,
                                                      data=asset_data,
                                                      name="Create asset")
                
                if asset_result.get("success") and asset_result.get("data"):
                    self.test_data["asset_id"] = asset_result["data"].get("id")
                    print(f"  📝 Created asset ID: {self.test_data['asset_id']}")
                
                # Get assets
                await self.test_endpoint("GET", f"/api/organizations/{org_id}/assets", 200,
                                       name="Get assets")
                
                # Get asset stats
                await self.test_endpoint("GET", f"/api/organizations/{org_id}/assets/stats", 200,
                                       name="Get asset stats")
                
                if self.test_data.get("asset_id"):
                    asset_id = self.test_data["asset_id"]
                    
                    # Update asset
                    await self.test_endpoint("PUT", f"/api/organizations/{org_id}/assets/{asset_id}", 200,
                                           data={"name": "Updated Asset", "capacity": 150.0},
                                           name="Update asset")
        
        # ==========================================
        # 8. EMISSIONS ENDPOINTS
        # ==========================================
        print("\n📌 EMISSIONS ENDPOINTS")
        print("-" * 40)
        
        # Create emission record
        emission_data = {
            "organization_id": self.test_data.get("org_id"),
            "asset_id": self.test_data.get("asset_id"),
            "start_date": "2024-01-01",
            "end_date": "2024-01-31",
            "raw_quantity": 1000.0,
            "calculated_kg_co2e": 250.5
        }
        
        emission_result = await self.test_endpoint("POST", "/api/emissions", 201,
                                                  data=emission_data,
                                                  name="Create emission record")
        
        if emission_result.get("success") and emission_result.get("data"):
            self.test_data["emission_id"] = emission_result["data"].get("id")
            print(f"  📝 Created emission ID: {self.test_data['emission_id']}")
        
        # Get emissions
        await self.test_endpoint("GET", "/api/emissions", 200,
                               name="Get emissions")
        
        # Get emission stats
        await self.test_endpoint("GET", "/api/emissions/stats", 200,
                               name="Get emission stats")
        
        if self.test_data.get("emission_id"):
            emission_id = self.test_data["emission_id"]
            
            # Update emission
            await self.test_endpoint("PUT", f"/api/emissions/{emission_id}", 200,
                                   data={"calculated_kg_co2e": 300.0},
                                   name="Update emission record")
            
            # Delete emission
            await self.test_endpoint("DELETE", f"/api/emissions/{emission_id}", 200,
                                   name="Delete emission record")
        
        # ==========================================
        # 9. DOCUMENTS AND UPLOAD ENDPOINTS
        # ==========================================
        print("\n📌 DOCUMENTS AND UPLOAD ENDPOINTS")
        print("-" * 40)
        
        # Get documents
        await self.test_endpoint("GET", "/api/documents", 200,
                               name="Get documents")
        
        # Get document stats
        await self.test_endpoint("GET", "/api/documents/stats", 200,
                               name="Get document stats")
        
        # Upload test (will need actual file)
        await self.test_endpoint("POST", "/api/upload/test-upload", 200,
                               name="Test upload (no file)")
        
        # ==========================================
        # 10. GLOSSARY ENDPOINTS
        # ==========================================
        print("\n📌 GLOSSARY ENDPOINTS")
        print("-" * 40)
        
        # Create glossary term
        glossary_data = {
            "term": f"Test Term {random.randint(1000, 9999)}",
            "definition": "This is a test definition",
            "category": "Test"
        }
        glossary_result = await self.test_endpoint("POST", "/api/glossary", 201,
                                                 data=glossary_data,
                                                 name="Create glossary term")
        
        if glossary_result.get("success") and glossary_result.get("data"):
            self.test_data["glossary_id"] = glossary_result["data"].get("id")
        
        # Get glossary
        await self.test_endpoint("GET", "/api/glossary", 200,
                               name="Get glossary")
        
        # Get glossary categories
        await self.test_endpoint("GET", "/api/glossary/categories", 200,
                               name="Get glossary categories")
        
        # Search glossary
        await self.test_endpoint("GET", "/api/glossary/search?q=Test", 200,
                               name="Search glossary")
        
        if self.test_data.get("glossary_id"):
            glossary_id = self.test_data["glossary_id"]
            
            # Get single term
            await self.test_endpoint("GET", f"/api/glossary/{glossary_id}", 200,
                                   name="Get glossary term")
            
            # Update term
            await self.test_endpoint("PUT", f"/api/glossary/{glossary_id}", 200,
                                   data={"definition": "Updated definition"},
                                   name="Update glossary term")
            
            # Delete term
            await self.test_endpoint("DELETE", f"/api/glossary/{glossary_id}", 200,
                                   name="Delete glossary term")
        
        # ==========================================
        # 11. NOTIFICATIONS ENDPOINTS
        # ==========================================
        print("\n📌 NOTIFICATIONS ENDPOINTS")
        print("-" * 40)
        
        # Get notification templates
        await self.test_endpoint("GET", "/api/notifications/templates", 200,
                               name="Get notification templates")
        
        # ==========================================
        # 12. FEEDBACK ENDPOINTS
        # ==========================================
        print("\n📌 FEEDBACK ENDPOINTS")
        print("-" * 40)
        
        # Submit feedback
        feedback_data = {
            "type": "suggestion",
            "title": "Test Feedback",
            "description": "This is a test feedback",
            "severity": "medium",
            "rating": 4
        }
        await self.test_endpoint("POST", "/api/feedback", 201,
                               data=feedback_data,
                               name="Submit feedback")
        
        # Get user feedback
        await self.test_endpoint("GET", "/api/feedback", 200,
                               name="Get user feedback")
        
        # ==========================================
        # 13. ADMIN ENDPOINTS (Admin Only)
        # ==========================================
        print("\n📌 ADMIN ENDPOINTS")
        print("-" * 40)
        
        # Get staff list
        await self.test_endpoint("GET", "/api/admin/staff", 200,
                               headers=self.admin_headers,
                               name="Get staff list")
        
        # Get staff performance
        await self.test_endpoint("GET", "/api/admin/staff/performance", 200,
                               headers=self.admin_headers,
                               name="Get staff performance")
        
        # Get staff activity
        await self.test_endpoint("GET", "/api/admin/staff/activity", 200,
                               headers=self.admin_headers,
                               name="Get staff activity")
        
        # Get workload
        await self.test_endpoint("GET", "/api/admin/staff/workload", 200,
                               headers=self.admin_headers,
                               name="Get staff workload")
        
        # Get queue settings
        await self.test_endpoint("GET", "/api/admin/queue/settings", 200,
                               headers=self.admin_headers,
                               name="Get queue settings")
        
        # Get queue stats
        await self.test_endpoint("GET", "/api/admin/queue/stats", 200,
                               headers=self.admin_headers,
                               name="Get queue stats")
        
        # Get priority queue
        await self.test_endpoint("GET", "/api/admin/reviews/queue/priority", 200,
                               headers=self.admin_headers,
                               name="Get priority queue")
        
        # Get detailed queue stats
        await self.test_endpoint("GET", "/api/admin/reviews/queue/stats/detailed", 200,
                               headers=self.admin_headers,
                               name="Get detailed queue stats")
        
        # Get SLA monitor
        await self.test_endpoint("GET", "/api/admin/reviews/queue/sla-monitor", 200,
                               headers=self.admin_headers,
                               name="Get SLA monitor")
        
        # Get beta codes
        await self.test_endpoint("GET", "/api/admin/beta/codes", 200,
                               headers=self.admin_headers,
                               name="Get beta codes")
        
        # Get beta users
        await self.test_endpoint("GET", "/api/admin/beta/users", 200,
                               headers=self.admin_headers,
                               name="Get beta users")
        
        # Get beta stats
        await self.test_endpoint("GET", "/api/admin/beta/users/stats", 200,
                               headers=self.admin_headers,
                               name="Get beta stats")
        
        # Get audit logs
        await self.test_endpoint("GET", "/api/admin/audit/activity", 200,
                               headers=self.admin_headers,
                               name="Get audit logs")
        
        # Get email logs
        await self.test_endpoint("GET", "/api/admin/logs/email", 200,
                               headers=self.admin_headers,
                               name="Get email logs")
        
        # Get email stats
        await self.test_endpoint("GET", "/api/admin/logs/email/stats", 200,
                               headers=self.admin_headers,
                               name="Get email stats")
        
        # Get processing logs
        await self.test_endpoint("GET", "/api/admin/logs/processing", 200,
                               headers=self.admin_headers,
                               name="Get processing logs")
        
        # Get processing stats
        await self.test_endpoint("GET", "/api/admin/logs/processing/stats", 200,
                               headers=self.admin_headers,
                               name="Get processing stats")
        
        # Get system health
        await self.test_endpoint("GET", "/api/admin/analytics/system/health", 200,
                               headers=self.admin_headers,
                               name="Get system health")
        
        # Get system performance
        await self.test_endpoint("GET", "/api/admin/analytics/system/performance", 200,
                               headers=self.admin_headers,
                               name="Get system performance")
        
        # Get email templates
        await self.test_endpoint("GET", "/api/admin/email/templates", 200,
                               headers=self.admin_headers,
                               name="Get email templates")
        
        # Get settings history
        await self.test_endpoint("GET", "/api/admin/settings/history", 200,
                               headers=self.admin_headers,
                               name="Get settings history")
        
        # Validate settings
        await self.test_endpoint("POST", "/api/admin/settings/validate", 200,
                               data={"max_file_size_mb": 50},
                               headers=self.admin_headers,
                               name="Validate settings")
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        total = self.results["total"]
        passed = self.results["passed"]
        failed = self.results["failed"]
        skipped = self.results["skipped"]
        
        print(f"\n📈 Results:")
        print(f"  ✅ Passed: {passed}/{total} ({passed/total*100:.1f}%)" if total > 0 else "  ✅ Passed: 0")
        print(f"  ❌ Failed: {failed}/{total} ({failed/total*100:.1f}%)" if total > 0 else "  ❌ Failed: 0")
        print(f"  ⏭️  Skipped: {skipped}")
        
        if failed > 0:
            print("\n❌ Failed Tests:")
            for detail in self.results["details"]:
                if "FAILED" in detail.get("status", ""):
                    print(f"  - {detail.get('name', 'Unknown')}")
                    if detail.get("response"):
                        print(f"    Response: {detail['response'][:200]}")
        
        # Export results to file
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n📝 Detailed results saved to test_results.json")
        
        return total, passed, failed

async def main():
    """Run all tests"""
    # Load test configuration
    base_url = TestConfig.API_BASE_URL
    admin_email = TestConfig.TEST_ADMIN_EMAIL
    admin_password = TestConfig.TEST_ADMIN_PASSWORD
    user_email = TestConfig.TEST_USER_EMAIL
    user_password = TestConfig.TEST_USER_PASSWORD
    
    print(f"🔍 Testing API at: {base_url}")
    
    # Create test users
    auth_helper = AuthHelper(base_url)
    
    # Login as admin
    print("\n🔑 Authenticating...")
    admin_success = await auth_helper.login(admin_email, admin_password)
    if not admin_success:
        print("❌ Admin authentication failed! Please check credentials.")
        return
    
    admin_token = auth_helper.access_token
    print(f"✅ Admin authenticated: {admin_email}")
    
    # Login as user
    user_success = await auth_helper.login(user_email, user_password)
    if not user_success:
        print("⚠️  User authentication failed! Continuing with admin token only.")
        user_token = admin_token
    else:
        user_token = auth_helper.access_token
        print(f"✅ User authenticated: {user_email}")
    
    # Run tests
    async with APITester(base_url) as tester:
        await tester.test_all_endpoints(admin_token, user_token)
        tester.print_summary()

if __name__ == "__main__":
    asyncio.run(main())