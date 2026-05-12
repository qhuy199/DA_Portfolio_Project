# AGENTS (Single Source of Truth) — DA Portfolio Project

> **File này là Single Source of Truth cho mọi AI coding assistant (Antigravity, Cline, Claude, v.v.).**
> Mọi quyết định về code style, kiến trúc, conventions đều phải tuân theo file này.
> Nếu cần kiến thức đặc thù, AI sẽ tự động load các file trong thư mục `.agents/skills/`.

---

## 1. Thông Tin Dự Án

- **Tên:** Modern Workspace Deployment Management — Data Pipeline
- **Loại:** Portfolio project (Data Engineering)
- **Kiến trúc:** ELT (Extract → Load → Transform)
- **Tech Stack:** Python 3.9+, Pandas, SQLAlchemy, Psycopg2, PostgreSQL 15 (Docker), Power BI
- **Orchestrator:** `main.py` — điều phối toàn bộ pipeline bằng subprocess
- **Mục tiêu nghiệp vụ:** Mô phỏng quy trình đối soát cấu hình thiết bị CNTT (IT Asset Audit) cho doanh nghiệp

---

## 2. Ngôn Ngữ & Giao Tiếp

- **Comment trong code:** Tiếng Anh (English) (rõ ràng, ngắn gọn)
- **Print/Log messages:** Tiếng Anh (English)
- **Tên biến, hàm, file:** Tiếng Anh (snake_case)
- **README & Documentation:** Tiếng Anh (English)
- **Commit messages:** Tiếng Anh (English)

---

## 3. Code Style & Conventions

### 3.1 Python
- **Naming:** `snake_case` cho biến, hàm, module. `UPPER_SNAKE_CASE` cho constants.
- **Encoding:** Luôn đặt `sys.stdout.reconfigure(encoding='utf-8')` ở đầu mỗi script chạy độc lập.
- **Import order:** stdlib → third-party → local (cách nhau 1 dòng trống).
- **String format:** Dùng f-string.
- **Path handling:** Dùng `os.path.join()` (không hardcode path separator).
- **Config/Secrets:** Đọc từ `.env` qua `python-dotenv`. **KHÔNG BAO GIỜ** hardcode credentials.
- **Error handling pattern:**
  ```python
  try:
      # logic
  except SpecificException as e:
      print(f"  --> LỖI: {e}")
      exit(1)
  ```
- **Subprocess:** Dùng `sys.executable` khi gọi Python subprocess (đảm bảo đúng venv).
- **Dependencies:** Khai báo trong `requirement.txt` với version pinning (`==`).

### 3.2 SQL
- **Keywords:** VIẾT HOA (`SELECT`, `FROM`, `WHERE`, `CREATE VIEW`, ...)
- **Indentation:** 4 spaces
- **Alias:** Dùng alias ngắn gọn (`a` cho assets, `e` cho enrollment)
- **Views:** Luôn `DROP VIEW IF EXISTS ... CASCADE` trước `CREATE VIEW`
- **Comment:** `--` inline comment (tiếng Việt)

### 3.3 File Naming

| Layer | Prefix | Ví dụ |
|---|---|---|
| Extract scripts | `extract_` | `extract_assets_to_csv.py` |
| Load scripts | `load_` | `load_csv_to_db.py` |
| Staging tables | `stg_` | `stg_enrollment` |
| Transform SQL | `trf_` | `trf_assets.sql` |
| Seed/Lookup SQL | `seed_` | `seed_depreciation.sql` |
| Fact views | `fct_` | `fct_asset_audit.sql` |
| Utility scripts | `db_` hoặc mô tả rõ | `db_data_summary.py` |

---

## 4. Kiến Trúc & Pipeline Flow

### 4.1 Thứ tự thực thi (QUAN TRỌNG — không được đảo)
```
1. Infrastructure  → docker-compose up + health check
2. EXTRACT         → scripts/extract_*.py  → data/raw/*.csv
3. LOAD            → scripts/load_csv_to_db.py → stg_* tables
4. SEED            → sql/seed_depreciation.sql (business rules)
5. TRANSFORM       → sql/trf_*.sql → trf_* views
6. FACT            → sql/fct_asset_audit.sql (phụ thuộc trf_assets, trf_employees)
7. REPORT          → scripts/db_data_summary.py
```

### 4.2 Database Schema & Relationships

#### A. Các thực thể chính (Entities)
1.  **`trf_assets` (View):** Thông tin quản lý thiết bị.
    *   *Key:* `serial_number` (Unique), `asset_id`
    *   *Cột quan trọng:* `device_category`, `asset_status`, `"Assigned_To_ID"` (Mã NV đang giữ máy), `purchase_price_usd`, `operating_system`.
2.  **`stg_enrollment` (Table):** Dữ liệu thực tế từ hệ thống MDM (Intune/Jamf).
    *   *Key:* `serial_number`
    *   *Cột quan trọng:* `"Primary_User"` (Email/Mã NV đang đăng nhập thực tế), `Entra_Join_Type`, `OS`.
3.  **`trf_employees` (View):** Danh mục nhân sự.
    *   *Key:* `"Employee_ID"`
    *   *Cột quan trọng:* `full_name`, `department`, `status`.

#### B. Mối quan hệ & Logic Join (Relationships)
-   **Đối soát (Audit):** `trf_assets` (a) **FULL OUTER JOIN** `stg_enrollment` (e) ON `a.serial_number = e.serial_number`.
-   **Kiểm tra người dùng:** So khớp `a."Assigned_To_ID"` (kế toán quản lý) với `e."Primary_User"` (hệ thống ghi nhận).
-   **Mapping nhân sự:** `trf_assets."Assigned_To_ID"` **LEFT JOIN** `trf_employees."Employee_ID"`.

#### C. Quy tắc đặt tên (Naming)
-   Luôn dùng dấu ngoặc kép `"` cho các cột có chữ viết hoa hoặc ký tự đặc biệt (ví dụ: `"Assigned_To_ID"`, `"Employee_ID"`) để tránh lỗi Postgres.

### 4.3 Cấu trúc thư mục
```
scripts/          → Python logic (Extract + Load + Report)
sql/              → SQL logic (Seed + Transform + Fact)
data/raw/         → CSV output (auto-generated, git-tracked selectively)
data/processed/   → (Reserved cho tương lai)
reports/          → Power BI .pbix files
```

---

## 5. Business Logic & Data Traps

### 5.1 Bẫy dữ liệu được cài cắm (Intentional Data Quality Issues)
Các lỗi này được TẠO CỐ Ý trong `extract_enroll_to_csv.py` để kiểm tra năng lực phân tích:

| Loại lỗi | Tỷ lệ | Mô tả |
|---|---|---|
| Missing Enrollment | ~3% | Máy In_Use/Under_Maintenance nhưng KHÔNG có enrollment record |
| Ghost Device | ~5% | Máy Retired/In_Storage/Lost nhưng VẪN xuất hiện trong enrollment |
| Mismatch User (cùng pool) | ~10% | `Primary_User ≠ Assigned_To_ID` (cả 2 đều là NV hợp lệ) |
| Mismatch User (NV ảo) | ~2% | `Primary_User = 'NV-999'` (NV không tồn tại) |

### 5.2 Audit Status Logic (fct_asset_audit)
Thứ tự ưu tiên CASE WHEN (KHÔNG ĐƯỢC thay đổi thứ tự):
1. `Unknown Asset (Enrollment only)` — Chỉ có trong Enrollment
2. `Ghost Device` — Máy đã retire/storage/lost nhưng enrollment vẫn active
3. `Out Of Enrollment Scope` — Không phải Laptop/Desktop hoặc đã Retired
4. `Missing Enrollment (Active Device)` — Máy active nhưng chưa enroll
5. `Healthy (Asset in Storage)` — Máy trong kho, chưa cần enroll
6. `Mismatch User` — Sai khác thông tin người dùng
7. `Healthy` — Khớp hoàn toàn

---

## 6. Quy Tắc Chung Cho AI Assistant

### 6.1 Giao tiếp & Tư duy trước khi hành động
- **Làm rõ trước khi trả lời:** Nếu yêu cầu của người dùng chưa đủ rõ ràng hoặc có thể hiểu theo nhiều cách, AI phải **hỏi lại** để xác nhận trước khi thực hiện.
- **Giải thích bản chất:** Khi người dùng hỏi về một khái niệm hoặc kỹ thuật, AI phải nêu rõ:
  1. **Ý nghĩa cốt lõi** — Vấn đề này là gì, tại sao nó tồn tại.
  2. **Khi nào dùng / không dùng** — Use case phù hợp và anti-pattern cần tránh.
  3. **Liên hệ DE Roadmap** — Vấn đề này nằm ở đâu trong bức tranh lớn (Data Engineering, BI, Analytics).
- **Đánh giá trước khi sửa:** Khi người dùng yêu cầu chỉnh sửa, AI phải:
  1. **Đánh giá hiện trạng** — Cái hiện tại đang hoạt động như thế nào.
  2. **Giải thích lý do** — Tại sao code/logic hiện tại lại được viết như vậy.
  3. **Đưa ra ý kiến** — Có nên sửa theo yêu cầu không, hay có giải pháp tốt hơn. Nếu cách hiện tại đã tốt, phải nói thẳng.
- **Cấu trúc phản hồi:** Mỗi câu trả lời phải có đủ:
  1. **Câu trả lời cốt lõi** — Giải quyết đúng yêu cầu, không vòng vo.
  2. **Tư duy hệ thống** — Giải thích logic và reasoning đằng sau giải pháp (tại sao chọn cách này, trade-off là gì).
- **Khi có nhiều lựa chọn:** AI phải:
  1. **Phân tích ưu/nhược điểm** theo bảng so sánh rõ ràng.
  2. **Khuyến nghị cụ thể** theo đúng hướng mục tiêu của người dùng (portfolio, learning, production...).
  3. **Không để người dùng tự đoán** — luôn đưa ra quan điểm và lý do rõ ràng.

### 6.2 Quy tắc kỹ thuật
1. **KHÔNG tự ý thay đổi thứ tự pipeline** trong `main.py` mà không hỏi trước.
2. **KHÔNG xóa hoặc sửa tỷ lệ bẫy dữ liệu** trong extract scripts trừ khi được yêu cầu.
3. **KHÔNG hardcode** database credentials — luôn đọc từ `.env`.
4. **Khi tạo file mới:**
   - Python script → đặt trong `scripts/`
   - SQL file → đặt trong `sql/`
   - Tuân thủ prefix naming ở mục 3.3
5. **Khi sửa SQL view:** Luôn giữ pattern `DROP VIEW IF EXISTS ... CASCADE` + `CREATE VIEW`.
6. **Khi thêm dependency:** Cập nhật `requirement.txt` với version pinning.
7. **Khi tạo output data:** Ghi vào `data/raw/` (Extract) hoặc `data/processed/` (post-processing).
8. **Giữ nguyên comment và docstring** không liên quan đến phần đang sửa.
9. **Encoding:** Mọi file text phải là UTF-8.
10. **Testing:** Sau khi sửa code, mô tả cách test (lệnh cần chạy, output kỳ vọng).
11. **Dashboard Mockups:**
    - Luôn ưu tiên tạo mockup dashboard bằng **HTML/CSS/JS** (độc lập hoặc nhúng) thay vì chỉ dùng hình ảnh tĩnh.
    - **Chất lượng chuyên nghiệp:** Trước khi tạo mockup, AI phải **phân tích dataset** để xác định lĩnh vực nghiệp vụ liên quan. Nếu dataset có thể phục vụ nhiều góc nhìn (vd: Operations, Finance, HR...), phải **hỏi người dùng muốn tập trung vào lĩnh vực nào** trước khi triển khai. Nếu người dùng đã chỉ định lĩnh vực từ trước thì cứ làm theo mà không cần hỏi thêm.
    - **Đề xuất kèm lý do:** Khi hỏi người dùng, AI phải **luôn kèm theo đề xuất của mình** (gồm danh sách trang + lý do chọn). Không chỉ liệt kê lựa chọn mà phải đưa ra quan điểm rõ ràng, ví dụ: *"Tôi đề xuất 5 trang theo mô hình Pyramid Drill-down vì..."*
    - **Cấu trúc nhiều trang:** Khi thiết kế dashboard nhiều trang, tuân theo mô hình **Pyramid Drill-down** (từ rộng đến sâu): Tổng quan (What do we have?) → Vấn đề (What's wrong?) → Chi tiết chuyên sâu (Why & How?). Mỗi trang phải trả lời một câu hỏi nghiệp vụ cụ thể.
    - Insight phải có giá trị thực tế (actionable), phù hợp với đúng lĩnh vực nghiệp vụ được xác định.
    - **Tính khả thi:** Thiết kế phải dễ dàng tái hiện được bằng Power BI (sử dụng các visual chuẩn hoặc custom visual phổ biến).
    - **Thẩm mỹ:** Phong cách **Premium**, hiện đại, bắt trend (Glassmorphism, animations, modern typography).
    - Sử dụng các biến màu từ `quanghuy_powerbi_theme.json`.

12. **Browser Automation:**
    - Sau khi tạo xong file HTML mockup, AI phải **tự động chạy lệnh** (ví dụ: `Start-Process` trên Windows) để mở file đó trên trình duyệt mặc định của người dùng mà không cần chờ yêu cầu thêm.

### 6.3 Kỹ năng chuyên sâu (AI Skills)
- **Power BI & DAX (`powerbi-modeling-mcp`):** Khi người dùng yêu cầu thao tác với Power BI (như tạo/sửa measures, chạy DAX queries, kết nối server qua tool `powerbi-modeling-mcp`), AI **BẮT BUỘC** phải tự động đọc nội dung file `.agents/skills/powerbi-modeling.md` trước khi lên kế hoạch và gọi tool. File này chứa toàn bộ playbook, kiến thức xử lý lỗi, DAX pattern và logic đặc thù cho việc giao tiếp hiệu quả với Power BI.
