#!/usr/bin/env python3
"""
CarbonTally Data Generator - ID Generators
Generates unique identifiers for all entities.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

import uuid
import random
import string
from typing import List, Optional


class IDGenerator:
    """Utility for generating various types of identifiers."""
    
    @staticmethod
    def generate_uuid() -> str:
        """Generate a UUID v4 as string."""
        return str(uuid.uuid4())
    
    @staticmethod
    def generate_short_id(length: int = 8) -> str:
        """Generate a short alphanumeric ID."""
        chars = string.ascii_uppercase + string.digits
        return ''.join(random.choices(chars, k=length))
    
    @staticmethod
    def generate_company_number(country: str = "UK") -> str:
        """Generate a company registration number."""
        formats = {
            "UK": lambda: str(random.randint(10000000, 99999999)),
            "IE": lambda: str(random.randint(100000, 999999)),
            "DE": lambda: f"HRB {random.randint(10000, 99999)}",
            "FR": lambda: f"RCS {random.choice(['Paris', 'Lyon', 'Marseille'])} {random.randint(100000000, 999999999)}",
            "NL": lambda: str(random.randint(10000000, 99999999)),
            "BE": lambda: str(random.randint(100000000, 999999999)),
            "FI": lambda: str(random.randint(1000000, 9999999))
        }
        return formats.get(country, formats["UK"])()
    
    @staticmethod
    def generate_vat_number(country: str = "UK") -> str:
        """Generate a VAT number."""
        formats = {
            "UK": lambda: f"GB{random.randint(100000000, 999999999)}",
            "IE": lambda: f"IE{random.randint(1000000, 9999999)}{random.choice(['W', ''])}",
            "DE": lambda: f"DE{random.randint(100000000, 999999999)}",
            "FR": lambda: f"FR{random.randint(100000000, 999999999)}",
            "NL": lambda: f"NL{random.randint(100000000, 999999999)}B{random.randint(1, 99)}",
            "BE": lambda: f"BE{random.randint(1000000000, 9999999999)}",
            "FI": lambda: f"FI{random.randint(10000000, 99999999)}"
        }
        return formats.get(country, formats["UK"])()
    
    @staticmethod
    def generate_isin(country: str = "GB") -> str:
        """Generate an ISIN."""
        country_codes = {
            "UK": "GB", "IE": "IE", "DE": "DE",
            "FR": "FR", "NL": "NL", "BE": "BE", "FI": "FI"
        }
        prefix = country_codes.get(country, "XX")
        suffix = ''.join(str(random.randint(0, 9)) for _ in range(10))
        return f"{prefix}{suffix}"
    
    @staticmethod
    def generate_lei() -> str:
        """Generate a LEI (Legal Entity Identifier)."""
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return ''.join(random.choices(chars, k=20))
    
    @staticmethod
    def generate_sedol() -> str:
        """Generate a SEDOL."""
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return ''.join(random.choices(chars, k=7))
    
    @staticmethod
    def generate_eircode() -> str:
        """Generate an Irish Eircode."""
        pattern = "D{1,2}[0-9]{1,2}[A-Z]{1,2}[0-9]{1,2}[A-Z]{2}"
        # Simplified generation
        area = random.choice(["D", "A", "B", "C", "E", "F", "H", "K", "N", "P", "R", "T", "V", "W", "X", "Y"])
        number = random.randint(1, 99)
        suffix = ''.join(random.choices(string.ascii_uppercase, k=2))
        return f"{area}{number}{suffix}{random.randint(10, 99)}{''.join(random.choices(string.ascii_uppercase, k=1))}"
    
    @staticmethod
    def generate_filename(extension: str = "pdf") -> str:
        """Generate a realistic filename."""
        prefixes = ["invoice", "receipt", "statement", "report", "document", "upload", "scan", "export"]
        date = random.randint(1, 28)
        month = random.randint(1, 12)
        year = random.randint(2020, 2026)
        prefix = random.choice(prefixes)
        return f"{prefix}_{year}{month:02d}{date:02d}_{IDGenerator.generate_short_id(6)}.{extension}"
    
    @staticmethod
    def generate_reference_number(prefix: str = "REF") -> str:
        """Generate a reference number."""
        return f"{prefix}{random.randint(100000, 999999)}{random.choice(string.ascii_uppercase)}"
    
    @staticmethod
    def generate_invoice_number() -> str:
        """Generate an invoice number."""
        year = random.randint(2020, 2026)
        return f"INV-{year}-{random.randint(10000, 99999)}"
    
    @staticmethod
    def generate_batch_id() -> str:
        """Generate a batch ID."""
        date = datetime.now().strftime("%Y%m%d")
        return f"BATCH-{date}-{IDGenerator.generate_short_id(6)}"