markdown
# CarbonTally Demo Data Generator

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

Enterprise-grade data generation framework for CarbonTally platform demos. Produces production-quality demonstration data with realistic business scenarios spanning 12 months of historical activity.

## 📊 Key Features

- **97+ Data Modules**: Complete coverage of all database tables
- **1.5M+ Records**: Generates realistic enterprise-scale data
- **12 Months History**: Natural activity distribution over time
- **European Focus**: Realistic UK, Irish, German, French, Dutch, Belgian, and Finnish data
- **Industry Specific**: 8 major industries with realistic business patterns
- **No Placeholder Data**: All data is generated with real-world naming conventions
- **Referential Integrity**: All foreign keys are valid and consistent
- **CSV Output**: Easy to import or convert to SQL

## 🏗️ Architecture
demo_data_generator/
├── config.py # Central configuration
├── generators/ # All data generators
│ ├── core/ # Core identity data
│ ├── facilities/ # Facilities & assets
│ ├── documents/ # Documents & processing
│ ├── carbon/ # Carbon accounting
│ └── collaboration/ # Communication & tasks
├── scripts/ # Utility scripts
├── utils/ # Shared utilities
└── data_output/ # Generated CSV files

text

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/carbontally/demo-data-generator.git
cd demo-data-generator

# Install dependencies
pip install -r requirements.txt
Generate All Data
bash
python scripts/run_all_generators.py
Generate Specific Module
bash
# Example: Generate only organizations
python -m generators.core.generate_organizations

# Example: Generate only users
python -m generators.core.generate_users
Validate Generated Data
bash
python scripts/validate_data.py
Export to SQL
bash
python scripts/export_to_sql.py --format postgres --output seed_data.sql
📋 Module List
Phase 1: Core Identity
✅ generate_users.py - Users (staff, consultants, members)

✅ generate_organizations.py - Organizations

✅ generate_staff_profiles.py - Staff profiles & roles

✅ generate_consultant_profiles.py - Consultant firms

✅ generate_organization_members.py - Organization members

Phase 2: Facilities
✅ generate_facilities.py - Facilities

✅ generate_assets.py - Assets

Phase 3: Documents
✅ generate_document_types.py - Document types

✅ generate_customer_documents.py - Customer documents

✅ generate_organization_files.py - Organization files

Phase 4: Carbon
✅ generate_activity_categories.py - Activity categories

✅ generate_emissions_logs.py - Emissions calculations

Phase 5: Collaboration
✅ generate_conversations.py - Conversations

✅ generate_messages.py - Messages

✅ generate_notifications.py - Notifications

✅ generate_internal_tasks.py - Tasks

🔧 Configuration
All settings in config.py can be modified to adjust scale, data distribution, and output settings:

python
# Scale settings
SCALE = {
    "organizations": 100,
    "staff": 100,
    "documents": 50000,
    # ...
}

# Regional focus
SUPPORTED_COUNTRIES = ["UK", "IE", "DE", "FR", "NL", "BE", "FI"]

# Industry focus
INDUSTRIES = ["Construction", "Manufacturing", "Retail", ...]
📊 Data Output
Generated data is output as CSV files in data_output/:

text
data_output/
├── organizations.csv        # 100 organizations
├── users.csv               # 400+ users
├── facilities.csv          # 300 facilities
├── documents.csv           # 50,000 documents
├── emissions_logs.csv      # 80,000 calculations
├── messages.csv            # 10,000 messages
└── ... (97+ files)
🧪 Data Quality
All generated data follows these quality rules:

✅ No Lorem Ipsum or placeholder text

✅ Realistic European company names

✅ Valid postal codes and addresses

✅ Consistent industry-sector relationships

✅ Proper date ranges and historical patterns

✅ Complete foreign key references

✅ Realistic business scenarios

📈 Business Scenarios
The generator creates realistic business scenarios:

Failed OCR: Some documents fail and require manual correction

Rejected Reports: Reports sent back for revision

Missing Data: Suppliers with incomplete emissions data

Overdue Tasks: Some tasks are escalated

Varying Trends: Organizations show improving or deteriorating emissions

Support Tickets: Mix of open, pending, and resolved tickets

🤝 Contributing
Fork the repository

Create a feature branch

Add your generator module

Update documentation

Submit a pull request

📄 License
MIT License - see LICENSE file for details.

🏢 About CarbonTally
CarbonTally is an enterprise carbon accounting platform that helps organizations measure, manage, and report their greenhouse gas emissions.