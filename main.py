from dotenv import load_dotenv
import os
load_dotenv()  # This loads the variables from your .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)

# DEBUG PRINTS (We will remove these later)
print("🔍 DEBUG: SUPABASE_URL is", os.getenv("SUPABASE_URL"))
print("🔍 DEBUG: SUPABASE_SERVICE_KEY is", "SET" if os.getenv("SUPABASE_SERVICE_KEY") else "MISSING")

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
app = FastAPI(title="CarbonTally API", version="3.0.0")

# Initialize PDF Extractor
pdf_extractor = PDFExtractor()
resend.api_key = os.getenv("RESEND_API_KEY", "re_XRjsEbwv_2TDUBguF5TWzbn7wcTVn8JtN")
FOUNDER_EMAIL = "shomonrobie@gmail.com"  # Change this to your email
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", 
        "https://carbontally.co.uk", 
        "https://www.carbontally.co.uk"
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
# CSV PROCESSING FUNCTIONS (Cleaned & Deduplicated)
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
    
    # Handle Cost if it exists
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
        import traceback
        print(f"--- BACKEND CRASH ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")

async def _queue_for_manual_review(
    file_bytes: bytes,
    filename: str,
    content_type: str,
    data_type: str,
    organization_id: str,
    auto_result: dict,
    supabase_client
) -> str:
    """
    Queue a failed extraction for manual review and send email notification.
    Returns the review_id.
    """
    try:
        # 1. Upload file to Supabase Storage
        file_path = f"manual_review/{organization_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
        
        storage_response = supabase_client.storage.from_('documents').upload(
            file_path,
            file_bytes,
            file_options={"content-type": content_type}
        )
        
        file_url = supabase_client.storage.from_('documents').get_public_url(file_path)
        
        # 2. Insert into manual_review_queue
        queue_response = supabase_client.from_('manual_review_queue').insert({
            'organization_id': organization_id if organization_id and organization_id != "mock-org-id" else None,
            'file_url': file_url,
            'file_name': filename,
            'file_type': 'PDF' if filename.lower().endswith('.pdf') else 'IMAGE',
            'data_type': data_type,
            'status': 'pending',
            'auto_extraction_result': auto_result,
            'priority': 1 if auto_result.get('status') == 'error' else 0,
            'customer_notes': f"Auto-extraction failed. File: {filename}"
        }).execute()
        
        review_id = queue_response.data[0]['id']
        
        # 3. Send email notification to founder
        try:
            resend.Emails.send({
                "from": "CarbonTally <notifications@carbontally.co.uk>",
                "to": [FOUNDER_EMAIL],
                "subject": f"🚨 Manual Review Required: {filename}",  # <-- FIXED
                "html": f"""
                <h2>Manual Review Queue Alert</h2>
                <p>A customer's document could not be auto-extracted and requires manual review.</p>
                <table style="border-collapse: collapse; width: 100%;">
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Organization ID:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{organization_id}</td></tr>
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>File Name:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{filename}</td></tr>
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Data Type:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{data_type}</td></tr>
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Priority:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{'🔥 High' if auto_result.get('status') == 'error' else '📄 Normal'}</td></tr>
                  <tr><td style="padding: 8px; border: 1px solid #ddd;"><strong>Review ID:</strong></td><td style="padding: 8px; border: 1px solid #ddd;">{review_id}</td></tr>
                </table>
                <p><a href="https://carbontally.co.uk/staff-dashboard" style="background: #16a34a; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px;">Open Staff Dashboard</a></p>
                <p style="color: #64748b; font-size: 12px; margin-top: 20px;">Estimated completion: 24 hours</p>
                """
            })
        except Exception as email_error:
            print(f"Email notification failed (this is okay for local testing): {email_error}")
        
        return review_id
    
    except Exception as e:
        print(f"Failed to queue for manual review: {e}")
        raise e



def _has_low_confidence(extraction_result: dict) -> bool:
    """Check if any data stream has confidence < 60%"""
    for stream in extraction_result.get("data_streams", []):
        for field in stream.get("extracted_fields", {}).values():
            if field.get("confidence", 1.0) < 0.60:
                return True
    return False
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
        
        if extraction_result.get("status") == "error" or _has_low_confidence(extraction_result):
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
            
            if not supabase_url or not supabase_key:
                raise HTTPException(status_code=500, detail="Server configuration error: Missing Supabase credentials.")
            
            supabase_client = create_client(supabase_url, supabase_key)
            
            review_id = await _queue_for_manual_review(
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
                "estimated_completion": "24-48 hours"
            }
        
        return extraction_result
    
    except Exception as e:
        import traceback
        print(f"--- PDF EXTRACTION ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")
    
@app.post("/approve-pdf-batch")
async def approve_pdf_batch(batch_data: dict):
    try:
        batch_id = batch_data.get("batch_id")
        data_streams = batch_data.get("data_streams", [])
        
        # TODO: In production, save to Supabase here
        # 1. Create a pdf_batch record with status 'approved'
        # 2. Loop through data_streams and insert into emissions_records table
        
        return {
            "status": "success",
            "batch_id": batch_id,
            "records_committed": len(data_streams),
            "message": "Batch approved and committed to database"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch approval failed: {str(e)}")
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
        
        # 1. AWAIT the file read to get raw bytes
        file_bytes = await file.read()
        
        # 2. Pass bytes and filename to the engine
        extraction_result = pdf_extractor.extract_and_parse_image(
            file_bytes, file.filename, data_type, organization_assets
        )
        
        # 3. Check for failure
        if extraction_result.get("status") == "error" or _has_low_confidence(extraction_result):
            from supabase import create_client
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
            
            if not supabase_url or not supabase_key:
                raise HTTPException(status_code=500, detail="Server configuration error: Missing Supabase credentials.")
            
            supabase_client = create_client(supabase_url, supabase_key)
            
            review_id = await _queue_for_manual_review(
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
                "estimated_completion": "24-48 hours"
            }
        
        return extraction_result
    
    except Exception as e:
        import traceback
        print(f"--- IMAGE EXTRACTION ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Image extraction failed: {str(e)}")

@app.post("/notify-customer-manual-extraction")
async def notify_customer_manual_extraction(batch_data: dict):
    """
    Send an email to the customer notifying them that their manual extraction is complete
    and ready for their final review.
    """
    try:
        review_id = batch_data.get("review_id")
        organization_id = batch_data.get("organization_id")
        file_name = batch_data.get("file_name")
        
        # 1. Fetch the customer's email from the organization
        # (Assuming the organization has at least one member with an email)
        org_members = supabase_client.from_('organization_members')\
            .select('user_id, auth.users(email)')\
            .eq('organization_id', organization_id)\
            .limit(1)\
            .execute()
        
        if not org_members.data or len(org_members.data) == 0:
            return {"status": "warning", "message": "No customer email found, but extraction completed"}
        
        customer_email = org_members.data[0]['auth.users']['email']
        
        # 2. Send email notification
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
        import traceback
        print(f"--- CUSTOMER NOTIFICATION ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Customer notification failed: {str(e)}")
@app.post("/upload-batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    batch_name: str = Form(...),
    data_type: str = Form('mixed'),
    organization_id: str = Form(...)
):
    """
    Accept multiple files at once and create a batch for processing.
    """
    try:
        # Initialize Supabase client
        from supabase import create_client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
        supabase_client = create_client(supabase_url, supabase_key)
        
        # 1. Create the batch record
        batch_response = supabase_client.from_('upload_batches').insert({
            'organization_id': organization_id,
            'batch_name': batch_name,
            'total_files': len(files),
            'processed_files': 0,
            'status': 'processing',
            'metadata': {'data_type': data_type}
        }).execute()
        
        batch_id = batch_response.data[0]['id']
        
        # 2. Upload each file and queue for processing
        processed_count = 0
        failed_files = []
        
        for file in files:
            try:
                # Upload to storage
                file_bytes = await file.read()
                file_path = f"batches/{organization_id}/{batch_id}/{file.filename}"
                
                supabase_client.storage.from_('documents').upload(
                    file_path,
                    file_bytes,
                    file_options={"content-type": file.content_type}
                )
                
                file_url = supabase_client.storage.from_('documents').get_public_url(file_path)
                
                # Determine file type
                file_type = 'PDF' if file.filename.lower().endswith('.pdf') else 'IMAGE'
                
                # Determine actual data type (if mixed, default to utility)
                actual_data_type = data_type if data_type != 'mixed' else 'utility'
                
                # Try auto-extraction first
                if file_type == 'PDF':
                    extraction_result = pdf_extractor.extract_and_parse(
                        file_bytes, file.filename, actual_data_type, []
                    )
                else:
                    extraction_result = pdf_extractor.extract_and_parse_image(
                        file_bytes, file.filename, actual_data_type, []
                    )
                
                # Queue for manual review if extraction failed or low confidence
                if extraction_result.get("status") == "error" or _has_low_confidence(extraction_result):
                    # Insert into manual_review_queue with batch_id
                    supabase_client.from_('manual_review_queue').insert({
                        'organization_id': organization_id,
                        'batch_id': batch_id,
                        'file_url': file_url,
                        'file_name': file.filename,
                        'file_type': file_type,
                        'data_type': actual_data_type,
                        'status': 'pending',
                        'auto_extraction_result': extraction_result,
                        'priority': 1 if extraction_result.get('status') == 'error' else 0,
                        'customer_notes': f"Batch upload: {batch_name}. File: {file.filename}"
                    }).execute()
                
                processed_count += 1
                
            except Exception as file_error:
                print(f"Error processing file {file.filename}: {file_error}")
                failed_files.append(file.filename)
                continue
        
        # 3. Update batch status
        final_status = 'completed' if len(failed_files) == 0 else 'partial'
        supabase_client.from_('upload_batches').update({
            'processed_files': processed_count,
            'status': final_status,
            'completed_at': datetime.now().isoformat(),
            'metadata': {
                'data_type': data_type,
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
        import traceback
        print(f"--- BATCH UPLOAD ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")      