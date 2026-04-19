import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

# Thông tin kết nối
load_dotenv()

conn_params = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASS"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT")
}

def get_inventory_report():
    try:
        conn = psycopg2.connect(**conn_params)
        tables = ['trf_assets', 'stg_enrollment', 'trf_employees']
        
        print(f"{'='*25} DATABASE INVENTORY REPORT {'='*25}")

        for table in tables:
            print(f"\n[BẢNG: {table.upper()}]")
            
            # 1. LẤY SCHEMA (Tên cột và Kiểu dữ liệu)
            schema_query = f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table}' AND table_schema = 'public'
            ORDER BY ordinal_position;
            """
            schema_df = pd.read_sql(schema_query, conn)
            print("\n1. Schema (Cấu trúc):")
            print(schema_df.to_string(index=False))
            
            # 2. LẤY SUMMARY (Số dòng và Check NULL)
            print("\n2. Summary (Tóm tắt dữ liệu):")
            # Tổng số dòng
            total_rows = pd.read_sql(f"SELECT COUNT(*) FROM {table}", conn).iloc[0,0]
            print(f"- Tổng số bản ghi: {total_rows}")
            
            # Kiểm tra NULL cho từng cột
            null_data = []
            for col in schema_df['column_name']:
                # Dùng dấu ngoặc kép để tránh lỗi nếu tên cột có viết hoa
                null_count = pd.read_sql(f'SELECT COUNT(*) FROM {table} WHERE "{col}" IS NULL', conn).iloc[0,0]
                if null_count > 0:
                    null_data.append({"Cột": col, "Số lượng NULL": null_count})
            
            if null_data:
                print("- Các cột bị thiếu dữ liệu (NULL):")
                print(pd.DataFrame(null_data).to_string(index=False))
            else:
                print("- Dữ liệu đầy đủ, không có NULL.")
            
            print("-" * 30)

        # 3. KẾT QUẢ AUDIT (After created view audit)
        print(f"\n{'='*25} AUDIT STATUS SUMMARY {'='*25}")
        try:
            audit_summary = pd.read_sql("SELECT audit_status, COUNT(*) as count FROM fct_assets_audit GROUP BY audit_status", conn)
            print(audit_summary.to_string(index=False))
        except Exception as e:
            print("Lưu ý: Chưa tìm thấy view fct_assets_audit")

        conn.close()
    except Exception as e:
        print(f"Lỗi: {e}")

if __name__ == "__main__":
    get_inventory_report()