# backend/main.py
import os
from dotenv import load_dotenv
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from fastapi.responses import JSONResponse

# Load environment
load_dotenv()

# Import config and database
from config import Config
from database import get_supabase_client

# ==========================================
# V3 (v2.1) API — single composition root
# Mounted alongside the legacy surface during the transition.
# If the V3 layer cannot import (e.g. a missing dependency), the legacy
# app still starts and logs a clear warning.
# ==========================================
try:
    from api.router import (
        router as api_router,
        carbon_tally_error_handler,
    )
    from core.exceptions import CarbonTallyError
    V3_API_AVAILABLE = True
except Exception as _v3_import_error:  # pragma: no cover - defensive fallback
    V3_API_AVAILABLE = False
    api_router = None
    carbon_tally_error_handler = None
    CarbonTallyError = Exception
    print(f"⚠️ V3 (v2.1) API unavailable (legacy app only): {_v3_import_error!r}")

# ==========================================
# IMPORT ALL ROUTERS
# ==========================================
# Public/General routes
from routes import (
    waitlist,
    upload,
    reports,
    glossary,
    users,
    notifications,
    documents_main,      # ✅ Direct import
    document_activity,   # ✅ Direct import
    drafts,
    reference,
    logs,
    emissions,
    feedback,
    drafts_enhanced,
    customer_documents,
)

# Admin routes
from routes.admin import (
    staff,
    defra,
    extraction,
    reviews,
    assignments,
    permissions,
    workload,
    beta,
    audit,
    review_history,    
    admin_bulk,
    email_templates,
    admin_analytics,
    settings,
)

# Admin logs (renamed to avoid conflict)
from routes.admin import logs as admin_logs

# Organization routes
from routes.organizations import (
    management,
    members,
    assets,
    data,
    analytics,
    dashboard,
    files,
    team,
    metadata,
    exports,
    bulk as org_bulk,
)



# ==========================================
# FASTAPI APP INITIALIZATION
# ==========================================

app = FastAPI(
    title=Config.APP_NAME,
    version=Config.APP_VERSION,
    description="CarbonTally API for carbon emissions tracking and reporting",
    docs_url="/docs",
    redoc_url="/redoc",
    redirect_slashes=False,  # ✅ Prevents 307 redirects
    openapi_tags=[
        # Health & System
        {"name": "Health", "description": "Health check and system status endpoints"},
        {"name": "System", "description": "System health, performance, and usage metrics"},
        
        # Public/General
        {"name": "Waitlist", "description": "Public waitlist management"},
        {"name": "Upload", "description": "File upload and processing endpoints"},
        {"name": "Reports", "description": "Report generation (SECR, CSRD, ISSB)"},
        {"name": "Glossary", "description": "Glossary management"},
        {"name": "User Management", "description": "User profile and authentication"},
        {"name": "Notifications", "description": "Email notifications"},
        {"name": "Feedback", "description": "User feedback collection and management"},
        
        # Admin
        {"name": "Admin - Staff Management", "description": "Staff member management (admin only)"},
        {"name": "Admin - Staff Performance", "description": "Staff performance metrics and activity tracking"},
        {"name": "Admin - DEFRA Factor Management", "description": "DEFRA factor management (admin only)"},
        {"name": "Admin - Extraction Management", "description": "Extraction approval and review"},
        {"name": "Admin - Reviews & Assignments", "description": "Review queue and assignment management"},
        {"name": "Admin - Workload", "description": "Staff workload and queue settings"},
        {"name": "Admin - Permissions", "description": "Role and permission management"},
        {"name": "Admin - Beta Management", "description": "Beta access code and user management"},
        {"name": "Admin - Audit", "description": "System audit and activity logs"},
        {"name": "Admin - Review History", "description": "Review assignment history and audit trail"},
        {"name": "Admin - Logs", "description": "Email and processing logs"},
        {"name": "Admin - Bulk Operations", "description": "Bulk operations for organizations and documents"},
        {"name": "Admin - Email Templates", "description": "Email template management"},
        {"name": "Admin - Analytics", "description": "System analytics and health metrics"},
        {"name": "Admin - Settings", "description": "System settings management"},
        
        # Organization
        {"name": "Organization Management", "description": "Organization CRUD operations"},
        {"name": "Organization Metadata", "description": "Organization metadata management"},
        {"name": "Organization Members", "description": "Organization member management"},
        {"name": "Organization Team", "description": "Team member management"},
        {"name": "Organization Assets", "description": "Facility and asset management"},
        {"name": "Organization Data", "description": "Emissions data management"},
        {"name": "Organization Analytics", "description": "Analytics and insights"},
        {"name": "Organization Dashboard", "description": "Dashboard summaries"},
        {"name": "Organization Files", "description": "File management"},
        {"name": "Organization Exports", "description": "Data export management"},
        {"name": "Organization Bulk Operations", "description": "Bulk operations for members and assets"},
        
        # Documents
        {"name": "Documents", "description": "Document management"},
        {"name": "Documents - Activity", "description": "Document activity and customer reviews"},
        {"name": "Customer Documents", "description": "Customer document management with asset linking and verification"},  # ✅ NEW

        # Drafts
        {"name": "Drafts", "description": "Draft management"},
        {"name": "Drafts - Enhanced", "description": "Enhanced draft management with sections"},
        
        # Other
        {"name": "Emissions", "description": "Emissions data management"},
        {"name": "Reference Data", "description": "Reference data (units, fuel types, etc.)"},
        {"name": "Logs", "description": "System logs and activity"},
        {"name": "Customer Reviews", "description": "Customer document review and verification"},  # ✅ NEW

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
        "X-Client-Version",
        "X-Client-Platform",
    ],
    expose_headers=[
        "Content-Disposition",
        "X-Total-Count",
        "X-RateLimit-Limit",
        "X-RateLimit-Remaining",
        "X-RateLimit-Reset",
    ],
    max_age=600,
)

# ==========================================
# INCLUDE ALL ROUTERS
# ==========================================

# ==========================================
# INCLUDE ALL ROUTERS
# ==========================================

# Public/General routes
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
app.include_router(documents_main.router)   # ✅ Direct
app.include_router(document_activity.router) # ✅ Direct
app.include_router(reference.router)
app.include_router(drafts.router)
app.include_router(logs.router)
app.include_router(emissions.router)
app.include_router(feedback.router)
app.include_router(drafts_enhanced.router)
app.include_router(customer_documents.router)

# Admin routes
app.include_router(staff.router)
app.include_router(defra.router)
app.include_router(extraction.router)
app.include_router(reviews.router)
app.include_router(assignments.router)
app.include_router(permissions.router)
app.include_router(workload.router)
app.include_router(beta.router)
app.include_router(audit.router)
app.include_router(review_history.router)
app.include_router(admin_logs.router)
app.include_router(admin_bulk.router)
app.include_router(email_templates.router)
app.include_router(admin_analytics.router)
app.include_router(settings.router)

# Organization routes
app.include_router(management.router)
app.include_router(members.router)
app.include_router(assets.router)
app.include_router(data.router)
app.include_router(analytics.router)
app.include_router(dashboard.router)
app.include_router(files.router)
app.include_router(team.router)
app.include_router(metadata.router)
app.include_router(exports.router)
app.include_router(org_bulk.router)

# ==========================================
# V3 (v2.1) API — mounted on the single composition root
# ==========================================
if V3_API_AVAILABLE:
    app.include_router(api_router)
    app.add_exception_handler(CarbonTallyError, carbon_tally_error_handler)

# ==========================================
# ROOT ENDPOINTS
# ==========================================

@app.on_event("startup")
async def startup_event():
    print("🚀 Starting CarbonTally API...")
    print(f"📋 CORS Allowed Origins: {Config.ALLOWED_ORIGINS}")
    print(f"🔧 CORS Allow Credentials: {Config.CORS_ALLOW_CREDENTIALS}")
    print(f"📊 Total routes registered: {len(app.routes)}")

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint. Returns basic service information."""
    return {
        "message": Config.APP_NAME,
        "version": Config.APP_VERSION,
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "documentation": "/docs",
        "api_version": "v3",
        "routes_count": len(app.routes)
    }

@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint. Verifies database connectivity."""
    try:
        supabase = get_supabase_client()
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
                "version": Config.APP_VERSION,
                "routes": len(app.routes)
            }
        }
    }

# ==========================================
# ERROR HANDLERS
# ==========================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler for consistent error responses."""
    return JSONResponse(
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
    """Generic exception handler for unhandled errors."""
    print(f"❌ Unhandled exception: {exc}")
    import traceback
    traceback.print_exc()
    
    return JSONResponse(
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
    """Clean up on application shutdown."""
    print("🛑 Shutting down CarbonTally API...")
    try:
        from infra.supabase import close_service_pool
        close_service_pool()
    except Exception:
        pass

# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    import uvicorn
    
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