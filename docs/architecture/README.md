## Entity Relationship Diagram
┌─────────────────────────────────────────────────────────────┐
│ auth.users │
│ (All authenticated users) │
└─────────────────────┬───────────────────────────────────────┘
│
┌───────────┴───────────┐
│ │
▼ ▼
┌─────────────────┐ ┌─────────────────────────────────────┐
│ staff_profiles │ │ organization_members │
│ (CarbonTally │ │ (Customer organization members) │
│ employees) │ │ │
│ │ │ organization_id ─────┐ │
│ - admin │ │ role: admin/editor/viewer │
│ - data_extractor│ └─────────────────────────────────────┘
│ - staff │ │
│ - reviewer │ ▼
└─────────────────┘ ┌─────────────────────────────────────┐
│ organizations │
│ (Customer organizations) │
└─────────────────────────────────────┘

text

---

## Authentication Flow

### User Types

1. **Anonymous User**
   - Can: View public pages, sign up, log in
   - Cannot: Access API endpoints

2. **Authenticated User** (in auth.users)
   - Can: Access public endpoints with valid JWT
   - Cannot: Access admin or org-specific endpoints

3. **Organization Member** (in organization_members)
   - Can: Access org-specific endpoints based on role
   - Roles: admin, editor, viewer

4. **Staff Member** (in staff_profiles)
   - Can: Access internal admin endpoints
   - Roles: admin, data_extractor, staff, reviewer

### Authentication Flow
User submits credentials (email/password)
↓

Supabase Auth validates credentials
↓

JWT token returned to client
↓

Client includes token in Authorization header
↓

Backend validates token with Supabase
↓

Backend checks user role/permissions
↓

Access granted/denied based on role

text

### JWT Token Validation

```python
# Backend validates token in auth.py
async def get_current_user(credentials: HTTPAuthorizationCredentials):
    token = credentials.credentials
    user = supabase.auth.get_user(token)  # Validate with Supabase
    # Check staff_profiles or organization_members
    # Return AuthUser with roles/permissions
Permission Matrix
API Access Control
Endpoint Type	Anonymous	Authenticated	Org Member	Staff
Public (/, /health)	✅	✅	✅	✅
Waitlist	✅	✅	✅	✅
User Profile	❌	✅	✅	✅
Organization Data	❌	❌	✅	✅
Organization Admin	❌	❌	✅ (admin)	✅
Staff Admin	❌	❌	❌	✅ (admin)
System Settings	❌	❌	❌	✅ (admin)
Staff Roles & Permissions
Role	Permissions
admin	Full system access, manage staff, system settings, all data
data_extractor	Process documents, extract data, review queue
staff	View data, process assignments, basic operations
reviewer	Review extracted data, approve/reject submissions
Organization Roles & Permissions
Role	Permissions
admin	Manage org settings, members, all org data
editor	Edit org data, upload documents, generate reports
viewer	View org data, download reports
API Architecture
Route Organization
text
backend/routes/
├── __init__.py              # Route registry
├── admin/                   # Staff-only endpoints
│   ├── staff.py            # Staff management
│   ├── defra.py            # DEFRA factor management
│   ├── extraction.py       # Data extraction
│   ├── reviews.py          # Review queue
│   ├── assignments.py      # Review assignments
│   ├── workload.py         # Staff workload
│   ├── beta.py             # Beta program
│   ├── audit.py            # Audit logs
│   ├── review_history.py   # Review history
│   ├── logs.py             # System logs
│   └── staff_enhanced.py   # Staff performance
├── organizations/           # Organization endpoints
│   ├── management.py       # Org CRUD
│   ├── members.py          # Member management
│   ├── assets.py           # Facilities & assets
│   ├── data.py             # Org data
│   ├── analytics.py        # Analytics
│   ├── dashboard.py        # Dashboard
│   ├── files.py            # File management
│   ├── team.py             # Team management
│   ├── metadata.py         # Org metadata
│   ├── exports.py          # Data exports
│   └── bulk.py             # Bulk operations
├── documents/               # Document management
│   ├── main.py             # Document CRUD
│   └── activity.py         # Document activity
├── emissions.py             # Emissions tracking
├── feedback.py              # User feedback
├── glossary.py              # Glossary terms
├── users.py                 # User profile
├── waitlist.py              # Waitlist
├── upload.py                # File uploads
├── reports.py               # Reports
├── drafts.py                # Drafts
├── drafts_enhanced.py       # Enhanced drafts
├── reference.py             # Reference data
├── logs.py                  # Activity logs
└── notifications.py         # Notifications
API Response Format
json
{
  "success": true,
  "data": { ... },
  "message": "Operation successful"
}
Error Response Format
json
{
  "success": false,
  "error": {
    "code": 403,
    "message": "Not authorized",
    "timestamp": "2026-07-28T03:23:37.277361",
    "path": "/api/users/profile"
  }
}
Development Workflow
Local Development
bash
# 1. Clone repository
git clone https://github.com/your-repo/carbon_ledger.git

# 2. Set up environment
cp .env.example .env
# Edit .env with your Supabase credentials

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start server
uvicorn main:app --reload
Testing
bash
# Run all tests
python backend/tests/test_api_simple.py

# Run specific test
python backend/tests/test_api_simple.py --test=users

# Run with coverage
pytest --cov=backend tests/
Deployment
Backend: Deploy to Render/Heroku

Frontend: Deploy to Vercel

Database: Supabase (managed)

Storage: Supabase Storage

Security
Authentication
JWT tokens via Supabase Auth

Tokens expire after 24 hours

Refresh tokens supported

Authorization
Role-based access control (RBAC)

Permission-based checks for fine-grained access

Data Security
RLS policies in Supabase

Row-level security for multi-tenant data

Encrypted sensitive data

API Security
CORS configured for trusted domains

Rate limiting (planned)

Input validation with Pydantic

Monitoring & Logging
Logs
Activity logs in activity_logs table

Email logs in email_logs table

Processing logs in processing_logs table

Audit trails in review_audit_trail table

Health Checks
/health - System health

/admin/analytics/system/health - Detailed health

/admin/analytics/system/performance - Performance metrics

Future Improvements
□ Redis caching
□ Rate limiting
□ WebSocket for real-time updates
□ Background job queue (Celery)
□ API versioning
□ GraphQL support
□ Automated backup
□ Disaster recovery
Contributing
Code Style
Follow PEP 8

Use type hints

Document functions with docstrings

PR Process
Fork repository

Create feature branch

Write tests

Submit PR with description

Documentation
Keep this document updated

Update API docs when endpoints change

Document new features

Support
Documentation: https://docs.carbontally.co.uk

API Reference: https://api.carbontally.co.uk/docs

Issues: GitHub Issues

Slack: #carbontally-support

License
Copyright © 2024 CarbonTally. All rights reserved.

text

## 3. API Documentation

Create `docs/api/README.md`:

```markdown
# CarbonTally API Documentation

## Quick Links

- **Live API**: [https://api.carbontally.co.uk](https://api.carbontally.co.uk)
- **Swagger UI**: [https://api.carbontally.co.uk/docs](https://api.carbontally.co.uk/docs)
- **ReDoc**: [https://api.carbontally.co.uk/redoc](https://api.carbontally.co.uk/redoc)

## Authentication

### Supabase Auth

CarbonTally uses Supabase Auth for authentication. To access the API, you need a valid JWT token.

#### Get Token

```bash
# Using Supabase Auth (same as frontend)
# Use Supabase client or API
Use Token
bash
curl -X GET https://api.carbontally.co.uk/api/users/profile \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
User Types
Type	Description	Access
Authenticated User	Logged in user	Basic endpoints
Organization Member	Member of an org	Org-specific endpoints
Staff	CarbonTally employee	Admin endpoints
Endpoints Overview
Public Endpoints
markdown
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | API info |
| GET | /health | Health check |
| POST | /api/waitlist/ | Join waitlist |
User Endpoints
markdown
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/users/profile | Get profile |
| PUT | /api/users/profile | Update profile |
| POST | /api/users/change-password | Change password |
Organization Endpoints
markdown
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/organizations/ | List orgs |
| POST | /api/organizations/ | Create org |
| GET | /api/organizations/{id} | Get org |
| PUT | /api/organizations/{id} | Update org |
| DELETE | /api/organizations/{id} | Delete org |
Admin Endpoints
markdown
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/admin/staff | List staff |
| GET | /api/admin/staff/performance | Staff performance |
| GET | /api/admin/queue/settings | Queue settings |
| GET | /api/admin/beta/codes | Beta codes |
| GET | /api/admin/audit/activity | Audit logs |
Full endpoint list available in Swagger UI.

Rate Limiting
Tier	Requests per minute
Free	60
Pro	300
Enterprise	Unlimited
Error Codes
Code	Description
200	Success
201	Created
400	Bad Request
401	Unauthorized
403	Forbidden
404	Not Found
500	Internal Server Error
text

## 4. Development Guide

Create `docs/guides/development.md`:

```markdown
# CarbonTally Development Guide

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Supabase account
- Git

### Setup

1. **Clone repository**
```bash
git clone https://github.com/your-repo/carbon_ledger.git
cd carbon_ledger
Backend setup

bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your credentials
Frontend setup

bash
cd frontend
npm install
cp .env.example .env.local
# Edit .env.local with your credentials
Run development server

bash
# Backend
uvicorn main:app --reload

# Frontend (in another terminal)
cd frontend
npm start
Database Migrations
bash
# Generate migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head
Testing
Backend Tests
bash
# Run all tests
python backend/tests/test_api_simple.py

# Run with coverage
pytest --cov=backend tests/
Frontend Tests
bash
cd frontend
npm test
Adding New Endpoints
Create/update route file in backend/routes/

Define Pydantic models

Implement endpoint with proper authentication

Add to __init__.py

Write tests

Update documentation

Adding New Tables
Create migration

Add RLS policies

Update models

Add endpoints

Common Tasks
Add a new admin endpoint
python
# backend/routes/admin/new_feature.py
from fastapi import APIRouter, Depends
from auth import AuthUser, require_admin

router = APIRouter(prefix="/api/admin/new-feature", tags=["Admin"])

@router.get("/")
async def get_data(
    current_user: AuthUser = Depends(require_admin())
):
    # Your logic here
    return {"data": "..."}
Add a new organization endpoint
python
# backend/routes/organizations/new_feature.py
from fastapi import APIRouter, Depends
from auth import AuthUser, require_org_member

router = APIRouter(prefix="/api/organizations/{org_id}/new-feature", tags=["Organizations"])

@router.get("/")
async def get_org_data(
    org_id: str,
    current_user: AuthUser = Depends(require_org_member())
):
    # Your logic here
    return {"data": "..."}
Debugging
Backend Logs
bash
# Check logs
tail -f logs/uvicorn.log
Database Queries
sql
-- Enable query logging
SET log_statement = 'all';

-- Check slow queries
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;
Common Issues
Authentication Errors
Error: "User does not have access to this system"
Solution: Add user to staff_profiles or organization_members

Error: "Invalid authentication credentials"
Solution: Check token validity, ensure user exists in Supabase

Database Errors
Error: "Could not find a relationship between tables"
Solution: Check foreign key constraints, use correct join syntax

CORS Errors
Error: CORS policy blocking requests
Solution: Add origin to ALLOWED_ORIGINS in config

Performance Tips
Use database indexes

Paginate large results

Use caching for frequent queries

Optimize N+1 queries

Use async/await properly

text

## 5. Update Root README

Update `D:\carbon_ledger\README.md`:

```markdown
# CarbonTally

Automated Carbon Accounting for UK Businesses

## Quick Start

```bash
# Clone repository
git clone https://github.com/your-repo/carbon_ledger.git
cd carbon_ledger

# Setup
cp .env.example .env
# Edit .env with your Supabase credentials

# Start server
uvicorn main:app --reload
Documentation
Architecture

API Reference

Development Guide

License
Copyright © 2024 CarbonTally. All rights reserved.

text

## 6. Create Summary Script

```python
# docs/generate_docs.py
"""
Generate documentation summary
Run: python docs/generate_docs.py
"""

import os
from pathlib import Path

def create_summary():
    """Create documentation summary"""
    
    summary = """
# CarbonTally Documentation

## Table of Contents

### Architecture
- [System Overview](architecture/README.md#system-overview)
- [Tech Stack](architecture/README.md#tech-stack)
- [Database Schema](architecture/README.md#database-schema)
- [Entity Relationship Diagram](architecture/README.md#entity-relationship-diagram)
- [Authentication Flow](architecture/README.md#authentication-flow)
- [Permission Matrix](architecture/README.md#permission-matrix)
- [API Architecture](architecture/README.md#api-architecture)

### API Reference
- [Quick Links](api/README.md#quick-links)
- [Authentication](api/README.md#authentication)
- [Endpoints Overview](api/README.md#endpoints-overview)
- [Rate Limiting](api/README.md#rate-limiting)
- [Error Codes](api/README.md#error-codes)

### Development
- [Getting Started](guides/development.md#getting-started)
- [Database Migrations](guides/development.md#database-migrations)
- [Testing](guides/development.md#testing)
- [Adding New Endpoints](guides/development.md#adding-new-endpoints)
- [Debugging](guides/development.md#debugging)

## Quick Links

- **Live API**: https://api.carbontally.co.uk
- **Swagger UI**: https://api.carbontally.co.uk/docs
- **ReDoc**: https://api.carbontally.co.uk/redoc
- **Frontend**: https://carbontally.co.uk
- **Admin Panel**: https://admin.carbontally.co.uk

## Support

- Documentation: https://docs.carbontally.co.uk
- Issues: GitHub Issues
- Slack: #carbontally-support
"""
    
    with open('docs/README.md', 'w') as f:
        f.write(summary)
    
    print("✅ Documentation summary created!")

if __name__ == "__main__":
    create_summary()
Run it:

bash
cd D:\carbon_ledger
python docs/generate_docs.py
Final Structure
text
D:\carbon_ledger/
├── README.md                    # Root README
├── docs/
│   ├── README.md               # Documentation home
│   ├── architecture/
│   │   └── README.md           # Architecture docs
│   ├── api/
│   │   └── README.md           # API docs
│   └── guides/
│       └── development.md      # Development guide
├── backend/
│   ├── routes/                 # API routes
│   ├── tests/                  # Tests
│   └── ...
└── frontend/
    └── ...