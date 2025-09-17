# 新架構多出來的部分

## 📊 簡單對比

### 原本（JSONB 方式）
```
只有 3 個表：
├── Assignment
├── StudentAssignment
└── StudentContentProgress
    └── response_data: JSONB 大雜燴
        ├── recordings: ["url1", "url2", "url3"]
        ├── answers: ["ans1", "ans2", "ans3"]
        └── ai_assessments: [{...}, {...}, {...}]
```

### 現在（獨立表格方式）
```
有 5 個表：
├── Assignment
├── StudentAssignment
├── StudentContentProgress（保留作為摘要）
├── 🆕 ContentItem（題目表）
└── 🆕 StudentItemProgress（每題進度表）
```

## 🆕 具體多出來什麼？

### 1. ContentItem 表（題目表）
**作用**：把原本的 `Content.items` JSONB 陣列拆開

**原本**：
```json
Content.items = [
  {"text": "I am happy", "translation": "我很開心"},
  {"text": "You are sad", "translation": "你很難過"},
  {"text": "He is tall", "translation": "他很高"}
]
```

**現在**：
```sql
ContentItem 表：
┌────┬────────────┬─────────────┬─────────────┬──────────────┐
│ id │ content_id │ order_index │ text        │ translation  │
├────┼────────────┼─────────────┼─────────────┼──────────────┤
│ 1  │ 23         │ 0           │ I am happy  │ 我很開心     │
│ 2  │ 23         │ 1           │ You are sad │ 你很難過     │
│ 3  │ 23         │ 2           │ He is tall  │ 他很高       │
└────┴────────────┴─────────────┴─────────────┴──────────────┘
```

### 2. StudentItemProgress 表（每題進度表）
**作用**：把原本的 `response_data` JSONB 拆開

**原本**：
```json
response_data = {
  "recordings": ["", "audio2.webm", "audio3.webm"],
  "ai_assessments": [null, {"accuracy": 85}, {"accuracy": 90}]
}
```

**現在**：
```sql
StudentItemProgress 表：
┌────┬─────────────────────┬─────────────────┬─────────────────┬────────────────┐
│ id │ student_assignment  │ content_item_id │ recording_url   │ accuracy_score │
├────┼─────────────────────┼─────────────────┼─────────────────┼────────────────┤
│ 1  │ 365                 │ 1               │ NULL            │ NULL           │
│ 2  │ 365                 │ 2               │ audio2.webm     │ 85.00          │
│ 3  │ 365                 │ 3               │ audio3.webm     │ 90.00          │
└────┴─────────────────────┴─────────────────┴─────────────────┴────────────────┘
```

## 🔗 新增的關聯

### 1. ContentItem → Content
```
ContentItem.content_id → Content.id
（每個題目知道自己屬於哪個內容組）
```

### 2. StudentItemProgress → ContentItem
```
StudentItemProgress.content_item_id → ContentItem.id
（每個進度知道自己對應哪一題）
```

## 💡 核心概念

**就是把「陣列」變「表格」：**

| 原本 | 現在 |
|------|------|
| JSONB 陣列（無約束） | 資料表（有外鍵約束） |
| 手動管理索引 | 資料庫自動管理 ID |
| 容易錯位 | 不可能錯位 |
| 難以查詢 | 容易查詢 |

## 🎯 實際大小

- **ContentItem**：122 筆記錄（原本是 25 個 Content，每個平均 5 題）
- **StudentItemProgress**：95 筆記錄（學生已經答題的記錄）

**總結：多了 2 個表，但解決了陣列同步的根本問題！**
