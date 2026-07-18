from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
import io
from pydantic import BaseModel

app = FastAPI(title="CarbonTally API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://carbontally.co.uk"], # Add your future Vercel URL here
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OFFICIAL UK DEFRA 2024 CONVERSION FACTORS
DEFRA_FACTORS = {
    # Scope 1: Transport Fuel (kgCO2e per Litre)
    'Diesel': 2.54,
    'Petrol': 2.16,
    'AdBlue': 0.0,
    'Unknown Fuel': 0.0,
    
    # Scope 2: Utilities (kgCO2e per kWh) - Location Based
    'Electricity': 0.20712, 
    'Natural Gas': 0.18316,
    'Unknown Utility': 0.0
}
def process_fuel_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    
    # 1. Smart Column Mapping
    date_col = next((c for c in df.columns if 'date' in c.lower()), 'Transaction Date')
    vol_col = next((c for c in df.columns if 'vol' in c.lower() or 'litre' in c.lower() or 'liter' in c.lower()), 'Volume (L)')
    reg_col = next((c for c in df.columns if 'reg' in c.lower() or 'vehicle' in c.lower() or 'plate' in c.lower()), 'Vehicle Registration')
    fuel_col = next((c for c in df.columns if 'fuel' in c.lower()), 'Fuel Type')
    
    df = df.rename(columns={date_col: 'Transaction Date', vol_col: 'Volume (L)', reg_col: 'Vehicle Registration', fuel_col: 'Fuel Type'})
    
    # 2. Clean Data
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Volume (L)'] = pd.to_numeric(df['Volume (L)'], errors='coerce')
    df['Fuel Type'] = df['Fuel Type'].astype(str).replace('', 'Unknown Fuel').fillna('Unknown Fuel')
    
    # 3. Normalize Fuel Types
    def normalize_fuel(fuel):
        fuel_str = str(fuel).strip().lower()
        if 'diesel' in fuel_str: return 'Diesel'
        if 'petrol' in fuel_str or 'gas' in fuel_str: return 'Petrol'
        if 'adblue' in fuel_str or 'def' in fuel_str: return 'AdBlue'
        return 'Unknown Fuel'

    df['Standardized Fuel'] = df['Fuel Type'].apply(normalize_fuel)
    df['DEFRA Factor (kgCO2e/L)'] = df['Standardized Fuel'].map(DEFRA_FACTORS)
    df['Total kgCO2e'] = (df['Volume (L)'] * df['DEFRA Factor (kgCO2e/L)']).round(2).fillna(0)
    
    # 4. Flag for Review
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Volume (L)'].isna(), 'needs_review'] = True
    df.loc[df['Volume (L)'].isna(), 'review_reason'] = 'Missing Volume'
    df.loc[df['Standardized Fuel'] == 'Unknown Fuel', 'needs_review'] = True
    df.loc[df['Standardized Fuel'] == 'Unknown Fuel', 'review_reason'] = 'Unrecognized Fuel Type'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Transaction Date', 'Vehicle Registration', 'Standardized Fuel', 'Volume (L)', 'DEFRA Factor (kgCO2e/L)', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())


def process_utility_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    
    # 1. Smart Column Mapping
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'period' in c.lower()), 'Billing Period Start')
    site_col = next((c for c in df.columns if 'site' in c.lower() or 'facility' in c.lower() or 'location' in c.lower()), 'Site Name')
    vol_col = next((c for c in df.columns if 'consumption' in c.lower() or 'kwh' in c.lower() or 'usage' in c.lower()), 'Consumption (kWh)')
    type_col = next((c for c in df.columns if 'type' in c.lower() or 'utility' in c.lower() or 'meter' in c.lower()), 'Utility Type')
    
    df = df.rename(columns={date_col: 'Billing Period Start', site_col: 'Site Name', vol_col: 'Consumption (kWh)', type_col: 'Utility Type'})
    
    # 2. Clean Data
    df['Billing Period Start'] = pd.to_datetime(df['Billing Period Start'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Consumption (kWh)'] = pd.to_numeric(df['Consumption (kWh)'], errors='coerce')
    df['Utility Type'] = df['Utility Type'].astype(str).replace('', 'Unknown Utility').fillna('Unknown Utility')
    
    # 3. Normalize Utility Types
    def normalize_utility(utype):
        utype_str = str(utype).strip().lower()
        if 'electric' in utype_str: return 'Electricity'
        if 'gas' in utype_str: return 'Natural Gas'
        return 'Unknown Utility'

    df['Standardized Utility'] = df['Utility Type'].apply(normalize_utility)
    df['DEFRA Factor (kgCO2e/kWh)'] = df['Standardized Utility'].map(DEFRA_FACTORS)
    df['Total kgCO2e'] = (df['Consumption (kWh)'] * df['DEFRA Factor (kgCO2e/kWh)']).round(2).fillna(0)
    
    # 4. Flag for Review
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Consumption (kWh)'].isna(), 'needs_review'] = True
    df.loc[df['Consumption (kWh)'].isna(), 'review_reason'] = 'Missing kWh Consumption'
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'needs_review'] = True
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'review_reason'] = 'Unrecognized Utility Type'
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'needs_review'] = True
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'review_reason'] = 'Missing Site/Facility Name'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Billing Period Start', 'Site Name', 'Standardized Utility', 'Consumption (kWh)', 'DEFRA Factor (kgCO2e/kWh)', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())


def process_scope3_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    
    # 1. Smart Column Mapping
    date_col = next((c for c in df.columns if 'date' in c.lower()), 'Date')
    desc_col = next((c for c in df.columns if 'desc' in c.lower() or 'detail' in c.lower() or 'purpose' in c.lower()), 'Description')
    vol_col = next((c for c in df.columns if 'qty' in c.lower() or 'quantity' in c.lower() or 'amount' in c.lower() or 'distance' in c.lower() or 'weight' in c.lower()), 'Quantity')
    cat_col = next((c for c in df.columns if 'cat' in c.lower() or 'type' in c.lower() or 'class' in c.lower()), 'Category')
    
    df = df.rename(columns={date_col: 'Date', desc_col: 'Description', vol_col: 'Quantity', cat_col: 'Category'})
    
    # 2. Clean Data
    df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df['Category'] = df['Category'].astype(str).replace('', 'Unknown Scope 3').fillna('Unknown Scope 3')
    df['Description'] = df['Description'].astype(str).replace('', 'N/A').fillna('N/A')
    
    # 3. Normalize Scope 3 Types
    def normalize_scope3(cat):
        cat_str = str(cat).strip().lower()
        if 'flight' in cat_str or 'air' in cat_str: return 'Flight (Long Haul)' if 'long' in cat_str else 'Flight (Short Haul)'
        if 'rail' in cat_str or 'train' in cat_str: return 'Rail (National)'
        if 'hotel' in cat_str or 'stay' in cat_str: return 'Hotel Stay'
        if 'waste' in cat_str or 'rubbish' in cat_str: return 'Recycled Waste' if 'recycle' in cat_str else 'Mixed Waste'
        return 'Unknown Scope 3'

    df['Standardized Scope3'] = df['Category'].apply(normalize_scope3)
    df['DEFRA Factor'] = df['Standardized Scope3'].map(DEFRA_FACTORS)
    df['Total kgCO2e'] = (df['Quantity'] * df['DEFRA Factor']).round(2).fillna(0)
    
    # 4. Flag for Review
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Quantity'].isna(), 'needs_review'] = True
    df.loc[df['Quantity'].isna(), 'review_reason'] = 'Missing Quantity'
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'needs_review'] = True
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'review_reason'] = 'Unrecognized Category'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Date', 'Description', 'Standardized Scope3', 'Quantity', 'DEFRA Factor', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())


def process_utility_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    
    # 1. Smart Column Mapping
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'period' in c.lower()), 'Billing Period Start')
    site_col = next((c for c in df.columns if 'site' in c.lower() or 'facility' in c.lower() or 'location' in c.lower()), 'Site Name')
    vol_col = next((c for c in df.columns if 'consumption' in c.lower() or 'kwh' in c.lower() or 'usage' in c.lower()), 'Consumption (kWh)')
    type_col = next((c for c in df.columns if 'type' in c.lower() or 'utility' in c.lower() or 'meter' in c.lower()), 'Utility Type')
    
    df = df.rename(columns={date_col: 'Billing Period Start', site_col: 'Site Name', vol_col: 'Consumption (kWh)', type_col: 'Utility Type'})
    
    # 2. Clean Data
    df['Billing Period Start'] = pd.to_datetime(df['Billing Period Start'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Consumption (kWh)'] = pd.to_numeric(df['Consumption (kWh)'], errors='coerce')
    df['Utility Type'] = df['Utility Type'].astype(str).replace('', 'Unknown Utility').fillna('Unknown Utility')
    
    # 3. Normalize Utility Types
    def normalize_utility(utype):
        utype_str = str(utype).strip().lower()
        if 'electric' in utype_str: return 'Electricity'
        if 'gas' in utype_str: return 'Natural Gas'
        return 'Unknown Utility'

    df['Standardized Utility'] = df['Utility Type'].apply(normalize_utility)
    df['DEFRA Factor (kgCO2e/kWh)'] = df['Standardized Utility'].map(DEFRA_FACTORS)
    df['Total kgCO2e'] = (df['Consumption (kWh)'] * df['DEFRA Factor (kgCO2e/kWh)']).round(2).fillna(0)
    
    # 4. Flag for Review
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Consumption (kWh)'].isna(), 'needs_review'] = True
    df.loc[df['Consumption (kWh)'].isna(), 'review_reason'] = 'Missing kWh Consumption'
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'needs_review'] = True
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'review_reason'] = 'Unrecognized Utility Type'
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'needs_review'] = True
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'review_reason'] = 'Missing Site/Facility Name'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Billing Period Start', 'Site Name', 'Standardized Utility', 'Consumption (kWh)', 'DEFRA Factor (kgCO2e/kWh)', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())


def process_scope3_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    
    # 1. Smart Column Mapping
    date_col = next((c for c in df.columns if 'date' in c.lower()), 'Date')
    desc_col = next((c for c in df.columns if 'desc' in c.lower() or 'detail' in c.lower() or 'purpose' in c.lower()), 'Description')
    vol_col = next((c for c in df.columns if 'qty' in c.lower() or 'quantity' in c.lower() or 'amount' in c.lower() or 'distance' in c.lower() or 'weight' in c.lower()), 'Quantity')
    cat_col = next((c for c in df.columns if 'cat' in c.lower() or 'type' in c.lower() or 'class' in c.lower()), 'Category')
    
    df = df.rename(columns={date_col: 'Date', desc_col: 'Description', vol_col: 'Quantity', cat_col: 'Category'})
    
    # 2. Clean Data
    df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df['Category'] = df['Category'].astype(str).replace('', 'Unknown Scope 3').fillna('Unknown Scope 3')
    df['Description'] = df['Description'].astype(str).replace('', 'N/A').fillna('N/A')
    
    # 3. Normalize Scope 3 Types
    def normalize_scope3(cat):
        cat_str = str(cat).strip().lower()
        if 'flight' in cat_str or 'air' in cat_str: return 'Flight (Long Haul)' if 'long' in cat_str else 'Flight (Short Haul)'
        if 'rail' in cat_str or 'train' in cat_str: return 'Rail (National)'
        if 'hotel' in cat_str or 'stay' in cat_str: return 'Hotel Stay'
        if 'waste' in cat_str or 'rubbish' in cat_str: return 'Recycled Waste' if 'recycle' in cat_str else 'Mixed Waste'
        return 'Unknown Scope 3'

    df['Standardized Scope3'] = df['Category'].apply(normalize_scope3)
    df['DEFRA Factor'] = df['Standardized Scope3'].map(DEFRA_FACTORS)
    df['Total kgCO2e'] = (df['Quantity'] * df['DEFRA Factor']).round(2).fillna(0)
    
    # 4. Flag for Review
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Quantity'].isna(), 'needs_review'] = True
    df.loc[df['Quantity'].isna(), 'review_reason'] = 'Missing Quantity'
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'needs_review'] = True
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'review_reason'] = 'Unrecognized Category'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Date', 'Description', 'Standardized Scope3', 'Quantity', 'DEFRA Factor', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())

def process_utility_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    
    # 1. Smart Column Mapping
    date_col = next((c for c in df.columns if 'date' in c.lower() or 'period' in c.lower()), 'Billing Period Start')
    site_col = next((c for c in df.columns if 'site' in c.lower() or 'facility' in c.lower() or 'location' in c.lower()), 'Site Name')
    vol_col = next((c for c in df.columns if 'consumption' in c.lower() or 'kwh' in c.lower() or 'usage' in c.lower()), 'Consumption (kWh)')
    type_col = next((c for c in df.columns if 'type' in c.lower() or 'utility' in c.lower() or 'meter' in c.lower()), 'Utility Type')
    
    df = df.rename(columns={date_col: 'Billing Period Start', site_col: 'Site Name', vol_col: 'Consumption (kWh)', type_col: 'Utility Type'})
    
    # 2. Clean Data
    df['Billing Period Start'] = pd.to_datetime(df['Billing Period Start'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Consumption (kWh)'] = pd.to_numeric(df['Consumption (kWh)'], errors='coerce')
    df['Utility Type'] = df['Utility Type'].astype(str).replace('', 'Unknown Utility').fillna('Unknown Utility')
    
    # 3. Normalize Utility Types
    def normalize_utility(utype):
        utype_str = str(utype).strip().lower()
        if 'electric' in utype_str: return 'Electricity'
        if 'gas' in utype_str: return 'Natural Gas'
        return 'Unknown Utility'

    df['Standardized Utility'] = df['Utility Type'].apply(normalize_utility)
    df['DEFRA Factor (kgCO2e/kWh)'] = df['Standardized Utility'].map(DEFRA_FACTORS)
    df['Total kgCO2e'] = (df['Consumption (kWh)'] * df['DEFRA Factor (kgCO2e/kWh)']).round(2).fillna(0)
    
    # 4. Flag for Review
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Consumption (kWh)'].isna(), 'needs_review'] = True
    df.loc[df['Consumption (kWh)'].isna(), 'review_reason'] = 'Missing kWh Consumption'
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'needs_review'] = True
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'review_reason'] = 'Unrecognized Utility Type'
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'needs_review'] = True
    df.loc[df['Site Name'].isna() | (df['Site Name'] == ''), 'review_reason'] = 'Missing Site/Facility Name'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Billing Period Start', 'Site Name', 'Standardized Utility', 'Consumption (kWh)', 'DEFRA Factor (kgCO2e/kWh)', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())


def process_scope3_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    
    # 1. Smart Column Mapping
    date_col = next((c for c in df.columns if 'date' in c.lower()), 'Date')
    desc_col = next((c for c in df.columns if 'desc' in c.lower() or 'detail' in c.lower() or 'purpose' in c.lower()), 'Description')
    vol_col = next((c for c in df.columns if 'qty' in c.lower() or 'quantity' in c.lower() or 'amount' in c.lower() or 'distance' in c.lower() or 'weight' in c.lower()), 'Quantity')
    cat_col = next((c for c in df.columns if 'cat' in c.lower() or 'type' in c.lower() or 'class' in c.lower()), 'Category')
    
    df = df.rename(columns={date_col: 'Date', desc_col: 'Description', vol_col: 'Quantity', cat_col: 'Category'})
    
    # 2. Clean Data
    df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df['Category'] = df['Category'].astype(str).replace('', 'Unknown Scope 3').fillna('Unknown Scope 3')
    df['Description'] = df['Description'].astype(str).replace('', 'N/A').fillna('N/A')
    
    # 3. Normalize Scope 3 Types
    def normalize_scope3(cat):
        cat_str = str(cat).strip().lower()
        if 'flight' in cat_str or 'air' in cat_str: return 'Flight (Long Haul)' if 'long' in cat_str else 'Flight (Short Haul)'
        if 'rail' in cat_str or 'train' in cat_str: return 'Rail (National)'
        if 'hotel' in cat_str or 'stay' in cat_str: return 'Hotel Stay'
        if 'waste' in cat_str or 'rubbish' in cat_str: return 'Recycled Waste' if 'recycle' in cat_str else 'Mixed Waste'
        return 'Unknown Scope 3'

    df['Standardized Scope3'] = df['Category'].apply(normalize_scope3)
    df['DEFRA Factor'] = df['Standardized Scope3'].map(DEFRA_FACTORS)
    df['Total kgCO2e'] = (df['Quantity'] * df['DEFRA Factor']).round(2).fillna(0)
    
    # 4. Flag for Review
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Quantity'].isna(), 'needs_review'] = True
    df.loc[df['Quantity'].isna(), 'review_reason'] = 'Missing Quantity'
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'needs_review'] = True
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'review_reason'] = 'Unrecognized Category'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    clean_cols = ['Date', 'Description', 'Standardized Scope3', 'Quantity', 'DEFRA Factor', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[[c for c in clean_cols if c in df.columns]].to_dict(orient='records'), int(df['needs_review'].sum())

def process_utility_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    
    # 1. Clean Dates
    df['Billing Period Start'] = pd.to_datetime(df['Billing Period Start'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    
    # 2. Clean Numerics (kWh)
    df['Consumption (kWh)'] = pd.to_numeric(df['Consumption (kWh)'], errors='coerce')
    df['Cost (£)'] = pd.to_numeric(df['Cost (£)'], errors='coerce').fillna(0)
    
    # 3. Clean Site Names
    df['Site Name'] = df['Site Name'].replace('', 'UNKNOWN_SITE').fillna('UNKNOWN_SITE')
    df['Meter ID (MPAN/MPRN)'] = df['Meter ID (MPAN/MPRN)'].replace('', 'UNKNOWN_METER').fillna('UNKNOWN_METER')
    
    # 4. Normalize Utility Types
    def normalize_utility_type(utype):
        if pd.isna(utype): return 'Unknown Utility'
        utype_str = str(utype).strip().lower()
        if 'electric' in utype_str: return 'Electricity'
        if 'gas' in utype_str or 'nat' in utype_str: return 'Natural Gas'
        return 'Unknown Utility' # Catches "Standing Charge", etc.

    df['Standardized Utility'] = df['Meter Type'].apply(normalize_utility_type)
    
    # 5. Apply DEFRA Factors (kWh based)
    df['DEFRA Factor (kgCO2e/kWh)'] = df['Standardized Utility'].map(DEFRA_FACTORS)
    
    # 6. Calculate Emissions
    df['Total kgCO2e'] = (df['Consumption (kWh)'] * df['DEFRA Factor (kgCO2e/kWh)']).round(2).fillna(0)
    
    # 7. Flag for Review
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Consumption (kWh)'].isna(), 'needs_review'] = True
    df.loc[df['Consumption (kWh)'].isna(), 'review_reason'] = 'Missing kWh Consumption'
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'needs_review'] = True
    df.loc[df['Standardized Utility'] == 'Unknown Utility', 'review_reason'] = 'Unrecognized Utility Type (e.g. Standing Charge)'
    df.loc[df['Site Name'] == 'UNKNOWN_SITE', 'needs_review'] = True
    df.loc[df['Site Name'] == 'UNKNOWN_SITE', 'review_reason'] = 'Missing Site/Facility Name'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    
    clean_columns = ['Billing Period Start', 'Site Name', 'Meter ID (MPAN/MPRN)', 'Standardized Utility', 'Consumption (kWh)', 'Cost (£)', 'DEFRA Factor (kgCO2e/kWh)', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[clean_columns].to_dict(orient='records'), int(df['needs_review'].sum())
def process_scope3_data(df: pd.DataFrame) -> tuple:
    df = df.copy()
    
    # 1. Clean Dates
    df['Date'] = pd.to_datetime(df['Date'], format='mixed', dayfirst=True, errors='coerce').dt.strftime('%Y-%m-%d')
    
    # 2. Clean Numerics (Quantity)
    df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
    df['Cost (£)'] = pd.to_numeric(df['Cost (£)'], errors='coerce').fillna(0)
    
    # 3. Clean Categories
    df['Category'] = df['Category'].replace('', 'Unknown Scope 3').fillna('Unknown Scope 3')
    df['Description'] = df['Description'].replace('', 'N/A').fillna('N/A')
    
    # 4. Normalize Scope 3 Types
    def normalize_scope3(cat):
        if pd.isna(cat): return 'Unknown Scope 3'
        cat_str = str(cat).strip().lower()
        if 'flight' in cat_str or 'air' in cat_str: 
            return 'Flight (Long Haul)' if 'long' in cat_str else 'Flight (Short Haul)'
        if 'rail' in cat_str or 'train' in cat_str: return 'Rail (National)'
        if 'hotel' in cat_str: return 'Hotel Stay'
        if 'waste' in cat_str or 'rubbish' in cat_str: 
            return 'Recycled Waste' if 'recycle' in cat_str else 'Mixed Waste'
        return 'Unknown Scope 3'

    df['Standardized Scope3'] = df['Category'].apply(normalize_scope3)
    
    # 5. Apply DEFRA Factors
    df['DEFRA Factor'] = df['Standardized Scope3'].map(DEFRA_FACTORS)
    
    # 6. Calculate Emissions
    df['Total kgCO2e'] = (df['Quantity'] * df['DEFRA Factor']).round(2).fillna(0)
    
    # 7. Flag for Review
    df['needs_review'] = False
    df['review_reason'] = ''
    df.loc[df['Quantity'].isna(), 'needs_review'] = True
    df.loc[df['Quantity'].isna(), 'review_reason'] = 'Missing Quantity'
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'needs_review'] = True
    df.loc[df['Standardized Scope3'] == 'Unknown Scope 3', 'review_reason'] = 'Unrecognized Category'
    
    df = df.replace({np.nan: None, pd.NaT: None})
    
    clean_columns = ['Date', 'Description', 'Standardized Scope3', 'Quantity', 'Cost (£)', 'DEFRA Factor', 'Total kgCO2e', 'needs_review', 'review_reason']
    return df[clean_columns].to_dict(orient='records'), int(df['needs_review'].sum())

@app.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    data_type: str = Form('fuel')
):
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(status_code=400, detail="Only CSV or Excel files are allowed.")
    
    try:
        contents = await file.read()
        df = pd.read_csv(io.BytesIO(contents))
        
        # CRITICAL: Strip invisible spaces from CSV headers
        df.columns = df.columns.str.strip()
        
        if data_type == 'utility':
            clean_data, flagged_rows = process_utility_data(df)
            scope = "Scope 2"
        elif data_type == 'scope3':
            clean_data, flagged_rows = process_scope3_data(df)
            scope = "Scope 3"
        else:
            clean_data, flagged_rows = process_fuel_data(df)
            scope = "Scope 1"
            
        total_emissions = sum(row.get('Total kgCO2e', 0) or 0 for row in clean_data)
        
        return {
            "status": "success",
            "filename": file.filename,
            "data_type": data_type,
            "scope": scope,
            "rows_processed": len(clean_data),
            "rows_flagged_for_review": flagged_rows,
            "total_kgCO2e": round(total_emissions, 2),
            "data": clean_data
        }
    except Exception as e:
        import traceback
        # Print to Render's basic console so we have a backup
        print(f"--- BACKEND CRASH ---\n{traceback.format_exc()}\n-------------------")
        # Send the exact error back to the browser!
        raise HTTPException(status_code=500, detail=f"Backend Error: {str(e)}")

@app.get("/")
def read_root():
    return {"message": "CarbonTally API v2.0 is running."}
