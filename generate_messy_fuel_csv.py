import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Generate 50 rows of mock UK fuel card data
np.random.seed(42)
dates = [datetime(2023, 10, 1) + timedelta(days=i) for i in range(50)]
vehicles = [f"BV67 {chr(65+i)}{chr(65+i)}{chr(65+i)}" for i in range(10)] # Mock UK number plates

# Intentionally introduce "messy" real-world variations
fuel_types = np.random.choice(['DERV', 'Diesel', 'diesel', 'Diesel (Premium)', 'AdBlue', np.nan], 50)
litres = np.round(np.random.uniform(20.0, 80.0, 50), 2)
cost = np.round(litres * np.random.uniform(1.45, 1.65, 50), 2)

# Create messy dataframe
df = pd.DataFrame({
    'Transaction Date': [d.strftime('%d/%m/%Y') for d in dates], # UK date format
    'Vehicle Registration': np.random.choice(vehicles, 50),
    'Fuel Type': fuel_types,
    'Volume (L)': litres,
    'Total Cost (£)': cost,
    'Merchant': np.random.choice(['Shell', 'BP', 'Esso', 'MOTO Services', 'Unknown Stop'], 50),
    'Driver ID': np.random.choice(['D001', 'D002', 'D003', 'MISSING'], 50)
})

# Introduce intentional errors for your parser to handle
df['Volume (L)'] = df['Volume (L)'].astype(object) # <-- ADD THIS LINE
df.loc[12, 'Transaction Date'] = '2023-10-13' # Mixed date formats (ISO vs UK)
df.loc[25, 'Vehicle Registration'] = ''     # Blank value

# Save to CSV
df.to_csv('mock_uk_fuel_card_messy.csv', index=False)
print("Generated mock_uk_fuel_card_messy.csv")