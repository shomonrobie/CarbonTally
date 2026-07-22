from dotenv import load_dotenv
import os

load_dotenv()
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# DEBUG PRINTS (We will remove these later)
print("🔍 DEBUG: SUPABASE_URL is", os.getenv("SUPABASE_URL"))
print("🔍 DEBUG: SUPABASE_SERVICE_KEY is", "SET" if os.getenv("SUPABASE_SERVICE_KEY") else "MISSING")
import base64
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io
from pydantic import BaseModel
from pdf_engine import PDFExtractor
import resend
from typing import List
from datetime import datetime
import traceback
from fpdf import FPDF
import re
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
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# OFFICIAL UK DEFRA CONVERSION FACTORS
DEFRA_FACTORS = {
    # Scope 1: Transport Fuel (kgCO2e per Litre)
    'Diesel': 2.54,
    'Petrol': 2.16,
    'AdBlue': 0.0,
    'Unknown Fuel': 0.0,
    
    # Scope 2: Utilities (kgCO2e per kWh)
    'Electricity': 0.20712, 
    'Natural Gas': 0.18316,
    'Unknown Utility': 0.0,

    # Scope 3: Travel & Waste
    'Flight (Short Haul)': 0.25496,
    'Flight (Long Haul)': 0.19534,
    'Rail (National)': 0.03546,
    'Hotel Stay': 19.50000,
    'Mixed Waste': 0.57000,
    'Recycled Waste': -0.45000,
    'Unknown Scope 3': 0.0,
}

# ==========================================
# CSV PROCESSING FUNCTIONS
# ==========================================

def process_fuel_data(df: pd.DataFrame) -> tuple:
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
        return 'Unknown Fuel'

    df['Standardized Fuel'] = df['Fuel Type'].apply(normalize_fuel)
    df['DEFRA Factor (kgCO2e/L)'] = df['Standardized Fuel'].map(DEFRA_FACTORS)
    df['Total kgCO2e'] = (df['Volume (L)'] * df['DEFRA Factor (kgCO2e/L)']).round(2).fillna(0)
    
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Volume (L)'].isna(), 'needs_review'] = True
    df.loc[df['Volume (L)'].isna(), 'review_reason'] = 'Missing Volume'
    df.loc[df['Standardized Fuel'] == 'Unknown Fuel', 'needs_review'] = True
    df.loc[df['Standardized Fuel'] == 'Unknown Fuel', 'review_reason'] = 'Unrecognized Fuel Type'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Transaction Date', 'Vehicle Registration', 'Standardized Fuel', 'Volume (L)', 'DEFRA Factor (kgCO2e/L)', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())


def process_utility_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'period' in c.lower()), 'Billing Period Start')
    site_col = next((c for c in df.columns if 'site' in c.lower() or 'facility' in c.lower() or 'location' in c.lower()), 'Site Name')
    vol_col = next((c for c in df.columns if 'consumption' in c.lower() or 'kwh' in c.lower() or 'usage' in c.lower()), 'Consumption (kWh)')
    type_col = next((c for c in df.columns if 'type' in c.lower() or 'utility' in c.lower() or 'meter' in c.lower()), 'Utility Type')
    
    df = df.rename(columns={date_col: 'Billing Period Start', site_col: 'Site Name', vol_col: 'Consumption (kWh)', type_col: 'Utility Type'})
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
        return 'Unknown Utility'

    df['Standardized Utility'] = df['Utility Type'].apply(normalize_utility_type)
    df['DEFRA Factor (kgCO2e/kWh)'] = df['Standardized Utility'].map(DEFRA_FACTORS)
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
    clean_columns = ['Billing Period Start', 'Site Name', 'Standardized Utility', 'Consumption (kWh)', 'DEFRA Factor (kgCO2e/kWh)', 'Total kgCO2e', 'needs_review', 'review_reason']
    if 'Cost (£)' in df.columns:
        clean_columns.insert(4, 'Cost (£)')
        
    return df[[c for c in clean_columns if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())


def process_scope3_data(df: pd.DataFrame) -> tuple:
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
        if 'flight' in cat_str or 'air' in cat_str: return 'Flight (Long Haul)' if 'long' in cat_str else 'Flight (Short Haul)'
        if 'rail' in cat_str or 'train' in cat_str: return 'Rail (National)'
        if 'hotel' in cat_str or 'stay' in cat_str: return 'Hotel Stay'
        if 'waste' in cat_str or 'rubbish' in cat_str: return 'Recycled Waste' if 'recycle' in cat_str else 'Mixed Waste'
        return 'Unknown Scope 3'

    df['Standardized Scope3'] = df['Category'].apply(normalize_scope3)
    df['DEFRA Factor'] = df['Standardized Scope3'].map(DEFRA_FACTORS)
    df['Total kgCO2e'] = (df['Quantity'] * df['DEFRA Factor']).round(2).fillna(0)
    
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Quantity'].isna(), 'needs_review'] = True
    df.loc[df['Quantity'].isna(), 'review_reason'] = 'Missing Quantity'
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'needs_review'] = True
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'review_reason'] = 'Unrecognized Category'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_columns = ['Date', 'Description', 'Standardized Scope3', 'Quantity', 'DEFRA Factor', 'Total kgCO2e', 'needs_review', 'review_reason']
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
        
        # 1. Upload file to Supabase Storage
        file_path = f"manual_review/{organization_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        storage_response = supabase_client.storage.from_('documents').upload(
            file_path,
            file_bytes,
            file_options={"content-type": content_type}
        )
        
        file_url = supabase_client.storage.from_('documents').get_public_url(file_path)
        
        # 2. Insert into manual_review_queue - using your existing columns
        queue_response = supabase_client.from_('manual_review_queue').insert({
            'organization_id': organization_id if organization_id and organization_id != "mock-org-id" else None,
            'file_url': file_url,
            'file_name': filename,
            'file_type': 'PDF' if filename.lower().endswith('.pdf') else 'IMAGE',
            'data_type': data_type,
            'status': 'pending',
            'auto_extraction_result': {
                'extraction_result': auto_result,
                'extraction_issues': issues,  # Store issues inside auto_extraction_result
                'extraction_summary': summary,  # Store summary inside auto_extraction_result
                'confidence_score': summary.get('confidence_score', 0.0)
            },
            'priority': 1 if auto_result.get('status') == 'error' else 0,
            'customer_notes': f"Auto-extraction failed. File: {filename}",
            'estimated_completion_hours': 24
        }).execute()
        
        review_id = queue_response.data[0]['id']
        
        # 3. Send email notification to founder with detailed issues
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
            
            resend.Emails.send({
                "from": "CarbonTally <notifications@carbontally.co.uk>",
                "to": [FOUNDER_EMAIL],
                "subject": f"🚨 Manual Review Required: {filename}",
                "html": f"""
                <h2 style="color: #0f172a;">Manual Review Queue Alert</h2>
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
                        <td style="padding: 8px; border: 1px solid #ddd; font-weight: bold; background: #f8fafc;">Data Type:</td>
                        <td style="padding: 8px; border: 1px solid #ddd;">{data_type}</td>
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
            })
        except Exception as email_error:
            print(f"Email notification failed: {email_error}")
        
        return review_id, issues, summary
    
    except Exception as e:
        print(f"Failed to queue for manual review: {e}")
        import traceback
        traceback.print_exc()
        raise e

def calculate_emissions_with_defra(supabase_client, activity_type: str, consumption: float, start_date: str, override_year: int = None):
    """
    Auto-detects the reporting year from the start_date, 
    but allows an override. Fetches the exact DEFRA multiplier and calculates kgCO2e.
    """
    # 1. Auto-detect year from start_date (e.g., "2025-05-15" -> 2025)
    try:
        detected_year = int(str(start_date).split('-')[0])
    except (ValueError, IndexError):
        detected_year = 2025 # Fallback if date is malformed
        
    # 2. Apply override if provided by the user
    reporting_year = override_year if override_year else detected_year
    
    # 3. Fetch the specific factor for this year and activity
    factor_res = supabase_client.from_('defra_conversion_factors') \
        .select('co2e_multiplier') \
        .eq('activity_type', activity_type) \
        .eq('reporting_year', reporting_year) \
        .single() \
        .execute()
        
    if not factor_res.data:
        raise ValueError(f"No DEFRA factor found for '{activity_type}' in year {reporting_year}. Please import the latest DEFRA data.")
        
    multiplier = float(factor_res.data['co2e_multiplier'])
    calculated_kg_co2e = round(consumption * multiplier, 4)
    
    return {
        "reporting_year": reporting_year,
        "multiplier_used": multiplier,
        "calculated_kg_co2e": calculated_kg_co2e
    }
# ==========================================
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
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        df.columns = df.columns.str.strip()
        
        if data_type == 'utility':
            clean_data, flagged_rows = process_utility_data(df)
            scope = "Scope 2"
        elif data_type == 'scope3':
            clean_data, flagged_rows = process_scope3_data(df)
            scope = "Scope 3"
        else:
            clean_data, flagged_rows = process_fuel_data(df)
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

@app.post("/upload-image")
async def upload_image(
    file: UploadFile = File(...),
    data_type: str = Form('utility'),
    organization_id: str = Form(None)
):
    if not file.filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, or PNG images are allowed.")
    
    try:
        organization_assets = [
            {"id": "1", "name": "Birmingham Hub Main Floor"},
            {"id": "2", "name": "Birmingham Hub Unit 4"}
        ]
        
        file_bytes = await file.read()
        extraction_result = pdf_extractor.extract_and_parse_image(
            file_bytes, file.filename, data_type, organization_assets
        )
        
        # Check if extraction failed or has low confidence
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
            
            # Return detailed response with issues and summary
            return {
                "status": "manual_review_required",
                "message": "Our team will manually extract your data within 24 hours.",
                "review_id": review_id,
                "estimated_completion": "24-48 hours",
                "extraction_issues": issues,
                "extraction_summary": summary,
                "confidence_score": summary.get("confidence_score", 0.0)
            }
        
        # If extraction was successful, return the result
        return extraction_result
    
    except Exception as e:
        print(f"--- IMAGE EXTRACTION ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Image extraction failed: {str(e)}")

@app.post("/upload-batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    batch_name: str = Form(...),
    data_type: str = Form('mixed'),
    organization_id: str = Form(...),
    special_instructions: str = Form('')  # 👈 ADD THIS PARAMETER
):
    """
    Accept multiple files at once and create a batch for processing.
    """
    try:
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        batch_response = supabase_client.from_('upload_batches').insert({
            'organization_id': organization_id,
            'batch_name': batch_name,
            'total_files': len(files),
            'processed_files': 0,
            'status': 'processing',
            'metadata': {'data_type': data_type, 'special_instructions': special_instructions}
        }).execute()
        
        batch_id = batch_response.data[0]['id']
        
        processed_count = 0
        failed_files = []
        
        for file in files:
            try:
                file_bytes = await file.read()
                file_path = f"batches/{organization_id}/{batch_id}/{file.filename}"
                
                supabase_client.storage.from_('documents').upload(
                    file_path,
                    file_bytes,
                    file_options={"content-type": file.content_type}
                )
                
                file_url = supabase_client.storage.from_('documents').get_public_url(file_path)
                
                file_type = 'PDF' if file.filename.lower().endswith('.pdf') else 'IMAGE'
                actual_data_type = data_type if data_type != 'mixed' else 'utility'
                
                if file_type == 'PDF':
                    extraction_result = pdf_extractor.extract_and_parse(
                        file_bytes, file.filename, actual_data_type, []
                    )
                else:
                    extraction_result = pdf_extractor.extract_and_parse_image(
                        file_bytes, file.filename, actual_data_type, []
                    )
                
                if extraction_result.get("status") == "error" or has_low_confidence(extraction_result):
                    issues, summary = extract_issues_from_result(extraction_result, actual_data_type)
                    
                    # 👇 BUILD THE CUSTOMER NOTE WITH SPECIAL INSTRUCTIONS
                    base_note = f"Batch upload: {batch_name}. File: {file.filename}"
                    if special_instructions.strip():
                        base_note += f" | 📝 CUSTOMER NOTE: {special_instructions.strip()}"
                    
                    supabase_client.from_('manual_review_queue').insert({
                        'organization_id': organization_id,
                        'batch_id': batch_id,
                        'file_url': file_url,
                        'file_name': file.filename,
                        'file_type': file_type,
                        'data_type': actual_data_type,
                        'status': 'pending',
                        'auto_extraction_result': extraction_result,
                        'extraction_issues': issues,
                        'extraction_summary': summary,
                        'priority': 1 if extraction_result.get('status') == 'error' else 0,
                        'customer_notes': base_note  # 👈 NOW INCLUDES SPECIAL INSTRUCTIONS
                    }).execute()
                
                processed_count += 1
                
            except Exception as file_error:
                print(f"Error processing file {file.filename}: {file_error}")
                failed_files.append(file.filename)
                continue
        
        final_status = 'completed' if len(failed_files) == 0 else 'partial'
        supabase_client.from_('upload_batches').update({
            'processed_files': processed_count,
            'status': final_status,
            'completed_at': datetime.now().isoformat(),
            'metadata': {
                'data_type': data_type,
                'special_instructions': special_instructions,
                'failed_files': failed_files
            }
        }).eq('id', batch_id).execute()
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "message": f"Successfully uploaded {processed_count}/{len(files)} files",
            "batch_name": batch_name,
            "failed_files": failed_files
        }
        
    except Exception as e:
        print(f"--- BATCH UPLOAD ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")


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
        
        try:
            resend.Emails.send({
                "from": "CarbonTally <notifications@carbontally.co.uk>",
                "to": [customer_email],
                "subject": f"✅ Your Bulk Upload is Ready: {batch_name}",
                "html": f"""
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
                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 2rem 0;">
                    <p style="color: #94a3b8; font-size: 0.75rem; text-align: center;">
                      This is an automated message from CarbonTally.
                    </p>
                  </div>
                </div>
                """
            })
            return {"status": "success", "message": f"Batch completion email sent to {customer_email}"}
        
        except Exception as email_error:
            print(f"Email notification failed: {email_error}")
            return {"status": "warning", "message": "Batch marked complete, but email failed"}
    
    except Exception as e:
        print(f"--- BATCH NOTIFICATION ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Batch notification failed: {str(e)}")
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

# class SECRReportPDF(FPDF):
#     def __init__(self, org_name, reporting_year):
#         super().__init__()
#         self.org_name = org_name
#         self.reporting_year = reporting_year
#         # Add a Unicode font (you'll need to download this)
#         # For now, we'll use the built-in fonts and avoid special characters
        
#     def header(self):
#         # Add a subtle header line
#         self.set_draw_color(200, 200, 200)
#         self.line(10, 10, 200, 10)
        
#     def footer(self):
#         self.set_y(-15)
#         self.set_font('Helvetica', 'I', 8)
#         self.set_text_color(128, 128, 128)
#         self.cell(0, 10, f'Page {self.page_no()} | Generated by CarbonTally', 0, 0, 'C')

# # Helper function to sanitize text (remove emojis and special characters)
# def sanitize_text(text):
#     """Remove emojis and non-latin-1 characters from text"""
#     if not text:
#         return text
#     # Remove emoji characters (simple approach)
#     # This regex removes most emojis and special Unicode symbols
#     import re
#     # Remove emoji and other non-latin-1 characters
#     emoji_pattern = re.compile("["
#         u"\U0001F600-\U0001F64F"  # emoticons
#         u"\U0001F300-\U0001F5FF"  # symbols & pictographs
#         u"\U0001F680-\U0001F6FF"  # transport & map symbols
#         u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
#         u"\U00002500-\U00002BEF"  # chinese char
#         u"\U00002702-\U000027B0"
#         u"\U000024C2-\U0001F251"
#         u"\U0001f926-\U0001f937"
#         u"\U00010000-\U0010ffff"
#         u"\u2640-\u2642" 
#         u"\u2600-\u2B55"
#         u"\u200d"
#         u"\u23cf"
#         u"\u23e9"
#         u"\u231a"
#         u"\ufe0f"  # dingbats
#         u"\u3030"
#         "]+", flags=re.UNICODE)
#     return emoji_pattern.sub('', text)
# @app.post("/generate-secr-report")
# async def generate_secr_report(report_data: dict):
#     """
#     Generate a branded SECR compliance report PDF for the organization.
#     """
#     try:
#         from supabase import create_client
#         supabase_url = os.getenv("SUPABASE_URL")
#         supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
#         supabase_client = create_client(supabase_url, supabase_key)
        
#         organization_id = report_data.get("organization_id")
#         requested_year = report_data.get("reporting_year", datetime.now().year)
        
#         print(f"📊 Generating report for organization: {organization_id}, year: {requested_year}")
        
#         # 1. Fetch organization details
#         org_res = supabase_client.from_('organizations')\
#             .select('name, company_number')\
#             .eq('id', organization_id)\
#             .single()\
#             .execute()
        
#         if not org_res.data:
#             raise HTTPException(status_code=404, detail="Organization not found")
            
#         org_name = sanitize_text(org_res.data['name'])
#         company_number = sanitize_text(org_res.data.get('company_number', 'N/A'))
        
#         # 2. Fetch ALL emissions data for the specific year (with pagination)
#         print(f"🔍 Fetching emissions data for year: {requested_year}")
        
#         all_emissions_data = []
#         has_more = True
#         page = 0
#         page_size = 1000
        
#         while has_more:
#             start = page * page_size
#             end = (page + 1) * page_size - 1
            
#             emissions_res = supabase_client.from_('emissions_logs')\
#                 .select('*, defra_conversion_factors(activity_type, co2e_multiplier, reporting_year), assets(name)')\
#                 .eq('organization_id', organization_id)\
#                 .gte('start_date', f'{requested_year}-01-01')\
#                 .lte('start_date', f'{requested_year}-12-31')\
#                 .range(start, end)\
#                 .execute()
            
#             if emissions_res.data:
#                 all_emissions_data.extend(emissions_res.data)
#                 page += 1
                
#                 if len(emissions_res.data) < page_size:
#                     has_more = False
#             else:
#                 has_more = False
        
#         emissions_data = all_emissions_data
#         print(f"📊 Found {len(emissions_data)} records for {requested_year}")
        
#         # If no data for the requested year, try to find the most recent year with data
#         if len(emissions_data) == 0:
#             print(f"⚠️ No data for {requested_year}, checking for available years...")
            
#             # Get all years with data
#             all_years_res = supabase_client.from_('emissions_logs')\
#                 .select('start_date')\
#                 .eq('organization_id', organization_id)\
#                 .execute()
            
#             if all_years_res.data:
#                 years_available = sorted(set([row['start_date'][:4] for row in all_years_res.data if row.get('start_date')]))
#                 if years_available:
#                     most_recent_year = years_available[-1]
#                     print(f"📊 Using most recent year with data: {most_recent_year}")
                    
#                     # Fetch ALL data for the most recent year with pagination
#                     all_emissions_data = []
#                     has_more = True
#                     page = 0
                    
#                     while has_more:
#                         start = page * page_size
#                         end = (page + 1) * page_size - 1
                        
#                         emissions_res = supabase_client.from_('emissions_logs')\
#                             .select('*, defra_conversion_factors(activity_type, co2e_multiplier, reporting_year), assets(name)')\
#                             .eq('organization_id', organization_id)\
#                             .gte('start_date', f'{most_recent_year}-01-01')\
#                             .lte('start_date', f'{most_recent_year}-12-31')\
#                             .range(start, end)\
#                             .execute()
                        
#                         if emissions_res.data:
#                             all_emissions_data.extend(emissions_res.data)
#                             page += 1
                            
#                             if len(emissions_res.data) < page_size:
#                                 has_more = False
#                         else:
#                             has_more = False
                    
#                     emissions_data = all_emissions_data
#                     requested_year = most_recent_year
#                     print(f"📊 Found {len(emissions_data)} records for {requested_year}")
        
#         # 3. Calculate totals by scope
#         scope_totals = {'Scope 1': 0, 'Scope 2': 0, 'Scope 3': 0}
#         total_emissions = 0
        
#         for record in emissions_data:
#             kg_co2e = float(record.get('calculated_kg_co2e', 0))
#             total_emissions += kg_co2e
            
#             # Get scope from metadata
#             metadata = record.get('metadata', {})
#             if metadata:
#                 scope = metadata.get('scope', '')
#                 if 'Scope 1' in scope:
#                     scope_totals['Scope 1'] += kg_co2e
#                 elif 'Scope 2' in scope:
#                     scope_totals['Scope 2'] += kg_co2e
#                 elif 'Scope 3' in scope:
#                     scope_totals['Scope 3'] += kg_co2e
#                 else:
#                     # Fallback: try to determine from fuel type
#                     fuel_type = metadata.get('fuel_type', '')
#                     if fuel_type in ['Diesel', 'Diesel (DERV)', 'Petrol', 'Petrol (Unleaded)', 'Natural Gas', 'LPG', 'AdBlue']:
#                         scope_totals['Scope 1'] += kg_co2e
#                     elif fuel_type == 'Electricity' or fuel_type == 'UK Electricity Grid':
#                         scope_totals['Scope 2'] += kg_co2e
#                     else:
#                         scope_totals['Scope 3'] += kg_co2e
#             else:
#                 # If no metadata, try to infer from defra factor
#                 defra = record.get('defra_conversion_factors', {})
#                 activity_type = defra.get('activity_type', '')
#                 if any(fuel in activity_type for fuel in ['Diesel', 'Petrol', 'Natural Gas', 'LPG', 'AdBlue']):
#                     scope_totals['Scope 1'] += kg_co2e
#                 elif 'Electricity' in activity_type:
#                     scope_totals['Scope 2'] += kg_co2e
#                 else:
#                     scope_totals['Scope 3'] += kg_co2e
        
#         print(f"📊 Scope totals: {scope_totals}")
#         print(f"📊 Total emissions: {total_emissions}")
#         print(f"📊 Records used: {len(emissions_data)}")
        
#         # 4. Generate PDF (your existing PDF generation code continues here...)
#         # ... rest of your PDF generation code ...
        
#         pdf = SECRReportPDF(org_name, requested_year)
#         pdf.alias_nb_pages()
#         pdf.add_page()
        
#         # Title Section
#         pdf.set_font('Helvetica', 'B', 24)
#         pdf.set_text_color(15, 23, 42)
#         pdf.cell(0, 20, org_name, 0, 1, 'C')
        
#         pdf.set_font('Helvetica', '', 14)
#         pdf.set_text_color(71, 85, 105)
#         pdf.cell(0, 10, 'Streamlined Energy and Carbon Reporting (SECR)', 0, 1, 'C')
#         pdf.cell(0, 10, f'Reporting Period: 01/01/{requested_year} - 31/12/{requested_year}', 0, 1, 'C')
#         pdf.cell(0, 10, f'Company Number: {company_number}', 0, 1, 'C')
#         pdf.ln(15)
        
#         # Executive Summary
#         pdf.set_font('Helvetica', 'B', 16)
#         pdf.set_text_color(15, 23, 42)
#         pdf.cell(0, 10, 'Executive Summary', 0, 1, 'L')
#         pdf.set_draw_color(22, 163, 74)
#         pdf.line(10, pdf.get_y(), 50, pdf.get_y())
#         pdf.ln(5)
        
#         pdf.set_font('Helvetica', '', 11)
#         pdf.set_text_color(51, 65, 85)
#         summary_text = f'This report provides a comprehensive overview of {org_name} greenhouse gas emissions for the financial year {requested_year}, in compliance with the UK Streamlined Energy and Carbon Reporting (SECR) regulations.'
#         pdf.multi_cell(0, 6, sanitize_text(summary_text))
#         pdf.ln(8)
        
#         # Total Emissions Box
#         pdf.set_fill_color(240, 253, 244)
#         pdf.set_draw_color(22, 163, 74)
#         pdf.rect(10, pdf.get_y(), 190, 30, 'DF')
        
#         pdf.set_y(pdf.get_y() + 5)
#         pdf.set_font('Helvetica', 'B', 14)
#         pdf.set_text_color(22, 101, 52)
#         total_text = f'Total Emissions: {total_emissions:,.2f} kg CO2e ({total_emissions/1000:,.2f} tonnes CO2e)'
#         pdf.cell(0, 10, sanitize_text(total_text), 0, 1, 'C')
        
#         pdf.set_font('Helvetica', '', 10)
#         pdf.set_text_color(71, 85, 105)
#         record_text = f'Based on {len(emissions_data)} emission records'
#         pdf.cell(0, 8, sanitize_text(record_text), 0, 1, 'C')
#         pdf.ln(12)
        
#         # Scope Breakdown
#         pdf.set_font('Helvetica', 'B', 16)
#         pdf.set_text_color(15, 23, 42)
#         pdf.cell(0, 10, 'Emissions by Scope', 0, 1, 'L')
#         pdf.set_draw_color(22, 163, 74)
#         pdf.line(10, pdf.get_y(), 50, pdf.get_y())
#         pdf.ln(5)
        
#         # Table Header
#         pdf.set_fill_color(241, 245, 249)
#         pdf.set_font('Helvetica', 'B', 11)
#         pdf.set_text_color(15, 23, 42)
#         pdf.cell(60, 10, 'Scope', 1, 0, 'L', True)
#         pdf.cell(65, 10, 'Emissions (kg CO2e)', 1, 0, 'R', True)
#         pdf.cell(65, 10, 'Emissions (tonnes CO2e)', 1, 1, 'R', True)
        
#         # Table Rows
#         pdf.set_font('Helvetica', '', 10)
#         pdf.set_text_color(51, 65, 85)
        
#         for scope, emissions in scope_totals.items():
#             pdf.cell(60, 10, sanitize_text(scope), 1, 0, 'L')
#             pdf.cell(65, 10, f'{emissions:,.2f}', 1, 0, 'R')
#             pdf.cell(65, 10, f'{emissions/1000:,.2f}', 1, 1, 'R')
        
#         pdf.ln(10)
        
#         # Methodology
#         pdf.set_font('Helvetica', 'B', 16)
#         pdf.set_text_color(15, 23, 42)
#         pdf.cell(0, 10, 'Methodology', 0, 1, 'L')
#         pdf.set_draw_color(22, 163, 74)
#         pdf.line(10, pdf.get_y(), 50, pdf.get_y())
#         pdf.ln(5)
        
#         pdf.set_font('Helvetica', '', 10)
#         pdf.set_text_color(51, 65, 85)
#         method_text = f'Emissions have been calculated using official UK Government GHG Conversion Factors for Company Reporting ({requested_year}). All conversion factors are sourced from DEFRA and BEIS.'
#         pdf.multi_cell(0, 5, sanitize_text(method_text))
#         pdf.ln(5)
        
#         pdf.set_font('Helvetica', 'I', 9)
#         pdf.set_text_color(100, 116, 139)
#         scope_texts = [
#             'Scope 1: Direct emissions from owned or controlled sources (e.g., fuel combustion in company vehicles, natural gas heating).',
#             'Scope 2: Indirect emissions from purchased electricity, steam, heating, and cooling.',
#             'Scope 3: Other indirect emissions (e.g., business travel, waste disposal, employee commuting).'
#         ]
#         for text in scope_texts:
#             pdf.multi_cell(0, 5, sanitize_text(text))
#         pdf.ln(10)
        
#         # Compliance Statement
#         pdf.set_font('Helvetica', 'B', 16)
#         pdf.set_text_color(15, 23, 42)
#         pdf.cell(0, 10, 'Compliance Statement', 0, 1, 'L')
#         pdf.set_draw_color(22, 163, 74)
#         pdf.line(10, pdf.get_y(), 50, pdf.get_y())
#         pdf.ln(5)
        
#         pdf.set_font('Helvetica', '', 10)
#         pdf.set_text_color(51, 65, 85)
#         compliance_text = f'This report has been prepared in accordance with the Companies (Directors Report) and Limited Liability Partnerships (Energy and Carbon Report) Regulations 2018. The data has been verified and validated by CarbonTally automated extraction and review system.'
#         pdf.multi_cell(0, 5, sanitize_text(compliance_text))
#         pdf.ln(8)
        
#         pdf.set_font('Helvetica', 'B', 10)
#         pdf.set_text_color(22, 163, 74)
#         generated_text = f'Report generated on: {datetime.now().strftime("%d %B %Y at %H:%M")}'
#         pdf.cell(0, 6, sanitize_text(generated_text), 0, 1, 'L')
        
#         # Add a footer note
#         pdf.set_y(-20)
#         pdf.set_font('Helvetica', 'I', 8)
#         pdf.set_text_color(128, 128, 128)
#         pdf.cell(0, 5, 'This report is automatically generated by CarbonTally', 0, 0, 'C')
        
#         # Output PDF
#         pdf_output = pdf.output(dest='S').encode('latin-1')
#         pdf_base64 = base64.b64encode(pdf_output).decode('utf-8')
        
#         return {
#             "status": "success",
#             "pdf_base64": pdf_base64,
#             "filename": f"SECR_Report_{org_name}_{requested_year}.pdf",
#             "records_used": len(emissions_data),
#             "total_emissions": total_emissions,
#             "year_used": requested_year
#         }
        
#     except Exception as e:
#         import traceback
#         print(f"--- SECR REPORT ERROR ---\n{traceback.format_exc()}\n-------------------")
#         raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")

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