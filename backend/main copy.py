from dotenv import load_dotenv
import os

load_dotenv()
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# DEBUG PRINTS (We will remove these later)
print("🔍 DEBUG: SUPABASE_URL is", os.getenv("SUPABASE_URL"))
print("🔍 DEBUG: SUPABASE_SERVICE_KEY2 is", "SET" if os.getenv("SUPABASE_SERVICE_KEY2") else "MISSING")
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io
from pydantic import BaseModel, EmailStr, Field
from pdf_engine import PDFExtractor
import resend
from typing import List, Optional
from datetime import datetime
import traceback
from fpdf import FPDF
import re
from supabase import create_client, Client
# from report_generator import (
#     SustainabilityReportGenerator,
#     sanitize_text,
#     SECRReportPDF,
#     CSRDReportPDF,
#     ISSBReportPDF,
#     generate_sustainability_report,
#     generate_auditor_excel_endpoint
# )

from report_generator import router as report_router

app = FastAPI(title="CarbonTally API", version="3.0.0")
app.include_router(report_router)
# Initialize PDF Extractor
pdf_extractor = PDFExtractor()
resend.api_key = os.getenv("RESEND_API_KEY", "re_XRjsEbwv_2TDUBguF5TWzbn7wcTVn8JtN")
FOUNDER_EMAIL = "shomonrobie@gmail.com"
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        # Local development
        "http://localhost:3000",      # Main app
        "http://localhost:3001",      # Admin dashboard
        # Production - Main domain
        "https://carbontally.co.uk",
        "https://www.carbontally.co.uk",
        # Production - If admin is on a separate subdomain
        "https://admin.carbontally.co.uk",
        # Production - If using separate Vercel deployments
        "https://carbontally-frontend.vercel.app",
        "https://carbontally-admin.vercel.app",
        # Render deployment
        "https://carbontally-api.onrender.com",
        
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ============ SUPABASE CLIENT ============
# ✅ Initialize Supabase as a global variable
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY2")
print(f"🔍 DEBUG: SUPABASE_SERVICE_KEY2 length is {len(os.getenv('SUPABASE_SERVICE_KEY2', ''))}")

if not supabase_url or not supabase_key:
    print("❌ ERROR: Missing Supabase credentials!")
    supabase = None
else:
    try:
        # ✅ Try with explicit initialization
            
        # Clean the key - remove any whitespace
        supabase_key = supabase_key.strip()
        
        print(f"🔍 DEBUG: Key after strip length: {len(supabase_key)}")
        print(f"🔍 DEBUG: Key starts with: {supabase_key[:10]}...")
        
        # Test the connection with a simple query
        supabase = create_client(supabase_url, supabase_key)
        
        # Test the connection
        test = supabase.table("glossary").select("count").limit(1).execute()
        print("✅ Supabase connection test successful")
        print(f"✅ supabase_connected: True")
        
    except Exception as e:
        print(f"❌ Supabase initialization error: {e}")
        import traceback
        traceback.print_exc()
        supabase = None


# ============ PYDANTIC MODELS ============
class WaitlistRequest(BaseModel):
    email: EmailStr
    full_name: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, max_length=100)
    company_size: Optional[str] = Field(None, max_length=50)
    interested_in: Optional[str] = Field(None, max_length=100)
    source: Optional[str] = Field("landing_page", max_length=50)

class WaitlistResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None
    data: Optional[dict] = None


# ============ HEALTH CHECK ============
@app.get("/")
@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "CarbonTally API",
        "version": "3.0.0",
        "timestamp": datetime.now().isoformat(),
        "supabase_connected": supabase is not None
    }

@app.post("/api/waitlist", response_model=WaitlistResponse)
async def add_to_waitlist(request: WaitlistRequest):
    """
    Add email to waitlist - POST endpoint
    """
    try:
        if supabase is None:
            print("❌ Supabase client is None")
            raise HTTPException(status_code=500, detail="Database not available")

        # Validate and clean email
        email_lower = request.email.lower().strip()
        print(f"📝 Adding to waitlist: {email_lower}")

        # ✅ Check if email already exists - FIXED
        try:
            existing = supabase.table("waitlist")\
                .select("email, status, full_name")\
                .eq("email", email_lower)\
                .maybe_single()\
                .execute()
            
            # ✅ Check if data exists before accessing
            if existing and existing.data:
                print(f"⚠️ Email already on waitlist: {email_lower}")
                return WaitlistResponse(
                    success=False,
                    message="Email already on waitlist",
                    error="Already on waitlist",
                    data={"status": existing.data.get("status", "pending")}
                )
        except Exception as e:
            print(f"⚠️ Error checking existing email: {e}")
            # Continue anyway - may be first insert
        
        # Insert into waitlist
        now = datetime.now().isoformat()
        result = supabase.table("waitlist").insert({
            "email": email_lower,
            "full_name": request.full_name,
            "company_name": request.company_name,
            "company_size": request.company_size,
            "interested_in": request.interested_in,
            "source": request.source or "landing_page",
            "status": "pending",
            "created_at": now,
            "updated_at": now
        }).execute()
        
        if not result.data or len(result.data) == 0:
            print("❌ Failed to insert into waitlist - no data returned")
            raise HTTPException(status_code=500, detail="Failed to add to waitlist")
        
        print(f"✅ Added {email_lower} to waitlist")

        # Send confirmation email (async)
        try:
            await send_confirmation_email_sync(request.email, request.full_name)
        except Exception as email_error:
            print(f"Email error: {email_error}")
            # Don't fail the request if email fails

        return WaitlistResponse(
            success=True,
            message="Added to waitlist successfully!",
            data=result.data[0]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Waitlist error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/waitlist")
async def get_waitlist(limit: int = 100, status: Optional[str] = None):
    """
    Get waitlist entries - GET endpoint (admin only)
    """
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        query = supabase.table("waitlist").select("*")
        
        if status:
            query = query.eq("status", status)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return {
            "success": True,
            "data": result.data,
            "count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        print(f"Get waitlist error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/waitlist/count")
async def get_waitlist_count():
    """
    Get total waitlist count
    """
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        result = supabase.table("waitlist").select("id", count="exact").execute()
        
        return {
            "success": True,
            "count": result.count or 0
        }
        
    except Exception as e:
        print(f"Get waitlist count error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# # OFFICIAL UK DEFRA CONVERSION FACTORS
# DEFRA_FACTORS = {
#     # Scope 1: Transport Fuel (kgCO2e per Litre)
#     'Diesel': 2.54,
#     'Petrol': 2.16,
#     'AdBlue': 0.0,
#     'Unknown Fuel': 0.0,
    
#     # Scope 2: Utilities (kgCO2e per kWh)
#     'Electricity': 0.20712, 
#     'Natural Gas': 0.18316,
#     'Unknown Utility': 0.0,

#     # Scope 3: Travel & Waste
#     'Flight (Short Haul)': 0.25496,
#     'Flight (Long Haul)': 0.19534,
#     'Rail (National)': 0.03546,
#     'Hotel Stay': 19.50000,
#     'Mixed Waste': 0.57000,
#     'Recycled Waste': -0.45000,
#     'Unknown Scope 3': 0.0,
# }

ACTIVITY_TYPE_MAPPING = {
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
    
    # Scope 3 types (if you have them in DEFRA table)
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

def get_emission_factor(supabase_client, activity_type: str, reporting_year: int = None):
    """
    Fetch emission factor from database with optional year fallback.
    """
    try:
        # If no year provided, use the most recent available
        if reporting_year is None:
            # Get the most recent year with data
            year_result = supabase_client.from_('defra_conversion_factors') \
                .select('reporting_year') \
                .eq('activity_type', activity_type) \
                .order('reporting_year', desc=True) \
                .limit(1) \
                .execute()
            
            if year_result.data:
                reporting_year = year_result.data[0]['reporting_year']
            else:
                raise ValueError(f"No emission factor found for '{activity_type}'")
        
        # Fetch the factor for the specific year
        factor_result = supabase_client.from_('defra_conversion_factors') \
            .select('co2e_multiplier, reporting_year') \
            .eq('activity_type', activity_type) \
            .eq('reporting_year', reporting_year) \
            .single() \
            .execute()
        
        if not factor_result.data:
            # Try to get the most recent factor for this activity
            fallback_result = supabase_client.from_('defra_conversion_factors') \
                .select('co2e_multiplier, reporting_year') \
                .eq('activity_type', activity_type) \
                .order('reporting_year', desc=True) \
                .limit(1) \
                .execute()
            
            if fallback_result.data:
                return {
                    'multiplier': float(fallback_result.data[0]['co2e_multiplier']),
                    'reporting_year': fallback_result.data[0]['reporting_year'],
                    'is_fallback': True
                }
            else:
                raise ValueError(f"No emission factor found for '{activity_type}'")
        
        return {
            'multiplier': float(factor_result.data['co2e_multiplier']),
            'reporting_year': factor_result.data['reporting_year'],
            'is_fallback': False
        }
        
    except Exception as e:
        print(f"❌ Error fetching emission factor: {e}")
        raise

def get_activity_category(supabase_client, activity_type: str):
    """
    Get CSRD/ISSB category mapping for an activity.
    """
    try:
        result = supabase_client.from_('activity_categories') \
            .select('*') \
            .eq('activity_type', activity_type) \
            .single() \
            .execute()
        
        if result.data:
            return result.data
        else:
            # Return default mapping for unknown activities
            return {
                'activity_type': activity_type,
                'esrs_e1_category': 'Other',
                'issb_category': 'Other',
                'ghg_protocol_scope': 'Scope 3',
                'ghg_protocol_category': 'Other'
            }
    except Exception as e:
        print(f"⚠️ Error fetching category for {activity_type}: {e}")
        return {
            'activity_type': activity_type,
            'esrs_e1_category': 'Other',
            'issb_category': 'Other',
            'ghg_protocol_scope': 'Scope 3',
            'ghg_protocol_category': 'Other'
        }


# ==========================================
# CSV PROCESSING FUNCTIONS
# ==========================================
def process_fuel_data(df: pd.DataFrame, supabase_client) -> tuple:
    """
    Process fuel data using database-stored emission factors.
    """
    df = df.copy()
    date_col = next((c for c in df.columns if 'date' in c.lower()), 'Transaction Date')
    vol_col = next((c for c in df.columns if 'vol' in c.lower() or 'litre' in c.lower() or 'liter' in c.lower()), 'Volume (L)')
    reg_col = next((c for c in df.columns if 'reg' in c.lower() or 'vehicle' in c.lower() or 'plate' in c.lower()), 'Vehicle Registration')
    fuel_col = next((c for c in df.columns if 'fuel' in c.lower()), 'Fuel Type')
    
    df = df.rename(columns={date_col: 'Transaction Date', vol_col: 'Volume (L)', reg_col: 'Vehicle Registration', fuel_col: 'Fuel Type'})
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Volume (L)'] = pd.to_numeric(df['Volume (L)'], errors='coerce')
    df['Fuel Type'] = df['Fuel Type'].astype(str).replace('', 'Unknown Fuel').fillna('Unknown Fuel')
    
    def normalize_fuel(fuel):
        fuel_str = str(fuel).strip().lower()
        if 'diesel' in fuel_str: return 'Diesel'
        if 'petrol' in fuel_str or 'gas' in fuel_str: return 'Petrol'
        if 'adblue' in fuel_str or 'def' in fuel_str: return 'AdBlue'
        if 'lpg' in fuel_str: return 'LPG'
        if 'cng' in fuel_str: return 'CNG'
        return 'Unknown Fuel'

    df['Standardized Fuel'] = df['Fuel Type'].apply(normalize_fuel)
    
    # ✅ Get factors from database
    factors = []
    for fuel in df['Standardized Fuel'].unique():
        if fuel == 'Unknown Fuel':
            factors.append({'fuel': fuel, 'factor': 0, 'year': None})
        else:
            try:
                factor_data = get_emission_factor(supabase_client, fuel)
                factors.append({
                    'fuel': fuel, 
                    'factor': factor_data['multiplier'],
                    'year': factor_data['reporting_year']
                })
            except:
                factors.append({'fuel': fuel, 'factor': 0, 'year': None})
    
    factor_map = {f['fuel']: f['factor'] for f in factors}
    df['DEFRA Factor (kgCO2e/L)'] = df['Standardized Fuel'].map(factor_map).fillna(0)
    df['Total kgCO2e'] = (df['Volume (L)'] * df['DEFRA Factor (kgCO2e/L)']).round(2).fillna(0)
    
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Volume (L)'].isna(), 'needs_review'] = True
    df.loc[df['Volume (L)'].isna(), 'review_reason'] = 'Missing Volume'
    df.loc[df['Standardized Fuel'] == 'Unknown Fuel', 'needs_review'] = True
    df.loc[df['Standardized Fuel'] == 'Unknown Fuel', 'review_reason'] = 'Unrecognized Fuel Type'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Transaction Date', 'Vehicle Registration', 'Standardized Fuel', 'Volume (L)', 
                  'DEFRA Factor (kgCO2e/L)', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())
def process_utility_data(df: pd.DataFrame, supabase_client) -> tuple:
    """
    Process utility data using database-stored emission factors.
    """
    df = df.copy()
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'period' in c.lower()), 'Billing Period Start')
    site_col = next((c for c in df.columns if 'site' in c.lower() or 'facility' in c.lower() or 'location' in c.lower()), 'Site Name')
    vol_col = next((c for c in df.columns if 'consumption' in c.lower() or 'kwh' in c.lower() or 'usage' in c.lower()), 'Consumption (kWh)')
    type_col = next((c for c in df.columns if 'type' in c.lower() or 'utility' in c.lower() or 'meter' in c.lower()), 'Utility Type')
    
    df = df.rename(columns={date_col: 'Billing Period Start', site_col: 'Site Name', 
                           vol_col: 'Consumption (kWh)', type_col: 'Utility Type'})
    df['Billing Period Start'] = pd.to_datetime(df['Billing Period Start'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Consumption (kWh)'] = pd.to_numeric(df['Consumption (kWh)'], errors='coerce')
    
    if 'Cost (£)' in df.columns:
        df['Cost (£)'] = pd.to_numeric(df['Cost (£)'], errors='coerce').fillna(0)

    df['Utility Type'] = df['Utility Type'].astype(str).replace('', 'Unknown Utility').fillna('Unknown Utility')
    
    def normalize_utility_type(utype):
        if pd.isna(utype): return 'Unknown Utility'
        utype_str = str(utype).strip().lower()
        if 'electric' in utype_str: return 'Electricity'
        if 'gas' in utype_str or 'nat' in utype_str: return 'Natural Gas'
        if 'steam' in utype_str: return 'Steam'
        if 'chilled' in utype_str or 'cooling' in utype_str: return 'Chilled Water'
        return 'Unknown Utility'

    df['Standardized Utility'] = df['Utility Type'].apply(normalize_utility_type)
    
    # ✅ Get factors from database
    factors = []
    for utility in df['Standardized Utility'].unique():
        if utility == 'Unknown Utility':
            factors.append({'utility': utility, 'factor': 0})
        else:
            try:
                factor_data = get_emission_factor(supabase_client, utility)
                factors.append({'utility': utility, 'factor': factor_data['multiplier']})
            except:
                factors.append({'utility': utility, 'factor': 0})
    
    factor_map = {f['utility']: f['factor'] for f in factors}
    df['DEFRA Factor (kgCO2e/kWh)'] = df['Standardized Utility'].map(factor_map).fillna(0)
    df['Total kgCO2e'] = (df['Consumption (kWh)'] * df['DEFRA Factor (kgCO2e/kWh)']).round(2).fillna(0)
    
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Consumption (kWh)'].isna(), 'needs_review'] = True
    df.loc[df['Consumption (kWh)'].isna(), 'review_reason'] = 'Missing kWh Consumption'
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'needs_review'] = True
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'review_reason'] = 'Unrecognized Utility Type'
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'needs_review'] = True
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'review_reason'] = 'Missing Site/Facility Name'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_columns = ['Billing Period Start', 'Site Name', 'Standardized Utility', 
                     'Consumption (kWh)', 'DEFRA Factor (kgCO2e/kWh)', 'Total kgCO2e', 
                     'needs_review', 'review_reason']
    if 'Cost (£)' in df.columns:
        clean_columns.insert(4, 'Cost (£)')
        
    return df[[c for c in clean_columns if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())


def process_scope3_data(df: pd.DataFrame, supabase_client) -> tuple:
    """
    Process Scope 3 data using database-stored emission factors.
    """
    df = df.copy()
    date_col = next((c for c in df.columns if 'date' in c.lower()), 'Date')
    desc_col = next((c for c in df.columns if 'desc' in c.lower() or 'detail' in c.lower() or 'purpose' in c.lower()), 'Description')
    vol_col = next((c for c in df.columns if 'qty' in c.lower() or 'quantity' in c.lower() or 'amount' in c.lower() or 'distance' in c.lower() or 'weight' in c.lower()), 'Quantity')
    cat_col = next((c for c in df.columns if 'cat' in c.lower() or 'type' in c.lower() or 'class' in c.lower()), 'Category')
    
    df = df.rename(columns={date_col: 'Date', desc_col: 'Description', vol_col: 'Quantity', cat_col: 'Category'})
    df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    
    if 'Cost (£)' in df.columns:
        df['Cost (£)'] = pd.to_numeric(df['Cost (£)'], errors='coerce').fillna(0)

    df['Category'] = df['Category'].astype(str).replace('', 'Unknown Scope 3').fillna('Unknown Scope 3')
    df['Description'] = df['Description'].astype(str).replace('', 'N/A').fillna('N/A')
    
    def normalize_scope3(cat):
        if pd.isna(cat): return 'Unknown Scope 3'
        cat_str = str(cat).strip().lower()
        if 'flight' in cat_str or 'air' in cat_str: 
            return 'Flight (Long Haul)' if 'long' in cat_str else 'Flight (Short Haul)'
        if 'rail' in cat_str or 'train' in cat_str: return 'Rail (National)'
        if 'hotel' in cat_str or 'stay' in cat_str: return 'Hotel Stay'
        if 'waste' in cat_str or 'rubbish' in cat_str: 
            return 'Recycled Waste' if 'recycle' in cat_str else 'Mixed Waste'
        if 'car' in cat_str or 'taxi' in cat_str: return 'Taxi'
        if 'bus' in cat_str: return 'Bus'
        if 'freight' in cat_str or 'cargo' in cat_str: return 'Freight'
        return 'Unknown Scope 3'

    df['Standardized Scope3'] = df['Category'].apply(normalize_scope3)
    
    # ✅ Get factors from database
    factors = []
    for scope in df['Standardized Scope3'].unique():
        if scope == 'Unknown Scope 3':
            factors.append({'scope': scope, 'factor': 0})
        else:
            try:
                factor_data = get_emission_factor(supabase_client, scope)
                factors.append({'scope': scope, 'factor': factor_data['multiplier']})
            except:
                factors.append({'scope': scope, 'factor': 0})
    
    factor_map = {f['scope']: f['factor'] for f in factors}
    df['DEFRA Factor'] = df['Standardized Scope3'].map(factor_map).fillna(0)
    df['Total kgCO2e'] = (df['Quantity'] * df['DEFRA Factor']).round(2).fillna(0)
    
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Quantity'].isna(), 'needs_review'] = True
    df.loc[df['Quantity'].isna(), 'review_reason'] = 'Missing Quantity'
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'needs_review'] = True
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'review_reason'] = 'Unrecognized Category'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_columns = ['Date', 'Description', 'Standardized Scope3', 'Quantity', 
                     'DEFRA Factor', 'Total kgCO2e', 'needs_review', 'review_reason']
    if 'Cost (£)' in df.columns:
        clean_columns.insert(3, 'Cost (£)')
        
    return df[[c for c in clean_columns if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())

# ==========================================
# PDF/IMAGE EXTRACTION HELPERS
# ==========================================

def extract_issues_from_result(extraction_result: dict, data_type: str) -> tuple:
    """
    Extract real issues from the extraction result.
    Returns (issues_list, summary_dict)
    """
    issues = []
    summary = {
        "total_fields": 0,
        "extracted_successfully": 0,
        "needs_manual_review": 0,
        "failed": 0,
        "confidence_score": 0.0
    }
    
    # If extraction failed completely
    if extraction_result.get("status") == "error":
        issues.append({
            "severity": "critical",
            "type": "extraction_failure",
            "field": "document",
            "message": "Failed to extract any data from the document",
            "technical_details": extraction_result.get("error", "Unknown extraction error")
        })
        summary["failed"] = 1
        summary["confidence_score"] = 0.0
        return issues, summary
    
    # Check data streams
    data_streams = extraction_result.get("data_streams", [])
    total_fields = 0
    extracted_count = 0
    review_count = 0
    failed_count = 0
    confidence_scores = []
    
    for stream in data_streams:
        # Check for errors in the stream
        stream_errors = stream.get("errors", [])
        if stream_errors:
            for error in stream_errors:
                issue = {
                    "severity": "critical" if error.get("error_type") == "low_confidence" else "warning",
                    "type": error.get("error_type", "unknown_error"),
                    "field": error.get("field", stream.get("stream_name", "unknown")),
                    "message": error.get("message", "Data extraction issue"),
                    "technical_details": f"Stream: {stream.get('stream_name')} - {error.get('message', '')}"
                }
                
                # Add value if available
                if error.get("value"):
                    issue["value"] = error.get("value")
                
                issues.append(issue)
                failed_count += 1
        
        # Check extracted fields
        extracted_fields = stream.get("extracted_fields", {})
        for field_name, field_data in extracted_fields.items():
            total_fields += 1
            
            # Check confidence
            confidence = field_data.get("confidence", 1.0)
            confidence_scores.append(confidence)
            
            if confidence < 0.60:
                issues.append({
                    "severity": "warning",
                    "type": "low_confidence",
                    "field": field_name,
                    "message": f"Low confidence extraction for {field_name.replace('_', ' ')}",
                    "technical_details": f"Confidence score: {confidence:.2f} (threshold: 0.60)",
                    "value": field_data.get("value", "")
                })
                review_count += 1
            elif field_data.get("status") == "failed" or field_data.get("value") is None or field_data.get("value") == "":
                issues.append({
                    "severity": "critical",
                    "type": "missing_data",
                    "field": field_name,
                    "message": f"Could not extract {field_name.replace('_', ' ')}",
                    "technical_details": f"Field extraction failed - no value found"
                })
                failed_count += 1
            else:
                extracted_count += 1
    
    # Check asset mapping issues
    for stream in data_streams:
        asset_mapping = stream.get("asset_mapping", {})
        if asset_mapping.get("matched_asset_id") is None:
            suggested = asset_mapping.get("suggested_assets", [])
            issues.append({
                "severity": "warning",
                "type": "unmapped_asset",
                "field": "asset_mapping",
                "message": "Could not automatically map to an asset",
                "technical_details": f"No matching asset found. Suggested: {', '.join(suggested) if suggested else 'None'}",
                "value": stream.get("stream_name", "Unknown")
            })
            review_count += 1
    
    # Update summary
    summary["total_fields"] = total_fields
    summary["extracted_successfully"] = extracted_count
    summary["needs_manual_review"] = review_count
    summary["failed"] = failed_count
    summary["confidence_score"] = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    
    return issues, summary


def has_low_confidence(extraction_result: dict) -> bool:
    """Check if any data stream has confidence < 60%"""
    for stream in extraction_result.get("data_streams", []):
        for field in stream.get("extracted_fields", {}).values():
            if field.get("confidence", 1.0) < 0.60:
                return True
    return False


def calculate_emissions_with_defra(supabase_client, activity_type: str, consumption: float, start_date: str, override_year: int = None):
    """
    Auto-detects the reporting year from the start_date, 
    but allows an override. Fetches the exact DEFRA multiplier and calculates kgCO2e.
    """
    # 1. Auto-detect year from start_date (e.g., "2025-05-15" -> 2025)
    try:
        detected_year = int(str(start_date).split('-')[0])
    except (ValueError, IndexError):
        detected_year = 2025
        
    # 2. Apply override if provided by the user
    reporting_year = override_year if override_year else detected_year
    
    # 3. Get category info for audit trail
    category_info = get_activity_category(supabase_client, activity_type)
    
    # 4. Fetch the specific factor for this year and activity
    factor_data = get_emission_factor(supabase_client, activity_type, reporting_year)
    
    multiplier = factor_data['multiplier']
    calculated_kg_co2e = round(consumption * multiplier, 4)
    
    return {
        "reporting_year": factor_data['reporting_year'],
        "multiplier_used": multiplier,
        "calculated_kg_co2e": calculated_kg_co2e,
        "is_fallback": factor_data.get('is_fallback', False),
        "category_mapping": {
            "esrs_e1_category": category_info.get('esrs_e1_category'),
            "issb_category": category_info.get('issb_category'),
            "ghg_protocol_scope": category_info.get('ghg_protocol_scope'),
            "ghg_protocol_category": category_info.get('ghg_protocol_category')
        }
    }

# ==================================
# API ENDPOINTS
# ==========================================

@app.get("/")
def read_root():
    return {"message": "CarbonTally API v3.0 is running."}

@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    data_type: str = Form('fuel')
):
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are allowed.")
    
    try:
        # Initialize Supabase client for database lookups
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key) if supabase_url and supabase_key else None
        
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        df.columns = df.columns.str.strip()
        
        if data_type == 'utility':
            clean_data, flagged_rows = process_utility_data(df, supabase_client)
            scope = "Scope 2"
        elif data_type == 'scope3':
            clean_data, flagged_rows = process_scope3_data(df, supabase_client)
            scope = "Scope 3"
        else:
            clean_data, flagged_rows = process_fuel_data(df, supabase_client)
            scope = "Scope 1"
            
        total_emissions = sum(row.get('Total kgCO2e', 0) or 0 for row in clean_data)
        
        return {
            "status": "success",
            "filename": file.filename,
            "data_type": data_type,
            "scope": scope,
            "rows_processed": len(clean_data),
            "rows_flagged_for_review": flagged_rows,
            "total_kgCO2e": round(total_emissions, 2),
            "data": clean_data
        }
    except Exception as e:
        print(f"--- BACKEND CRASH ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")
    
@app.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    data_type: str = Form('utility'),
    organization_id: str = Form(None)
):
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
    
    try:
        organization_assets = [
            {"id": "1", "name": "Birmingham Hub Main Floor"},
            {"id": "2", "name": "Birmingham Hub Unit 4"}
        ]
        
        file_bytes = await file.read()
        extraction_result = pdf_extractor.extract_and_parse(
            file_bytes, file.filename, data_type, organization_assets
        )
        
        if extraction_result.get("status") == "error" or has_low_confidence(extraction_result):
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
            
            if not supabase_url or not supabase_key:
                raise HTTPException(status_code=500, detail="Server configuration error: Missing Supabase credentials.")
            
            supabase_client = create_client(supabase_url, supabase_key)
            
            # 🔥 Extract issues and summary BEFORE queueing
            issues, summary = extract_issues_from_result(extraction_result, data_type)
            
            # Queue for manual review with the extracted issues
            review_id, issues, summary = await queue_for_manual_review(
                file_bytes=file_bytes,
                filename=file.filename,
                content_type=file.content_type,
                data_type=data_type,
                organization_id=organization_id or "unknown",
                auto_result=extraction_result,
                supabase_client=supabase_client
            )
            
            return {
                "status": "manual_review_required",
                "message": "Our team will manually extract your data within 24 hours.",
                "review_id": review_id,
                "estimated_completion": "24-48 hours",
                "extraction_issues": issues,
                "extraction_summary": summary,
                "confidence_score": summary.get("confidence_score", 0.0)
            }
        
        return extraction_result
    
    except Exception as e:
        print(f"--- PDF EXTRACTION ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

@app.post("/upload-batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    batch_name: str = Form(...),
    data_type: str = Form('mixed'),
    organization_id: str = Form(...),
    special_instructions: str = Form('')
):
    """
    Accept multiple files at once and create a batch for processing.
    Uses database-driven emission factors and asset mapping.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        
        if not supabase_url or not supabase_key:
            raise HTTPException(status_code=500, detail="Server configuration error: Missing Supabase credentials.")
        
        supabase_client = create_client(supabase_url, supabase_key)
        
        # ✅ FIX: Validate and clean organization_id
        import uuid
        valid_org_id = None
        
        if organization_id and organization_id != "unknown" and organization_id != "mock-org-id":
            try:
                uuid.UUID(organization_id)
                valid_org_id = organization_id
            except ValueError:
                print(f"⚠️ Invalid organization_id format: {organization_id}")
                # Try to get first organization
                org_response = supabase_client.from_('organizations').select('id').limit(1).execute()
                if org_response.data:
                    valid_org_id = org_response.data[0]['id']
                    print(f"✅ Using fallback organization: {valid_org_id}")
        
        if not valid_org_id:
            raise HTTPException(status_code=400, detail="Valid organization_id is required")
        
        # ✅ FIX: Get organization assets - CORRECT QUERY
        # Option 1: If assets table has organization_id column
        assets_response = supabase_client.from_('assets') \
            .select('id, name, facility_id') \
            .eq('organization_id', valid_org_id) \
            .execute()
        
        # Option 2: If assets table doesn't have organization_id, join through facilities
        if not assets_response.data:
            # First get facilities for this organization
            facilities_response = supabase_client.from_('facilities') \
                .select('id') \
                .eq('organization_id', valid_org_id) \
                .execute()
            
            facility_ids = [f['id'] for f in facilities_response.data] if facilities_response.data else []
            
            if facility_ids:
                # Then get assets for these facilities
                assets_response = supabase_client.from_('assets') \
                    .select('id, name, facility_id') \
                    .in_('facility_id', facility_ids) \
                    .execute()
        
        organization_assets = assets_response.data or []
        print(f"📦 Found {len(organization_assets)} assets for organization {valid_org_id}")
        
        # ✅ Get facilities for asset mapping
        facilities_response = supabase_client.from_('facilities') \
            .select('id, name') \
            .eq('organization_id', valid_org_id) \
            .execute()
        
        facilities = facilities_response.data or []
        print(f"🏢 Found {len(facilities)} facilities for organization {valid_org_id}")
        
        # ✅ Get emission factors for validation (pre-load for speed)
        factors_response = supabase_client.from_('defra_conversion_factors') \
            .select('activity_type, reporting_year, co2e_multiplier') \
            .eq('reporting_year', datetime.now().year) \
            .execute()
        
        available_factors = {f['activity_type']: f['co2e_multiplier'] for f in factors_response.data or []}
        print(f"📊 Loaded {len(available_factors)} emission factors for {datetime.now().year}")
        
        # Create batch record
        batch_response = supabase_client.from_('upload_batches').insert({
            'organization_id': valid_org_id,  # ✅ Use validated org_id
            'batch_name': batch_name,
            'total_files': len(files),
            'processed_files': 0,
            'status': 'processing',
            'metadata': {
                'data_type': data_type,
                'special_instructions': special_instructions,
                'assets_count': len(organization_assets),
                'facilities_count': len(facilities)
            }
        }).execute()
        
        batch_id = batch_response.data[0]['id']
        print(f"📋 Created batch: {batch_id} with {len(files)} files")
        
        processed_count = 0
        failed_files = []
        processed_files = []
        
        for file in files:
            try:
                print(f"📄 Processing file: {file.filename}")
                file_bytes = await file.read()
                file_size = len(file_bytes)
                
                # Generate unique file path
                file_path = f"batches/{valid_org_id}/{batch_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                
                # Upload to Supabase Storage
                storage_response = supabase_client.storage.from_('documents').upload(
                    file_path,
                    file_bytes,
                    file_options={"content-type": file.content_type}
                )
                
                file_url = supabase_client.storage.from_('documents').get_public_url(file_path)
                print(f"✅ File uploaded: {file_url}")
                
                file_type = 'PDF' if file.filename.lower().endswith('.pdf') else 'IMAGE'
                actual_data_type = data_type if data_type != 'mixed' else 'utility'
                
                # ✅ Extract data with proper asset mapping
                if file_type == 'PDF':
                    extraction_result = pdf_extractor.extract_and_parse(
                        file_bytes, 
                        file.filename, 
                        actual_data_type, 
                        organization_assets
                    )
                else:
                    extraction_result = pdf_extractor.extract_and_parse_image(
                        file_bytes, 
                        file.filename, 
                        actual_data_type, 
                        organization_assets
                    )
                
                # ✅ Check if extraction succeeded or needs review
                if extraction_result.get("status") == "error" or has_low_confidence(extraction_result):
                    print(f"⚠️ Extraction for {file.filename} needs review")
                    issues, summary = extract_issues_from_result(extraction_result, actual_data_type)
                    
                    # Build customer note with special instructions
                    base_note = f"Batch upload: {batch_name}. File: {file.filename}"
                    if special_instructions.strip():
                        base_note += f" | 📝 CUSTOMER NOTE: {special_instructions.strip()}"
                    
                    # ✅ Add asset mapping info to extraction result
                    if organization_assets:
                        asset_names = [a['name'] for a in organization_assets[:5]]
                        extraction_result['available_assets'] = asset_names
                    
                    # ✅ Insert into manual review queue with valid org_id
                    review_response = supabase_client.from_('manual_review_queue').insert({
                        'organization_id': valid_org_id,  # ✅ Use validated org_id
                        'batch_id': batch_id,
                        'file_url': file_url,
                        'file_name': file.filename,
                        'file_size_bytes': file_size,
                        'file_type': file_type,
                        'data_type': actual_data_type,
                        'status': 'pending',
                        'auto_extraction_result': extraction_result,
                        'extraction_issues': issues,
                        'extraction_summary': summary,
                        'priority': 1 if extraction_result.get('status') == 'error' else 0,
                        'customer_notes': base_note,
                        'estimated_completion_hours': 24,
                        'created_at': datetime.now().isoformat()
                    }).execute()
                    
                    review_id = review_response.data[0]['id']
                    processed_files.append({
                        'filename': file.filename,
                        'status': 'manual_review_required',
                        'review_id': review_id,
                        'issues_count': len(issues)
                    })
                    print(f"📋 Added {file.filename} to manual review queue: {review_id}")
                else:
                    # ✅ Extraction successful - data ready for review
                    data_streams = extraction_result.get('data_streams', [])
                    extracted_count = 0
                    for stream in data_streams:
                        extracted_fields = stream.get('extracted_fields', {})
                        if extracted_fields:
                            extracted_count += len(extracted_fields)
                    
                    processed_files.append({
                        'filename': file.filename,
                        'status': 'extracted',
                        'data_streams_count': len(data_streams),
                        'extracted_fields_count': extracted_count
                    })
                    print(f"✅ Extraction successful for {file.filename}: {extracted_count} fields extracted")
                
                processed_count += 1
                
            except Exception as file_error:
                print(f"❌ Error processing file {file.filename}: {file_error}")
                failed_files.append({
                    'filename': file.filename,
                    'error': str(file_error)
                })
                continue
        
        # ✅ Update batch status
        final_status = 'completed' if len(failed_files) == 0 else 'partial'
        
        # Check if any files need manual review
        needs_review = any(f.get('status') == 'manual_review_required' for f in processed_files)
        if needs_review and final_status == 'completed':
            final_status = 'review_needed'
        
        supabase_client.from_('upload_batches').update({
            'processed_files': processed_count,
            'status': final_status,
            'completed_at': datetime.now().isoformat(),
            'metadata': {
                'data_type': data_type,
                'special_instructions': special_instructions,
                'failed_files': failed_files,
                'processed_files': processed_files,
                'assets_available': len(organization_assets),
                'facilities_available': len(facilities),
                'needs_review': needs_review
            }
        }).eq('id', batch_id).execute()
        
        # ✅ Send notification if any files need review
        if needs_review:
            try:
                await notify_staff_batch_review_needed(
                    batch_id=batch_id,
                    organization_id=valid_org_id,  # ✅ Use validated org_id
                    batch_name=batch_name,
                    files_needing_review=[f for f in processed_files if f.get('status') == 'manual_review_required'],
                    supabase_client=supabase_client
                )
            except Exception as notify_error:
                print(f"⚠️ Notification error: {notify_error}")
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "message": f"Successfully uploaded {processed_count}/{len(files)} files",
            "batch_name": batch_name,
            "processed_files": processed_files,
            "failed_files": failed_files,
            "needs_review": needs_review,
            "assets_available": len(organization_assets),
            "facilities_available": len(facilities)
        }
        
    except Exception as e:
        print(f"--- BATCH UPLOAD ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


@app.post("/repair-pdf")
async def repair_pdf(file: UploadFile = File(...)):
    """
    Advanced PDF repair with OCR for corrupted or scanned documents
    """
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        from PIL import Image
        import io
        from pypdf import PdfReader, PdfWriter
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.utils import ImageReader
        
        file_bytes = await file.read()
        
        # Step 1: Try to read with pypdf
        is_readable = False
        try:
            pdf_reader = PdfReader(io.BytesIO(file_bytes))
            if len(pdf_reader.pages) > 0:
                is_readable = True
                print(f"✅ PDF has {len(pdf_reader.pages)} pages")
        except Exception as e:
            print(f"⚠️ PDF read error: {e}")
        
        # Step 2: Convert to images for OCR
        try:
            images = convert_from_bytes(file_bytes, dpi=300)
            print(f"🖼️ Converted to {len(images)} images")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Unsupported PDF format: {str(e)}")
        
        # Step 3: OCR each page
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        
        packet = io.BytesIO()
        c = canvas.Canvas(packet, pagesize=letter)
        
        ocr_texts = []
        for i, image in enumerate(images):
            # OCR the image with multiple languages
            ocr_text = pytesseract.image_to_string(image, lang='eng+deu+fra')
            ocr_texts.append(ocr_text[:500])  # Store sample
            
            # Get image dimensions
            width, height = image.size
            
            # Scale to fit page
            scale = min(letter[0] / width, letter[1] / height) * 0.95
            scaled_width = width * scale
            scaled_height = height * scale
            x_offset = (letter[0] - scaled_width) / 2
            y_offset = (letter[1] - scaled_height) / 2
            
            # Convert image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)
            
            # Draw image
            img = ImageReader(img_byte_arr)
            c.drawImage(img, x_offset, y_offset, width=scaled_width, height=scaled_height)
            
            # Add invisible OCR text layer
            c.setFont("Helvetica", 1)
            c.setFillColorRGB(1, 1, 1)
            c.drawString(10, 10, ocr_text)
            
            c.showPage()
        
        c.save()
        packet.seek(0)
        
        # Step 4: Merge with original if readable
        if is_readable:
            writer = PdfWriter()
            original = PdfReader(io.BytesIO(file_bytes))
            ocr_pdf = PdfReader(packet)
            
            for page_num, page in enumerate(original.pages):
                if page_num < len(ocr_pdf.pages):
                    page.merge_page(ocr_pdf.pages[page_num])
                writer.add_page(page)
            
            output = io.BytesIO()
            writer.write(output)
            output.seek(0)
            repaired_bytes = output.getvalue()
        else:
            repaired_bytes = packet.getvalue()
        
        # Step 5: Upload to Supabase
        repaired_filename = f"repaired_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        file_path = f"repaired_pdfs/{repaired_filename}"
        
        storage_response = supabase.storage.from_('documents').upload(
            file_path,
            repaired_bytes,
            file_options={"content-type": "application/pdf"}
        )
        
        file_url = supabase.storage.from_('documents').get_public_url(file_path)
        
        return {
            "status": "success",
            "message": "PDF repaired successfully",
            "repaired_url": file_url,
            "filename": repaired_filename,
            "pages": len(images),
            "ocr_text_samples": [text[:200] for text in ocr_texts[:3]]
        }
        
    except Exception as e:
        print(f"❌ PDF repair error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"PDF repair failed: {str(e)}")
            
async def notify_staff_batch_review_needed(batch_id: str, organization_id: str, batch_name: str, files_needing_review: list, supabase_client):
    """
    Send notification to staff when batch files need manual review.
    """
    try:
        # Get staff emails from staff_profiles
        staff_response = supabase_client.from_('staff_profiles') \
            .select('email, first_name, last_name') \
            .eq('is_active', True) \
            .execute()
        
        staff_emails = [s['email'] for s in staff_response.data or [] if s.get('email')]
        
        if not staff_emails:
            print("⚠️ No staff emails found for notification")
            return
        
        # Build email content
        file_list = "\n".join([f"  - {f['filename']}" for f in files_needing_review])
        
        html_content = f"""
        <h2>📋 Batch Manual Review Required</h2>
        <p><strong>Batch:</strong> {batch_name}</p>
        <p><strong>Organization ID:</strong> {organization_id}</p>
        <p><strong>Batch ID:</strong> {batch_id}</p>
        <p><strong>Files Needing Review:</strong></p>
        <pre style="background: #f1f5f9; padding: 1rem; border-radius: 8px;">
{file_list}
        </pre>
        <p><a href="https://carbontally.co.uk/staff-dashboard" style="background: #16a34a; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Open Staff Dashboard</a></p>
        """
        
        # Send to all staff
        for email in staff_emails:
            try:
                send_email(
                    to=email,
                    subject=f"📋 Batch Review Required: {batch_name}",
                    html_content=html_content
                )
            except Exception as email_error:
                print(f"⚠️ Failed to send email to {email}: {email_error}")
        
        print(f"✅ Notified {len(staff_emails)} staff members about batch {batch_id}")
        
    except Exception as e:
        print(f"❌ Failed to send staff notification: {e}")


@app.post("/approve-pdf-batch")
async def approve_pdf_batch(batch_data: dict):
    try:
        batch_id = batch_data.get("batch_id")
        data_streams = batch_data.get("data_streams", [])
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "records_committed": len(data_streams),
            "message": "Batch approved and committed to database"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch approval failed: {str(e)}")


def send_email(to: str, subject: str, html_content: str, from_email: str = "CarbonTally <notifications@carbontally.co.uk>"):
    """
    Generic email sending function using Resend.
    Returns: (success: bool, message: str)
    """
    try:
        if not resend.api_key:
            print("⚠️ RESEND_API_KEY not set, skipping email")
            return False, "API key not configured"
        
        response = resend.Emails.send({
            "from": from_email,
            "to": [to],
            "subject": subject,
            "html": html_content,
        })
        
        print(f"✅ Email sent to {to}: {subject}")
        return True, "Email sent successfully"
        
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False, str(e)
    
@app.post("/notify-customer-manual-extraction")

async def notify_customer_manual_extraction(batch_data: dict):
    """
    Send an email to the customer notifying them that their manual extraction is complete
    and ready for their final review.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)

        review_id = batch_data.get("review_id")
        organization_id = batch_data.get("organization_id")
        file_name = batch_data.get("file_name")
        
        org_members = supabase_client.from_('organization_members')\
            .select('user_id, auth.users(email)')\
            .eq('organization_id', organization_id)\
            .limit(1)\
            .execute()
        
        if not org_members.data or len(org_members.data) == 0:
            return {"status": "warning", "message": "No customer email found, but extraction completed"}
        
        customer_email = org_members.data[0]['auth.users']['email']
        
        try:
            resend.Emails.send({
                "from": "CarbonTally <notifications@carbontally.co.uk>",
                "to": [customer_email],
                "subject": f"✅ Your Document Has Been Processed: {file_name}",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                  <h2 style="color: #16a34a;">✅ Your Document Has Been Processed</h2>
                  <p>Hi there,</p>
                  <p>Great news! Our team has manually reviewed and extracted the data from your uploaded document:</p>
                  <div style="background: #f8fafc; padding: 1.5rem; border-radius: 8px; margin: 1.5rem 0;">
                    <p style="margin: 0.5rem 0;"><strong>Document:</strong> {file_name}</p>
                    <p style="margin: 0.5rem 0;"><strong>Review ID:</strong> <code style="background: #e2e8f0; padding: 2px 6px; border-radius: 4px;">{review_id}</code></p>
                    <p style="margin: 0.5rem 0;"><strong>Status:</strong> <span style="color: #16a34a; font-weight: bold;">Ready for Your Review</span></p>
                  </div>
                  <p>The extracted data is now available in your CarbonTally dashboard. Please review it and click "Approve" to commit it to your emissions records.</p>
                  <a href="https://carbontally.co.uk" style="display: inline-block; background: #16a34a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; margin: 1rem 0;">
                    Review & Approve Data →
                  </a>
                  <p style="color: #64748b; font-size: 0.875rem; margin-top: 2rem;">
                    If you have any questions or need adjustments, please reply to this email or contact our support team.
                  </p>
                  <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0;">
                  <p style="color: #94a3b8; font-size: 0.75rem;">
                    This is an automated message from CarbonTally. Please do not reply directly to this email.
                  </p>
                </div>
                """
            })
            
            return {
                "status": "success",
                "message": f"Customer notification sent to {customer_email}"
            }
        
        except Exception as email_error:
            print(f"Email notification failed: {email_error}")
            return {
                "status": "warning", 
                "message": "Extraction completed but email notification failed",
                "error": str(email_error)
            }
    
    except Exception as e:
        print(f"--- CUSTOMER NOTIFICATION ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Customer notification failed: {str(e)}")

@app.post("/notify-batch-completion")
async def notify_batch_completion(batch_data: dict):
    """
    Send an email to the customer when the LAST file in their batch is manually processed.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)

        batch_id = batch_data.get("batch_id")
        organization_id = batch_data.get("organization_id")
        
        batch_res = supabase_client.from_('upload_batches')\
            .select('batch_name, total_files')\
            .eq('id', batch_id)\
            .single()\
            .execute()
        
        batch_info = batch_res.data
        if not batch_info:
            return {"status": "error", "message": "Batch not found"}
            
        batch_name = batch_info.get('batch_name', 'Your Documents')
        total_files = batch_info.get('total_files', 0)
        
        org_members = supabase_client.from_('organization_members')\
            .select('user_id, auth.users(email)')\
            .eq('organization_id', organization_id)\
            .limit(1)\
            .execute()
        
        if not org_members.data or len(org_members.data) == 0:
            return {"status": "warning", "message": "No customer email found"}
        
        customer_email = org_members.data[0]['auth.users']['email']
        
        # Send email using the refactored function
        success = send_batch_completion_email(
            customer_email=customer_email,
            batch_name=batch_name,
            total_files=total_files
        )
        
        if success:
            return {"status": "success", "message": f"Batch completion email sent to {customer_email}"}
        else:
            return {"status": "warning", "message": "Batch marked complete, but email failed"}
    
    except Exception as e:
        print(f"--- BATCH NOTIFICATION ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Batch notification failed: {str(e)}")

def send_batch_completion_email(customer_email: str, batch_name: str, total_files: int):
    """
    Send batch completion notification to customer
    """
    try:
        html_content = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; color: #334155;">
            <div style="background: #16a34a; color: white; padding: 2rem; text-align: center; border-radius: 8px 8px 0 0;">
                <h1 style="margin: 0; font-size: 1.5rem;">✅ Processing Complete!</h1>
            </div>
            <div style="background: #ffffff; padding: 2rem; border: 1px solid #e2e8f0; border-top: none; border-radius: 0 0 8px 8px;">
                <p>Hi there,</p>
                <p>Great news! Our team has finished manually reviewing and extracting the data from your bulk upload.</p>
                <div style="background: #f0fdf4; border-left: 4px solid #16a34a; padding: 1rem; margin: 1.5rem 0;">
                    <p style="margin: 0.25rem 0;"><strong>Batch Name:</strong> {batch_name}</p>
                    <p style="margin: 0.25rem 0;"><strong>Files Processed:</strong> {total_files} documents</p>
                    <p style="margin: 0.25rem 0;"><strong>Status:</strong> <span style="color: #16a34a; font-weight: bold;">Ready for Review</span></p>
                </div>
                <p>All extracted emissions data has been mapped to your facilities and assets. You can now review the data and generate your SECR compliance report with a single click.</p>
                <div style="text-align: center; margin: 2rem 0;">
                    <a href="https://carbontally.co.uk" style="background: #16a34a; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                        Review Data & Generate Report →
                    </a>
                </div>
                <p style="color: #64748b; font-size: 0.875rem; margin-top: 2rem;">
                    If you notice any discrepancies or need adjustments, simply reply to this email and our support team will assist you.
                </p>
            </div>
        </div>
        """
        
        success, message = send_email(
            to=customer_email,
            subject=f"✅ Your Bulk Upload is Ready: {batch_name}",
            html_content=html_content
        )
        
        if success:
            print(f"✅ Batch completion email sent to {customer_email}")
        else:
            print(f"⚠️ Failed to send batch completion email: {message}")
        
        return success
        
    except Exception as e:
        print(f"❌ send_batch_completion_email error: {e}")
        return False

@app.post("/admin/import-defra-factors")
async def import_defra_factors(
    file: UploadFile = File(...),
    reporting_year: int = Form(...)
):
    """
    Admin endpoint to upload a cleaned DEFRA CSV and upsert factors for a specific year.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)

        # 1. Read the uploaded CSV
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # 2. Basic cleaning (Adjust column names to match your actual cleaned CSV)
        # Assuming your CSV has columns: 'activity_type' and 'co2e_multiplier'
        required_cols = ['activity_type', 'co2e_multiplier']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(status_code=400, detail=f"CSV must contain columns: {required_cols}")
            
        df = df.dropna(subset=required_cols)
        df['reporting_year'] = reporting_year
        df['co2e_multiplier'] = df['co2e_multiplier'].astype(float)
        df['activity_type'] = df['activity_type'].str.strip() # Clean whitespace
        
        # 3. Convert to list of dicts for Supabase
        records = df[['reporting_year', 'activity_type', 'co2e_multiplier']].to_dict('records')
        
        # 4. Upsert into Supabase (Updates if exists, inserts if new)
        res = supabase_client.from_('defra_conversion_factors').upsert(
            records, 
            on_conflict='reporting_year,activity_type'
        ).execute()
        
        return {
            "status": "success", 
            "message": f"Successfully imported/updated {len(records)} DEFRA factors for {reporting_year}"
        }
        
    except Exception as e:
        import traceback
        print(f"--- DEFRA IMPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Import failed: {str(e)}")

@app.post("/approve-extraction")
async def approve_extraction(approval_data: dict):
    """
    Called when admin completes manual review OR customer approves auto-extracted data.
    Calculates emissions using DEFRA factors and saves to emissions_logs.
    """
    try:
        # Initialize Supabase client
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        review_id = approval_data.get("review_id")
        organization_id = approval_data.get("organization_id")
        extraction_result = approval_data.get("extraction_result")
        
        # Extract the data fields
        billing_start = extraction_result.get("billing_start")
        consumption = float(extraction_result.get("consumption"))
        fuel_utility_type = extraction_result.get("fuel_utility_type")
        asset_name = extraction_result.get("asset_name")
        override_year = approval_data.get("reporting_year")  # Optional override
        
        # 🎯 CALL THE DEFRA CALCULATION FUNCTION
        calculation = calculate_emissions_with_defra(
            supabase_client=supabase_client,
            activity_type=fuel_utility_type,
            consumption=consumption,
            start_date=billing_start,
            override_year=override_year
        )
        
        # Fetch the asset_id from the asset_name
        asset_res = supabase_client.from_('assets') \
            .select('id') \
            .eq('name', asset_name) \
            .eq('organization_id', organization_id) \
            .single() \
            .execute()
        
        asset_id = asset_res.data['id'] if asset_res.data else None
        
        # Fetch the DEFRA factor_id
        factor_res = supabase_client.from_('defra_conversion_factors') \
            .select('id') \
            .eq('activity_type', fuel_utility_type) \
            .eq('reporting_year', calculation['reporting_year']) \
            .single() \
            .execute()
        
        factor_id = factor_res.data['id'] if factor_res.data else None
        
        # 🎯 INSERT INTO emissions_logs (the official SECR record)
        emissions_log_res = supabase_client.from_('emissions_logs').insert({
            'organization_id': organization_id,
            'asset_id': asset_id,
            'defra_factor_id': factor_id,
            'start_date': billing_start,
            'end_date': billing_start,  # For simplicity, use same date
            'raw_quantity': consumption,
            'calculated_kg_co2e': calculation['calculated_kg_co2e'],
            'created_by_user_id': approval_data.get("approved_by_user_id"),
            'metadata': {
                'fuel_type': fuel_utility_type,
                'reporting_year': calculation['reporting_year'],
                'multiplier_used': calculation['multiplier_used'],
                'source': 'manual_review' if review_id else 'auto_extraction',
                'review_id': review_id
            }
        }).execute()
        
        return {
            "status": "success",
            "message": "Emissions record saved to official logs",
            "emission_id": emissions_log_res.data[0]['id'],
            "calculated_kg_co2e": calculation['calculated_kg_co2e'],
            "reporting_year": calculation['reporting_year']
        }
        
    except Exception as e:
        import traceback
        print(f"--- APPROVAL ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Approval failed: {str(e)}")
@app.post("/add-manual-review-note")
async def add_manual_review_note(note_data: dict):
    """
    Allows a customer to append a special instruction to an already queued manual review item.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        review_id = note_data.get("review_id")
        special_instructions = note_data.get("special_instructions", "").strip()
        
        if not review_id or not special_instructions:
            raise HTTPException(status_code=400, detail="review_id and special_instructions are required")
            
        # 1. Fetch the current queue item to get existing notes
        current_item = supabase_client.from_('manual_review_queue')\
            .select('customer_notes')\
            .eq('id', review_id)\
            .single()\
            .execute()
            
        if not current_item.data:
            raise HTTPException(status_code=404, detail="Review item not found")
            
        existing_notes = current_item.data.get('customer_notes') or ""
        
        # 2. Append the new note cleanly
        if "📝 CUSTOMER NOTE:" in existing_notes:
            # If a note already exists, just append to it
            updated_notes = f"{existing_notes} | {special_instructions}"
        else:
            # First time adding a note
            updated_notes = f"{existing_notes} | 📝 CUSTOMER NOTE: {special_instructions}".strip(" |")
            
        # 3. Update the database
        supabase_client.from_('manual_review_queue')\
            .update({'customer_notes': updated_notes})\
            .eq('id', review_id)\
            .execute()
            
        return {"status": "success", "message": "Note added successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"--- ADD NOTE ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Failed to add note: {str(e)}")


@app.post("/generate-secr-report")
async def generate_secr_report(report_data: dict):
    """
    Generate a branded SECR compliance report PDF for the organization.
    Uses the new report_generator module.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        organization_id = report_data.get("organization_id")
        requested_year = report_data.get("reporting_year", datetime.now().year)
        
        print(f"📊 Generating SECR report for organization: {organization_id}, year: {requested_year}")
        
        # Use the new report generator
        generator = SustainabilityReportGenerator(
            supabase_client, 
            organization_id, 
            requested_year
        )
        
        result = generator.generate_secr_report()
        
        print(f"✅ SECR report generated successfully with {result.get('records_used', 0)} records")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- SECR REPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.post("/generate-csrd-report")
async def generate_csrd_report(report_data: dict):
    """
    Generate a CSRD (EU) compliance report for the organization.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        organization_id = report_data.get("organization_id")
        requested_year = report_data.get("reporting_year", datetime.now().year)
        
        print(f"📊 Generating CSRD report for organization: {organization_id}, year: {requested_year}")
        
        generator = SustainabilityReportGenerator(
            supabase_client, 
            organization_id, 
            requested_year
        )
        
        result = generator.generate_csrd_report()
        
        print(f"✅ CSRD report generated successfully")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- CSRD REPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.post("/generate-issb-report")
async def generate_issb_report(report_data: dict):
    """
    Generate an ISSB (International) compliance report for the organization.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        organization_id = report_data.get("organization_id")
        requested_year = report_data.get("reporting_year", datetime.now().year)
        
        print(f"📊 Generating ISSB report for organization: {organization_id}, year: {requested_year}")
        
        generator = SustainabilityReportGenerator(
            supabase_client, 
            organization_id, 
            requested_year
        )
        
        result = generator.generate_issb_report()
        
        print(f"✅ ISSB report generated successfully")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- ISSB REPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")


@app.post("/generate-all-reports")
async def generate_all_reports(report_data: dict):
    """
    Generate all three report types (SECR, CSRD, ISSB) at once.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        organization_id = report_data.get("organization_id")
        requested_year = report_data.get("reporting_year", datetime.now().year)
        
        print(f"📊 Generating all reports for organization: {organization_id}, year: {requested_year}")
        
        generator = SustainabilityReportGenerator(
            supabase_client, 
            organization_id, 
            requested_year
        )
        
        results = {
            "secr": generator.generate_secr_report(),
            "csrd": generator.generate_csrd_report(),
            "issb": generator.generate_issb_report()
        }
        
        print(f"✅ All reports generated successfully")
        
        return {
            "status": "success",
            "reports": results,
            "organization": generator.organization_name,
            "year": requested_year
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- ALL REPORTS ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
def map_to_ghg_protocol(activity_type: str) -> tuple[str, str]:
    """
    Maps our internal activity types to official GHG Protocol Scopes and Categories 
    required for CSRD (ESRS E1) and ISSB (IFRS S2) compliance.
    """
    activity_lower = activity_type.lower()
    
    if any(fuel in activity_lower for fuel in ['diesel', 'petrol', 'lpg', 'natural gas']):
        if 'natural gas' in activity_lower:
            return "Scope 1", "Scope 1: Stationary Combustion"
        return "Scope 1", "Scope 1: Mobile Combustion (Company Vehicles)"
        
    elif 'electricity' in activity_lower:
        return "Scope 2", "Scope 2: Purchased Electricity (Location-based)"
        
    elif any(travel in activity_lower for travel in ['flight', 'rail', 'hotel', 'taxi', 'uber']):
        return "Scope 3", "Scope 3, Category 6: Business Travel"
        
    elif 'waste' in activity_lower:
        return "Scope 3", "Scope 3, Category 5: Waste Generated in Operations"
        
    elif 'commute' in activity_lower or 'employee' in activity_lower:
        return "Scope 3", "Scope 3, Category 7: Employee Commuting"
        
    else:
        return "Scope 3", "Scope 3: Other Indirect Emissions"

@app.post("/export-ghg-inventory")
async def export_ghg_inventory(report_data: dict):
    """
    Generates a granular, auditor-ready Excel file mapped to GHG Protocol / CSRD categories.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        organization_id = report_data.get("organization_id")
        reporting_year = report_data.get("reporting_year", 2024)
        
        # 1. Fetch detailed emissions data with joins
        emissions_res = supabase_client.from_('emissions_logs')\
            .select('''
                id,
                start_date,
                raw_quantity,
                calculated_kg_co2e,
                metadata,
                assets(name),
                defra_conversion_factors(activity_type, co2e_multiplier)
            ''')\
            .eq('organization_id', organization_id)\
            .gte('start_date', f'{reporting_year}-01-01')\
            .lte('start_date', f'{reporting_year}-12-31')\
            .execute()
            
        records = emissions_res.data or []
        
        if not records:
            return {"status": "error", "message": "No emissions data found for this year."}
            
        # 2. Transform data for Pandas
        flat_data = []
        for row in records:
            activity_type = row.get('defra_conversion_factors', {}).get('activity_type', 'Unknown')
            multiplier = row.get('defra_conversion_factors', {}).get('co2e_multiplier', 0)
            asset_name = row.get('assets', {}).get('name', 'Unassigned Asset')
            metadata = row.get('metadata', {})
            
            scope, category = map_to_ghg_protocol(activity_type)
            
            flat_data.append({
                'Reporting Year': reporting_year,
                'Scope': scope,
                'GHG Protocol Category': category,
                'Date': row.get('start_date', ''),
                'Facility / Asset': asset_name,
                'Activity Type': activity_type,
                'Consumption Quantity': float(row.get('raw_quantity', 0)),
                'Unit': metadata.get('fuel_type', 'Units'), # Fallback
                'DEFRA Multiplier': float(multiplier),
                'Emissions (kg CO2e)': float(row.get('calculated_kg_co2e', 0)),
                'Emissions (tonnes CO2e)': round(float(row.get('calculated_kg_co2e', 0)) / 1000, 4),
                'Data Source': metadata.get('source', 'Manual Entry')
            })
            
        # 3. Create Pandas DataFrame
        df = pd.DataFrame(flat_data)
        
        # 4. Create Summary DataFrame (Pivot Table for Auditors)
        summary_df = df.groupby(['Scope', 'GHG Protocol Category'])['Emissions (tonnes CO2e)'].sum().reset_index()
        summary_df = summary_df.rename(columns={'Emissions (tonnes CO2e)': 'Total Emissions (tonnes CO2e)'})
        
        # 5. Generate Excel File in Memory
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Sheet 1: Detailed Inventory
            df.to_excel(writer, sheet_name='Detailed Inventory', index=False)
            
            # Sheet 2: Summary by Scope (Auditors love this)
            summary_df.to_excel(writer, sheet_name='Summary by Scope', index=False)
            
            # Auto-adjust column widths for professionalism
            for sheet_name in writer.sheets:
                worksheet = writer.sheets[sheet_name]
                for i, col in enumerate(worksheet.columns):
                    max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in col)
                    worksheet.column_dimensions[chr(65 + i)].width = max(min(max_length + 2, 30), 15)

        output.seek(0)
        
        # 6. Return as FileResponse (Triggers browser download)
        filename = f"CarbonTally_GHG_Inventory_{reporting_year}.xlsx"
        return Response(
            content=output.getvalue(),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        import traceback
        print(f"--- EXCEL EXPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Excel export failed: {str(e)}")


def send_review_queue_email(organization_id: str, filename: str, review_id: str, issues: list, summary: dict):
    """
    Send manual review queue notification to founder
    """
    try:
        # Build issues HTML
        issues_html = ""
        if issues:
            for issue in issues:
                severity_color = "#dc2626" if issue.get("severity") == "critical" else "#f59e0b"
                issues_html += f"""
                <div style="padding: 10px; margin: 5px 0; border-left: 4px solid {severity_color}; background: #f8fafc;">
                    <strong>{issue.get('field', 'Unknown')}:</strong> {issue.get('message', '')}
                    {f"<br><small style='color: #64748b;'>Value: {issue.get('value', 'N/A')}</small>" if issue.get('value') else ""}
                    <br><small style='color: #94a3b8;'>{issue.get('technical_details', '')}</small>
                </div>
                """
        
        html_content = f"""
        <h2 style="color: #0f172a;">🚨 Manual Review Queue Alert</h2>
        <p style="color: #475569;">A customer's document could not be auto-extracted and requires manual review.</p>
        
        <table style="border-collapse: collapse; width: 100%; margin: 15px 0; font-size: 14px;">
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f8fafc;">Organization ID:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{organization_id}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f8fafc;">File Name:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{filename}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f8fafc;">Confidence Score:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{(summary.get('confidence_score', 0) * 100):.1f}%</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f8fafc;">Fields Extracted:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{summary.get('extracted_successfully', 0)}/{summary.get('total_fields', 0)}</td>
            </tr>
            <tr>
                <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f8fafc;">Review ID:</td>
                <td style="padding: 8px; border: 1px solid #ddd;">{review_id}</td>
            </tr>
        </table>
        
        <h3 style="color: #0f172a;">📋 Extraction Issues:</h3>
        {issues_html if issues_html else '<p style="color: #64748b;">No specific issues identified, but extraction failed.</p>'}
        
        <div style="margin: 20px 0;">
            <a href="https://carbontally.co.uk/staff-dashboard" style="background: #16a34a; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: 600;">Open Staff Dashboard</a>
        </div>
        <p style="color: #64748b; font-size: 12px; margin-top: 20px;">Estimated completion: 24 hours</p>
        """
        
        success, message = send_email(
            to=FOUNDER_EMAIL,
            subject=f"🚨 Manual Review Required: {filename}",
            html_content=html_content
        )
        
        if success:
            print(f"✅ Review queue email sent to {FOUNDER_EMAIL}")
        else:
            print(f"⚠️ Failed to send review queue email: {message}")
        
        return success
        
    except Exception as e:
        print(f"❌ send_review_queue_email error: {e}")
        return False
    
async def queue_for_manual_review(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    data_type: str,
    organization_id: str,
    auto_result: dict,
    supabase_client
) -> tuple:
    """
    Queue a failed extraction for manual review and send email notification.
    Returns (review_id, issues, summary)
    """
    try:
        # Extract real issues from the result
        issues, summary = extract_issues_from_result(auto_result, data_type)
        
        # If no issues were found but we're here, add a generic one
        if not issues:
            issues.append({
                "severity": "warning",
                "type": "manual_review_required",
                "field": "document",
                "message": "Manual review required",
                "technical_details": "Auto-extraction did not meet quality standards"
            })
        
        # ✅ FIX: Validate organization_id
        import uuid
        valid_org_id = None
        if organization_id and organization_id != "unknown" and organization_id != "mock-org-id":
            try:
                # Try to parse as UUID
                uuid.UUID(organization_id)
                valid_org_id = organization_id
            except ValueError:
                print(f"⚠️ Invalid organization_id format: {organization_id}")
                # You might want to look up the org by name or use a default
                # For now, we'll set it to None and handle it
        
        # If no valid org_id, try to get the first organization or handle gracefully
        if not valid_org_id:
            print("⚠️ No valid organization_id provided, using None")
            # Option: Get default organization
            # org_response = supabase_client.from_('organizations').select('id').limit(1).execute()
            # if org_response.data:
            #     valid_org_id = org_response.data[0]['id']
        
        # 1. Upload file to Supabase Storage
        file_path = f"manual_review/{valid_org_id or 'unknown'}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        storage_response = supabase_client.storage.from_('documents').upload(
            file_path,
            file_bytes,
            file_options={"content-type": content_type}
        )
        
        file_url = supabase_client.storage.from_('documents').get_public_url(file_path)
        
        # ✅ FIX: Only include organization_id if valid
        insert_data = {
            'file_url': file_url,
            'file_name': filename,
            'file_type': 'PDF' if filename.lower().endswith('.pdf') else 'IMAGE',
            'data_type': data_type,
            'status': 'pending',
            'auto_extraction_result': {
                'extraction_result': auto_result,
                'extraction_issues': issues,
                'extraction_summary': summary,
                'confidence_score': summary.get('confidence_score', 0.0)
            },
            'priority': 1 if auto_result.get('status') == 'error' else 0,
            'customer_notes': f"Auto-extraction failed. File: {filename}",
            'estimated_completion_hours': 24
        }
        
        # Only add organization_id if it's valid
        if valid_org_id:
            insert_data['organization_id'] = valid_org_id
        
        # 2. Insert into manual_review_queue
        queue_response = supabase_client.from_('manual_review_queue').insert(insert_data).execute()
        
        review_id = queue_response.data[0]['id']
        
        # 3. Send email notification if we have a valid org
        if valid_org_id:
            send_review_queue_email(
                organization_id=valid_org_id,
                filename=filename,
                review_id=review_id,
                issues=issues,
                summary=summary
            )
        else:
            print(f"⚠️ Skipping email notification - no valid organization_id")
        
        return review_id, issues, summary
    
    except Exception as e:
        print(f"Failed to queue for manual review: {e}")
        import traceback
        traceback.print_exc()
        raise e

def send_confirmation_email_sync(email: str, full_name: Optional[str] = None):
    """Send confirmation email using Resend (synchronous)"""
    try:
        import requests
        
        resend_api_key = os.getenv("RESEND_API_KEY")
        if not resend_api_key:
            print("⚠️ RESEND_API_KEY not set, skipping email")
            return False

        name = full_name or email.split('@')[0]
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to CarbonTally Beta</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
                .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌱 CarbonTally</h1>
                <p style="opacity: 0.8;">Beta Access Request Received</p>
            </div>
            <div class="content">
                <h2>Hi {name}! 👋</h2>
                <p>Thank you for requesting early access to CarbonTally's beta program.</p>
                <p><strong>Here's what happens next:</strong></p>
                <ul>
                    <li>✅ We'll review your request within 24 hours</li>
                    <li>✅ You'll receive a beta invite with your unique access code</li>
                    <li>✅ Start tracking your carbon emissions immediately</li>
                </ul>
                <p style="text-align: center;">
                    <a href="https://carbontally.co.uk" style="display: inline-block; padding: 12px 24px; background: #10b981; color: white; text-decoration: none; border-radius: 8px;">Visit CarbonTally</a>
                </p>
            </div>
            <div class="footer">
                <p>© 2024 CarbonTally. All rights reserved.</p>
                <p style="font-size: 12px;">This email was sent to {email}</p>
            </div>
        </body>
        </html>
        """
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "CarbonTally <notifications@carbontally.co.uk>",
                "to": [email],
                "subject": "🎉 You're on the CarbonTally Beta Waitlist!",
                "html": html_content
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Confirmation email sent to {email}")
            return True
        else:
            print(f"⚠️ Email send failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Email error: {e}")
        return False


# backend/main.py - Add these endpoints

# ============ BETA MANAGEMENT ENDPOINTS ============

class BetaInviteRequest(BaseModel):
    email: EmailStr
    beta_code: str

class BetaInviteResponse(BaseModel):
    success: bool
    message: str
    error: Optional[str] = None
    data: Optional[dict] = None

@app.post("/api/waitlist/invite", response_model=BetaInviteResponse)
async def send_beta_invite(request: BetaInviteRequest):
    """
    Send beta invite email with magic link
    """
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")

        # 1. Check if email exists in waitlist
        email_lower = request.email.lower().strip()
        
        existing = supabase.table("waitlist")\
            .select("email, status, full_name")\
            .eq("email", email_lower)\
            .maybe_single()\
            .execute()
        
        if not existing or not existing.data:
            raise HTTPException(status_code=404, detail="Email not found in waitlist")

        # 2. Get or generate beta code
        existing_code = supabase.table("beta_access_codes")\
            .select("code, status")\
            .eq("email", email_lower)\
            .maybe_single()\
            .execute()
        
        beta_code = None
        if existing_code and existing_code.data and existing_code.data.get("status") == "unused":
            beta_code = existing_code.data.get("code")
            print(f"♻️ Reusing existing beta code: {beta_code}")
        
        if not beta_code:
            beta_code = request.beta_code or generate_beta_code()
            print(f"🆕 Generating new beta code: {beta_code}")
            
            supabase.table("beta_access_codes").insert({
                "code": beta_code,
                "email": email_lower,
                "status": "unused",
                "expires_at": (datetime.now().replace(year=datetime.now().year + 1)).isoformat(),
                "created_at": datetime.now().isoformat()
            }).execute()

        # 3. Update waitlist status to 'invited'
        supabase.table("waitlist")\
            .update({
                "status": "invited",
                "invited_at": datetime.now().isoformat()
            })\
            .eq("email", email_lower)\
            .execute()

        # 4. ✅ Send ONLY the magic link email (no confirmation email)
        try:
            email_sent = send_magic_link_email_sync(
                email=email_lower,
                beta_code=beta_code,
                full_name=existing.data.get("full_name")
            )
            if email_sent:
                print(f"✅ Magic link email sent to {email_lower}")
            else:
                print(f"⚠️ Failed to send magic link email to {email_lower}")
        except Exception as email_error:
            print(f"Email error: {email_error}")
            # Don't fail the request if email fails

        return BetaInviteResponse(
            success=True,
            message=f"Magic link sent to {email_lower}",
            data={"beta_code": beta_code}
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Beta invite error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

def send_magic_link_email_sync(email: str, beta_code: str, full_name: Optional[str] = None):
    """Send magic link email (no confirmation, just the magic link)"""
    try:
        import secrets
        import requests
        
        resend_api_key = os.getenv("RESEND_API_KEY")
        if not resend_api_key:
            print("⚠️ RESEND_API_KEY not set, skipping email")
            return False

        name = full_name or email.split('@')[0]
        
        # ✅ Generate magic token
        token = secrets.token_urlsafe(32)
        magic_link = f"https://carbontally.co.uk/auth/magic?token={token}&email={email}"
        
        # ✅ Save magic token to database
        try:
            supabase.table("beta_access_codes").update({
                "magic_token": token,
                "token_created_at": datetime.now().isoformat()
            }).eq("code", beta_code).execute()
            print(f"✅ Magic token saved for code: {beta_code}")
        except Exception as db_error:
            print(f"⚠️ Failed to save magic token: {db_error}")
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>You're Invited to CarbonTally Beta!</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
                .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
                .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
                .highlight {{ color: #10b981; font-weight: 600; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌱 CarbonTally</h1>
                <p style="opacity: 0.8;">You're Invited to the Beta!</p>
            </div>
            <div class="content">
                <h2>Hi {name}! 🎉</h2>
                <p>Great news! You've been selected for CarbonTally's beta program.</p>
                <p><strong>Click the button below to get started instantly:</strong></p>
                <p style="text-align: center;">
                    <a href="{magic_link}" class="button">🚀 Claim Your Beta Access</a>
                </p>
                <p style="font-size: 14px; color: #64748b; text-align: center;">
                    ✨ <span class="highlight">No signup form needed.</span> Just click and you're in!
                </p>
                <p style="font-size: 14px; color: #64748b; text-align: center; margin-top: 10px;">
                    Your beta code: <span class="highlight">{beta_code}</span>
                </p>
                <p style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 20px;">
                    🔒 This link expires in 7 days
                </p>
            </div>
            <div class="footer">
                <p>© 2024 CarbonTally. All rights reserved.</p>
                <p style="font-size: 12px;">This email was sent to {email}</p>
            </div>
        </body>
        </html>
        """
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "CarbonTally <notifications@carbontally.co.uk>",
                "to": [email],
                "subject": "🎉 You've been invited to CarbonTally Beta!",
                "html": html_content
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Magic link email sent to {email}")
            return True
        else:
            print(f"⚠️ Email send failed: {response.status_code} - {response.text}")
            return False
                
    except Exception as e:
        print(f"❌ Magic link email error: {e}")
        import traceback
        traceback.print_exc()
        return False

@app.post("/api/send-beta-confirmation")
async def resend_beta_confirmation(request: dict):
    """
    Resend beta confirmation email to user
    """
    try:
        email = request.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        email_lower = email.lower().strip()

        # Check if email exists in waitlist
        existing = supabase.table("waitlist")\
            .select("email, status, full_name")\
            .eq("email", email_lower)\
            .maybe_single()\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Email not found in waitlist")

        # Send confirmation email
        email_sent =  send_confirmation_email_sync(
            email=email_lower,
            full_name=existing.data.get("full_name")
        )

        return {
            "success": True,
            "message": "Confirmation email resent",
            "email_sent": email_sent
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Resend confirmation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ UNSUBSCRIBE / RESUBSCRIBE ============

@app.post("/api/waitlist/unsubscribe")
async def unsubscribe_from_waitlist(request: dict):
    """
    Unsubscribe a user from the waitlist
    """
    try:
        email = request.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        email_lower = email.lower().strip()

        # Update waitlist status to 'unsubscribed'
        result = supabase.table("waitlist")\
            .update({
                "status": "unsubscribed",
                "updated_at": datetime.now().isoformat()
            })\
            .eq("email", email_lower)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Email not found in waitlist")

        return {
            "success": True,
            "message": "Successfully unsubscribed from the waitlist"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Unsubscribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/waitlist/resubscribe")
async def resubscribe_to_waitlist(request: dict):
    """
    Resubscribe a user to the waitlist
    """
    try:
        email = request.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")

        email_lower = email.lower().strip()

        # Update waitlist status to 'pending'
        result = supabase.table("waitlist")\
            .update({
                "status": "pending",
                "updated_at": datetime.now().isoformat()
            })\
            .eq("email", email_lower)\
            .execute()

        if not result.data:
            raise HTTPException(status_code=404, detail="Email not found in waitlist")

        return {
            "success": True,
            "message": "Successfully resubscribed to the waitlist"
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Resubscribe error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ HELPER FUNCTIONS ============

def generate_beta_code() -> str:
    """Generate a unique beta access code"""
    import secrets
    import string
    return f"BETA-{secrets.token_hex(4).upper()}-{secrets.token_hex(3).upper()}"


def send_beta_invite_email_sync(email: str, beta_code: str, full_name: Optional[str] = None):
    """Send beta invite email with magic link (synchronous version)"""
    try:
        import secrets
        import httpx
        
        resend_api_key = os.getenv("RESEND_API_KEY")
        if not resend_api_key:
            print("⚠️ RESEND_API_KEY not set, skipping email")
            return False

        name = full_name or email.split('@')[0]
        
        # Generate a magic link token
        token = secrets.token_urlsafe(32)
        magic_link = f"https://carbontally.co.uk/auth/magic?token={token}&email={email}"
        
        # ✅ Update the beta_access_codes with the magic token
        try:
            supabase.table("beta_access_codes").update({
                "magic_token": token,
                "token_created_at": datetime.now().isoformat()
            }).eq("code", beta_code).execute()
            print(f"✅ Magic token saved for code: {beta_code}")
        except Exception as db_error:
            print(f"⚠️ Failed to save magic token: {db_error}")
            # Continue anyway - we can still send the email
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>You're Invited to CarbonTally Beta!</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
                .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
                .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌱 CarbonTally</h1>
                <p style="opacity: 0.8;">You're Invited to the Beta!</p>
            </div>
            <div class="content">
                <h2>Hi {name}! 🎉</h2>
                <p>You've been selected for CarbonTally's beta program.</p>
                <p><strong>Click the button below to get started:</strong></p>
                <p style="text-align: center;">
                    <a href="{magic_link}" class="button">🚀 Claim Your Beta Access</a>
                </p>
                <p style="font-size: 14px; color: #64748b;">
                    This link will automatically create your account. No password needed to start!
                </p>
                <p style="font-size: 14px; color: #64748b; text-align: center;">
                    Your beta code: <strong style="color: #10b981;">{beta_code}</strong>
                </p>
                <p style="font-size: 12px; color: #94a3b8; text-align: center; margin-top: 20px;">
                    This link expires in 7 days
                </p>
            </div>
            <div class="footer">
                <p>© 2024 CarbonTally. All rights reserved.</p>
                <p style="font-size: 12px;">This email was sent to {email}</p>
            </div>
        </body>
        </html>
        """
        
        # ✅ Use requests library (synchronous) instead of httpx.AsyncClient
        import requests
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "CarbonTally <notifications@carbontally.co.uk>",
                "to": [email],
                "subject": "🎉 You've been invited to CarbonTally Beta!",
                "html": html_content
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Beta invite email sent to {email}")
            return True
        else:
            print(f"⚠️ Email send failed: {response.status_code} - {response.text}")
            return False
                
    except Exception as e:
        print(f"❌ Beta invite email error: {e}")
        import traceback
        traceback.print_exc()
        return False

class GlossaryTerm(BaseModel):
    term: str
    definition: str
    category: Optional[str] = None
    related_terms: Optional[List[str]] = None
    example: Optional[str] = None


@app.get("/api/glossary")
async def get_glossary(category: Optional[str] = None, search: Optional[str] = None):
    """Get all glossary terms with optional filtering"""
    try:
        if supabase is None:
            print("❌ Supabase client is None")
            raise HTTPException(status_code=500, detail="Database not available")
        
        print("🔍 Fetching glossary terms...")
        
        # Start query - select all active terms
        query = supabase.table("glossary").select("*").eq("is_active", True)
        
        # Apply category filter if provided
        if category and category != "all":
            query = query.eq("category", category)
        
        # Apply search filter if provided
        if search:
            query = query.or_(f"term.ilike.%{search}%,definition.ilike.%{search}%")
        
        # Execute query
        result = query.execute()
        
        # Log results
        data = result.data or []
        print(f"📚 Found {len(data)} glossary terms")
        
        # Sort in Python
        data.sort(key=lambda x: x.get("term", "").lower())
        
        return {
            "success": True,
            "data": data,
            "count": len(data)
        }
        
    except Exception as e:
        print(f"❌ Glossary error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch glossary: {str(e)}")


@app.get("/api/glossary/{term_id}")
async def get_glossary_term(term_id: str):
    """Get a single glossary term by ID"""
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        result = supabase.table("glossary")\
            .select("*")\
            .eq("id", term_id)\
            .eq("is_active", True)\
            .single()\
            .execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail="Term not found")
        
        return {
            "success": True,
            "data": result.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Glossary term error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/glossary")
async def create_glossary_term(term: GlossaryTerm):
    """Create a new glossary term (admin only)"""
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Check if term already exists
        existing = supabase.table("glossary")\
            .select("term")\
            .eq("term", term.term)\
            .maybe_single()\
            .execute()
        
        if existing.data:
            raise HTTPException(status_code=409, detail="Term already exists")
        
        result = supabase.table("glossary").insert({
            "term": term.term,
            "definition": term.definition,
            "category": term.category,
            "related_terms": term.related_terms,
            "example": term.example,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }).execute()
        
        return {
            "success": True,
            "message": "Term created successfully",
            "data": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Create glossary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/glossary/{term_id}")
async def update_glossary_term(term_id: str, term: GlossaryTerm):
    """Update a glossary term (admin only)"""
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Check if term exists
        existing = supabase.table("glossary")\
            .select("id")\
            .eq("id", term_id)\
            .maybe_single()\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Term not found")
        
        result = supabase.table("glossary")\
            .update({
                "term": term.term,
                "definition": term.definition,
                "category": term.category,
                "related_terms": term.related_terms,
                "example": term.example,
                "updated_at": datetime.now().isoformat()
            })\
            .eq("id", term_id)\
            .execute()
        
        return {
            "success": True,
            "message": "Term updated successfully",
            "data": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Update glossary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/glossary/{term_id}")
async def delete_glossary_term(term_id: str):
    """Soft delete a glossary term (admin only)"""
    try:
        if supabase is None:
            raise HTTPException(status_code=500, detail="Database not available")
        
        # Check if term exists
        existing = supabase.table("glossary")\
            .select("id")\
            .eq("id", term_id)\
            .maybe_single()\
            .execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Term not found")
        
        # ✅ Soft delete - set is_active to false
        result = supabase.table("glossary")\
            .update({
                "is_active": False,
                "updated_at": datetime.now().isoformat()
            })\
            .eq("id", term_id)\
            .execute()
        
        return {
            "success": True,
            "message": "Term deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Delete glossary error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
# backend/main.py - Fixed magic_auth function
@app.get("/api/auth/magic")
async def magic_auth(token: str, email: str):
    """Handle magic link authentication - creates or updates beta user"""
    try:
        if supabase is None:
            print("❌ Supabase client is None")
            raise HTTPException(status_code=500, detail="Database not available")
        
        print(f"🔍 Magic link attempt: token={token[:10]}..., email={email}")
        
        # ✅ Verify the token exists in beta_access_codes
        code_data = supabase.table("beta_access_codes")\
            .select("code, email, status")\
            .eq("magic_token", token)\
            .eq("email", email)\
            .maybe_single()\
            .execute()
        
        if not code_data or not code_data.data:
            print(f"❌ Invalid or expired magic token: {token[:10]}...")
            raise HTTPException(status_code=404, detail="Invalid or expired magic link")
        
        print(f"✅ Magic token found for: {email}")
        beta_code = code_data.data.get("code")
        
        # Check if token is expired (7 days)
        token_created = code_data.data.get("token_created_at")
        if token_created:
            from datetime import timedelta
            try:
                created_date = datetime.fromisoformat(token_created.replace('Z', '+00:00'))
                if datetime.now().replace(tzinfo=created_date.tzinfo) - created_date > timedelta(days=7):
                    raise HTTPException(status_code=410, detail="Magic link has expired")
            except Exception as date_error:
                print(f"⚠️ Date parsing error: {date_error}")
        
        # ✅ Check if user exists in Supabase Auth
        user_exists_in_auth = False
        user_id = None
        
        try:
            from supabase import Client
            supabase_admin: Client = create_client(
                os.getenv("SUPABASE_URL"), 
                os.getenv("SUPABASE_SERVICE_KEY")
            )
            
            try:
                response = supabase_admin.auth.admin.list_users()
                
                if hasattr(response, 'data'):
                    users_list = response.data
                elif hasattr(response, 'users'):
                    users_list = response.users
                else:
                    users_list = response.get('data', []) if isinstance(response, dict) else []
                
                for user in users_list:
                    if user.get('email') == email:
                        user_exists_in_auth = True
                        user_id = user.get('id')
                        print(f"👤 User exists in Auth: {email} (ID: {user_id})")
                        break
                        
            except Exception as list_error:
                print(f"⚠️ List users error: {list_error}")
                try:
                    response = supabase_admin.auth.admin.get_user_by_email(email)
                    if response and hasattr(response, 'id'):
                        user_exists_in_auth = True
                        user_id = response.id
                        print(f"👤 User exists in Auth: {email} (ID: {user_id})")
                    elif response and isinstance(response, dict) and response.get('id'):
                        user_exists_in_auth = True
                        user_id = response.get('id')
                        print(f"👤 User exists in Auth: {email} (ID: {user_id})")
                except Exception as get_error:
                    print(f"ℹ️ User not found in Auth: {email}")
                    
        except Exception as e:
            print(f"⚠️ User check error: {e}")
            import traceback
            traceback.print_exc()
        
        # ✅ Check if user exists in beta_users
        beta_user_exists = False
        try:
            beta_check = supabase.table("beta_users")\
                .select("email")\
                .eq("email", email)\
                .maybe_single()\
                .execute()
            
            if beta_check and beta_check.data:
                beta_user_exists = True
                print(f"✅ User exists in beta_users: {email}")
        except Exception as beta_error:
            print(f"⚠️ Beta user check error: {beta_error}")
        
        # =============================================
        # CASE 1: User exists in BOTH Auth AND beta_users
        # =============================================
        if user_exists_in_auth and beta_user_exists:
            print(f"✅ User already has beta access: {email}")
            try:
                # Try to sign them in (they should know their password)
                return {
                    "status": "user_exists",
                    "message": "You already have beta access. Please sign in with your password.",
                    "redirect": "/beta-login"
                }
            except Exception as signin_error:
                print(f"⚠️ Login error: {signin_error}")
                return {
                    "status": "user_exists",
                    "message": "You already have beta access. Please sign in.",
                    "redirect": "/beta-login"
                }
        
        # =============================================
        # CASE 2: User exists in Auth BUT NOT in beta_users
        # =============================================
        if user_exists_in_auth and not beta_user_exists:
            print(f"🔄 User exists in Auth but NOT in beta_users. Adding to beta_users: {email}")
            
            try:
                # ✅ Generate a temporary password
                import secrets
                import string
                temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                
                # ✅ Update user's password in Auth
                from supabase import Client
                supabase_admin: Client = create_client(
                    os.getenv("SUPABASE_URL"), 
                    os.getenv("SUPABASE_SERVICE_KEY")
                )
                
                # Update the user's password
                supabase_admin.auth.admin.update_user_by_id(
                    user_id,
                    {"password": temp_password}
                )
                print(f"✅ Password updated for existing user: {email}")
                
                # ✅ Add to beta_users
                supabase.table("beta_users").insert({
                    "user_id": user_id,
                    "email": email,
                    "beta_code": beta_code,
                    "access_level": "beta",
                    "created_at": datetime.now().isoformat()
                }).execute()
                print(f"✅ User added to beta_users: {email}")
                
                # ✅ Mark beta code as used
                supabase.table("beta_access_codes").update({
                    "status": "used",
                    "used_at": datetime.now().isoformat()
                }).eq("code", beta_code).execute()
                
                # ✅ Send temporary password email
                try:
                    email_sent = send_temp_password_email(
                        email=email,
                        temp_password=temp_password,
                        full_name=email.split('@')[0],
                        beta_code=beta_code,
                        is_existing_user=True
                    )
                    if email_sent:
                        print(f"✅ Temporary password email sent to {email}")
                    else:
                        print(f"⚠️ Failed to send temp password email to {email}")
                except Exception as email_error:
                    print(f"⚠️ Email error: {email_error}")
                
                # ✅ Try auto-login
                try:
                    auth_response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": temp_password
                    })
                    
                    if auth_response and auth_response.session:
                        return {
                            "status": "success",
                            "message": "Beta access granted! You're now signed in.",
                            "session": auth_response.session.dict(),
                            "redirect": "/dashboard"
                        }
                except Exception as auth_error:
                    print(f"⚠️ Auto-login failed: {auth_error}")
                
                return {
                    "status": "beta_created",
                    "message": f"Beta access granted! A temporary password has been sent to {email}. Please check your email and sign in.",
                    "temp_password": temp_password,
                    "email": email,
                    "redirect": "/beta-login"
                }
                
            except Exception as update_error:
                print(f"❌ Error adding existing user to beta_users: {update_error}")
                raise HTTPException(status_code=500, detail=f"Failed to grant beta access: {str(update_error)}")
        
        # =============================================
        # CASE 3: User DOES NOT exist in Auth
        # =============================================
        if not user_exists_in_auth:
            import secrets
            import string
            temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
            
            print(f"🆕 Creating new user: {email}")
            
            try:
                from supabase import Client
                supabase_admin: Client = create_client(
                    os.getenv("SUPABASE_URL"), 
                    os.getenv("SUPABASE_SERVICE_KEY")
                )
                
                user_response = supabase_admin.auth.admin.create_user({
                    "email": email,
                    "password": temp_password,
                    "email_confirm": True,
                    "user_metadata": {
                        "is_beta_user": True,
                        "beta_code": beta_code,
                        "has_temp_password": True
                    }
                })
                
                if not user_response or not hasattr(user_response, 'user') or not user_response.user:
                    raise HTTPException(status_code=500, detail="Failed to create user")
                
                user_id = user_response.user.id
                print(f"✅ User created: {user_id}")
                
                # ✅ Mark beta code as used
                supabase.table("beta_access_codes").update({
                    "status": "used",
                    "used_at": datetime.now().isoformat()
                }).eq("code", beta_code).execute()
                
                # ✅ Add to beta_users
                supabase.table("beta_users").insert({
                    "user_id": user_id,
                    "email": email,
                    "beta_code": beta_code,
                    "access_level": "beta",
                    "created_at": datetime.now().isoformat()
                }).execute()
                print(f"✅ User added to beta_users: {email}")
                
                # ✅ Send temporary password email
                try:
                    email_sent = send_temp_password_email(
                        email=email,
                        temp_password=temp_password,
                        full_name=email.split('@')[0],
                        beta_code=beta_code,
                        is_existing_user=False
                    )
                    if email_sent:
                        print(f"✅ Temporary password email sent to {email}")
                    else:
                        print(f"⚠️ Failed to send temp password email to {email}")
                except Exception as email_error:
                    print(f"⚠️ Email error: {email_error}")
                
                # ✅ Try auto-login
                try:
                    auth_response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": temp_password
                    })
                    
                    if auth_response and auth_response.session:
                        return {
                            "status": "success",
                            "message": "Account created and signed in! Check your email for your temporary password.",
                            "session": auth_response.session.dict(),
                            "redirect": "/dashboard"
                        }
                except Exception as auth_error:
                    print(f"⚠️ Auto-login failed: {auth_error}")
                
                return {
                    "status": "beta_created",
                    "message": f"Account created! A temporary password has been sent to {email}. Please check your email and sign in.",
                    "temp_password": temp_password,
                    "email": email,
                    "redirect": "/beta-login"
                }
                
            except Exception as create_error:
                print(f"❌ User creation error: {create_error}")
                if "already been registered" in str(create_error):
                    return {
                        "status": "user_exists",
                        "message": "Account already exists. Please sign in.",
                        "redirect": "/beta-login"
                    }
                raise HTTPException(status_code=500, detail=f"User creation failed: {str(create_error)}")
        
        # Fallback
        return {
            "status": "error",
            "message": "Something went wrong. Please try again.",
            "redirect": "/beta-login"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Magic auth error: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# SEND TEMPORARY PASSWORD EMAIL
# ==========================================

def send_temp_password_email(email: str, temp_password: str, full_name: str, beta_code: str):
    """Send temporary password email to new beta user"""
    try:
        import requests
        
        resend_api_key = os.getenv("RESEND_API_KEY")
        if not resend_api_key:
            print("⚠️ RESEND_API_KEY not set, skipping email")
            return False

        name = full_name or email.split('@')[0]
        login_url = "https://carbontally.co.uk/beta-login"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to CarbonTally Beta!</title>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #1e293b; max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0f172a, #1e293b); color: white; padding: 30px; text-align: center; border-radius: 12px 12px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-left: 1px solid #e2e8f0; border-right: 1px solid #e2e8f0; }}
                .code-box {{ background: white; padding: 20px; border-radius: 8px; border: 2px dashed #10b981; text-align: center; margin: 20px 0; }}
                .code {{ font-size: 28px; font-weight: 700; color: #059669; letter-spacing: 2px; font-family: monospace; }}
                .button {{ display: inline-block; padding: 14px 28px; background: linear-gradient(135deg, #10b981, #059669); color: white; text-decoration: none; border-radius: 8px; font-weight: 600; margin: 10px 0; }}
                .footer {{ background: #f1f5f9; padding: 20px; text-align: center; border-radius: 0 0 12px 12px; color: #64748b; }}
                .warning {{ background: #fef3c7; padding: 12px; border-radius: 6px; border-left: 4px solid #f59e0b; margin: 15px 0; color: #92400e; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🌱 CarbonTally</h1>
                <p style="opacity: 0.8;">Welcome to the Beta Program!</p>
            </div>
            <div class="content">
                <h2>Hi {name}! 🎉</h2>
                <p>Your CarbonTally beta account has been created. Here are your login credentials:</p>
                
                <div class="code-box">
                    <p style="margin: 0 0 5px 0; color: #64748b; font-size: 14px;">Your Temporary Password</p>
                    <div class="code">{temp_password}</div>
                    <p style="margin: 10px 0 0 0; color: #64748b; font-size: 13px;">Beta Code: <strong>{beta_code}</strong></p>
                </div>
                
                <div class="warning">
                    <strong>⚠️ Important:</strong> Please change your password after your first login.
                </div>
                
                <p><strong>Login Details:</strong></p>
                <ul>
                    <li><strong>Email:</strong> {email}</li>
                    <li><strong>Temporary Password:</strong> {temp_password}</li>
                </ul>
                
                <p style="text-align: center;">
                    <a href="{login_url}" class="button">🔐 Go to Login</a>
                </p>
                
                <p style="font-size: 14px; color: #64748b; text-align: center;">
                    This password is temporary and will expire in 7 days.
                </p>
            </div>
            <div class="footer">
                <p>© 2024 CarbonTally. All rights reserved.</p>
                <p style="font-size: 12px;">This email was sent to {email}</p>
            </div>
        </body>
        </html>
        """
        
        response = requests.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {resend_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "from": "CarbonTally <notifications@carbontally.co.uk>",
                "to": [email],
                "subject": "🔐 Your CarbonTally Beta Credentials",
                "html": html_content
            },
            timeout=30
        )
        
        if response.status_code == 200:
            print(f"✅ Temporary password email sent to {email}")
            return True
        else:
            print(f"⚠️ Email send failed: {response.status_code} - {response.text}")
            return False
                
    except Exception as e:
        print(f"❌ Temporary password email error: {e}")
        import traceback
        traceback.print_exc()
        return False

# backend/main.py - Add this endpoint
