# Duotopia 產品需求文件 (PRD) v4.0

## 一、產品概述

### 1.1 產品定位
Duotopia 是一個以 AI 驅動的多元智能英語學習平台，專為國小到國中學生（6-15歲）設計。透過語音辨識、即時回饋和遊戲化學習，幫助學生提升英語口說能力。

**Phase 1 定位**：專注於個體教師版本，讓獨立教師能夠：
- 建立並管理自己的班級
- 新增學生並管理學習進度
- 建立課程內容
- 派發作業給學生
- 批改作業並追蹤成效

### 1.2 當前開發狀態
- **架構遷移**：從 Base44 BaaS 成功遷移至 Google Cloud 架構
- **技術棧**：前端 React + TypeScript，後端 FastAPI + PostgreSQL
- **部署環境**：Google Cloud Run + Cloud SQL
- **開發重點**：Phase 1 - 個體教師核心功能

### 1.3 目標用戶（Phase 1）
- **教師**：獨立英語教師
- **學生**：6-15歲學生

## 二、系統架構

### 2.1 技術架構
- **前端框架**：React 18 + Vite + TypeScript
- **UI 設計**：Tailwind CSS + shadcn/ui
- **動畫效果**：Framer Motion
- **後端服務**：Base44 BaaS 平台
- **資料管理**：Base44 Entities 系統
- **即時通訊**：WebSocket（規劃中）

### 2.2 核心實體模型（Phase 1）

#### 使用者相關
- **Teacher**：教師實體（獨立教師）
- **Student**：學生實體
- **TeacherSession**：教師會話管理
- **StudentSession**：學生會話管理

#### 班級管理
- **Classroom**：班級（屬於特定教師）
  - ⚠️ 注意：使用 Classroom 而非 Class（避免與 Python 保留字衝突）
- **ClassroomStudent**：班級學生關聯

#### 課程內容（三層架構）
- **Program**：課程計畫（如：國小五年級英語課程）
  - **創建歸屬**：必須在特定班級內創建（teacher_id + classroom_id）
  - **複製機制**：可被其他班級複製使用（source_from_id 追蹤原始來源）
  - **原創課程**：source_from_id = null（原創課程）
  - **複製課程**：source_from_id = 原始課程的 Program ID
  - 包含多個 Lesson
  - 設定整體學習目標
  - 定義課程期間

- **Lesson**：課程單元（如：Unit 1 - Greetings）
  - 屬於特定 Program
  - 包含多個 Content
  - 單元學習目標

- **Content**：課程內容（Phase 1 只有朗讀錄音集）
  - 屬於特定 Lesson
  - 實際的練習內容
  - 朗讀錄音集：3-15 個文本項目

**注意**：移除 ClassroomProgramMapping，因為 Program 已直接關聯到 Classroom

#### 作業與評量（新架構 - 2025年9月更新）
- **Assignment**：作業主表（教師建立的作業任務）
- **AssignmentContent**：作業-內容關聯表（一個作業可包含多個內容）
- **StudentAssignment**：學生作業實例（每個學生對應作業的記錄）
- **StudentContentProgress**：學生-內容進度表（追蹤學生對每個內容的完成狀況）

#### 系統功能
- **TeacherNotification**：教師通知
- **StudentProgress**：學生進度追蹤

### 2.3 Phase 2 擴展規劃（未來）
- **School**：學校管理
- **Institution**：機構管理
- **SchoolTeacher**：學校教師關聯
- **InstitutionTeacher**：機構教師關聯
- **CourseTemplate**：機構課程模板

### 2.4 活動類型架構（Phase 1）

系統 Phase 1 支援一種核心活動類型：

1. **朗讀評測 (reading_assessment)**
   - 評估指標：WPM（每分鐘字數）、準確率、流暢度、發音
   - AI 分析：提供詳細的發音錯誤分析
   - 文本內容：3-15 句的單字、片語或句子
   - 教師功能：可為每個文本錄製示範音檔
   - 學生練習：逐句錄音並獲得即時 AI 回饋

### 2.5 未來擴展活動類型（Phase 2）
- **口說練習 (speaking_practice)**
- **情境對話 (speaking_scenario)**
- **聽力填空 (listening_cloze)**
- **造句練習 (sentence_making)**
- **口說測驗 (speaking_quiz)**

## 三、核心功能模組（Phase 1）

### 3.1 認證系統

#### 教師認證（個體戶）
- **登入方式**：Email + 密碼
- **註冊流程**：
  - 輸入 Email
  - 設定密碼
  - 輸入教師姓名
  - Email 驗證（Phase 2 再做）
- **Demo 帳號**：demo@duotopia.com / demo123（含預設資料）
- **個人工作區**：每位教師擁有獨立的班級和課程空間
- **權限**：完全管理自己的班級、學生、課程

#### 學生認證

**密碼管理系統**：
- **預設密碼**：生日（YYYYMMDD 格式）
- **密碼欄位**：
  - `birthdate`：生日（Date 格式，用於產生預設密碼）
  - `password_hash`：密碼雜湊值
  - `password_changed`：布林值，記錄是否已更改密碼
- **教師檢視**：
  - 可看到學生是否已更改密碼
  - 若未更改，顯示預設密碼（生日格式）
  - 若已更改，只顯示狀態，不顯示實際密碼

**簡化登入流程**（Phase 1）：
1. **輸入教師 Email**
   - 學生輸入所屬班級教師的 Email

2. **選擇班級**
   - 顯示該教師所有班級
   - 學生選擇自己所屬班級

3. **選擇姓名並輸入密碼**
   - 從班級學生名單中選擇自己
   - 輸入密碼（預設為生日：YYYYMMDD 格式）
   - 登入成功，進入作業列表

**Phase 2 擴展**：
- 家長 Email 綁定
- Email 驗證機制
- 歷史記錄快速選擇

### 3.2 教師端功能（Phase 1）

#### 教師導航架構（Sidebar Navigation）

**側邊欄功能模組**：
1. **儀表板 (Dashboard)**
   - URL: `/teacher/dashboard`
   - 顯示統計摘要和快速操作入口

2. **我的班級 (Classrooms)**
   - URL: `/teacher/classrooms`
   - 顯示格式：**Table 表格檢視**
   - 表格欄位：ID、班級名稱、描述、等級、學生數、課程數、建立時間、操作
   - 點擊班級：進入班級詳情頁面 `/teacher/classroom/{id}`
   - 班級詳情功能：
     - 學生列表（可在班級內新增學生）
     - 課程列表（可在班級內建立課程）
     - 班級設定管理

3. **所有學生 (Students)**
   - URL: `/teacher/students`
   - 顯示格式：**Table 表格檢視**
   - 表格欄位：ID、學生姓名、Email、班級、密碼狀態、狀態、最後登入、操作
   - 密碼狀態顯示規則：
     - 未更改：顯示「預設密碼」標籤 + 生日格式（如：20120101）
     - 已更改：顯示「已更改」標籤（不顯示實際密碼）
   - 資料來源：**真實資料庫資料**（非 Mock）

4. **所有課程 (Programs)**
   - URL: `/teacher/programs`
   - 顯示格式：**Table 表格檢視**
   - 表格欄位：ID、課程名稱、所屬班級、等級、狀態、課程數、學生數、預計時數、更新時間、操作

**側邊欄底部資訊**：
- 顯示當前登入教師資訊
- 教師頭像（姓名首字母）
- 教師姓名
- 教師 Email
- 登出按鈕

#### 教師核心工作流程

**步驟 1：教師註冊/登入**
- 使用 Email + 密碼登入
- 新教師先註冊（Email、密碼、姓名）
- Demo 帳號可快速體驗

**步驟 2：建立班級**
- 班級名稱設定（如：國小五年級A班）
- 班級程度選擇：preA, A1, A2, B1, B2, C1, C2
- 班級描述（選填）

**步驟 3：新增學生**
- 必填資料：
  - 學生姓名
  - 生日（用作預設密碼，格式：YYYYMMDD）
- 選填資料：
  - 學號
- 批量加入班級

**步驟 4：建立課程（三層結構）**

4.1 建立課程計畫 (Program)
- 課程名稱（如：五年級上學期英語）
- 課程描述
- 預計時程

4.2 建立課程單元 (Lesson)
- 單元名稱（如：Unit 1 - Greetings）
- 單元目標
- 預計課時

4.3 建立朗讀評測內容 (Content)
- 內容標題（title）
- 內容描述（description，選填）
- 文本項目（3-15 句）：
  - 英文文本（必填）
  - 中文翻譯（選填，可使用翻譯 API）
- TTS 語音生成（批量生成所有項目的語音）

**步驟 5：作業派發**
- 選擇課程計畫 (Program)
- 選擇特定單元 (Lesson)
- 選擇內容 (Content)
- 選擇班級或個別學生
- 設定截止日期

#### 3.2.1 教師儀表板 (TeacherDashboard)

**課程管理**
- 建立新課程：設定名稱、描述、難度等級
- 課文管理：
  - 新增六種不同類型的活動
  - 設定活動參數（目標值、時間限制等）
  - 課文順序調整
  - 封存/取消封存功能
- 課程搜尋與篩選
- 課程複製功能

**Content 管理功能（在班級詳情頁）**
- 位置：`/teacher/classroom/{id}` → 課程標籤頁
- 三層結構顯示：Program → Lesson → Content
- Content 建立功能：
  - 標題（title）：Content 名稱
  - 描述（description）：選填說明
  - 類型選擇：朗讀評測（reading_assessment）
  - 項目管理（items）：
    - 支援 3-15 個朗讀項目
    - 每個項目包含英文文本
    - 支援中文翻譯（選填）
    - 動態新增/刪除項目
- API 輔助功能：
  - 翻譯 API：自動翻譯英文句子為中文
  - TTS API：批量生成語音檔案
- 編輯面板：點擊 Content 展開右側編輯面板
- 即時儲存：修改後即時更新

**快速操作區**
- 快速派發作業
- 查看待批改作業
- 查看班級狀態
- 最新通知提醒

#### 3.2.2 班級管理 (ClassManagement)

**班級操作**
- 建立班級：設定名稱、年級、難度等級
- 班級資訊編輯
- 班級課程關聯：選擇適合的課程內容
- 班級封存管理

**學生管理**
- **單一新增**：
  - 填寫學生姓名、學號、Email、生日
  - 設定個人化學習目標
  - 自動生成登入資訊

- **批量匯入**：
  - 支援 CSV 格式（姓名,學號,Email,生日）
  - 自動檢測重複資料
  - Email 格式驗證
  - 匯入預覽與錯誤提示
  - 衝突處理選項（跳過/更新/保留）

- **學生資料維護**：
  - 編輯個人資訊
  - 調整學習目標
  - 查看學習記錄
  - 停用/啟用帳號

#### 3.2.3 作業派發系統 (AssignHomework) - 新架構設計

#### 資料模型架構（2025年9月重構）

**核心設計理念**：
- 作業（Assignment）是一個獨立的實體，擁有自己的 ID
- 支援多內容作業（一個作業可包含多個 Content）
- 靈活的指派機制（全班或特定學生）
- 完整的進度追蹤（每個內容的完成狀態）

**資料表關係**：
```
Assignment (作業主表)
    ├── AssignmentContent (作業-內容關聯)
    │   └── Content (課程內容)
    └── StudentAssignment (學生-作業實例)
        └── StudentContentProgress (學生-內容進度)
```

**關鍵欄位設計**：
1. **Assignment**：
   - `id`：作業唯一識別碼（Primary Key）
   - `title`：作業標題
   - `description`：作業說明
   - `classroom_id`：所屬班級
   - `teacher_id`：建立教師
   - `due_date`：截止日期
   - `created_at`：建立時間
   - `updated_at`：更新時間
   - `is_active`：軟刪除標記（統一使用 is_active）

2. **AssignmentContent**：
   - `assignment_id`：作業 ID（Foreign Key）
   - `content_id`：內容 ID（Foreign Key）
   - `order_index`：內容順序（支援順序學習）

3. **StudentAssignment**：
   - `id`：學生作業實例 ID
   - `assignment_id`：關聯到 Assignment（Foreign Key）
   - `student_id`：學生 ID
   - `status`：作業狀態（見下方狀態說明）
   - `score`：總分（選填，保留欄位但不強制使用）
   - `feedback`：總評
   - `assigned_at`：指派時間
   - `started_at`：首次開始時間
   - `submitted_at`：提交時間（所有 Content 完成）
   - `graded_at`：批改完成時間
   - `is_active`：軟刪除標記

4. **StudentContentProgress**：
   - `student_assignment_id`：學生作業實例 ID
   - `content_id`：內容 ID
   - `status`：該內容的完成狀態（使用相同的 AssignmentStatus）
   - `score`：該內容的分數（選填，保留但不強制）
   - `checked`：教師批改標記（True=通過，False=未通過，None=未批改）
   - `feedback`：該內容的個別回饋
   - `response_data`：學生回答資料（JSON，儲存錄音URL等）
   - `ai_scores`：AI 評分結果（JSON，如 {"wpm": 85, "accuracy": 0.92}）
   - `ai_feedback`：AI 生成的回饋
   - `started_at`：開始練習時間
   - `completed_at`：完成時間
   - `order_index`：順序索引
   - `is_locked`：是否需要解鎖（Phase 2 支援順序學習）

#### 作業狀態定義

```python
class AssignmentStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"     # 未開始
    IN_PROGRESS = "IN_PROGRESS"     # 進行中
    SUBMITTED = "SUBMITTED"         # 已提交（待批改）
    GRADED = "GRADED"              # 已批改（完成）
    RETURNED = "RETURNED"          # 退回訂正
    RESUBMITTED = "RESUBMITTED"    # 重新提交（訂正後待批改）
```

**狀態流轉規則**：
1. 正常流程：NOT_STARTED → IN_PROGRESS → SUBMITTED → GRADED
2. 需要訂正：SUBMITTED/GRADED → RETURNED → RESUBMITTED → GRADED
3. 可多次訂正：GRADED → RETURNED → RESUBMITTED → GRADED（循環）

#### 作業建立流程

**新版三步驟精靈**：

**Step 1：選擇內容（支援多選）**
- Tree View 展示 Program → Lesson → Content
- 支援多選 Content（Checkbox）
- 自動計算預估完成時間
- 顯示每個 Content 的難度標籤

**Step 2：選擇對象**
- 選擇要指派的學生：
  - 「全選」按鈕：快速選擇班級所有學生
  - 個別勾選：選擇特定學生
  - 實際動作：為每個選中的學生建立 StudentAssignment 記錄
- 智慧提醒：顯示學生當前作業負擔

**Step 3：設定細節**
- 作業標題（可自動組合或自訂）
- 作業說明（Markdown 支援）
- 截止日期設定
- 順序學習選項（是否需要按順序完成內容）

#### 作業管理功能

**教師端作業管理**：
1. **建立作業** (`POST /api/assignments`)
   ```json
   {
     "title": "Unit 1 綜合練習",
     "description": "請完成以下三個朗讀練習",
     "classroom_id": 1,
     "content_ids": [101, 102, 103],
     "student_ids": [1, 2, 3, 4, 5],  // 要指派的學生 ID 列表
     "due_date": "2025-09-15T23:59:59Z"
   }
   ```

2. **編輯作業** (`PUT /api/assignments/{id}`)
   - 可修改：標題、說明、截止日期
   - 不可修改：內容列表（避免影響已開始的學生）
   - 編輯入口：作業詳情 Modal 內
   - 批量延長截止日期：編輯作業即可影響所有學生

3. **刪除作業** (`DELETE /api/assignments/{id}`)
   - 軟刪除：設定 `is_active = false`
   - CASCADE 刪除相關 StudentAssignment
   - 保留資料供日後分析

4. **複製作業** (`POST /api/assignments/{id}/copy`)
   - 複製作業到其他班級
   - 可用於額外指派給特定學生（差異化教學）
   - 保留原作業的內容結構

5. **查詢作業** (`GET /api/assignments`)
   - 支援篩選：班級、狀態、日期範圍
   - 包含統計：完成率、平均分數
   - 排序選項：截止日期、建立日期、完成率

**學生端作業功能**：
1. **查看作業列表** (`GET /api/student/assignments`)
   - 分類顯示：待完成、進行中、已完成、需修正
   - 顯示每個作業的內容數量和進度
   - 即時顯示作業狀態（老師可看到學生正在做）

2. **開始作業** (`POST /api/assignments/{id}/start`)
   - 更新 StudentAssignment 狀態為 IN_PROGRESS
   - 建立 StudentContentProgress 記錄
   - 進入作業執行介面

3. **作業執行介面**：
   - **作業總覽頁**：
     - 顯示作業標題和說明
     - Content 列表（卡片或列表形式）
     - 每個 Content 顯示：
       - 標題和類型圖示
       - 完成狀態（未開始/進行中/已完成/需修正）
       - checked 標記（通過✓/未通過✗）
       - 開始/繼續/重做按鈕
     - 進度指示器（3/5 完成）

   - **Content 練習介面**（朗讀錄音集）：
     - 顯示所有錄音項目列表（3-15句）
     - 每個項目顯示：
       - 英文文本
       - 中文翻譯（如有）
       - 錄音按鈕 / 播放按鈕（已錄）
       - 重錄按鈕（已錄）
       - AI 評分結果（已錄）
     - 每句錄完立即儲存
     - 全部完成自動返回作業總覽

4. **進度保存機制**（朗讀錄音集）：
   - **自動保存**：
     - 每個錄音項目完成即時保存
     - Content 全部項目完成後自動標記為 SUBMITTED

   - **中斷恢復**：
     - 顯示每個項目的錄音狀態（已錄/未錄）
     - 已錄的項目保留錄音，可繼續未完成的項目

   - **重做功能**：
     - 任何項目都可重新錄音
     - 重錄會覆蓋原有錄音

5. **提交內容** (`POST /api/assignments/{id}/contents/{content_id}/submit`)
   - 每個 Content 完成即自動提交
   - 更新 StudentContentProgress 狀態
   - 儲存答案和 AI 評分結果
   - 所有 Content 完成後，作業狀態自動變為 SUBMITTED

6. **作業完成後流程**：
   - **全部完成提示**：
     - 顯示「恭喜完成！」訊息
     - 自動返回作業列表
     - 作業卡片顯示「已提交」狀態

   - **查看批改結果**：
     - 作業狀態變為 GRADED 後
     - 作業卡片顯示「已批改」標籤
     - 點擊可查看批改詳情：
       - 每個 Content 的 checked 狀態
       - 教師回饋
       - AI 評分結果

   - **處理退回作業**：
     - 作業狀態為 RETURNED 時
     - 作業卡片顯示「需修正」標籤（紅色）
     - 點擊進入作業總覽
     - 未通過的 Content 顯示 ✗ 標記
     - 可查看教師回饋
     - 點擊重做未通過的 Content
     - 重新提交後狀態變為 RESUBMITTED

#### 批改與回饋系統

**多內容批改流程**：
1. **逐個 Content 批改**：
   - 每個 Content 可獨立給予評價和回饋
   - 每個 Content 有 `checked` 標記（通過/未通過）
   - 學生可快速識別哪些 Content 需要修正

2. **整體作業管理**：
   - 所有 Content 都需查看後才算完成批改
   - 整份作業退回（RETURNED）時，透過 checked 標記區分
   - 教師可選擇性標記哪些 Content 需要重做

3. **分數機制**（Phase 2 考慮）：
   - 目前先不實作分數計算
   - 專注於通過/未通過的評價機制

**AI 自動批改**：
- 朗讀評測即時 AI 評分
- 自動計算 WPM、準確率、流暢度
- 生成個人化改進建議

**教師手動批改**：
- 在作業詳情 Modal 內進行
- 逐個 Content 檢視和批改
- 標記 checked 狀態（通過/未通過）
- 添加文字或語音回饋
- 整份作業退回（狀態改為 RETURNED）

#### 統計與提醒

**未批改提醒**：
- 班級列表顯示未批改作業數量徽章
- 作業列表標記需要批改的項目
- Dashboard 顯示待批改統計卡片

**完成率統計**：
- 即時計算班級完成率
- 個人進度追蹤
- 視覺化進度條和圖表

#### 3.2.4 作業列表管理 (AssignmentList)

**教師端作業列表**

**列表檢視設計**：
- 位置：班級詳情頁 → 「作業列表」Tab
- 顯示格式：Table + 展開詳情
- 表格欄位：
  - 指派日期
  - 作業標題（Content 名稱組合）
  - 班級/學生數
  - 狀態分布（圓餅圖）
  - 截止日期（倒數提醒）
  - 完成率（進度條）
  - 平均分數
  - 操作選項

**狀態統計面板**：
- 即時統計卡片：
  - 待繳交：X 人
  - 已繳交：Y 人
  - 已批改：Z 人
  - 已退回：W 人
- 視覺化呈現：
  - 進度環圖
  - 趨勢折線圖
  - 分布長條圖

**篩選與排序**：
- 篩選條件：
  - 作業狀態（進行中/已結束）
  - 班級
  - 日期範圍
  - 完成率區間
- 排序選項：
  - 截止日期（預設）
  - 建立日期
  - 完成率
  - 平均分數

**批量操作**：
- 延長截止日期
- 發送提醒通知
- 匯出成績報表
- 封存舊作業

**學生端作業列表**

**介面設計**：
- 顯示格式：卡片式佈局
- 分類標籤：
  - 待完成（紅色標記）
  - 進行中（黃色標記）
  - 已完成（綠色標記）
  - 需修正（橘色標記）

**作業卡片資訊**：
- 作業標題
- 科目與老師
- 截止倒數（醒目顯示）
- 預估所需時間
- 目前進度（如完成 3/5 個 Content）
- 快速開始按鈕

**智慧提醒**：
- 即將到期提醒（24小時前）
- 建議開始時間（基於歷史資料）
- 最佳練習時段推薦

#### 3.2.5 批改系統 (GradingDashboard)

**批改流程**
1. **進入班級詳情頁**
   - 從側邊欄選擇「我的班級」
   - 點擊特定班級進入詳情頁

2. **查看作業列表**
   - 切換到「作業列表」Tab
   - 顯示該班級所有作業（最新在上）
   - 每個作業顯示待批改數量徽章

3. **進入批改介面**
   - 點擊作業的「批改」按鈕
   - 進入該作業的批改總覽頁面

4. **批改總覽頁面**
   - 左側：學生列表（顯示每位學生的提交狀態）
   - 右側：當前選中學生的所有 Content
   - 逐個學生、逐個 Content 進行批改

5. **批改單一 Content**
   - 查看學生提交的錄音
   - 查看 AI 評分結果
   - 標記 checked（通過/未通過）
   - 添加個別回饋（選填）

6. **完成批改**
   - 所有 Content 都查看後
   - 決定整體狀態：GRADED（通過）或 RETURNED（退回）
   - 添加總評（選填）
   - 儲存並進入下一位學生

**錄音集作業批改**
- **作業總覽顯示**：
  - 派發日期 / 截止日期
  - 課程-作業標題
  - 作業類型：錄音
  - 繳交人數：X/Y
  - 批改數量：X/Y

- **學生列表統計**：
  - 待批改文本數
  - 已訂正文本數
  - 待訂正文本數
  - 待完成文本數
  - 批改完畢文本數

- **批改 Modal 介面**：
  - 頂部資訊：學生名、課程-作業標題、截止日
  - 控制區：
    - 快速播放全部按鈕
    - 重新播放按鈕
    - AI 給評按鈕
    - 手動給評/AI 給評切換
    - 送出按鈕
  - 文本列表：
    - 全選訂正 checkbox
    - 各文本獨立訂正 checkbox
    - 播放控制區
    - 學生前端 AI 評測結果顯示
  - 訂正功能：可將特定文本打回重練

**批改介面設計**

**整體佈局**：
- 左側：學生列表（可收合）
  - 顯示批改狀態圖示
  - 快速跳轉功能
  - 進度指示器
- 中間：主要批改區域
  - 學生資訊頭部
  - Content 內容展示
  - 學生提交內容
  - 評分工具列
- 右側：AI 輔助面板
  - AI 評分建議
  - 常用評語模板
  - 歷史批改記錄

**朗讀評測批改流程**：
1. **學生答案呈現**：
   - 原文與錄音對照顯示
   - 波形圖視覺化
   - 播放控制（變速播放）
   - 逐句對照模式

2. **AI 評分顯示**：
   - WPM（每分鐘字數）
   - 準確率（Accuracy）
   - 流暢度（Fluency）
   - 發音評分（Pronunciation）
   - 具體錯誤標記

3. **教師調整工具**：
   - 分數調整滑桿（0-100）
   - 加減分快捷按鈕
   - 評分理由說明

4. **回饋編輯器**：
   - 富文本編輯器
   - 評語模板插入
   - 語音評語錄製
   - 鼓勵貼圖選擇

5. **修正要求功能**：
   - 勾選需要重做的項目
   - 設定修正說明
   - 新截止日期設定

**批改效率工具**：
- **快捷鍵支援**：
  - Space：播放/暫停
  - ←→：上/下一位學生
  - 1-5：快速評分
  - Enter：確認送出

- **批量操作**：
  - 套用相同分數
  - 複製評語到多位學生
  - 一鍵通過所有及格者

- **智慧輔助**：
  - 基於歷史資料的評分建議
  - 異常偵測（分數過高/過低警示）
  - 相似錯誤自動群組

**口說集作業批改**
- **自動批改流程**：
  - 學生完成作業當下，AI 直接批改
  - 記錄 AI 回覆、學生回答、優化建議
  - 自動生成個人化錄音集作業（無需教師手動派發）

- **批改介面顯示**：
  - 派發日期 / 截止日期
  - 課程-作業標題
  - 作業類型：口說
  - 繳交人數：X/Y
  - 批改數量：X/Y（通常為自動完成）

- **學生詳細檢視**：
  - 搜尋或選擇特定學生
  - 顯示對話過程：
    - AI 回覆內容
    - 學生回答內容
    - 優化學生回答的建議
    - 自動生成的後續練習

#### 3.2.6 統計分析 (Statistics)

**班級整體分析**
- 平均 WPM 趨勢圖
- 準確率分布圖
- 達標率統計
- 活躍度分析

**個人學習報告**
- 學習曲線圖表
- 強弱項分析
- 進步率計算
- 練習頻率統計

**作業完成分析**
- 準時繳交率
- 平均完成時間
- 各類型活動表現
- 改善建議

### 3.3 學生端功能

#### 3.3.1 作業列表 (Assignments)

**作業顯示**
- 依派發時間排序（新到舊）
- 作業卡片顯示：
  - 作業標題
  - 活動類型圖示
  - 截止時間倒數
  - 完成狀態標記
- 無作業時顯示「恭喜你！目前沒有作業」

**作業分類**
- 待完成作業
- 已完成作業
- 已過期作業

#### 3.3.2 練習介面

**通用功能**
- 練習前說明
- 目標值顯示
- 計時器（如有時限）
- 暫停/繼續功能
- 放棄練習確認

**各類型練習特色**
- **朗讀評測**：
  - 錄音介面
  - 即時音量顯示
  - 重錄功能
  - 結果即時顯示

- **聽力填空**：
  - 音檔播放控制
  - 填空作答介面
  - 提示功能
  - 答案檢查

- **造句練習**：
  - 目標單字高亮
  - 字數計算
  - 範例參考
  - 語法檢查提示

### 3.4 資料管理功能（Phase 1）

#### 3.4.1 匯入匯出
- **學生資料匯入**：
  - 支援 CSV 格式（姓名,學號,生日）
  - 批量新增學生到班級
  - 重複檢查與錯誤提示

- **成績匯出**：
  - 匯出班級成績報表
  - 支援 CSV/Excel 格式
  - 包含個人和班級統計

#### 3.4.2 資料備份
- 教師資料定期備份
- 學生成績記錄保存
- 課程內容版本管理

### 3.5 通知系統

#### 3.5.1 教師通知
- **通知類型**：
  - 學生未達標警示
  - 作業完成通知
  - 系統公告
  - 家長訊息

- **通知管理**：
  - 未讀標記
  - 重要度分級
  - 詳細內容查看
  - 批次標記已讀

#### 3.5.2 學生通知（規劃中）
- 新作業通知
- 成績公布通知
- 教師評語通知
- 系統提醒

### 3.6 資料管理功能

#### 3.6.1 匯入匯出
- **支援格式**：
  - CSV（學生資料、成績）
  - Excel（報表匯出）
  - PDF（成績單、報告）

- **匯入驗證**：
  - 格式檢查
  - 必填欄位驗證
  - 資料衝突處理
  - 匯入預覽確認

#### 3.6.2 資料備份
- 自動備份機制
- 手動備份功能
- 資料還原
- 版本管理

## 四、使用者體驗設計

### 4.1 介面設計原則
- **一致性**：統一的操作模式和視覺風格
- **直覺性**：符合使用者心智模型
- **回饋性**：即時的操作回饋
- **容錯性**：友善的錯誤處理

### 4.2 響應式設計
- **桌面版**：完整功能展現
- **平板版**：優化的觸控操作
- **手機版**：簡化的核心功能

### 4.3 無障礙設計
- 鍵盤導航支援
- 螢幕閱讀器相容
- 高對比模式
- 字體大小調整

## 五、系統整合與擴展

### 5.1 第三方整合
- **Google Workspace**：行事曆、雲端硬碟
- **LINE**：訊息通知
- **YouTube**：教學影片嵌入

### 5.2 API 開放（規劃中）
- RESTful API
- Webhook 支援
- 開發者文件
- API 金鑰管理

### 5.3 擴展功能規劃
- **家長端 App**：
  - 查看孩子學習進度
  - 接收成績通知
  - 與教師溝通

- **AI 教學助理**：
  - 自動作業建議
  - 學習路徑規劃
  - 弱點加強建議

- **遊戲化元素**：
  - 成就系統
  - 排行榜
  - 虛擬獎勵

## 六、API 功能規格（Phase 1）

### 6.1 教師 CRUD API

#### 班級管理 API
- **CREATE** `POST /api/teachers/classrooms`
  - 建立新班級
  - 必填：name, level
  - 選填：description

- **READ** `GET /api/teachers/classrooms/{id}`
  - 取得單一班級詳情
  - 包含學生列表

- **UPDATE** `PUT /api/teachers/classrooms/{id}`
  - 更新班級資訊
  - 可更新：name, description, level

- **DELETE** `DELETE /api/teachers/classrooms/{id}`
  - 軟刪除班級（設定 is_active = False）

- **LIST** `GET /api/teachers/classrooms`
  - 列出教師所有班級

#### 學生管理 API
- **CREATE** `POST /api/teachers/students`
  - 新增單一學生
  - 必填：name, email, birthdate, classroom_id
  - 選填：student_id
  - 自動產生預設密碼（生日格式）

- **BATCH CREATE** `POST /api/teachers/classrooms/{id}/students/batch`
  - 批量新增學生到特定班級
  - 支援 CSV 格式資料

- **READ** `GET /api/teachers/students/{id}`
  - 取得單一學生資料
  - 包含密碼狀態但不包含實際密碼

- **UPDATE** `PUT /api/teachers/students/{id}`
  - 更新學生資訊
  - 可更新：name, student_id, target_wpm, target_accuracy
  - 不可更新：password（需透過專門的密碼重設流程）

- **DELETE** `DELETE /api/teachers/students/{id}`
  - 軟刪除學生（設定 is_active = False）

#### 課程管理 API
- **CREATE** `POST /api/teachers/programs`
  - 建立新課程
  - 必填：name, level, classroom_id
  - 選填：description, estimated_hours
  - 自動分配 order_index

- **READ** `GET /api/teachers/programs/{id}`
  - 取得單一課程詳情
  - 包含 Lesson 列表（按 order_index 排序）
  - 包含每個 Lesson 的 Content 列表

- **UPDATE** `PUT /api/teachers/programs/{id}`
  - 更新課程資訊
  - 可更新：name, description, estimated_hours, level

- **DELETE** `DELETE /api/teachers/programs/{id}`
  - 刪除課程及其所有單元和內容

- **REORDER** `PUT /api/teachers/programs/reorder`
  - 重新排序課程（拖曳功能）
  - 接受課程 ID 和新的 order_index 陣列

- **LIST** `GET /api/teachers/programs`
  - 列出教師所有課程
  - 包含 lesson_count 和 student_count 統計

#### 單元管理 API
- **CREATE** `POST /api/teachers/programs/{id}/lessons`
  - 為課程新增單元
  - 必填：name
  - 選填：description, estimated_minutes
  - 自動分配 order_index

- **UPDATE** `PUT /api/teachers/lessons/{id}`
  - 更新單元資訊
  - 可更新：name, description, estimated_minutes

- **DELETE** `DELETE /api/teachers/lessons/{id}`
  - 刪除單元及其所有內容

- **REORDER** `PUT /api/teachers/programs/{id}/lessons/reorder`
  - 重新排序單元（拖曳功能）
  - 接受單元 ID 和新的 order_index 陣列

#### 內容管理 API
- **CREATE** `POST /api/teachers/lessons/{id}/contents`
  - 為單元新增內容
  - 必填：type, title, items（朗讀項目陣列）
  - 選填：description
  - items 格式：`[{text: string, translation?: string}]`
  - 自動分配 order_index

- **READ** `GET /api/teachers/contents/{id}`
  - 取得單一內容詳情
  - 包含所有朗讀項目

- **UPDATE** `PUT /api/teachers/contents/{id}`
  - 更新內容資訊
  - 可更新：title, description, items

- **DELETE** `DELETE /api/teachers/contents/{id}`
  - 刪除內容及相關資源

#### 輔助功能 API
- **TRANSLATE** `POST /api/teachers/translate`
  - 翻譯英文文本為中文
  - 輸入：`{text: string}`
  - 輸出：`{translation: string}`
  - 使用 OpenAI API

- **TTS BATCH** `POST /api/teachers/tts/batch`
  - 批量生成語音檔案
  - 輸入：`{texts: string[]}`
  - 輸出：`{audio_urls: string[]}`
  - 使用 OpenAI TTS API

### 6.2 資料驗證規則

#### 學生資料驗證
- **Email**：必須唯一，格式驗證
- **生日**：YYYY-MM-DD 格式，用於產生預設密碼
- **密碼**：
  - 預設：生日轉換為 YYYYMMDD
  - 更改後：最少 8 位，需包含英數字

#### 班級資料驗證
- **班級名稱**：最多 50 字元
- **等級**：必須為預定義值之一（preA, A1, A2, B1, B2, C1, C2）
- **班級人數**：最多 50 人

#### 課程資料驗證
- **課程名稱**：最多 100 字元
- **單元數量**：建議不超過 20 個
- **Content 驗證**：
  - 標題（title）：必填，最多 200 字元
  - 描述（description）：選填
  - 朗讀項目（items）：3-15 個項目
  - 每個項目文本：最多 500 字元

## 七、技術規格與限制

### 7.1 系統需求
- **瀏覽器**：Chrome 90+、Firefox 88+、Safari 14+、Edge 90+
- **網路**：穩定的網路連線（建議 10Mbps 以上）
- **裝置**：支援麥克風的裝置（口說練習必需）

### 7.2 效能指標
- 頁面載入時間：< 2 秒
- API 回應時間：< 200ms
- 音訊處理延遲：< 500ms
- 並發用戶支援：1000+

### 7.3 資料限制
- 單次 CSV 匯入：最多 500 筆
- 錄音長度：最長 5 分鐘
- 檔案大小：最大 50MB
- 班級人數：最多 50 人

### 7.4 安全性要求
- HTTPS 加密傳輸
- 資料隱私保護
- 定期安全更新
- 操作日誌記錄

## 八、專案里程碑

### Phase 1：個體教師版（進行中）
- ✅ 教師 Email 註冊/登入
- ✅ 班級建立與管理（CRUD API 完成）
- ✅ 學生新增（單筆/批量）
- ✅ 學生密碼管理系統（生日作為預設密碼）
- ✅ 三層課程架構（Program → Lesson → Content）
- ✅ 課程 CRUD API（完整建立、更新、刪除）
- ✅ 教師 Sidebar 導航系統
- ✅ Table 格式檢視（班級、學生、課程）
- ✅ 班級詳情頁面（班級內管理學生和課程）
- ✅ 拖曳重新排序功能（課程和單元）
- ✅ Content CRUD API（建立、更新、刪除內容）
- ✅ Content 建立編輯介面（在班級詳情頁）
- ✅ 翻譯 API 整合（OpenAI）
- ✅ TTS API 整合（批量語音生成）
- □ 作業派發系統（開發中）
  - □ Phase 1：基礎指派功能
  - □ Phase 2：作業列表管理
  - □ Phase 3：AI 自動批改
  - □ Phase 4：人工批改功能
  - □ Phase 5：進階功能
- ✅ 學生登入流程
- □ 作業練習介面
- □ AI 語音評分
- □ 基礎批改功能
- □ 簡單統計報表

### Phase 2：擴展功能（規劃中）
- □ 機構/學校管理系統
- □ 多種活動類型（口說、聽力等）
- □ 家長功能
- □ 進階統計分析
- □ 通知系統完善

### Phase 3：智能化升級（未來）
- □ AI 學習路徑
- □ 自適應練習
- □ 智能批改
- □ 預測分析


## 十一、作業系統實施計畫（新架構 - 2025年9月更新）

### 11.1 資料遷移計畫

#### 現有資料分析
- 目前有 95 筆 StudentAssignment 記錄（舊結構）
- 這些記錄使用組合 ID：`{content_id}_{classroom_id}`
- 需要遷移到新的 Assignment 架構

#### 遷移策略
1. **Phase 1：建立新表結構**
   - 建立 Assignment 表
   - 建立 AssignmentContent 表
   - 建立 StudentContentProgress 表
   - 更新 StudentAssignment 加入 assignment_id

2. **Phase 2：資料遷移**
   ```sql
   -- 為每個唯一的 content_id + classroom_id 組合建立 Assignment
   INSERT INTO assignments (title, classroom_id, teacher_id, assign_to_all, is_active)
   SELECT DISTINCT
     sa.title,
     sa.classroom_id,
     c.teacher_id,
     true,  -- 預設為全班
     true
   FROM student_assignments sa
   JOIN classrooms c ON c.id = sa.classroom_id;

   -- 建立 AssignmentContent 關聯
   -- 更新 StudentAssignment 的 assignment_id
   ```

3. **Phase 3：驗證與清理**
   - 確認所有舊資料都已正確遷移
   - 保留舊欄位一段時間以防回滾需要

### 11.2 階段性開發規劃

#### Phase 1：資料模型建立（已完成）
**目標**：建立新的作業系統資料結構

**完成項目**：
- ✅ Assignment 模型設計
- ✅ AssignmentContent 關聯表
- ✅ StudentContentProgress 進度追蹤
- ✅ 統一使用 is_active 軟刪除

#### Phase 2：Migration 建立（進行中）
**目標**：建立資料庫 migration 並遷移現有資料

**待完成**：
```python
# Alembic migration 檔案
# 建立新表結構
# 遷移現有 95 筆資料
# 設定外鍵約束
```

#### Phase 3：API 開發（1週）
**目標**：實作完整的作業 CRUD API

**API 端點規劃**：
- `POST /api/assignments` - 建立作業（支援多內容）
- `GET /api/assignments` - 查詢作業列表
- `GET /api/assignments/{id}` - 取得作業詳情
- `PUT /api/assignments/{id}` - 編輯作業
- `DELETE /api/assignments/{id}` - 軟刪除作業
- `GET /api/assignments/{id}/students` - 取得學生完成狀態
- `POST /api/assignments/{id}/assign` - 指派給特定學生

#### Phase 4：前端整合（1週）
**目標**：整合新的作業系統到前端介面

**開發項目**：
- 作業建立精靈（支援多內容選擇）
- 作業列表顯示（含統計資訊）
- 作業詳情 Modal（含學生完成儀表板）
- 編輯作業功能（在詳情 Modal 內）
- 刪除作業確認

#### Phase 5：測試與優化（1週）
**目標**：確保系統穩定性和效能

**測試項目**：
- 單元測試：模型驗證、業務邏輯
- 整合測試：API 端點測試
- E2E 測試：完整作業流程
- 效能測試：批量作業建立、查詢效能

### 11.3 技術實施細節

#### 資料庫索引設計
```sql
-- 提升查詢效能的索引
CREATE INDEX idx_assignments_classroom_id ON assignments(classroom_id);
CREATE INDEX idx_assignments_teacher_id ON assignments(teacher_id);
CREATE INDEX idx_student_assignments_student_id ON student_assignments(student_id);
CREATE INDEX idx_student_assignments_assignment_id ON student_assignments(assignment_id);
CREATE INDEX idx_assignment_contents_assignment_id ON assignment_contents(assignment_id);
CREATE INDEX idx_student_content_progress_student_assignment_id ON student_content_progress(student_assignment_id);
```

#### API 回應格式規範
```typescript
// 作業列表回應
interface AssignmentListResponse {
  assignments: Assignment[];
  pagination: {
    total: number;
    page: number;
    pageSize: number;
  };
  statistics: {
    totalAssignments: number;
    pendingGrading: number;
    averageCompletionRate: number;
  };
}

// 學生完成狀態回應
interface StudentProgressResponse {
  studentId: number;
  studentName: string;
  status: AssignmentStatus;
  contentProgress: {
    contentId: number;
    contentTitle: string;
    status: AssignmentStatus;
    score?: number;
    completedAt?: string;
  }[];
  totalScore?: number;
  feedback?: string;
}
```

## 十二、結論

Duotopia 致力於打造最適合台灣學生的英語學習平台，透過完整的功能設計、友善的使用介面、以及強大的 AI 技術，協助教師提升教學效率，幫助學生快樂學習。本 PRD 將持續更新，以反映產品發展的最新狀態。

---
*文件版本：4.0*
*最後更新：2025年8月*
*重點：Phase 1 個體教師版*
