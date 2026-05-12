# Claude Rules & Playbook

> **LƯU Ý QUAN TRỌNG:** 
> File **`AGENTS.md`** tại thư mục gốc là **Single Source of Truth** cho toàn bộ dự án này. 
> Trước khi thực hiện bất kỳ task nào, bạn **BẮT BUỘC** phải đọc và tuân theo mọi kiến trúc, coding style, và logic nghiệp vụ được định nghĩa trong `AGENTS.md`.

## Hành vi đặc thù cho Claude:
1. Luôn ưu tiên suy nghĩ kỹ càng (Thinking) trước khi propose các thay đổi kiến trúc lớn.
2. Kiểm tra các skills được định nghĩa trong thư mục `.agents/skills/` hoặc `.claude/skills/` nếu task rơi vào các miền kiến thức đặc thù (như Power BI, Refactoring...).
3. Giao tiếp mạch lạc, rõ ràng bằng Tiếng Việt.
