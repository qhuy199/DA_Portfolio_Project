---
name: powerbi-modeling
description: "Use this skill whenever working with Power BI Desktop via the powerbi-modeling-mcp tool. Triggers: user mentions Power BI, .pbix file, DAX measures, Power BI visuals, semantic model, or asks to create/update/query anything in Power BI. Read this before any powerbi-modeling-mcp tool call."
---

# Power BI Modeling MCP — Agent Playbook

## 0. Luôn đọc skill này trước khi gọi bất kỳ powerbi-modeling-mcp tool nào

---

## 1. Khởi tạo kết nối

Power BI Desktop random assign port mới mỗi lần restart — **không bao giờ hardcode port**.

### Quy trình bắt buộc:

```
Bước 1 → ListLocalInstances   (tìm port hiện tại)
Bước 2 → Connect              (dùng connectionString từ kết quả)
Bước 3 → Lưu connectionName   (dùng cho mọi request tiếp theo)
```

```json
// Bước 1
{ "operation": "ListLocalInstances" }

// Bước 2 — dùng connectionString trả về từ Bước 1
{
  "operation": "Connect",
  "connectionString": "data source=localhost:<port>;Application Name=MCP-PBIModeling"
}

// Response trả về connectionName — lưu lại dùng tiếp
// Ví dụ: "PBIDesktop-Dashboard_FN-6878"
```

### ❌ Các lỗi phổ biến khi Connect:
- Gửi kèm `connectionName` trong request Connect → server từ chối
- Dùng port cũ từ session trước → "connection not found"
- Dùng `DataSource` thay `connectionString` → sai schema

---

## 2. Xử lý lỗi "connection not found"

```
Error: Connection 'PBIDesktop-X-<port>' not found
```

Port đã đổi do Power BI restart. **Không retry với tên cũ.**

```
→ Gọi lại ListLocalInstances
→ Connect với port mới
→ Dùng connectionName mới cho các request tiếp theo
```

---

## 3. Tạo Measures — Deploy theo 2 batch

Power BI validate toàn bộ DAX expressions trong 1 batch **cùng lúc** trước khi commit. Nếu `M2` reference `[M1]` mà `M1` chưa tồn tại trong model → `SemanticError` → rollback cả batch.

### Quy tắc 2-batch:

```
Batch 1 → Tất cả base measures (không reference measure khác)
Batch 2 → Tất cả derived measures (reference measures từ Batch 1)
```

```json
// Batch 1 — Base measures
{
  "operation": "Create",
  "definitions": [
    { "name": "Total Devices", "expression": "COUNTROWS(trf_assets)" },
    { "name": "Active Fleet",  "expression": "COUNTROWS(FILTER(trf_assets, trf_assets[status] = \"In_Use\"))" }
  ]
}

// Batch 2 — Derived measures (chạy sau khi Batch 1 đã committed)
{
  "operation": "Create",
  "definitions": [
    { "name": "Active Fleet %", "expression": "DIVIDE([Active Fleet], [Total Devices])" }
  ]
}
```

> ✅ Code vẫn clean và dễ maintain  
> ✅ Không cần inline logic  
> ✅ Chỉ cần 2 lần gọi API thay vì N lần

---

## 4. Create vs Update — kiểm tra trước khi ghi

Nhầm operation → transaction rollback toàn bộ batch.

```
Measure chưa tồn tại → "Create"
Measure đã tồn tại   → "Update"
```

Nếu không chắc, query kiểm tra trước:

```dax
EVALUATE SELECTCOLUMNS(
    FILTER(INFO.MEASURES(), [Name] = "TênMeasure"),
    "Name", [Name]
)
```

Không có row trả về → measure chưa tồn tại → dùng Create.

---

## 5. Transaction rollback — isolate và fix

Nếu 1 measure lỗi trong batch → **toàn bộ batch rollback**, kể cả những measure đã thành công trước đó.

```
→ Đọc error message xác định measure nào lỗi
→ Tách measure lỗi ra khỏi batch
→ Fix DAX expression
→ Deploy lại toàn bộ batch (các measure thành công trước đó chưa được persist)
```

---

## 6. Calculated Tables (DATATABLE) — bắt buộc Refresh sau Create

Calculated table tạo xong chưa có data cho đến khi refresh. Query ngay sẽ lỗi.

```json
// Bước 1: Create
{
  "operation": "Create",
  "definitions": [{
    "name": "lkp_my_table",
    "daxExpression": "DATATABLE(\"Col1\", STRING, \"Col2\", STRING, {{\"A\", \"B\"}})"
  }]
}

// Bước 2: Refresh ngay — không skip
{
  "operation": "RefreshWithXMLA",
  "references": [{ "name": "lkp_my_table" }]
}
```

> ❌ Query trước Refresh → `table does not hold any data`

---

## 7. Verify sau mỗi thao tác quan trọng

Luôn chạy DAX query để xác nhận kết quả trước khi báo user hoàn thành:

```dax
-- Verify measure đơn
EVALUATE ROW("Result", [TênMeasure])

-- Verify measure với breakdown
EVALUATE
SUMMARIZECOLUMNS(
    TableName[ColumnName],
    "Value", [TênMeasure]
)
```

---

## 8. Filter context và TREATAS

Khi measure cần cross-filter giữa 2 bảng không có relationship, hoặc relationship không propagate đúng chiều:

```dax
-- Dùng TREATAS để ánh xạ filter thủ công
VAR _valid_keys =
    CALCULATETABLE(
        VALUES(TableA[key]),
        TableA[category] = "X"
    )
RETURN
    CALCULATE(
        COUNTROWS(TableB),
        TREATAS(_valid_keys, TableB[key])
    )
```

Nếu visual axis dùng column từ `TableB` mà measure dùng filter từ `TableA`:

```dax
-- Thêm REMOVEFILTERS để thoát filter context của visual axis
CALCULATE(
    COUNTROWS(TableB),
    REMOVEFILTERS(TableB[axis_column]),
    TREATAS(_valid_keys, TableB[key])
)
```

---

## 9. Lookup Action Text — dùng bảng tĩnh thay vì calculated column

Khi cần gán text action theo combination của nhiều cột (ví dụ: join_type × autopilot_profile → recommended action), **không dùng calculated column trên bảng gốc** vì sẽ bị cross-contaminate khi visual filter theo OS hay category khác nhau.

```
✅ Đúng: Tạo DATATABLE lookup riêng + measure SELECTEDVALUE để lookup theo context
❌ Sai:  Calculated column trên bảng gốc → mọi row đều bị gán giá trị dù không relevant
```

```dax
-- Measure lookup pattern
P4 My Action =
VAR _key1 = SELECTEDVALUE(TableB[col1])
VAR _key2 = SELECTEDVALUE(TableB[col2])
RETURN
    CALCULATE(
        SELECTEDVALUE(lkp_table[Recommended_Action]),
        lkp_table[col1] = _key1,
        lkp_table[col2] = _key2
    )
```

---

## 10. Chống Hardcode (Anti-pattern) — Tận dụng Filter Context của Visual

Tuyệt đối **KHÔNG tạo các measure riêng lẻ cho từng giá trị của một Dimension** (ví dụ: `P5 Active Finance`, `P5 Active HR`, `P5 Finance % of Active`, v.v.). Đây là một anti-pattern dẫn đến:
- Phình to Data Model với hàng tá measure thừa thãi.
- Thiếu tính mở rộng (không tự động nhận diện nếu có thêm phòng ban/hạng mục mới).
- Sai lệch khi tính toán tỷ lệ phần trăm (do Filter Context bị ghi đè không đúng cách).

### ✅ Cách làm chuẩn (Best Practice):
1. **Viết 1 measure chung duy nhất** (ví dụ: `[P5 Assigned Assets]`) chỉ làm nhiệm vụ đếm và filter các trạng thái hợp lệ.
2. **Giao việc phân tách cho Visual**: Kéo cột Dimension (ví dụ: `trf_employees[department]`) vào Legend, Axis, hoặc Category của Visual (Bar chart, Donut chart).
3. **Hiển thị % của tổng**: Visual (đặc biệt là Donut/Pie Chart) sẽ tự động tính và hiển thị tỷ lệ % chính xác dựa trên Filter Context mà không cần viết thêm DAX.

```dax
// ✅ CHỈ CẦN 1 MEASURE NÀY
P5 Assigned Assets = 
CALCULATE(
    COUNTROWS(trf_assets), 
    trf_assets[asset_status] IN {"In_Use", "Under_Maintenance"}
)
```

---

## 11. Custom Sorting & Separation of Concerns (DA vs DE)

Khi cần sắp xếp tùy chỉnh (Custom Sort) cho các giá trị Text trên Visual (ví dụ: xếp hạng thiết bị `Laptop` > `Desktop` > `Server` thay vì theo bảng chữ cái Alphabet):

**Tuyệt đối KHÔNG đẩy Presentation Logic (Logic hiển thị) xuống Data Warehouse (Database):**
- Việc thêm cột `sort_order` trực tiếp vào bảng Fact/View ở tầng Database chỉ để phục vụ cách hiển thị của Power BI sẽ làm **dư thừa dữ liệu (Database Bloat)**, đi ngược lại thiết kế Tool-agnostic.
- Vi phạm nguyên tắc **Separation of Concerns**: Data Engineer (DE) cung cấp "Business Truth", còn việc Visualize (bao gồm Custom Sort) là trách nhiệm của Data Analyst (DA) trên tầng BI Tool.

### ✅ Cách làm chuẩn (Best Practice):
Giải quyết trực tiếp trong Power BI bằng cách tạo bảng Dimension tĩnh (Lookup Table) qua DAX `DATATABLE`. Việc này giúp giữ sạch Database và cho phép DA toàn quyền kiểm soát logic hiển thị.

1. Tạo một bảng độc lập lưu thứ tự sắp xếp bằng DAX.
2. Thiết lập Relationship giữa cột `Category` này với Fact table.
3. Dùng tính năng **Sort by Column** trên Power BI để cột `Category` tự động sort theo cột `Sort_Order`.

```dax
// Ví dụ tạo bảng Sort Order nội bộ trong Power BI
dim_device_category = 
DATATABLE (
    "Category", STRING,
    "Sort_Order", INTEGER,
    {
        {"Laptop", 1},
        {"Desktop", 2},
        {"Server", 3},
        {"Network", 4},
        {"IoT", 5}
    }
)

---

## 12. Tính toán tỷ lệ % theo tổng (Share of Total) & Ghi đè Filter Context

Khi tính % tỷ trọng của một thành phần so với tổng (ví dụ: % In_Storage so với tổng Unassigned, hoặc % Assigned theo từng phòng ban), lỗi kinh điển nhất là **chia ra 100% ở mọi dòng** trên biểu đồ. Lỗi này xảy ra do mẫu số không phá vỡ được Filter Context của Visual.

### ❌ Lỗi sai phổ biến (100% Bug):
```dax
-- Mẫu số bị Filter Context của biểu đồ cắt nhỏ (chia ra luôn = 100%)
Total Autopilot = CALCULATE(COUNTROWS(stg_enrollment))
```

### ✅ Cách làm chuẩn (Ghi đè bằng REMOVEFILTERS hoặc IN)
Hàm `CALCULATE` có sức mạnh **ghi đè (override) Filter Context**. Khi cung cấp một điều kiện cụ thể hoặc dùng hàm xóa bộ lọc, nó sẽ tính toán dựa trên tập dữ liệu mới, bỏ qua bộ lọc hiện tại của Visual.

**Trường hợp 1: Tính % trên TOÀN BỘ tập dữ liệu (Dùng REMOVEFILTERS/ALL)**
*Thường dùng khi tính Share of Total của một trạng thái (như Autopilot).*
```dax
-- Tử số (tôn trọng Filter Context của Visual)
Total Count = COUNTROWS(stg_enrollment)

-- Mẫu số (Bỏ qua bộ lọc của trạng thái, giữ nguyên tổng toàn cục)
Total Pool = CALCULATE(COUNTROWS(stg_enrollment), REMOVEFILTERS(stg_enrollment[Autopilot_Status]))

-- Kết quả phép chia %
Share % = DIVIDE([Total Count], [Total Pool])
```

**Trường hợp 2: Tính % trên một NHÓM CỤ THỂ (Dùng IN)**
*Thường dùng khi tập hợp tổng chỉ là một tập con cụ thể (ví dụ: Unassigned Pool chỉ gồm Storage, Lost, Retired).*
Khi truyền toán tử `IN` vào trong `CALCULATE`, DAX ngầm định dùng `ALL()` để ghi đè mọi bộ lọc hiện tại trên cột đó bằng danh sách mới.
```dax
-- Tử số (ví dụ: In_Storage Count)
Count = COUNTROWS(trf_assets)

-- Mẫu số (Ghi đè Filter Context của trạng thái trên visual, thay bằng danh sách tĩnh)
Unassigned Pool = 
CALCULATE(
    COUNTROWS(trf_assets), 
    trf_assets[asset_status] IN {"In_Storage", "Lost", "Retired"}
)
```
```
