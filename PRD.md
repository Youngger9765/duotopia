# Duotopia 產品需求文件 (PRD) v5.0

## 📋 文件資訊
- **版本**: 5.0
- **最後更新**: 2025-12-06
- **當前狀態**: Phase 1 MVP 完成，Phase 1.5 優化進行中
- **下一里程碑**: Phase 2 擴展功能

## 一、產品概述

### 1.1 產品定位
Duotopia 是一個以 AI 驅動的多元智能英語學習平台，專為國小到國中學生（6-15歲）設計。透過語音辨識、即時回饋和遊戲化學習，幫助學生提升英語口說能力。

**Phase 1 定位**：專注於個體教師版本，讓獨立教師能夠：
- 建立並管理自己的班級
- 新增學生並管理學習進度
- 建立課程內容
- 派發作業給學生
- 批改作業並追蹤成效
- 管理訂閱與配額使用

### 1.2 當前開發狀態 (更新於 2025-12-06)

#### 版本狀態
- **Phase 1 MVP**: ✅ 100% 完成
- **Phase 1.5 優化**: 🔄 進行中 (70% 完成)
- **下一階段**: Phase 2 擴展功能

#### 技術棧
**前端**：
- React 18 + Vite 5
- TypeScript 5.3
- Tailwind CSS + Radix UI (shadcn/ui)
- React Router v6
- i18next (多語言支援)
- MediaRecorder API (瀏覽器原生錄音)

**後端**：
- Python 3.11
- FastAPI 0.109+
- SQLAlchemy 2.0 (ORM)
- Alembic (資料庫遷移)
- Pydantic v2 (資料驗證)

**資料庫**：
- PostgreSQL 15 (Supabase 託管)
- Row Level Security (RLS) 啟用
- 免費層配置 (500MB 資料 + 2GB 頻寬/月)

**AI 服務**：
- **Azure Speech Services**: 語音辨識與發音評分
  - Region: eastasia
  - Features: Pronunciation Assessment, Real-time STT
- **OpenAI API**: 翻譯與 TTS
  - GPT-4 Turbo: 英中翻譯
  - TTS-1: 文字轉語音

**金流服務**：
- **TapPay**: 信用卡支付處理
  - 已開通正式環境 (Production)
  - 已開通電子發票服務
  - PCI DSS Level 1 合規

#### 部署環境
**Production (正式環境)**：
- URL: `https://duotopia-frontend-xxx.run.app`
- Platform: Google Cloud Run (asia-east1)
- 資源: 1 CPU + 1GB RAM
- Auto-scaling: 0-6 實例
- 資料庫: Supabase Production
- 環境: `ENVIRONMENT=production`
- TapPay: Production 模式

**Staging (測試環境)**：
- URL: `https://duotopia-staging-frontend-xxx.run.app`
- Platform: Google Cloud Run (asia-east1)
- 資源: 1 CPU + 256MB RAM
- Auto-scaling: 0-3 實例
- 資料庫: Supabase Staging
- 環境: `ENVIRONMENT=staging`
- TapPay: Production 模式 (測試真實刷卡)

**Per-Issue Preview (PR 預覽環境)**：
- 自動部署: 推送到 `claude/issue-XX` 或 `fix/issue-XX` 分支時
- URL Pattern: `https://duotopia-preview-issue-{N}-frontend-xxx.run.app`
- 自動清理: Issue 關閉時自動刪除資源
- 用途: PR 審查前的功能驗證

**Local Development (本地開發)**：
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8080`
- 資料庫: Docker PostgreSQL

#### 資源配置與成本優化

**Cloud Run 配置**：
```yaml
Production Backend:
  cpu: 1
  memory: 1Gi
  min-instances: 0
  max-instances: 6
  concurrency: 80
  timeout: 300s

Staging Backend:
  cpu: 1
  memory: 256Mi
  min-instances: 0
  max-instances: 3
  concurrency: 80
  timeout: 300s
```

**成本結構** (2025-12-06):
- 資料庫: $0/月 (Supabase 免費層)
- Cloud Run: ~$5-10/月 (依流量計費)
- Cloud Storage: ~$1/月 (錄音檔案儲存)
- Cloud Scheduler: $0.10/月 (每日帳單監控)
- **總計**: ~$6-11/月

**成本控制措施**：
- ✅ min-instances=0 (無流量時零成本)
- ✅ 自動清理 Per-Issue 環境
- ✅ 定期清理舊 Docker 映像 (保留最新 2 個版本)
- ✅ 每日帳單監控與警報 (預算 $30/月)
- ✅ Rate Limiting (防止異常高頻請求)

### 1.3 目標用戶（Phase 1）
- **教師**：獨立英語教師、補習班教師
- **學生**：6-15歲學生 (國小到國中)

### 1.4 使用者價值與目標（User Value）
- **教師價值**：用最少時間建立課程與作業、快速掌握班級/學生進度、以清楚的批改流程提升教學效率。
- **學生價值**：清楚知道要做什麼、錄完即有回饋、容易持續完成練習並看到進步。
- **成功定義（MVP）**：單一教師可在一天內完成「建立班級 → 新增學生 → 建立內容 → 指派作業 → 學生完成 → 教師批改」的閉環。
  - ✅ **狀態**: 閉環已完成！(2025-09-12 達成)

### 1.5 教師訂閱與付費機制

#### 1.5.1 訂閱系統概述
Duotopia 採用簡化的訂閱制度，確保教師能持續使用平台功能：

#### 1.5.2 註冊與驗證流程
1. **教師註冊**：填寫基本資料（姓名、Email、密碼）
2. **Email 驗證**：系統發送驗證信到教師 Email
3. **帳號啟用**：點擊驗證連結後，帳號正式啟用
4. **30 天試用**：驗證成功後，自動獲得 30 天免費使用期

#### 1.5.3 訂閱狀態管理
- **啟用狀態**：email 驗證前無法使用任何功能
- **試用期**：30 天免費使用，可使用所有核心功能
- **過期狀態**：試用期結束後，無法指派新作業但可查看現有內容
- **付費狀態**：充值後恢復所有功能使用權限

#### 1.5.4 充值機制
1. **充值單位**：每次充值 30 天使用期
2. **多次充值**：可一次購買多個 30 天（如：90 天 = 3 個月）
3. **累積計算**：新充值天數會加到現有剩餘天數上
4. **彈性付費**：教師可依需求選擇充值月數

#### 1.5.5 儀表板顯示
教師儀表板必須清楚顯示：
- 📅 **剩餘天數**：距離訂閱到期還有幾天
- 📊 **訂閱狀態**：試用中/已付費/已過期
- 💳 **充值按鈕**：快速進行訂閱延長
- ⚠️ **到期提醒**：剩餘 7 天時顯示續費提醒

#### 1.5.6 功能限制規則
- **試用期間**：所有功能正常使用
- **過期後限制**：
  - ❌ 無法指派新作業
  - ❌ 無法創建新班級
  - ❌ 無法新增學生
  - ✅ 可查看現有班級和學生
  - ✅ 可批改已提交的作業

#### 1.5.7 配額系統 (Quota System)

**配額機制概述**：
- 每次付款創建一個訂閱週期 (SubscriptionPeriod)
- 每個週期包含固定配額（以秒為單位）
- 配額用於記錄學生使用 AI 功能的消耗
- **重要**：配額超限不阻擋學生學習（業務優先）

**配額方案**：
- **Tutor Teachers**：NT$330/月 → 10,000 點配額
- **School Teachers**：NT$660/月 → 25,000 點配額

**配額扣除規則**：
- **語音錄音**：1 秒 = 1 點
- **文字批改**：1 字 = 0.1 點（500 字 = 50 點）
- **圖片批改**：1 張 = 10 點

**配額使用場景**：
- ✅ **學生錄音**：扣除配額（記錄在老師帳下）
- ✅ **AI 評分**：扣除配額
- ❌ **派作業**：不扣配額（只檢查訂閱狀態）
- ❌ **老師批改**：不扣配額

**配額超限處理**：
- **學生仍可使用**：配額用完時，學生仍可提交作業
- **記錄超額使用**：完整記錄超額使用量
- **提醒老師升級**：配額使用率 > 80% 時顯示提醒

**配額與訂閱關係**：
- 訂閱控制「能否派作業」
- 配額記錄「學生使用量」
- 訂閱過期 → 無法派作業，學生也無法使用
- 配額用完 → 可以派作業，學生仍可使用（允許超額）

---

#### 1.5.8 TapPay 金流整合

**支付方案**：
- **Tutor Teachers**：NT$330/月
- **School Teachers**：NT$660/月

**TapPay 負責處理**：
- 信用卡資料安全（PCI DSS Level 1 合規）
- 支付處理和銀行溝通
- 電子發票開立與管理（✅ 已開通電子發票服務）
- 風險控管和盜刷偵測

**我們負責處理**：
- 訂閱狀態管理和功能權限控制
- 交易記錄和稽核追蹤
- 用戶介面和支付流程整合
- 通過 TapPay API 查詢發票資訊
- 配額管理與使用量追蹤

**整合狀態** (2025-12-06):
- ✅ Production 環境已上線
- ✅ 支援信用卡支付
- ✅ 電子發票自動開立
- ✅ 前後端環境變數正確配置
- ✅ Sandbox 和 Production 環境分離

### 1.6 使用者情境（Key Scenarios）
- 教師（剛加入）：用 Demo 帳號或註冊後，10 分鐘內完成首批作業指派給一個班級。
- 教師（日常運營）：每週建立 1-2 次作業，查看完成率與逾期名單，針對部分學生退回訂正。
- 學生（第一次登入）：透過 URL 參數快速登入，開始朗讀，錄完即看回饋並自動保存。
- 學生（回家練習）：可斷點續做、重錄最佳化；完成後查看老師回饋，必要時按指示訂正。

### 1.7 User Stories 與驗收標準（摘錄）

#### 教師核心功能
- 教師：我能從課程樹多選內容，一次指派給整個班級或個別學生（✅ 驗收：可多選、可全選、可設定截止日、指派後作業出現在學生端）。
- 教師：我能在作業總覽看到每位學生的狀態與完成率（✅ 驗收：分佈統計與完成率百分比正確）。
- 教師：我能批改並退回需修正的內容（✅ 驗收：學生端顯示需修正標記並可重做）。
- 教師：我能分享課程內容給其他班級使用（✅ 驗收：作業-課程內容分離機制完成）。

#### 學生核心功能
- 學生：我能看到清楚的作業列表與進度標記（✅ 驗收：作業卡片顯示狀態、完成數/總數、截止日提醒）。
- 學生：我能逐句錄音並即時保存（✅ 驗收：頁面刷新後不丟失進度，可重錄覆蓋）。
- 學生：我能在完成所有內容後提交，狀態變為已提交（✅ 驗收：教師端同步顯示待批改）。
- 學生：我可以透過教師分享的 URL 快速登入（✅ 驗收：URL 參數自動填入教師 email 和班級 ID）。

#### 訂閱與付費功能
- 教師：我在註冊後必須驗證 Email 才能使用（✅ 驗收：未驗證時無法使用任何功能，顯示驗證提醒）。
- 教師：我驗證成功後自動獲得 30 天試用期（✅ 驗收：顯示剩餘天數，所有功能可正常使用）。
- 教師：我能在儀表板清楚看到訂閱狀態和剩餘天數（✅ 驗收：顯示剩餘天數、訂閱狀態、充值按鈕）。
- 教師：我在試用期過期後無法建立新作業但可查看現有內容（✅ 驗收：創建按鈕被禁用，現有資料仍可檢視）。
- 教師：我能透過 TapPay 充值延長使用期限（✅ 驗收：充值後剩餘天數正確增加）。
- 教師：我能選擇充值多個月份（✅ 驗收：可選擇 1-12 個月，價格正確計算）。

#### 配額管理功能
- 教師：我能在儀表板看到配額使用狀況（✅ 驗收：顯示已使用/總配額、使用百分比）。
- 教師：我能查看配額使用明細（✅ 驗收：顯示學生、作業、功能類型、消耗點數）。
- 教師：配額用完時學生仍可提交作業（✅ 驗收：配額超限不阻擋學生使用）。
- 教師：配額使用率 > 80% 時收到提醒（✅ 驗證：顯示升級方案建議）。
- 系統：每次付款創建新的配額週期（✅ 驗收：quota_used 歸零，quota_total 正確設定）。

### 1.8 Roadmap（以使用者價值為主）
- **Phase 1（MVP）** - ✅ 100% 完成：
  - 單教師閉環：班級/學生/內容管理、作業指派、學生完成、教師批改/退回
  - 朗讀評測活動（reading_assessment）與 AI 即時評分（Azure Speech API）
  - 學生 Email 驗證為選配管理工具（不影響登入）
  - ✅ 教師訂閱系統：Email 驗證 + 30 天試用 + TapPay 充值續費機制
  - ✅ 配額系統：訂閱週期配額管理，超額使用追蹤
  - ✅ Safari 瀏覽器相容性修復
  - ✅ 作業-課程內容分離機制（Issue #56）

- **Phase 1.5（提升易用性與穩定性）** - 🔄 70% 完成：
  - ✅ 學生 URL 快速登入（教師分享連結）
  - ✅ AI 自動評分與分數回填機制
  - ✅ 錄音錯誤監控與每日報告
  - ✅ 全局 Rate Limiting（防止異常高頻請求）
  - ✅ 成本優化（Cloud Run 資源調整）
  - 🔄 作業複製功能（規劃中）
  - 🔄 截止日批量延長（規劃中）
  - 🔄 完成率/逾期提醒優化（規劃中）
  - 🔄 教師通知面板（規劃中）

- **Phase 2（內容擴展）** - 未來：
  - 活動類型擴充（情境對話、聽力填空等）
  - 校方/機構多角色管理
  - 多教師協作功能
  - 學習進度視覺化圖表

- **Phase 3（智慧化輔助）** - 未來：
  - 深度 AI 批改與個人化建議
  - 學習路徑推薦
  - 報告自動化生成

### 1.9 KPI 與成功指標（Phase 1）
- 教師激活：新教師完成首個作業指派比例 ≥ 60%。
- 完成率：被指派學生中，作業完成比例 ≥ 70%。
- 首次指派用時：新教師從登入到完成首次指派 ≤ 10 分鐘（P50）。
- 退回訂正循環：被退回後重新提交比例 ≥ 80%。
- 留存：被指派後一週內再次登入/練習的學生比例 ≥ 50%。

## 二、系統架構

### 2.1 技術架構

#### 前端技術棧
- **核心框架**：React 18 + Vite + TypeScript
- **UI 框架**：Tailwind CSS + shadcn/ui (Radix UI 元件)
- **路由**：React Router v6
- **狀態管理**：React Context + Custom Hooks
- **多語言**：i18next + react-i18next (支援繁中/英文)
- **API 通訊**：Fetch API + Custom Hooks
- **錄音功能**：MediaRecorder API (瀏覽器原生)
- **音訊播放**：HTML5 Audio API

#### 後端技術棧
- **核心框架**：FastAPI 0.109+ (Python 3.11)
- **ORM**：SQLAlchemy 2.0
- **資料驗證**：Pydantic v2
- **資料庫遷移**：Alembic
- **認證**：JWT (python-jose)
- **密碼加密**：bcrypt
- **環境變數**：python-dotenv

#### 資料庫與儲存
- **主資料庫**：PostgreSQL 15 (Supabase 託管)
- **Row Level Security**：全面啟用 RLS (所有業務資料表)
- **檔案儲存**：Google Cloud Storage
  - 錄音檔案：`gs://duotopia-audio-files/`
  - TTS 音檔：`gs://duotopia-tts-files/`
- **連線池**：Supabase Pooler (Transaction mode)

#### AI 與第三方服務
- **語音辨識與評分**：Azure Speech Services
  - Pronunciation Assessment
  - Real-time Speech-to-Text
  - Accuracy, Fluency, Completeness 評分
- **翻譯**：OpenAI GPT-4 Turbo
- **TTS**：OpenAI TTS-1
- **金流**：TapPay (Production + Sandbox)
- **Email**：SMTP (Google Workspace)

#### CI/CD 與部署
- **版本控制**：GitHub
- **CI/CD**：GitHub Actions
- **容器化**：Docker (multi-stage builds)
- **映像倉庫**：Google Artifact Registry
- **部署平台**：Google Cloud Run
- **監控**：
  - Cloud Run Metrics
  - Custom Dashboard (錄音錯誤監控)
  - 每日帳單監控 (Cloud Scheduler + Billing API)

### 2.2 核心實體模型（Phase 1）

#### 使用者相關
- **Teacher**：教師實體
  - 基本資料：name, email, password_hash
  - 訂閱資訊：subscription_status, trial_end_date
  - 配額：quota_total, quota_used (當前週期)
  - TapPay：card_token, card_last_four, card_holder_name
  - 權限：is_admin, admin_permissions (JSON)
- **Student**：學生實體
  - 基本資料：name, email, birthdate, student_number
  - 驗證狀態：email_verified, email_verification_token
  - 密碼：password_hash, password_changed
- **TeacherSession**：教師會話管理
- **StudentSession**：學生會話管理

#### 訂閱與配額
- **SubscriptionPeriod**：訂閱週期
  - 週期資訊：start_date, end_date
  - 配額：quota_total, quota_used
  - 付款記錄：payment_id, amount, payment_method
  - 狀態：is_active
- **QuotaUsage**：配額使用記錄
  - 使用資訊：student_id, assignment_id, content_type
  - 消耗量：seconds_used, characters_used, images_used
  - 時間戳：created_at

#### 班級管理
- **Classroom**：班級（使用 Classroom 而非 Class 避免 Python 保留字衝突）
  - 基本資料：name, description, level
  - 關聯：teacher_id
- **ClassroomStudent**：班級學生關聯

#### 課程內容（三層架構）
- **Program**：課程計畫
  - 基本資料：name, description, level
  - 歸屬：teacher_id, classroom_id
  - 複製追蹤：source_from_id (原創 = null)
  - 預估：estimated_hours
  - 排序：order_index

- **Lesson**：課程單元
  - 基本資料：name, description
  - 歸屬：program_id
  - 預估：estimated_minutes
  - 排序：order_index

- **Content**：課程內容
  - 基本資料：title, description, type (ContentType enum)
  - 歸屬：lesson_id
  - **作業副本機制** (Issue #56):
    - `is_assignment_copy`: 是否為作業專用副本
    - `copied_from_id`: 原始課程內容 ID
    - `assignment_id`: 關聯的作業 ID
  - 項目：items (JSON array)
  - 排序：order_index

- **ContentItem**：內容項目（朗讀文本）
  - 文本資料：text (英文), translation (中文)
  - 音訊：audio_url (TTS 生成)
  - 歸屬：content_id
  - 排序：order_index

#### 作業與評量（新架構 - 2025年9月更新）
- **Assignment**：作業主表
  - 基本資料：title, description
  - 歸屬：teacher_id, classroom_id
  - 時間：due_date, created_at, updated_at
  - 狀態：is_active

- **AssignmentContent**：作業-內容關聯表
  - 關聯：assignment_id, content_id
  - 順序：order_index

- **StudentAssignment**：學生作業實例
  - 基本資料：assignment_id, student_id
  - 狀態：status (AssignmentStatus enum)
  - 評分：score (自動計算), ai_assessment (JSON)
  - 回饋：feedback
  - 時間戳：assigned_at, started_at, submitted_at, graded_at

- **StudentContentProgress**：學生-內容進度表
  - 關聯：student_assignment_id, content_id
  - 狀態：status, checked (True/False/None)
  - 評分：score, ai_scores (JSON)
  - 回饋：feedback, ai_feedback
  - 資料：response_data (JSON，含錄音 URL)
  - 時間：started_at, completed_at
  - 順序：order_index, is_locked

- **StudentItemProgress**：學生項目進度
  - 關聯：student_content_progress_id, item_id
  - 錄音：audio_url, audio_duration
  - AI 評分：ai_scores (JSON), completeness_score
  - 狀態：is_completed

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
   - 評估指標：WPM（每分鐘字數）、準確率、流暢度、發音、完整度
   - AI 分析：Azure Speech API 即時評分
   - 文本內容：3-15 句的單字、片語或句子
   - 教師功能：可為每個文本錄製示範音檔（使用 OpenAI TTS）
   - 學生練習：逐句錄音並獲得即時 AI 回饋
   - Safari 相容性：✅ 完整支援 (使用 MediaRecorder API with fallback)

註：其他活動類型規劃於 Phase 2，Phase 1 僅開放朗讀評測。

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
  - Email 驗證（必須完成才能使用）
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
   - ✅ 支援 URL 參數自動填入：`?teacher=xxx@example.com`

2. **選擇班級**
   - 顯示該教師所有班級
   - 學生選擇自己所屬班級
   - ✅ 支援 URL 參數自動填入：`&classroom=123`

3. **選擇姓名並輸入密碼**
   - 從班級學生名單中選擇自己
   - 輸入密碼（預設為生日：YYYYMMDD 格式）
   - 登入成功，進入作業列表

**教師分享功能** (Issue #59):
- ✅ 教師可複製學生登入連結
- ✅ URL 包含教師 email 和班級 ID
- ✅ 學生點擊連結自動填入資訊，只需選擇姓名和輸入密碼
- ✅ 提升學生登入體驗

**Phase 2 擴展**：
- 家長 Email 綁定（已部分實作）
- Email 驗證機制（已實作）
- 歷史記錄快速選擇

#### Email 驗證機制（2025年9月實作）

**設計目標**：
- Email 作為純管理工具，不影響登入流程
- 選擇性功能，不綁定也能正常使用
- 統一驗證把關，確保 email 正確性

**資料模型**：
```
Student 表欄位：
- email: 學生 email（可為系統生成或真實 email）
- email_verified: 是否已驗證（預設 false）
- email_verified_at: 驗證時間
- email_verification_token: 驗證 token
- email_verification_sent_at: 最後發送時間
```

**設計原則**：
- 使用現有的 `student.email` 欄位，不另外建立欄位
- 系統生成的 email 格式：`student_timestamp@duotopia.local`
- 老師可填寫真實 email 取代系統生成的
- 登入方式維持不變（email + 生日）

**功能流程**：

1. **老師端功能**：
   - 建立/編輯學生時可填寫真實 email（選填）
   - 顯示 email 驗證狀態（待驗證/已驗證）
   - 區分系統生成 email 與真實 email

2. **學生端功能**：
   - 登入後顯示 email 驗證狀態
   - 若老師已預填 email，顯示並提示驗證
   - 可自行輸入或修改 email
   - 發送/重發驗證信（5分鐘頻率限制）

3. **驗證流程**：
   - 發送含驗證連結的 HTML email
   - 24小時內有效
   - 點擊連結完成驗證
   - 驗證成功後可接收通知

**Email 用途**（非登入）：
- 學習進度通知
- 作業完成通知
- 每週/月度學習報告
- 重要公告

**安全考量**：
- Token 使用 secrets.token_urlsafe(32) 生成
- Token 一次性使用，驗證後立即清除
- 發送頻率限制防止濫用
- 開發模式下在 console 顯示驗證連結

### 3.2 教師端功能（Phase 1）

#### 教師導航架構（Sidebar Navigation）

**側邊欄功能模組**：
1. **儀表板 (Dashboard)**
   - URL: `/teacher/dashboard`
   - 顯示統計摘要和快速操作入口
   - 訂閱狀態與配額使用顯示
   - 待批改作業提醒

2. **我的班級 (Classrooms)**
   - URL: `/teacher/classrooms`
   - 顯示格式：Table 表格檢視
   - 表格欄位：ID、班級名稱、描述、等級、學生數、課程數、建立時間、操作
   - 點擊班級：進入班級詳情頁面 `/teacher/classroom/{id}`
   - 班級詳情功能：
     - 學生列表（可在班級內新增學生）
     - 課程列表（可在班級內建立課程）
     - 作業管理（指派、批改、統計）
     - 班級設定管理

3. **所有學生 (Students)**
   - URL: `/teacher/students`
   - 顯示格式：Table 表格檢視
   - 表格欄位：ID、學生姓名、學號、Email、班級、密碼狀態、狀態、最後登入、操作
   - 密碼狀態顯示規則：
     - 未更改：顯示「預設密碼」標籤 + 生日格式（如：20120101）
     - 已更改：顯示「已更改」標籤（不顯示實際密碼）
   - 資料來源：真實資料庫資料

4. **所有課程 (Programs)**
   - URL: `/teacher/programs`
   - 顯示格式：Table 表格檢視
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
- Email 驗證（必須完成）
- Demo 帳號可快速體驗

**步驟 2：建立班級**
- 班級名稱設定（如：國小五年級A班）
- 班級程度選擇：preA, A1, A2, B1, B2, C1, C2
- 班級描述（選填）

**步驟 3：新增學生**
- 必填資料：
  - 學生姓名
  - 學號
  - 生日（用作預設密碼，格式：YYYYMMDD）
- 選填資料：
  - Email（可供驗證與接收通知）
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
  - 中文翻譯（選填，可使用 OpenAI 翻譯 API）
- TTS 語音生成（批量生成所有項目的語音，使用 OpenAI TTS-1）

**步驟 5：作業派發**
- 選擇課程計畫 (Program)
- 選擇特定單元 (Lesson)
- 選擇內容 (Content)
- ✅ 自動建立作業專用副本（不影響原始課程內容）
- 選擇班級或個別學生
- 設定截止日期

#### 3.2.1 教師儀表板 (TeacherDashboard)

**訂閱與配額管理**：
- 訂閱狀態顯示（試用中/已付費/已過期）
- 剩餘天數倒數計時
- 配額使用進度條（已使用/總配額）
- 充值按鈕（快速跳轉 TapPay 支付）
- 配額超限提醒（> 80% 使用率）

**課程管理**：
- 建立新課程：設定名稱、描述、難度等級
- 課文管理：
  - 活動類型：Phase 1 僅開放朗讀評測（reading_assessment）
  - 設定活動參數（目標值、時間限制等）
  - 課程順序調整
  - 封存/取消封存功能
  - 課程搜尋與篩選
  - ✅ 課程複製功能（透過作業副本機制）

**Content 管理功能**：
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
  - 翻譯 API：自動翻譯英文句子為中文（OpenAI GPT-4 Turbo）
  - TTS API：批量生成語音檔案（OpenAI TTS-1）
- 編輯面板：點擊 Content 展開右側編輯面板
- 即時儲存：修改後即時更新

**快速操作區**：
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
  - 支援 CSV 格式（姓名,學號,生日,Email）
  - 自動檢測重複資料
  - Email 格式驗證
  - 匯入預覽與錯誤提示
  - 衝突處理選項（跳過/更新/保留）
  - ✅ 修正：不再自動建立假的學生 email (Issue #30)

- **學生資料維護**：
  - 編輯個人資訊
  - 調整學習目標
  - 查看學習記錄
  - 停用/啟用帳號
  - 複製學生登入連結（含 URL 參數）

#### 3.2.3 作業派發系統 (AssignHomework) - 新架構設計

#### 資料模型架構（2025年9月重構）

**核心設計理念**：
- 作業（Assignment）是一個獨立的實體，擁有自己的 ID
- 支援多內容作業（一個作業可包含多個 Content）
- 靈活的指派機制（全班或特定學生）
- 完整的進度追蹤（每個內容的完成狀態）
- ✅ 作業-課程內容分離（Issue #56）：
  - 派作業時自動建立 Content 副本
  - 原始課程內容可繼續編輯，不影響已派發作業
  - 支援同一課程內容派發給多個班級

**資料表關係**：
```
Assignment (作業主表)
    ├── AssignmentContent (作業-內容關聯)
    │   └── Content (課程內容副本)
    │       └── ContentItem (文本項目)
    └── StudentAssignment (學生-作業實例)
        └── StudentContentProgress (學生-內容進度)
            └── StudentItemProgress (學生-項目進度)
```

**關鍵欄位設計**：
1. **Assignment**：
   - `id`：作業唯一識別碼（Primary Key）
   - `title`：作業標題
   - `description`：作業說明
   - `classroom_id`：所屬班級
   - `teacher_id`：建立教師
   - `due_date`：截止日期
   - `start_date`：開始日期（學生在此日期後才能看到作業）
   - `created_at`：建立時間
   - `updated_at`：更新時間
   - `is_active`：軟刪除標記

2. **AssignmentContent**：
   - `assignment_id`：作業 ID（Foreign Key）
   - `content_id`：內容 ID（Foreign Key，指向作業專用副本）
   - `order_index`：內容順序（支援順序學習）

3. **Content** (作業副本機制):
   - `is_assignment_copy`：是否為作業專用副本
   - `copied_from_id`：原始課程內容 ID
   - `assignment_id`：關聯的作業 ID
   - 其他欄位同原始 Content

4. **StudentAssignment**：
   - `id`：學生作業實例 ID
   - `assignment_id`：關聯到 Assignment（Foreign Key）
   - `student_id`：學生 ID
   - `status`：作業狀態（見下方狀態說明）
   - `score`：總分（✅ 自動計算，從 AI 評分結果）
   - `ai_assessment`：AI 評估結果 (JSON)
   - `feedback`：總評
   - `assigned_at`：指派時間
   - `started_at`：首次開始時間
   - `submitted_at`：提交時間（所有 Content 完成）
   - `graded_at`：批改完成時間
   - `is_active`：軟刪除標記

5. **StudentContentProgress**：
   - `student_assignment_id`：學生作業實例 ID
   - `content_id`：內容 ID（指向作業副本）
   - `status`：該內容的完成狀態（使用相同的 AssignmentStatus）
   - `score`：該內容的分數（自動計算）
   - `checked`：教師批改標記（True=通過，False=未通過，None=未批改）
   - `feedback`：該內容的個別回饋
   - `response_data`：學生回答資料（JSON，儲存錄音URL等）
   - `ai_scores`：AI 評分結果（JSON）
   - `ai_feedback`：AI 生成的回饋
   - `started_at`：開始練習時間
   - `completed_at`：完成時間
   - `order_index`：順序索引
   - `is_locked`：是否需要解鎖（Phase 2 支援順序學習）

6. **StudentItemProgress**：
   - `id`：項目進度 ID
   - `student_content_progress_id`：關聯到 StudentContentProgress
   - `item_id`：關聯到 ContentItem
   - `audio_url`：學生錄音 URL (Cloud Storage)
   - `audio_duration`：錄音長度（秒）
   - `ai_scores`：AI 評分結果 (JSON)
     ```json
     {
       "accuracy": 0.95,
       "fluency": 0.88,
       "completeness": 0.92,
       "pronunciation": 0.90,
       "wpm": 120
     }
     ```
   - `completeness_score`：完整度分數（0-100）
   - `is_completed`：是否完成
   - `created_at`：建立時間
   - `updated_at`：更新時間

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

**作業生命週期（教師視角）**：

1. **未指派** → 顯示「指派」按鈕
   - 學生尚未被指派此作業

2. **未開始 (NOT_STARTED)** → 學生已被指派但未開始
   - 作業已指派給學生
   - 學生尚未開始做作業
   - 教師可取消指派

3. **進行中 (IN_PROGRESS)** → 學生正在做作業
   - 學生已開始練習
   - 可能已完成部分內容
   - 教師需確認才能取消指派

4. **待批改 (SUBMITTED)** → 學生已提交，等待教師批改
   - 學生已完成並提交作業
   - ✅ 自動 AI 評分（提交時觸發）
   - ✅ 自動計算總分（從 AI 評分結果）
   - 等待教師批改
   - 教師不可取消指派

5. **待訂正 (RETURNED)** → 教師退回，要求學生訂正
   - 教師已批改並發現需要改進
   - 退回給學生進行訂正
   - 學生需重新練習未通過的內容

6. **待批改(訂正) (RESUBMITTED)** → 學生重新提交訂正後的作業
   - 學生已完成訂正並重新提交
   - 等待教師再次批改
   - 可能需要多次訂正循環

7. **已完成 (GRADED)** → 教師已批改完成
   - 作業已完成所有流程
   - 分數已確定
   - 教師不可取消指派

**狀態流轉規則**：
1. 正常流程：NOT_STARTED → IN_PROGRESS → SUBMITTED → GRADED
2. 需要訂正：SUBMITTED/GRADED → RETURNED → RESUBMITTED → GRADED
3. 可多次訂正：GRADED → RETURNED → RESUBMITTED → GRADED（循環）

**取消指派保護機制**：
- **NOT_STARTED**：可直接取消，刪除相關記錄
- **IN_PROGRESS**：需要教師確認（force=true），執行軟刪除
- **SUBMITTED/GRADED/RETURNED/RESUBMITTED**：完全禁止取消，保護學生成果

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
- 開始日期設定（學生在此日期後才能看到作業）
- 截止日期設定
- 順序學習選項（是否需要按順序完成內容）

#### 作業管理功能

**教師端作業管理**：
1. **建立作業**：從課程樹（Program → Lesson → Content）多選內容，選擇全班或個別學生、設定截止日期與說明，一鍵建立。
   - ✅ 自動建立 Content 副本
   - ✅ 原始課程內容不受影響
2. **編輯作業**：可改標題、說明、截止日；內容列表為保護學生進度不可更動；可快速延長整體截止日。
3. **刪除作業**：軟刪除（保留歷史），不影響已完成評分的記錄可追溯。
4. **複製作業（✅ 已實作）**：快速複製到其他班級或做差異化指派，保留原內容結構。
5. **查詢/總覽**：依班級、狀態、時間篩選；顯示完成率、平均分數與緊急度排序（近期截止優先）。

**學生端作業功能**：
1. **查看作業列表**：分頁分類（待完成/進行中/已完成/需修正），同卡片顯示內容數量與當前進度。
   - ✅ 修正：未到開始日期時不顯示作業 (Issue #34)
2. **進入作業**：顯示活動清單，自動建立/同步進度；首次進入即標記為進行中。
   - ✅ 修正：移除確認畫面，直接開始練習 (Issue #28)

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
       - TTS 示範音訊播放
       - 錄音按鈕 / 播放按鈕（已錄）
       - 重錄按鈕（已錄）
       - ✅ AI 評分結果（Azure Speech API 即時評分）
     - ✅ Safari 瀏覽器錄音支援（MediaRecorder API with fallback）
     - ✅ 錄音大小驗證（防止 Safari 空白錄音問題）
     - 每句錄完立即儲存
     - 全部完成自動返回作業總覽

   - 進度儲存：每題完成即自動儲存；中斷可原地續練；重錄會覆蓋上一版。

4. **進度保存機制**（朗讀錄音集）：
   - **自動保存**：
     - 每個錄音項目完成即時保存（上傳至 Cloud Storage）
     - Content 全部項目完成後自動標記為 SUBMITTED
     - ✅ 提交時自動分析未分析的錄音 (Issue #60)

   - **中斷恢復**：
     - 顯示每個項目的錄音狀態（已錄/未錄）
     - 已錄的項目保留錄音，可繼續未完成的項目

   - **重做功能**：
     - 任何項目都可重新錄音
     - 重錄會覆蓋原有錄音

5. **提交作業**：完成所有內容後一鍵提交，狀態改為「已提交」，等待教師批改。
   - ✅ 自動觸發 AI 評分（Azure Speech API）
   - ✅ 自動計算總分（從 AI 評分結果）

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
     - ✅ 修正按鈕文字：「開始訂正」而非「重新提交」(Issue #33)
     - 重新提交後狀態變為 RESUBMITTED

#### 批改與回饋系統

註：AI 批改與語音辨識深度集成已於 Phase 1 完成（Azure Speech API）。

**AI 自動批改** (✅ 已實作):
- 朗讀評測即時 AI 評分（Azure Speech Pronunciation Assessment）
- 自動計算 WPM、準確率、流暢度、完整度、發音評分
- 生成個人化改進建議
- ✅ 自動計算作業總分（從 AI 評分結果）
- ✅ 分數回填機制（Score Fallback + Backfill）

**多內容批改流程**：
1. **逐個 Content 批改**：
   - 每個 Content 可獨立給予評價和回饋
   - 每個 Content 有 `checked` 標記（通過/未通過）
   - 學生可快速識別哪些 Content 需要修正

2. **整體作業管理**：
   - 所有 Content 都需查看後才算完成批改
   - 整份作業退回（RETURNED）時，透過 checked 標記區分
   - 教師可選擇性標記哪些 Content 需要重做

3. **分數機制** (✅ 已實作)：
   - 自動從 AI 評分計算總分
   - 教師可手動調整分數
   - 支援批量評分

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
- ✅ 修正：改善顯示方式 (Issue #27)

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
   - 查看 AI 評分結果（Azure Speech API）
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
    - AI 評測結果顯示（Azure Speech API）
  - 訂正功能：可將特定文本打回重練

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
- ✅ 修正：考慮開始日期，未到日期不顯示 (Issue #34)
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
- ✅ 移除練習前確認畫面 (Issue #28)
- 目標值顯示
- 計時器（如有時限）
- 暫停/繼續功能
- 放棄練習確認

**朗讀評測練習**：
- ✅ Safari 瀏覽器完整支援
- ✅ MediaRecorder API 錄音
- ✅ 錄音大小驗證（防止空白錄音）
- 即時音量顯示
- 重錄功能
- ✅ AI 評分結果即時顯示（Azure Speech API）
- ✅ 自動上傳至 Cloud Storage
- ✅ 進度自動保存

### 3.4 資料管理功能（Phase 1）

#### 3.4.1 匯入匯出
- **學生資料匯入**：
  - 支援 CSV 格式（姓名,學號,生日,Email）
  - 批量新增學生到班級
  - 重複檢查與錯誤提示
  - ✅ 修正：不自動建立假的學生 email (Issue #30)

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

## 四、範圍界定與非目標（Phase 1）
- **非目標**：多校/機構角色、家長入口、深度 AI 批改（自動逐句建議與誤差對齊）、即時多人互動、行動裝置原生 App。
- ✅ **已實作**：TapPay 金流整合、教師訂閱付費機制、配額系統、作業-課程內容分離、Safari 錄音支援、AI 自動評分
- **可延後**：作業複製、批量截止日管理、通知中心、更多活動類型、報告自動化。
- **必要**：教師單人閉環、朗讀評測活動、作業生命週期（含退回訂正）、學生端流暢錄音體驗與自動保存。

## 五、風險與依賴
- ✅ 錄音權限與裝置相容性：已修復 Safari 相容性問題
- 學生端網路不穩造成進度同步延遲（需強化離線/重試提示與保留機制）
- 教師首次建立內容門檻（提供模板與示例內容以縮短上手時間）

## 六、技術規格與限制

### 6.1 系統需求
- **瀏覽器**：Chrome 90+、Firefox 88+、Safari 14+、Edge 90+
- **網路**：穩定的網路連線（建議 10Mbps 以上）
- **裝置**：支援麥克風的裝置（口說練習必需）
- ✅ **Safari 支援**：完整支援 MediaRecorder API 錄音功能

### 6.2 效能指標
- 頁面載入時間：< 2 秒
- API 回應時間：< 200ms
- 音訊處理延遲：< 500ms
- 並發用戶支援：1000+
- Cloud Run 冷啟動：< 10s

### 6.3 資料限制
- 單次 CSV 匯入：最多 500 筆
- 錄音長度：最長 5 分鐘
- 檔案大小：最大 50MB
- 班級人數：最多 50 人

### 6.4 安全性要求
- HTTPS 加密傳輸
- Row Level Security (RLS) 全面啟用
- JWT Token 認證
- 資料隱私保護
- 定期安全更新
- 操作日誌記錄
- TapPay PCI DSS Level 1 合規

## 七、專案里程碑

### Phase 1：個體教師版（✅ 100% 完成！）

#### ✅ 已完成功能 (2025-12-06)
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
- ✅ 翻譯 API 整合（OpenAI GPT-4 Turbo）
- ✅ TTS API 整合（OpenAI TTS-1）
- ✅ 學生登入流程
- ✅ 學生 Email 驗證機制（2025年9月實作）
- ✅ 作業系統（新架構 - 2025年9月完成）
  - ✅ 新架構資料模型（Assignment, AssignmentContent, StudentContentProgress）
  - ✅ 作業建立 API（支援多內容作業）
  - ✅ 作業列表管理 API
  - ✅ 作業編輯與刪除 API
  - ✅ 學生作業列表介面
  - ✅ 教師作業管理介面
  - ✅ 教師端作業詳情頁面
  - ✅ 學生進度追蹤儀表板
  - ✅ 作業狀態管理（NOT_STARTED, IN_PROGRESS, SUBMITTED, GRADED, RETURNED, RESUBMITTED）
- ✅ AI 自動批改（2025年11月完成）
  - ✅ Azure Speech API 語音評分（WPM, Accuracy, Fluency, Completeness, Pronunciation）
  - ✅ 自動批改流程
  - ✅ AI 回饋在學生端顯示
  - ✅ 自動計算作業總分
  - ✅ 分數回填機制（Score Fallback + Backfill）
- ✅ 人工批改功能
  - ✅ 教師批改介面
  - ✅ 手動評分與回饋
  - ✅ 作業退回訂正功能
  - ✅ 批改狀態管理
- ✅ 核心錄音功能（2025-09-12 完成）
  - ✅ 學生錄音元件開發（MediaRecorder API 完整實作）
  - ✅ 錄音檔案上傳 Cloud Storage（整合完成）
  - ✅ 錄音進度保存與中斷恢復（自動保存機制）
  - ✅ 作業提交與狀態更新（完整實作）
  - ✅ 學生完成度統計（完整實作）
  - ✅ Safari 瀏覽器相容性修復（2025-11月完成）
  - ✅ 錄音大小驗證（防止空白錄音）
- ✅ 訂閱與付費系統（2025年10月完成）
  - ✅ TapPay 金流整合（Production 環境上線）
  - ✅ 訂閱週期管理
  - ✅ 配額系統（Quota System）
  - ✅ 儀表板訂閱狀態顯示
  - ✅ 充值功能（支援多月充值）
  - ✅ 配額使用追蹤
  - ✅ 超額使用記錄
- ✅ 作業-課程內容分離（Issue #56，2025-11月完成）
  - ✅ 派作業自動建立 Content 副本
  - ✅ 原始課程內容可繼續編輯
  - ✅ 支援同一內容派給多個班級
- ✅ UX 改進（2025-11月完成）
  - ✅ 學生 URL 快速登入（Issue #59）
  - ✅ 按鈕文字修正（Issue #60, #33, #25）
  - ✅ 作業顯示邏輯修正（Issue #34, #27, #28）
  - ✅ 學號顯示修正（Issue #31）
- ✅ 成本優化（2025-11月完成）
  - ✅ Cloud Run 資源配置優化
  - ✅ Production vs Staging 差異化配置
  - ✅ 全局 Rate Limiting
  - ✅ Per-Issue 環境自動清理
  - ✅ 每日帳單監控
  - ✅ 錄音錯誤監控與報告

#### 📊 實際完成度統計
- **核心功能**: 100% 完成 ✅
- **作業系統**: 100% 完成 ✅
- **前端介面**: 100% 完成 ✅
- **AI 評分**: 100% 完成 ✅
- **Safari 支援**: 100% 完成 ✅
- **訂閱付費**: 100% 完成 ✅
- **整體 Phase 1**: **100% 完成** ✅

### Phase 1.5：提升易用性與穩定性（🔄 70% 完成）

#### ✅ 已完成
- ✅ 學生 URL 快速登入（教師分享連結）
- ✅ AI 自動評分與分數回填機制
- ✅ 錄音錯誤監控與每日報告
- ✅ 全局 Rate Limiting（防止異常高頻請求）
- ✅ 成本優化（Cloud Run 資源調整）
- ✅ Safari 錄音相容性修復
- ✅ 作業-課程內容分離機制

#### 🔄 進行中
- 🔄 作業複製功能（規劃中）
- 🔄 截止日批量延長（規劃中）
- 🔄 完成率/逾期提醒優化（規劃中）
- 🔄 教師通知面板（規劃中）

### Phase 2：內容擴展（未來 - 2025年Q4）
- □ 統計圖表功能（班級/學生進度視覺化）
- □ 機構/學校管理系統
- □ 多種活動類型（口說、聽力、造句等）
- □ 家長功能
- □ 進階統計分析與報表
- □ 通知系統完善
- □ 遊戲化元素（成就系統、排行榜）

### Phase 3：智能化升級（未來 - 2026年）
- □ AI 學習路徑規劃
- □ 自適應練習推薦
- □ 智能批改優化
- □ 預測分析與學習洞察

## 八、部署與維運

### 8.1 CI/CD 流程

#### 部署觸發條件
- **Production**: 推送到 `main` 分支
- **Staging**: 推送到 `staging` 分支
- **Per-Issue Preview**: 推送到 `claude/issue-XX` 或 `fix/issue-XX` 分支

#### 自動化檢查
- **Frontend**:
  - Prettier 格式化檢查
  - TypeScript 型別檢查
  - ESLint 程式碼檢查
  - Vite 建置測試
- **Backend**:
  - Black 格式化檢查
  - Flake8 程式碼檢查
  - pytest 單元測試
  - Alembic migration 檢查
  - RLS 配置驗證

#### 部署驗證
- **Backend**:
  - Cloud Run 部署確認
  - Health check endpoint 測試
  - 環境變數驗證
- **Frontend**:
  - Cloud Run 部署確認
  - 首頁載入測試
  - 資產編譯驗證
  - API 連接設定確認

### 8.2 監控與警報

#### 成本監控
- **每日帳單監控**: Cloud Scheduler + Billing API
- **預算警報**: $30 USD/月
- **成本趨勢追蹤**: 每日執行，Email 通知

#### 錄音錯誤監控
- **Admin Dashboard**: 錄音錯誤統計與分析
- **每日報告**: Cron job 自動執行（中午 12:00 和晚上 23:00）
- **CSV 匯出**: 支援錯誤明細匯出

#### Rate Limiting
- **全局限制**: 防止異常高頻請求
- **IP 黑名單**: 自動封鎖惡意 IP
- **流量監控**: Cloud Run Metrics

### 8.3 資料庫管理

#### Alembic Migrations
- **自動執行**: CI/CD 部署時自動執行 `alembic upgrade head`
- **檢查機制**: Pre-commit hook + CI/CD 強制檢查
- **回滾支援**: `alembic downgrade -1`

#### Row Level Security (RLS)
- **全面啟用**: 所有業務資料表
- **自動檢查**: CI/CD 部署前驗證
- **RLS Template**: `backend/alembic/rls_template.py`
- **檢查腳本**: `scripts/check_rls.sh`

#### 備份策略
- **Supabase 自動備份**: 每日自動備份
- **Point-in-Time Recovery**: 支援時間點恢復
- **測試資料**: 定期匯出 seed data

### 8.4 環境配置

#### GitHub Secrets
```yaml
# 資料庫
STAGING_SUPABASE_URL
STAGING_SUPABASE_POOLER_URL
STAGING_SUPABASE_PROJECT_URL
STAGING_SUPABASE_ANON_KEY
PRODUCTION_SUPABASE_URL
PRODUCTION_SUPABASE_POOLER_URL
PRODUCTION_SUPABASE_ANON_KEY

# JWT
STAGING_JWT_SECRET
PRODUCTION_JWT_SECRET

# TapPay (區分 Sandbox 和 Production)
TAPPAY_SANDBOX_APP_ID
TAPPAY_SANDBOX_APP_KEY
TAPPAY_SANDBOX_PARTNER_KEY
TAPPAY_SANDBOX_MERCHANT_ID
TAPPAY_PRODUCTION_APP_ID
TAPPAY_PRODUCTION_APP_KEY
TAPPAY_PRODUCTION_PARTNER_KEY
TAPPAY_PRODUCTION_MERCHANT_ID

# Azure Speech
AZURE_SPEECH_KEY
AZURE_SPEECH_REGION

# OpenAI
OPENAI_API_KEY

# GCP
GCP_SA_KEY
GCP_PROJECT_ID
```

## 九、已知問題與限制

### 9.1 技術限制
- **Safari 舊版本**: Safari 14 以下可能不支援 MediaRecorder API
- **網路延遲**: 錄音上傳受網路速度影響
- **併發限制**: Cloud Run 最多支援 6 個併發實例（Production）

### 9.2 功能限制
- **活動類型**: Phase 1 僅支援朗讀評測
- **統計圖表**: 移至 Phase 2 實作
- **多教師協作**: 未實作
- **家長端**: 未實作

### 9.3 已修復問題
- ✅ Safari 錄音空白問題（錄音大小驗證）
- ✅ 學生批量匯入假 email 問題
- ✅ 作業開始日期顯示邏輯
- ✅ 按鈕文字混淆問題
- ✅ 學號顯示問題

## 十、聯絡資訊與支援

### 10.1 環境 URL
- **Production**: https://duotopia-frontend-xxx.run.app
- **Staging**: https://duotopia-staging-frontend-xxx.run.app
- **API Docs (Staging)**: https://duotopia-staging-backend-xxx.run.app/docs

### 10.2 測試帳號
- **教師**: demo@duotopia.com / demo123
- **學生**: 選擇教師後，使用預設密碼 20120101

### 10.3 技術支援
- **Region**: asia-east1
- **Support**: 透過 GitHub Issues 回報問題
- **Documentation**: 參考 `/docs` 目錄

## 十一、附錄

### 11.1 相關文件
- **[CICD.md](./CICD.md)** - 部署與 CI/CD 準則
- **[TESTING_GUIDE.md](./docs/TESTING_GUIDE.md)** - 詳細測試指南
- **[DEPLOYMENT_STATUS.md](./docs/DEPLOYMENT_STATUS.md)** - 部署狀態
- **[金流安全檢查清單](./docs/payment/PAYMENT_SECURITY_CHECKLIST.md)** - 運營必備
- **[台灣金流法規遵循](./docs/payment/TAIWAN_PAYMENT_COMPLIANCE.md)** - 法規參考
- **[TapPay 責任分工](./docs/payment/TAPPAY_COVERAGE_ANALYSIS.md)** - 責任劃分

### 11.2 Agent 系統文件
- **[agent-manager.md](./.claude/agents/agent-manager.md)** - 核心原則
- **[git-issue-pr-flow.md](./.claude/agents/git-issue-pr-flow.md)** - Git 工作流程
- **[test-runner.md](./.claude/agents/test-runner.md)** - 測試指南
- **[code-reviewer.md](./.claude/agents/code-reviewer.md)** - 代碼審查
- **[cicd-monitor.md](./.claude/agents/cicd-monitor.md)** - CI/CD 監控

### 11.3 重要 Git Commits
- `017bcfb` - Auto-calculate assignment score from AI assessment
- `5cb37f3` - Optimize resources by environment - Production vs Staging
- `a791117` - Fix Safari recording size validation
- `9a33406` - 調整錄音錯誤報告 cron 時間
- `2026592` - 實施全局 Rate Limiting
- `7e40521` - Enhance student login with URL parameters

---

**文件版本：5.0**
**最後更新：2025-12-06**
**重點：Phase 1 個體教師版 100% 完成 + Phase 1.5 優化 70% 完成**
**狀態：MVP 功能全部完成，正式上線運營中**
**成本：~$6-11/月（完全可控）**
**下一步：Phase 2 擴展功能（統計圖表、多活動類型等）**
