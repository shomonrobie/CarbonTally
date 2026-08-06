#!/usr/bin/env python3
"""
CarbonTally Data Generator - Organizations
Generates realistic organization data.

Author: CarbonTally Data Team
Version: 1.0.0
Date: 2026-08-02
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from faker import Faker
from faker.providers import company, internet, address, date_time

from config import Config
from generators.base_generator import BaseGenerator
from utils import IDGenerator, DateUtils


@dataclass
class Organization:
    """Organization data model."""
    id: str
    name: str
    company_number: str
    vat_number: str
    industry: str
    sector: str
    company_size: str
    country: str
    registered_address: str
    address_line1: str
    address_line2: str
    city: str
    county: str
    postcode: str
    eircode: str
    website: str
    primary_contact_email: str
    primary_contact_name: str
    billing_contact_email: str
    billing_contact_name: str
    timezone: str
    currency: str
    language: str
    locale: str
    financial_year_end: datetime
    vat_region: str
    vat_registered: bool
    tax_region: str
    tax_rate: float
    reporting_standard: str
    reporting_frequency: str
    accounting_standard: str
    sustainability_standard: str
    secr_enabled: bool
    esrs_enabled: bool
    issb_enabled: bool
    registration_number: str
    registration_region: str
    business_structure: str
    is_public: bool
    is_listed: bool
    isin: Optional[str]
    cik: Optional[str]
    sedol: Optional[str]
    lei: Optional[str]
    subscription_status: str
    subscription_tier: str
    subscription_id: Optional[str]
    trial_start_date: Optional[datetime]
    trial_end_date: Optional[datetime]
    billing_address: str
    carbon_tax_region: str
    default_defra_version: int
    preferred_units: str
    data_protection_officer: Optional[str]
    privacy_policy_url: Optional[str]
    terms_url: Optional[str]
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime


class OrganizationGenerator(BaseGenerator):
    """Generates organization data."""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the organization generator."""
        super().__init__(config)
        
        # Initialize Faker with European locales
        self.faker = Faker(['en_GB', 'en_IE', 'de_DE', 'fr_FR', 'nl_NL'])
        self.faker.add_provider(company)
        self.faker.add_provider(internet)
        self.faker.add_provider(address)
        self.faker.add_provider(date_time)
        
        # Track used names and numbers
        self.used_names = set()
        self.used_numbers = set()
        
        # Country-specific data
        self.country_data = self._load_country_data()
        self.industry_data = self._load_industry_data()
    
    def _load_country_data(self) -> Dict[str, Any]:
        """Load country-specific data."""
        return {
            "UK": {
                "locales": ["en_GB"],
                "company_suffixes": ["Ltd", "PLC", "Group", "Holdings", "Partners"],
                "business_structures": ["Limited", "Public Limited", "Sole Trader", "Partnership", "LLP"],
                "postcode_pattern": r'^([A-Z]{1,2}\d[A-Z\d]? ?\d[A-Z]{2}|GIR ?0AA)$',
                "vat_format": "GB{9-12 digits}",
                "tax_rate": 19.0
            },
            "IE": {
                "locales": ["en_IE"],
                "company_suffixes": ["Ltd", "Group", "Holdings", "Partners"],
                "business_structures": ["Limited", "PLC", "Sole Trader", "Partnership", "LLP"],
                "postcode_pattern": r'^[A-Z]{1,2}\d{1,2} ?[A-Z]{1,2}\d{1,2}$',
                "vat_format": "IE{7 digits}{W or empty}",
                "tax_rate": 12.5
            },
            "DE": {
                "locales": ["de_DE"],
                "company_suffixes": ["GmbH", "AG", "KG", "Group"],
                "business_structures": ["GmbH", "AG", "KG", "OHG", "Einzelunternehmen"],
                "postcode_pattern": r'^\d{5}$',
                "vat_format": "DE{9 digits}",
                "tax_rate": 19.0
            },
            "FR": {
                "locales": ["fr_FR"],
                "company_suffixes": ["SAS", "SA", "Sarl", "Group"],
                "business_structures": ["SAS", "SA", "SARL", "Entreprise Individuelle", "EURL"],
                "postcode_pattern": r'^\d{5}$',
                "vat_format": "FR{2 chars}{9 digits}",
                "tax_rate": 25.0
            },
            "NL": {
                "locales": ["nl_NL"],
                "company_suffixes": ["B.V.", "N.V.", "Group"],
                "business_structures": ["BV", "NV", "Eenmanszaak", "VOF"],
                "postcode_pattern": r'^\d{4} ?[A-Z]{2}$',
                "vat_format": "NL{9 digits}B{2 digits}",
                "tax_rate": 21.0
            },
            "BE": {
                "locales": ["nl_BE"],
                "company_suffixes": ["NV", "SA", "Group"],
                "business_structures": ["NV", "SA", "BVBA", "CommV"],
                "postcode_pattern": r'^\d{4}$',
                "vat_format": "BE{10 digits}",
                "tax_rate": 25.0
            },
            "FI": {
                "locales": ["fi_FI"],
                "company_suffixes": ["Oy", "Group"],
                "business_structures": ["Oy", "Osakeyhtiö", "Toiminimi", "Avoin yhtiö", "Kommandiittiyhtiö"],
                "postcode_pattern": r'^\d{5}$',
                "vat_format": "FI{8 digits}",
                "tax_rate": 20.0
            }
        }
    
    def _load_industry_data(self) -> Dict[str, Any]:
        """Load industry-specific data."""
        return {
            "Construction": {
                "sectors": ["Residential", "Commercial", "Infrastructure", "Industrial", "Renovation", "Civil Engineering"],
                "size_weights": {"small": 0.3, "medium": 0.4, "large": 0.2, "enterprise": 0.1},
                "name_prefixes": ["Build", "Construct", "Develop", "Arch", "Structure", "Foundation"],
                "company_size": "large"
            },
            "Manufacturing": {
                "sectors": ["Automotive", "Electronics", "Food & Beverage", "Textiles", "Chemicals", "Pharmaceuticals"],
                "size_weights": {"small": 0.15, "medium": 0.3, "large": 0.35, "enterprise": 0.2},
                "name_prefixes": ["Industrial", "Manufacture", "Produce", "Fabricate", "Create", "Engineering"],
                "company_size": "large"
            },
            "Retail": {
                "sectors": ["E-commerce", "Brick & Mortar", "Food Retail", "Fashion", "Electronics", "Furniture"],
                "size_weights": {"small": 0.35, "medium": 0.35, "large": 0.2, "enterprise": 0.1},
                "name_prefixes": ["Shop", "Retail", "Market", "Trade", "Store", "Merchant"],
                "company_size": "medium"
            },
            "Healthcare": {
                "sectors": ["Hospitals", "Pharmaceuticals", "Medical Devices", "Healthcare Services", "Biotech", "Research"],
                "size_weights": {"small": 0.2, "medium": 0.35, "large": 0.3, "enterprise": 0.15},
                "name_prefixes": ["Health", "Care", "Medical", "Wellness", "Pharma", "Life"],
                "company_size": "large"
            },
            "Technology": {
                "sectors": ["Software", "Hardware", "Cloud Services", "AI/ML", "Cybersecurity", "Fintech"],
                "size_weights": {"small": 0.4, "medium": 0.3, "large": 0.2, "enterprise": 0.1},
                "name_prefixes": ["Tech", "Digital", "Innovate", "Data", "Cyber", "Cloud", "AI"],
                "company_size": "medium"
            },
            "Logistics": {
                "sectors": ["Freight", "Courier", "Warehousing", "Supply Chain", "Cold Chain", "Last Mile Delivery"],
                "size_weights": {"small": 0.2, "medium": 0.35, "large": 0.3, "enterprise": 0.15},
                "name_prefixes": ["Logist", "Transport", "Freight", "Courier", "Supply", "Chain"],
                "company_size": "large"
            },
            "Hospitality": {
                "sectors": ["Hotels", "Restaurants", "Resorts", "Event Management", "Catering", "Travel & Tourism"],
                "size_weights": {"small": 0.4, "medium": 0.3, "large": 0.2, "enterprise": 0.1},
                "name_prefixes": ["Hotel", "Lodge", "Hospitality", "Cater", "Resort", "Inn"],
                "company_size": "medium"
            },
            "Energy": {
                "sectors": ["Renewable", "Oil & Gas", "Utilities", "Energy Services", "Solar", "Wind Power"],
                "size_weights": {"small": 0.1, "medium": 0.25, "large": 0.35, "enterprise": 0.3},
                "name_prefixes": ["Energy", "Power", "Renew", "Solar", "Eco", "Wind", "Hydro"],
                "company_size": "enterprise"
            }
        }
    
    def generate(self) -> List[Organization]:
        """Generate organizations."""
        total = self.config.SCALE.get("organizations", 100)
        organizations = []
        
        for _ in range(total):
            org = self._generate_organization()
            organizations.append(org)
        
        self.logger.info(f"Generated {len(organizations)} organizations")
        return organizations
    
    def _generate_organization(self) -> Organization:
        """Generate a single organization."""
        # Select country and industry
        country = random.choice(self.config.SUPPORTED_COUNTRIES)
        industry = random.choice(self.config.INDUSTRIES)
        
        # Get country data
        country_config = self.country_data[country]
        industry_config = self.industry_data[industry]
        
        # Generate company name
        name = self._generate_name(country, industry, country_config, industry_config)
        
        # Generate address
        address_data = self._generate_address(country)
        
        # Generate contact info
        contacts = self._generate_contacts(country)
        
        # Determine company size
        size = self._determine_size(industry_config)
        
        # Generate company number
        company_number = self._generate_company_number(country)
        
        # Generate VAT number
        vat_number = self._generate_vat_number(country)
        
        # Generate dates
        created_at = self.date_utils.random_date(
            self.config.START_DATE,
            self.config.END_DATE
        )
        updated_at = self._generate_update_date(created_at)
        
        # Generate financial year end
        financial_year_end = self.date_utils.random_financial_year_end(country)
        
        # Generate subscription data
        subscription_status = random.choice(["active", "trial", "expired", "cancelled"])
        subscription_tier = random.choice(self.config.SUBSCRIPTION_TIERS)
        
        # Generate trial dates
        trial_start = None
        trial_end = None
        if random.random() < 0.7:
            trial_start = created_at + timedelta(days=random.randint(0, 30))
            trial_end = trial_start + timedelta(days=random.randint(14, 90))
        
        # Generate metadata
        metadata = {
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
        
        # Build organization object
        return Organization(
            id=str(uuid.uuid4()),
            name=name,
            company_number=company_number,
            vat_number=vat_number,
            industry=industry,
            sector=random.choice(industry_config["sectors"]),
            company_size=size,
            country=country,
            registered_address=self._format_address(address_data),
            address_line1=address_data["address_line1"],
            address_line2=address_data.get("address_line2", ""),
            city=address_data["city"],
            county=address_data.get("county", ""),
            postcode=address_data["postcode"],
            eircode=address_data.get("eircode", ""),
            website=self._generate_website(name),
            primary_contact_email=contacts["primary_email"],
            primary_contact_name=contacts["primary_name"],
            billing_contact_email=contacts["billing_email"],
            billing_contact_name=contacts["billing_name"],
            timezone=Config.COUNTRY_TIMEZONES[country],
            currency=Config.COUNTRY_CURRENCIES[country],
            language=Config.COUNTRY_LANGUAGES[country],
            locale=Config.COUNTRY_LANGUAGES[country].replace('-', '_'),
            financial_year_end=financial_year_end,
            vat_region=country,
            vat_registered=True,
            tax_region=country,
            tax_rate=country_config["tax_rate"],
            reporting_standard=random.choice(self.config.REPORTING_STANDARDS),
            reporting_frequency=random.choice(["monthly", "quarterly", "annually"]),
            accounting_standard="IFRS" if country != "UK" else "UK GAAP",
            sustainability_standard=random.choice(["GRI", "SASB", "TCFD"]),
            secr_enabled=country in ["UK", "IE"],
            esrs_enabled=country in ["DE", "FR", "NL", "BE", "FI"],
            issb_enabled=True,
            registration_number=f"REG{random.randint(100000, 999999)}",
            registration_region=country,
            business_structure=random.choice(country_config["business_structures"]),
            is_public=random.random() < 0.2,
            is_listed=random.random() < 0.15,
            isin=self.id_gen.generate_isin(country) if random.random() < 0.15 else None,
            cik=None,
            sedol=self.id_gen.generate_sedol() if random.random() < 0.15 else None,
            lei=self.id_gen.generate_lei() if random.random() < 0.1 else None,
            subscription_status=subscription_status,
            subscription_tier=subscription_tier,
            subscription_id=None,
            trial_start_date=trial_start,
            trial_end_date=trial_end,
            billing_address=self._format_address(address_data),
            carbon_tax_region=country,
            default_defra_version=random.choice([2020, 2021, 2022, 2023, 2024]),
            preferred_units=random.choice(["metric", "imperial"]),
            data_protection_officer=contacts.get("dpo_name"),
            privacy_policy_url=f"https://{self._generate_domain(name)}/privacy",
            terms_url=f"https://{self._generate_domain(name)}/terms",
            metadata=metadata,
            created_at=created_at,
            updated_at=updated_at
        )
    
    def _generate_name(self, country: str, industry: str, 
                       country_config: Dict, industry_config: Dict) -> str:
        """Generate a company name."""
        prefixes = industry_config["name_prefixes"]
        suffixes = country_config["company_suffixes"]
        
        # Create name variations
        name_parts = [
            f"{random.choice(prefixes)} {random.choice(['Solutions', 'Group', 'Partners'])}",
            f"{random.choice(['Premier', 'Advanced', 'Global'])} {random.choice(prefixes)}",
            f"{random.choice(prefixes)} {random.choice(['European', 'British', 'National'])}"
        ]
        
        name = random.choice(name_parts)
        
        # Ensure uniqueness
        counter = 1
        base_name = name
        while name in self.used_names:
            name = f"{base_name} {counter}"
            counter += 1
        
        self.used_names.add(name)
        
        # Add suffix if needed
        if not any(name.endswith(s) for s in suffixes):
            name = f"{name} {random.choice(suffixes)}"
        
        return name
    
    def _generate_address(self, country: str) -> Dict[str, Any]:
        """Generate an address."""
        # Create country-specific address
        address = {}
        
        # Street address
        building = random.randint(1, 999)
        street = self.faker.street_name()
        address["address_line1"] = f"{building} {street}"
        
        # Add unit/suite sometimes
        if random.random() < 0.3:
            unit = random.choice(["Unit", "Suite", "Floor", "Building"])
            address["address_line1"] = f"{address['address_line1']}, {unit} {random.randint(1, 20)}"
        
        # City and county
        if country == "IE":
            cities = ["Dublin", "Cork", "Limerick", "Galway", "Waterford", "Kilkenny"]
            address["city"] = random.choice(cities)
            address["county"] = address["city"] if address["city"] in ["Dublin", "Cork"] else random.choice(cities)
            
            # Eircode
            address["eircode"] = self.id_gen.generate_eircode()
            address["postcode"] = address["eircode"]
        else:
            self.faker.locale = random.choice(self.country_data[country]["locales"])
            address["city"] = self.faker.city()
            address["postcode"] = self.faker.postcode()
            if country in ["UK", "IE"]:
                address["county"] = self.faker.county()
            else:
                address["county"] = self.faker.state()
        
        return address
    
    def _generate_contacts(self, country: str) -> Dict[str, str]:
        """Generate contact information."""
        # Country-specific first and last names
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
        
        fname = random.choice(first_names[country])
        lname = random.choice(last_names[country])
        bfname = random.choice(first_names[country])
        blname = random.choice(last_names[country])
        
        return {
            "primary_name": f"{fname} {lname}",
            "primary_email": f"{fname.lower()}.{lname.lower()}@carbontally.com",
            "billing_name": f"{bfname} {blname}",
            "billing_email": f"{bfname.lower()}.{blname.lower()}@carbontally.com",
            "dpo_name": f"{random.choice(first_names[country])} {random.choice(last_names[country])}" if random.random() < 0.3 else None
        }
    
    def _generate_website(self, name: str) -> str:
        """Generate a website URL."""
        domain = self._generate_domain(name)
        return f"https://{domain}"
    
    def _generate_domain(self, name: str) -> str:
        """Generate a domain from a name."""
        clean_name = name.lower().replace(' ', '').replace("'", '').replace('.', '')
        for suffix in ['ltd', 'plc', 'gmbh', 'ag', 'sas', 'sa', 'sarl', 'bv', 'nv', 'oy']:
            clean_name = clean_name.replace(suffix, '')
        tld = random.choice(['com', 'co.uk', 'eu', 'io', 'org'])
        return f"{clean_name}.{tld}"
    
    def _generate_company_number(self, country: str) -> str:
        """Generate a company registration number."""
        number = self.id_gen.generate_company_number(country)
        while number in self.used_numbers:
            number = self.id_gen.generate_company_number(country)
        self.used_numbers.add(number)
        return number
    
    def _generate_vat_number(self, country: str) -> str:
        """Generate a VAT number."""
        return self.id_gen.generate_vat_number(country)
    
    def _determine_size(self, industry_config: Dict) -> str:
        """Determine company size."""
        weights = industry_config["size_weights"]
        sizes = list(weights.keys())
        probabilities = list(weights.values())
        return random.choices(sizes, weights=probabilities)[0]
    
    def _generate_update_date(self, created_at: datetime) -> datetime:
        """Generate an update date."""
        if random.random() < 0.7:
            delta = datetime.now() - created_at
            if delta.days > 0:
                return created_at + timedelta(days=random.randint(1, min(delta.days, 365)))
        return created_at
    
    def _format_address(self, address_data: Dict[str, Any]) -> str:
        """Format address as a single string."""
        parts = [
            address_data.get("address_line1", ""),
            address_data.get("address_line2", ""),
            address_data.get("city", ""),
            address_data.get("county", ""),
            address_data.get("postcode", ""),
            address_data.get("country", "")
        ]
        parts = [p for p in parts if p]
        return ", ".join(parts)
    
    def to_csv_row(self, record: Organization) -> Dict[str, Any]:
        """Convert organization to CSV row."""
        return {
            "id": record.id,
            "name": record.name,
            "company_number": record.company_number,
            "vat_number": record.vat_number,
            "industry": record.industry,
            "sector": record.sector,
            "company_size": record.company_size,
            "country": record.country,
            "registered_address": record.registered_address,
            "address_line1": record.address_line1,
            "address_line2": record.address_line2,
            "city": record.city,
            "county": record.county,
            "postcode": record.postcode,
            "eircode": record.eircode,
            "website": record.website,
            "primary_contact_email": record.primary_contact_email,
            "primary_contact_name": record.primary_contact_name,
            "billing_contact_email": record.billing_contact_email,
            "billing_contact_name": record.billing_contact_name,
            "timezone": record.timezone,
            "currency": record.currency,
            "language": record.language,
            "locale": record.locale,
            "financial_year_end": record.financial_year_end.isoformat() if record.financial_year_end else "",
            "vat_region": record.vat_region,
            "vat_registered": str(record.vat_registered).lower(),
            "tax_region": record.tax_region,
            "tax_rate": str(record.tax_rate),
            "reporting_standard": record.reporting_standard,
            "reporting_frequency": record.reporting_frequency,
            "accounting_standard": record.accounting_standard,
            "sustainability_standard": record.sustainability_standard,
            "secr_enabled": str(record.secr_enabled).lower(),
            "esrs_enabled": str(record.esrs_enabled).lower(),
            "issb_enabled": str(record.issb_enabled).lower(),
            "registration_number": record.registration_number,
            "registration_region": record.registration_region,
            "business_structure": record.business_structure,
            "is_public": str(record.is_public).lower(),
            "is_listed": str(record.is_listed).lower(),
            "isin": record.isin or "",
            "cik": record.cik or "",
            "sedol": record.sedol or "",
            "lei": record.lei or "",
            "subscription_status": record.subscription_status,
            "subscription_tier": record.subscription_tier,
            "subscription_id": record.subscription_id or "",
            "trial_start_date": record.trial_start_date.isoformat() if record.trial_start_date else "",
            "trial_end_date": record.trial_end_date.isoformat() if record.trial_end_date else "",
            "billing_address": record.billing_address,
            "carbon_tax_region": record.carbon_tax_region,
            "default_defra_version": str(record.default_defra_version),
            "preferred_units": record.preferred_units,
            "data_protection_officer": record.data_protection_officer or "",
            "privacy_policy_url": record.privacy_policy_url or "",
            "terms_url": record.terms_url or "",
            "metadata": json.dumps(record.metadata),
            "created_at": record.created_at.isoformat(),
            "updated_at": record.updated_at.isoformat()
        }
    
    def get_csv_fields(self) -> List[str]:
        """Get CSV field names."""
        return [
            "id", "name", "company_number", "vat_number", "industry", "sector",
            "company_size", "country", "registered_address", "address_line1",
            "address_line2", "city", "county", "postcode", "eircode",
            "website", "primary_contact_email", "primary_contact_name",
            "billing_contact_email", "billing_contact_name", "timezone",
            "currency", "language", "locale", "financial_year_end",
            "vat_region", "vat_registered", "tax_region", "tax_rate",
            "reporting_standard", "reporting_frequency", "accounting_standard",
            "sustainability_standard", "secr_enabled", "esrs_enabled",
            "issb_enabled", "registration_number", "registration_region",
            "business_structure", "is_public", "is_listed", "isin",
            "cik", "sedol", "lei", "subscription_status",
            "subscription_tier", "subscription_id", "trial_start_date",
            "trial_end_date", "billing_address", "carbon_tax_region",
            "default_defra_version", "preferred_units",
            "data_protection_officer", "privacy_policy_url", "terms_url",
            "metadata", "created_at", "updated_at"
        ]


def main():
    """Main execution function."""
    print("🚀 CarbonTally Organization Generator")
    print("=" * 60)
    
    # Initialize generator
    generator = OrganizationGenerator()
    
    # Generate organizations
    print("📊 Generating organizations...")
    organizations = generator.generate()
    
    # Write to CSV
    print("💾 Writing to CSV...")
    filepath = generator.write_csv(organizations, "organizations.csv")
    
    print(f"\n✅ Generated {len(organizations)} organizations")
    print(f"📁 Output: {filepath}")


if __name__ == "__main__":
    main()