# backend/database.py
"""
Database module for Supabase client management.
Provides a singleton pattern for the Supabase client.
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# ==========================================
# SINGLETON CLIENT
# ==========================================

_supabase_client = None

def get_supabase_client() -> Client:
    """
    Get or create Supabase client instance.
    Uses singleton pattern to avoid multiple connections.
    
    Returns:
        Client: Supabase client instance
    
    Raises:
        Exception: If Supabase credentials are missing or connection fails
    """
    global _supabase_client
    
    if _supabase_client is None:
        if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
            print("❌ ERROR: Missing Supabase credentials!")
            print("   Please check your .env file has:")
            print("   SUPABASE_URL=your_supabase_url")
            print("   SUPABASE_SERVICE_KEY=your_service_key")
            raise Exception("Supabase credentials missing")
        
        try:
            print("🔌 Initializing Supabase client...")
            
            # Clean the key - remove any whitespace
            supabase_key = SUPABASE_SERVICE_KEY.strip()
            supabase_url = SUPABASE_URL.strip()
            
            # Create client
            _supabase_client = create_client(supabase_url, supabase_key)
            
            # Test connection
            test = _supabase_client.table("glossary").select("count", count="exact").limit(1).execute()
            print("✅ Supabase client initialized successfully")
            
        except Exception as e:
            print(f"❌ Supabase initialization error: {e}")
            import traceback
            traceback.print_exc()
            _supabase_client = None
            raise Exception(f"Failed to initialize Supabase client: {str(e)}")
    
    return _supabase_client

def reset_supabase_client():
    """
    Reset the Supabase client instance.
    Useful for testing or when configuration changes.
    """
    global _supabase_client
    _supabase_client = None
    print("🔄 Supabase client reset")

def is_supabase_connected() -> bool:
    """
    Check if Supabase is connected and working.
    
    Returns:
        bool: True if connected, False otherwise
    """
    try:
        client = get_supabase_client()
        test = client.table("glossary").select("count", count="exact").limit(1).execute()
        return True
    except Exception:
        return False

def get_supabase_health() -> dict:
    """
    Get detailed health information about Supabase connection.
    
    Returns:
        dict: Health status with details
    """
    try:
        client = get_supabase_client()
        start_time = datetime.now()
        
        # Test multiple tables
        test1 = client.table("glossary").select("count", count="exact").limit(1).execute()
        test2 = client.table("organizations").select("count", count="exact").limit(1).execute()
        
        response_time = (datetime.now() - start_time).total_seconds() * 1000  # milliseconds
        
        return {
            "status": "connected",
            "response_time_ms": round(response_time, 2),
            "tables_accessible": {
                "glossary": test1.data is not None,
                "organizations": test2.data is not None
            },
            "url": SUPABASE_URL,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


def get_supabase_admin() -> Client:
    """Get Supabase client with service role key (admin)."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# ==========================================
# CLEANUP
# ==========================================

def close_supabase_client():
    """
    Close the Supabase client connection.
    """
    global _supabase_client
    if _supabase_client:
        try:
            # Supabase client doesn't have a close method,
            # but we can clear the reference
            _supabase_client = None
            print("🔌 Supabase client closed")
        except Exception as e:
            print(f"⚠️ Error closing Supabase client: {e}")

# ==========================================
# IMPORT FOR HEALTH CHECK
# ==========================================

from datetime import datetime

# Optional: Auto-close on script exit
import atexit
atexit.register(close_supabase_client)