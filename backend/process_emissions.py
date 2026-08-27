#backennd\process_emissions.py
import pandas as pd
import json
import numpy as np

def process_fuel_card_data(input_csv, output_json):
    print(f"🔄 Reading data from {input_csv}...")
    df = pd.read_csv(input_csv)
    initial_row_count = len(df)

    # ==========================================
    # STEP 1: CLEAN THE MESSY DATA
    # ==========================================
    
    # 1A. Fix Mixed Date Formats (DD/MM/YYYY vs YYYY-MM-DD)
    # 'mixed' allows pandas to figure out the format, dayfirst=True prioritizes UK format
    df['Transaction Date'] = pd.to_datetime(df['Transaction Date'], format='mixed', dayfirst=True, errors='coerce')
    # Convert to standard ISO 8601 string format for JSON
    df['Transaction Date'] = df['Transaction Date'].dt.strftime('%Y-%m-%d')
    
    # 1B. Clean Numeric Columns (Handle 'N/A', blanks, etc.)
    # 'coerce' turns invalid parsing (like 'N/A') into NaN (Not a Number)
    df['Volume (L)'] = pd.to_numeric(df['Volume (L)'], errors='coerce')
    df['Total Cost (£)'] = pd.to_numeric(df['Total Cost (£)'], errors='coerce')
    
    # Drop rows where critical volume data is missing
    df = df.dropna(subset=['Volume (L)'])
    
    # 1C. Clean Categorical Columns (Fill blank vehicle regs)
    df['Vehicle Registration'] = df['Vehicle Registration'].replace('', 'UNKNOWN').fillna('UNKNOWN')

    # ==========================================
    # STEP 2: STANDARDIZE FUEL TYPES & MAP DEFRA
    # ==========================================
    
    # Map messy real-world fuel names to a clean, standard category
    def normalize_fuel_type(fuel):
        if pd.isna(fuel): return 'Unknown'
        fuel_str = str(fuel).strip().lower()
        
        # Map variations of Diesel
        if fuel_str in ['derv', 'diesel', 'diesel (premium)', 'derw']:
            return 'Diesel'
        # Map variations of Petrol
        if fuel_str in ['petrol', 'unleaded', 'super unleaded']:
            return 'Petrol'
        # AdBlue is an exhaust fluid, NOT a fuel. It generates 0 Scope 1 emissions.
        if fuel_str == 'adblue':
            return 'AdBlue' 
            
        return 'Unknown'

    df['Standardized Fuel'] = df['Fuel Type'].apply(normalize_fuel_type)

    # Official UK DEFRA 2023/2024 Conversion Factors (kgCO2e per Litre)
    # Source: UK Gov GHG Conversion Factors for Company Reporting
    defra_factors = {
        'Diesel': 2.54,    # Scope 1 direct emissions for DERV/Diesel
        'Petrol': 2.16,    # Scope 1 direct emissions for Petrol
        'AdBlue': 0.0,     # Not a fuel, no direct combustion emissions
        'Unknown': 0.0     # Fallback (in production, this would trigger a manual review flag)
    }

    # Map the factors to the dataframe
    df['DEFRA Factor (kgCO2e/L)'] = df['Standardized Fuel'].map(defra_factors)

    # ==========================================
    # STEP 3: CALCULATE EMISSIONS
    # ==========================================
    
    # The core math: Volume * DEFRA Factor = Total Carbon Emissions
    df['Total kgCO2e'] = df['Volume (L)'] * df['DEFRA Factor (kgCO2e/L)']
    
    # Round to 2 decimal places for clean reporting
    df['Total kgCO2e'] = df['Total kgCO2e'].round(2)
    df['Total Cost (£)'] = df['Total Cost (£)'].round(2)

    # ==========================================
    # STEP 4: EXPORT TO CLEAN JSON
    # ==========================================
    
    # Select only the clean, relevant columns for the final output
    clean_columns = [
        'Transaction Date', 
        'Vehicle Registration', 
        'Standardized Fuel', 
        'Volume (L)', 
        'Total Cost (£)', 
        'DEFRA Factor (kgCO2e/L)', 
        'Total kgCO2e'
    ]
    
    final_df = df[clean_columns]
    
    # Convert to JSON
    json_data = final_df.to_dict(orient='records')
    
    with open(output_json, 'w') as f:
        json.dump(json_data, f, indent=4)
        
    print(f"✅ Success! Cleaned {len(final_df)} rows (dropped {initial_row_count - len(final_df)} invalid rows).")
    print(f"📁 Output saved to {output_json}")

# Run the function
if __name__ == "__main__":
    process_fuel_card_data('mock_uk_fuel_card_messy.csv', 'clean_emissions_output.json')