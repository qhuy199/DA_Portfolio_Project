import pandas as pd
from sqlalchemy import create_engine
import os
import sys
from dotenv import load_dotenv

# Tải biến môi trường
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

# Kết nối database bằng biến môi trường
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

import warnings
from sqlalchemy import text
# Bỏ qua warning không quan trọng
warnings.filterwarnings('ignore')

def load_data():
    files = {
        'master_assets.csv': 'stg_assets',
        'master_employees.csv': 'dim_employees',
        'master_enrollment.csv': 'stg_enrollment'
    }
    
    data_dir = "data/raw"
    
    for file, table in files.items():
        file_path = os.path.join(data_dir, file)
        print(f"--- Đang nạp {file_path} vào bảng {table}... ---")
        try:
            df = pd.read_csv(file_path)
            
            # Xóa dữ liệu cũ thay vì báo DROP TABLE để tránh lỗi View Dependent
            with engine.begin() as conn:
                try:
                    conn.execute(text(f'TRUNCATE TABLE {table} CASCADE;'))
                except Exception:
                    pass # Bỏ qua nếu bảng chưa tồn tại
            
            df.to_sql(table, engine, if_exists='append', index=False)
            print(f"Thành công: Đã nạp {len(df)} dòng vào {table}.")
        except Exception as e:
            print(f"Lỗi khi nạp {file}: {e}")
            import sys
            sys.exit(1) # Bắt buộc phải dừng Pipeline nếu có file bị lỗi

if __name__ == "__main__":
    load_data()