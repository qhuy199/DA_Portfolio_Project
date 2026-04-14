import pandas as pd
import numpy as np

# 1. Đọc file asset vừa tạo
df_assets = pd.read_csv("master_assets.csv")

# 2. Tạo pool "Hợp lệ" (Laptop/Desktop VÀ In_Use/Under_Maintenance)
pool_hop_le = df_assets[
    (df_assets['device_category'].isin(['Laptop', 'Desktop'])) & 
    (df_assets['asset_status'].isin(['In_Use', 'Under_Maintenance']))
].copy()

# 3. Tạo 3% LỖI: Có trong Asset (In_Use) nhưng KHÔNG có trong Enrollment (IT quên nhập)
# Chúng ta lấy 97% dữ liệu hợp lệ để đi tiếp
df_enroll = pool_hop_le.sample(frac=0.97).copy()

# 4. Tạo 5% LỖI: Máy không phải In_Use/Under_Maint nhưng VẪN có trong Enrollment
pool_ngoai_le = df_assets[
    (df_assets['device_category'].isin(['Laptop', 'Desktop'])) & 
    (~df_assets['asset_status'].isin(['In_Use', 'Under_Maintenance']))
].sample(frac=0.05).copy()

df_enroll = pd.concat([df_enroll, pool_ngoai_le])

# 5. Gán thông tin Enrollment & Tạo 10% LỖI: Sai mã NV (Primary_User != Assigned_To_ID)
num_enroll = len(df_enroll)
df_enroll['Primary_User'] = df_enroll['Assigned_To_ID']

# Chọn 10% dòng để đổi mã NV khác
mismatch_idx = df_enroll.sample(frac=0.1).index
df_enroll.loc[mismatch_idx, 'Primary_User'] = [f'NV-{np.random.randint(1, 201)}' for _ in range(len(mismatch_idx))]

# 6. Bổ sung các trường chuyên môn anh yêu cầu
df_enroll['Entra_Join_Type'] = np.random.choice(['Hybrid Azure AD Join', 'Azure AD Join'], num_enroll)
df_enroll['Windows_Device_Autopilot'] = True
df_enroll['Windows_Autopilot_Profile'] = 'Assigned'
df_enroll['ASM_State'] = 'Enrolled'
df_enroll['OS'] = np.random.choice(['Windows 10', 'Windows 11'], num_enroll)

# Lưu file
df_enroll[['serial_number', 'Primary_User', 'Entra_Join_Type', 'Windows_Device_Autopilot', 'Windows_Autopilot_Profile', 'ASM_State', 'OS']].to_csv("master_enrollment.csv", index=False)

print("--- Đã tạo Enrollment với đầy đủ các bẫy dữ liệu của anh! ---")