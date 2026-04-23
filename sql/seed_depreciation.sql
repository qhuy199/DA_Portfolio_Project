-- Cập nhật tỷ lệ khấu hao thực tế theo từng loại thiết bị
-- Chạy sau bước LOAD để ghi đè giá trị mặc định từ Kaggle không sát thực tế
UPDATE stg_assets
SET depreciation_rate = CASE device_category
        WHEN 'Laptop'          THEN 0.25 + RANDOM() * 0.08   -- 25–33%
        WHEN 'Desktop'         THEN 0.20 + RANDOM() * 0.08   -- 20–28%
        WHEN 'Server'          THEN 0.15 + RANDOM() * 0.10   -- 15–25%
        WHEN 'Network_Device'  THEN 0.15 + RANDOM() * 0.05   -- 15–20%
        WHEN 'IoT'             THEN 0.25 + RANDOM() * 0.15   -- 25–40%
        ELSE 0.20
    END;
