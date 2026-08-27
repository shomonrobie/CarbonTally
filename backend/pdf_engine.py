#backennd\pdf_engine.py

import os
import pdfplumber
import pytesseract
from pdf2image import convert_from_bytes
import io
import re
import uuid
from datetime import datetime
from PIL import Image

class PDFExtractor:
    """
    Hybrid PDF extraction engine that handles both digital and scanned PDFs.
    Returns granular data streams with confidence scores for the Ingestion Portal.
    """

    def __init__(self):
        # Tesseract path: prefer an explicit TESSERACT_CMD override; otherwise let
        # pytesseract resolve ``tesseract`` from the system PATH (Linux/Render).
        # Never force a Windows-only path unconditionally — that broke OCR on Linux.
        tesseract_cmd = os.environ.get("TESSERACT_CMD")
        if tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = tesseract_cmd
    
    def extract_and_parse(self, file_bytes: bytes, filename: str, data_type: str, organization_assets: list = None) -> dict:
        extraction_method = "Digital PDF (Text)"
        text = self._extract_text_direct(file_bytes)
        
        if not text or len(text.strip()) < 50:
            extraction_method = "Tesseract OCR Engine v2.4"
            text = self._extract_text_ocr(file_bytes)
        
        if not text or len(text.strip()) < 50:
            return {
                "status": "error",
                "message": "Could not extract text from file."
            }
        
        batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        if data_type == 'utility':
            data_streams = self._parse_utility_bill(text, organization_assets)
        elif data_type == 'fuel':
            data_streams = self._parse_fuel_invoice(text, organization_assets)
        else:
            data_streams = self._parse_scope3_document(text, organization_assets)
        
        return {
            "batch_id": batch_id,
            "file_metadata": {
                "filename": filename,
                "file_type": "PDF",
                "extraction_method": extraction_method,
                "page_count": self._get_page_count(file_bytes)
            },
            "data_streams": data_streams
        }
    def _extract_text_direct(self, pdf_bytes: bytes) -> str:
        """Extract text directly from digital PDFs using pdfplumber"""
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Direct extraction failed: {e}")
            return ""
        return text
    
    def _extract_text_ocr(self, pdf_bytes: bytes) -> str:
        """Extract text from scanned PDFs using OCR.

        Renders each page with pdf2image (poppler) and runs Tesseract over every
        rendered page. ``pdf2image`` requires ``convert_from_bytes`` for in-memory
        input — ``convert_from_path`` only accepts a filesystem path and raised a
        TypeError here, which silently left scanned-PDF OCR returning nothing.
        """
        text = ""
        try:
            images = convert_from_bytes(pdf_bytes, dpi=300)
            for page_no, img in enumerate(images, start=1):
                page_text = pytesseract.image_to_string(img)
                if page_text:
                    # Page boundary markers keep multi-page OCR output separable
                    # while leaving the raw page text intact for the parsers.
                    text += f"\n[page {page_no}]\n{page_text}\n"
        except Exception as e:
            print(f"OCR extraction failed: {e}")
            return ""
        return text
    
    def _get_page_count(self, pdf_bytes: bytes) -> int:
        """Get the number of pages in the PDF"""
        try:
            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                return len(pdf.pages)
        except:
            return 1
    
    def _parse_utility_bill(self, text: str, organization_assets: list = None) -> list:
        """Parse utility bill and return structured data streams"""
        data_streams = []
        
        # Extract billing period
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+\w+\s+\d{2,4})',
        ]
        
        dates_found = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            dates_found.extend(matches)
        
        billing_start = dates_found[0] if len(dates_found) >= 1 else None
        billing_end = dates_found[1] if len(dates_found) >= 2 else None
        
        # Extract consumption
        consumption_kwh = None
        consumption_confidence = 0.0
        
        consumption_patterns = [
            (r'(\d[\d,]*\.?\d*)\s*kWh', 0.95),
            (r'Consumption[:\s]+(\d[\d,]*\.?\d*)', 0.90),
            (r'Usage[:\s]+(\d[\d,]*\.?\d*)', 0.85),
        ]
        
        for pattern, confidence in consumption_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                consumption_kwh = float(match.group(1).replace(',', ''))
                consumption_confidence = confidence
                break
        
        # Detect utility type
        utility_type = 'Unknown'
        if re.search(r'electric|electricity', text, re.IGNORECASE):
            utility_type = 'Electricity'
        elif re.search(r'gas|natural gas', text, re.IGNORECASE):
            utility_type = 'Natural Gas'
        
        # Extract address for asset mapping
        address_match = re.search(r'(?:Address|Supply Address|Location)[:\s]+([^\n]+)', text, re.IGNORECASE)
        extracted_address = address_match.group(1).strip() if address_match else None
        
        # Match to organization assets
        matched_asset = None
        suggested_assets = []
        
        if organization_assets and extracted_address:
            for asset in organization_assets:
                if extracted_address.lower() in asset['name'].lower() or asset['name'].lower() in extracted_address.lower():
                    matched_asset = asset['name']
                    break
            # If no exact match, suggest all assets
            suggested_assets = [asset['name'] for asset in organization_assets[:5]]
        
        # Build data stream
        stream = {
            "stream_id": 1,
            "stream_name": f"{utility_type} Grid Metrics",
            "scope": "Scope 2",
            "status": "verified" if consumption_kwh and matched_asset else "error",
            "extracted_fields": {
                "consumption_kwh": {
                    "value": consumption_kwh,
                    "confidence": consumption_confidence,
                    "status": "verified" if consumption_kwh else "failed"
                },
                "billing_start": {
                    "value": billing_start,
                    "confidence": 0.90 if billing_start else 0.0,
                    "status": "verified" if billing_start else "failed"
                },
                "billing_end": {
                    "value": billing_end,
                    "confidence": 0.90 if billing_end else 0.0,
                    "status": "verified" if billing_end else "failed"
                }
            },
            "asset_mapping": {
                "extracted_address": extracted_address,
                "matched_asset_id": matched_asset,
                "suggested_assets": suggested_assets
            },
            "defra_factor": {
                "factor_name": f"UK {utility_type} (2026)",
                "multiplier": 0.19850 if utility_type == 'Electricity' else 2.02000,
                "unit": "kg CO2e/kWh"
            }
        }
        
        # Calculate emissions if we have consumption
        if consumption_kwh:
            stream["calculated_emissions_kg_co2e"] = round(
                consumption_kwh * stream["defra_factor"]["multiplier"], 2
            )
        
        # Add errors if needed
        errors = []
        if not consumption_kwh:
            errors.append({
                "field": "consumption_kwh",
                "error_type": "low_confidence",
                "message": "Could not extract consumption value from document",
                "requires_manual_input": True
            })
        if not matched_asset:
            errors.append({
                "field": "asset_mapping",
                "error_type": "unmapped_asset",
                "message": f"Could not locate asset matching '{extracted_address or 'extracted address'}'",
                "requires_asset_selection": True
            })
        
        if errors:
            stream["errors"] = errors
            stream["status"] = "error"
        
        data_streams.append(stream)
        return data_streams
    
    def _parse_fuel_invoice(self, text: str, organization_assets: list = None) -> list:
        """Parse fuel invoice and return structured data streams"""
        data_streams = []
        records = []
        
        lines = text.split('\n')
        
        for line in lines:
            date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})', line)
            reg_match = re.search(r'([A-Z]{2}\d{2}\s*[A-Z]{3})', line)
            volume_match = re.search(r'(\d+\.?\d*)\s*[Ll]', line)
            amount_match = re.search(r'£?(\d+\.\d{2})', line)
            
            fuel_type = 'Unknown'
            if re.search(r'diesel', line, re.IGNORECASE):
                fuel_type = 'Diesel'
            elif re.search(r'petrol|gasoline', line, re.IGNORECASE):
                fuel_type = 'Petrol'
            elif re.search(r'adblue|def', line, re.IGNORECASE):
                fuel_type = 'AdBlue'
            
            if date_match and volume_match:
                records.append({
                    'date': date_match.group(1),
                    'vehicle_registration': reg_match.group(1) if reg_match else 'UNKNOWN',
                    'fuel_type': fuel_type,
                    'volume_litres': float(volume_match.group(1)),
                    'amount': float(amount_match.group(1)) if amount_match else None
                })
        
        # Group by fuel type
        fuel_groups = {}
        for record in records:
            fuel_type = record['fuel_type']
            if fuel_type not in fuel_groups:
                fuel_groups[fuel_type] = []
            fuel_groups[fuel_type].append(record)
        
        # Create a data stream for each fuel type
        stream_id = 1
        for fuel_type, fuel_records in fuel_groups.items():
            total_volume = sum(r['volume_litres'] for r in fuel_records)
            
            stream = {
                "stream_id": stream_id,
                "stream_name": f"{fuel_type} Fuel Consumption",
                "scope": "Scope 1",
                "status": "verified",
                "extracted_fields": {
                    "total_volume_litres": {
                        "value": total_volume,
                        "confidence": 0.90,
                        "status": "verified"
                    },
                    "transaction_count": {
                        "value": len(fuel_records),
                        "confidence": 1.0,
                        "status": "verified"
                    }
                },
                "defra_factor": {
                    "factor_name": f"UK {fuel_type} (2026)",
                    "multiplier": 2.68915 if fuel_type == 'Diesel' else 2.32380 if fuel_type == 'Petrol' else 0.0,
                    "unit": "kg CO2e/L"
                },
                "calculated_emissions_kg_co2e": round(total_volume * (2.68915 if fuel_type == 'Diesel' else 2.32380 if fuel_type == 'Petrol' else 0.0), 2)
            }
            
            data_streams.append(stream)
            stream_id += 1
        
        return data_streams
    
    def _parse_scope3_document(self, text: str, organization_assets: list = None) -> list:
        """Parse Scope 3 document (travel, waste, etc.)"""
        # Simplified for now - can be expanded later
        return [{
            "stream_id": 1,
            "stream_name": "Scope 3 Data",
            "scope": "Scope 3",
            "status": "error",
            "errors": [{
                "field": "parsing",
                "error_type": "not_implemented",
                "message": "Scope 3 PDF parsing is not yet implemented",
                "requires_manual_input": True
            }],
            "extracted_fields": {}
        }]
    def extract_image_text(self, file_bytes: bytes) -> str:
        """Raw OCR text for an image (PIL decode + Tesseract).

        Additive primitive used by the V3 upload/OCR wiring and reused by
        :meth:`extract_and_parse_image`. Raises on unreadable images.
        """
        image = Image.open(io.BytesIO(file_bytes))
        return pytesseract.image_to_string(image)

    def extract_and_parse_image(self, file_bytes: bytes, filename: str, data_type: str, organization_assets: list = None) -> dict:
        try:
            text = self.extract_image_text(file_bytes)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Could not process image: {str(e)}"
            }
        
        if not text or len(text.strip()) < 50:
            return {
                "status": "error",
                "message": "Could not extract text from image. The image may be too low quality."
            }
        
        batch_id = f"BATCH-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        if data_type == 'utility':
            data_streams = self._parse_utility_bill(text, organization_assets)
        elif data_type == 'fuel':
            data_streams = self._parse_fuel_invoice(text, organization_assets)
        else:
            data_streams = self._parse_scope3_document(text, organization_assets)
        
        return {
            "batch_id": batch_id,
            "file_metadata": {
                "filename": filename,
                "file_type": "IMAGE",
                "extraction_method": "Tesseract OCR Engine v2.4",
                "page_count": 1
            },
            "data_streams": data_streams
        }
