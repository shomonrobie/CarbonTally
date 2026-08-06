# backend/tests/config.py
"""
Test configuration for CarbonTally API
"""

import os
from dotenv import load_dotenv

load_dotenv()

class TestConfig:
    # API Configuration
    API_BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
    API_VERSION = "v3"
    
    # Test Users
    TEST_USER_EMAIL = os.getenv("TEST_USER_EMAIL", "shomenrobie@gmail.com")
    TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "Robie@1974")
    TEST_ADMIN_EMAIL = os.getenv("TEST_ADMIN_EMAIL", "shomonrobie@gmail.com")
    TEST_ADMIN_PASSWORD = os.getenv("TEST_ADMIN_PASSWORD", "Robie@1974")
    
    # Test Organization
    TEST_ORG_ID = os.getenv("2b7a2e09-2cc3-461e-84e6-81137eb63ab3", "Babui Limited")
    
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")