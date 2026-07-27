# backend/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from fastapi.responses import JSONResponse  # ✅ Make sure this is imported

# Load environment
load_dotenv()

# Import config and database
from config import Config
from database import get_supabase_client

# Import all routers
from routes import (
    waitlist,
    upload,
    reports,
    glossary,
    users,
    notifications,
)
from routes.admin import staff, defra, extraction
from routes.organizations import (
    management,
    members,
    assets,
    data,
    analytics,
    dashboard,
    files,
)
from routes.organizations import team
from routes import documents
from routes import reference, drafts
from routes.admin import reviews
from routes.admin import assignments

# ==========================================
# FASTAPI APP INITIALIZATION
# ==========================================

app = FastAPI(
    title=Config.APP_NAME,
    version=Config.APP_VERSION,
    description="CarbonTally API for carbon emissions tracking and reporting",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "Waitlist",
            "description": "Public waitlist management"
        },
        {
            "name": "Upload",
            "description": "File upload and processing endpoints"
        },
        {
            "name": "Reports",
            "description": "Report generation (SECR, CSRD, ISSB)"
        },
        {
            "name": "Glossary",
            "description": "Glossary management"
        },
        {
            "name": "User Management",
            "description": "User profile and authentication"
        },
        {
            "name": "Notifications",
            "description": "Email notifications"
        },
        {
            "name": "Admin - Staff Management",
            "description": "Staff member management (admin only)"
        },
        {
            "name": "Admin - DEFRA Factor Management",
            "description": "DEFRA factor management (admin only)"
        },
        {
            "name": "Admin - Extraction Management",
            "description": "Extraction approval and review (admin/data approver)"
        },
        {
            "name": "Organization Management",
            "description": "Organization CRUD operations"
        },
        {
            "name": "Organization Members",
            "description": "Organization member management"
        },
        {
            "name": "Organization Assets",
            "description": "Facility and asset management"
        },
        {
            "name": "Organization Data",
            "description": "Emissions data management"
        },
        {
            "name": "Organization Analytics",
            "description": "Analytics and insights"
        },
        {
            "name": "Organization Dashboard",
            "description": "Dashboard summaries"
        },
        {
            "name": "Organization Files",
            "description": "File management"
        }
    ]
)

# ==========================================
# CORS CONFIGURATION
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "X-Requested-With",
    ],
    expose_headers=["Content-Disposition"],
    max_age=600,  # Cache preflight requests for 10 minutes
)


# ==========================================
# INCLUDE ALL ROUTERS
# ==========================================

# Public/General routes
app.include_router(waitlist.router)
app.include_router(upload.router)
app.include_router(reports.router)
app.include_router(glossary.router)
app.include_router(users.router)
app.include_router(notifications.router)

# Admin routes
app.include_router(staff.router)
app.include_router(defra.router)
app.include_router(extraction.router)

# Organization routes
app.include_router(management.router)
app.include_router(members.router)
app.include_router(assets.router)
app.include_router(data.router)
app.include_router(analytics.router)
app.include_router(dashboard.router)
app.include_router(files.router)
app.include_router(team.router)
app.include_router(documents.router)
app.include_router(reference.router)
app.include_router(drafts.router)
app.include_router(reviews.router)
app.include_router(assignments.router)

# ==========================================
# ROOT ENDPOINTS
# ==========================================
@app.on_event("startup")
async def startup_event():
    print("🚀 Starting CarbonTally API...")
    print(f"📋 CORS Allowed Origins: {Config.ALLOWED_ORIGINS}")
    print(f"🔧 CORS Allow Credentials: {Config.CORS_ALLOW_CREDENTIALS}")

@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint.
    Returns basic service information.
    """
    return {
        "message": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "documentation": "/docs",
        "api_version": "v3"
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Verifies database connectivity and service status.
    """
    try:
        supabase = get_supabase_client()
        # Test connection
        test = supabase.table("glossary").select("count", count="exact").limit(1).execute()
        supabase_connected = True
    except Exception as e:
        print(f"⚠️ Health check error: {e}")
        supabase_connected = False
    
    return {
        "status": "healthy" if supabase_connected else "degraded",
        "service": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "supabase_connected": supabase_connected,
        "components": {
            "database": {
                "status": "connected" if supabase_connected else "disconnected",
                "timestamp": datetime.now().isoformat()
            },
            "api": {
                "status": "running",
                "version": Config.APP_VERSION
            }
        }
    }

@app.get("/test-upload", tags=["Health"])
async def test_upload():
    """
    Test endpoint for file uploads.
    Returns available upload endpoints.
    """
    return {
        "status": "ready",
        "message": "File upload endpoints available",
        "endpoints": [
            {
                "path": "/upload-csv",
                "method": "POST",
                "description": "Upload and process CSV/Excel files"
            },
            {
                "path": "/upload-pdf",
                "method": "POST",
                "description": "Upload and process PDF files"
            },
            {
                "path": "/upload-batch",
                "method": "POST",
                "description": "Batch upload multiple files (premium)"
            },
            {
                "path": "/repair-pdf",
                "method": "POST",
                "description": "Repair corrupted PDF with OCR"
            }
        ],
        "limits": {
            "max_file_size_mb": 50,
            "max_batch_files": 20,
            "max_batch_size_mb": 200
        }
    }

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """
    Custom HTTP exception handler for consistent error responses.
    """
    return JSONResponse(  # ✅ Use JSONResponse, not a dict
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.now().isoformat(),
                "path": request.url.path
            }
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    """
    Generic exception handler for unhandled errors.
    """
    print(f"❌ Unhandled exception: {exc}")
    import traceback
    traceback.print_exc()
    
    return JSONResponse(  # ✅ Use JSONResponse, not a dict
        status_code=500,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": str(exc),
                "timestamp": datetime.now().isoformat(),
                "path": request.url.path
            }
        }
    )


# ==========================================
# SHUTDOWN EVENT
# ==========================================

@app.on_event("shutdown")
async def shutdown_event():
    """
    Clean up on application shutdown.
    """
    print("🛑 Shutting down CarbonTally API...")
    # Add any cleanup logic here (e.g., close database connections)

# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"🚀 Starting CarbonTally API v{Config.APP_VERSION}")
    print(f"📍 Host: {host}:{port}")
    print(f"🔄 Reload: {reload}")
    print(f"📚 API Documentation: http://{host}:{port}/docs")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info",
        access_log=True
    )