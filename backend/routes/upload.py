# backend/routes/upload.py
"""
File upload endpoints for CSV, PDF, and batch uploads.
"""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from typing import Optional, List, Dict, Any
from datetime import datetime
import io
import pandas as pd
import numpy as np
import traceback
from auth import AuthUser, get_current_user, require_auth, require_org_member

from database import get_supabase_client
from utils.emissions import (
    process_fuel_data,
    process_utility_data,
    process_scope3_data,
    extract_issues_from_result,
    has_low_confidence,
    get_emission_factor,
    calculate_emissions_with_defra,
    ACTIVITY_TYPE_MAPPING
)


router = APIRouter(prefix="/api", tags=["Upload"])

# ==========================================
# HELPER FUNCTIONS
# ==========================================

async def get_system_settings(supabase_client):
    """
    Fetch system settings from database with caching.
    """
    try:
        # Try to get settings from system_settings table
        result = supabase_client.from_('system_settings') \
            .select('*') \
            .maybe_single() \
            .execute()
        
        if result.data:
            settings = result.data
            if settings.get('settings_json'):
                return settings['settings_json']
            return {
                'max_file_size_mb': settings.get('max_file_size_mb', 50),
                'allowed_file_types': settings.get('allowed_file_types', ['pdf', 'csv', 'xlsx', 'jpg', 'jpeg', 'png']),
                'enable_auto_repair': settings.get('enable_auto_repair', True),
                'max_batch_files': settings.get('max_batch_files', 20),
                'max_total_batch_size_mb': settings.get('max_total_batch_size_mb', 200),
                'data_retention_days': settings.get('data_retention_days', 365)
            }
        
        # Return defaults if no settings found
        return {
            'max_file_size_mb': 50,
            'allowed_file_types': ['pdf', 'csv', 'xlsx', 'jpg', 'jpeg', 'png'],
            'enable_auto_repair': True,
            'max_batch_files': 20,
            'max_total_batch_size_mb': 200,
            'data_retention_days': 365
        }
    except Exception as e:
        print(f"⚠️ Error fetching settings: {e}")
        return {
            'max_file_size_mb': 50,
            'allowed_file_types': ['pdf', 'csv', 'xlsx', 'jpg', 'jpeg', 'png'],
            'enable_auto_repair': True,
            'max_batch_files': 20,
            'max_total_batch_size_mb': 200,
            'data_retention_days': 365
        }

async def validate_file_upload(file: UploadFile, settings: dict, is_batch: bool = False):
    """
    Validate file against system settings.
    Returns (is_valid, error_message, file_bytes)
    """
    # Check file size
    file_bytes = await file.read()
    file_size_mb = len(file_bytes) / (1024 * 1024)
    max_size_mb = settings.get('max_file_size_mb', 50)
    
    if file_size_mb > max_size_mb:
        return False, f"File too large. Max size is {max_size_mb}MB. Your file is {file_size_mb:.1f}MB", None
    
    # Check file type
    file_ext = file.filename.split('.')[-1].lower()
    allowed_types = settings.get('allowed_file_types', ['pdf', 'csv', 'xlsx', 'jpg', 'jpeg', 'png'])
    
    if file_ext not in allowed_types:
        return False, f"File type '{file_ext}' not allowed. Allowed types: {', '.join(allowed_types)}", None
    
    # Reset file position for further processing
    await file.seek(0)
    
    return True, None, file_bytes

# ==========================================
# UPLOAD ENDPOINTS
# ==========================================

@router.post("/test-upload")
async def test_upload(file: UploadFile = File(...)):
    """
    Simple test endpoint to verify file uploads work.
    """
    try:
        content = await file.read()
        return {
            "status": "success",
            "filename": file.filename,
            "size": len(content),
            "content_type": file.content_type
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    data_type: str = Form('fuel'),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Upload and process CSV/Excel file with system settings validation.
    """
    try:
        # Get system settings
        supabase = get_supabase_client()
        settings = await get_system_settings(supabase)
        
        # Validate file
        is_valid, error_msg, file_bytes = await validate_file_upload(file, settings)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Only CSV or Excel files
        if not file.filename.endswith(('.csv', '.xlsx')):
            raise HTTPException(status_code=400, detail="Only CSV or Excel files are allowed.")
        
        # Read the file
        if not file_bytes:
            file_bytes = await file.read()
        
        df = pd.read_csv(io.BytesIO(file_bytes))
        df.columns = df.columns.str.strip()
        
        # Import processing functions from main
        from main import process_fuel_data, process_utility_data, process_scope3_data
        
        if data_type == 'utility':
            clean_data, flagged_rows = process_utility_data(df, supabase)
            scope = "Scope 2"
        elif data_type == 'scope3':
            clean_data, flagged_rows = process_scope3_data(df, supabase)
            scope = "Scope 3"
        else:
            clean_data, flagged_rows = process_fuel_data(df, supabase)
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
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- BACKEND CRASH ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")

@router.post("/upload-pdf")
async def upload_pdf(
    file: UploadFile = File(...),
    data_type: str = Form('utility'),
    organization_id: str = Form(None),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Upload and process PDF with system settings validation.
    """
    try:
        # Get system settings
        supabase = get_supabase_client()
        settings = await get_system_settings(supabase)
        
        # Validate file
        is_valid, error_msg, file_bytes = await validate_file_upload(file, settings)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Check if it's a PDF
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed.")
        
        # Check if auto-repair is enabled
        enable_auto_repair = settings.get('enable_auto_repair', True)
        
        organization_assets = [
            {"id": "1", "name": "Birmingham Hub Main Floor"},
            {"id": "2", "name": "Birmingham Hub Unit 4"}
        ]
        
        # Use file_bytes from validation
        if not file_bytes:
            file_bytes = await file.read()
        
        # Import PDF extractor
        from pdf_engine import PDFExtractor
        pdf_extractor = PDFExtractor()
        
        extraction_result = pdf_extractor.extract_and_parse(
            file_bytes, file.filename, data_type, organization_assets
        )
        
        # Check if extraction failed and auto-repair is enabled
        if (extraction_result.get("status") == "error" or has_low_confidence(extraction_result)) and enable_auto_repair:
            # Import queue function from main
            from main import queue_for_manual_review, extract_issues_from_result
            
            # Extract issues and summary BEFORE queueing
            issues, summary = extract_issues_from_result(extraction_result, data_type)
            
            # Queue for manual review with the extracted issues
            review_id, issues, summary = await queue_for_manual_review(
                file_bytes=file_bytes,
                filename=file.filename,
                content_type=file.content_type,
                data_type=data_type,
                organization_id=organization_id or current_user.organization_id,
                auto_result=extraction_result,
                supabase_client=supabase
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
        elif extraction_result.get("status") == "error" or has_low_confidence(extraction_result):
            # Auto-repair disabled, return error
            return {
                "status": "error",
                "message": "Extraction failed. Auto-repair is disabled. Please contact support.",
                "extraction_issues": extraction_result.get("issues", [])
            }
        
        return extraction_result
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- PDF EXTRACTION ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"PDF extraction failed: {str(e)}")

@router.post("/upload-batch")
async def upload_batch(
    files: List[UploadFile] = File(...),
    batch_name: str = Form(...),
    data_type: str = Form('mixed'),
    organization_id: str = Form(...),
    special_instructions: str = Form(''),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Accept multiple files at once and create a batch for processing.
    Bulk upload is disabled for beta - premium feature.
    """
    try:
        # Premium feature - disabled for beta
        return {
            "status": "premium_feature",
            "message": "Bulk upload is a premium feature. Please upgrade to access this functionality.",
            "feature": "bulk_upload",
            "limit": 1,
            "action": "upgrade_required"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"--- BATCH UPLOAD ERROR ---\n{traceback.format_exc()}\n-------------------")
        raise HTTPException(status_code=500, detail=f"Batch upload failed: {str(e)}")

@router.post("/repair-pdf")
async def repair_pdf(
    file: UploadFile = File(...),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Advanced PDF repair with OCR for corrupted or scanned documents.
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
        supabase = get_supabase_client()
        
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
            ocr_texts.append(ocr_text[:500])
            
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

# ==========================================
# HELPER FUNCTIONS FOR PDF EXTRACTION
# ==========================================

def has_low_confidence(extraction_result: dict) -> bool:
    """Check if any data stream has confidence < 60%"""
    for stream in extraction_result.get("data_streams", []):
        for field in stream.get("extracted_fields", {}).values():
            if field.get("confidence", 1.0) < 0.60:
                return True
    return False

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
# ==========================================
# UPLOAD ENDPOINT
# ==========================================

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    data_type: str = Form("utility"),
    organization_id: str = Form(...),
    special_instructions: Optional[str] = Form(None),
    current_user: AuthUser = Depends(require_org_member())
):
    """
    Upload a document for processing.
    """
    try:
        supabase = get_supabase_client()
        
        # Validate file
        if not file:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No file provided"
            )
        
        # Check file size (max 50MB)
        file_bytes = await file.read()
        file_size = len(file_bytes)
        if file_size > 50 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="File size exceeds 50MB limit"
            )
        
        # Determine file type
        file_ext = file.filename.split('.')[-1].lower() if '.' in file.filename else ''
        mime_type = file.content_type or 'application/octet-stream'
        
        if file_ext in ['pdf'] or 'pdf' in mime_type:
            file_type = 'PDF'
        elif file_ext in ['jpg', 'jpeg', 'png', 'gif', 'webp'] or 'image' in mime_type:
            file_type = 'IMAGE'
        elif file_ext in ['csv', 'xlsx', 'xls']:
            file_type = 'SPREADSHEET'
        else:
            file_type = 'OTHER'
        
        # Generate storage path
        now = datetime.now()
        file_path = f"uploads/{organization_id}/{now.strftime('%Y/%m/%d')}/{now.strftime('%Y%m%d_%H%M%S')}_{file.filename}"
        
        # Upload to Supabase Storage
        try:
            bucket = 'documents'
            # Upload to Supabase Storage
            supabase.storage.from_(bucket).upload(
                file_path,
                file_bytes,
                file_options={
                    "content-type": mime_type,
                    "cache-control": "3600"
                }
            )
            # Get public URL
            file_url = supabase.storage.from_(bucket).get_public_url(file_path)
        except Exception as storage_error:
            print(f"❌ Storage upload error: {storage_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file to storage: {str(storage_error)}"
            )
        
        # Create file record in organization_files
        file_record = {
            'organization_id': organization_id,
            'name': file.filename,
            'path': file_path,
            'size_bytes': file_size,
            'file_type': file_type,
            'mime_type': mime_type,
            'bucket': bucket,
            'uploaded_by': current_user.user_id,
            'uploaded_at': datetime.now().isoformat(),
            'status': 'uploaded',
            'status_updated_at': datetime.now().isoformat(),
            'is_active': True,
            'access_count': 0,
            'metadata': {
                'data_type': data_type,
                'special_instructions': special_instructions,
                'uploaded_by_email': current_user.email,
                'upload_timestamp': datetime.now().isoformat()
            }
        }
        
        result = supabase.from_('organization_files') \
            .insert(file_record) \
            .execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create file record"
            )
        
        file_id = result.data[0]['id']
        
        # Try to extract data if it's a PDF or Image
        extraction_result = None
        status = 'uploaded'
        confidence_score = 0
        issues = []
        
        if file_type in ['PDF', 'IMAGE']:
            try:
                # Call the correct extraction method per file type. The legacy
                # consolidation previously called the PDF path for images too,
                # which made JPG/PNG OCR unreachable (pdfplumber cannot open a
                # bitmap). extract_and_parse_image performs PIL decode + OCR.
                from pdf_engine import PDFExtractor
                pdf_extractor = PDFExtractor()
                
                # Get organization assets for mapping
                assets_result = supabase.from_('assets') \
                    .select('id, name, facility_id') \
                    .eq('organization_id', organization_id) \
                    .execute()
                organization_assets = assets_result.data or []
                
                # Extract data
                if file_type == 'IMAGE':
                    extraction_result = pdf_extractor.extract_and_parse_image(
                        file_bytes,
                        file.filename,
                        data_type,
                        organization_assets
                    )
                else:
                    extraction_result = pdf_extractor.extract_and_parse(
                        file_bytes,
                        file.filename,
                        data_type,
                        organization_assets
                    )
                
                if extraction_result.get('status') == 'success':
                    status = 'ready_for_review'
                    confidence_score = extraction_result.get('confidence_score', 0.8)
                    issues = extraction_result.get('issues', [])
                    
                    # Update file record with extraction result
                    supabase.from_('organization_files') \
                        .update({
                            'status': 'ready_for_review',
                            'status_updated_at': datetime.now().isoformat(),
                            'review_ready_at': datetime.now().isoformat(),
                            'metadata': {
                                'data_type': data_type,
                                'special_instructions': special_instructions,
                                'extraction_result': extraction_result,
                                'confidence_score': confidence_score,
                                'issues': issues
                            }
                        }) \
                        .eq('id', file_id) \
                        .execute()
                else:
                    # Extraction failed or needs manual review
                    status = 'staff_review'
                    issues = extraction_result.get('issues', ['Extraction failed'])
                    
                    # Add to manual review queue
                    supabase.from_('manual_review_queue') \
                        .insert({
                            'file_id': file_id,
                            'organization_id': organization_id,
                            'file_name': file.filename,
                            'file_type': file_type,
                            'data_type': data_type,
                            'file_url': file_url,
                            'status': 'pending',
                            'auto_extraction_result': extraction_result,
                            'customer_notes': special_instructions,
                            'priority': 1,
                            'created_at': datetime.now().isoformat()
                        }) \
                        .execute()
                    
                    # Update file status
                    supabase.from_('organization_files') \
                        .update({
                            'status': 'staff_review',
                            'status_updated_at': datetime.now().isoformat(),
                            'metadata': {
                                'data_type': data_type,
                                'special_instructions': special_instructions,
                                'extraction_result': extraction_result,
                                'issues': issues
                            }
                        }) \
                        .eq('id', file_id) \
                        .execute()
                    
            except Exception as extract_error:
                print(f"⚠️ Extraction error: {extract_error}")
                status = 'uploaded'
                issues = [str(extract_error)]
                
                # Update file with extraction error
                supabase.from_('organization_files') \
                    .update({
                        'metadata': {
                            'data_type': data_type,
                            'special_instructions': special_instructions,
                            'extraction_error': str(extract_error)
                        }
                    }) \
                    .eq('id', file_id) \
                    .execute()
        
        # Return response
        return {
            "success": True,
            "message": "File uploaded successfully",
            "file_id": file_id,
            "file_url": file_url,
            "status": status,
            "file_type": file_type,
            "data_type": data_type,
            "extraction_result": extraction_result,
            "confidence_score": confidence_score,
            "issues": issues
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error uploading file: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )
# Add to backend/routes/upload.py

# ==========================================
# Batch Status Endpoints
# ==========================================

@router.get("/batches/{batch_id}/status")
async def get_batch_status(
    batch_id: str,
    current_user: AuthUser = Depends(require_auth())
):
    """Get detailed status of a batch."""
    try:
        supabase = get_supabase_client()
        
        # Get batch details
        batch = supabase.from_('upload_batches') \
            .select('*') \
            .eq('id', batch_id) \
            .maybe_single() \
            .execute()
        
        if not batch.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # Check access
        if not current_user.is_admin:
            member = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', batch.data['organization_id']) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            # supabase-py 2.9.0 returns None (not an APIResponse) for an empty
            # maybe_single result — guard before reading .data (fail closed 403).
            if not member or not member.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this batch"
                )
        
        # Get files in batch
        files = supabase.from_('organization_files') \
            .select('id, name, status, created_at, uploaded_at') \
            .eq('batch_id', batch_id) \
            .execute()
        
        return {
            "success": True,
            "data": {
                "batch": batch.data,
                "files": files.data,
                "total_files": len(files.data) if files.data else 0,
                "processed_files": batch.data.get('processed_files', 0)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch status: {str(e)}"
        )

@router.get("/batches/{batch_id}/progress")
async def get_batch_progress(
    batch_id: str,
    current_user: AuthUser = Depends(require_auth())
):
    """Get real-time progress of a batch."""
    try:
        supabase = get_supabase_client()
        
        batch = supabase.from_('upload_batches') \
            .select('total_files, processed_files, status, created_at, completed_at, organization_id') \
            .eq('id', batch_id) \
            .maybe_single() \
            .execute()
        
        if not batch.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        # F2 (IDOR fix): progress must not leak to callers outside the owning
        # organisation. Mirrors the membership scope on GET .../status.
        if not current_user.is_admin:
            member = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', batch.data['organization_id']) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            # supabase-py 2.9.0 returns None for an empty maybe_single result.
            if not member or not member.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view this batch"
                )
        
        total = batch.data.get('total_files', 0)
        processed = batch.data.get('processed_files', 0)
        
        progress = {
            'total_files': total,
            'processed_files': processed,
            'percentage': round((processed / total * 100), 2) if total > 0 else 0,
            'status': batch.data.get('status', 'pending'),
            'created_at': batch.data.get('created_at'),
            'completed_at': batch.data.get('completed_at')
        }
        
        return {"success": True, "data": progress}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch progress: {str(e)}"
        )

@router.post("/batches/{batch_id}/cancel")
async def cancel_batch(
    batch_id: str,
    current_user: AuthUser = Depends(require_auth())
):
    """Cancel a batch upload."""
    try:
        supabase = get_supabase_client()
        
        batch = supabase.from_('upload_batches') \
            .select('organization_id, status') \
            .eq('id', batch_id) \
            .maybe_single() \
            .execute()
        
        if not batch.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Batch not found"
            )
        
        if batch.data['status'] in ['completed', 'cancelled']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch is already {batch.data['status']}"
            )
        
        # Check access
        if not current_user.is_admin:
            member = supabase.from_('organization_members') \
                .select('id') \
                .eq('organization_id', batch.data['organization_id']) \
                .eq('user_id', current_user.user_id) \
                .maybe_single() \
                .execute()
            
            if not member or not member.data:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to cancel this batch"
                )
        
        # Update batch status
        result = supabase.from_('upload_batches') \
            .update({
                'status': 'cancelled',
                'completed_at': datetime.utcnow().isoformat()
            }) \
            .eq('id', batch_id) \
            .execute()
        
        return {
            "success": True,
            "message": "Batch cancelled successfully",
            "data": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cancel batch: {str(e)}"
        )

@router.get("/batches/stats")
async def get_batch_stats(
    current_user: AuthUser = Depends(require_auth()),
    organization_id: Optional[str] = None
):
    """Get batch statistics."""
    try:
        supabase = get_supabase_client()
        
        query = supabase.from_('upload_batches').select('*')
        
        if organization_id:
            # F2 (IDOR fix): an explicit organization_id is only honoured when
            # the caller is a global admin or a member of that organisation.
            # Previously any authenticated user could read another org's stats.
            if not current_user.is_admin:
                member = supabase.from_('organization_members') \
                    .select('id') \
                    .eq('organization_id', organization_id) \
                    .eq('user_id', current_user.user_id) \
                    .maybe_single() \
                    .execute()
                # supabase-py 2.9.0 returns None for an empty maybe_single result.
                if not member or not member.data:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Not authorized to view this organization's batches"
                    )
            query = query.eq('organization_id', organization_id)
        elif not current_user.is_admin:
            orgs = supabase.from_('organization_members') \
                .select('organization_id') \
                .eq('user_id', current_user.user_id) \
                .execute()
            
            if orgs.data:
                org_ids = [o['organization_id'] for o in orgs.data]
                query = query.in_('organization_id', org_ids)
        
        result = query.execute()
        
        if not result.data:
            return {
                "success": True,
                "data": {
                    "total_batches": 0,
                    "by_status": {},
                    "total_files": 0,
                    "avg_batch_size": 0
                }
            }
        
        stats = {
            'total_batches': len(result.data),
            'by_status': {},
            'total_files': 0,
            'avg_batch_size': 0
        }
        
        total_files = 0
        for batch in result.data:
            batch_status = batch.get('status', 'unknown')
            # Note: must not shadow the module-level ``status`` from fastapi —
            # the except handler below references ``status.HTTP_500_...``.
            stats['by_status'][batch_status] = stats['by_status'].get(batch_status, 0) + 1
            total_files += batch.get('total_files', 0)
        
        stats['total_files'] = total_files
        stats['avg_batch_size'] = round(total_files / len(result.data), 2) if result.data else 0
        
        return {"success": True, "data": stats}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get batch stats: {str(e)}"
        )