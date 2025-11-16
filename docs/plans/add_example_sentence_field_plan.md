# 新增「例句」欄位開發計畫

> **需求**: 在 ContentItem 中新增一個選填的「例句」欄位，用於輸入包含該單字的範例句子
> **建立日期**: 2025-11-10
> **優先級**: Medium
> **預估工時**: 4-6 小時

---

## 📋 目錄

- [1. 需求分析](#1-需求分析)
- [2. 資料庫變更](#2-資料庫變更)
- [3. 後端 API 變更](#3-後端-api-變更)
- [4. 前端 UI/UX 變更](#4-前端-uiux-變更)
- [5. 測試計畫](#5-測試計畫)
- [6. 部署計畫](#6-部署計畫)
- [7. 風險評估](#7-風險評估)
- [8. 時程規劃](#8-時程規劃)

---

## 1. 需求分析

### 1.1 功能需求

**核心需求**:
- 每個 ContentItem 可以有一個選填的「例句」欄位
- 例句應該是包含該單字的完整句子
- 例句需要支援儲存、編輯、刪除

**擴展需求（已確認）**:
- [x] 例句需要翻譯（中文翻譯 + 英文釋義）
- [ ] 例句**不需要**音檔
- [ ] 先以單個例句實作（之後考慮支援多個例句）
- [ ] AI 自動生成例句（待討論實作方式）

### 1.2 使用場景

**場景 1: 教師新增單字時輸入例句**
```
單字: "put"
翻譯: "放置"
例句: "Put it away." ← 新增欄位
```

**場景 2: 批次貼上時包含例句**
```
put
Put it away.
It's time to put everything away.
---
get
Get the book from the shelf.
```

**場景 3: 學生查看單字時看到例句**
```
單字: put
翻譯: 放置
例句: Put it away.
      放好它。（如果有例句翻譯）
```

### 1.3 設計決策

#### ✅ **Phase 1 (MVP - 立即實作)**: 例句翻譯功能
- 新增 `example_sentence` 欄位（選填，英文例句，**教師手動輸入**）
- 新增 `example_sentence_translation` 欄位（例句的中文翻譯，**AI 自動翻譯**）
- 新增 `example_sentence_definition` 欄位（例句的英文釋義，**AI 自動翻譯**）
- 支援手動輸入例句
- 支援 AI 自動生成例句翻譯（使用現有 `translateText` API，成本極低）
- 支援批次生成翻譯（使用現有 `batchTranslate` API）
- **不包含**例句音檔
- **不包含** AI 自動生成例句（Phase 2 功能）
- 前端 UI 顯示為簡單的 input/textarea
- 單個例句設計

**成本**: 約 $0.000002/次翻譯（極低）

---

#### 🔄 **Phase 2 (待團隊決策)**: AI 自動生成例句功能

**核心功能**:
- **AI 自動生成例句**（根據單字自動創建合適的例句）
- 教師只需輸入單字，AI 自動產生例句 + 翻譯
- 批次生成例句（大幅提升效率）

**成本**: 約 $0.00006/次生成（約為翻譯的 30 倍，但絕對成本仍很低）

**待討論項目**:
- [ ] 成本接受度（每月預估 $1-3，50 位教師使用情境）
- [ ] 是否需要使用限制（每日/每月上限）
- [ ] 是否預設開啟或由教師手動啟用

**詳細設計請參考**: [附錄 A - Phase 2 完整功能設計](#附錄-a-phase-2-完整功能設計)

---

#### 🚫 **Phase 3 (暫不考慮)**:
- 支援多個例句（資料結構改為一對多關係）
- 例句音檔（TTS 或教師錄音）

---

## 2. 資料庫變更

### 2.1 Schema 變更

**檔案**: `backend/models.py`

**修改 ContentItem 模型**:
```python
class ContentItem(Base):
    """Individual question/item within a Content"""

    __tablename__ = "content_items"

    id = Column(Integer, primary_key=True, index=True)
    content_id = Column(Integer, ForeignKey("contents.id", ondelete="CASCADE"))
    order_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    translation = Column(Text)
    audio_url = Column(Text)

    # ✨ 新增欄位（例句相關）
    example_sentence = Column(Text, nullable=True)              # 例句（英文，選填）
    example_sentence_translation = Column(Text, nullable=True)  # 例句中文翻譯（選填）
    example_sentence_definition = Column(Text, nullable=True)   # 例句英文釋義（選填）

    item_metadata = Column(JSON, default={})
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

### 2.2 Database Migration

**步驟**:
1. 建立 Alembic migration 檔案
2. 新增 `example_sentence` 欄位（Text, nullable=True）
3. 測試 migration（先在開發環境）
4. 準備 rollback script

**Migration Script**:
```bash
# 1. 生成 migration
cd backend
alembic revision --autogenerate -m "add_example_sentence_to_content_items"

# 2. 檢查生成的 migration 檔案
# 檔案位置: backend/alembic/versions/xxxx_add_example_sentence_to_content_items.py

# 3. 執行 migration (開發環境)
alembic upgrade head

# 4. 如需回滾
alembic downgrade -1
```

**Migration 檔案內容範例**:
```python
def upgrade():
    op.add_column(
        'content_items',
        sa.Column('example_sentence', sa.Text(), nullable=True)
    )

def downgrade():
    op.drop_column('content_items', 'example_sentence')
```

### 2.3 資料驗證

**檢查項目**:
- [ ] 欄位類型正確（Text, nullable=True）
- [ ] 現有資料不受影響（所有現有 row 的 `example_sentence` 預設為 NULL）
- [ ] 索引優化（是否需要對 `example_sentence` 建立索引？目前不需要）

---

## 3. 後端 API 變更

### 3.1 Pydantic Schema 更新

**檔案**: `backend/schemas.py` (或相關的 schema 定義檔案)

**修改項目**:

```python
# ContentItem Schema (用於 API response)
class ContentItemResponse(BaseModel):
    id: int
    content_id: int
    order_index: int
    text: str
    translation: Optional[str] = None
    audio_url: Optional[str] = None
    example_sentence: Optional[str] = None  # ✨ 新增
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ContentItem Create Schema (用於創建)
class ContentItemCreate(BaseModel):
    text: str
    translation: Optional[str] = None
    audio_url: Optional[str] = None
    example_sentence: Optional[str] = None  # ✨ 新增
    order_index: int = 0

# ContentItem Update Schema (用於更新)
class ContentItemUpdate(BaseModel):
    text: Optional[str] = None
    translation: Optional[str] = None
    audio_url: Optional[str] = None
    example_sentence: Optional[str] = None  # ✨ 新增
    order_index: Optional[int] = None
```

### 3.2 API 端點變更

**影響的端點**:
- `POST /api/contents` - 創建內容（包含 items）
- `PUT /api/contents/{id}` - 更新內容
- `PATCH /api/contents/{id}` - 部分更新
- `GET /api/contents/{id}` - 取得內容詳情

**變更重點**:
- 所有 CRUD 操作都需要支援 `example_sentence` 欄位
- 確保向後相容性（沒有 `example_sentence` 時不應報錯）

**程式碼位置**:
- `backend/routers/contents.py`
- `backend/routers/teachers.py` (如果有 teacher-specific 的內容創建 API)

### 3.3 CRUD 操作更新

**檔案**: `backend/crud.py` 或相關的 CRUD 函數

**更新項目**:
```python
def create_content_item(db: Session, content_id: int, item_data: dict) -> ContentItem:
    content_item = ContentItem(
        content_id=content_id,
        text=item_data.get("text"),
        translation=item_data.get("translation"),
        audio_url=item_data.get("audio_url"),
        example_sentence=item_data.get("example_sentence"),  # ✨ 新增
        order_index=item_data.get("order_index", 0),
    )
    db.add(content_item)
    db.commit()
    db.refresh(content_item)
    return content_item

def update_content_item(db: Session, item_id: int, item_data: dict) -> ContentItem:
    item = db.query(ContentItem).filter(ContentItem.id == item_id).first()
    if item:
        if "text" in item_data:
            item.text = item_data["text"]
        if "translation" in item_data:
            item.translation = item_data["translation"]
        if "audio_url" in item_data:
            item.audio_url = item_data["audio_url"]
        if "example_sentence" in item_data:  # ✨ 新增
            item.example_sentence = item_data["example_sentence"]
        db.commit()
        db.refresh(item)
    return item
```

### 3.4 API 測試

**測試案例**:
```python
# tests/integration/api/test_content_items.py

def test_create_content_item_with_example_sentence():
    """測試創建包含例句的內容項目"""
    payload = {
        "text": "put",
        "translation": "放置",
        "example_sentence": "Put it away."
    }
    response = client.post("/api/contents/1/items", json=payload)
    assert response.status_code == 201
    assert response.json()["example_sentence"] == "Put it away."

def test_create_content_item_without_example_sentence():
    """測試創建不包含例句的內容項目（向後相容）"""
    payload = {
        "text": "get",
        "translation": "取得"
    }
    response = client.post("/api/contents/1/items", json=payload)
    assert response.status_code == 201
    assert response.json()["example_sentence"] is None

def test_update_example_sentence():
    """測試更新例句"""
    payload = {"example_sentence": "Get the book from the shelf."}
    response = client.patch("/api/contents/1/items/1", json=payload)
    assert response.status_code == 200
    assert response.json()["example_sentence"] == "Get the book from the shelf."

def test_delete_example_sentence():
    """測試刪除例句（設為 null）"""
    payload = {"example_sentence": None}
    response = client.patch("/api/contents/1/items/1", json=payload)
    assert response.status_code == 200
    assert response.json()["example_sentence"] is None
```

---

## 4. 前端 UI/UX 變更

### 4.1 TypeScript Interface 更新

**檔案**: `frontend/src/components/ReadingAssessmentPanel.tsx`

**修改 ContentRow interface**:
```typescript
interface ContentRow {
  id: string | number
  text: string                            // 單字/句子
  definition: string                      // 中文翻譯
  translation: string                     // 英文釋義
  example_sentence?: string               // ✨ 新增：例句（選填）
  audioUrl?: string
  audio_url?: string
  selectedLanguage?: "chinese" | "english"
  audioSettings?: {
    accent: string
    gender: string
    speed: string
  }
}
```

**檔案**: `frontend/src/types/index.ts`

**更新全域類型定義**:
```typescript
export interface ContentItem {
  id: number
  text: string
  translation?: string
  audio_url?: string
  example_sentence?: string  // ✨ 新增
  order_index: number
}
```

### 4.2 UI 設計方案

#### **方案 A: 簡單輸入框（推薦 MVP）**

**位置**: 在翻譯欄位下方新增一個輸入框

**UI 設計**:
```
┌─────────────────────────────────────────────────────┐
│ 1. [拖曳] put                      [🎙️] [🗑️]        │
│                                                      │
│    ┌──────────────────────────────────────────┐    │
│    │ put                                       │    │ ← 單字輸入框
│    └──────────────────────────────────────────┘    │
│                                                      │
│    ┌──────────────────────────────────────────┐    │
│    │ 放置                          [中文翻譯 ▼]│    │ ← 翻譯輸入框
│    └──────────────────────────────────────────┘    │
│                                                      │
│    ┌──────────────────────────────────────────┐    │
│    │ Put it away.                    [例句 📝]│    │ ← ✨ 新增：例句
│    └──────────────────────────────────────────┘    │
│                                                      │
│    [📋 複製] [🗑️ 刪除]                              │
└─────────────────────────────────────────────────────┘
```

**優點**:
- 簡單直觀
- 不增加 UI 複雜度
- 開發成本低

**缺點**:
- 如果例句很長，單行輸入框不夠用

---

#### **方案 B: 可展開區塊（未來擴展用）**

**UI 設計**:
```
┌─────────────────────────────────────────────────────┐
│ 1. [拖曳] put                      [🎙️] [🗑️]        │
│                                                      │
│    單字: put                                         │
│    翻譯: 放置                                        │
│                                                      │
│    ┌─ 📝 例句 ─────────────────────────── [▼]     │ ← 可摺疊
│    │                                                │
│    │  ┌────────────────────────────────────┐      │
│    │  │ Put it away.                        │      │
│    │  └────────────────────────────────────┘      │
│    │                                                │
│    │  中文: 放好它。                               │
│    │  [🎙️ 音檔]                                    │
│    └────────────────────────────────────────────  │
│                                                      │
│    [📋 複製] [🗑️ 刪除]                              │
└─────────────────────────────────────────────────────┘
```

**優點**:
- 未來可擴展（例句翻譯、音檔）
- 保持主介面簡潔

**缺點**:
- 開發成本較高
- 對於簡單需求來說過度設計

---

### 4.3 前端實作清單

#### **4.3.1 ReadingAssessmentPanel 更新**

**檔案**: `frontend/src/components/ReadingAssessmentPanel.tsx`

**修改項目**:

1. **更新 ContentRow interface** (已在 4.1 說明)

2. **更新 SortableRowInner 元件** (約 Line 803-993):
   ```typescript
   // 在翻譯 textarea 下方新增例句輸入框
   <div className="space-y-2">
     {/* 現有的翻譯 textarea */}
     <div className="relative">
       <textarea
         value={...}
         onChange={...}
         placeholder="中文翻譯 / English definition"
       />
     </div>

     {/* ✨ 新增：例句輸入框 */}
     <div className="relative">
       <input
         type="text"
         value={row.example_sentence || ""}
         onChange={(e) => handleUpdateRow(index, "example_sentence", e.target.value)}
         className="w-full px-3 py-2 border rounded-md text-sm"
         placeholder="例句 (optional)"
         maxLength={300}
       />
       <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-400">
         📝 Example
       </span>
     </div>
   </div>
   ```

3. **更新 handleUpdateRow 函數** (約 Line 1194):
   - 確保支援 `example_sentence` 欄位更新

4. **更新 useEffect（同步到父元件）** (約 Line 1119):
   ```typescript
   useEffect(() => {
     if (!onUpdateContent) return;

     const items = rows.map((row) => ({
       text: row.text,
       definition: row.definition,
       translation: row.translation,
       audio_url: row.audioUrl,
       example_sentence: row.example_sentence,  // ✨ 新增
       selectedLanguage: row.selectedLanguage,
     }));

     onUpdateContent({
       ...editingContent,
       title,
       items,
     });
   }, [rows, title]);
   ```

5. **更新 loadContentData** (約 Line 1067):
   ```typescript
   const loadContentData = async () => {
     // ...
     const convertedRows = data.items.map((item, index) => ({
       id: (index + 1).toString(),
       text: item.text || "",
       definition: item.definition || "",
       translation: item.english_definition || "",
       audioUrl: item.audio_url || "",
       example_sentence: item.example_sentence || "",  // ✨ 新增
       selectedLanguage: item.selectedLanguage || "chinese",
     }));
     setRows(convertedRows);
   };
   ```

6. **更新批次貼上功能** (約 Line 1581):
   - 決定是否支援批次貼上時包含例句
   - 格式可能是：
     ```
     put|放置|Put it away.
     get|取得|Get the book.
     ```

#### **4.3.2 StudentActivityPageContent 更新**

**檔案**: `frontend/src/pages/student/StudentActivityPageContent.tsx`

**修改項目**:
- 更新 `Activity` 和 `ActivityItem` interface，新增 `example_sentence` 欄位
- 顯示例句給學生查看

#### **4.3.3 GroupedQuestionsTemplate 更新**

**檔案**: `frontend/src/components/activities/GroupedQuestionsTemplate.tsx`

**修改項目**:
- 在題目顯示區域新增例句顯示
- UI 設計：
  ```tsx
  <div className="question">
    <h3 className="text-lg font-bold">{item.text}</h3>
    <p className="text-gray-600">{item.translation}</p>

    {/* ✨ 新增：例句顯示 */}
    {item.example_sentence && (
      <div className="mt-2 p-2 bg-blue-50 rounded border-l-4 border-blue-400">
        <span className="text-xs text-blue-600 font-medium">例句</span>
        <p className="text-sm text-gray-700 italic">
          {item.example_sentence}
        </p>
      </div>
    )}
  </div>
  ```

### 4.4 前端測試計畫

**測試案例**:

```typescript
// frontend/src/components/__tests__/ReadingAssessmentPanel.test.tsx

describe('ReadingAssessmentPanel - Example Sentence', () => {
  it('應該顯示例句輸入框', () => {
    render(<ReadingAssessmentPanel />)
    const exampleInputs = screen.getAllByPlaceholderText(/例句/)
    expect(exampleInputs.length).toBeGreaterThan(0)
  })

  it('應該能夠輸入例句', () => {
    render(<ReadingAssessmentPanel />)
    const exampleInput = screen.getAllByPlaceholderText(/例句/)[0]

    fireEvent.change(exampleInput, { target: { value: 'Put it away.' } })

    expect(exampleInput.value).toBe('Put it away.')
  })

  it('應該能夠清空例句', () => {
    render(<ReadingAssessmentPanel />)
    const exampleInput = screen.getAllByPlaceholderText(/例句/)[0]

    fireEvent.change(exampleInput, { target: { value: 'Put it away.' } })
    fireEvent.change(exampleInput, { target: { value: '' } })

    expect(exampleInput.value).toBe('')
  })

  it('例句欄位應該是選填的（可以為空）', () => {
    // 測試儲存時沒有例句也不會報錯
  })

  it('應該正確載入已存在的例句', async () => {
    // Mock API 返回包含例句的資料
    const mockData = {
      items: [
        {
          text: 'put',
          translation: '放置',
          example_sentence: 'Put it away.'
        }
      ]
    }

    // 驗證例句正確顯示
  })
})
```

---

## 5. 測試計畫

### 5.1 後端測試

#### **Unit Tests**

**檔案**: `backend/tests/unit/test_models.py`

```python
def test_content_item_with_example_sentence():
    """測試 ContentItem 模型包含例句"""
    item = ContentItem(
        content_id=1,
        text="put",
        translation="放置",
        example_sentence="Put it away.",
        order_index=0
    )
    assert item.example_sentence == "Put it away."

def test_content_item_without_example_sentence():
    """測試 ContentItem 模型不包含例句（nullable）"""
    item = ContentItem(
        content_id=1,
        text="get",
        translation="取得",
        order_index=0
    )
    assert item.example_sentence is None
```

#### **Integration Tests**

**檔案**: `backend/tests/integration/api/test_content_api.py`

```python
def test_create_content_with_example_sentences(client, teacher_token):
    """測試創建包含例句的內容"""
    payload = {
        "type": "reading_assessment",
        "title": "測試內容",
        "items": [
            {
                "text": "put",
                "translation": "放置",
                "example_sentence": "Put it away."
            },
            {
                "text": "get",
                "translation": "取得",
                "example_sentence": "Get the book."
            }
        ]
    }

    response = client.post(
        "/api/contents",
        json=payload,
        headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 201
    data = response.json()
    assert data["items"][0]["example_sentence"] == "Put it away."
    assert data["items"][1]["example_sentence"] == "Get the book."

def test_update_example_sentence(client, teacher_token, content_id):
    """測試更新例句"""
    payload = {
        "items": [
            {
                "text": "put",
                "translation": "放置",
                "example_sentence": "Put everything away."  # 更新例句
            }
        ]
    }

    response = client.put(
        f"/api/contents/{content_id}",
        json=payload,
        headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["example_sentence"] == "Put everything away."

def test_backward_compatibility(client, teacher_token):
    """測試向後相容性（沒有 example_sentence 欄位）"""
    payload = {
        "type": "reading_assessment",
        "title": "測試內容",
        "items": [
            {
                "text": "hello",
                "translation": "你好"
                # 沒有 example_sentence
            }
        ]
    }

    response = client.post(
        "/api/contents",
        json=payload,
        headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 201
    assert response.json()["items"][0]["example_sentence"] is None
```

### 5.2 前端測試

**Component Tests** (已在 4.4 說明)

**E2E Tests**

**檔案**: `frontend/e2e/content-creation.spec.ts`

```typescript
import { test, expect } from '@playwright/test'

test.describe('Content Creation with Example Sentence', () => {
  test('教師應該能夠新增包含例句的內容', async ({ page }) => {
    // 1. 登入
    await page.goto('/teacher/login')
    // ...登入流程

    // 2. 進入課程頁面
    await page.goto('/teacher/classroom/1')

    // 3. 新增內容
    await page.click('text=新增內容')
    await page.click('text=朗讀錄音')

    // 4. 輸入單字和例句
    await page.fill('input[placeholder*="輸入文本"]', 'put')
    await page.fill('textarea[placeholder*="中文翻譯"]', '放置')
    await page.fill('input[placeholder*="例句"]', 'Put it away.')

    // 5. 儲存
    await page.click('text=儲存')

    // 6. 驗證
    await expect(page.locator('text=Put it away.')).toBeVisible()
  })

  test('學生應該能夠看到例句', async ({ page }) => {
    // 1. 學生登入
    await page.goto('/student/login')
    // ...登入流程

    // 2. 進入作業
    await page.goto('/student/assignment/1/activity')

    // 3. 驗證例句顯示
    await expect(page.locator('text=Put it away.')).toBeVisible()
  })
})
```

### 5.3 測試檢查清單

**功能測試**:
- [ ] 創建包含例句的內容項目
- [ ] 創建不包含例句的內容項目（向後相容）
- [ ] 更新例句
- [ ] 刪除例句（設為 null）
- [ ] 批次操作包含例句
- [ ] 例句最大長度限制（300 字元）
- [ ] 特殊字元處理（引號、換行等）

**UI/UX 測試**:
- [ ] 例句輸入框正確顯示
- [ ] 例句輸入框支援輸入/編輯/刪除
- [ ] 長例句顯示正確（不溢出）
- [ ] 響應式設計（手機/平板/桌面）
- [ ] 學生端正確顯示例句

**資料庫測試**:
- [ ] Migration 執行成功
- [ ] 現有資料不受影響
- [ ] 新欄位可正常寫入/讀取
- [ ] NULL 值處理正確

**效能測試**:
- [ ] 批次創建 100+ 項目（包含例句）效能正常
- [ ] API 回應時間無明顯增加

---

## 6. 部署計畫

### 6.1 部署前準備

**檢查清單**:
- [ ] 所有測試通過（單元測試、整合測試、E2E 測試）
- [ ] Migration 腳本已準備並測試
- [ ] Rollback 計畫已準備
- [ ] 程式碼已通過 Code Review
- [ ] 文件已更新（API 文件、使用手冊）

### 6.2 部署步驟

#### **Step 1: 部署到 Staging 環境**

```bash
# 1. 切換到 staging 分支
git checkout staging
git merge feature/add-example-sentence-field

# 2. 部署後端
cd backend

# 3. 執行 Migration
alembic upgrade head

# 4. 重啟服務
# (Cloud Run 會自動重啟)

# 5. 驗證
curl https://staging.duotopia.com/api/health
```

#### **Step 2: Staging 環境測試**

**測試項目**:
- [ ] Migration 成功執行
- [ ] 現有資料正常運作
- [ ] 新功能正常運作
- [ ] API 回應正常
- [ ] 前端 UI 正常顯示

**測試時間**: 至少 2 小時

#### **Step 3: 部署到 Production 環境**

```bash
# 1. 備份資料庫
gcloud sql backups create --instance=duotopia-prod

# 2. 切換到 main 分支
git checkout main
git merge staging

# 3. 部署後端
cd backend

# 4. 執行 Migration（Production）
alembic upgrade head

# 5. 驗證 Migration
alembic current

# 6. 部署前端
cd ../frontend
npm run build
# 部署到 Cloud Run 或 CDN

# 7. 監控
# 查看 Cloud Logging，確保無錯誤
```

### 6.3 Rollback 計畫

**如果出現問題，執行以下步驟**:

```bash
# 1. 回滾 Migration
cd backend
alembic downgrade -1

# 2. 回滾程式碼
git revert HEAD
git push origin main

# 3. 重新部署
# (使用上一個穩定版本)

# 4. 驗證
# 確保系統恢復正常
```

### 6.4 監控與告警

**監控項目**:
- [ ] API 錯誤率（應 < 1%）
- [ ] API 回應時間（應 < 500ms）
- [ ] 資料庫查詢效能
- [ ] 前端錯誤率（Sentry）

**告警設定**:
- API 錯誤率 > 5% → 發送 Slack 通知
- API 回應時間 > 1s → 發送 Slack 通知
- 資料庫連線失敗 → 立即通知

---

## 7. 風險評估

### 7.1 技術風險

| 風險 | 影響 | 機率 | 緩解措施 |
|-----|------|------|---------|
| Migration 失敗 | High | Low | 先在 Staging 測試，準備 Rollback |
| 向後相容性問題 | Medium | Low | 完整的測試覆蓋，欄位設為 nullable |
| 前端 UI 破版 | Low | Low | 響應式設計測試 |
| 例句過長影響 UI | Low | Medium | 設定最大長度限制（300 字元） |
| 資料庫效能下降 | Low | Low | 欄位為 Text，不建索引 |

### 7.2 產品風險

| 風險 | 影響 | 機率 | 緩解措施 |
|-----|------|------|---------|
| 使用者不知道如何使用 | Low | Medium | 新增 tooltip 提示 |
| 例句需求變更（需要翻譯/音檔） | Medium | High | Phase 1 只做基本功能，預留擴展空間 |
| 批次貼上格式混亂 | Low | Medium | 提供範例格式，驗證輸入 |

### 7.3 時程風險

| 風險 | 影響 | 機率 | 緩解措施 |
|-----|------|------|---------|
| 開發時間超出預期 | Low | Low | 預留 buffer 時間 |
| 測試發現重大 Bug | Medium | Low | 分階段測試，及早發現問題 |
| Code Review 需要大幅修改 | Low | Low | 遵循現有程式碼風格 |

---

## 8. 時程規劃

### 8.1 開發階段

| 階段 | 任務 | 負責人 | 預估時間 | 完成日期 |
|-----|------|--------|---------|---------|
| **Phase 1: 資料庫** | | | | |
| 1.1 | 修改 models.py | Backend Dev | 30 min | Day 1 |
| 1.2 | 建立 Migration | Backend Dev | 30 min | Day 1 |
| 1.3 | 測試 Migration（Dev） | Backend Dev | 30 min | Day 1 |
| **Phase 2: 後端 API** | | | | |
| 2.1 | 更新 Pydantic Schema | Backend Dev | 30 min | Day 1 |
| 2.2 | 更新 CRUD 操作 | Backend Dev | 1 hour | Day 1 |
| 2.3 | 後端單元測試 | Backend Dev | 1 hour | Day 1 |
| 2.4 | 後端整合測試 | Backend Dev | 1 hour | Day 2 |
| **Phase 3: 前端 UI** | | | | |
| 3.1 | 更新 TypeScript types | Frontend Dev | 30 min | Day 2 |
| 3.2 | 修改 ReadingAssessmentPanel | Frontend Dev | 1.5 hours | Day 2 |
| 3.3 | 修改 StudentActivityPageContent | Frontend Dev | 30 min | Day 2 |
| 3.4 | 修改 GroupedQuestionsTemplate | Frontend Dev | 30 min | Day 2 |
| 3.5 | 前端測試 | Frontend Dev | 1 hour | Day 3 |
| **Phase 4: E2E 測試** | | | | |
| 4.1 | 撰寫 E2E 測試 | QA / Dev | 1 hour | Day 3 |
| 4.2 | 執行完整測試套件 | QA / Dev | 1 hour | Day 3 |
| **Phase 5: 部署** | | | | |
| 5.1 | 部署到 Staging | DevOps | 30 min | Day 3 |
| 5.2 | Staging 驗證 | QA | 2 hours | Day 3 |
| 5.3 | 部署到 Production | DevOps | 1 hour | Day 4 |
| 5.4 | Production 監控 | DevOps | 1 day | Day 4-5 |

**總預估時間**: 14.5 小時（約 2 個工作天）

### 8.2 Milestone

- [ ] **M1**: 資料庫 Migration 完成（Day 1）
- [ ] **M2**: 後端 API 完成並測試通過（Day 2）
- [ ] **M3**: 前端 UI 完成並測試通過（Day 3）
- [ ] **M4**: Staging 環境驗證通過（Day 3）
- [ ] **M5**: Production 部署完成（Day 4）

---

## 9. 未來擴展

### Phase 2 功能（未來考慮）

#### **9.1 例句翻譯**
- 新增 `example_sentence_translation` 欄位（中文翻譯）
- 新增 `example_sentence_definition` 欄位（英文釋義）
- 支援 AI 自動翻譯例句

#### **9.2 例句音檔**
- 新增 `example_sentence_audio_url` 欄位
- 支援 TTS 生成例句音檔
- 支援教師錄製例句音檔

#### **9.3 AI 自動生成例句**
- 整合 OpenAI GPT 或其他 LLM
- 根據單字自動生成合適的例句
- 批次生成例句功能

#### **9.4 多個例句**
- 變更資料結構為一對多（一個 ContentItem 對應多個 ExampleSentence）
- 新增 `example_sentences` 表
- UI 支援新增/刪除多個例句

---

## 10. 檢查清單

### 開發前
- [ ] 閱讀並理解本計畫
- [ ] 確認需求（例句是否需要翻譯/音檔）
- [ ] 準備開發環境
- [ ] 建立 feature branch: `feature/add-example-sentence-field`

### 開發中
- [ ] 遵循 CLAUDE.md 規範
- [ ] 每個階段完成後執行測試
- [ ] 撰寫清晰的 commit message
- [ ] 不使用 `--no-verify` 跳過 pre-commit hooks

### 開發後
- [ ] 所有測試通過
- [ ] 程式碼格式化（black, ESLint）
- [ ] 更新文件
- [ ] 提交 Pull Request
- [ ] Code Review 通過
- [ ] 部署到 Staging 並驗證
- [ ] 部署到 Production

---

## 11. 參考資料

### 相關文件
- [CLAUDE.md](../../CLAUDE.md) - 開發規範
- [ASSIGNMENT_FLOW_DIAGRAM.md](../technical/ASSIGNMENT_FLOW_DIAGRAM.md) - 作業系統架構
- [TESTING_GUIDE.md](../TESTING_GUIDE.md) - 測試指南
- [assignment_diff.md](../../assignment_diff.md) - Spec vs 實作差異
- [frontend_flow.md](../../frontend_flow.md) - 前端流程

### 技術文件
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [React TypeScript Documentation](https://react-typescript-cheatsheet.netlify.app/)

---

## 12. 附錄

### A. 資料庫欄位詳細規格

```sql
-- content_items 表新增欄位
ALTER TABLE content_items
ADD COLUMN example_sentence TEXT NULL;

-- 欄位說明
-- example_sentence: 例句（選填）
-- 類型: TEXT
-- 允許 NULL: YES
-- 預設值: NULL
-- 索引: NO（不需要）
-- 最大長度: 無限制（前端限制 300 字元）
```

### B. API Request/Response 範例

**創建內容（包含例句）**:
```json
// POST /api/contents
{
  "type": "reading_assessment",
  "title": "基礎動詞練習",
  "items": [
    {
      "text": "put",
      "translation": "放置",
      "example_sentence": "Put it away."
    },
    {
      "text": "get",
      "translation": "取得",
      "example_sentence": "Get the book from the shelf."
    }
  ]
}

// Response 200 OK
{
  "id": 123,
  "type": "reading_assessment",
  "title": "基礎動詞練習",
  "items": [
    {
      "id": 1,
      "text": "put",
      "translation": "放置",
      "example_sentence": "Put it away.",
      "audio_url": null,
      "order_index": 0
    },
    {
      "id": 2,
      "text": "get",
      "translation": "取得",
      "example_sentence": "Get the book from the shelf.",
      "audio_url": null,
      "order_index": 1
    }
  ]
}
```

**更新例句**:
```json
// PATCH /api/contents/123/items/1
{
  "example_sentence": "Put everything away right now."
}

// Response 200 OK
{
  "id": 1,
  "text": "put",
  "translation": "放置",
  "example_sentence": "Put everything away right now.",
  "audio_url": null,
  "order_index": 0
}
```

---

## 附錄 A - Phase 2 完整功能設計

> **狀態**: 📋 待團隊決策（成本評估中）
> **預估成本**: $1-3/月（50 位教師使用情境）
> **開發時間**: 約 1-2 天

---

### A.1 功能概述

**Phase 2 目標**: 讓教師只需輸入單字，AI 自動生成合適的例句並翻譯。

**使用流程**:
```
教師輸入：put
         ↓
點擊「AI 生成例句」
         ↓
AI 自動產生：
  - 例句: Put it away.
  - 中文翻譯: 放好它。
  - 英文釋義: To place something in its proper location.
```

---

### A.2 後端實作

#### **A.2.1 擴展 TranslationService**

**檔案**: `backend/services/translation.py`

**新增方法**:
```python
async def generate_example_sentence(
    self,
    word: str,
    context: str = None,
    level: str = "A1-B1"
) -> str:
    """
    根據單字自動生成例句

    Args:
        word: 單字（如 "put"）
        context: 額外的上下文（選填，如 "classroom"）
        level: 難度級別（預設 A1-B1）

    Returns:
        生成的例句
    """
    self._ensure_client()

    try:
        # 構建 prompt
        if context:
            prompt = f"""Please create a simple, natural example sentence using the word "{word}" in the context of {context}.

Requirements:
1. Suitable for English learners ({level} level)
2. Clear and easy to understand
3. Natural and commonly used
4. Maximum 15 words
5. Use simple grammar

Only return the sentence, no explanation or punctuation at the end."""
        else:
            prompt = f"""Please create a simple, natural example sentence using the word "{word}".

Requirements:
1. Suitable for English learners ({level} level)
2. Clear and easy to understand
3. Natural and commonly used
4. Maximum 15 words
5. Use simple grammar

Only return the sentence, no explanation or punctuation at the end."""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an experienced English teacher creating example sentences "
                        "for language learners. Create simple, clear, and natural sentences."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,  # 稍高的隨機性以獲得更自然的句子
            max_tokens=50
        )

        sentence = response.choices[0].message.content.strip()

        # 移除可能的句號（我們統一在前端加）
        sentence = sentence.rstrip('.')

        return sentence

    except Exception as e:
        print(f"Generate example sentence error: {e}")
        # Fallback: 返回基本句型
        return f"This is {word}"


async def batch_generate_example_sentences(
    self,
    words: List[str],
    context: str = None,
    level: str = "A1-B1"
) -> List[str]:
    """
    批次生成例句

    Args:
        words: 單字列表
        context: 上下文（選填）
        level: 難度級別

    Returns:
        例句列表
    """
    import asyncio

    # 使用 asyncio.gather 並行處理
    tasks = [
        self.generate_example_sentence(word, context, level)
        for word in words
    ]
    example_sentences = await asyncio.gather(*tasks)

    return example_sentences


async def generate_example_with_translations(
    self,
    word: str,
    context: str = None,
    level: str = "A1-B1"
) -> dict:
    """
    一次生成例句及其翻譯（優化版）

    Args:
        word: 單字
        context: 上下文
        level: 難度級別

    Returns:
        {
            "example_sentence": "Put it away.",
            "translation": "放好它。",
            "definition": "To place something in its proper location."
        }
    """
    # 1. 生成例句
    example_sentence = await self.generate_example_sentence(word, context, level)

    # 2. 並行翻譯（中文 + 英文釋義）
    import asyncio

    translation_task = self.translate_text(example_sentence, "zh-TW")
    definition_task = self.translate_text(example_sentence, "en")

    translation, definition = await asyncio.gather(
        translation_task,
        definition_task
    )

    return {
        "example_sentence": example_sentence,
        "translation": translation,
        "definition": definition
    }
```

---

#### **A.2.2 新增 API 端點**

**檔案**: `backend/routers/teachers.py`

**新增 Schema**:
```python
class GenerateExampleSentenceRequest(BaseModel):
    word: str
    context: Optional[str] = None
    level: Optional[str] = "A1-B1"

class BatchGenerateExampleSentenceRequest(BaseModel):
    words: List[str]
    context: Optional[str] = None
    level: Optional[str] = "A1-B1"
```

**新增端點**:
```python
@router.post("/generate-example-sentence")
async def generate_example_sentence(
    request: GenerateExampleSentenceRequest,
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """
    為單字生成例句及翻譯

    成本: 約 $0.00006/次
    """
    try:
        result = await translation_service.generate_example_with_translations(
            request.word,
            request.context,
            request.level
        )
        return result
    except Exception as e:
        print(f"Generate example sentence error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate example sentence"
        )


@router.post("/generate-example-sentence/batch")
async def batch_generate_example_sentences(
    request: BatchGenerateExampleSentenceRequest,
    current_teacher: Teacher = Depends(get_current_teacher)
):
    """
    批次生成例句及翻譯

    成本: 約 $0.00006/次 × 數量
    """
    try:
        import asyncio

        # 並行生成所有例句及翻譯
        tasks = [
            translation_service.generate_example_with_translations(
                word,
                request.context,
                request.level
            )
            for word in request.words
        ]

        results = await asyncio.gather(*tasks)

        return {
            "words": request.words,
            "results": results
        }
    except Exception as e:
        print(f"Batch generate example sentences error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to batch generate example sentences"
        )
```

---

### A.3 前端實作

#### **A.3.1 API Client 擴展**

**檔案**: `frontend/src/lib/api.ts`

**新增方法**:
```typescript
// ============ Example Sentence Generation Methods ============

async generateExampleSentence(
  word: string,
  context?: string,
  level?: string
): Promise<{
  example_sentence: string
  translation: string
  definition: string
}> {
  return this.request("/api/teachers/generate-example-sentence", {
    method: "POST",
    body: JSON.stringify({ word, context, level }),
  })
}

async batchGenerateExampleSentences(
  words: string[],
  context?: string,
  level?: string
): Promise<{
  words: string[]
  results: Array<{
    example_sentence: string
    translation: string
    definition: string
  }>
}> {
  return this.request("/api/teachers/generate-example-sentence/batch", {
    method: "POST",
    body: JSON.stringify({ words, context, level }),
  })
}
```

---

#### **A.3.2 ReadingAssessmentPanel 更新**

**檔案**: `frontend/src/components/ReadingAssessmentPanel.tsx`

**新增功能 1: 單個生成**
```typescript
const handleGenerateExampleSentence = async (index: number) => {
  const row = rows[index]

  if (!row.text) {
    toast.error("請先輸入單字")
    return
  }

  try {
    toast.info("AI 正在生成例句...")

    const result = await apiClient.generateExampleSentence(row.text)

    // 更新 row
    const newRows = [...rows]
    newRows[index] = {
      ...newRows[index],
      example_sentence: result.example_sentence,
      example_sentence_translation: result.translation,
      example_sentence_definition: result.definition
    }
    setRows(newRows)

    toast.success("例句生成完成！")
  } catch (error) {
    console.error("Generate example sentence error:", error)
    toast.error("生成失敗，請重試")
  }
}
```

**新增功能 2: 批次生成**
```typescript
const handleBatchGenerateExampleSentences = async () => {
  // 收集有單字但沒有例句的項目
  const itemsNeedExample = rows.filter(
    row => row.text && !row.example_sentence
  )

  if (itemsNeedExample.length === 0) {
    toast.info("沒有需要生成例句的項目")
    return
  }

  try {
    toast.info(`正在生成 ${itemsNeedExample.length} 個例句...`)

    const words = itemsNeedExample.map(row => row.text)
    const result = await apiClient.batchGenerateExampleSentences(words)

    // 更新 rows
    const newRows = [...rows]
    itemsNeedExample.forEach((item, idx) => {
      const rowIndex = rows.findIndex(r => r.id === item.id)
      newRows[rowIndex] = {
        ...newRows[rowIndex],
        example_sentence: result.results[idx].example_sentence,
        example_sentence_translation: result.results[idx].translation,
        example_sentence_definition: result.results[idx].definition
      }
    })
    setRows(newRows)

    toast.success(`成功生成 ${itemsNeedExample.length} 個例句！`)
  } catch (error) {
    console.error("Batch generate error:", error)
    toast.error("批次生成失敗")
  }
}
```

**UI 更新**:
```tsx
{/* 在每個 row 的例句輸入框旁邊新增按鈕 */}
<div className="relative">
  <input
    type="text"
    value={row.example_sentence || ""}
    onChange={(e) => handleUpdateRow(index, "example_sentence", e.target.value)}
    className="w-full px-3 py-2 pr-24 border rounded-md text-sm"
    placeholder="例句 (optional)"
    maxLength={300}
  />

  {/* ✨ 新增：AI 生成例句按鈕 */}
  <button
    onClick={() => handleGenerateExampleSentence(index)}
    className="absolute right-2 top-1/2 -translate-y-1/2 px-2 py-1 text-xs bg-purple-100 hover:bg-purple-200 rounded"
    title="AI 生成例句（約 0.006 美分）"
  >
    🤖 AI
  </button>
</div>

{/* 批次操作按鈕 */}
<div className="flex flex-wrap gap-2">
  {/* ... 現有按鈕 ... */}

  {/* ✨ 新增：批次生成例句按鈕 */}
  <Button
    variant="outline"
    size="sm"
    onClick={handleBatchGenerateExampleSentences}
    className="bg-purple-100 hover:bg-purple-200 border-purple-300"
    title="AI 批次生成例句（約 0.006 美分/句）"
  >
    🤖 批次生成例句
  </Button>
</div>
```

---

### A.4 使用限制（成本控制）

**選項 1: 前端提示**
```tsx
<Checkbox onChange={(e) => setAutoGenerateExample(e.target.checked)}>
  ✓ AI 自動生成例句（每次約 0.006 美分，每月預估 $1-3）
</Checkbox>
```

**選項 2: 後端限制**
```python
# 在 translation.py 中新增
class TranslationService:
    def __init__(self):
        self.daily_example_count = 0
        self.daily_example_limit = 1000  # 每日限制

    async def generate_example_sentence(self, word: str, ...):
        # 檢查限制
        if self.daily_example_count >= self.daily_example_limit:
            raise Exception("Daily limit reached. Please try again tomorrow.")

        # ... 生成例句

        self.daily_example_count += 1
```

**選項 3: Redis 計數**
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379)

async def check_daily_limit(teacher_id: int) -> bool:
    key = f"example_sentence_count:{teacher_id}:{date.today()}"
    count = redis_client.get(key)

    if count and int(count) >= 100:  # 每位教師每日 100 次
        return False

    redis_client.incr(key)
    redis_client.expire(key, 86400)  # 24 小時過期
    return True
```

---

### A.5 測試計畫

**單元測試**:
```python
# backend/tests/unit/test_translation_service.py

async def test_generate_example_sentence():
    """測試生成例句"""
    sentence = await translation_service.generate_example_sentence("put")
    assert "put" in sentence.lower()
    assert len(sentence.split()) <= 15

async def test_generate_example_with_translations():
    """測試生成例句及翻譯"""
    result = await translation_service.generate_example_with_translations("get")
    assert "example_sentence" in result
    assert "translation" in result
    assert "definition" in result
```

**整合測試**:
```python
def test_generate_example_sentence_api(client, teacher_token):
    """測試 API 端點"""
    response = client.post(
        "/api/teachers/generate-example-sentence",
        json={"word": "put"},
        headers={"Authorization": f"Bearer {teacher_token}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "example_sentence" in data
    assert "translation" in data
```

---

### A.6 成本分析與監控

#### **預估成本**:
| 使用情境 | 每月生成量 | 每月成本 |
|---------|-----------|---------|
| 輕量使用（每位教師 100 句） | 5,000 句 | $0.30 |
| 中等使用（每位教師 500 句） | 25,000 句 | $1.50 |
| 重度使用（每位教師 1,000 句） | 50,000 句 | $3.00 |

#### **監控措施**:
1. **OpenAI Dashboard 設定**:
   - 每月預算上限：$10
   - 超過 $5 發送警告郵件
   - 超過 $10 自動停止 API 調用

2. **內部監控**:
   ```python
   # 記錄每次 API 調用
   import logging

   logger.info(f"Generated example for '{word}' - Cost: ~$0.00006")
   ```

3. **使用報表**:
   - 每週生成使用統計報表
   - 追蹤各教師的使用量
   - 識別異常使用模式

---

### A.7 部署清單

**部署前確認**:
- [ ] OpenAI API Key 已設定
- [ ] 每月預算上限已設定
- [ ] 使用限制已實作（可選）
- [ ] 監控告警已設定
- [ ] 測試通過

**部署後監控**:
- [ ] 監控 API 調用次數
- [ ] 監控成本增長
- [ ] 收集教師回饋
- [ ] 評估功能使用率

---

### A.8 團隊決策檢查清單

討論 Phase 2 實作前，請確認以下問題：

- [ ] **成本接受度**: 每月 $1-3 是否可接受？
- [ ] **使用限制**: 是否需要設定每日/每月上限？
- [ ] **預設行為**: AI 生成例句預設開啟還是關閉？
- [ ] **品質控制**: 是否需要人工審核 AI 生成的例句？
- [ ] **替代方案**: 是否考慮使用更便宜的模型？
- [ ] **ROI 評估**: 提升的效率是否值得增加的成本？

---

**Phase 2 總結**:
- ✅ 技術可行（擴展現有服務即可）
- ✅ 成本可控（每月 $1-3）
- ⚠️ 需團隊決策（成本、限制、預設行為）
- 📊 建議先部署 Phase 1，收集使用數據後再決定

---

**計畫版本**: v1.1
**最後更新**: 2025-11-10
**狀態**: ✅ Phase 1 計畫完成，準備實作
**Phase 2**: 📋 待團隊決策
