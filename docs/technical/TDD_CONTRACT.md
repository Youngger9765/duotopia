# TDD 測試合約 - Content 重構驗證

## 🎯 測試合約目標

**確保所有 Content 相關功能在新架構下正常運作，無功能退化**

## 📋 核心測試合約

### 🔴 **Contract 1: 學生錄音上傳** (Critical)
```python
def test_student_recording_upload_contract():
    """
    合約：學生上傳錄音後，資料正確儲存到新結構
    """
    # Given: 學生有一個作業，包含3題
    assignment = create_test_assignment_with_3_items()
    student = create_test_student()

    # When: 學生上傳第2題的錄音
    response = upload_recording(
        student_id=student.id,
        assignment_id=assignment.id,
        item_index=1,  # 第2題
        audio_file="test_audio.webm"
    )

    # Then:
    assert response.status_code == 200

    # 1. StudentItemProgress 正確更新
    item_progress = get_student_item_progress(
        student_assignment_id=assignment.id,
        item_index=1
    )
    assert item_progress.recording_url is not None
    assert item_progress.status == 'COMPLETED'

    # 2. 其他題目不受影響
    item_0 = get_student_item_progress(student_assignment_id=assignment.id, item_index=0)
    item_2 = get_student_item_progress(student_assignment_id=assignment.id, item_index=2)
    assert item_0.recording_url is None
    assert item_2.recording_url is None

    # 3. 摘要統計自動更新
    summary = get_content_progress_summary(assignment.id)
    assert summary.completed_items == 1
    assert summary.completion_rate == 33.33
```

### 🔴 **Contract 2: 學生檢視活動** (Critical)
```python
def test_student_activities_view_contract():
    """
    合約：學生檢視活動時，看到正確的題目和進度
    """
    # Given: 學生已完成第1題，第2題進行中
    assignment = create_assignment_with_progress()

    # When: 學生檢視活動
    response = get_student_activities(assignment.id)

    # Then:
    assert response.status_code == 200
    activities = response.json()

    # 1. 題目內容正確顯示
    assert len(activities) == 2  # 2個 Content
    content1 = activities[0]
    assert len(content1['items']) == 3  # 第1個 Content 有3題

    # 2. 進度狀態正確
    item1 = content1['items'][0]
    assert item1['status'] == 'COMPLETED'
    assert item1['recording_url'] is not None

    item2 = content1['items'][1]
    assert item2['status'] == 'IN_PROGRESS'

    # 3. AI 評分正確對應
    assert item1['accuracy_score'] == 85.5
    assert item1['fluency_score'] == 78.9
```

### 🔴 **Contract 3: AI 評分儲存** (Critical)
```python
def test_ai_assessment_storage_contract():
    """
    合約：AI 評分正確儲存到對應的題目
    """
    # Given: 學生已上傳第3題錄音
    item_progress = create_recorded_item_progress(item_index=2)

    # When: AI 評分系統評分
    ai_result = {
        'accuracy_score': 92.5,
        'fluency_score': 88.3,
        'pronunciation_score': 95.1,
        'feedback': 'Excellent pronunciation!'
    }

    response = save_ai_assessment(
        student_assignment_id=item_progress.student_assignment_id,
        content_item_id=item_progress.content_item_id,
        assessment=ai_result
    )

    # Then:
    assert response.status_code == 200

    # 1. 評分正確儲存
    updated_progress = get_student_item_progress(item_progress.id)
    assert updated_progress.accuracy_score == 92.5
    assert updated_progress.fluency_score == 88.3
    assert updated_progress.pronunciation_score == 95.1
    assert updated_progress.ai_feedback == 'Excellent pronunciation!'

    # 2. 時間戳記更新
    assert updated_progress.ai_assessed_at is not None

    # 3. 摘要統計更新
    summary = get_content_progress_summary(item_progress.student_assignment_id)
    assert summary.average_accuracy is not None
```

### 🟡 **Contract 4: 老師檢視進度** (Important)
```python
def test_teacher_progress_view_contract():
    """
    合約：老師可以檢視每個學生每題的詳細進度
    """
    # Given: 3個學生完成不同進度的作業
    assignment = create_assignment_with_multiple_students()

    # When: 老師檢視作業進度
    response = get_assignment_progress(assignment.id)

    # Then:
    assert response.status_code == 200
    progress_data = response.json()

    # 1. 可以看到每個學生的進度
    assert len(progress_data['students']) == 3

    # 2. 可以看到每題的完成情況
    student1 = progress_data['students'][0]
    assert 'item_progress' in student1
    assert len(student1['item_progress']) > 0

    # 3. 統計數據正確
    stats = progress_data['statistics']
    assert 'completion_rate' in stats
    assert 'average_score' in stats
```

### 🟡 **Contract 5: 老師創建內容** (Important)
```python
def test_teacher_content_creation_contract():
    """
    合約：老師創建課程內容時，自動創建 ContentItem
    """
    # Given: 老師要創建包含5題的朗讀練習
    content_data = {
        'title': 'Daily Greetings',
        'type': 'pronunciation',
        'items': [
            {'text': 'Good morning', 'translation': '早安'},
            {'text': 'Good afternoon', 'translation': '午安'},
            {'text': 'Good evening', 'translation': '晚安'},
            {'text': 'Good night', 'translation': '晚安'},
            {'text': 'Have a nice day', 'translation': '祝你有美好的一天'}
        ]
    }

    # When: 老師創建內容
    response = create_content(content_data)

    # Then:
    assert response.status_code == 201
    content_id = response.json()['id']

    # 1. Content 記錄創建
    content = get_content(content_id)
    assert content.title == 'Daily Greetings'

    # 2. ContentItem 記錄自動創建
    items = get_content_items(content_id)
    assert len(items) == 5

    # 3. 順序正確
    for i, item in enumerate(items):
        assert item.order_index == i
        assert item.text == content_data['items'][i]['text']
```

## 🧪 TDD 實作腳本

### 測試檔案結構
```
tests/
├── integration/
│   ├── test_content_migration_contract.py     # 主要合約測試
│   ├── test_student_workflow_contract.py      # 學生流程測試
│   ├── test_teacher_workflow_contract.py      # 老師流程測試
│   └── test_api_compatibility_contract.py     # API 相容性測試
├── unit/
│   ├── test_content_item_model.py            # ContentItem 模型測試
│   ├── test_student_item_progress_model.py   # StudentItemProgress 模型測試
│   └── test_content_relationships.py         # 關聯測試
└── e2e/
    └── test_complete_learning_flow.py         # 端到端測試
```

## 📊 測試覆蓋率要求

### **必須達到的覆蓋率**
- **API 端點**: 100% (所有 Content 相關 API)
- **資料模型**: 100% (ContentItem, StudentItemProgress)
- **核心業務邏輯**: 95%
- **前端組件**: 85% (StudentActivityPage, TeacherAssignmentDetailPage)

### **測試環境要求**
- **測試資料庫**: 獨立的測試環境
- **Mock 服務**: AI 評分服務、檔案上傳服務
- **並行測試**: 支援多執行緒測試

## 🎯 驗收標準

### **功能性測試** ✅
- [ ] 所有 TDD 合約測試通過
- [ ] 無功能退化
- [ ] 新功能正常運作

### **效能測試** 📈
- [ ] API 回應時間 < 舊版本
- [ ] 資料庫查詢效能提升
- [ ] 記憶體使用量合理

### **穩定性測試** 🛡️
- [ ] 壓力測試通過
- [ ] 資料一致性檢查
- [ ] 錯誤處理測試

## 🚀 執行計畫

### **Phase 1: TDD 測試撰寫** (2 天)
1. 撰寫所有合約測試（先寫測試，確保會失敗）
2. 建立測試環境和 Mock 服務
3. 確認測試覆蓋率達標

### **Phase 2: 實作開發** (3 天)
1. 後端 API 重構
2. 前端介面調整
3. 逐一讓測試通過

### **Phase 3: 驗證測試** (1 天)
1. 所有測試通過
2. 效能測試驗證
3. 手動測試確認

## 📝 測試執行指令

```bash
# 執行所有 Content 相關測試
npm run test:content

# 執行合約測試
npm run test:contracts

# 執行覆蓋率測試
npm run test:coverage

# 執行效能測試
npm run test:performance
```

## 🔍 測試報告格式

每個測試完成後需要產生：
1. **功能測試報告** - 所有合約是否通過
2. **效能對比報告** - 新舊版本效能差異
3. **覆蓋率報告** - 程式碼覆蓋率統計
4. **問題清單** - 發現的 Bug 和待修復項目

---

**這份 TDD 合約將確保重構過程中不會破壞現有功能，並驗證新架構的正確性。**
