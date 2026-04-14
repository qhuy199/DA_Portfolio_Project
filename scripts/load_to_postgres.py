import pandas as pd
from sqlalchemy import create_engine

# Kết nối tới database trong Docker
engine = create_engine('postgresql://admin:mysecretpassword@localhost:5432/it_management')

def load_data():
    files = {
        'master_assets.csv': 'stg_assets',
        'master_employees.csv': 'dim_employees',
        'master_enrollment.csv': 'stg_enrollment'
    }
    
    for file, table in files.items():
        print(f"--- Đang nạp {file} vào bảng {table}... ---")
        try:
            df = pd.read_csv(file)
            df.to_sql(table, engine, if_exists='replace', index=False)
            print(f"Thành công: Đã nạp {len(df)} dòng vào {table}.")
        except Exception as e:
            print(f"Lỗi khi nạp {file}: {e}")

if __name__ == "__main__":
    load_data()