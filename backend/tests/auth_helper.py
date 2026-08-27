# backend/tests/auth_helper.py
"""
Authentication helper for testing
"""

import httpx
from typing import Dict, Optional
from datetime import datetime
import json

class AuthHelper:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.access_token = None
        self.refresh_token = None
        self.user_id = None
    
    async def login(self, email: str, password: str) -> bool:
        """Login and get access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/auth/login",
                    json={
                        "email": email,
                        "password": password
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    self.user_id = data.get("user", {}).get("id")
                    return True
                else:
                    print(f"❌ Login failed: {response.status_code} - {response.text}")
                    return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if not self.access_token:
            return {}
        
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
    
    async def refresh_token(self) -> bool:
        """Refresh the access token"""
        if not self.refresh_token:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/api/auth/refresh",
                    json={"refresh_token": self.refresh_token}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    self.access_token = data.get("access_token")
                    self.refresh_token = data.get("refresh_token")
                    return True
                return False
        except Exception:
            return False

class TestUser:
    def __init__(self, email: str, password: str, role: str = "user"):
        self.email = email
        self.password = password
        self.role = role
        self.auth = None
        self.access_token = None
        self.user_id = None
        self.organization_id = None
    
    async def authenticate(self, base_url: str):
        """Authenticate user"""
        self.auth = AuthHelper(base_url)
        success = await self.auth.login(self.email, self.password)
        if success:
            self.access_token = self.auth.access_token
            self.user_id = self.auth.user_id
        return success
    
    def get_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if not self.auth or not self.auth.access_token:
            return {}
        return self.auth.get_headers()

# Create test users
async def create_test_users(base_url: str) -> Dict[str, TestUser]:
    """Create test users for testing"""
    users = {
        "admin": TestUser(
            email=os.getenv("TEST_ADMIN_EMAIL", "admin@test.com"),
            password=os.getenv("TEST_ADMIN_PASSWORD", "AdminPass123!"),
            role="admin"
        ),
        "user": TestUser(
            email=os.getenv("TEST_USER_EMAIL", "user@test.com"),
            password=os.getenv("TEST_USER_PASSWORD", "UserPass123!"),
            role="user"
        ),
        "org_admin": TestUser(
            email=os.getenv("TEST_ORG_ADMIN_EMAIL", "orgadmin@test.com"),
            password=os.getenv("TEST_ORG_ADMIN_PASSWORD", "OrgAdminPass123!"),
            role="org_admin"
        )
    }
    
    # Authenticate all users
    for name, user in users.items():
        success = await user.authenticate(base_url)
        if success:
            print(f"✅ {name} authenticated successfully")
        else:
            print(f"❌ {name} authentication failed")
    
    return users