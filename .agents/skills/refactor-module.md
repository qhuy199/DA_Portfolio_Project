---
name: refactor-module
description: "Sử dụng skill này khi cần tái cấu trúc (refactor) một module Python hoặc SQL view. Kích hoạt khi user yêu cầu tối ưu hóa, clean code, hoặc tách nhỏ functions."
---

# Tái Cấu Trúc (Refactoring) Playbook

## 1. Nguyên Tắc Cốt Lõi
- **Không làm thay đổi behavior:** Trước khi refactor, hãy đảm bảo hiểu rõ Input và Output của module hiện tại. Output cuối cùng phải giữ nguyên.
- **Từng bước nhỏ (Baby steps):** Không refactor toàn bộ file hàng trăm dòng trong một lần. Cắt nhỏ thành từng function/block.

## 2. Python Refactoring
- Ưu tiên sử dụng `List Comprehensions` hoặc các tính năng built-in của Pandas/Numpy thay vì vòng lặp `for` nếu xử lý dữ liệu lớn.
- Tách biệt logic xử lý dữ liệu (Data transformation) và logic I/O (Đọc/Ghi file hoặc kết nối DB).

## 3. SQL Refactoring
- Tách các subqueries phức tạp thành `CTEs` (Common Table Expressions) để dễ đọc và dễ debug.
- Luôn giữ lại comment giải thích logic nghiệp vụ (nếu có) từ file cũ sang file mới.

## 4. Xác nhận sau Refactoring
- Thực thi script/query vừa được refactor để đảm bảo không có lỗi cú pháp.
- Đối chiếu số lượng records (count) hoặc sample data trước và sau khi refactor.
