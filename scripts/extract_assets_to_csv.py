import kagglehub
import os
import pandas as pd
import glob
import numpy as np
from dotenv import load_dotenv

# 1. Cấu hình Token
load_dotenv() # Tải biến từ file .env
os.environ["KAGGLE_API_TOKEN"] = os.getenv("KAGGLE_TOKEN")

# 2. Tải dữ liệu từ Kaggle
print("--- Đang tải dữ liệu từ Kaggle ---")
path = kagglehub.dataset_download("isuranga/ai-based-technical-device-asset-profiling-dataset")

# 3. Đọc dữ liệu
csv_files = glob.glob(f"{path}/*.csv")
if not csv_files:
    print("Không tìm thấy file CSV!")
    exit()

df = pd.read_csv(csv_files[0])
print(f"Đã tải thành công {len(df)} dòng dữ liệu.")

# 4. "Làm giàu" dữ liệu (Data Enrichment)
num_rows = len(df)

# --- FIX LỖI Ở ĐÂY ---
# Khởi tạo cột với kiểu chuỗi (None thay vì np.nan để ép kiểu sang Object ngay từ đầu)
df['Assigned_To_ID'] = None 

# Xác định mask (Phải đảm bảo 'asset_status' tồn tại trong file Kaggle)
mask_active = df['asset_status'].isin(['In_Use', 'Under_Maintenance'])
num_active = mask_active.sum()

# Gán mã NV
if num_active > 0:
    # Sử dụng .astype(object) để đảm bảo Pandas chấp nhận gán chuỗi
    df['Assigned_To_ID'] = df['Assigned_To_ID'].astype(object)
    df.loc[mask_active, 'Assigned_To_ID'] = [f'NV-{np.random.randint(1, 201)}' for _ in range(num_active)]

# Gán Campus
df['Campus'] = np.random.choice(['District 7', 'Sala', 'Garden Hills'], num_rows)

# 5. Lưu lại file master
output_dir = "data/raw"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)
df.to_csv(os.path.join(output_dir, "master_assets.csv"), index=False)
print("--- Đã tạo file master_assets.csv thành công! ---")