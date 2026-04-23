# 🏢 Modern Workspace Deployment Management - Data Pipeline

Dự án này là một **Data Engineering Pipeline (Kiến trúc ELT)** hoàn chỉnh, tập trung vào việc mô phỏng quá trình quản lý và đối soát cấu hình thiết bị CNTT (IT Assets) cho nhân sự trong doanh nghiệp. Hệ thống hoàn toàn tự động hóa từ bước kéo dữ liệu chuẩn Kaggle, tạo kịch bản bẫy dữ liệu (Data Traps), nạp vào CSDL PostgreSQL và xử lý nghiệp vụ thông qua Data Warehouse (Mô hình Kimball).

---

## 🏗️ Kiến trúc & Công nghệ (Tech Stack)

- **Ngôn ngữ:** Python (Pandas, SQLAlchemy, Psycopg2)
- **Database:** PostgreSQL (Triển khai trên Docker)
- **Kiến trúc luồng dữ liệu:** ELT (Extract - Load - Transform)
- **Môi trường:** Docker, Virtual Environment

---

## 🚀 Hướng dấn Cài đặt & Chạy dự án (Quick Start)

Pipeline được thiết kế để chỉ cần bấm **1 nút duy nhất** là toàn bộ hệ thống (kể cả Docker Database) sẽ tự động kích hoạt. Xin làm theo đúng 3 bước sau:

### Bước 1: Yêu cầu hệ thống (Prerequisites)
- Đảm bảo máy tính đã cài đặt sẵn **Python 3.9+**
- Đảm bảo máy tính đã cài và đang mở ứng dụng **Docker Desktop**

### Bước 2: Chuẩn bị biến môi trường (Environment Setup)
Hệ thống sử dụng file `.env` để bảo mật thông tin.
1. Tại thư mục gốc, tìm file có tên `.env.example`.
2. Đổi tên (hoặc copy) file này thành **`.env`** (chỗ này rất quan trọng).
3. (Tùy chọn) Để kéo dữ liệu thực từ Kaggle, bạn cần điền `KAGGLE_TOKEN` của riêng bạn vào file `.env`. 
*(Cách lấy: Truy cập Kaggle.com -> Settings -> Account -> Create New API Token -> Dán chuỗi bí mật vào mục KAGGLE_TOKEN).*

### Bước 3: Khởi chạy Data Pipeline
Mở Terminal (Powershell/CMD) tại thư mục dự án và chạy các lệnh sau:

```bash
# 1. Tạo và kích hoạt môi trường bộ nhớ ảo (nếu bạn chưa có)
python -m venv venv
.\venv\Scripts\activate      # Dành cho Windows
# source venv/bin/activate   # Dành cho Mac/Linux

# 2. Cài đặt các thư viện cần thiết
pip install -r requirement.txt

# 3. KÍCH HOẠT HỆ THỐNG (Chỉ cần 1 lệnh duy nhất này)
python main.py
```

🎉 **XONG!** Script `main.py` sẽ thực thi các tác vụ:
1. Tự động đánh thức Docker và thiết lập CSDL Postgres (`it_management`).
2. Gõ cửa kiểm tra liên tục đến khi DB sẵn sàng (Health Check).
3. `EXTRACT`: Sinh ngẫu nhiên và kéo Data về lưu thành định dạng `.csv` tại folder `data/raw/`
4. `LOAD`: Quét dọn DB và bơm các data này thẳng vào staging tables.
5. `TRANSFORM`: Thực thi SQL dọn rác và nhào nặn thành các Views hoàn chỉnh (`fct_asset_audit`, `trf_assets`).

---

## 📂 Cấu trúc thư mục (Directory Structure)

```plaintext
DA_PORTFOLIO_PROJECT/
├── data/raw/             # Nơi hệ thống tự động đổ file thô (CSV) sau quá trình Extract
├── scripts/              # Chứa kịch bản xử lý Python
│   ├── extract_*         # Các file bốc/sinh dữ liệu (Tạo kịch bản lỗi Mismatch ID...)
│   ├── load_csv_to_db.py # Xe tải: Nạp file vào Staging Table
│   └── db_data_summary.py# Xuất báo cáo sơ bộ ra console
├── sql/                  # Chứa logic biến đổi dữ liệu (Chạy bên trong CSDL)
│   ├── trf_*.sql         # Lớp làm sạch dữ liệu (Transformation Layer)
│   └── fct_*.sql         # Bảng Fact lưu trữ kết quả kiểm toán (Audit Layer)
├── reports/              # [Tương lai] Trữ file Dashboard (.pbix)
├── .env.example          # Khung xương thiết lập cấu hình môi trường bảo mật
├── docker-compose.yaml   # Cấu hình kiến trúc Hạ tầng Database
├── requirement.txt       # Các công cụ thư viện Python phụ trợ
└── main.py               # 🏆 BỘ ĐIỀU KHIỂN TRUNG TÂM (Orchestrator)
```

---

## 📊 Hướng ra báo cáo (Mảnh ghép cuối cùng)
Sau khi `main.py` báo `TOÀN BỘ QUY TRÌNH ĐÃ HOÀN TẤT`, dữ liệu của bạn đã nằm gọn gàng tươm tất trong Database.
Lúc này cắm **Power BI** trực tiếp vào Data source là `PostgreSQL (localhost:5432)`, lấy thẳng view `fct_asset_audit` để vẽ Dashboard!