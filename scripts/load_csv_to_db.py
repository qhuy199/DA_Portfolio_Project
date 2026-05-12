import pandas as pd
from sqlalchemy import create_engine
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

# Connect to database using env variables
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

import warnings
from sqlalchemy import text
# Ignore unimportant warnings
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
        print(f"--- Loading {file_path} into table {table}... ---")
        try:
            df = pd.read_csv(file_path)
            
            # Truncate old data instead of DROP TABLE to avoid View Dependent errors
            with engine.begin() as conn:
                try:
                    conn.execute(text(f'TRUNCATE TABLE {table} CASCADE;'))
                except Exception:
                    pass # Skip if table does not exist
            
            df.to_sql(table, engine, if_exists='append', index=False)
            print(f"Success: Loaded {len(df)} rows into {table}.")
        except Exception as e:
            print(f"Error loading {file}: {e}")
            import sys
            sys.exit(1) # Force stop Pipeline if any file fails

if __name__ == "__main__":
    load_data()