# %% [markdown]
# # Data Quality & EDA - IT Asset Management
# This script is used for Exploratory Data Analysis (EDA) and verifying intentionally planted Data Traps.
# 💡 Instruction: You can run each code cell directly in VS Code by clicking "Run Cell" (Jupyter extension required).
# This is more convenient than a pure .ipynb file for Git version control.

# %%
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Display configuration
pd.set_option('display.max_columns', None)
sns.set_theme(style="whitegrid")

# %% [markdown]
# ## 1. Database Connection
# Use SQLAlchemy to read data from Postgres. If DB is unavailable, fallback to raw CSVs.

# %%
# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "it_assets")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

# Create connection
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

try:
    df_assets = pd.read_sql("SELECT * FROM trf_assets", engine)
    df_enroll = pd.read_sql("SELECT * FROM stg_enrollment", engine)
    df_employees = pd.read_sql("SELECT * FROM trf_employees", engine)
    print("✅ Successfully loaded data from Database!")
except Exception as e:
    print(f"❌ DB connection error: {e}. Falling back to original CSV files...")
    # Handle relative path (assuming running from scripts/ directory)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    raw_dir = os.path.join(base_dir, '..', 'data', 'raw')
    
    df_assets = pd.read_csv(os.path.join(raw_dir, 'extract_assets.csv'))
    df_enroll = pd.read_csv(os.path.join(raw_dir, 'extract_enrollment.csv'))
    df_employees = pd.read_csv(os.path.join(raw_dir, 'extract_employees.csv'))
    
    # Clean column names if reading from CSV (to match DB format)
    df_assets.columns = df_assets.columns.str.lower()
    df_enroll.columns = df_enroll.columns.str.lower()
    print("✅ Successfully loaded data from CSV!")

# %% [markdown]
# ## 2. Data Profiling
# High-level overview to understand the big picture before diving into details.

# %%
print("--- DATA OVERVIEW ---")
print(f"Device count (Assets): {len(df_assets)}")
print(f"MDM records count (Enrollment): {len(df_enroll)}")
print(f"Employee count: {len(df_employees)}")

print("\n--- MISSING VALUES ---")
print("Assets Table:")
display(df_assets.isnull().sum()[df_assets.isnull().sum() > 0])

# Visualize device status distribution
plt.figure(figsize=(10, 5))
sns.countplot(data=df_assets, y='asset_status', order=df_assets['asset_status'].value_counts().index, palette='Blues_r')
plt.title("Asset Status Distribution", fontsize=14)
plt.xlabel("Count")
plt.ylabel("Status")
plt.show()

# %% [markdown]
# ## 3. Outlier Detection (Histogram & Boxplot)
# Check `purchase_price_usd` column to find devices with unusually high prices.

# %%
plt.figure(figsize=(15, 5))

# 3.1 Histogram (Check distribution shape)
plt.subplot(1, 2, 1)
sns.histplot(df_assets['purchase_price_usd'], bins=30, kde=True, color='#2ecc71')
plt.title("Purchase Price Distribution (Histogram)")
plt.xlabel("Price (USD)")
plt.ylabel("Frequency")

# 3.2 Boxplot (Detect clear Outliers)
plt.subplot(1, 2, 2)
sns.boxplot(x=df_assets['purchase_price_usd'], color='#3498db')
plt.title("Purchase Price Outliers Detection (Boxplot)")
plt.xlabel("Price (USD)")

plt.tight_layout()
plt.show()

# Display outlier devices (e.g., top 5 most expensive)
print("Top 5 most expensive devices (Potential Outliers):")
display(df_assets.nlargest(5, 'purchase_price_usd')[['serial_number', 'device_category', 'purchase_price_usd', 'asset_status']])


# %% [markdown]
# ## 4. Business Data Traps Analysis
# Cross-check Accounting data (Assets) and Reality (Enrollment) to find management loopholes.

# %%
# Merge data for reconciliation (FULL OUTER JOIN - matching fct_asset_audit SQL View logic)
df_audit = pd.merge(df_assets, df_enroll, on='serial_number', how='outer', indicator=True)

# Merge employees to check validity
# Note: Column names depend on DB or CSV, script defaults to standard format
assigned_col = 'assigned_to_id' if 'assigned_to_id' in df_audit.columns else 'Assigned_To_ID'
primary_user_col = 'primary_user' if 'primary_user' in df_audit.columns else 'Primary_User'
emp_id_col = 'employee_id' if 'employee_id' in df_employees.columns else 'Employee_ID'

df_audit = pd.merge(df_audit, df_employees, left_on=assigned_col, right_on=emp_id_col, how='left')
df_audit['_merge_type'] = df_audit['_merge'].map({'left_only': 'Asset Only', 'right_only': 'Enrollment Only', 'both': 'Both'})

# %% [markdown]
# ### 4.1. Missing Enrollment (Approx. 3%)
# Device is recorded as In_Use or Under_Maintenance but has not pinged the MDM system.

# %%
missing_enrollment = df_audit[
    (df_audit['asset_status'].isin(['In_Use', 'Under_Maintenance'])) & 
    (df_audit['_merge_type'] == 'Asset Only')
]
pct_missing = len(missing_enrollment) / len(df_assets) * 100
print(f"🚨 Detected {len(missing_enrollment)} Missing Enrollment devices ({pct_missing:.1f}%)")
display(missing_enrollment[['serial_number', 'asset_status', assigned_col]].head())

# %% [markdown]
# ### 4.2. Ghost Device (Approx. 5%)
# Hardware ghosts: Device reported as retired/lost/in storage but is still online in the network. High security risk!

# %%
ghost_devices = df_audit[
    (df_audit['asset_status'].isin(['Retired', 'In_Storage', 'Lost'])) & 
    (df_audit['_merge_type'] == 'Both')
]
pct_ghost = len(ghost_devices) / len(df_assets) * 100
print(f"👻 Detected {len(ghost_devices)} Ghost Devices ({pct_ghost:.1f}%)")
display(ghost_devices[['serial_number', 'asset_status', primary_user_col]].head())

# %% [markdown]
# ### 4.3. Mismatch User & Virtual Employee
# Device handed over without notice or user is a virtual account that hasn't been disabled.

# %%
df_both = df_audit[df_audit['_merge_type'] == 'Both'].copy()

# Mismatch User (Approx. 10%)
mismatch_user = df_both[df_both[assigned_col] != df_both[primary_user_col]]

# Virtual Employee (Approx. 2%)
valid_employees = df_employees[emp_id_col].tolist()
virtual_employees = df_both[~df_both[primary_user_col].isin(valid_employees)]

print(f"⚠️ Detected {len(mismatch_user)} cases of Mismatch User (Unauthorized device swap)")
print(f"🕵️ Detected {len(virtual_employees)} cases of Virtual Employee (User not in HR records)")

# %% [markdown]
# ### 4.4. Summary of Data Quality Issues
# %%
trap_counts = {
    "Missing Enrollment": len(missing_enrollment),
    "Ghost Devices": len(ghost_devices),
    "Mismatch User": len(mismatch_user),
    "Virtual Employee": len(virtual_employees)
}

plt.figure(figsize=(10, 5))
sns.barplot(x=list(trap_counts.values()), y=list(trap_counts.keys()), palette="Reds_r")
plt.title("Data Quality Issues Summary (Audit Traps)", fontsize=14, fontweight='bold')
plt.xlabel("Error Record Count")
for index, value in enumerate(trap_counts.values()):
    plt.text(value + 1, index, str(value), va='center')
plt.show()
