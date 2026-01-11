# 用戶角色與權限體系規格

## 概述

DUOTOPIA 採用多層級用戶角色體系，涵蓋系統管理、個人教師、團購、機構四大類型，共 12 種角色。不同角色擁有不同的功能權限與資料訪問範圍。

## 角色分類

### 系統管理類

#### 1. 專案擁有人（Platform Owner）

- **職責**：DUOTOPIA 平台最高管理者，擁有系統完整控制權
- **實作方式**：Teacher.is_admin = True
- **管理範圍**：整個 DUOTOPIA 平台（所有機構、所有用戶）
- **典型使用場景**：平台營運管理、系統維護、全局資料分析

- **具體權限列表**：

**機構管理**：

- `manage_organizations`（創建/編輯/刪除/關閉/開啟機構）
- `view_all_organizations`（查看所有機構資訊）

**用戶管理**：

- `view_all_teachers`（查看所有教師帳號）
- `view_all_students`（查看所有學生帳號）
- `manage_user_accounts`（管理用戶帳號狀態）

**訂閱與財務管理**：

- `view_all_subscriptions`（查看所有訂閱記錄）
- `manage_subscriptions`（創建/編輯/取消訂閱）
- `process_refunds`（處理退款）
- `view_transaction_analytics`（查看交易分析）
- `view_billing_summary`（查看帳單摘要）
- `view_billing_anomalies`（查看帳單異常）

**平台數據分析**：

- `view_platform_analytics`（平台級數據分析）
- `view_learning_analytics`（學習數據分析）
- `view_subscription_stats`（訂閱統計）
- `view_extension_history`（延展歷史記錄）

**系統配置與維護**：

- `database_operations`（資料庫重建/seed）
- `view_database_stats`（資料庫統計）
- `system_monitoring`（系統監控：音頻上傳/AI 分析狀態）
- `view_error_logs`（查看錯誤日誌）
- `retry_statistics`（重試統計）
- `health_check`（系統健康檢查）

**開發與測試**：

- `test_audio_upload`（測試音頻上傳）
- `test_ai_analysis`（測試 AI 分析）

- **實作參考**（基於現有實作整理，2026-01-07）：
  - [backend/routers/admin.py](../../backend/routers/admin.py) - 資料庫操作、訂閱管理
  - [backend/routers/admin_subscriptions.py](../../backend/routers/admin_subscriptions.py) - 訂閱 CRUD、分析報表
  - [backend/routers/admin_billing.py](../../backend/routers/admin_billing.py) - 帳單摘要與異常檢查
  - [backend/routers/admin_monitoring.py](../../backend/routers/admin_monitoring.py) - 系統監控與測試
  - [backend/routers/admin_audio_errors.py](../../backend/routers/admin_audio_errors.py) - 錯誤日誌追蹤
  - [backend/routers/organizations.py](../../backend/routers/organizations.py) - 機構 CRUD 操作
  - [backend/models/user.py](../../backend/models/user.py#L33) - Teacher.is_admin 欄位定義

#### 2. 專案助理（Platform Assistant）

- **職責**：協助專案擁有人管理平台
- **權限**：待定義（與專案擁有人的差異）
- **管理範圍**：待定義（可能是特定功能或特定機構的管理權）
- **與專案擁有人的差異**：待定義（如：無法修改系統核心設定、無法刪除機構、無法變更財務設定等）
- **典型使用場景**：客服支援、數據分析、營運協助

### 個人教師類

#### 3. 個人教師（免費版）

- **訂閱層級**：免費
- **功能限制**：待定義（如：班級數量上限、學生數量上限、教材庫訪問限制等）
- **典型使用場景**：個人獨立教師，小規模教學

#### 4. 個人教師（BASIC）

- **訂閱層級**：BASIC（付費）
- **功能限制**：待定義
- **與免費版的差異**：待定義（如：更多班級配額、進階功能訪問等）

#### 5. 個人教師（PRO）

- **訂閱層級**：PRO（付費）
- **功能限制**：待定義
- **與 BASIC 的差異**：待定義（如：無限班級、完整教材庫、進階分析報表等）

### 團購類

#### 6. 團購負責教師

- **職責**：團購發起與管理者
- **權限**：待定義（如：邀請成員、管理團購訂閱、分配權限等）
- **與團購成員的關係**：待定義（一對多、管理者與被管理者）

#### 7. 團購教師成員

- **職責**：團購參與者
- **權限**：待定義（如：使用團購訂閱的功能、受限於負責教師的管理等）
- **限制**：待定義（如：無法邀請其他成員、依賴負責教師的訂閱狀態等）

### 機構類

#### 8. 機構負責人

- **職責**：機構最高管理者，擁有機構所有權
- **實作方式**：teacher_organizations.role = 'org_owner'
- **管理範圍**：整個機構（含所有分校）
- **權限管理**：基於 Casbin RBAC 模型

- **具體權限列表**：

**機構層級管理**：
  - `manage_schools`（創建/編輯/刪除分校）
  - `manage_teachers`（邀請/編輯/移除機構內教師）
  - `manage_students`（查看/管理機構內所有學生）
  - `manage_classrooms`（管理機構內所有班級）
  - `manage_subscription`（管理機構訂閱方案）
  - `view_analytics`（查看機構級數據分析）

**教師權限管理**：
  - `add_teacher_to_organization`（邀請教師加入機構）
  - `update_teacher_permissions`（修改教師權限）
  - `remove_teacher_from_organization`（移除教師）
  - `assign_teacher_to_school`（指派教師到分校）

**分校管理**：
  - `create_school`（創建分校）
  - `update_school`（編輯分校資訊）
  - `delete_school`（刪除分校）
  - `view_school_list`（查看所有分校）

**機構資訊管理**：
  - `update_organization`（編輯機構基本資訊）
  - `view_organization_teachers`（查看機構內所有教師）
  - 注意：`delete_organization` 功能不開放（機構不可刪除）

- **實作參考**（基於現有實作整理，2026-01-07）：
  - [backend/config/casbin_policy.csv](../../backend/config/casbin_policy.csv) - Casbin RBAC 權限定義
  - [backend/routers/organizations.py](../../backend/routers/organizations.py) - 機構 CRUD、教師管理
  - [backend/routers/schools.py](../../backend/routers/schools.py) - 分校管理
  - [backend/services/casbin_service.py](../../backend/services/casbin_service.py) - 權限檢查服務

#### 9. 機構管理人

- **職責**：協助機構負責人管理機構
- **實作方式**：teacher_organizations.role = 'org_admin'
- **管理範圍**：整個機構（含所有分校）
- **權限管理**：基於 Casbin RBAC 模型

- **與機構負責人的差異**：

**org_admin 不能做的（僅 org_owner 可以）**：
  - ❌ `view_subscription` / `manage_subscription` - 查看/管理機構訂閱方案

**兩者都不能做的**：
  - ❌ `delete_organization` - 刪除機構（不開放此功能）

**兩者共有的權限**：
  - ✅ `manage_schools` - 刪除/編輯/新增/管理學校（分校）
  - ✅ `manage_teachers` - 管理教師
  - ✅ `manage_students` - 管理學生
  - ✅ `manage_classrooms` - 管理班級
  - ✅ `view_analytics` - 查看分析數據
  - ✅ `update_organization` - 編輯機構資訊
  - ✅ 邀請/添加/移除教師
  - ✅ 修改教師權限
  - ✅ 指派教師到分校

- **實作參考**（基於現有實作整理，2026-01-07）：
  - [backend/config/casbin_policy.csv](../../backend/config/casbin_policy.csv) - org_admin 無 manage_subscription 權限
  - [backend/routers/organizations.py](../../backend/routers/organizations.py) - 機構管理 API

#### 10. 分校校長

- **職責**：分校管理者（最高管理者）
- **實作方式**：teacher_schools.roles 包含 'school_admin'
- **管理範圍**：單一分校
- **權限管理**：基於 Casbin RBAC 模型

- **具體權限列表**：

**分校層級管理**：
  - `manage_teachers` - 管理分校內的教師
  - `manage_students` - 管理分校內的學生
  - `manage_classrooms` - 管理分校內的班級
  - `view_school_analytics` - 查看分校數據分析

**權限限制**：
  - ❌ 無法管理學校（分校）本身的創建/刪除（僅 org_owner/org_admin 可以）
  - ❌ 無法查看機構訂閱方案
  - ✅ 僅限單一分校範圍（透過 teacher_schools 表關聯）

- **實作參考**（基於現有實作整理，2026-01-07）：
  - [backend/config/casbin_policy.csv](../../backend/config/casbin_policy.csv) - school_admin 權限定義
  - [backend/models/organization.py](../../backend/models/organization.py#L186) - TeacherSchool 表結構
  - [backend/routers/schools.py](../../backend/routers/schools.py) - 分校管理 API

#### 11. 分校管理人

- **職責**：協助分校校長管理分校
- **實作方式**：teacher_schools.roles 包含 'school_director'
- **管理範圍**：單一分校
- **與分校校長的差異**：權限完全相同，僅職責名稱不同

- **權限說明**：
  - 與分校校長（school_admin）**權限完全相同**
  - 包含：manage_teachers, manage_students, manage_classrooms, view_school_analytics
  - 語義上為協助者角色，但權限層面無差異

- **實作參考**（基於現有實作整理，2026-01-07）：
  - [backend/config/casbin_policy.csv](../../backend/config/casbin_policy.csv) - school_director 與 school_admin 權限相同

#### 12. 分校老師

- **職責**：教學執行者
- **權限**：待定義（如：建立班級、指派作業、查看自己班級的學生成績等）
- **管理範圍**：自己建立的班級
- **限制**：待定義（如：無法訪問其他老師的班級、無法管理分校設定等）

### 學生類

#### 學生

- **角色**：學習者
- **權限**：待定義（如：完成作業、查看自己的成績、訪問教材等）

**帳號建立與身份驗證機制**：

學生帳號有兩種建立方式：

1. **學生自行註冊**：

   - 學生使用 Email 註冊帳號
   - Email 作為登入帳號
   - 自行設定密碼
   - **登入方式**：Email + 密碼

2. **老師建立學生帳號**：
   - 老師在建立班級時，輸入學生的基本資料（姓名、學號、生日）
   - 系統以「生日」作為預設密碼（格式：YYYYMMDD）
   - 學生登入後可選擇性綁定 Email（非必要）
   - **重要**：未綁定 Email 不影響完成作業等核心功能
   - **登入方式**（老師建立的學生）：
     1. 輸入老師的 Email
     2. 系統顯示該老師的所有班級
     3. 學生選擇自己所屬的班級
     4. 系統顯示該班級的所有學生姓名
     5. 學生點選自己的姓名
     6. 輸入密碼（預設為生日 YYYYMMDD）
     7. 登入成功後，可自行更改密碼與綁定 Email

**帳號唯一性規則**：混合模式

- **內部識別**：使用內部自動產生的 Student ID（數字主鍵）作為唯一識別
- **登入識別**：
  - **有 Email 的學生**：使用 Email 登入
  - **無 Email 的學生**：使用「老師 Email + 班級 + 學生姓名 + 密碼」組合登入
- **唯一性約束**：
  - Student ID（主鍵）：全系統唯一
  - Email：選填，若填寫則必須全系統唯一
  - 學號：選填，可重複（不同老師可能有相同學號的學生）
  - 姓名 + 班級 + 老師：組合必須唯一（同一個班級內不能有重複姓名）
- **帳號合併邏輯**：
  - 當老師建立的學生綁定 Email 後，若該 Email 已存在（自行註冊），需決定是合併帳號或拒絕綁定（待定義）
  - 跨老師、跨班級時，學生需要有某種方式關聯同一個 Student ID（待定義：如何識別是同一個學生？）

**帳號唯一性規則**：待定義（系統用什麼來唯一識別一個學生帳號？Email、學號、還是內部 ID？）

**跨機構、跨班級歸屬規則**：

- **資料模型**：一個學生可以同時在多個機構註冊，可以屬於多個班級

  - Student 實體與 Classroom 的關係為多對多（透過 classroom_enrollments 關聯表）
  - 學生可以同時參加個人老師的班級與機構老師的班級
  - **重要**：各機構的學習記錄**完全隔離**，不互相共享（詳見「資料模型考量 > 資料隔離」章節）

- **情境切換機制**（類似教師的多角色切換）：

  - 學生登入後，透過下拉選單選擇要進入哪個班級的學生端介面
  - 切換情境範例：
    - 「機構 A - 王老師 - 英文初級班」
    - 「個人老師 - 李老師 - 英文進階班」
  - 切換後，僅顯示該機構/老師的作業、成績、教材等資訊
  - UI/UX 需提供清楚的情境指示（目前在哪個機構/班級）

- **資料訪問權限**：

  - 學生只能查看自己在各班級的資料
  - 不同機構的資料完全隔離（切換情境時，看到的是完全不同的資料集）
  - 同一機構內不同班級的資料分別顯示（依據當前選擇的班級情境）
  - 教師只能查看自己班級內該學生的資料

- **可歸屬**：多個機構、多個班級（需定義跨機構、跨班級的規則）
- **帳號唯一性**：待定義（單一帳號或每個機構獨立帳號）

## 核心規則

### 角色層級關係

完整的角色層級關係：

**系統層級（最高）：**

- 專案擁有人 > 專案助理

**機構層級：**

- 機構負責人 > 機構管理人 > 分校校長 > 分校管理人 > 分校老師

**個人與團購層級：**

- 團購負責教師 > 團購教師成員
- 個人教師（PRO）> 個人教師（BASIC）> 個人教師（免費版）

**跨層級關係：**

- 專案擁有人/專案助理可管理所有機構
- 機構角色與個人教師角色相互獨立（同一用戶可同時擁有）

**權限繼承原則**：

- **機構後台（RBAC 體系）**：上層角色自動繼承下層角色的所有權限

  - 機構負責人自動擁有機構管理人、分校校長、分校管理人、分校老師在機構後台的所有管理權限
  - 分校校長自動擁有分校管理人、分校老師在分校管理功能的所有權限
  - 繼承關係僅限於同一機構體系內（機構 A 的負責人無法管理機構 B）

- **個人教師後台（所有權體系）**：無繼承關係
  - 每個教師僅能管理自己建立的資源（班級、作業等）
  - 訂閱層級（免費/BASIC/PRO）控制功能可用性，非權限繼承

權限繼承原則：待定義（上層角色是否自動擁有下層角色的所有權限）

### 跨類型角色

一位用戶可能同時擁有多種角色：

- 同時是機構負責人和個人 PRO 教師
- 同時是團購負責教師和機構分校老師

**多角色時的行為邏輯**：依據操作情境自動選擇最合適的角色

- **情境導向的角色切換**：

  - 進入「個人教師後台」時，自動使用個人教師角色與權限（所有權模式）
  - 進入「機構後台」時，自動使用機構相關角色與權限（RBAC 模式）
  - 不需要手動切換角色，系統根據當前後台環境自動判定

- **實作考量**：

  - URL 路徑區分：`/teacher/*` 為個人教師後台，`/organization/*` 為機構後台
  - Session 或 Context 記錄當前後台類型
  - API 請求根據路徑前綴自動套用對應的權限驗證邏輯

- **跨後台操作**：
  - 若需要跨後台操作（例如：在個人教師後台查看機構班級），系統根據資源類型自動判斷使用哪種權限檢查
  - 優先使用當前後台的權限邏輯，若無權限再嘗試跨後台權限檢查

多角色時的行為：待定義（角色切換機制、預設角色、權限合併策略）

### 角色轉換

角色的生命週期管理：

- 教師離職時的處理：待定義（班級轉移、權限回收等）
- 學生退出機構時的處理：待定義（資料保留、成績歸檔等）
- 機構負責人變更：待定義（所有權轉移流程）

## 資料模型考量

### 角色的資料結構

**已採用設計方式**：Teacher/Student 分離設計 + 關聯表處理機構角色

- **Teacher 表與 Student 表分離設計**：不同類型用戶使用不同表（參考 backend/models/user.py）
  - Teacher 表：記錄教師的基本資料、訂閱資訊、信用卡資料等
  - Student 表：記錄學生的基本資料、學號、生日（預設密碼）等
- **機構角色使用關聯表**（參考 backend/models/organization.py）：

  - `teacher_organizations` 表：記錄教師在機構層級的角色（org_owner, org_admin）
  - `teacher_schools` 表：記錄教師在學校層級的角色（school_principal, school_admin, teacher）
  - 支援一個 Teacher 同時擁有多個機構/學校角色

- **優勢**：

  - Teacher 與 Student 的資料結構差異大，分離設計避免欄位冗餘
  - 使用關聯表支援多角色，靈活度高
  - 查詢效能佳（利用索引與外鍵）

- **個人教師訂閱方案角色**：待定義（是否需要額外的角色欄位或關聯表）
- **團購角色**：待定義（是否需要 GroupPurchase 相關表）
- **系統管理角色（Platform Owner/Assistant）**：待定義（是否需要額外的角色標記或權限表）

角色可採用不同的設計方式：

- 單一用戶表 + 角色欄位（role ENUM）
- 教師表 + 學生表分離設計
- 角色繼承體系（User > Teacher > InstitutionTeacher）
- 多角色關聯表（User-Role 多對多關係）

### 權限控制策略

**已採用策略**：混合模式（RBAC + 資源所有權），依據後台類型分別應用

#### 整體系統：混合模式（C）

系統整體採用 RBAC + 資源所有權的混合模式，但兩個後台的側重不同：

#### 個人教師後台：所有權模式（D）

- **主要策略**：簡單所有權模式
- **控制邏輯**：
  - 教師只能管理自己建立的資源（班級、作業、教材）
  - 不涉及階層管理，無需複雜的角色權限
  - 訂閱層級（免費/BASIC/PRO）控制功能開關，非權限控制
- **適用資源**：
  - 班級管理（我的班級）
  - 作業指派（我的作業）
  - 學生成績（我的學生）
  - 教材管理（我的教材）

#### 機構後台：RBAC 模式（A）

- **主要策略**：基於角色的訪問控制（RBAC）
- **實作工具**：Casbin（參考 backend 中的 Casbin 配置）
- **角色層級**：
  - 專案擁有人 > 專案助理（系統級）
  - 機構負責人 > 機構管理人（機構級）
  - 分校校長 > 分校管理人 > 分校老師（學校級）
- **控制邏輯**：
  - 依據用戶在機構/學校的角色決定權限
  - 上層角色可管理下層資源（待定義繼承規則）
  - 適用於階層管理場景
- **適用資源**：
  - 機構管理（建立/刪除分校、管理成員）
  - 分校管理（指派教師、查看所有班級）
  - 成員權限管理

#### 混合判斷邏輯

當跨後台操作時（例如：機構管理者要查看某教師的班級）：

1. 先檢查機構後台的角色權限（RBAC）：使用者在機構中的角色是否有權限
2. 若無機構角色，檢查個人教師後台的所有權：是否為資源擁有者
3. 兩者任一通過即允許操作

- **RBAC（基於角色的訪問控制）**：

  - 使用 Casbin 實作角色權限管理（參考 backend 中的 Casbin 配置）
  - 定義角色層級：專案擁有人 > 機構負責人 > 分校校長 > 老師等
  - 每個角色配置對應的權限集合
  - 適用場景：機構階層管理、系統級功能訪問控制

- **資源所有權檢查**：

  - 檢查資源的建立者或擁有者
  - 適用場景：班級編輯、作業管理、個人資料存取
  - 範例：老師只能編輯自己建立的班級，但分校校長可以編輯所有班級

- **混合判斷邏輯**：

  1. 先檢查角色權限（RBAC）：使用者的角色是否有執行此動作的權限
  2. 再檢查資源所有權：若角色權限不足，檢查是否為資源擁有者
  3. 兩者任一通過即允許操作

- **優勢**：
  - 兼顧階層管理的清晰性（透過 RBAC）
  - 保有資料隔離與個人所有權（透過所有權檢查）
  - 靈活度高，可應對複雜的權限需求

權限控制可採用：

- 基於角色的訪問控制（RBAC）
- 基於屬性的訪問控制（ABAC）
- 混合模式（角色 + 資源所有權）

### 資料隔離

**機構間的資料隔離規則**：

- **機構與機構之間**：完全隔離

  - 機構 A 的任何角色（負責人、校長、老師等）無法訪問機構 B 的任何資料
  - 包括：學生資料、班級資料、作業資料、成績資料、教材資料等
  - 實作方式：PostgreSQL Row-Level Security (RLS) 策略

- **機構內分校之間**：部分隔離

  - **可共享**：教材資料（機構內所有分校可共享教材庫）
  - **完全隔離**：班級資料、學生資料、作業資料、成績資料
  - 分校 A 的老師無法查看分校 B 的班級與學生
  - 但機構負責人、機構管理人可查看所有分校的資料（依據 RBAC 權限）

- **跨機構用戶的資料隔離**：

  - **學生跨機構**：

    - 同一個學生帳號可以在多個機構註冊（作為不同機構的學生）
    - 各機構的學習記錄**完全隔離**，不互相共享
    - 學生需透過下拉選單切換情境，查看不同機構的資料
    - 範例：小明在機構 A 的英文初級班和機構 B 的英文進階班，兩邊的成績、作業記錄是分開的

  - **老師跨機構**：
    - 同一個老師帳號可以在多個機構任教
    - 各機構的班級、學生資料**完全隔離**
    - 老師需透過情境切換（進入不同機構後台）查看不同機構的資料
    - 在個人教師後台看到的是自己所有的班級（跨機構合併顯示）
    - 在機構後台看到的僅限該機構的資料

機構與班級的資料隔離：

- 機構間的資料隔離規則
- 班級間的資料隔離規則
- 學生跨機構/跨班級時的資料訪問權限

## 與現有系統的關聯

### 相關實體（參考 backend/models.py）

- **Teacher**：教師實體

  - 需補充：訂閱層級欄位（subscription_tier）
  - 需補充：角色欄位或關聯表

- **Student**：學生實體

  - 需補充：跨機構/跨班級的關聯設計

- **待新增實體**：
  - Organization/Institution：機構實體
  - Campus：分校實體
  - Role/Permission：角色權限實體（如採用 RBAC）

### 相關功能

需考慮角色權限的功能：

- 班級管理（不同角色的建立/查看/修改權限）
- 作業指派（誰可以指派、誰可以查看）
- 成績查詢（教師查看範圍、學生查看範圍）
- 教材管理（誰可以新增、誰可以查看、分享規則）

## 參考資料

- [backend/models.py](../../backend/models.py)：Teacher/Student 模型
- [student-abilities-assessment.md](./student-abilities-assessment.md)：學生能力評估體系
