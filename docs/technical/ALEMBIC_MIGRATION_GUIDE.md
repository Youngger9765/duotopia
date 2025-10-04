# Alembic Migration 指南

## 🎯 Migration 策略

我們採用**漸進式遷移**策略，確保資料安全和系統穩定：

### 📋 Migration 順序

#### 1️⃣ **建立新表格** ✅
```bash
# Migration: 20250917_1151_3419c62b5255
alembic revision -m "add_content_item_and_student_item_progress_tables"
```

**建立項目：**
- `content_items` 表
- `student_item_progress` 表
- 新增摘要統計欄位到 `student_content_progress`
- 建立索引和外鍵約束
- 建立觸發器

#### 2️⃣ **資料遷移** 📊
```bash
# 執行資料遷移腳本（在 Alembic migration 後）
python scripts/migrate_content_data.py
```

**遷移內容：**
- `Content.items` → `ContentItem` 記錄
- `StudentContentProgress.response_data` → `StudentItemProgress` 記錄
- 更新摘要統計

#### 3️⃣ **標記舊欄位為棄用** ⚠️
```bash
# Migration: 20250917_1154_71a9b9a902fc
alembic revision -m "deprecate_old_jsonb_columns_in_content_and_progress"
```

**標記項目：**
- 為 `contents.items` 加入 DEPRECATED 註解
- 為 `student_content_progress.response_data` 加入 DEPRECATED 註解

#### 4️⃣ **更新程式碼** 🔧
- 修改 API 使用新表格
- 更新前端處理新資料格式
- 完整測試

#### 5️⃣ **最終清理** (未來)
```bash
# 等確認系統穩定後，再建立最終清理 migration
alembic revision -m "remove_deprecated_jsonb_columns"
```

## 🚀 執行步驟

### **第一階段：建立新結構**

1. **執行 Schema Migration**
   ```bash
   alembic upgrade head
   ```

2. **執行資料遷移**
   ```bash
   python scripts/migrate_content_data.py
   ```

3. **驗證遷移結果**
   ```sql
   -- 檢查新表格記錄數
   SELECT COUNT(*) FROM content_items;
   SELECT COUNT(*) FROM student_item_progress;

   -- 檢查摘要統計
   SELECT completion_rate, total_items, completed_items
   FROM student_content_progress
   WHERE total_items > 0;
   ```

### **第二階段：程式碼更新**

1. **後端 API 更新**
   - 修改所有使用 `Content.items` 的地方
   - 修改所有使用 `response_data` 的地方

2. **前端介面更新**
   - 調整資料結構處理
   - 更新 API 呼叫

3. **測試驗證**
   - 執行所有測試
   - 手動驗證功能

### **第三階段：清理 (未來)**

等確認新系統運作 1-2 週無問題後：

```sql
-- 最終清理 migration (暫不執行)
ALTER TABLE contents DROP COLUMN items;
ALTER TABLE student_content_progress DROP COLUMN response_data;
```

## ⚠️ 注意事項

### **資料安全**
- ✅ 舊欄位保留作為備份
- ✅ 可以隨時回滾到舊系統
- ✅ 新舊系統可以並行運作

### **測試要求**
- ✅ 所有 migration 都有 downgrade 方法
- ✅ 資料遷移腳本可重複執行
- ✅ 完整的測試覆蓋

### **效能考量**
- ✅ 所有新表格都有適當索引
- ✅ 外鍵約束確保資料完整性
- ✅ 觸發器自動維護時間戳記

## 🔄 回滾計畫

如果需要回滾：

```bash
# 回滾到舊 schema
alembic downgrade 11560478a023

# 程式碼也需要回到舊版本
git revert <commit-hash>
```

## 📊 監控指標

### **Migration 完成後檢查：**
- [ ] 新表格記錄數正確
- [ ] 舊資料完整保留
- [ ] 摘要統計計算正確
- [ ] 所有索引建立成功
- [ ] 外鍵約束運作正常

### **程式碼更新後檢查：**
- [ ] API 回應正常
- [ ] 前端顯示正確
- [ ] 錄音上傳功能正常
- [ ] AI 評分儲存正確
- [ ] 效能沒有退化

## 💡 最佳實務

1. **分階段執行** - 不要一次改太多
2. **保留備份** - 舊欄位先不刪除
3. **充分測試** - 每個階段都要測試
4. **監控效能** - 確保沒有退化
5. **文件記錄** - 記錄所有變更

這樣的 migration 策略確保了系統的穩定性和資料的安全性。
