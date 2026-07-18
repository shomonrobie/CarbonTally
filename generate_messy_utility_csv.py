import pandas as pd
import numpy as np

# Generate 20 rows of mock UK Utility data (Electricity & Gas)
np.random.seed(42)
dates = pd.date_range(start='2023-10-01', periods=20, freq='MS') # Monthly starts

# Messy meter IDs (MPAN for electricity, MPRN for gas)
meters = ['1234567890123', '9876543210987', '1112223334445', 'UNKNOWN_METER']

df = pd.DataFrame({
    'Billing Period Start': dates.strftime('%d/%m/%Y'),
    'Meter Type': np.random.choice(['Electricity', 'Gas', 'electricity', 'NAT GAS', np.nan], 20),
    'Meter ID (MPAN/MPRN)': np.random.choice(meters, 20),
    'Consumption (kWh)': np.round(np.random.uniform(1000.0, 15000.0, 20), 2),
    'Cost (£)': np.round(np.random.uniform(200.0, 3000.0, 20), 2),
    'Site Name': np.random.choice(['Birmingham Hub', 'London Warehouse', 'Manchester Factory', ''], 20)
})

# Introduce intentional errors
df['Consumption (kWh)'] = df['Consumption (kWh)'].astype(object) # <-- ADD THIS LINE
df.loc[3, 'Consumption (kWh)'] = 'N/A'             # Text in numeric column
df.loc[7, 'Meter Type'] = 'Standing Charge'        # Not actual consumption
df.loc[12, 'Billing Period Start'] = '2023-11-01'  # ISO date format mixed in
df.loc[15, 'Consumption (kWh)'] = np.nan           # Missing value

df.to_csv('mock_uk_utility_bill.csv', index=False)
print("Generated mock_uk_utility_bill.csv")