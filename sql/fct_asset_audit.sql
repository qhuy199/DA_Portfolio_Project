DROP VIEW IF EXISTS fct_assets_audit CASCADE;

CREATE VIEW fct_assets_audit AS
SELECT 
    -- Ưu tiên lấy serial từ Asset, nếu không có thì lấy từ Enrollment
    COALESCE(a.serial_number, e.serial_number) AS serial_number,
    a.asset_status,
    a."Assigned_To_ID" AS asset_owner,
    e."Primary_User" AS enrolled_user,
    CASE 
        -- 1. TRƯỜNG HỢP CHỈ CÓ TRONG ENROLLMENT (Máy lạ/Máy ngoài danh mục tài sản)
        WHEN a.serial_number IS NULL THEN 'Unknown Asset (Enrollment only)'

        -- 2. TRƯỜNG HỢP CÓ TRONG ASSET NHƯNG KHÔNG CÓ TRONG ENROLLMENT
        WHEN e.serial_number IS NULL THEN 
            CASE 
                WHEN a.asset_status IN ('In_Use', 'Under_Maintenance') THEN 'Missing Enrollment (Active Device)'
                ELSE 'Healthy (Asset in Storage/Retired)' -- Máy kho không cần enroll là bình thường
            END

        -- 3. TRƯỜNG HỢP CÓ CẢ HAI NHƯNG SAI KHÁC THÔNG TIN
        WHEN a."Assigned_To_ID" != e."Primary_User" THEN 'Mismatch User'

        -- 4. TRƯỜNG HỢP GHOST DEVICE (Máy đã báo mất/hủy nhưng Enrollment vẫn active)
        WHEN a.asset_status IN ('In_Storage', 'Retired', 'Lost') AND e.serial_number IS NOT NULL THEN 'Ghost Device'

        -- 5. TRƯỜNG HỢP KHỚP HOÀN TOÀN
        ELSE 'Healthy'
    END AS audit_status
FROM trf_assets a
FULL OUTER JOIN stg_enrollment e ON a.serial_number = e.serial_number;