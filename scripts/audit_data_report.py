import pandas as pd
import os

def profile_and_audit(file_list):
    dfs = {}
    
    for file_name, label in file_list.items():
        if not os.path.exists(file_name):
            print(f"Lỗi: Không tìm thấy file {file_name}")
            continue
            
        df = pd.read_csv(file_name)
        dfs[file_name] = df
        
        print(f"\n{'='*20} TÓM TẮT: {label} ({file_name}) {'='*20}")
        print(f"- Số dòng: {len(df)}")
        print(f"- Số cột: {len(df.columns)}")
        print("- Kiểm tra dữ liệu rỗng (NaN) trên các cột quan trọng:")
        # Chỉ kiểm tra cột rỗng để tiết kiệm màn hình
        missing = df.isnull().sum()
        print(missing[missing > 0])
        print("- 3 dòng dữ liệu mẫu:")
        print(df.head(3))

    # KIỂM TRA LOGIC MISMATCH (Audit)
    if "master_assets.csv" in dfs and "master_enrollment.csv" in dfs:
        df_assets = dfs["master_assets.csv"]
        df_enroll = dfs["master_enrollment.csv"]
        
        # Chỉ merge các cột cần thiết để kiểm tra
        merged = pd.merge(df_assets[['serial_number', 'Assigned_To_ID']], 
                          df_enroll[['serial_number', 'Primary_User']], 
                          on='serial_number', how='inner')
        
        mismatch = merged[merged['Assigned_To_ID'] != merged['Primary_User']]
        
        print(f"\n{'='*20} BÁO CÁO AUDIT DỮ LIỆU {'='*20}")
        print(f"- Tổng số máy khớp trong Asset & Enrollment: {len(merged)}")
        print(f"- Số máy bị LỆCH USER (Mismatch): {len(mismatch)} ({round(len(mismatch)/len(merged)*100, 2)}%)")
        
        # Thêm check lỗi 3%: Asset In_Use nhưng không có trong Enrollment
        in_use_assets = df_assets[df_assets['asset_status'].isin(['In_Use', 'Under_Maintenance'])]
        missing_in_enroll = in_use_assets[~in_use_assets['serial_number'].isin(df_enroll['serial_number'])]
        print(f"- Số máy đang hoạt động nhưng THIẾU record Enrollment (Lỗi 3%): {len(missing_in_enroll)}")

# Danh sách file cần check
files = {
    "master_assets.csv": "TÀI SẢN (ASSETS)",
    "master_employees.csv": "NHÂN SỰ (HR)",
    "master_enrollment.csv": "QUẢN TRỊ (ENROLLMENT)"
}

profile_and_audit(files)