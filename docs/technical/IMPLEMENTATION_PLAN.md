# 實施計畫：獨立 Item 表格架構

## ✅ 已完成項目

### 1. **資料庫結構建立** ✅
- 創建 `content_items` 表格（122 筆記錄）
- 創建 `student_item_progress` 表格（95 筆記錄）
- 更新 `student_content_progress` 增加摘要欄位
- 所有資料成功遷移

### 2. **SQLAlchemy 模型** ✅
- 新增 `ContentItem` 模型
- 新增 `StudentItemProgress` 模型
- 建立正確的關聯關係

## 📋 待完成項目

### 3. **API 端點更新** 🚧

#### 3.1 上傳錄音 API (`/api/students/upload-recording`)
需要改為直接使用 `StudentItemProgress`：

```python
# 舊方式（JSONB 陣列）
progress.response_data['recordings'][index] = url

# 新方式（獨立記錄）
item_progress = StudentItemProgress.query.filter_by(
    student_assignment_id=assignment_id,
    content_item_id=item_id
).first()
item_progress.recording_url = url
item_progress.status = 'COMPLETED'
```

#### 3.2 取得活動 API (`/api/students/assignments/{id}/activities`)
需要改為從 `ContentItem` 和 `StudentItemProgress` 讀取：

```python
# 取得所有 items
items = ContentItem.query.filter_by(content_id=content_id).order_by(ContentItem.order_index).all()

# 取得進度
progress_items = StudentItemProgress.query.filter_by(
    student_assignment_id=assignment_id
).all()
```

#### 3.3 AI 評分儲存
直接更新 `StudentItemProgress` 的欄位：

```python
item_progress.accuracy_score = 85.5
item_progress.fluency_score = 78.9
item_progress.pronunciation_score = 90.2
item_progress.ai_feedback = "Great job!"
item_progress.ai_assessed_at = datetime.now()
```

### 4. **前端更新** 🚧

#### 4.1 資料結構調整
前端需要適應新的資料格式：

```typescript
// 舊格式
interface ResponseData {
  recordings: string[];
  answers: string[];
  ai_assessments: AIAssessment[];
}

// 新格式
interface ItemProgress {
  content_item_id: number;
  recording_url: string | null;
  accuracy_score: number | null;
  fluency_score: number | null;
  pronunciation_score: number | null;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
}
```

#### 4.2 API 呼叫更新
- 改用 item_id 而不是 index
- 直接取得個別 item 的進度

### 5. **測試與驗證** 📝

#### 5.1 單元測試
- 測試新的模型關係
- 測試資料完整性約束

#### 5.2 整合測試
- 測試完整的錄音上傳流程
- 測試 AI 評分儲存
- 測試進度統計更新

#### 5.3 E2E 測試
- 從學生登入到完成作業的完整流程

## 🎯 實施步驟

### **第一階段：API 更新（今天）**

1. **更新 upload-recording API**
   - 使用 `StudentItemProgress` 取代 JSONB
   - 自動更新摘要統計

2. **更新 activities API**
   - 從新表格讀取資料
   - 保持回傳格式相容

3. **更新 AI 評分 API**
   - 直接儲存到結構化欄位

### **第二階段：前端調整（明天）**

1. **更新 TypeScript 介面**
2. **調整 API 呼叫邏輯**
3. **確保 UI 正常顯示**

### **第三階段：測試驗證（後天）**

1. **執行所有測試**
2. **手動測試關鍵流程**
3. **效能測試**

## 📊 預期效益

### 效能提升
- **查詢速度提升 3-5 倍**：直接查詢而非 JSONB 解析
- **索引效果更好**：可以對個別欄位建立索引
- **統計更快速**：使用 SQL 聚合函數

### 資料完整性
- **不再有陣列同步問題**
- **外鍵約束保證資料一致性**
- **個別 item 可獨立追蹤**

### 維護性
- **程式碼更清晰**：不需要處理複雜的 JSONB 操作
- **除錯更容易**：可以直接查看個別記錄
- **擴展更方便**：容易增加新欄位或功能

## 🚀 部署計畫

1. **測試環境驗證**（已完成）
2. **Staging 環境部署**（今天）
3. **生產環境部署**（確認無誤後）

## ⚠️ 風險管理

### 資料遷移風險
- ✅ 已備份原始資料
- ✅ 遷移腳本可重複執行
- ✅ 保留原始 JSONB 欄位作為備份

### 相容性風險
- 需要確保前端可以處理新格式
- API 需要向下相容一段時間
- 考慮使用 feature flag 逐步切換

## 📝 檢查清單

- [x] 資料庫 migration 完成
- [x] SQLAlchemy 模型更新
- [x] 資料遷移成功
- [ ] upload-recording API 更新
- [ ] activities API 更新
- [ ] AI 評分 API 更新
- [ ] 前端 TypeScript 更新
- [ ] 前端 API 呼叫更新
- [ ] 單元測試通過
- [ ] 整合測試通過
- [ ] E2E 測試通過
- [ ] 效能測試
- [ ] 文件更新

## 💡 結論

這次重構將徹底解決陣列同步問題，提供更穩定、更高效的系統架構。雖然需要一些工作，但長期收益遠大於短期成本。
