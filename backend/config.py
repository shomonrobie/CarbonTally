import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
# backend/config.py - Add these attributes

class Config:
    # Supabase Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
    
    # App Configuration
    APP_NAME = "CarbonTally API"
    APP_VERSION = "3.0.0"
    
    # Email Configuration
    RESEND_API_KEY = os.getenv("RESEND_API_KEY")
    FOUNDER_EMAIL = os.getenv("FOUNDER_EMAIL", "shomonrobie@gmail.com")
    
    # CORS Configuration
    ALLOWED_ORIGINS = [
        "http://localhost:3001",
        "http://localhost:3002",
        "https://carbontally.co.uk",
        "https://www.carbontally.co.uk",
        "https://admin.carbontally.co.uk",
        "https://carbontally-frontend.vercel.app",
        "https://carbontally-admin.vercel.app",
        "https://carbontally-api.onrender.com",
        "https://www.carbontally.co.uk",
        "https://*.onrender.com",  # ✅ Allow all onrender subdomains

    ]
    
    # ✅ ADD THESE CORS SETTINGS
    CORS_ALLOW_CREDENTIALS = True
    CORS_ALLOW_METHODS = ["*"]
    CORS_ALLOW_HEADERS = ["*"]
    CORS_EXPOSE_HEADERS = ["Content-Disposition", "Content-Type"]
    CORS_MAX_AGE = 600
    
    @classmethod
    def get_supabase_client(cls):
        """Get Supabase client instance."""
        if not cls.SUPABASE_URL or not cls.SUPABASE_SERVICE_KEY:
            print("❌ Supabase credentials missing")
            return None
        return create_client(cls.SUPABASE_URL, cls.SUPABASE_SERVICE_KEY)