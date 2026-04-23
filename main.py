import sys
import subprocess
import os
import time
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

# Thiết lập encoding utf-8 cho terminal để in tiếng Việt không bị lỗi
sys.stdout.reconfigure(encoding='utf-8')

# Tải cấu hình từ .env
load_dotenv()

def wait_for_db_ready():
    print("\n[SYSTEM] Đang kích hoạt hạ tầng Docker và chờ Database...")
    
    # Kích hoạt docker-compose (tự động tải image nếu chưa có, bỏ qua nếu đã chạy)
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    
    max_retries = 10
    print("           Bắt đầu gõ cửa thăm dò Database...")
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                dbname=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASS"),
                host=os.getenv("DB_HOST"),
                port=os.getenv("DB_PORT")
            )
            conn.close()
            print("  --> Gõ cửa thành công! Database ĐÃ SẴN SÀNG!")
            return
        except OperationalError:
            print(f"  --> Chờ Database thức dậy (Lần thử {i+1}/{max_retries})...")
            time.sleep(2)
            
    print("  --> LỖI MẠNG: Database từ chối kết nối. Vui lòng check lại Docker Desktop!")
    sys.exit(1)

def run_python_script(path):
    print(f"\n[PYTHON] Đang chạy: {path}...")
    
    # Sử dụng sys.executable để lấy đúng đường dẫn của venv hiện tại
    python_executable = sys.executable 
    
    # Ép các tiến trình con dùng UTF-8 trên console Windows
    run_env = os.environ.copy()
    run_env["PYTHONUTF8"] = "1"
    
    result = subprocess.run([python_executable, path], capture_output=True, text=True, encoding='utf-8', env=run_env)
    
    if result.returncode == 0:
        print(f"  --> Thành công!")
    else:
        print(f"  --> LỖI: {result.stderr}")
        exit(1)

def run_sql_file(file_path):
    print(f"\n[SQL] Đang thực thi: {file_path}...")
    try:
        # Kết nối DB từ biến môi trường
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        
        # Đọc nội dung file SQL
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_query = f.read()
        
        # Thực thi SQL
        cur.execute(sql_query)
        conn.commit()
        
        print(f"  --> Thành công: Đã cập nhật View/Table từ {file_path}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  --> LỖI SQL: {e}")
        exit(1)

def main():
    print("="*50)
    print("KHỞI CHẠY HỆ THỐNG DATA PIPELINE")
    print("="*50)
    
    # BƯỚC 0: INFRASTRUCTURE SETUP
    wait_for_db_ready()
    
    # BƯỚC 1: EXTRACT (Python)
    # Tải dữ liệu từ Kaggle và tạo dữ liệu giả lập
    run_python_script("scripts/extract_assets_to_csv.py")
    run_python_script("scripts/extract_employees_to_csv.py")
    run_python_script("scripts/extract_enroll_to_csv.py")
    
    # BƯỚC 2: LOAD (Python)
    # Nạp dữ liệu thô từ CSV vào Postgres (Staging Layer)
    run_python_script("scripts/load_csv_to_db.py")
    
    # BƯỚC 3: SEED - Ghi đè các business rules vào dữ liệu thô
    # Phải chạy TRƯỚC khi tạo View để View phản chiếu đúng giá trị
    run_sql_file("sql/seed_depreciation.sql")

    # BƯỚC 4: TRANSFORM & AUDIT (SQL)
    # Chạy theo thứ tự: trf_ (làm sạch) -> fct_ (tổng hợp kiểm toán)
    # Lưu ý: fct_asset_audit phụ thuộc vào trf_assets và trf_employees
    sql_files = [
        "sql/trf_assets.sql",
        "sql/trf_employees.sql",
        "sql/fct_asset_audit.sql"
    ]
    for sql in sql_files:
        run_sql_file(sql)
        
    # BƯỚC 4: REPORT (Python)
    # Xuất báo cáo tóm tắt cuối cùng
    run_python_script("scripts/db_data_summary.py")
    
    print("\n" + "="*50)
    print("TOÀN BỘ QUY TRÌNH ĐÃ HOÀN TẤT THÀNH CÔNG!")
    print("="*50)

if __name__ == "__main__":
    main()