import kagglehub
import os
import pandas as pd
import glob
import numpy as np
from dotenv import load_dotenv

# 1. Token Configuration
load_dotenv() # Load variables from .env file
os.environ["KAGGLE_API_TOKEN"] = os.getenv("KAGGLE_TOKEN")

# 2. Download data from Kaggle
print("--- Downloading data from Kaggle ---")
path = kagglehub.dataset_download("isuranga/ai-based-technical-device-asset-profiling-dataset")

# 3. Read data
csv_files = glob.glob(f"{path}/*.csv")
if not csv_files:
    print("CSV file not found!")
    exit()

df = pd.read_csv(csv_files[0])
print(f"Successfully loaded {len(df)} rows of data.")

# 4. Data Enrichment
num_rows = len(df)

# --- FIX ERROR HERE ---
# Initialize column with string type (None instead of np.nan to cast to Object from the start)
df['Assigned_To_ID'] = None 

# Define mask (Ensure 'asset_status' exists in Kaggle file)
mask_active = df['asset_status'].isin(['In_Use', 'Under_Maintenance'])
num_active = mask_active.sum()

# Assign Employee ID
if num_active > 0:
    # Use .astype(object) to ensure Pandas accepts string assignment
    df['Assigned_To_ID'] = df['Assigned_To_ID'].astype(object)
    df.loc[mask_active, 'Assigned_To_ID'] = [f'NV-{np.random.randint(1, 201)}' for _ in range(num_active)]

# Assign Campus
df['Campus'] = np.random.choice(['District 7', 'Sala', 'Garden Hills'], num_rows)

# 5. Save master file
output_dir = "data/raw"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
df.to_csv(os.path.join(output_dir, "master_assets.csv"), index=False)
print("--- Successfully created master_assets.csv! ---")
