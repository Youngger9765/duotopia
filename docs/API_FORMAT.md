# API 格式文件

## 🔄 拖拽排序 API

### 課程排序
```http
PUT /api/teachers/programs/reorder
Authorization: Bearer {token}
Content-Type: application/json

[
  {"id": 1, "order_index": 1},
  {"id": 2, "order_index": 2}
]
```

### 單元排序
```http
PUT /api/teachers/programs/{program_id}/lessons/reorder
Authorization: Bearer {token}
Content-Type: application/json

[
  {"id": 1, "order_index": 1},
  {"id": 2, "order_index": 2},
  {"id": 3, "order_index": 3}
]
```

### 重要提醒
- ✅ 使用 `order_index` 欄位（不是 `order`）
- ✅ 資料格式是陣列，不是物件
- ✅ 每個項目包含 `id` 和 `order_index`

## ✅ 班級功能總結

### 完全正常的功能
1. **班級管理** - 100% ✅
   - 班級列表（包含學生資料）
   - 班級詳情
   - 班級內學生數顯示正確

2. **學生管理** - 100% ✅
   - 新增學生
   - 編輯學生
   - 重設密碼（預設為生日）
   - 刪除學生
   - 學生列表顯示

3. **課程管理** - 100% ✅
   - 課程列表（三層結構：課程→單元→內容）
   - 新增課程
   - 編輯課程
   - 刪除課程

4. **拖拽排序** - 100% ✅
   - 課程排序
   - 單元排序

## 📊 測試結果
- 日期：2025-08-29
- 環境：Staging (Supabase)
- 所有班級功能測試通過 ✅
