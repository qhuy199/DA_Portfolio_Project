DROP VIEW IF EXISTS fct_assets_audit CASCADE;
CREATE VIEW fct_assets_audit AS
SELECT -- Prioritize serial from Asset, fallback to Enrollment
    COALESCE(a.serial_number, e.serial_number) AS serial_number,
    a.asset_status,
    a.device_category,
    a."Assigned_To_ID" AS asset_owner,
    e."Primary_User" AS enrolled_user,
    CASE
        -- 1. Only in Enrollment, not in Asset (Unknown Device)
        WHEN a.serial_number IS NULL THEN 'Unknown Asset (Enrollment only)' -- 2. Ghost Device: Device reported lost/storage/retired but Enrollment is active
        -- (Prioritize this error before filtering 'Out Of Enrollment Scope')
        WHEN a.asset_status IN ('In_Storage', 'Retired', 'Lost')
        AND e.serial_number IS NOT NULL THEN 'Ghost Device' -- 3. Out of Enrollment Scope (Not Laptop/Desktop, or Retired)
        -- At this point, Retired devices are definitely not in Enrollment
        WHEN a.device_category NOT IN ('Laptop', 'Desktop')
        OR a.asset_status = 'Retired' THEN 'Out Of Enrollment Scope' -- 4. In Asset but not in Enrollment
        WHEN e.serial_number IS NULL THEN CASE
            WHEN a.asset_status IN ('In_Use', 'Under_Maintenance') THEN 'Missing Enrollment (Active Device)'
            ELSE 'Healthy (Asset in Storage)'
        END -- 5. Both are NULL -> classify by asset_status
        WHEN a."Assigned_To_ID" IS NULL
        AND e."Primary_User" IS NULL THEN CASE
            WHEN a.asset_status IN ('In_Use', 'Under_Maintenance') THEN 'Healthy'
            ELSE 'Healthy (Asset in Storage)'
        END -- 6. User mismatch (catches cases where one side is NULL)
        WHEN a."Assigned_To_ID" IS DISTINCT
        FROM e."Primary_User" THEN 'Mismatch User' -- 7. Perfect match
            ELSE 'Healthy'
    END AS audit_status
FROM trf_assets a
    FULL OUTER JOIN stg_enrollment e ON a.serial_number = e.serial_number;