#!/usr/bin/env python3
"""
CarbonTally Demo Data Generator - Configuration
Central configuration for all data generation modules.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class Config:
    """Master configuration for the data generator."""
    
    # ==========================================
    # Project Structure
    # ==========================================
    PROJECT_ROOT = Path(__file__).parent
    OUTPUT_DIR = PROJECT_ROOT / "data_output"
    GENERATORS_DIR = PROJECT_ROOT / "generators"
    
    # ==========================================
    # Generation Settings
    # ==========================================
    RANDOM_SEED = 42  # For reproducibility
    START_DATE = datetime(2025, 8, 1)  # 12 months ago
    END_DATE = datetime(2026, 8, 2)    # Current date
    
    # ==========================================
    # Scale Settings (Target Numbers)
    # ==========================================
    SCALE = {
        "organizations": 100,
        "staff": 100,
        "consultants": 50,
        "consultant_companies": 10,
        "organization_users": 250,
        "facilities": 300,
        "assets": 500,
        "suppliers": 5000,
        "documents": 50000,
        "ocr_jobs": 100000,
        "ai_jobs": 100000,
        "carbon_calculations": 80000,
        "reports": 20000,
        "notifications": 25000,
        "messages": 10000,
        "tasks": 50000,
        "audit_logs": 500000,
    }
    
    # ==========================================
    # Batch Processing
    # ==========================================
    BATCH_SIZE = 1000  # Records per batch for large tables
    ENABLE_PROGRESS_BAR = True
    ENABLE_LOGGING = True
    
    # ==========================================
    # Regional Settings
    # ==========================================
    SUPPORTED_COUNTRIES = ["UK", "IE", "DE", "FR", "NL", "BE", "FI"]
    
    COUNTRY_TIMEZONES = {
        "UK": "Europe/London",
        "IE": "Europe/Dublin",
        "DE": "Europe/Berlin",
        "FR": "Europe/Paris",
        "NL": "Europe/Amsterdam",
        "BE": "Europe/Brussels",
        "FI": "Europe/Helsinki"
    }
    
    COUNTRY_CURRENCIES = {
        "UK": "GBP",
        "IE": "EUR",
        "DE": "EUR",
        "FR": "EUR",
        "NL": "EUR",
        "BE": "EUR",
        "FI": "EUR"
    }
    
    # ==========================================
    # Industry Settings
    # ==========================================
    INDUSTRIES = [
        "Construction",
        "Manufacturing",
        "Retail",
        "Healthcare",
        "Technology",
        "Logistics",
        "Hospitality",
        "Energy"
    ]
    
    # ==========================================
    # Business Settings
    # ==========================================
    COMPANY_SIZES = {
        "small": (10, 49),
        "medium": (50, 249),
        "large": (250, 999),
        "enterprise": (1000, 50000)
    }
    
    SUBSCRIPTION_TIERS = ["free", "starter", "professional", "enterprise"]
    REPORTING_STANDARDS = ["GHG Protocol", "ISO 14064", "SECR", "ESRS", "ISSB"]
    
    # ==========================================
    # File Settings
    # ==========================================
    CSV_ENCODING = "utf-8"
    CSV_DELIMITER = ","
    CSV_QUOTE_CHAR = '"'
    
    # ==========================================
    # Logging
    # ==========================================
    LOG_FILE = PROJECT_ROOT / "generation.log"
    LOG_LEVEL = "INFO"
    
    # ==========================================
    # Data Quality
    # ==========================================
    MINIMAL_DATE = datetime(2020, 1, 1)
    MAX_DATE = datetime(2026, 12, 31)
    DEFAULT_TIMEZONE = "UTC"
    
    @classmethod
    def get_country_config(cls, country_code: str) -> Dict[str, Any]:
        """Get country-specific configuration."""
        return {
            "timezone": cls.COUNTRY_TIMEZONES.get(country_code, "UTC"),
            "currency": cls.COUNTRY_CURRENCIES.get(country_code, "EUR"),
            "supported": country_code in cls.SUPPORTED_COUNTRIES
        }
    
    @classmethod
    def get_company_size(cls, size_key: str) -> tuple:
        """Get employee range for company size."""
        return cls.COMPANY_SIZES.get(size_key, (10, 49))
    
    @classmethod
    def get_random_country(cls) -> str:
        """Get a random supported country."""
        import random
        return random.choice(cls.SUPPORTED_COUNTRIES)
    
    @classmethod
    def get_random_industry(cls) -> str:
        """Get a random industry."""
        import random
        return random.choice(cls.INDUSTRIES)