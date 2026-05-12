import psycopg2
import os
import pandas as pd
from dotenv import load_dotenv

# Connection info
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
            print(f"\n[TABLE: {table.upper()}]")
            
            # 1. GET SCHEMA (Column name and Data type)
            schema_query = f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table}' AND table_schema = 'public'
            ORDER BY ordinal_position;
            """
            schema_df = pd.read_sql(schema_query, conn)
            print("\n1. Schema (Structure):")
            print(schema_df.to_string(index=False))
            
            # 2. GET SUMMARY (Row count and NULL check)
            print("\n2. Summary (Data Overview):")
            # Total rows
            total_rows = pd.read_sql(f"SELECT COUNT(*) FROM {table}", conn).iloc[0,0]
            print(f"- Total records: {total_rows}")
            
            # Check NULL for each column
            null_data = []
            for col in schema_df['column_name']:
                # Use double quotes to avoid errors if column name is capitalized
                null_count = pd.read_sql(f'SELECT COUNT(*) FROM {table} WHERE "{col}" IS NULL', conn).iloc[0,0]
                if null_count > 0:
                    null_data.append({"Column": col, "NULL Count": null_count})
            
            if null_data:
                print("- Columns with missing data (NULL):")
                print(pd.DataFrame(null_data).to_string(index=False))
            else:
                print("- Data is complete, no NULLs.")
            
            print("-" * 30)

        # 3. AUDIT RESULTS (After created view audit)
        print(f"\n{'='*25} AUDIT STATUS SUMMARY {'='*25}")
        try:
            audit_summary = pd.read_sql("SELECT audit_status, COUNT(*) as count FROM fct_assets_audit GROUP BY audit_status", conn)
            print(audit_summary.to_string(index=False))
        except Exception as e:
            print("Note: View fct_assets_audit not found")

        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    get_inventory_report()