DROP VIEW IF EXISTS trf_employees CASCADE;

CREATE VIEW trf_employees AS
SELECT 
    "Employee_ID",
    TRIM("Full_Name") AS full_name,
    TRIM("Department") AS department,
    TRIM("Position") AS position,
    -- Ép kiểu ngày Join_Date từ text sang date
    CAST(NULLIF("Join_Date", '') AS DATE) AS join_date,
    TRIM("Status") AS status
FROM dim_employees;