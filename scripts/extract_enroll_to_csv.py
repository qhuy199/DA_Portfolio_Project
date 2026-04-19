import pandas as pd
import numpy as np
import os
import sys
import random

# Thiết lập encoding utf-8 cho terminal để in tiếng Việt không bị lỗi
sys.stdout.reconfigure(encoding='utf-8')

# 1. Định nghĩa đường dẫn
output_dir = "data/raw"
if not os.path.exists(output_dir):
    os.makedirs(output_dir) # Tạo thư mục nếu chưa có

# 1. Đọc file asset vừa tạo
df_assets = pd.read_csv(os.path.join(output_dir, "master_assets.csv"))

# 2. Tạo pool "Hợp lệ" (Laptop/Desktop VÀ In_Use/Under_Maintenance)
pool_hop_le = df_assets[
    (df_assets['device_category'].isin(['Laptop', 'Desktop'])) & 
    (df_assets['asset_status'].isin(['In_Use', 'Under_Maintenance']))
].copy()

# 3. Tạo 3% LỖI: Có trong Asset (In_Use/Under_Maintenance) nhưng KHÔNG có trong Enrollment (máy đang dùng nhưng chưa enroll)
# Chúng ta lấy 97% dữ liệu hợp lệ để đi tiếp
df_enroll = pool_hop_le.sample(frac=0.97).copy()

# 4. Tạo 5% LỖI: Máy không phải In_Use/Under_Maint nhưng VẪN có trong Enrollment (IT nhập sai Asset State)
pool_ngoai_le = df_assets[
    (df_assets['device_category'].isin(['Laptop', 'Desktop'])) & 
    (~df_assets['asset_status'].isin(['In_Use', 'Under_Maintenance']))
].sample(frac=0.05).copy()

df_enroll = pd.concat([df_enroll, pool_ngoai_le])

# 5. Gán thông tin Enrollment & Tạo 10% LỖI: Sai mã NV (Primary_User != Assigned_To_ID)
num_enroll = len(df_enroll)

# Giả sử danh sách NV tồn tại của anh là từ NV-1 đến NV-200 (không có padding 0 để đúng với các file khác)
all_employee_ids = [f'NV-{i}' for i in range(1, 201)]

# Đầu tiên, gán đúng hết 100%
df_enroll['Primary_User'] = df_enroll['Assigned_To_ID']

# Tạo tập chứa 12% dữ liệu lỗi để đảm bảo không bị ghi đè (overlap)
error_pool_idx = df_enroll.sample(frac=0.12).index
split_point = int(len(error_pool_idx) * (10/12)) # 10% lỗi sai mã NV, 2% lỗi mã ảo

# Tạo 10% LỖI: Chọn NV KHÁC (cùng trong danh sách)
mismatch_idx = error_pool_idx[:split_point]
# Sử dụng apply kết hợp list comprehension để CHẮC CHẮN ID được chọn phải khác ID hiện tại
df_enroll.loc[mismatch_idx, 'Primary_User'] = df_enroll.loc[mismatch_idx, 'Primary_User'].apply(
    lambda current_id: np.random.choice([eid for eid in all_employee_ids if eid != current_id])
)

# Đảm bảo 2% trường hợp cố tình tạo ra NV không tồn tại
error_idx = error_pool_idx[split_point:]
df_enroll.loc[error_idx, 'Primary_User'] = 'NV-999'

# 6. Bổ sung các trường chuyên môn dựa trên bảng tỷ lệ thực tế
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

# Lưu file
output_path = os.path.join(output_dir, "master_enrollment.csv")
df_enroll[['serial_number', 'Primary_User', 'Entra_Join_Type', 'Windows_Device_Autopilot', 'Windows_Autopilot_Profile', 'ASM_State', 'OS']].to_csv(output_path, index=False)

print("--- Đã tạo Enrollment với đầy đủ các bẫy dữ liệu của anh! ---")