#!/usr/bin/env python3
"""
CarbonTally Data Generator - Data Validators
Validation utilities for generated data.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

import re
import uuid
from typing import Any, Dict, List, Optional, Pattern
from datetime import datetime
import json


class DataValidator:
    """Validation utilities for ensuring data quality."""
    
    @staticmethod
    def is_valid_uuid(value: str) -> bool:
        """Check if a string is a valid UUID."""
        try:
            uuid.UUID(str(value))
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Validate email address format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(email)))
    
    @staticmethod
    def is_valid_phone(phone: str) -> bool:
        """Validate phone number format."""
        # Allow various formats: +44 20 7123 4567, 02071234567, etc.
        cleaned = re.sub(r'[\s\-()]', '', str(phone))
        return bool(re.match(r'^\+?[0-9]{7,15}$', cleaned))
    
    @staticmethod
    def is_valid_postcode(postcode: str, country: str = "UK") -> bool:
        """Validate postcode for a given country."""
        patterns = {
            "UK": r'^([A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}|GIR ?0AA)$',
            "IE": r'^[A-Z]{1,2}\d{1,2} ?[A-Z]{1,2}\d{1,2}$',
            "DE": r'^\d{5}$',
            "FR": r'^\d{5}$',
            "NL": r'^\d{4} ?[A-Z]{2}$',
            "BE": r'^\d{4}$',
            "FI": r'^\d{5}$'
        }
        
        pattern = patterns.get(country, r'.*')
        return bool(re.match(pattern, str(postcode).upper()))
    
    @staticmethod
    def is_valid_vat_number(vat: str, country: str = "UK") -> bool:
        """Validate VAT number format for a given country."""
        patterns = {
            "UK": r'^GB\d{9}$|^GB\d{12}$',
            "IE": r'^IE\d{7}[A-Z]?$',
            "DE": r'^DE\d{9}$',
            "FR": r'^FR[A-Z0-9]{2}\d{9}$',
            "NL": r'^NL\d{9}B\d{2}$',
            "BE": r'^BE\d{10}$',
            "FI": r'^FI\d{8}$'
        }
        
        pattern = patterns.get(country, r'.*')
        return bool(re.match(pattern, str(vat).upper()))
    
    @staticmethod
    def is_valid_date(date_str: str) -> bool:
        """Check if a string is a valid date."""
        try:
            datetime.fromisoformat(date_str)
            return True
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def is_valid_json(value: Any) -> bool:
        """Check if a value is valid JSON."""
        if isinstance(value, (dict, list)):
            return True
        try:
            json.loads(str(value))
            return True
        except (json.JSONDecodeError, TypeError):
            return False
    
    @staticmethod
    def validate_required_fields(data: Dict, required: List[str]) -> List[str]:
        """Check for missing required fields."""
        missing = []
        for field in required:
            if field not in data or data[field] in (None, '', [], {}):
                missing.append(field)
        return missing
    
    @staticmethod
    def validate_data_types(data: Dict, type_map: Dict[str, type]) -> List[str]:
        """Validate that fields have the correct data type."""
        errors = []
        for field, expected_type in type_map.items():
            if field in data:
                value = data[field]
                if not isinstance(value, expected_type):
                    errors.append(f"{field}: expected {expected_type.__name__}, got {type(value).__name__}")
        return errors
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """Sanitize a string to prevent injection."""
        if not isinstance(value, str):
            return str(value)
        # Remove any potential SQL injection patterns
        dangerous = [';', '--', '/*', '*/', 'xp_', 'exec', 'insert', 'update', 'delete']
        sanitized = value
        for d in dangerous:
            sanitized = sanitized.replace(d, '')
        return sanitized
    
    @staticmethod
    def validate_referential_integrity(
        data: Dict[str, Any],
        foreign_keys: Dict[str, List[str]]
    ) -> Dict[str, List[str]]:
        """
        Validate foreign key references.
        
        Args:
            data: Dictionary containing all records by table
            foreign_keys: Map of table -> list of foreign key fields
            
        Returns:
            Dictionary of broken references by table
        """
        broken_refs = {}
        
        for table, keys in foreign_keys.items():
            if table in data:
                table_data = data[table]
                broken = []
                
                for record in table_data:
                    for key in keys:
                        if key in record and record[key]:
                            ref_table, ref_field = key.split('.')
                            if ref_table in data:
                                # Check if the referenced record exists
                                ref_exists = any(
                                    r.get('id') == record[key]
                                    for r in data[ref_table]
                                )
                                if not ref_exists:
                                    broken.append({
                                        'record': record.get('id'),
                                        'field': key,
                                        'value': record[key]
                                    })
                
                if broken:
                    broken_refs[table] = broken
        
        return broken_refs