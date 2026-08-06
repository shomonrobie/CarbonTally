#!/usr/bin/env python3
"""
CarbonTally Demo Data Generator
Module 1: Organization Generator

This module generates realistic organization data for European companies
across multiple industries and countries. It produces a CSV file that can
be used as seed data for the CarbonTally platform.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

import csv
import json
import random
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path

from faker import Faker
from faker.providers import company, internet, address, date_time, lorem

# ============================================================================
# Configuration
# ============================================================================

class Config:
    """Configuration settings for organization generation."""
    
    # Output settings
    OUTPUT_DIR = Path("data_output")
    OUTPUT_FILE = "organizations.csv"
    
    # Generation settings
    NUM_ORGANIZATIONS = 100
    START_DATE = datetime(2025, 8, 1)  # 12 months of historical data
    END_DATE = datetime(2026, 8, 2)    # Current date
    
    # Random seed for reproducibility
    RANDOM_SEED = 42
    
    # Regional settings
    SUPPORTED_COUNTRIES = [
        "UK", "IE", "DE", "FR", "NL", "BE", "FI"
    ]
    
    # Industry settings
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
    
    # Company size categories
    COMPANY_SIZES = {
        "small": (10, 49),
        "medium": (50, 249),
        "large": (250, 999),
        "enterprise": (1000, 50000)
    }
    
    # Reporting standards
    REPORTING_STANDARDS = [
        "GHG Protocol",
        "ISO 14064",
        "SECR",
        "ESRS",
        "ISSB"
    ]
    
    # Subscription tiers
    SUBSCRIPTION_TIERS = [
        "free",
        "starter",
        "professional", 
        "enterprise"
    ]
    
    # Timezones by country
    COUNTRY_TIMEZONES = {
        "UK": "Europe/London",
        "IE": "Europe/Dublin",
        "DE": "Europe/Berlin",
        "FR": "Europe/Paris",
        "NL": "Europe/Amsterdam",
        "BE": "Europe/Brussels",
        "FI": "Europe/Helsinki"
    }
    
    # Currency by country
    COUNTRY_CURRENCIES = {
        "UK": "GBP",
        "IE": "EUR",
        "DE": "EUR",
        "FR": "EUR",
        "NL": "EUR",
        "BE": "EUR",
        "FI": "EUR"
    }
    
    # Default language by country
    COUNTRY_LANGUAGES = {
        "UK": "en-GB",
        "IE": "en-IE",
        "DE": "de-DE",
        "FR": "fr-FR",
        "NL": "nl-NL",
        "BE": "nl-BE",
        "FI": "fi-FI"
    }


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Address:
    """Address data model."""
    address_line1: str
    address_line2: Optional[str]
    city: str
    county: Optional[str]
    postcode: str
    country: str
    eircode: Optional[str] = None  # Irish postal code
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert address to dictionary."""
        return {
            "address_line1": self.address_line1,
            "address_line2": self.address_line2 or "",
            "city": self.city,
            "county": self.county or "",
            "postcode": self.postcode,
            "country": self.country,
            "eircode": self.eircode or ""
        }


@dataclass
class Organization:
    """Organization data model representing a company or entity."""
    
    # Core fields
    id: uuid.UUID
    name: str
    company_number: str
    vat_number: str
    
    # Classification
    industry: str
    sector: str
    company_size: str
    
    # Location
    country: str
    registered_address: str
    address_line1: str
    address_line2: str
    city: str
    county: str
    postcode: str
    eircode: str
    
    # Contact
    website: str
    primary_contact_email: str
    primary_contact_name: str
    billing_contact_email: str
    billing_contact_name: str
    
    # Regional settings
    timezone: str
    currency: str
    language: str
    locale: str
    
    # Financial
    financial_year_end: Optional[datetime]
    vat_region: str
    vat_registered: bool
    tax_region: str
    tax_rate: float
    
    # Reporting
    reporting_standard: str
    reporting_frequency: str
    accounting_standard: str
    sustainability_standard: str
    secr_enabled: bool
    esrs_enabled: bool
    issb_enabled: bool
    
    # Registration
    registration_number: str
    registration_region: str
    business_structure: str
    is_public: bool
    is_listed: bool
    
    # Corporate identifiers
    isin: Optional[str]
    cik: Optional[str]
    sedol: Optional[str]
    lei: Optional[str]
    
    # Subscription
    subscription_status: str
    subscription_tier: str
    subscription_id: Optional[str]
    trial_start_date: Optional[datetime]
    trial_end_date: Optional[datetime]
    
    # Billing
    billing_address: str
    billing_contact_email: str
    billing_contact_name: str
    
    # Carbon/tax
    carbon_tax_region: str
    default_defra_version: int
    
    # Preferences
    preferred_units: str
    default_defra_version: int
    
    # Compliance
    data_protection_officer: Optional[str]
    privacy_policy_url: Optional[str]
    terms_url: Optional[str]
    
    # Metadata
    metadata: Dict[str, Any]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    def to_csv_row(self) -> Dict[str, Any]:
        """Convert organization to CSV row dictionary."""
        return {
            "id": str(self.id),
            "name": self.name,
            "company_number": self.company_number,
            "vat_number": self.vat_number,
            "industry": self.industry,
            "sector": self.sector,
            "company_size": self.company_size,
            "country": self.country,
            "registered_address": self.registered_address,
            "address_line1": self.address_line1,
            "address_line2": self.address_line2,
            "city": self.city,
            "county": self.county,
            "postcode": self.postcode,
            "eircode": self.eircode,
            "website": self.website,
            "primary_contact_email": self.primary_contact_email,
            "primary_contact_name": self.primary_contact_name,
            "billing_contact_email": self.billing_contact_email,
            "billing_contact_name": self.billing_contact_name,
            "timezone": self.timezone,
            "currency": self.currency,
            "language": self.language,
            "locale": self.locale,
            "financial_year_end": self.financial_year_end.strftime("%Y-%m-%d") if self.financial_year_end else "",
            "vat_region": self.vat_region,
            "vat_registered": str(self.vat_registered).lower(),
            "tax_region": self.tax_region,
            "tax_rate": str(self.tax_rate),
            "reporting_standard": self.reporting_standard,
            "reporting_frequency": self.reporting_frequency,
            "accounting_standard": self.accounting_standard,
            "sustainability_standard": self.sustainability_standard,
            "secr_enabled": str(self.secr_enabled).lower(),
            "esrs_enabled": str(self.esrs_enabled).lower(),
            "issb_enabled": str(self.issb_enabled).lower(),
            "registration_number": self.registration_number,
            "registration_region": self.registration_region,
            "business_structure": self.business_structure,
            "is_public": str(self.is_public).lower(),
            "is_listed": str(self.is_listed).lower(),
            "isin": self.isin or "",
            "cik": self.cik or "",
            "sedol": self.sedol or "",
            "lei": self.lei or "",
            "subscription_status": self.subscription_status,
            "subscription_tier": self.subscription_tier,
            "subscription_id": self.subscription_id or "",
            "trial_start_date": self.trial_start_date.strftime("%Y-%m-%d %H:%M:%S%z") if self.trial_start_date else "",
            "trial_end_date": self.trial_end_date.strftime("%Y-%m-%d %H:%M:%S%z") if self.trial_end_date else "",
            "billing_address": self.billing_address,
            "carbon_tax_region": self.carbon_tax_region,
            "default_defra_version": str(self.default_defra_version),
            "preferred_units": self.preferred_units,
            "data_protection_officer": self.data_protection_officer or "",
            "privacy_policy_url": self.privacy_policy_url or "",
            "terms_url": self.terms_url or "",
            "metadata": json.dumps(self.metadata),
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S%z"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S%z")
        }


# ============================================================================
# Data Generators
# ============================================================================

class OrganizationGenerator:
    """
    Primary class for generating organization data.
    
    This class handles the generation of realistic organization data
    for European companies using Faker and custom logic.
    """
    
    def __init__(self, config: Config = None):
        """
        Initialize the organization generator.
        
        Args:
            config: Configuration object. If None, default Config is used.
        """
        self.config = config or Config()
        
        # Initialize Faker with European locales
        self.faker = Faker([
            'en_GB', 'en_IE', 'de_DE', 'fr_FR', 'nl_NL'
        ])
        
        # Add custom providers
        self.faker.add_provider(company)
        self.faker.add_provider(internet)
        self.faker.add_provider(address)
        self.faker.add_provider(date_time)
        
        # Set random seed for reproducibility
        random.seed(self.config.RANDOM_SEED)
        
        # Initialize counters and caches
        self._organization_counter = 0
        self._used_names = set()
        self._used_numbers = set()
        
        # Create output directory
        self.config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    def generate_organizations(self, count: int = None) -> List[Organization]:
        """
        Generate a list of organizations.
        
        Args:
            count: Number of organizations to generate. If None, uses config value.
            
        Returns:
            List of Organization objects.
        """
        count = count or self.config.NUM_ORGANIZATIONS
        
        organizations = []
        for _ in range(count):
            org = self._generate_single_organization()
            organizations.append(org)
            
        return organizations
    
    def _generate_single_organization(self) -> Organization:
        """
        Generate a single organization with realistic data.
        
        Returns:
            Organization object with complete data.
        """
        # Select country and industry first (as they influence many fields)
        country = random.choice(self.config.SUPPORTED_COUNTRIES)
        industry = random.choice(self.config.INDUSTRIES)
        
        # Generate base data
        company_name = self._generate_company_name(country, industry)
        company_size = self._determine_company_size(industry)
        
        # Generate address
        address = self._generate_address(country)
        
        # Generate contact information
        contact = self._generate_contact_info(country)
        
        # Generate timestamps
        created_at = self._generate_random_timestamp()
        updated_at = self._generate_update_timestamp(created_at)
        
        # Build the organization object
        return Organization(
            id=uuid.uuid4(),
            name=company_name,
            company_number=self._generate_company_number(country),
            vat_number=self._generate_vat_number(country),
            industry=industry,
            sector=self._generate_sector(industry),
            company_size=company_size,
            country=country,
            registered_address=self._format_address(address),
            address_line1=address.address_line1,
            address_line2=address.address_line2 or "",
            city=address.city,
            county=address.county or "",
            postcode=address.postcode,
            eircode=address.eircode or "",
            website=self._generate_website(company_name),
            primary_contact_email=contact['email'],
            primary_contact_name=contact['name'],
            billing_contact_email=contact['billing_email'],
            billing_contact_name=contact['billing_name'],
            timezone=Config.COUNTRY_TIMEZONES[country],
            currency=Config.COUNTRY_CURRENCIES[country],
            language=Config.COUNTRY_LANGUAGES[country],
            locale=Config.COUNTRY_LANGUAGES[country].replace('-', '_'),
            financial_year_end=self._generate_financial_year_end(),
            vat_region=self._generate_vat_region(country),
            vat_registered=True,
            tax_region=country,
            tax_rate=self._generate_tax_rate(country),
            reporting_standard=random.choice(Config.REPORTING_STANDARDS),
            reporting_frequency=self._generate_reporting_frequency(),
            accounting_standard="IFRS" if country != "UK" else "UK GAAP",
            sustainability_standard=random.choice(["GRI", "SASB", "TCFD"]),
            secr_enabled=country in ["UK", "IE"],
            esrs_enabled=country in ["DE", "FR", "NL", "BE", "FI"],
            issb_enabled=True,
            registration_number=self._generate_registration_number(country),
            registration_region=country,
            business_structure=self._generate_business_structure(country),
            is_public=random.random() < 0.2,  # 20% public companies
            is_listed=random.random() < 0.15,  # 15% listed companies
            isin=self._generate_isin(country) if random.random() < 0.15 else None,
            cik=None,  # US-only
            sedol=self._generate_sedol() if random.random() < 0.15 else None,
            lei=self._generate_lei() if random.random() < 0.1 else None,
            subscription_status=random.choice(["active", "trial", "expired", "cancelled"]),
            subscription_tier=random.choice(Config.SUBSCRIPTION_TIERS),
            subscription_id=None,  # Would be generated by billing system
            trial_start_date=self._generate_trial_start(created_at),
            trial_end_date=self._generate_trial_end(created_at),
            billing_address=self._format_address(address),
            billing_contact_email=contact['billing_email'],
            billing_contact_name=contact['billing_name'],
            carbon_tax_region=country,
            default_defra_version=self._generate_defra_version(),
            preferred_units=random.choice(["metric", "imperial"]),
            data_protection_officer=contact['dpo_name'] if random.random() < 0.3 else None,
            privacy_policy_url=f"https://{self._generate_domain(company_name)}/privacy",
            terms_url=f"https://{self._generate_domain(company_name)}/terms",
            metadata=self._generate_metadata(),
            created_at=created_at,
            updated_at=updated_at
        )
    
    def _generate_company_name(self, country: str, industry: str) -> str:
        """
        Generate a realistic company name based on country and industry.
        
        Args:
            country: Country code
            industry: Industry sector
            
        Returns:
            Realistic company name.
        """
        suffixes = {
            "UK": ["Ltd", "PLC", "Group", "Holdings", "Partners"],
            "IE": ["Ltd", "Group", "Holdings", "Partners"],
            "DE": ["GmbH", "AG", "KG", "Group"],
            "FR": ["SAS", "SA", "Sarl", "Group"],
            "NL": ["B.V.", "N.V.", "Group"],
            "BE": ["NV", "SA", "Group"],
            "FI": ["Oy", "Group"]
        }
        
        prefixes = {
            "Construction": ["Build", "Construct", "Develop", "Arch", "Structure", "Foundation"],
            "Manufacturing": ["Industrial", "Manufacture", "Produce", "Fabricate", "Create", "Engineering"],
            "Retail": ["Shop", "Retail", "Market", "Trade", "Store", "Merchant"],
            "Healthcare": ["Health", "Care", "Medical", "Wellness", "Pharma", "Life"],
            "Technology": ["Tech", "Digital", "Innovate", "Data", "Cyber", "Cloud", "AI"],
            "Logistics": ["Logist", "Transport", "Freight", "Courier", "Supply", "Chain"],
            "Hospitality": ["Hotel", "Lodge", "Hospitality", "Cater", "Resort", "Inn"],
            "Energy": ["Energy", "Power", "Renew", "Solar", "Eco", "Wind", "Hydro"]
        }
        
        # Generate company name components
        prefix = random.choice(prefixes[industry])
        suffix = random.choice(suffixes[country])
        
        # Add location or adjective for variety
        locations = ["European", "British", "Irish", "German", "French", "Dutch", "Nordic"]
        adjectives = ["Premier", "Advanced", "Global", "National", "Regional", "Leading"]
        
        name_parts = [
            f"{random.choice(adjectives)} {prefix}",
            f"{prefix} {random.choice(locations)}",
            f"{prefix} Solutions",
            f"{prefix} Group"
        ]
        
        company_name = random.choice(name_parts)
        
        # Ensure uniqueness
        counter = 1
        base_name = company_name
        while company_name in self._used_names:
            company_name = f"{base_name} {counter}"
            counter += 1
        
        self._used_names.add(company_name)
        
        # Add suffix if not already present
        if not any(company_name.endswith(s) for s in suffixes[country]):
            company_name = f"{company_name} {suffix}"
        
        return company_name
    
    def _generate_address(self, country: str) -> Address:
        """
        Generate a realistic address for a given country.
        
        Args:
            country: Country code
            
        Returns:
            Address object.
        """
        country_config = {
            "UK": {
                "faker_locale": "en_GB",
                "postcode_format": lambda: self.faker.postcode(),
                "city": lambda: self.faker.city(),
                "county": lambda: self.faker.county()
            },
            "IE": {
                "faker_locale": "en_IE",
                "postcode_format": lambda: f"D{random.randint(1, 24)}{random.choice(['', 'W', 'N', 'S', 'E'])}",
                "city": lambda: random.choice(["Dublin", "Cork", "Limerick", "Galway", "Waterford", "Kilkenny"]),
                "county": lambda: random.choice(["Dublin", "Cork", "Limerick", "Galway", "Waterford", "Kilkenny"])
            },
            "DE": {
                "faker_locale": "de_DE",
                "postcode_format": lambda: f"{random.randint(1000, 99999)}",
                "city": lambda: self.faker.city(),
                "county": lambda: self.faker.state()
            },
            "FR": {
                "faker_locale": "fr_FR",
                "postcode_format": lambda: f"{random.randint(1000, 99999)}",
                "city": lambda: self.faker.city(),
                "county": lambda: self.faker.department()
            },
            "NL": {
                "faker_locale": "nl_NL",
                "postcode_format": lambda: f"{random.randint(1000, 9999)} {random.choice(['AB', 'CD', 'EF', 'GH', 'IJ', 'KL', 'MN', 'OP', 'QR', 'ST', 'UV', 'WX', 'YZ'])}",
                "city": lambda: self.faker.city(),
                "county": lambda: self.faker.province()
            },
            "BE": {
                "faker_locale": "nl_BE",
                "postcode_format": lambda: f"{random.randint(1000, 9999)}",
                "city": lambda: self.faker.city(),
                "county": lambda: self.faker.province()
            },
            "FI": {
                "faker_locale": "fi_FI",
                "postcode_format": lambda: f"{random.randint(1000, 99999)}",
                "city": lambda: self.faker.city(),
                "county": lambda: self.faker.province()
            }
        }
        
        cfg = country_config[country]
        
        # Temporarily switch Faker locale
        original_locale = self.faker.locale
        self.faker.locale = cfg["faker_locale"]
        
        # Generate address components
        street_number = random.randint(1, 999)
        street_name = self.faker.street_name()
        address_line1 = f"{street_number} {street_name}"
        
        # Sometimes add building or unit
        if random.random() < 0.3:
            address_line1 = f"{address_line1}, {random.choice(['Unit', 'Suite', 'Floor', 'Building'])} {random.randint(1, 20)}"
        
        city = cfg["city"]()
        postcode = cfg["postcode_format"]()
        
        # Restore original locale
        self.faker.locale = original_locale
        
        # Special handling for Ireland (Eircode)
        eircode = None
        if country == "IE":
            eircode = f"D{random.randint(1, 24)}{random.choice(['W', 'N', 'S', 'E'])}XY{random.randint(1, 99)}"
        
        return Address(
            address_line1=address_line1,
            address_line2=None if random.random() < 0.7 else self.faker.street_name(),
            city=city,
            county=cfg["county"]() if country in ["UK", "IE"] else None,
            postcode=postcode,
            country=country,
            eircode=eircode
        )
    
    def _generate_contact_info(self, country: str) -> Dict[str, str]:
        """
        Generate contact information including names and emails.
        
        Args:
            country: Country code
            
        Returns:
            Dictionary containing contact information.
        """
        # Generate names appropriate for country
        first_names = {
            "UK": ["James", "Sarah", "Michael", "Emma", "David", "Lisa", "John", "Karen", "Robert", "Helen"],
            "IE": ["Seán", "Niamh", "Patrick", "Siobhán", "Conor", "Aoife", "Ciarán", "Caoimhe", "Darragh", "Orla"],
            "DE": ["Hans", "Anna", "Klaus", "Maria", "Peter", "Sabine", "Thomas", "Monika", "Andreas", "Julia"],
            "FR": ["Jean", "Marie", "Pierre", "Sophie", "Louis", "Isabelle", "François", "Catherine", "Philippe", "Élisabeth"],
            "NL": ["Jan", "Anne", "Willem", "Linda", "Pieter", "Karin", "Gerard", "Monique", "Hubert", "Petra"],
            "BE": ["Jean", "Marie", "Luc", "Lea", "Marc", "Anne", "Henri", "Cécile", "Philippe", "Elisabeth"],
            "FI": ["Juhani", "Maria", "Matti", "Helena", "Mika", "Johanna", "Olli", "Riitta", "Pekka", "Kaisa"]
        }
        
        last_names = {
            "UK": ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"],
            "IE": ["Murphy", "Kelly", "O'Brien", "Ryan", "O'Connor", "Walsh", "O'Sullivan", "Doyle", "McCarthy", "Gallagher"],
            "DE": ["Schmidt", "Müller", "Weber", "Schneider", "Fischer", "Meyer", "Wagner", "Becker", "Schulz", "Hoffmann"],
            "FR": ["Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau"],
            "NL": ["Janssen", "Van der Meer", "De Vries", "Van Dijk", "Bakker", "Visser", "Smit", "Mulder", "De Jong", "Van den Berg"],
            "BE": ["Peeters", "Janssens", "Maes", "Vermeulen", "Dupont", "Lambert", "Dubois", "Martin", "Bernard", "Thijs"],
            "FI": ["Korhonen", "Virtanen", "Nieminen", "Mäkelä", "Kallio", "Heikkilä", "Järvinen", "Laine", "Salminen", "Lehtonen"]
        }
        
        # Select names
        first_name = random.choice(first_names[country])
        last_name = random.choice(last_names[country])
        
        # Generate email
        email = self._generate_email(first_name, last_name, country)
        
        # Generate billing contact
        billing_first = random.choice(first_names[country])
        billing_last = random.choice(last_names[country])
        billing_email = self._generate_email(billing_first, billing_last, country)
        
        # Generate DPO name (sometimes)
        dpo_name = None
        if random.random() < 0.3:
            dpo_first = random.choice(first_names[country])
            dpo_last = random.choice(last_names[country])
            dpo_name = f"{dpo_first} {dpo_last}"
        
        return {
            'name': f"{first_name} {last_name}",
            'email': email,
            'billing_name': f"{billing_first} {billing_last}",
            'billing_email': billing_email,
            'dpo_name': dpo_name
        }
    
    def _generate_email(self, first_name: str, last_name: str, country: str) -> str:
        """
        Generate a realistic email address.
        
        Args:
            first_name: First name
            last_name: Last name
            country: Country code
            
        Returns:
            Email address.
        """
        domains = {
            "UK": [".co.uk", ".com"],
            "IE": [".ie", ".com"],
            "DE": [".de", ".com"],
            "FR": [".fr", ".com"],
            "NL": [".nl", ".com"],
            "BE": [".be", ".com"],
            "FI": [".fi", ".com"]
        }
        
        # Generate email formats
        formats = [
            f"{first_name.lower()}.{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()}",
            f"{first_name.lower()}{last_name.lower()[0]}",
            f"{first_name.lower()[0]}{last_name.lower()}",
            f"{first_name.lower()}_{last_name.lower()}"
        ]
        
        email_prefix = random.choice(formats)
        email_domain = random.choice(domains[country])
        
        return f"{email_prefix}@carbontally{email_domain}"
    
    def _generate_website(self, company_name: str) -> str:
        """Generate a realistic website URL from company name."""
        # Clean company name for domain
        clean_name = company_name.lower().replace(' ', '').replace("'", '').replace('.', '')
        # Remove common suffixes
        for suffix in ['ltd', 'plc', 'gmbh', 'ag', 'sas', 'sa', 'sarl', 'bv', 'nv', 'oy']:
            clean_name = clean_name.replace(suffix, '')
        
        domain = f"https://{clean_name}.com"
        
        # Add some variety
        if random.random() < 0.3:
            tld = random.choice(['co.uk', 'eu', 'io'])
            domain = f"https://{clean_name}.{tld}"
        
        return domain
    
    def _generate_domain(self, company_name: str) -> str:
        """Generate a domain name from company name."""
        clean_name = company_name.lower().replace(' ', '').replace("'", '').replace('.', '')
        for suffix in ['ltd', 'plc', 'gmbh', 'ag', 'sas', 'sa', 'sarl', 'bv', 'nv', 'oy']:
            clean_name = clean_name.replace(suffix, '')
        return f"{clean_name}.com"
    
    def _generate_company_number(self, country: str) -> str:
        """Generate a company registration number for a specific country."""
        formats = {
            "UK": lambda: f"{random.randint(10000000, 99999999)}",
            "IE": lambda: f"{random.randint(100000, 999999)}",
            "DE": lambda: f"HRB {random.randint(10000, 99999)}",
            "FR": lambda: f"RCS {random.choice(['Paris', 'Lyon', 'Marseille'])} {random.randint(100000000, 999999999)}",
            "NL": lambda: f"{random.randint(10000000, 99999999)}",
            "BE": lambda: f"{random.randint(100000000, 999999999)}",
            "FI": lambda: f"{random.randint(1000000, 9999999)}"
        }
        
        number = formats[country]()
        
        # Ensure uniqueness
        counter = 1
        base_number = number
        while number in self._used_numbers:
            number = f"{base_number}_{counter}"
            counter += 1
        
        self._used_numbers.add(number)
        return number
    
    def _generate_vat_number(self, country: str) -> str:
        """Generate a VAT number for a specific country."""
        formats = {
            "UK": lambda: f"GB{random.randint(100000000, 999999999)}",
            "IE": lambda: f"IE{random.randint(1000000, 9999999)}{random.choice(['W', ''])}",
            "DE": lambda: f"DE{random.randint(100000000, 999999999)}",
            "FR": lambda: f"FR{random.randint(100000000, 999999999)}",
            "NL": lambda: f"NL{random.randint(100000000, 999999999)}B{random.randint(1, 99)}",
            "BE": lambda: f"BE{random.randint(1000000000, 9999999999)}",
            "FI": lambda: f"FI{random.randint(10000000, 99999999)}"
        }
        
        return formats[country]()
    
    def _generate_sector(self, industry: str) -> str:
        """Generate a detailed sector within an industry."""
        sector_map = {
            "Construction": ["Residential", "Commercial", "Infrastructure", "Industrial", "Renovation", "Civil Engineering"],
            "Manufacturing": ["Automotive", "Electronics", "Food & Beverage", "Textiles", "Chemicals", "Pharmaceuticals"],
            "Retail": ["E-commerce", "Brick & Mortar", "Food Retail", "Fashion", "Electronics", "Furniture"],
            "Healthcare": ["Hospitals", "Pharmaceuticals", "Medical Devices", "Healthcare Services", "Biotech", "Research"],
            "Technology": ["Software", "Hardware", "Cloud Services", "AI/ML", "Cybersecurity", "Fintech"],
            "Logistics": ["Freight", "Courier", "Warehousing", "Supply Chain", "Cold Chain", "Last Mile Delivery"],
            "Hospitality": ["Hotels", "Restaurants", "Resorts", "Event Management", "Catering", "Travel & Tourism"],
            "Energy": ["Renewable", "Oil & Gas", "Utilities", "Energy Services", "Solar", "Wind Power"]
        }
        
        return random.choice(sector_map[industry])
    
    def _determine_company_size(self, industry: str) -> str:
        """Determine company size based on industry."""
        # Different industries have different size distributions
        size_weights = {
            "Construction": {"small": 0.3, "medium": 0.4, "large": 0.2, "enterprise": 0.1},
            "Manufacturing": {"small": 0.15, "medium": 0.3, "large": 0.35, "enterprise": 0.2},
            "Retail": {"small": 0.35, "medium": 0.35, "large": 0.2, "enterprise": 0.1},
            "Healthcare": {"small": 0.2, "medium": 0.35, "large": 0.3, "enterprise": 0.15},
            "Technology": {"small": 0.4, "medium": 0.3, "large": 0.2, "enterprise": 0.1},
            "Logistics": {"small": 0.2, "medium": 0.35, "large": 0.3, "enterprise": 0.15},
            "Hospitality": {"small": 0.4, "medium": 0.3, "large": 0.2, "enterprise": 0.1},
            "Energy": {"small": 0.1, "medium": 0.25, "large": 0.35, "enterprise": 0.3}
        }
        
        weights = size_weights[industry]
        sizes = list(weights.keys())
        probabilities = list(weights.values())
        
        return random.choices(sizes, weights=probabilities)[0]
    
    def _generate_reporting_frequency(self) -> str:
        """Generate a reporting frequency."""
        return random.choice(["monthly", "quarterly", "annually"])
    
    def _generate_financial_year_end(self) -> datetime:
        """Generate a financial year end date."""
        year = random.choice([2024, 2025])
        month = random.choice([3, 6, 9, 12])  # Common FYE months
        day = random.choice([31, 30, 28, 29])
        return datetime(year, month, min(day, 28))
    
    def _generate_vat_region(self, country: str) -> str:
        """Generate VAT region."""
        return country
    
    def _generate_tax_rate(self, country: str) -> float:
        """Generate a tax rate for a specific country."""
        rates = {
            "UK": 19.0,
            "IE": 12.5,
            "DE": 19.0,
            "FR": 25.0,
            "NL": 21.0,
            "BE": 25.0,
            "FI": 20.0
        }
        
        # Add small variation
        rate = rates[country]
        rate += random.uniform(-2, 2)
        return round(rate, 1)
    
    def _generate_registration_number(self, country: str) -> str:
        """Generate a registration number."""
        return f"REG{random.randint(100000, 999999)}"
    
    def _generate_business_structure(self, country: str) -> str:
        """Generate a business structure."""
        structures = {
            "UK": ["Limited", "Public Limited", "Sole Trader", "Partnership", "LLP"],
            "IE": ["Limited", "PLC", "Sole Trader", "Partnership", "LLP"],
            "DE": ["GmbH", "AG", "KG", "OHG", "Einzelunternehmen"],
            "FR": ["SAS", "SA", "SARL", "Entreprise Individuelle", "EURL"],
            "NL": ["BV", "NV", "Eenmanszaak", "VOF"],
            "BE": ["NV", "SA", "BVBA", "CommV"],
            "FI": ["Oy", "Osakeyhtiö", "Toiminimi", "Avoin yhtiö", "Kommandiittiyhtiö"]
        }
        
        return random.choice(structures[country])
    
    def _generate_isin(self, country: str) -> str:
        """Generate an ISIN (International Securities Identification Number)."""
        country_codes = {
            "UK": "GB",
            "IE": "IE",
            "DE": "DE",
            "FR": "FR",
            "NL": "NL",
            "BE": "BE",
            "FI": "FI"
        }
        
        prefix = country_codes[country]
        suffix = ''.join([str(random.randint(0, 9)) for _ in range(10)])
        return f"{prefix}{suffix}"
    
    def _generate_sedol(self) -> str:
        """Generate a SEDOL (Stock Exchange Daily Official List)."""
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return ''.join(random.choice(chars) for _ in range(7))
    
    def _generate_lei(self) -> str:
        """Generate a LEI (Legal Entity Identifier)."""
        chars = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        return ''.join(random.choice(chars) for _ in range(20))
    
    def _generate_trial_start(self, created_at: datetime) -> Optional[datetime]:
        """Generate a trial start date."""
        if random.random() < 0.7:  # 70% have trials
            return created_at + timedelta(days=random.randint(0, 30))
        return None
    
    def _generate_trial_end(self, created_at: datetime) -> Optional[datetime]:
        """Generate a trial end date."""
        start = self._generate_trial_start(created_at)
        if start:
            return start + timedelta(days=random.randint(14, 90))
        return None
    
    def _generate_defra_version(self) -> int:
        """Generate a DEFRA conversion factor version."""
        return random.choice([2020, 2021, 2022, 2023, 2024])
    
    def _generate_metadata(self) -> Dict[str, Any]:
        """Generate organization metadata."""
        return {
            "source": "demo_data_generator",
            "version": "1.0.0",
            "generated_at": datetime.now().isoformat(),
            "random_seed": self.config.RANDOM_SEED,
            "additional_info": {
                "number_of_employees": random.randint(10, 50000),
                "annual_revenue": random.randint(1000000, 1000000000),
                "has_sustainability_report": random.random() < 0.4,
                "carbon_verified": random.random() < 0.3
            }
        }
    
    def _generate_random_timestamp(self) -> datetime:
        """Generate a random timestamp within the allowed range."""
        delta = self.config.END_DATE - self.config.START_DATE
        random_days = random.randint(0, delta.days)
        random_seconds = random.randint(0, 86400)  # Seconds in a day
        return self.config.START_DATE + timedelta(days=random_days, seconds=random_seconds)
    
    def _generate_update_timestamp(self, created_at: datetime) -> datetime:
        """Generate an update timestamp after creation."""
        if random.random() < 0.7:  # 70% chance of being updated
            delta = datetime.now() - created_at
            random_days = random.randint(1, max(1, delta.days))
            return created_at + timedelta(days=random_days)
        return created_at
    
    def _format_address(self, address: Address) -> str:
        """Format address as a single string."""
        parts = [
            address.address_line1,
            address.address_line2,
            address.city,
            address.county,
            address.postcode,
            address.country
        ]
        parts = [p for p in parts if p]
        return ", ".join(parts)


# ============================================================================
# CSV Writer
# ============================================================================

class CSVWriter:
    """Handles writing organization data to CSV files."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize the CSV writer.
        
        Args:
            output_dir: Directory to write CSV files.
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def write_organizations(self, organizations: List[Organization], filename: str):
        """
        Write organizations to a CSV file.
        
        Args:
            organizations: List of Organization objects.
            filename: Output filename.
        """
        if not organizations:
            return
        
        filepath = self.output_dir / filename
        
        # Get CSV header from the first organization
        sample_row = organizations[0].to_csv_row()
        fieldnames = list(sample_row.keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for org in organizations:
                writer.writerow(org.to_csv_row())
        
        print(f"✅ Wrote {len(organizations)} organizations to {filepath}")


# ============================================================================
# Main Execution
# ============================================================================

def main():
    """Main execution function."""
    print("🚀 CarbonTally Organization Generator")
    print("=" * 60)
    print(f"📊 Generating {Config.NUM_ORGANIZATIONS} organizations...")
    
    # Initialize generator and writer
    config = Config()
    generator = OrganizationGenerator(config)
    writer = CSVWriter(config.OUTPUT_DIR)
    
    # Generate organizations
    organizations = generator.generate_organizations()
    
    # Write to CSV
    writer.write_organizations(organizations, config.OUTPUT_FILE)
    
    # Print summary
    print("\n📈 Summary:")
    print(f"   Total organizations: {len(organizations)}")
    
    # Count by country
    country_counts = {}
    for org in organizations:
        country_counts[org.country] = country_counts.get(org.country, 0) + 1
    
    print("\n   By country:")
    for country, count in sorted(country_counts.items()):
        print(f"      {country}: {count}")
    
    # Count by industry
    industry_counts = {}
    for org in organizations:
        industry_counts[org.industry] = industry_counts.get(org.industry, 0) + 1
    
    print("\n   By industry:")
    for industry, count in sorted(industry_counts.items()):
        print(f"      {industry}: {count}")
    
    print("\n✅ Generation complete!")
    print(f"📁 Output file: {config.OUTPUT_DIR / config.OUTPUT_FILE}")


if __name__ == "__main__":
    main()