DROP VIEW IF EXISTS trf_assets CASCADE;
CREATE VIEW trf_assets AS
SELECT asset_id,
    device_category,
    manufacturer,
    model_name,
    serial_number,
    -- Cast to Date type so Power BI recognizes it as date format
    CAST(NULLIF(purchase_date, '') AS DATE) AS purchase_date,
    CAST(NULLIF(warranty_end_date, '') AS DATE) AS warranty_end_date,
    CAST(NULLIF(eol_date, '') AS DATE) AS eol_date,
    CAST(NULLIF(eos_date, '') AS DATE) AS eos_date,
    physical_location,
    asset_status,
    purchase_price_usd,
    depreciation_rate,
    replacement_cost,
    maintenance_cost,
    operating_system,
    "Assigned_To_ID",
    "Campus"
FROM stg_assets;