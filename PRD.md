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

### 1.3 核心價值（Phase 1）
- **簡單易用**：教師可快速上手，無需複雜設定
- **核心功能完整**：班級、學生、課程、作業的完整管理
- **AI 智能評分**：提供即時、客觀的語音評估
- **獨立運作**：不依賴機構或學校架構

### 1.4 目標用戶（Phase 1）
- **主要用戶**：獨立英語教師（家教、補習班個體戶）
- **次要用戶**：6-15歲學生

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

#### 作業與評量
- **StudentAssignment**：學生作業
- **AssignmentSubmission**：作業提交
- **ActivityResult**：活動結果記錄

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

#### 3.2.3 作業派發系統 (AssignHomework)

**五步驟派發流程**：
1. **選擇課程**：從已建立的課程中選擇
2. **選擇課文**：選擇要作為作業的活動
3. **選擇班級**：可多選班級
4. **選擇學生**：
   - 支援全選/取消全選
   - 個別勾選
   - 顯示學生當前作業負擔
5. **設定詳情**：
   - 作業標題（自動帶入）
   - 作業說明（選填）
   - 派發時間（立即/預約）
   - 繳交期限
   - 是否允許遲交

**作業管理功能**
- 查看作業派發記錄
- 修改作業期限
- 撤回未開始的作業
- 複製作業設定

#### 3.2.4 批改系統 (GradingDashboard)

**批改流程**
1. 選擇班級管理
2. 選擇特定班級
3. 顯示班級所有作業（最新作業在上）
4. 選擇某份作業
5. 批改作業或觀看 AI 批改結果

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

#### 3.2.5 統計分析 (Statistics)

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
- □ 作業派發系統
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

## 九、成功指標

### 8.1 技術指標
- 系統可用性：> 99.9%
- 錯誤率：< 0.1%
- 用戶滿意度：> 4.5/5

### 8.2 業務指標
- 教師採用率：> 80%
- 學生活躍率：> 70%
- 作業完成率：> 85%
- 家長參與率：> 60%

### 8.3 學習成效
- 平均 WPM 提升：> 20%
- 準確率提升：> 15%
- 學習動機提升：> 30%

## 十、風險管理

### 9.1 技術風險
- Base44 平台依賴性
- 瀏覽器相容性
- 網路穩定性要求

### 9.2 使用風險
- 教師培訓需求
- 學生適應期
- 家長配合度

### 9.3 營運風險
- 資料安全性
- 系統擴展性
- 成本控制

## 十一、結論

Duotopia 致力於打造最適合台灣學生的英語學習平台，透過完整的功能設計、友善的使用介面、以及強大的 AI 技術，協助教師提升教學效率，幫助學生快樂學習。本 PRD 將持續更新，以反映產品發展的最新狀態。

---
*文件版本：4.0*  
*最後更新：2025年8月*  
*重點：Phase 1 個體教師版*