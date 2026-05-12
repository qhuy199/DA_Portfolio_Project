import pandas as pd
import numpy as np
import os
import sys
import random

# Set utf-8 encoding for terminal
sys.stdout.reconfigure(encoding='utf-8')

# 1. Define paths
output_dir = "data/raw"
if not os.path.exists(output_dir):
    os.makedirs(output_dir) # Create directory if not exists

# 1. Read newly created asset file
df_assets = pd.read_csv(os.path.join(output_dir, "master_assets.csv"))

# 2. Create "Valid" pool (Laptop/Desktop AND In_Use/Under_Maintenance)
pool_hop_le = df_assets[
    (df_assets['device_category'].isin(['Laptop', 'Desktop'])) & 
    (df_assets['asset_status'].isin(['In_Use', 'Under_Maintenance']))
].copy()

# 3. Create 3% ERROR: In Asset (In_Use/Under_Maintenance) but NOT in Enrollment
# Take 97% of valid data to proceed
df_enroll = pool_hop_le.sample(frac=0.97).copy()

# 4. Create 5% ERROR: Device is not In_Use/Under_Maint but STILL in Enrollment
pool_ngoai_le = df_assets[
    (df_assets['device_category'].isin(['Laptop', 'Desktop'])) & 
    (~df_assets['asset_status'].isin(['In_Use', 'Under_Maintenance']))
].sample(frac=0.05).copy()

df_enroll = pd.concat([df_enroll, pool_ngoai_le])

# 5. Assign Enrollment info & Create 10% ERROR: Wrong Employee ID (Primary_User != Assigned_To_ID)
num_enroll = len(df_enroll)

# Assume employee list exists from NV-1 to NV-200
all_employee_ids = [f'NV-{i}' for i in range(1, 201)]

# First, assign 100% correctly
df_enroll['Primary_User'] = df_enroll['Assigned_To_ID']

# Create pool of 12% error data to ensure no overlap
error_pool_idx = df_enroll.sample(frac=0.12).index
split_point = int(len(error_pool_idx) * (10/12)) # 10% wrong ID, 2% fake ID

# Create 10% ERROR: Select DIFFERENT employee
mismatch_idx = error_pool_idx[:split_point]
# Ensure selected ID is different from current ID
df_enroll.loc[mismatch_idx, 'Primary_User'] = df_enroll.loc[mismatch_idx, 'Primary_User'].apply(
    lambda current_id: np.random.choice([eid for eid in all_employee_ids if eid != current_id])
)

# Ensure 2% cases intentionally create non-existent employee
error_idx = error_pool_idx[split_point:]
df_enroll.loc[error_idx, 'Primary_User'] = 'NV-999'

# 6. Add technical fields based on actual ratio
data = [
    (0.10, 'Azure AD Join', 'Windows 11', 'True', 'Assigned', 'Not Registered'),
    (0.04, 'Azure AD Join', 'Windows 11', 'False', 'Assigned', 'Not Registered'),
    (0.02, 'Azure AD Join', 'Windows 11', 'False', 'Not Assigned', 'Not Registered'),
    (0.01, 'Azure AD Join', 'Windows 11', 'False', 'Not Registered', 'Not Registered'),
    (0.05, 'Azure AD Join', 'Windows 10', 'True', 'Assigned', 'Not Registered'),
    (0.03, 'Azure AD Join', 'Windows 10', 'False', 'Assigned', 'Not Registered'),
    (0.02, 'Azure AD Join', 'Windows 10', 'False', 'Not Assigned', 'Not Registered'),
    (0.01, 'Azure AD Join', 'Windows 10', 'False', 'Not Registered', 'Not Registered'),
    (0.30, 'Azure AD Join', 'MacOS', 'False', 'Not Registered', 'Assigned'),
    (0.005, 'Azure AD Join', 'MacOS', 'False', 'Not Registered', 'Not Registered'),
    (0.10, 'Hybrid Azure AD Join', 'Windows 11', 'False', 'Assigned', 'Not Registered'),
    (0.02, 'Hybrid Azure AD Join', 'Windows 11', 'False', 'Not Assigned', 'Not Registered'),
    (0.01, 'Hybrid Azure AD Join', 'Windows 11', 'False', 'Not Registered', 'Not Registered'),
    (0.15, 'Hybrid Azure AD Join', 'Windows 10', 'False', 'Assigned', 'Not Registered'),
    (0.03, 'Hybrid Azure AD Join', 'Windows 10', 'False', 'Not Assigned', 'Not Registered'),
    (0.01, 'Hybrid Azure AD Join', 'Windows 10', 'False', 'Not Registered', 'Not Registered'),
    (0.01, 'Azure AD Register', 'Windows 11', 'False', 'Assigned', 'Not Registered'),
    (0.01, 'Azure AD Register', 'Windows 11', 'False', 'Not Assigned', 'Not Registered'),
    (0.01, 'Azure AD Register', 'Windows 11', 'False', 'Not Registered', 'Not Registered'),
    (0.03, 'Azure AD Register', 'Windows 10', 'False', 'Assigned', 'Not Registered'),
    (0.01, 'Azure AD Register', 'Windows 10', 'False', 'Not Assigned', 'Not Registered'),
    (0.01, 'Azure AD Register', 'Windows 10', 'False', 'Not Registered', 'Not Registered'),
    (0.01, 'Azure AD Register', 'MacOS', 'False', 'Not Registered', 'Assigned'),
    (0.005, 'Azure AD Register', 'MacOS', 'False', 'Not Registered', 'Not Registered')
]

enrollment_features = []
for ratio, join_type, os_val, autopilot, profile, asm in data:
    count = int(num_enroll * ratio)
    enrollment_features.extend([(join_type, autopilot, profile, asm, os_val)] * count)

missing = num_enroll - len(enrollment_features)
if missing > 0:
    enrollment_features.extend(random.choices(enrollment_features, k=missing))
elif missing < 0:
    enrollment_features = enrollment_features[:num_enroll]

random.shuffle(enrollment_features)
features_df = pd.DataFrame(enrollment_features, columns=['Entra_Join_Type', 'Windows_Device_Autopilot', 'Windows_Autopilot_Profile', 'ASM_State', 'OS'])

df_enroll = df_enroll.reset_index(drop=True)
df_enroll[['Entra_Join_Type', 'Windows_Device_Autopilot', 'Windows_Autopilot_Profile', 'ASM_State', 'OS']] = features_df

# Save file
output_path = os.path.join(output_dir, "master_enrollment.csv")
df_enroll[['serial_number', 'Primary_User', 'Entra_Join_Type', 'Windows_Device_Autopilot', 'Windows_Autopilot_Profile', 'ASM_State', 'OS']].to_csv(output_path, index=False)

print("--- Successfully created Enrollment with all data traps! ---")
