CarbonTally - Multi-Company Management Strategy
Date: August 2, 2026
Author: Shomon Robie & DeepSeek
Version: 1.0
Status: Strategic Recommendation

1. Market Opportunity
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  MARKET OPPORTUNITY - CONSULTANTS & ADVISORS                                        │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Target Users:                                                                  │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  ● Sustainability Consultants (e.g., EY, Deloitte, boutique firms)       │ │
│  │  │  ● ESG Advisory Firms                                                      │ │
│  │  │  ● Accounting Firms with carbon services                                   │ │
│  │  │  ● Carbon Management Agencies                                              │ │
│  │  │  ● Net Zero Advisors                                                       │ │
│  │  │  ● Energy Consultants                                                      │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Market Size:                                                                   │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  ● UK Sustainability Consulting Market: £2.5B+                             │ │
│  │  │  ● 2,000+ sustainability consultancies in UK                              │ │
│  │  │  ● Each serves 20-100+ clients                                             │ │
│  │  │  ● Significant demand for efficiency tools                                 │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
2. Two Options: Now vs Later
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  DECISION: BUILD NOW OR VERSION 2?                                                  │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  OPTION A: BUILD NOW (Version 1)                                               │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  ✅ First-mover advantage in consultant market                            │ │
│  │  │  ✅ Higher revenue per user                                                │ │
│  │  │  ✅ Attract power users from day one                                      │ │
│  │  │  ✅ More complex to build (requires multi-tenant architecture)            │ │
│  │  │  ⚠️ Delays core product launch                                            │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  OPTION B: VERSION 2 (Recommended)                                             │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  ✅ Launch core product faster                                             │ │
│  │  │  ✅ Validate product-market fit first                                      │ │
│  │  │  ✅ Build multi-company feature with real user feedback                    │ │
│  │  │  ✅ Generate additional revenue stream                                     │ │
│  │  │  ✅ Consultants can use current version (one account per company)          │ │
│  │  │  ⚠️ Need to migrate users later                                            │ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  ✅ RECOMMENDATION: VERSION 2                                                   │ │
│  │                                                                                │ │
│  │  Reason:                                                                        │ │
│  │  1. Launch fast, get customers                                                │ │
│  │  2. Learn from real usage                                                      │ │
│  │  3. Build multi-company properly with real needs                               │ │
│  │  4. Consultants can use product today (one company per account)                │ │
│  │  5. Version 2 becomes a premium upsell                                         │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
3. Version 2: Multi-Company Management Design
3.1 Proposed Architecture
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  VERSION 2 ARCHITECTURE - CONSULTANT DASHBOARD                                      │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │                          CONSULTANT ACCOUNT                                     │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  Consultant Profile                                                         ││ │
│  │  │  ├── Name: GreenPath Sustainability                                       ││ │
│  │  │  ├── Email: consultant@greenpath.com                                      ││ │
│  │  │  ├── Plan: Enterprise (Multi-Company)                                     ││ │
│  │  │  └── Team: 5 advisors                                                     ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  COMPANY A           COMPANY B           COMPANY C         + Add Company   ││ │
│  │  │  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               ││ │
│  │  │  │ Acme Corp       │ │ XYZ Ltd         │ │ Beta Inc        │               ││ │
│  │  │  │ 1,234 tCO2e    │ │ 856 tCO2e      │ │ 2,100 tCO2e    │               ││ │
│  │  │  │ 45 documents   │ │ 23 documents   │ │ 67 documents   │               ││ │
│  │  │  │ Status: Active │ │ Status: Active │ │ Status: Review │               ││ │
│  │  │  │ [Manage]       │ │ [Manage]       │ │ [Manage]       │               ││ │
│  │  │  └─────────────────┘ └─────────────────┘ └─────────────────┘               ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  │                                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  📊 CONSULTANT DASHBOARD                                                    ││ │
│  │  │  ┌─────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  │  Total Clients: 12   Total Emissions: 45,678 tCO2e                     ││ │
│  │  │  │  Reports Generated: 34   Avg Client Size: 3,800 tCO2e                 ││ │
│  │  │  │  Active Projects: 5   Documents Processed: 567                        ││ │
│  │  │  └─────────────────────────────────────────────────────────────────────────┘│ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
3.2 Database Schema Additions
sql
-- ============================================
-- VERSION 2: Multi-Company Management Tables
-- ============================================

-- 1. Consultant/User Accounts
CREATE TABLE consultant_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Consultant Profile
    company_name VARCHAR(255) NOT NULL,
    company_number VARCHAR(100),
    vat_number VARCHAR(100),
    website VARCHAR(255),
    
    -- Plan
    plan VARCHAR(50) DEFAULT 'enterprise_multi',
    subscription_status VARCHAR(50) DEFAULT 'active',
    
    -- Limits
    max_companies INTEGER DEFAULT 50,
    max_team_members INTEGER DEFAULT 20,
    max_clients_per_month INTEGER DEFAULT 1000,
    
    -- Billing
    stripe_customer_id VARCHAR(255),
    billing_email VARCHAR(255),
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- 2. Company-Consultant Relationship (Many-to-Many)
CREATE TABLE consultant_companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultant_account_id UUID NOT NULL REFERENCES consultant_accounts(id),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    
    -- Relationship
    role VARCHAR(50) DEFAULT 'managed', -- 'managed', 'view_only', 'collaborator'
    relationship_type VARCHAR(50) DEFAULT 'consulting', -- 'consulting', 'audit', 'reporting'
    
    -- Access Level
    access_level VARCHAR(50) DEFAULT 'full', -- 'full', 'read_only', 'reports_only'
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_primary BOOLEAN DEFAULT FALSE, -- If consultant owns/manages the account
    
    -- Client Management
    client_reference VARCHAR(100),
    client_contact_name VARCHAR(255),
    client_contact_email VARCHAR(255),
    client_contact_phone VARCHAR(50),
    
    -- Contract
    contract_start_date DATE,
    contract_end_date DATE,
    engagement_type VARCHAR(50), -- 'monthly', 'quarterly', 'project'
    engagement_fee DECIMAL(10,2),
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

-- 3. Consultant Team Members
CREATE TABLE consultant_team_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultant_account_id UUID NOT NULL REFERENCES consultant_accounts(id),
    user_id UUID NOT NULL REFERENCES users(id),
    
    -- Role
    role VARCHAR(50) NOT NULL, -- 'admin', 'analyst', 'viewer'
    
    -- Access
    access_level VARCHAR(50) DEFAULT 'full',
    assigned_companies UUID[] DEFAULT '{}',
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);

-- 4. Cross-Company Reporting
CREATE TABLE cross_company_reports (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultant_account_id UUID NOT NULL REFERENCES consultant_accounts(id),
    
    -- Report Details
    report_name VARCHAR(255) NOT NULL,
    report_type VARCHAR(50) NOT NULL, -- 'summary', 'comparison', 'portfolio'
    report_format VARCHAR(50) DEFAULT 'pdf', -- 'pdf', 'excel', 'powerpoint'
    
    -- Companies Included
    included_companies UUID[] NOT NULL,
    
    -- Data Filters
    data_filters JSONB,
    -- {
    --   "year": 2025,
    --   "scope": ["1", "2", "3"],
    --   "industries": ["technology", "manufacturing"]
    -- }
    
    -- Content
    generated_content JSONB,
    -- {
    --   "executive_summary": "...",
    --   "comparison_analysis": "...",
    --   "charts": {...}
    -- }
    
    -- Status
    status VARCHAR(50) DEFAULT 'generating',
    file_url TEXT,
    file_size_bytes BIGINT,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES users(id),
    generated_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- 5. Consultant Billing & Usage
CREATE TABLE consultant_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    consultant_account_id UUID NOT NULL REFERENCES consultant_accounts(id),
    
    -- Usage Period
    usage_month DATE DEFAULT DATE_TRUNC('month', CURRENT_DATE),
    
    -- Per-Company Usage
    active_companies INTEGER DEFAULT 0,
    total_companies_managed INTEGER DEFAULT 0,
    
    -- Per-Service Usage
    ai_files_processed INTEGER DEFAULT 0,
    manual_pages_extracted INTEGER DEFAULT 0,
    reports_generated INTEGER DEFAULT 0,
    cross_company_reports INTEGER DEFAULT 0,
    
    -- Billing
    billed_amount DECIMAL(10,2) DEFAULT 0,
    billing_currency VARCHAR(3) DEFAULT 'GBP',
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
4. Pricing Model for Version 2
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  VERSION 2 PRICING - CONSULTANT TIER                                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Plan               │ Price      │ Companies │ Team    │ Features              │ │
│  ├─────────────────────┼────────────┼───────────┼─────────┼───────────────────────┤ │
│  │  Consultant Basic   │ $499/mo    │ Up to 5   │ 2 users │ • Company switching  │ │
│  │                     │            │           │         │ • Basic cross-report │ │
│  ├─────────────────────┼────────────┼───────────┼─────────┼───────────────────────┤ │
│  │  Consultant Pro     │ $999/mo    │ Up to 20  │ 5 users │ • Client dashboard   │ │
│  │                     │            │           │         │ • White-label reports│ │
│  │                     │            │           │         │ • API access         │ │
│  ├─────────────────────┼────────────┼───────────┼─────────┼───────────────────────┤ │
│  │  Consultant Premium │ $2,499/mo  │ Up to 100 │ 15 users│ • All features       │ │
│  │                     │            │           │         │ • Client portals     │ │
│  │                     │            │           │         │ • Custom branding    │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
5. Key Features for Version 2
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  VERSION 2 FEATURES                                                                 │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  1. Company Switching                                                          │ │
│  │     ├── Seamless switch between companies                                     │ │
│  │     ├── Context-aware navigation                                              │ │
│  │     └── Company-specific settings                                               │ │
│  ├─────────────────────────────────────────────────────────────────────────────────┤ │
│  │  2. Client Dashboard                                                            │ │
│  │     ├── At-a-glance view of all clients                                        │ │
│  │     ├── Emissions summary per client                                           │ │
│  │     ├── Document status across clients                                        │ │
│  │     └── Quick actions for each client                                          │ │
│  ├─────────────────────────────────────────────────────────────────────────────────┤ │
│  │  3. Cross-Company Reports                                                      │ │
│  │     ├── Compare emissions across clients                                      │ │
│  │     ├── Portfolio-level reporting                                              │ │
│  │     ├── Industry benchmarks                                                    │ │
│  │     └── Combined SECR/CSRD reports                                            │ │
│  ├─────────────────────────────────────────────────────────────────────────────────┤ │
│  │  4. White-Label Reports                                                        │ │
│  │     ├── Consultant branding                                                    │ │
│  │     ├── Custom cover pages                                                     │ │
│  │     ├── Confidentiality notices                                               │ │
│  │     └── Client-specific formatting                                             │ │
│  ├─────────────────────────────────────────────────────────────────────────────────┤ │
│  │  5. Client Portals                                                             │ │
│  │     ├── Client access to their data                                           │ │
│  │     ├── Report sharing                                                         │ │
│  │     ├── Document upload by clients                                            │ │
│  │     └── Approval workflows                                                     │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
6. Consultant User Journey (Version 2)
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  CONSULTANT USER JOURNEY - VERSION 2                                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 1: Consultant Onboarding                                                 ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ● Sign up as Consultant                                                   │││
│  │  │  ● Add team members                                                         │││
│  │  │  ● Set up company profile                                                   │││
│  │  │  ● Choose plan (Basic/Pro/Premium)                                         │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 2: Add Clients                                                            ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ● Add client companies                                                       ││
│  │  │  ● Set up client relationships                                               ││
│  │  │  ● Configure access levels                                                   ││
│  │  │  ● Assign to team members                                                    ││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 3: Manage Clients                                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ● Switch between clients                                                   │││
│  │  │  ● Upload documents for each client                                        │││
│  │  │  ● Generate reports for each client                                        │││
│  │  │  ● Track progress across clients                                           │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                      │                                               │
│                                      ▼                                               │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  STEP 4: Cross-Client Reporting                                                 ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ● Generate portfolio reports                                              │││
│  │  │  ● Compare emissions across clients                                        │││
│  │  │  ● Create board-level presentations                                         │││
│  │  │  ● Share with clients                                                       │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
7. Version 2 Dashboard Mockup
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  🌿 CarbonTally - Consultant Dashboard                                              │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  Dashboard  │ Clients  │ Reports  │ Team  │ Settings  │  👤 Consultant         ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  👋 Welcome, GreenPath Sustainability Team!                          📅 2 Aug 2026  │
│                                                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │  Total       │ │  Active      │ │  Reports     │ │  Documents   │                │
│  │  Clients     │ │  Projects    │ │  Generated   │ │  Processed   │                │
│  │  12          │ │  5           │ │  34          │ │  567         │                │
│  │  ↑ 2 this    │ │  ⏳ 3        │ │  ↓ 8% vs     │ │  ↑ 12% vs    │                │
│  │  month       │ │  completed   │ │  last month  │ │  last month  │                │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📊 Client Portfolio Overview                                                   ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  Client Name     │ Emissions  │ Documents │ Status    │ Actions              ││
│  │  ├──────────────────┼────────────┼───────────┼───────────┼──────────────────────┤│
│  │  │  Acme Corp       │ 1,234 t    │ 45        │ ✅ Active │ [Manage] [Report]   ││
│  │  │  XYZ Ltd         │ 856 t      │ 23        │ ✅ Active │ [Manage] [Report]   ││
│  │  │  Beta Inc        │ 2,100 t    │ 67        │ ⏳ Review │ [Manage] [Report]   ││
│  │  │  Delta Co        │ 456 t      │ 12        │ ⏳ Review │ [Manage] [Report]   ││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  │  [Add Client]  [Generate Portfolio Report]                                      ││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  📈 Cross-Company Emissions Comparison                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  2,500 ┤                                                          ╭╮       │││
│  │  │  2,000 ┤                                                      ╭──╯╰──╮     │││
│  │  │  1,500 ┤                                                  ╭──╯       ╰──╮  │││
│  │  │  1,000 ┤                                              ╭──╯            ╰──╮│││
│  │  │    500 ┤                                          ╭──╯                   │││
│  │  │      0 ┴───────────────────────────────────────────────────────────┤       ││
│  │  │         Acme   XYZ    Beta   Delta   Epsilon  Zeta   Eta    Theta        ││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐│
│  │  🔔 Recent Activity                                                             ││
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐││
│  │  │  ● Acme Corp: Invoice_123 approved    2 hours ago                         │││
│  │  │  ● XYZ Ltd: Fuel_Card_Q4 processed   4 hours ago                         │││
│  │  │  ● Beta Inc: SECR Report generated   1 day ago                           │││
│  │  │  ● Delta Co: 5 documents uploaded   2 days ago                          │││
│  │  └─────────────────────────────────────────────────────────────────────────────┘││
│  └─────────────────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────────────────┘
8. Implementation Timeline
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  IMPLEMENTATION TIMELINE - VERSION 2                                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Phase 1: Database & Backend (Weeks 1-3)                                       │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  ● Create consultant_accounts table                                        ││ │
│  │  │  ● Create consultant_companies table                                       ││ │
│  │  │  ● Create consultant_team_members table                                   ││ │
│  │  │  ● Build company switching API                                             ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Phase 2: Consultant Portal (Weeks 4-6)                                        │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  ● Consultant dashboard                                                     ││ │
│  │  │  ● Client management interface                                               ││ │
│  │  │  ● Company switching UI                                                     ││ │
│  │  │  ● Team member management                                                   ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Phase 3: Cross-Company Reports (Weeks 7-9)                                    │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  ● Portfolio report generation                                             ││ │
│  │  │  ● Cross-company comparison charts                                         ││ │
│  │  │  ● Consolidated reporting                                                   ││ │
│  │  │  ● Export functionality                                                     ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  Phase 4: White-Label & Client Portals (Weeks 10-12)                           │ │
│  │  ┌─────────────────────────────────────────────────────────────────────────────┐│ │
│  │  │  ● Custom branding                                                          ││ │
│  │  │  ● Client access portals                                                    ││ │
│  │  │  ● Report sharing                                                           ││ │
│  │  │  ● Approval workflows                                                       ││ │
│  │  └─────────────────────────────────────────────────────────────────────────────┘│ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
9. Summary & Recommendations
text
┌─────────────────────────────────────────────────────────────────────────────────────┐
│  FINAL RECOMMENDATIONS                                                               │
├─────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  1. ✅ Build Version 1 NOW (Core Product)                                      │ │
│  │     ● Launch with single-company per account                                  │ │
│  │     ● Validate product-market fit                                              │ │
│  │     ● Get early customers                                                      │ │
│  │     ● Consultants can use (one account per client)                             │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  2. ✅ Plan Version 2 for Month 6-9                                            │ │
│  │     ● Based on real customer feedback                                           │ │
│  │     ● Consultants need multi-company                                            │ │
│  │     ● Build once, sell many                                                    │ │
│  │     ● Premium pricing tier                                                     │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────┐ │
│  │  3. ✅ Additional Revenue Streams                                               │ │
│  │     ● Consultant Monthly Fee (Premium)                                         │ │
│  │     ● Per-Client Fee (Setup)                                                    │ │
│  │     ● White-label Fee (Customization)                                          │ │
│  │     ● Cross-Company Reports (Premium feature)                                   │ │
│  └─────────────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────────────┘
