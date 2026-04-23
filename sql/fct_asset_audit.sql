DROP VIEW IF EXISTS fct_assets_audit CASCADE;

CREATE VIEW fct_assets_audit AS
SELECT
    -- Ưu tiên lấy serial từ Asset, nếu không có thì lấy từ Enrollment
    COALESCE(a.serial_number, e.serial_number) AS serial_number,
    a.asset_status,
    a.device_category,
    a."Assigned_To_ID" AS asset_owner,
    e."Primary_User"   AS enrolled_user,
    CASE
        -- 1. Chỉ có trong Enrollment, không có trong Asset (Máy lạ)
        WHEN a.serial_number IS NULL
            THEN 'Unknown Asset (Enrollment only)'

        -- 2. Không phải Laptop/Desktop → không thuộc phạm vi Enrollment
        WHEN a.device_category NOT IN ('Laptop', 'Desktop')
            THEN 'Out Of Enrollment Scope'

        -- 3. Có trong Asset nhưng không có trong Enrollment
        WHEN e.serial_number IS NULL THEN
            CASE
                WHEN a.asset_status IN ('In_Use', 'Under_Maintenance')
                    THEN 'Missing Enrollment (Active Device)'
                ELSE 'Healthy (Asset in Storage/Retired)'
            END

        -- 4. Ghost Device: Máy đã báo mất/hủy/kho nhưng Enrollment vẫn active
        WHEN a.asset_status IN ('In_Storage', 'Retired', 'Lost')
            AND e.serial_number IS NOT NULL
            THEN 'Ghost Device'

        -- 5. Cả hai đều NULL → phân loại theo asset_status
        WHEN a."Assigned_To_ID" IS NULL
            AND e."Primary_User" IS NULL THEN
            CASE
                WHEN a.asset_status IN ('In_Use', 'Under_Maintenance')
                    THEN 'Healthy'
                ELSE 'Healthy (Asset in Storage/Retired)'
            END

        -- 6. Sai khác thông tin người dùng (bắt được cả trường hợp NULL một bên)
        WHEN a."Assigned_To_ID" IS DISTINCT FROM e."Primary_User"
            THEN 'Mismatch User'

        -- 7. Khớp hoàn toàn
        ELSE 'Healthy'
    END AS audit_status

FROM trf_assets a
FULL OUTER JOIN stg_enrollment e ON a.serial_number = e.serial_number;