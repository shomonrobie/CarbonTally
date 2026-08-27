# backend/tests/test_auth_simple.py
"""
Simple authentication test script
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_auth():
    base_url = os.getenv("TEST_API_URL", "http://localhost:8000")
    
    async with httpx.AsyncClient() as client:
        # 1. Login
        print("🔑 Testing login...")
        response = await client.post(
            f"{base_url}/api/auth/login",
            json={
                "email": "test@example.com",
                "password": "TestPassword123!"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login successful! Token: {token[:20]}...")
        else:
            print(f"❌ Login failed: {response.status_code}")
            print(f"Response: {response.text}")
            return
        
        # 2. Test protected endpoint
        print("\n🔒 Testing protected endpoint...")
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        response = await client.get(
            f"{base_url}/api/users/profile",
            headers=headers
        )
        
        if response.status_code == 200:
            print("✅ Protected endpoint accessible!")
            print(f"Profile: {response.json()}")
        else:
            print(f"❌ Protected endpoint failed: {response.status_code}")
            print(f"Response: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_auth())