import pandas as pd
import os

def audit_all(file_list):
    dfs = {}
    print(f"{'='*60}\nBÁO CÁO TỔNG HỢP HỆ THỐNG IT ASSETS\n{'='*60}")
    
    # 1. Profile dữ liệu và Schema
    for file_name, label in file_list.items():
        if os.path.exists(file_name):
            df = pd.read_csv(file_name)
            dfs[file_name] = df
            print(f"\n[SCHEMA: {label}]")
            # Tạo bảng mô tả cột và kiểu dữ liệu
            schema = pd.DataFrame({'Kiểu dữ liệu': df.dtypes, 'Số giá trị NULL': df.isnull().sum()})
            print(schema.to_string())
        else:
            print(f"[WARN] Không tìm thấy file {file_name}")

    # 2. Logic Audit liên bảng (Cross-Table Audit)
    if "master_assets.csv" in dfs and "master_enrollment.csv" in dfs:
        assets = dfs["master_assets.csv"]
        enroll = dfs["master_enrollment.csv"]
        
        # Audit các loại lỗi
        in_use = assets[assets['asset_status'].isin(['In_Use', 'Under_Maintenance'])]
        mismatch = pd.merge(assets, enroll, on='serial_number', how='inner')
        mismatch = mismatch[mismatch['Assigned_To_ID'] != mismatch['Primary_User']]
        
        missing_enroll = in_use[~in_use['serial_number'].isin(enroll['serial_number'])]
        ghost = assets[assets['asset_status'].isin(['Retired', 'In_Storage', 'Lost']) & 
                       assets['serial_number'].isin(enroll['serial_number'])]

        print(f"\n{'='*60}\nKẾT QUẢ ĐỐI CHIẾU DỮ LIỆU (AUDIT REPORT)\n{'='*60}")
        print(f"- Tổng số tài sản (Assets): {len(assets)}")
        print(f"- Lỗi Mismatch User: {len(mismatch)} trường hợp")
        print(f"- Lỗi Thiếu Enrollment: {len(missing_enroll)} trường hợp")
        print(f"- Lỗi Ghost Device: {len(ghost)} trường hợp")
        print(f"{'='*60}")

if __name__ == "__main__":
    files = {
        "master_assets.csv": "TÀI SẢN (ASSETS)",
        "master_employees.csv": "NHÂN SỰ (HR)",
        "master_enrollment.csv": "QUẢN TRỊ (ENROLLMENT)"
    }
    audit_all(files)