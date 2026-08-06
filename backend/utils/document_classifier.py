# backend/utils/document_classifier.py

from typing import Dict, Optional, List
from datetime import datetime
from database import get_supabase_client

DOCUMENT_TYPE_KEYWORDS = {
    'invoice_electricity': ['electricity', 'electric', 'utility', 'kilowatt', 'kwh', 'power', 'energy', 'grid'],
    'invoice_gas': ['gas', 'natural gas', 'therm', 'm3', 'cubic', 'heat', 'heating'],
    'invoice_water': ['water', 'aqua', 'h2o', 'water supply', 'sewage', 'wastewater'],
    'invoice_fuel': ['fuel', 'diesel', 'petrol', 'gasoline', 'lpg', 'adblue', 'fuel card'],
    'invoice_services': ['service', 'consulting', 'maintenance', 'repair', 'service charge', 'professional'],
    'receipt_fuel': ['fuel', 'diesel', 'petrol', 'gasoline', 'gas station', 'petrol station', 'fuel receipt', 'fill up'],
    'receipt_maintenance': ['maintenance', 'repair', 'service', 'mechanic', 'garage', 'parts', 'workshop'],
    'receipt_supplies': ['supplies', 'stationery', 'office', 'equipment', 'consumables'],
    'log_fuel': ['fuel log', 'fuel consumption', 'fuel usage', 'fuel record', 'consumption log'],
    'log_mileage': ['mileage', 'travel log', 'vehicle log', 'trip log', 'distance', 'odometer'],
    'log_energy': ['energy log', 'energy consumption', 'power log', 'energy usage'],
    'export_erp': ['sap', 'oracle', 'erp', 'enterprise', 'resource planning', 'dynamics'],
    'export_accounting': ['quickbooks', 'xero', 'sage', 'accounting', 'general ledger', 'qb', 'qbo'],
    'export_utility': ['utility export', 'energy data', 'smart meter', 'meter read'],
    'spreadsheet_emissions': ['emissions', 'carbon', 'co2', 'ghg', 'footprint', 'sustainability', 'ghg protocol'],
    'spreadsheet_assets': ['asset', 'equipment', 'machinery', 'inventory', 'register', 'fixed assets'],
    'spreadsheet_facilities': ['facility', 'building', 'site', 'location', 'premise', 'property'],
}

async def classify_document(
    file_name: str, 
    file_content: Optional[bytes] = None, 
    user_selected_type: Optional[str] = None
) -> Dict:
    """
    Classify document type based on filename, content, and user selection.
    
    Returns:
        {
            'document_type_code': 'invoice_fuel',
            'document_type_id': 'uuid',
            'confidence': 0.85,
            'suggested_type': 'Fuel Invoice',
            'category': 'invoice',
            'source': 'auto_classified',
            'alternative_types': ['receipt_fuel', 'log_fuel']
        }
    """
    try:
        supabase = get_supabase_client()
        
        # Get all document types
        types_result = supabase.from_('document_types') \
            .select('*') \
            .eq('is_active', True) \
            .execute()
        
        document_types = types_result.data or []
        type_map = {t['code']: t for t in document_types}
        
        # If user selected a type, respect it
        if user_selected_type and user_selected_type in type_map:
            selected_type = type_map[user_selected_type]
            return {
                'document_type_code': user_selected_type,
                'document_type_id': selected_type['id'],
                'confidence': 0.95,
                'suggested_type': selected_type['name'],
                'category': selected_type['category'],
                'source': 'user_selected',
                'alternative_types': []
            }
        
        # Auto-classify by filename
        file_name_lower = file_name.lower()
        scores = {}
        
        for doc_type in document_types:
            code = doc_type['code']
            keywords = DOCUMENT_TYPE_KEYWORDS.get(code, [])
            
            # Skip 'other' type as fallback
            if code == 'other':
                continue
            
            score = 0
            matched_keywords = []
            for keyword in keywords:
                if keyword in file_name_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Check file extension
            ext = file_name_lower.split('.')[-1] if '.' in file_name_lower else ''
            if ext in doc_type.get('file_extensions', []):
                score += 0.5
            
            if score > 0:
                scores[code] = {
                    'score': score,
                    'document_type_id': doc_type['id'],
                    'name': doc_type['name'],
                    'category': doc_type['category'],
                    'matched_keywords': matched_keywords
                }
        
        # Sort by score
        sorted_scores = sorted(scores.items(), key=lambda x: x[1]['score'], reverse=True)
        
        if sorted_scores and sorted_scores[0][1]['score'] >= 1:
            best_match = sorted_scores[0]
            confidence = min(0.9, 0.5 + (best_match[1]['score'] * 0.1))
            
            return {
                'document_type_code': best_match[0],
                'document_type_id': best_match[1]['document_type_id'],
                'confidence': confidence,
                'suggested_type': best_match[1]['name'],
                'category': best_match[1]['category'],
                'alternative_types': [s[0] for s in sorted_scores[1:3]],
                'source': 'auto_classified'
            }
        
        # Default to 'other'
        other_type = type_map.get('other')
        return {
            'document_type_code': 'other',
            'document_type_id': other_type['id'] if other_type else None,
            'confidence': 0.1,
            'suggested_type': 'Other Document',
            'category': 'other',
            'source': 'fallback',
            'alternative_types': []
        }
        
    except Exception as e:
        print(f"⚠️ Error classifying document: {e}")
        import traceback
        traceback.print_exc()
        return {
            'document_type_code': 'other',
            'document_type_id': None,
            'confidence': 0,
            'suggested_type': 'Other Document',
            'category': 'other',
            'source': 'error',
            'alternative_types': []
        }