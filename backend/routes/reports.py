# backend/routes/reports.py 
"""
Report generation routes.
This file is a thin wrapper that imports the actual report generator.
All business logic is in report_generator.py.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from datetime import datetime
import io
import pandas as pd
import traceback

from auth import AuthUser, require_org_member, require_role
from database import get_supabase_client

# ==========================================
# IMPORT FROM REPORT GENERATOR
# ==========================================

# Import the router and classes from report_generator.py
from report_generator import (
    router as report_generator_router,
    EnhancedSustainabilityReportGenerator,  # ✅ This exists    
    EnhancedReportRequest,  # ✅ This exists
)


# ==========================================
# ROUTER SETUP
# ==========================================

# Use the router from report_generator
router = report_generator_router

# ==========================================
# ADDITIONAL ENDPOINTS (Not in report_generator)
# ==========================================

@router.get("/report-status")
async def report_service_status():
    """
    Check if report generation service is available.
    """
    return {
        "status": "operational",
        "service": "CarbonTally Report Generator",
        "version": "2.0",
        "available_reports": ["SECR", "CSRD", "ISSB", "AUDITOR_EXCEL"],
        "available_enhanced_reports": ["SECR"],
        "supported_formats": ["PDF", "Excel"],
        "timestamp": datetime.now().isoformat()
    }

# ==========================================
# DEFRA MAPPING ENDPOINTS (Moved here from main.py)
# ==========================================

@router.get("/api/defra-mapping")
async def get_defra_mapping(
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get the current activity type mapping for DEFRA factors.
    Useful for debugging and frontend display.
    """
    mapping = {
        # Fuel types
        'Diesel': 'Diesel (DERV)',
        'Petrol': 'Petrol (Unleaded)',
        'AdBlue': 'AdBlue',
        'LPG': 'LPG',
        'CNG': 'CNG',
        
        # Utility types
        'Electricity': 'UK Electricity Grid',
        'Natural Gas': 'Natural Gas',
        'Steam': 'Steam',
        'Chilled Water': 'Chilled Water',
        
        # Scope 3 types
        'Flight (Short Haul)': 'Flight (Short Haul)',
        'Flight (Long Haul)': 'Flight (Long Haul)',
        'Rail (National)': 'Rail (National)',
        'Hotel Stay': 'Hotel Stay',
        'Mixed Waste': 'Mixed Waste',
        'Recycled Waste': 'Recycled Waste',
        'Taxi': 'Taxi',
        'Bus': 'Bus',
        'Freight': 'Freight',
    }
    
    return {
        "status": "success",
        "mapping": mapping
    }

@router.get("/api/defra-factors/{reporting_year}")
async def get_defra_factors_by_year(
    reporting_year: int,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Get all DEFRA factors for a specific reporting year.
    """
    try:
        supabase = get_supabase_client()
        
        result = supabase.from_('defra_conversion_factors') \
            .select('*') \
            .eq('reporting_year', reporting_year) \
            .order('activity_type') \
            .execute()
        
        return {
            "status": "success",
            "reporting_year": reporting_year,
            "factors": result.data,
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        print(f"❌ Error fetching DEFRA factors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==========================================
# ADMIN DEFRA IMPORT ENDPOINT
# ==========================================

@router.post("/admin/import-defra-factors")
async def import_defra_factors(
    file: UploadFile = File(...),
    reporting_year: int = Form(...),
    current_user: AuthUser = Depends(require_role(["admin"]))
):
    """
    Admin endpoint to upload a cleaned DEFRA CSV and upsert factors for a specific year.
    Admin only endpoint.
    """
    try:
        supabase = get_supabase_client()

        # Read the uploaded CSV
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # Basic cleaning
        required_cols = ['activity_type', 'co2e_multiplier']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=400, 
                detail=f"CSV must contain columns: {required_cols}"
            )
            
        df = df.dropna(subset=required_cols)
        df['reporting_year'] = reporting_year
        df['co2e_multiplier'] = df['co2e_multiplier'].astype(float)
        df['activity_type'] = df['activity_type'].str.strip()
        
        # Convert to list of dicts for Supabase
        records = df[['reporting_year', 'activity_type', 'co2e_multiplier']].to_dict('records')
        
        # Upsert into Supabase
        result = supabase.from_('defra_conversion_factors').upsert(
            records, 
            on_conflict='reporting_year,activity_type'
        ).execute()
        
        return {
            "status": "success", 
            "message": f"Successfully imported/updated {len(records)} DEFRA factors for {reporting_year}",
            "records_imported": len(records)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"--- DEFRA IMPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

# ==========================================
# DIRECT REPORT GENERATION ENDPOINTS
# (These call the report generator directly)
# ==========================================

@router.post("/generate-enhanced-report")
async def generate_enhanced_sustainability_report(
    request: EnhancedReportRequest,
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Generate an enhanced sustainability report with narratives and YoY comparison.
    Uses the enhanced report generator from report_generator.py.
    """
    try:
        supabase = get_supabase_client()
        
        generator = EnhancedSustainabilityReportGenerator(
            supabase, 
            request.organization_id, 
            request.reporting_year,
            request.report_type,
            request.include_narratives
        )
        
        if request.report_type == 'SECR':
            result = generator.generate_enhanced_secr_report()
        elif request.report_type == 'CSRD':
            # For CSRD, use enhanced report with CSRD-specific logic
            result = generator.generate_enhanced_secr_report()  # Placeholder for CSRD
        elif request.report_type == 'ISSB':
            # For ISSB, use enhanced report with ISSB-specific logic
            result = generator.generate_enhanced_secr_report()  # Placeholder for ISSB
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported report type: {request.report_type}. Supported: SECR, CSRD, ISSB"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- ENHANCED REPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Enhanced report generation failed: {str(e)}")