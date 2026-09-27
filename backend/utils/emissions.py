# backend/utils/emissions.py
"""
Emissions calculation utilities for CSV processing and canonical emission-factor
resolution (CT-SCHEMA-03 F-03/F-04 remediation).
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

# ==========================================
# ACTIVITY TYPE MAPPING
# ==========================================

ACTIVITY_TYPE_MAPPING = {
    # Fuel types
    'Diesel': 'Diesel (DERV)',
    'Petrol': 'Petrol (Unleaded)',
    'AdBlue': 'AdBlue',
    'LPG': 'LPG',
    'CNG': 'CNG',
    
    # Utility types
    'Electricity': 'UK Electricity Grid',
    'Natural Gas': 'Natural Gas',
    'Steam': 'Steam',
    'Chilled Water': 'Chilled Water',
    
    # Scope 3 types
    'Flight (Short Haul)': 'Flight (Short Haul)',
    'Flight (Long Haul)': 'Flight (Long Haul)',
    'Rail (National)': 'Rail (National)',
    'Hotel Stay': 'Hotel Stay',
    'Mixed Waste': 'Mixed Waste',
    'Recycled Waste': 'Recycled Waste',
    'Taxi': 'Taxi',
    'Bus': 'Bus',
    'Freight': 'Freight',
}

# ==========================================
# EMISSION FACTOR FUNCTIONS
# ==========================================

class FactorUnresolved(ValueError):
    """No governed emission factor could be resolved for the activity.

    CT-SCHEMA-03 F-03/F-04: an unresolved factor is a *controlled manual-review*
    state (AGENTS.md #15/#22), never a silent ``None`` provenance link.
    """


# Canonical provenance columns.  Verified against the CT-SCHEMA-02 canonical
# inventory: `emission_factors` retains the legacy column names
# (activity_type, co2e_multiplier, reporting_year) and adds the governed
# provenance columns (unit, scope, country, factor_source, factor_set).
CANONICAL_FACTOR_COLUMNS = (
    'id, activity_type, co2e_multiplier, reporting_year, unit, scope, '
    'country, factor_source, factor_set'
)

CUSTOMER_FACTOR_COLUMNS = (
    'id, activity_type, co2e_multiplier, reporting_year, unit, scope, '
    'country, factor_source, version, status'
)

#: Canonical eligibility for customer-factor precedence.  Mirrors
#: ``CustomerFactorsRepository.get_active_for_org`` (D-cf-5): only approved
#: (``status = 'active'``) customer factors outrank CarbonTally factors.
CUSTOMER_FACTOR_ACTIVE_STATUS = 'active'


def _resolve_activity_alias(supabase_client, activity_type, organization_id=None):
    """Resolve a governed activity alias (org-scoped first, then global).

    Mirrors ``FactorAliasesRepository.find_by_alias`` over the canonical
    ``factor_aliases`` table (AGENTS.md #22: alias matching is a governed stage).
    """
    try:
        result = supabase_client.from_('factor_aliases') \
            .select('alias_text, target_activity_type, organization_id') \
            .eq('alias_text', activity_type) \
            .execute()
    except Exception as alias_error:
        print(f"⚠️ Alias lookup failed for '{activity_type}': {alias_error}")
        return None

    rows = result.data or []
    org_scoped = [
        r for r in rows
        if organization_id and r.get('organization_id') == organization_id
    ]
    global_rows = [r for r in rows if not r.get('organization_id')]
    for row in (org_scoped or global_rows):
        target = row.get('target_activity_type')
        if target:
            return target
    return None


def _resolve_customer_factor(supabase_client, activity_type, reporting_year, organization_id):
    """Tier 1 — APPROVED CUSTOMER FACTOR (highest precedence, AGENTS.md #15)."""
    if not organization_id:
        return None
    query = supabase_client.from_('customer_factors') \
        .select(CUSTOMER_FACTOR_COLUMNS) \
        .eq('organization_id', organization_id) \
        .eq('status', CUSTOMER_FACTOR_ACTIVE_STATUS) \
        .eq('activity_type', activity_type)
    if reporting_year is not None:
        query = query.eq('reporting_year', reporting_year)
    result = query.order('version', desc=True).limit(1).execute()
    return result.data[0] if result.data else None


def _resolve_canonical_factor(supabase_client, activity_type, reporting_year):
    """Tier 2 — CarbonTally governed factor in the canonical `emission_factors`.

    Returns ``(row, is_fallback)``; ``(None, False)`` when nothing resolves.
    The retired legacy DEFRA conversion-factor table was renamed to
    ``emission_factors`` by the canonical chain and its recreation is
    structurally forbidden (CT-SCHEMA-03 F-01).
    """
    if reporting_year is None:
        year_result = supabase_client.from_('emission_factors') \
            .select('reporting_year') \
            .eq('activity_type', activity_type) \
            .order('reporting_year', desc=True) \
            .limit(1) \
            .execute()
        if not year_result.data:
            return None, False
        reporting_year = year_result.data[0]['reporting_year']

    exact = supabase_client.from_('emission_factors') \
        .select(CANONICAL_FACTOR_COLUMNS) \
        .eq('activity_type', activity_type) \
        .eq('reporting_year', reporting_year) \
        .limit(1) \
        .execute()
    if exact.data:
        return exact.data[0], False

    # Latest-year fallback — explicit and recorded in the returned provenance
    # (`is_fallback` / `resolution`), never applied silently (AGENTS.md #22).
    fallback = supabase_client.from_('emission_factors') \
        .select(CANONICAL_FACTOR_COLUMNS) \
        .eq('activity_type', activity_type) \
        .order('reporting_year', desc=True) \
        .limit(1) \
        .execute()
    if fallback.data:
        return fallback.data[0], True
    return None, False


def get_emission_factor(supabase_client, activity_type: str, reporting_year: int = None,
                        organization_id: Optional[str] = None) -> Dict:
    """Resolve an emission factor through the canonical governed chain.

    Precedence (AGENTS.md #15 — ratified policy, not a fallback chain):

        1. APPROVED CUSTOMER FACTOR    (`customer_factors`, org-scoped)
        2. CARBONTALLY FACTOR MATCHING (`emission_factors` via `factor_aliases`)
        3. UNRESOLVED → FactorUnresolved (controlled manual review)

    The returned mapping is a superset of the historical contract, so existing
    callers keep working while the factor decision becomes traceable:

        multiplier, reporting_year, factor_id, is_fallback     (historical)
        factor_kind, factor_source, factor_set, unit, scope, country,
        customer_factor_id, alias_used, resolution             (provenance)

    ``organization_id`` is optional for backward compatibility; when supplied,
    approved customer factors take precedence over CarbonTally factors.
    """
    db_activity_type = ACTIVITY_TYPE_MAPPING.get(activity_type, activity_type)
    alias_used = None

    # ---- Tier 1: approved customer factor (org-scoped) ---------------------
    if organization_id:
        customer_row = _resolve_customer_factor(
            supabase_client, db_activity_type, reporting_year, organization_id
        )
        if customer_row is None and db_activity_type != activity_type:
            customer_row = _resolve_customer_factor(
                supabase_client, activity_type, reporting_year, organization_id
            )
        if customer_row:
            print(f"✅ Customer factor (approved): {customer_row['co2e_multiplier']} "
                  f"for {db_activity_type} (org={organization_id})")
            return {
                'multiplier': float(customer_row['co2e_multiplier']),
                'reporting_year': customer_row.get('reporting_year'),
                'factor_id': customer_row['id'],
                'is_fallback': False,
                'factor_kind': 'customer_factor',
                'factor_source': customer_row.get('factor_source'),
                'factor_set': None,
                'unit': customer_row.get('unit'),
                'scope': customer_row.get('scope'),
                'country': customer_row.get('country'),
                'customer_factor_id': customer_row['id'],
                'alias_used': None,
                'resolution': 'customer_factor',
            }

    # ---- Governed alias resolution ----------------------------------------
    resolved_activity = _resolve_activity_alias(
        supabase_client, db_activity_type, organization_id
    )
    if resolved_activity and resolved_activity != db_activity_type:
        alias_used = resolved_activity
        db_activity_type = resolved_activity

    # ---- Tier 2: CarbonTally governed factor ------------------------------
    row, is_fallback = _resolve_canonical_factor(
        supabase_client, db_activity_type, reporting_year
    )
    if row:
        print(f"{'⚠️ Fallback' if is_fallback else '✅'} Factor: "
              f"{row['co2e_multiplier']} for {db_activity_type} "
              f"({row.get('reporting_year')})")
        return {
            'multiplier': float(row['co2e_multiplier']),
            'reporting_year': row.get('reporting_year'),
            'factor_id': row['id'],
            'is_fallback': is_fallback,
            'factor_kind': 'carbontally_factor',
            'factor_source': row.get('factor_source'),
            'factor_set': row.get('factor_set'),
            'unit': row.get('unit'),
            'scope': row.get('scope'),
            'country': row.get('country'),
            'customer_factor_id': None,
            'alias_used': alias_used,
            'resolution': 'latest_year_fallback' if is_fallback else 'exact_year',
        }

    # ---- Tier 3: unresolved → controlled manual review ---------------------
    raise FactorUnresolved(
        f"No governed emission factor resolved for '{activity_type}' "
        f"(activity_type='{db_activity_type}', reporting_year={reporting_year}); "
        "route to manual review — do not record a null factor reference."
    )


def get_activity_category(supabase_client, activity_type: str) -> Dict:
    """
    Get CSRD/ISSB category mapping for an activity.
    """
    try:
        db_activity_type = ACTIVITY_TYPE_MAPPING.get(activity_type, activity_type)
        
        result = supabase_client.from_('activity_categories') \
            .select('*') \
            .eq('activity_type', db_activity_type) \
            .execute()
        
        if result.data and len(result.data) > 0:
            return result.data[0]
        
        return {
            'activity_type': activity_type,
            'esrs_e1_category': 'Other',
            'issb_category': 'Other',
            'ghg_protocol_scope': 'Scope 3',
            'ghg_protocol_category': 'Other'
        }
    except Exception as e:
        print(f"⚠️ Error fetching category for {activity_type}: {e}")
        return {
            'activity_type': activity_type,
            'esrs_e1_category': 'Other',
            'issb_category': 'Other',
            'ghg_protocol_scope': 'Scope 3',
            'ghg_protocol_category': 'Other'
        }

def calculate_emissions_with_defra(supabase_client, activity_type: str, consumption: float, 
                                   start_date: str, override_year: int = None) -> Dict:
    """
    Auto-detects the reporting year from the start_date, 
    but allows an override. Fetches the exact DEFRA multiplier and calculates kgCO2e.
    """
    try:
        detected_year = int(str(start_date).split('-')[0])
    except (ValueError, IndexError):
        detected_year = 2025
        
    reporting_year = override_year if override_year else detected_year
    
    category_info = get_activity_category(supabase_client, activity_type)
    factor_data = get_emission_factor(supabase_client, activity_type, reporting_year)
    
    multiplier = factor_data['multiplier']
    calculated_kg_co2e = round(consumption * multiplier, 4)
    
    return {
        "reporting_year": factor_data['reporting_year'],
        "multiplier_used": multiplier,
        "calculated_kg_co2e": calculated_kg_co2e,
        "is_fallback": factor_data.get('is_fallback', False),
        "category_mapping": {
            "esrs_e1_category": category_info.get('esrs_e1_category'),
            "issb_category": category_info.get('issb_category'),
            "ghg_protocol_scope": category_info.get('ghg_protocol_scope'),
            "ghg_protocol_category": category_info.get('ghg_protocol_category')
        }
    }

# ==========================================
# CSV PROCESSING FUNCTIONS
# ==========================================

def process_fuel_data(df: pd.DataFrame, supabase_client) -> Tuple[List[Dict], int]:
    """Process fuel data using database-stored emission factors."""
    df = df.copy()
    date_col = next((c for c in df.columns if 'date' in c.lower()), 'Transaction Date')
    vol_col = next((c for c in df.columns if 'vol' in c.lower() or 'litre' in c.lower() or 'liter' in c.lower()), 'Volume (L)')
    reg_col = next((c for c in df.columns if 'reg' in c.lower() or 'vehicle' in c.lower() or 'plate' in c.lower()), 'Vehicle Registration')
    fuel_col = next((c for c in df.columns if 'fuel' in c.lower()), 'Fuel Type')
    
    df = df.rename(columns={date_col: 'Transaction Date', vol_col: 'Volume (L)', reg_col: 'Vehicle Registration', fuel_col: 'Fuel Type'})
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Volume (L)'] = pd.to_numeric(df['Volume (L)'], errors='coerce')
    df['Fuel Type'] = df['Fuel Type'].astype(str).replace('', 'Unknown Fuel').fillna('Unknown Fuel')
    
    def normalize_fuel(fuel):
        fuel_str = str(fuel).strip().lower()
        if 'diesel' in fuel_str: return 'Diesel'
        if 'petrol' in fuel_str or 'gasoline' in fuel_str: return 'Petrol'
        if 'adblue' in fuel_str or 'def' in fuel_str: return 'AdBlue'
        if 'lpg' in fuel_str: return 'LPG'
        if 'cng' in fuel_str: return 'CNG'
        return 'Unknown Fuel'

    df['Standardized Fuel'] = df['Fuel Type'].apply(normalize_fuel)
    
    factors = []
    for fuel in df['Standardized Fuel'].unique():
        if fuel == 'Unknown Fuel':
            factors.append({'fuel': fuel, 'factor': 0, 'year': None, 'factor_id': None})
        else:
            try:
                factor_data = get_emission_factor(supabase_client, fuel)
                factors.append({
                    'fuel': fuel, 
                    'factor': factor_data['multiplier'],
                    'year': factor_data['reporting_year'],
                    'factor_id': factor_data.get('factor_id')
                })
            except Exception as e:
                print(f"⚠️ Error getting factor for {fuel}: {e}")
                factors.append({'fuel': fuel, 'factor': 0, 'year': None, 'factor_id': None})
    
    factor_map = {f['fuel']: f['factor'] for f in factors}
    year_map = {f['fuel']: f['year'] for f in factors}
    factor_id_map = {f['fuel']: f['factor_id'] for f in factors}
    
    df['DEFRA Factor (kgCO2e/L)'] = df['Standardized Fuel'].map(factor_map).fillna(0)
    df['DEFRA Factor Year'] = df['Standardized Fuel'].map(year_map)
    df['DEFRA Factor ID'] = df['Standardized Fuel'].map(factor_id_map)
    df['Total kgCO2e'] = (df['Volume (L)'] * df['DEFRA Factor (kgCO2e/L)']).round(2).fillna(0)
    
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Volume (L)'].isna(), 'needs_review'] = True
    df.loc[df['Volume (L)'].isna(), 'review_reason'] = 'Missing Volume'
    df.loc[df['Standardized Fuel'] == 'Unknown Fuel', 'needs_review'] = True
    df.loc[df['Standardized Fuel'] == 'Unknown Fuel', 'review_reason'] = 'Unrecognized Fuel Type'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Transaction Date', 'Vehicle Registration', 'Standardized Fuel', 'Volume (L)', 
                  'DEFRA Factor (kgCO2e/L)', 'DEFRA Factor Year', 'DEFRA Factor ID', 
                  'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())

def process_utility_data(df: pd.DataFrame, supabase_client) -> Tuple[List[Dict], int]:
    """Process utility data using database-stored emission factors."""
    df = df.copy()
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'period' in c.lower()), 'Billing Period Start')
    site_col = next((c for c in df.columns if 'site' in c.lower() or 'facility' in c.lower() or 'location' in c.lower()), 'Site Name')
    vol_col = next((c for c in df.columns if 'consumption' in c.lower() or 'kwh' in c.lower() or 'usage' in c.lower()), 'Consumption (kWh)')
    type_col = next((c for c in df.columns if 'type' in c.lower() or 'utility' in c.lower() or 'meter' in c.lower()), 'Utility Type')
    
    df = df.rename(columns={date_col: 'Billing Period Start', site_col: 'Site Name', 
                           vol_col: 'Consumption (kWh)', type_col: 'Utility Type'})
    df['Billing Period Start'] = pd.to_datetime(df['Billing Period Start'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Consumption (kWh)'] = pd.to_numeric(df['Consumption (kWh)'], errors='coerce')
    
    if 'Cost (£)' in df.columns:
        df['Cost (£)'] = pd.to_numeric(df['Cost (£)'], errors='coerce').fillna(0)

    df['Utility Type'] = df['Utility Type'].astype(str).replace('', 'Unknown Utility').fillna('Unknown Utility')
    
    def normalize_utility_type(utype):
        if pd.isna(utype): return 'Unknown Utility'
        utype_str = str(utype).strip().lower()
        if 'electric' in utype_str: return 'Electricity'
        if 'gas' in utype_str or 'nat' in utype_str: return 'Natural Gas'
        if 'steam' in utype_str: return 'Steam'
        if 'chilled' in utype_str or 'cooling' in utype_str: return 'Chilled Water'
        return 'Unknown Utility'

    df['Standardized Utility'] = df['Utility Type'].apply(normalize_utility_type)
    
    factors = []
    for utility in df['Standardized Utility'].unique():
        if utility == 'Unknown Utility':
            factors.append({'utility': utility, 'factor': 0, 'year': None, 'factor_id': None})
        else:
            try:
                factor_data = get_emission_factor(supabase_client, utility)
                factors.append({
                    'utility': utility, 
                    'factor': factor_data['multiplier'],
                    'year': factor_data['reporting_year'],
                    'factor_id': factor_data.get('factor_id')
                })
            except Exception as e:
                print(f"⚠️ Error getting factor for {utility}: {e}")
                factors.append({'utility': utility, 'factor': 0, 'year': None, 'factor_id': None})
    
    factor_map = {f['utility']: f['factor'] for f in factors}
    year_map = {f['utility']: f['year'] for f in factors}
    factor_id_map = {f['utility']: f['factor_id'] for f in factors}
    
    df['DEFRA Factor (kgCO2e/kWh)'] = df['Standardized Utility'].map(factor_map).fillna(0)
    df['DEFRA Factor Year'] = df['Standardized Utility'].map(year_map)
    df['DEFRA Factor ID'] = df['Standardized Utility'].map(factor_id_map)
    df['Total kgCO2e'] = (df['Consumption (kWh)'] * df['DEFRA Factor (kgCO2e/kWh)']).round(2).fillna(0)
    
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Consumption (kWh)'].isna(), 'needs_review'] = True
    df.loc[df['Consumption (kWh)'].isna(), 'review_reason'] = 'Missing kWh Consumption'
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'needs_review'] = True
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'review_reason'] = 'Unrecognized Utility Type'
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'needs_review'] = True
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'review_reason'] = 'Missing Site/Facility Name'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_columns = ['Billing Period Start', 'Site Name', 'Standardized Utility', 
                     'Consumption (kWh)', 'DEFRA Factor (kgCO2e/kWh)', 'DEFRA Factor Year',
                     'DEFRA Factor ID', 'Total kgCO2e', 'needs_review', 'review_reason']
    if 'Cost (£)' in df.columns:
        clean_columns.insert(4, 'Cost (£)')
        
    return df[[c for c in clean_columns if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())

def process_scope3_data(df: pd.DataFrame, supabase_client) -> Tuple[List[Dict], int]:
    """Process Scope 3 data using database-stored emission factors."""
    df = df.copy()
    date_col = next((c for c in df.columns if 'date' in c.lower()), 'Date')
    desc_col = next((c for c in df.columns if 'desc' in c.lower() or 'detail' in c.lower() or 'purpose' in c.lower()), 'Description')
    vol_col = next((c for c in df.columns if 'qty' in c.lower() or 'quantity' in c.lower() or 'amount' in c.lower() or 'distance' in c.lower() or 'weight' in c.lower()), 'Quantity')
    cat_col = next((c for c in df.columns if 'cat' in c.lower() or 'type' in c.lower() or 'class' in c.lower()), 'Category')
    
    df = df.rename(columns={date_col: 'Date', desc_col: 'Description', vol_col: 'Quantity', cat_col: 'Category'})
    df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    
    if 'Cost (£)' in df.columns:
        df['Cost (£)'] = pd.to_numeric(df['Cost (£)'], errors='coerce').fillna(0)

    df['Category'] = df['Category'].astype(str).replace('', 'Unknown Scope 3').fillna('Unknown Scope 3')
    df['Description'] = df['Description'].astype(str).replace('', 'N/A').fillna('N/A')
    
    def normalize_scope3(cat):
        if pd.isna(cat): return 'Unknown Scope 3'
        cat_str = str(cat).strip().lower()
        if 'flight' in cat_str or 'air' in cat_str: 
            return 'Flight (Long Haul)' if 'long' in cat_str else 'Flight (Short Haul)'
        if 'rail' in cat_str or 'train' in cat_str: return 'Rail (National)'
        if 'hotel' in cat_str or 'stay' in cat_str: return 'Hotel Stay'
        if 'waste' in cat_str or 'rubbish' in cat_str: 
            return 'Recycled Waste' if 'recycle' in cat_str else 'Mixed Waste'
        if 'car' in cat_str or 'taxi' in cat_str: return 'Taxi'
        if 'bus' in cat_str: return 'Bus'
        if 'freight' in cat_str or 'cargo' in cat_str: return 'Freight'
        return 'Unknown Scope 3'

    df['Standardized Scope3'] = df['Category'].apply(normalize_scope3)
    
    factors = []
    for scope in df['Standardized Scope3'].unique():
        if scope == 'Unknown Scope 3':
            factors.append({'scope': scope, 'factor': 0, 'year': None, 'factor_id': None})
        else:
            try:
                factor_data = get_emission_factor(supabase_client, scope)
                factors.append({
                    'scope': scope, 
                    'factor': factor_data['multiplier'],
                    'year': factor_data['reporting_year'],
                    'factor_id': factor_data.get('factor_id')
                })
            except Exception as e:
                print(f"⚠️ Error getting factor for {scope}: {e}")
                factors.append({'scope': scope, 'factor': 0, 'year': None, 'factor_id': None})
    
    factor_map = {f['scope']: f['factor'] for f in factors}
    year_map = {f['scope']: f['year'] for f in factors}
    factor_id_map = {f['scope']: f['factor_id'] for f in factors}
    
    df['DEFRA Factor'] = df['Standardized Scope3'].map(factor_map).fillna(0)
    df['DEFRA Factor Year'] = df['Standardized Scope3'].map(year_map)
    df['DEFRA Factor ID'] = df['Standardized Scope3'].map(factor_id_map)
    df['Total kgCO2e'] = (df['Quantity'] * df['DEFRA Factor']).round(2).fillna(0)
    
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Quantity'].isna(), 'needs_review'] = True
    df.loc[df['Quantity'].isna(), 'review_reason'] = 'Missing Quantity'
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'needs_review'] = True
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'review_reason'] = 'Unrecognized Category'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_columns = ['Date', 'Description', 'Standardized Scope3', 'Quantity', 
                     'DEFRA Factor', 'DEFRA Factor Year', 'DEFRA Factor ID',
                     'Total kgCO2e', 'needs_review', 'review_reason']
    if 'Cost (£)' in df.columns:
        clean_columns.insert(3, 'Cost (£)')
        
    return df[[c for c in clean_columns if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())

# ==========================================
# EXTRACTION HELPERS
# ==========================================

def extract_issues_from_result(extraction_result: dict, data_type: str) -> Tuple[List[Dict], Dict]:
    """Extract real issues from the extraction result."""
    issues = []
    summary = {
        "total_fields": 0,
        "extracted_successfully": 0,
        "needs_manual_review": 0,
        "failed": 0,
        "confidence_score": 0.0
    }
    
    if extraction_result.get("status") == "error":
        issues.append({
            "severity": "critical",
            "type": "extraction_failure",
            "field": "document",
            "message": "Failed to extract any data from the document",
            "technical_details": extraction_result.get("error", "Unknown extraction error")
        })
        summary["failed"] = 1
        summary["confidence_score"] = 0.0
        return issues, summary
    
    data_streams = extraction_result.get("data_streams", [])
    total_fields = 0
    extracted_count = 0
    review_count = 0
    failed_count = 0
    confidence_scores = []
    
    for stream in data_streams:
        stream_errors = stream.get("errors", [])
        if stream_errors:
            for error in stream_errors:
                issue = {
                    "severity": "critical" if error.get("error_type") == "low_confidence" else "warning",
                    "type": error.get("error_type", "unknown_error"),
                    "field": error.get("field", stream.get("stream_name", "unknown")),
                    "message": error.get("message", "Data extraction issue"),
                    "technical_details": f"Stream: {stream.get('stream_name')} - {error.get('message', '')}"
                }
                if error.get("value"):
                    issue["value"] = error.get("value")
                issues.append(issue)
                failed_count += 1
        
        extracted_fields = stream.get("extracted_fields", {})
        for field_name, field_data in extracted_fields.items():
            total_fields += 1
            confidence = field_data.get("confidence", 1.0)
            confidence_scores.append(confidence)
            
            if confidence < 0.60:
                issues.append({
                    "severity": "warning",
                    "type": "low_confidence",
                    "field": field_name,
                    "message": f"Low confidence extraction for {field_name.replace('_', ' ')}",
                    "technical_details": f"Confidence score: {confidence:.2f} (threshold: 0.60)",
                    "value": field_data.get("value", "")
                })
                review_count += 1
            elif field_data.get("status") == "failed" or field_data.get("value") is None or field_data.get("value") == "":
                issues.append({
                    "severity": "critical",
                    "type": "missing_data",
                    "field": field_name,
                    "message": f"Could not extract {field_name.replace('_', ' ')}",
                    "technical_details": f"Field extraction failed - no value found"
                })
                failed_count += 1
            else:
                extracted_count += 1
    
    # Asset mapping issues
    for stream in data_streams:
        asset_mapping = stream.get("asset_mapping", {})
        if asset_mapping.get("matched_asset_id") is None:
            suggested = asset_mapping.get("suggested_assets", [])
            issues.append({
                "severity": "warning",
                "type": "unmapped_asset",
                "field": "asset_mapping",
                "message": "Could not automatically map to an asset",
                "technical_details": f"No matching asset found. Suggested: {', '.join(suggested) if suggested else 'None'}",
                "value": stream.get("stream_name", "Unknown")
            })
            review_count += 1
    
    summary["total_fields"] = total_fields
    summary["extracted_successfully"] = extracted_count
    summary["needs_manual_review"] = review_count
    summary["failed"] = failed_count
    summary["confidence_score"] = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
    
    return issues, summary

def has_low_confidence(extraction_result: dict) -> bool:
    """Check if any data stream has confidence < 60%"""
    for stream in extraction_result.get("data_streams", []):
        for field in stream.get("extracted_fields", {}).values():
            if field.get("confidence", 1.0) < 0.60:
                return True
    return False