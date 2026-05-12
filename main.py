import sys
import subprocess
import os
import time
import psycopg2
from psycopg2 import OperationalError
from dotenv import load_dotenv

# Set utf-8 encoding for terminal
sys.stdout.reconfigure(encoding='utf-8')

# Load config from .env
load_dotenv()

def wait_for_db_ready():
    print("\n[SYSTEM] Activating Docker infrastructure and waiting for Database...")
    
    # Activate docker-compose (auto pull image if needed, skip if running)
    subprocess.run(["docker-compose", "up", "-d"], check=True)
    
    max_retries = 10
    print("           Start pinging Database...")
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
            print("  --> Ping successful! Database is READY!")
            return
        except OperationalError:
            print(f"  --> Waiting for Database to wake up (Attempt {i+1}/{max_retries})...")
            time.sleep(2)
            
    print("  --> NETWORK ERROR: Database refused connection. Please check Docker Desktop!")
    sys.exit(1)

def run_python_script(path):
    print(f"\n[PYTHON] Running: {path}...")
    
    # Use sys.executable to get correct venv path
    python_executable = sys.executable 
    
    # Force child processes to use UTF-8 on Windows console
    run_env = os.environ.copy()
    run_env["PYTHONUTF8"] = "1"
    
    result = subprocess.run([python_executable, path], capture_output=True, text=True, encoding='utf-8', env=run_env)
    
    if result.returncode == 0:
        print(f"  --> Success!")
    else:
        print(f"  --> ERROR: {result.stderr}")
        exit(1)

def run_sql_file(file_path):
    print(f"\n[SQL] Executing: {file_path}...")
    try:
        # Connect to DB from environment variables
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASS"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        cur = conn.cursor()
        
        # Read SQL file content
        with open(file_path, 'r', encoding='utf-8') as f:
            sql_query = f.read()
        
        # Execute SQL
        cur.execute(sql_query)
        conn.commit()
        
        print(f"  --> Success: Updated View/Table from {file_path}")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"  --> SQL ERROR: {e}")
        exit(1)

def main():
    print("="*50)
    print("DATA PIPELINE INITIALIZATION")
    print("="*50)
    
    # STEP 0: INFRASTRUCTURE SETUP
    wait_for_db_ready()
    
    # STEP 1: EXTRACT (Python)
    # Download data from Kaggle and generate mock data
    run_python_script("scripts/extract_assets_to_csv.py")
    run_python_script("scripts/extract_employees_to_csv.py")
    run_python_script("scripts/extract_enroll_to_csv.py")
    
    # STEP 2: LOAD (Python)
    # Load raw data from CSV to Postgres (Staging Layer)
    run_python_script("scripts/load_csv_to_db.py")
    
    # STEP 3: SEED - Overwrite business rules onto raw data
    # Must run BEFORE creating Views so Views reflect correct values
    run_sql_file("sql/seed_depreciation.sql")

    # STEP 4: TRANSFORM & AUDIT (SQL)
    # Run in order: trf_ (clean) -> fct_ (audit summary)
    # Note: fct_asset_audit depends on trf_assets and trf_employees
    sql_files = [
        "sql/trf_assets.sql",
        "sql/trf_employees.sql",
        "sql/fct_asset_audit.sql"
    ]
    for sql in sql_files:
        run_sql_file(sql)
        
    # STEP 5: REPORT (Python)
    # Export final summary report
    run_python_script("scripts/db_data_summary.py")
    
    print("\n" + "="*50)
    print("ENTIRE PIPELINE COMPLETED SUCCESSFULLY!")
    print("="*50)

if __name__ == "__main__":
    main()