# Content 相關項目完整分析

## 📊 資料庫 Schema 分析

### 🗄️ Content 相關表格

1. **Content** (contents)
   - id, lesson_id, type, title, order_index, is_active
   - **items**: JSON - 需要改為 ContentItem 關聯
   - target_wpm, target_accuracy, time_limit_seconds

2. **ContentItem** (content_items) 🆕
   - id, content_id, order_index, text, translation, audio_url, item_metadata

3. **StudentContentProgress** (student_content_progress)
   - student_assignment_id, content_id, order_index, status
   - **response_data**: JSON - 需要改為 StudentItemProgress 關聯

4. **StudentItemProgress** (student_item_progress) 🆕
   - student_assignment_id, content_item_id
   - recording_url, answer_text, accuracy_score, fluency_score, pronunciation_score

5. **AssignmentContent** (assignment_contents)
   - assignment_id, content_id, order_index

## 🎯 後端 API 需要修改的檔案

### 1. **routers/students.py** 🔴 高優先級
#### 需要修改的 API：
- `POST /api/students/upload-recording` ⚠️ 已修復但需適配新結構
- `GET /api/students/assignments/{assignment_id}/activities` 🔥 重要
- `GET /api/students/assignments/{assignment_id}/submit`

#### 修改重點：
```python
# 舊方式：更新 JSONB
progress.response_data['recordings'][index] = url

# 新方式：更新 StudentItemProgress
item_progress = StudentItemProgress.query.filter_by(
    student_assignment_id=assignment_id,
    content_item_id=item_id
).first()
item_progress.recording_url = url
```

### 2. **routers/teachers.py** 🔴 高優先級
#### 需要修改的 API：
- `POST /api/teachers/contents` - 創建課程內容
- `PUT /api/teachers/contents/{content_id}` - 編輯課程內容
- `GET /api/teachers/assignments/{assignment_id}/progress` - 檢視學生進度
- `POST /api/teachers/assignments/{assignment_id}/grade` - 批改作業

#### 修改重點：
```python
# 創建 Content 時同時創建 ContentItem
for index, item in enumerate(items_data):
    ContentItem(
        content_id=content.id,
        order_index=index,
        text=item['text'],
        translation=item.get('translation')
    ).save()
```

### 3. **routers/assignments.py** 🟡 中優先級
#### 需要修改的 API：
- `POST /api/assignments` - 創建作業時的內容處理
- `GET /api/assignments/{assignment_id}` - 取得作業詳情

### 4. **routers/programs.py** 🟡 中優先級
#### 需要修改的 API：
- `GET /api/programs/{program_id}/lessons/{lesson_id}/contents` - 取得課程內容

### 5. **routers/speech_assessment.py** 🔴 高優先級
#### 需要修改的 API：
- AI 評分結果儲存到 StudentItemProgress

## 🎨 前端需要修改的檔案

### 1. **StudentActivityPage.tsx** 🔴 最重要
#### 修改項目：
- **資料結構調整**：從 response_data 陣列改為 StudentItemProgress 物件
- **API 呼叫**：activities API 回傳格式改變
- **狀態管理**：currentSubQuestionIndex 對應到 content_item_id

#### 關鍵修改：
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
  order_index: number;
  text: string;
  translation: string;
  recording_url: string | null;
  accuracy_score: number | null;
  status: 'NOT_STARTED' | 'IN_PROGRESS' | 'COMPLETED';
}
```

### 2. **AssignmentDetail.tsx** 🟡 中優先級
#### 修改項目：
- 作業詳情顯示邏輯
- 進度統計計算

### 3. **TeacherAssignmentDetailPage.tsx** 🟡 中優先級
#### 修改項目：
- 學生進度檢視
- 批改介面調整

### 4. **utils/api.ts** 🔴 高優先級
#### 修改項目：
- API 介面定義
- 資料型別定義
- 請求/回應格式

## 🧪 TDD 測試腳本合約

### 測試範圍分類：

#### 🔴 **Critical Path Tests** (必須通過)
1. **學生錄音上傳流程**
2. **學生檢視活動進度**
3. **老師檢視學生進度**
4. **AI 評分儲存**

#### 🟡 **Important Tests** (重要功能)
1. **老師創建課程內容**
2. **老師編輯課程內容**
3. **作業指派流程**

#### 🟢 **Nice-to-have Tests** (輔助功能)
1. **統計數據正確性**
2. **資料完整性檢查**

## 📋 實施檢查清單

### **Phase 1: 後端 API 更新**
- [ ] students.py - upload-recording API
- [ ] students.py - activities API
- [ ] teachers.py - progress API
- [ ] teachers.py - content CRUD APIs
- [ ] speech_assessment.py - AI 評分儲存

### **Phase 2: 前端調整**
- [ ] StudentActivityPage.tsx - 主要學習介面
- [ ] api.ts - 型別定義更新
- [ ] TeacherAssignmentDetailPage.tsx - 教師檢視

### **Phase 3: 測試驗證**
- [ ] 單元測試：新模型關係
- [ ] 整合測試：API 端點功能
- [ ] E2E 測試：完整學習流程
- [ ] 效能測試：查詢速度對比

## 🚨 風險評估

### **高風險項目**
1. **StudentActivityPage.tsx** - 主要學習介面，影響學生體驗
2. **upload-recording API** - 核心功能，錄音上傳
3. **activities API** - 資料格式大幅改變

### **中風險項目**
1. **老師檢視介面** - 資料顯示邏輯改變
2. **統計計算** - 從 JSONB 改為 SQL 聚合

### **低風險項目**
1. **課程內容 CRUD** - 邏輯相對簡單
2. **作業指派** - 主要是額外創建記錄

## 💡 建議實施順序

1. **先做後端 API** - 確保資料層穩定
2. **再做前端調整** - 適配新的資料格式
3. **最後做測試** - 驗證所有功能正常

## 🎯 成功標準

### **技術指標**
- [ ] 所有測試通過
- [ ] API 回應時間 < 200ms
- [ ] 資料一致性 100%

### **功能指標**
- [ ] 學生可以正常錄音上傳
- [ ] AI 評分正確對應題目
- [ ] 老師可以檢視詳細進度
- [ ] 不再有陣列同步錯誤
