import pandas as pd
import numpy as np

# Create 200 employees
hr_data = {
    'Employee_ID': [f'NV-{i}' for i in range(1, 201)],
    'Full_Name': [f'Employee Name {i}' for i in range(1, 201)],
    'Department': np.random.choice(['IT', 'HR', 'Finance', 'Sales', 'Academic', 'Operations'], 200),
    'Position': np.random.choice(['Manager', 'Staff', 'Lead', 'Coordinator'], 200),
    'Join_Date': pd.to_datetime(np.random.choice(pd.date_range('2020-01-01', '2025-01-01'), 200)),
    # Simulate 10% disabled employees
    'Status': np.random.choice(['Working', 'Disabled'], 200, p=[0.9, 0.1])
}

df_hr = pd.DataFrame(hr_data)
import os
output_dir = "data/raw"
if not os.path.exists(output_dir):
    os.makedirs(output_dir)

df_hr.to_csv(os.path.join(output_dir, "master_employees.csv"), index=False)
print("--- Successfully created Master_Employees! ---")
