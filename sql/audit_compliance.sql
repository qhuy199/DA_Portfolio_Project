DROP VIEW IF EXISTS vw_asset_audit CASCADE;

CREATE VIEW vw_asset_audit AS
SELECT 
    a.asset_id,
    a.serial_number,
    a.asset_status,
    a."Assigned_To_ID",
    e."Primary_User",
    CASE 
        WHEN a.asset_status IN ('In_Use', 'Under_Maintenance') AND e.serial_number IS NULL THEN 'Missing Enrollment'
        WHEN a.asset_status IN ('In_Use', 'Under_Maintenance') 
             AND a."Assigned_To_ID" IS NOT NULL AND e."Primary_User" IS NOT NULL 
             AND a."Assigned_To_ID" != e."Primary_User" THEN 'Mismatch User'
        WHEN a.asset_status IN ('In_Storage', 'Retired', 'Lost') AND e.serial_number IS NOT NULL THEN 'Ghost Device'
        ELSE 'Healthy'
    END AS audit_status
FROM vw_asset_clean a
LEFT JOIN stg_enrollment e ON a.serial_number = e.serial_number;
--------------
SELECT * FROM vw_asset_audit LIMIT 5;
--------------
SELECT audit_status, COUNT(*) 
FROM vw_asset_audit 
GROUP BY audit_status;

CREATE OR REPLACE VIEW vw_asset_clean AS
SELECT 
    asset_id,
    device_category,
    manufacturer,
    model_name,
    serial_number,
    -- Ép kiểu ngày tháng
    CAST(NULLIF(purchase_date, '') AS DATE) AS purchase_date,
    CAST(NULLIF(warranty_end_date, '') AS DATE) AS warranty_end_date,
    -- Thay thế NULL bằng giá trị mặc định để dashboard không bị trống
    COALESCE("Assigned_To_ID", 'Unassigned') AS "Assigned_To_ID",
    COALESCE("Campus", 'Unknown') AS "Campus",
    purchase_price_usd,
    asset_status
FROM stg_assets;