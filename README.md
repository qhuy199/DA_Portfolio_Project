Modern Workspace Deployment Management Project
Dự án này tập trung vào việc quản lý và tối ưu hóa quy trình triển khai không gian làm việc hiện đại (Modern Workspace). Hệ thống sử dụng kiến trúc container hóa để quản lý dữ liệu thiết bị, người dùng và trạng thái triển khai phần mềm (Enrollment) một cách tự động và bảo mật.

🏗️ Hạ tầng kỹ thuật (Infrastructure Stack)
Dự án được đóng gói và vận hành dựa trên các công nghệ cốt lõi:

Docker & Docker Compose: Container hóa toàn bộ môi trường để đảm bảo tính nhất quán từ lúc phát triển đến khi triển khai thực tế.

PostgreSQL: Cơ sở dữ liệu quan hệ mạnh mẽ, đóng vai trò là "Data Warehouse" thu nhỏ để lưu trữ toàn bộ thông tin tài sản và trạng thái workspace.

Python (ETL): Xử lý việc thu thập và đẩy dữ liệu vào kho lưu trữ.

SQL (Transformation Layer): Xây dựng các lớp dữ liệu nghiệp vụ để đối soát và báo cáo.

🛠️ Triển khai hệ thống (Deployment)
1. Khởi tạo Container (Docker + PostgreSQL)
Hệ thống được thiết lập thông qua file 5_docker-compose.yaml. Để khởi động cơ sở dữ liệu, chạy lệnh:

Bash
docker-compose up -d
Lưu ý: Việc này sẽ tự động khởi tạo một instance PostgreSQL sẵn sàng để tiếp nhận dữ liệu.

2. Quy trình dữ liệu (Data Pipeline)
Dự án áp dụng mô hình Modular & Layered Architecture để phân tách rõ ràng các bước:

Collect & Load: Sử dụng Python để đọc dữ liệu từ /data/raw và nạp vào Staging tables trong PostgreSQL.

Transform: Sử dụng SQL Views trong thư mục /sql để chuẩn hóa dữ liệu tài sản (vw_asset_clean) và kiểm tra logic tuân thủ (vw_asset_audit).

Audit: Giám sát sức khỏe dữ liệu thông qua các script summary trực tiếp từ Database.

📂 Cấu trúc thư mục (Best Practice)
Plaintext
DA_PORTFOLIO_PROJECT/
├── data/               # Dữ liệu nguồn CSV (Assets, Employees, Enrollment)
├── sql/                # Logic biến đổi dữ liệu (Clean views, Audit views)
├── scripts/            # Code Python (Load data, Summary report)
├── reports/            # Power BI Dashboard cho Modern Workspace
├── 5_docker-compose.yaml # Cấu hình hạ tầng Docker
├── .gitignore          # Bảo mật thông tin môi trường
└── README.md           # Tài liệu dự án
🎯 Mục tiêu dự án
Quản lý vòng đời thiết bị: Theo dõi từ lúc mua, cấp phát đến lúc thu hồi/thanh lý.

Đối soát Enrollment: Đảm bảo 100% thiết bị thực tế được đăng ký đúng trên hệ thống quản lý tập trung (Intune/Autopilot).

Tối ưu chi phí: Phân tích khấu hao và chi phí bảo trì dựa trên dữ liệu thực tế trong Database.